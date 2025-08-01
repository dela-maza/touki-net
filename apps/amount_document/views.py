### amount_document/views.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, Response
from db import db
from apps.entrusted_book.models import EntrustedBook
from apps.amount_document.forms import AmountDocumentForm
from apps.amount_document.models import AmountDocument
from apps.client.models import Client
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Any, Dict, Union, Optional

amount_document_bp = Blueprint(
    "amount_document", __name__, url_prefix="/amount-document", template_folder="templates", static_folder="static"
)


def get_document_or_404(document_id: int) -> AmountDocument:
    """共通のAmountDocument取得処理"""
    return AmountDocument.query.get_or_404(document_id)


def populate_form_items(form: AmountDocumentForm, items: Dict[str, list]) -> None:
    """フォームの明細欄に既存データをセット（JSONBなのでそのまま代入）"""
    for field_list_name in ("item_types", "reward_amounts", "expense_amounts"):
        data_list = items.get(field_list_name, [])
        form_field_list = getattr(form, field_list_name, [])
        for i, value in enumerate(data_list):
            if i < len(form_field_list):
                form_field_list[i].data = value


def extract_items_from_form(form: AmountDocumentForm) -> Dict[str, list]:
    """フォームから明細リストを抽出"""
    return {
        "item_types_list": [field.data for field in form.item_types],
        "reward_list": [field.data for field in form.reward_amounts],
        "expense_list": [field.data for field in form.expense_amounts],
    }


def commit_session_with_flash(success_message: str, error_message: str) -> bool:
    """DBコミット処理とフラッシュメッセージ表示の共通化"""
    try:
        db.session.commit()
        flash(success_message)
        return True
    except SQLAlchemyError:
        db.session.rollback()
        flash(error_message, "error")
        return False


@amount_document_bp.route("/")
def index() -> str:
    documents = AmountDocument.query.order_by(
        AmountDocument.issued_date.desc().nullslast(), AmountDocument.id.desc()
    ).all()
    return render_template("amount_document/index.html", documents=documents)


@amount_document_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    document = get_document_or_404(document_id)
    return render_template("amount_document/detail.html", document=document)


@amount_document_bp.route("/create", methods=["GET", "POST"])
def create() -> Union[str, WerkzeugResponse]:
    form = AmountDocumentForm()
    client_id: Optional[int] = request.args.get("client_id", type=int)
    entrusted_book_id: Optional[int] = request.args.get("entrusted_book_id", type=int)

    if client_id:
        client = Client.query.get(client_id)
        if client:
            form.client_id.data = client_id
            form.client_name.data = client.name

    if entrusted_book_id:
        entrusted_book = EntrustedBook.query.get(entrusted_book_id)
        if entrusted_book:
            form.entrusted_book_name.data = entrusted_book.name

    if form.validate_on_submit():
        document = AmountDocument(
            client_id=form.client_id.data,
            document_type=form.document_type.data,
            entrusted_book_name=form.entrusted_book_name.data,
            has_stamp=form.has_stamp.data,
            apply_consumption_tax=form.apply_consumption_tax.data,
            apply_withholding=form.apply_withholding.data,
            advance_payment=form.advance_payment.data,
            note=form.note.data,
            issued_date=form.issued_date.data,
        )
        items = extract_items_from_form(form)
        document.set_items(
            item_types_list=items["item_types_list"],
            reward_list=items["reward_list"],
            expense_list=items["expense_list"],
        )
        db.session.add(document)
        if commit_session_with_flash("金額文書を作成しました。", "金額文書の作成に失敗しました。"):
            return redirect(url_for("amount_document.detail", document_id=document.id))

    return render_template("amount_document/form.html", form=form)


@amount_document_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
def edit(document_id: int) -> Union[str, WerkzeugResponse]:
    document = get_document_or_404(document_id)
    form = AmountDocumentForm(obj=document)

    if request.method == "GET":
        populate_form_items(form, document.get_items())

    if form.validate_on_submit():
        form.populate_obj(document)
        items = extract_items_from_form(form)
        document.set_items(
            item_types_list=items["item_types_list"],
            reward_list=items["reward_list"],
            expense_list=items["expense_list"],
        )
        if commit_session_with_flash("金額文書を更新しました。", "金額文書の更新に失敗しました。"):
            return redirect(url_for("amount_document.detail", document_id=document.id))

    return render_template("amount_document/form.html", form=form)


@amount_document_bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id: int) -> WerkzeugResponse:
    document = get_document_or_404(document_id)
    try:
        db.session.delete(document)
        db.session.commit()
        flash("金額文書を削除しました。")
    except SQLAlchemyError:
        db.session.rollback()
        flash("金額文書の削除に失敗しました。", "error")
    return redirect(url_for("amount_document.index"))
