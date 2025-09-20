### apps/documents/delivery/views.py
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from wtforms import FieldList

from db import db

from apps.common.forms import CSRFOnlyForm
from apps.client.models import Client
from apps.documents.delivery.config_loader import load_paragraphs, get_default_documents
from apps.documents.delivery.models import DeliveryDocument
from apps.documents.delivery.forms import DeliveryDocumentForm

# --------------------------
# ブループリント
# --------------------------
delivery_bp = Blueprint(
    "delivery",  # Blueprint 名
    __name__,
    url_prefix="/documents/delivery",
    template_folder="templates",
    static_folder="static",
)


# --------------------------
# 内部ユーティリティ
# --------------------------
def _commit_with_flash(ok_msg: str, ng_msg: str) -> bool:
    """DB commit + フラッシュ。失敗なら rollback してエラーフラッシュ"""
    try:
        db.session.commit()
        flash(ok_msg, "success")
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"{ng_msg}: {e}", "danger")
        return False


def _fill_documents(field_list: FieldList, rows: list[dict[str, str]]) -> None:
    """rows: [{doc_name, copies}] を FieldList<FormField> に流し込む。"""
    while len(field_list) < len(rows):
        field_list.append_entry()
    for entry, row in zip(field_list, rows):
        f = entry.form
        f.doc_name.data = row.get("doc_name", "")
        f.copies.data = row.get("copies", "")


def _collect_documents(field_list: FieldList) -> list[dict[str, str]]:
    """FieldList<FormField> → [{doc_name, copies}]（空行はスキップ）。"""
    out: list[dict[str, str]] = []
    for entry in field_list:
        f = entry.form
        doc_name = (f.doc_name.data or "").strip()
        copies = (f.copies.data or "").strip()
        if doc_name or copies:
            out.append({"doc_name": doc_name, "copies": copies})
    return out


# --------------------------
# Index（一覧）
# --------------------------
@delivery_bp.route("/")
def index() -> str:
    client_id = request.args.get("client_id", type=int)
    q = (DeliveryDocument.query
         .options(joinedload(DeliveryDocument.client))
         .order_by(DeliveryDocument.created_at.desc(), DeliveryDocument.id.desc()))
    if client_id:
        q = q.filter(DeliveryDocument.client_id == client_id)

    documents = q.all()
    return render_template(
        "delivery/index.html",
        documents=documents,
        client_id=client_id,
    )


# --------------------------
# Detail（詳細）
# --------------------------
@delivery_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    doc = (DeliveryDocument.query
           .options(joinedload(DeliveryDocument.client))
           .get_or_404(document_id))
    return render_template("delivery/detail.html", document=doc)


# --------------------------
# Create（新規）
# --------------------------
@delivery_bp.route("/create", methods=["GET", "POST"])
def create():
    form = DeliveryDocumentForm()

    # 必須: client_id はクエリで渡す /?client_id=123
    client_id = request.args.get("client_id", type=int)
    if not client_id:
        flash("クライアントが指定されていません。", "danger")
        return redirect(url_for("client.index"))

    client = Client.query.get_or_404(client_id)
    form.client_id.data = client.id  # HiddenField へセット

    # 戻り先（ツールバー＆下部ボタン用）
    back_url = request.args.get("back") or url_for("client.documents_index", client_id=client.id)

    if request.method == "GET":
        # ---- 段落：config_loader から初期文面を流し込み ----
        paras = load_paragraphs()  # {"greeting": "...", "closing": "..."}
        form.greeting_paragraph.data = paras.get("greeting", "")
        form.closing_paragraph.data = paras.get("closing", "")

        # 行：client_type に応じたセクションから
        defaults = get_default_documents(client.client_type)  # ★ここがポイント
        _fill_documents(form.documents, defaults)

        # ---- 受託簿名：クライアントに紐づく受託簿名があれば初期値に ----
        if client.entrusted_book:
            form.entrusted_book_name.data = client.entrusted_book.name

    # ---- POST: 保存 ----
    if form.validate_on_submit():
        doc = DeliveryDocument(
            client_id=client.id,
            entrusted_book_name=form.entrusted_book_name.data,
            greeting_paragraph=form.greeting_paragraph.data or "",
            closing_paragraph=form.closing_paragraph.data or "",
            documents=_collect_documents(form.documents),
            sent_date=form.sent_date.data,
            created_at=datetime.utcnow(),
        )
        db.session.add(doc)
        try:
            db.session.flush()  # new id を発番
            db.session.commit()
            flash("納品書を作成しました。", "success")
            return redirect(url_for("delivery.detail", document_id=doc.id), code=303)
        except Exception as e:
            db.session.rollback()
            import traceback;
            traceback.print_exc()
            flash(f"納品書の作成に失敗しました: {e}", "danger")

    elif form.is_submitted():  # POSTだがバリデーションNG
        for field, errs in form.errors.items():
            flash(f"{field}: {', '.join(errs)}", "danger")

    # 失敗/初回表示
    return render_template(
        "delivery/form.html",
        form=form,
        client=client,
        is_edit=False,
        back_url=back_url,
        title="New Delivery",
    )


# --------------------------
# Edit（更新）
# --------------------------
@delivery_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
def edit(document_id: int):
    doc = DeliveryDocument.query.options(joinedload(DeliveryDocument.client)).get_or_404(document_id)
    form = DeliveryDocumentForm(obj=doc)
    # HiddenField を復元
    form.client_id.data = doc.client_id

    if request.method == "GET":
        # FieldList は obj=doc では埋まらないため個別に流し込む
        _fill_documents(form.documents, doc.documents or [])

    if form.validate_on_submit():
        # 基本フィールド
        doc.entrusted_book_name = form.entrusted_book_name.data
        doc.greeting_paragraph = form.greeting_paragraph.data or ""
        doc.closing_paragraph = form.closing_paragraph.data or ""
        doc.sent_date = form.sent_date.data
        # FieldList → JSONB
        doc.documents = _collect_documents(form.documents)

        if _commit_with_flash("納品書を更新しました。", "納品書の更新に失敗しました。"):
            return redirect(url_for("delivery.detail", document_id=doc.id))

    return render_template("delivery/form.html",
                           form=form,
                           document=doc,
                           client=doc.client,
                           title="Edit Delivery",
                           is_edit=True)


# --------------------------
# Confirm Delete（確認）
# --------------------------
@delivery_bp.route("/<int:document_id>/confirm_delete")
def confirm_delete(document_id: int) -> str:
    doc = DeliveryDocument.query.get_or_404(document_id)
    form = CSRFOnlyForm()
    return render_template("delivery/confirm_delete.html", document=doc, form=form)


# --------------------------
# Delete（削除）
# --------------------------
@delivery_bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id: int):
    form = CSRFOnlyForm()
    if not form.validate_on_submit():
        flash("不正なリクエストです。（CSRF）", "danger")
        return redirect(url_for("delivery.detail", document_id=document_id))

    doc = DeliveryDocument.query.get_or_404(document_id)
    db.session.delete(doc)
    if _commit_with_flash("納品書を削除しました。", "納品書の削除に失敗しました。"):
        return redirect(url_for("client.documents_index", client_id=doc.client_id))
    return redirect(url_for("delivery.detail", document_id=doc.id))
