### apps/amount_document/views.py
# from pprint import pprint
from flask import Blueprint, render_template, flash, redirect, url_for, request
from db import db
# from apps.entrusted_book.models import EntrustedBook
# from flask import current_app
from apps.amount_document.calculator import AmountDocumentCalculator
from apps.amount_document.forms import AmountDocumentForm
from apps.amount_document.models import AmountDocument
# from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Dict, Union, Optional

amount_document_bp = Blueprint(
    "amount_document", __name__,
    url_prefix="/amount-document",
    template_folder="templates",
    static_folder="static"
)


def _get_document_or_404(document_id: int) -> AmountDocument:
    """
    options(joinedload(AmountDocument.client)) AmountDocumentに紐つけられたclientをAmountDocumentと同時に一括取得
    """
    return (
        AmountDocument.query
        .options(joinedload(AmountDocument.client))
        .get_or_404(document_id))


def _commit_session_with_flash(success_message: str, error_message: str) -> bool:
    try:
        db.session.commit()
        flash(success_message)
        return True
    except SQLAlchemyError:
        db.session.rollback()
        flash(error_message, "error")
        return False


# apps/amount_document/views.py
from apps.client.models import Client
from apps.entrusted_book.models import EntrustedBook
from sqlalchemy.orm import joinedload


# --------------------------
# Index（一覧）
# --------------------------
@amount_document_bp.route("/")
def index() -> str:
    # クエリ取得（任意）
    client_id = request.args.get("client_id", type=int)
    entrusted_book_id = request.args.get("entrusted_book_id", type=int)

    # 一覧クエリ（Client→EntrustedBook をまとめてロードしてN+1回避）
    q = (AmountDocument.query
    .options(
        joinedload(AmountDocument.client)
        .joinedload(Client.entrusted_book)
    )
    .order_by(
        AmountDocument.created_at.desc().nullslast(),
        AmountDocument.id.desc()
    ))

    # フィルタ：client_id があればそのクライアントに限定
    if client_id:
        q = q.filter(AmountDocument.client_id == client_id)

    # フィルタ：entrusted_book_id があれば、Client 経由で受託簿に限定
    if entrusted_book_id:
        q = (q.join(AmountDocument.client)
             .filter(Client.entrusted_book_id == entrusted_book_id))

    documents = q.all()

    # ヘッダ表示用の文脈（存在しなければ None のまま渡す）
    client = Client.query.get(client_id) if client_id else None
    # entrusted_book は直接指定が優先。無ければ client から推測（あれば）
    entrusted_book = (EntrustedBook.query.get(entrusted_book_id)
                      if entrusted_book_id
                      else (client.entrusted_book if client and client.entrusted_book_id else None))

    return render_template(
        "amount_document/index.html",
        documents=documents,
        client=client,
        entrusted_book=entrusted_book,
        form=AmountDocumentForm(),
    )


# --------------------------
# Detail（詳細）
# --------------------------
@amount_document_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    document = _get_document_or_404(document_id)

    calc = AmountDocumentCalculator(
        reward_amounts=document.reward_amounts or [],
        expense_amounts=document.expense_amounts or [],
        apply_consumption_tax=document.apply_consumption_tax,
        apply_withholding=document.apply_withholding,
    )
    totals = calc.calculate_totals(round_unit=100)

    return render_template(
        "amount_document/detail.html",
        doc_labels={"estimate": "見積", "invoice": "請求", "receipt": "領収"},
        document=document,
        totals=totals,  # 詳細画面のみ集計あり
        document_note=str.replace(str(document.note), "\\n", "\n"),
    )


# --------------------------
# Create（新規）
# --------------------------
@amount_document_bp.route("/create", methods=["GET", "POST"])
def create():
    form = AmountDocumentForm()
    client_id = request.args.get("client_id", type=int)  # クエリパラメータ client_id 必須
    if not client_id:
        flash("クライアント情報が指定されていません。", "danger")
        return redirect(url_for("client.index"))

    client = (Client.query
              .options(joinedload(Client.entrusted_book))
              .get_or_404(client_id))

    ### GET
    if request.method == "GET":
        # 受託簿名: クライアントにぶら下がる受託簿名があるなら初期値に
        if client.entrusted_book:
            form.entrusted_book_name.data = client.entrusted_book.name

        # 備考デフォルトを注入
        from apps.amount_document.config_loader import (
            get_default_entries_for_client_type,
            get_note_default_for_client_type,
        )
        form.note.data = get_note_default_for_client_type(client.client_type)

        # デフォ行注入
        defaults = get_default_entries_for_client_type(client.client_type)
        for i, (it, rw, ex) in enumerate(
                zip(defaults["item_types"], defaults["reward_amounts"], defaults["expense_amounts"])
        ):
            if i < len(form.item_types):
                form.item_types[i].data = it
                form.reward_amounts[i].data = rw
                form.expense_amounts[i].data = ex

    ### POST
    if form.validate_on_submit():
        document = AmountDocument(
            client_id=client_id,
            entrusted_book_name=form.entrusted_book_name.data,
            apply_consumption_tax=form.apply_consumption_tax.data,
            apply_withholding=form.apply_withholding.data,
            advance_payment=form.advance_payment.data,
            note=form.note.data,
            estimate_date=form.estimate_date.data,
            receipt_date=form.receipt_date.data,
            invoice_date=form.invoice_date.data,
        )
        document.set_items_normalized(
            item_types_list=[f.data for f in form.item_types],
            reward_list=[f.data for f in form.reward_amounts],
            expense_list=[f.data for f in form.expense_amounts],
        )
        db.session.add(document)
        try:
            db.session.commit()
            flash("金額文書を作成しました。")
            return redirect(url_for("amount_document.detail", document_id=document.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("金額文書の作成に失敗しました。", "error")

    return render_template(
        "amount_document/form.html",
        form=form,
        client=client,
        is_edit=False,
    )

# --------------------------
# Edit（更新）
# ---------------------------
@amount_document_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
def edit(document_id: int) -> Union[str, WerkzeugResponse]:
    document = _get_document_or_404(document_id)
    form = AmountDocumentForm(obj=document)

    #### GET
    if request.method == "GET":
        form.client_id.data = document.client_id
        items = document.get_items()
        for field_list_name in ("item_types", "reward_amounts", "expense_amounts"):
            values = items.get(field_list_name, []) or []
            field_list = getattr(form, field_list_name)
            while len(values) < len(field_list):
                values.append("" if field_list_name == "item_types" else 0)
            for fld, val in zip(field_list, values):
                fld.data = val

    #### POST
    if form.validate_on_submit():
        form.populate_obj(document)
        document.set_items_normalized(
            item_types_list=[f.data for f in form.item_types],
            reward_list=[f.data for f in form.reward_amounts],
            expense_list=[f.data for f in form.expense_amounts],
        )
        try:
            db.session.commit()
            flash("金額文書を更新しました。")
            return redirect(url_for("amount_document.detail",
                                    document_id=document.id))
        except SQLAlchemyError:
            db.session.rollback()
            flash("金額文書の更新に失敗しました。", "error")

    return render_template(
        "amount_document/form.html",
        form=form,
        document=document,
        client=document.client,  # /createは、documentオブジェクトが存在しないため、document.createを参照できない
        is_edit=True,
    )


# --------------------------
# Confirm Delete（確認）
# --------------------------
@amount_document_bp.route("/<int:document_id>/confirm_delete")
def confirm_delete(document_id: int):
    document = _get_document_or_404(document_id)
    return render_template("amount_document/confirm_delete.html", document=document)


# --------------------------
# Delete（削除）
# --------------------------
@amount_document_bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id: int) -> WerkzeugResponse:
    document = _get_document_or_404(document_id)
    try:
        db.session.delete(document)
        db.session.commit()
        flash("金額文書を削除しました。")
    except SQLAlchemyError:
        db.session.rollback()
        flash("金額文書の削除に失敗しました。", "error")
    return redirect(url_for("amount_document.index"))
