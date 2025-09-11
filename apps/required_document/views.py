# apps/required_document/views.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from datetime import datetime

from db import db
from apps.required_document.models import RequiredDocument
from apps.required_document.forms import RequiredDocumentForm, DocumentItemForm
from apps.required_document.config_loader import load_paragraphs, get_required_doc_defaults
from apps.client.models import Client

# --------------------------
# ブループリント
# --------------------------
required_document_bp = Blueprint(
    "required_document",
    __name__,
    url_prefix="/required-document",
    template_folder="templates",
    static_folder="static",
)

# --------------------------
# 内部ユーティリティ
# --------------------------
def _commit_with_flash(ok_msg: str, ng_msg: str) -> bool:
    try:
        db.session.commit()
        flash(ok_msg, "success")
        return True
    except SQLAlchemyError:
        db.session.rollback()
        flash(ng_msg, "danger")
        return False

def _fill_field_list(field_list, rows):
    """[{name,note,copies}] を WTForms FieldList に流し込む"""
    while len(field_list) < len(rows):
        field_list.append_entry()
    for sub, row in zip(field_list, rows):
        sub.name.data   = row.get("name", "")
        # ReturnDocumentItemForm には note/copies あり、DocumentItemForm は name/copies 程度など
        if hasattr(sub, "note"):
            sub.note.data   = row.get("note", "")
        if hasattr(sub, "copies"):
            sub.copies.data = row.get("copies", "")

def _collect_field_list(field_list):
    """FieldList → [{name,note,copies}]（空行はスキップ）"""
    rows = []
    for sub in field_list:
        name   = (sub.name.data or "").strip() if hasattr(sub, "name") else ""
        note   = (sub.note.data or "").strip() if hasattr(sub, "note") else ""
        copies = (sub.copies.data or "").strip() if hasattr(sub, "copies") else ""
        if name or note or copies:
            rows.append({"name": name, "note": note, "copies": copies})
    return rows

# --------------------------
# Index（一覧）
# --------------------------
@required_document_bp.route("/")
def index() -> str:
    client_id = request.args.get("client_id", type=int)
    q = (RequiredDocument.query
         .options(joinedload(RequiredDocument.client))
         .order_by(RequiredDocument.created_at.desc(), RequiredDocument.id.desc()))
    if client_id:
        q = q.filter(RequiredDocument.client_id == client_id)

    documents = q.all()
    return render_template(
        "required_document/index.html",
        documents=documents,
        client_id=client_id,
    )

# --------------------------
# Detail（詳細）
# --------------------------
@required_document_bp.route("/<int:doc_id>")
def detail(doc_id: int) -> str:
    doc = (RequiredDocument.query
           .options(joinedload(RequiredDocument.client))
           .get_or_404(doc_id))
    return render_template("required_document/detail.html", document=doc)

# --------------------------
# Create（新規）
# --------------------------
@required_document_bp.route("/create", methods=["GET", "POST"])
def create():
    form = RequiredDocumentForm()

    # 必須: client_id はクエリで渡す /?client_id=123
    client_id = request.args.get("client_id", type=int)
    if not client_id:
        flash("クライアントが指定されていません。", "danger")
        return redirect(url_for("client.index"))
    client = Client.query.get_or_404(client_id)
    form.client_id.data = client.id  # HiddenField へセット

    if request.method == "GET":
        # 段落: config_loader から流し込み
        paras = load_paragraphs()
        form.greeting_paragraph.data = paras.get("greeting", "")
        form.main_paragraph.data     = paras.get("main", "")
        form.closing_paragraph.data  = paras.get("closing", "")

        # 明細（送付/返送）: client.client_type に応じて既定行を注入
        defaults = get_required_doc_defaults(client.client_type)
        _fill_field_list(form.mailed_documents, defaults["mailed"])
        _fill_field_list(form.requested_return_documents, defaults["requested"])

        # 受託簿名: クライアントにぶら下がる受託簿名があるなら初期値に
        if client.entrusted_book:
            form.entrusted_book_name.data = client.entrusted_book.name

    if form.validate_on_submit():
        doc = RequiredDocument(
            client_id=client.id,
            entrusted_book_name=form.entrusted_book_name.data,
            greeting_paragraph=form.greeting_paragraph.data or "",
            main_paragraph=form.main_paragraph.data or "",
            closing_paragraph=form.closing_paragraph.data or "",
            mailed_documents=_collect_field_list(form.mailed_documents),
            requested_return_documents=_collect_field_list(form.requested_return_documents),
            sent_date=form.sent_date.data,
            created_at=datetime.utcnow(),
        )
        db.session.add(doc)
        if _commit_with_flash("必要書類を作成しました。", "必要書類の作成に失敗しました。"):
            return redirect(url_for("required_document.detail", doc_id=doc.id))

    return render_template("required_document/form.html", form=form, client=client, is_edit=False)

# --------------------------
# Edit（更新）
# --------------------------
@required_document_bp.route("/<int:doc_id>/edit", methods=["GET", "POST"])
def edit(doc_id: int):
    doc = RequiredDocument.query.options(joinedload(RequiredDocument.client)).get_or_404(doc_id)
    form = RequiredDocumentForm(obj=doc)
    # HiddenField を復元
    form.client_id.data = doc.client_id

    if request.method == "GET":
        # JSONB → FieldList
        _fill_field_list(form.mailed_documents, doc.mailed_documents or [])
        _fill_field_list(form.requested_return_documents, doc.requested_return_documents or [])

    if form.validate_on_submit():
        # 基本フィールド
        doc.entrusted_book_name = form.entrusted_book_name.data
        doc.greeting_paragraph  = form.greeting_paragraph.data or ""
        doc.main_paragraph      = form.main_paragraph.data or ""
        doc.closing_paragraph   = form.closing_paragraph.data or ""
        doc.sent_date           = form.sent_date.data
        # FieldList → JSONB
        doc.mailed_documents = _collect_field_list(form.mailed_documents)
        doc.requested_return_documents = _collect_field_list(form.requested_return_documents)

        if _commit_with_flash("必要書類を更新しました。", "必要書類の更新に失敗しました。"):
            # 一覧から戻る導線があるなら、必要に応じて client_id を付ける
            return redirect(url_for("required_document.detail", doc_id=doc.id))

    return render_template("required_document/form.html", form=form, document=doc, client=doc.client, is_edit=True)

# --------------------------
# Confirm Delete（確認）
# --------------------------
@required_document_bp.route("/<int:doc_id>/confirm_delete")
def confirm_delete(doc_id: int) -> str:
    doc = RequiredDocument.query.get_or_404(doc_id)
    return render_template("required_document/confirm_delete.html", document=doc)

# --------------------------
# Delete（削除）
# --------------------------
@required_document_bp.route("/<int:doc_id>/delete", methods=["POST"])
def delete(doc_id: int):
    doc = RequiredDocument.query.get_or_404(doc_id)
    db.session.delete(doc)
    if _commit_with_flash("必要書類を削除しました。", "必要書類の削除に失敗しました。"):
        # 元の一覧へ戻す。client_id を付けるとクライアント別一覧に戻せる
        return redirect(url_for("required_document.index", client_id=doc.client_id))
    return redirect(url_for("required_document.detail", doc_id=doc.id))