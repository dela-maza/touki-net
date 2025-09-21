# apps/documents/required/views.py
from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from datetime import datetime
from apps.common.forms import CSRFOnlyForm
from db import db
from apps.documents.required.models import RequiredDocument
from apps.documents.required.forms import RequiredDocumentForm
from apps.documents.required.config_loader import load_paragraphs, get_required_doc_defaults
from apps.client.models import Client

# --------------------------
# ブループリント
# --------------------------
required_bp = Blueprint(
    "required",  # Blueprint 名
    __name__,
    url_prefix="/documents/required",
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
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"{ng_msg}: {e}", "danger")  # ← 例外を表示
        return False

from wtforms import FieldList

def _fill_field_list(field_list: FieldList, rows: list[dict[str, str]]):
    """
    rows: [{doc_name, note, copies}] を FieldList<FormField(DocumentItemForm)> に流し込む。
    """
    # 行数を揃える
    while len(field_list) < len(rows):
        field_list.append_entry()

    # 値をセット
    for entry, row in zip(field_list, rows):
        f = entry.form  # FormField の .form（サブフォーム）を想定
        f.doc_name.data = row.get("doc_name", "")
        if hasattr(f, "note"):
            f.note.data = row.get("note", "")
        if hasattr(f, "copies"):
            f.copies.data = row.get("copies", "")


def _collect_field_list(field_list: FieldList) -> list[dict[str, str]]:
    """
    FieldList<FormField(DocumentItemForm)> → [{doc_name, note, copies}]
    空行（全て空）はスキップ。
    """
    rows: list[dict[str, str]] = []
    for entry in field_list:
        f = entry.form
        doc_name = (f.doc_name.data or "").strip()
        note     = (getattr(f, "note", None).data or "").strip() if hasattr(f, "note") else ""
        copies   = (getattr(f, "copies", None).data or "").strip() if hasattr(f, "copies") else ""
        if doc_name or note or copies:
            rows.append({"doc_name": doc_name, "note": note, "copies": copies})
    return rows

# --------------------------
# Index（一覧）
# --------------------------
@required_bp.route("/")
def index() -> str:
    client_id = request.args.get("client_id", type=int)
    q = (RequiredDocument.query
         .options(joinedload(RequiredDocument.client))
         .order_by(RequiredDocument.created_at.desc(), RequiredDocument.id.desc()))
    if client_id:
        q = q.filter(RequiredDocument.client_id == client_id)

    documents = q.all()
    return render_template(
        "required/index.html",
        documents=documents,
        client_id=client_id,
    )


# --------------------------
# Detail（詳細）
# --------------------------
@required_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    doc = (RequiredDocument.query
           .options(joinedload(RequiredDocument.client))
           .get_or_404(document_id))
    return render_template("required/detail.html", document=doc)


# --------------------------
# Create（新規）
# --------------------------
@required_bp.route("/create", methods=["GET", "POST"])
def create():
    form = RequiredDocumentForm()

    # 必須: client_id はクエリで渡す /?client_id=123
    client_id = request.args.get("client_id", type=int)
    if not client_id:
        flash("クライアントが指定されていません。", "danger")
        return redirect(url_for("client.index"))

    client = Client.query.get_or_404(client_id)
    form.client_id.data = client.id  # HiddenField へセット

    # 戻り先（ツールバー＆下部ボタン用）
    back_url = (
            request.args.get("back")
            or url_for("client.documents_index", client_id=client.id)   # ← ここを修正
    )

    if request.method == "GET":
        # 段落: config_loader から流し込み
        paras = load_paragraphs()
        form.greeting_paragraph.data = paras.get("greeting", "")
        form.main_paragraph.data = paras.get("main", "")
        form.closing_paragraph.data = paras.get("closing", "")

        # 明細（送付/返送）: client.client_type に応じて既定行を注入
        defaults = get_required_doc_defaults(client.client_type)
        _fill_field_list(form.mailed_documents, defaults["mailed"])
        _fill_field_list(form.requested_return_documents, defaults["requested"])

        # 受託簿名: クライアントにぶら下がる受託簿名があるなら初期値に
        if client.entrusted_book:
            form.entrusted_book_name.data = client.entrusted_book.name


    # POST: 保存
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
        try:
            db.session.flush()  # ここで new id を発番（失敗も早期にわかる）
            # new_id = doc.id
            db.session.commit()
            flash("必要書類を作成しました。", "success")
            return redirect(url_for("required.detail", document_id=doc.id), code=303)
        except Exception as e:
            db.session.rollback()
            # ここでエラー内容を必ず露出させる
            import traceback
            traceback.print_exc()
            flash(f"必要書類の作成に失敗しました: {e}", "danger")
    else:
        # ここに来たらバリデーションNG。詳細を出す
        for field, errs in form.errors.items():
            flash(f"{field}: {', '.join(errs)}", "danger")

    # 失敗/初回表示
    return render_template(
        "required/form.html",
        form=form,
        client=client,
        is_edit=False,
        back_url=back_url,
    )


# --------------------------
# Edit（更新）
# --------------------------
@required_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
def edit(document_id: int):
    doc = RequiredDocument.query.options(joinedload(RequiredDocument.client)).get_or_404(document_id)
    form = RequiredDocumentForm(obj=doc)
    # HiddenField を復元
    form.client_id.data = doc.client_id

    if request.method == "GET":
        # FieldListは、form = RequiredDocumentForm(obj=doc)では入力されない。
        _fill_field_list(form.mailed_documents, doc.mailed_documents or [])
        _fill_field_list(form.requested_return_documents, doc.requested_return_documents or [])

    if form.validate_on_submit():
        # 基本フィールド
        doc.entrusted_book_name = form.entrusted_book_name.data
        doc.greeting_paragraph = form.greeting_paragraph.data or ""
        doc.main_paragraph = form.main_paragraph.data or ""
        doc.closing_paragraph = form.closing_paragraph.data or ""
        doc.sent_date = form.sent_date.data
        # FieldList → JSONB
        doc.mailed_documents = _collect_field_list(form.mailed_documents)
        doc.requested_return_documents = _collect_field_list(form.requested_return_documents)

        if _commit_with_flash("必要書類を更新しました。", "必要書類の更新に失敗しました。"):
            # 一覧から戻る導線があるなら、必要に応じて client_id を付ける
            return redirect(url_for("required.detail", document_id=doc.id))

    return render_template("required/form.html",
                           form=form,
                           document=doc,
                           client=doc.client,
                           is_edit=True)


# --------------------------
# Confirm Delete（確認）
# --------------------------
@required_bp.route("/<int:document_id>/confirm_delete")
def confirm_delete(document_id: int) -> str:
    doc = RequiredDocument.query.get_or_404(document_id)
    cancel_url = request.args.get("next") or url_for(
        "client.documents_index", client_id=doc.client_id
    )
    form = CSRFOnlyForm()
    return render_template("required/confirm_delete.html",
                           document=doc, form=form, cancel_url=cancel_url)


# --------------------------
# Delete（削除）
# --------------------------
@required_bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id: int):
    form = CSRFOnlyForm()
    cancel_url = request.args.get("next") or url_for(
        "client.documents_index", client_id=RequiredDocument.query.get_or_404(document_id).client_id
    )
    if not form.validate_on_submit():
        flash("不正なリクエストです。（CSRF）", "danger")
        return redirect(cancel_url)

    doc = RequiredDocument.query.get_or_404(document_id)
    db.session.delete(doc)
    if _commit_with_flash("必要書類を削除しました。", "必要書類の削除に失敗しました。"):
        return redirect(url_for("client.documents_index", client_id=doc.client_id))
    return redirect(url_for("required.detail", document_id=doc.id))
