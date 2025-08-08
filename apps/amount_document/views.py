### amount_document/views.py
# from pprint import pprint
from flask import Blueprint, render_template, flash, redirect, url_for, request
from db import db
from apps.entrusted_book.models import EntrustedBook
from apps.amount_document.calculator import AmountDocumentCalculator
from apps.amount_document.forms import AmountDocumentForm
from apps.amount_document.models import AmountDocumentType, AmountDocument
from apps.client.models import Client
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Dict, Union, Optional
from apps.amount_document.config_loader import load_config

param = load_config()["OFFICE"]

amount_document_bp = Blueprint(
    "amount_document", __name__, url_prefix="/amount-document", template_folder="templates", static_folder="static"
)


def get_document_or_404(document_id: int) -> AmountDocument:
    return AmountDocument.query.get_or_404(document_id)


def populate_form_items(form: AmountDocumentForm, items: Dict[str, list]) -> None:
    for field_list_name in ("item_types", "reward_amounts", "expense_amounts"):
        data_list = items.get(field_list_name, [])
        form_field_list = getattr(form, field_list_name, [])
        for i, value in enumerate(data_list):
            if i < len(form_field_list):
                form_field_list[i].data = value


def extract_items_from_form(form: AmountDocumentForm) -> Dict[str, list]:
    return {
        "item_types_list": [field.data for field in form.item_types],
        "reward_list": [field.data for field in form.reward_amounts],
        "expense_list": [field.data for field in form.expense_amounts],
    }


def commit_session_with_flash(success_message: str, error_message: str) -> bool:
    try:
        db.session.commit()
        flash(success_message)
        return True
    except SQLAlchemyError:
        db.session.rollback()
        flash(error_message, "error")
        return False


# ============================================= / =============================================
@amount_document_bp.route("/")
def index() -> str:
    documents = AmountDocument.query.order_by(
        AmountDocument.created_at.desc().nullslast(), AmountDocument.id.desc()
    ).all()
    return render_template("amount_document/index.html",
                           documents=documents,
                           form=AmountDocumentForm(),  # 空フォームを生成（CSRFトークン用）
                           )


# ============================================= /detail =============================================
@amount_document_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    document = get_document_or_404(document_id)
    client_name = document.client.name if document.client else ""
    # AmountDocumentCalculatorのインスタンスを生成して計算済み合計値を取得
    calc = AmountDocumentCalculator(
        reward_amounts=document.reward_amounts or [],
        expense_amounts=document.expense_amounts or [],
        apply_consumption_tax=document.apply_consumption_tax,
        apply_withholding=document.apply_withholding,
    )
    display_totals = calc.get_display_totals()

    return render_template(
        "amount_document/detail.html",
        AmountDocumentType=AmountDocumentType,
        document=document,
        document_type_label=AmountDocumentType.ESTIMATE.label,
        document_note=str.replace(str(document.note), '\\n', '\n'),
        param=load_config()["OFFICE"],
        client_name=client_name,
        tax_config=AmountDocumentCalculator.get_tax_config(),
        display_totals=display_totals,
    )


# ============================================= /create =============================================
@amount_document_bp.route("/create", methods=["GET", "POST"])
def create() -> Union[str, WerkzeugResponse]:
    form = AmountDocumentForm()
    client_id: Optional[int] = request.args.get("client_id", type=int)

    if not client_id:
        flash("クライアント情報が指定されていません。", "danger")
        return redirect(url_for("client.index"))

    entrusted_book_id: Optional[int] = request.args.get("entrusted_book_id", type=int)
    client_name = ""

    # クライアント取得
    if client_id:
        client = Client.query.get(client_id)
        if client:
            form.client_id.data = client_id
            client_name = client.name

            # クライアント種別に応じたデフォルトエントリを設定
            from apps.amount_document.config_loader import get_default_entries_for_client_type
            default_entries = get_default_entries_for_client_type(client.client_type)

            # デフォルト値をセット
            for i, (item_type, reward, expense) in enumerate(zip(
                    default_entries["item_types"],
                    default_entries["reward_amounts"],
                    default_entries["expense_amounts"]
            )):
                if i < len(form.item_types):
                    form.item_types[i].data = item_type
                    form.reward_amounts[i].data = reward
                    form.expense_amounts[i].data = expense

    if entrusted_book_id:
        entrusted_book = EntrustedBook.query.get(entrusted_book_id)
        if entrusted_book:
            form.entrusted_book_name.data = entrusted_book.name

    # 備考の初期値設定
    from apps.amount_document.config_loader import get_note_default_by_document_type

    if form.validate_on_submit():
        document = AmountDocument(
            client_id=form.client_id.data,
            entrusted_book_name=form.entrusted_book_name.data,
            apply_consumption_tax=form.apply_consumption_tax.data,
            apply_withholding=form.apply_withholding.data,
            advance_payment=form.advance_payment.data,
            note=form.note.data,
            estimate_date=form.estimate_date.data,
            receipt_date=form.receipt_date.data,
            invoice_date=form.invoice_date.data,
        )
        items = extract_items_from_form(form)
        document.set_items(
            item_types_list=items["item_types_list"],
            reward_list=items["reward_list"],
            expense_list=items["expense_list"],
        )
        db.session.add(document)
        if commit_session_with_flash("金額文書を作成しました。",
                                     "金額文書の作成に失敗しました。"):
            return redirect(url_for("amount_document.detail", document_id=document.id))

    _param = load_config()["OFFICE"]
    document_type_label = dict(form.document_type.choices).get(form.document_type.data, "")
    return render_template("amount_document/form.html",
                           form=form,
                           document=None,
                           document_type_label=document_type_label,
                           param=_param,
                           client_name=client_name,
                           tax_config=AmountDocumentCalculator.get_tax_config())


# ============================================= /edit =============================================
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

    _param = load_config()["OFFICE"]
    client_name = document.client.name if document.client else ""

    # AmountDocumentCalculatorのインスタンスを生成して計算済み合計値を取得
    calc = AmountDocumentCalculator(
        reward_amounts=document.reward_amounts or [],
        expense_amounts=document.expense_amounts or [],
        apply_consumption_tax=document.apply_consumption_tax,
        apply_withholding=document.apply_withholding,
    )
    display_totals = calc.get_display_totals()

    return render_template(
        "amount_document/form.html",
        form=form,
        document=document,
        param=_param,
        client_name=client_name,
        tax_config=AmountDocumentCalculator.get_tax_config(),
        display_totals=display_totals  # 計算済みの合計値をテンプレートに渡す
    )


# ============================================= /delete =============================================
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
