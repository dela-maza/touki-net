### apps/client/views.py
from datetime import datetime, time
from apps.common.forms import CSRFOnlyForm
from flask import Blueprint, render_template, redirect, url_for, flash, request
from db import db
from sqlalchemy import select, literal, union_all, and_
from apps.documents.amount.models import AmountDocument
from apps.documents.required.models import RequiredDocument
from apps.documents.delivery.models import DeliveryDocument
from apps.documents.origin.models import OriginDocument
from apps.documents.constants import DocumentType
from apps.client.models import Client, CorporateProfile
from apps.client.forms import CorporateProfileForm,AddressChangeForm
from apps.client.constants import EntityType
from apps.entrusted_book.models import EntrustedBook
from apps.client.forms import ClientForm

# --------------------------
# ブループリント
# --------------------------
client_bp = Blueprint(
    "client",
    __name__,
    url_prefix="/clients",
    template_folder="templates",
    static_folder="static",
)


# --------------------------
# 内部ユーティリティ
# --------------------------
def _date_to_dt(d):
    """WTForms DateField(date) -> datetime(yyyy-mm-dd 00:00) / None"""
    if d is None:
        return None
    return datetime.combine(d, time.min)


# --- 安全側: dtがdateだった場合も素通りに ---
def _dt_to_date(dt):
    """Model DateTime|date -> date / None（フォーム初期表示用）"""
    if dt is None:
        return None
    return dt.date() if hasattr(dt, "date") else dt


def _set_entrusted_book_choices(form: ClientForm):
    books = EntrustedBook.query.order_by(EntrustedBook.name.asc()).all()
    # 名前がNoneの時は #ID で補完
    form.entrusted_book_id.choices = [(b.id, b.name or f"Book #{b.id}") for b in books]


# --------------------------
# Index（一覧）
# --------------------------
@client_bp.route("/")
def index():
    clients = Client.query.order_by(Client.updated_at.desc()).all()
    return render_template("client/index.html", clients=clients)


# --------------------------
# documents list
# --------------------------
@client_bp.route("/<int:client_id>/documents")
def documents_index(client_id: int):
    client = Client.query.get_or_404(client_id)

    a = (
        select(
            AmountDocument.id.label("id"),
            AmountDocument.entrusted_book_name.label("title"),
            AmountDocument.created_at.label("created_at"),
            literal(DocumentType.AMOUNT.value).label("document_type"),
        )
        .where(and_(AmountDocument.client_id == client_id))
    )

    r = (
        select(
            RequiredDocument.id.label("id"),
            RequiredDocument.entrusted_book_name.label("title"),
            RequiredDocument.created_at.label("created_at"),
            literal(DocumentType.REQUIRED.value).label("document_type"),
        )
        .where(and_(RequiredDocument.client_id == client_id))
    )

    d = (
        select(
            DeliveryDocument.id.label("id"),
            DeliveryDocument.entrusted_book_name.label("title"),
            DeliveryDocument.created_at.label("created_at"),
            literal(DocumentType.DELIVERY.value).label("document_type"),
        )
        .where(and_(DeliveryDocument.client_id == client_id))
    )

    o = (
        select(
            OriginDocument.id.label("id"),
            OriginDocument.real_estate_description.label("title"),
            OriginDocument.created_at.label("created_at"),
            literal(DocumentType.ORIGIN.value).label("document_type"),
        )
        .where(and_(OriginDocument.client_id == client_id))
    )

    union_q = union_all(a, r, d, o).subquery()

    q = (
        db.session.query(
            union_q.c.id,
            union_q.c.title,
            union_q.c.created_at,
            union_q.c.document_type,
        )
        .order_by(union_q.c.created_at.desc(), union_q.c.id.desc())
    )

    documents = q.all()

    return render_template(
        "client/documents_index.html",
        documents=documents,
        client=client,  # ← 見出しで名前出す等に使える
        entrusted_book=client.entrusted_book,  # ← 必要なら
    )


# --------------------------
# Create（新規）
# --------------------------
@client_bp.route("/create", methods=["GET", "POST"])
def create():
    form = ClientForm()
    _set_entrusted_book_choices(form)

    pre_book_id = request.args.get("entrusted_book_id", type=int)
    if request.method == "GET" and pre_book_id:
        if EntrustedBook.query.get(pre_book_id):
            form.entrusted_book_id.data = pre_book_id

    if form.validate_on_submit():
        client = Client(
            entrusted_book_id=form.entrusted_book_id.data,
            client_type_id=form.client_type_id.data,
            entity_type_id=form.entity_type_id.data,
            name=form.name.data,
            name_kana=form.name_kana.data,
            birth_date=_date_to_dt(form.birth_date.data),
            postal_code=form.postal_code.data,
            address=form.address.data,
            phone_number=form.phone_number.data,
            fax=form.fax.data,
            email=form.email.data,
            intention_confirmed_at=_date_to_dt(form.intention_confirmed_at.data),
            note=form.note.data,
            equity_numerator=form.equity_numerator.data,
            equity_denominator=form.equity_denominator.data,
        )
        db.session.add(client)
        db.session.commit()
        flash("Client was created.", "success")
        return redirect(url_for("entrusted_book.detail", book_id=client.entrusted_book_id))

    return render_template("client/form.html", form=form, title="New Client")


# --------------------------
# Edit（更新）
# --------------------------
@client_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
def edit(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    _set_entrusted_book_choices(form)

    if request.method == "GET":
        form.birth_date.data = client.birth_date
        form.intention_confirmed_at.data = _dt_to_date(client.intention_confirmed_at)

    if form.validate_on_submit():
        client.entrusted_book_id = form.entrusted_book_id.data
        client.client_type_id = form.client_type_id.data
        client.entity_type_id = form.entity_type_id.data
        client.name = form.name.data
        client.name_kana = form.name_kana.data
        client.birth_date = _date_to_dt(form.birth_date.data)
        client.postal_code = form.postal_code.data
        client.address = form.address.data
        client.phone_number = form.phone_number.data
        client.fax = form.fax.data
        client.email = form.email.data
        client.intention_confirmed_at = _date_to_dt(form.intention_confirmed_at.data)
        client.note = form.note.data
        client.equity_numerator = form.equity_numerator.data
        client.equity_denominator = form.equity_denominator.data

        db.session.commit()
        flash("Client was updated.", "success")
        return redirect(url_for("entrusted_book.detail", book_id=client.entrusted_book_id))

    return render_template("client/form.html", form=form, is_edit=True, title="Edit Client")


# --------------------------
# Confirm Delete（確認）
# --------------------------
@client_bp.route("/<int:client_id>/confirm_delete")
def confirm_delete(client_id):
    client = Client.query.get_or_404(client_id)
    cancel_url = request.args.get("next") or url_for(
        "entrusted_book.detail", book_id=client.entrusted_book_id
    )
    form = CSRFOnlyForm()  # ← ここを追加（generate_csrf は不要）
    return render_template(
        "client/confirm_delete.html",
        client=client,
        cancel_url=cancel_url,
        form=form,  # ← これを渡す
    )


# --------------------------
# Delete（削除）
# --------------------------
@client_bp.route("/<int:client_id>/delete", methods=["POST"])
def delete(client_id):
    form = CSRFOnlyForm()
    client = Client.query.get_or_404(client_id)  # ★先に取得
    cancel_url = request.args.get("next") or url_for(
        "entrusted_book.detail", book_id=client.entrusted_book_id  # ★book_idにclient_idを入れていたのを修正
    )
    if not form.validate_on_submit():
        flash("不正なリクエストです。（CSRF）", "danger")
        return redirect(cancel_url)

    db.session.delete(client)
    db.session.commit()
    flash(f"Client #{client_id} deleted.", "success")
    return redirect(url_for("entrusted_book.detail", book_id=client.entrusted_book_id))
