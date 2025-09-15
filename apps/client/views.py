# apps/client/views.py
from datetime import datetime, time
from flask_wtf.csrf import generate_csrf
from flask import Blueprint, render_template, redirect, url_for, flash, request
from db import db
from apps.client.models import Client
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


def _dt_to_date(dt):
    """Model DateTime -> date / None（フォーム初期表示用）"""
    if dt is None:
        return None
    return dt.date()


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
# Create（新規）
# --------------------------
@client_bp.route("/create", methods=["GET", "POST"])
def create():
    form = ClientForm()
    _set_entrusted_book_choices(form)

    # クエリから簿IDを引き継いで初期化（GET時のみ）
    pre_book_id = request.args.get("entrusted_book_id", type=int)
    if request.method == "GET" and pre_book_id:
        if EntrustedBook.query.get(pre_book_id):
            form.entrusted_book_id.data = pre_book_id

    if form.validate_on_submit():
        client = Client(
            entrusted_book_id=form.entrusted_book_id.data,
            client_type_id=form.client_type_id.data,
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
            equity_numerator=form.equity_numerator.data,     # None または int
            equity_denominator=form.equity_denominator.data, # None または int
        )
        db.session.add(client)
        db.session.commit()
        flash("Client was created.")
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

    # DateField は date 型なので上書き
    if request.method == "GET":
        form.birth_date.data = _dt_to_date(client.birth_date)
        form.intention_confirmed_at.data = _dt_to_date(client.intention_confirmed_at)

    if form.validate_on_submit():
        client.entrusted_book_id = form.entrusted_book_id.data
        client.client_type_id = form.client_type_id.data
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
        client.equity_numerator = form.equity_numerator.data    # None または int
        client.equity_denominator = form.equity_denominator.data

        db.session.commit()
        flash("Client was updated.")
        return redirect(url_for("entrusted_book.detail", book_id=client.entrusted_book_id))

    return render_template("client/form.html",
                           form=form,
                           is_edit=True,
                           title="Edit Client")

# --------------------------
# Confirm Delete（確認）
# --------------------------
@client_bp.route("/<int:client_id>/confirm_delete")
def confirm_delete(client_id):
    client = Client.query.get_or_404(client_id)
    cancel_url = request.args.get("next") or url_for(
        "entrusted_book.detail", book_id=client.entrusted_book_id
    )
    csrf_token = generate_csrf()  # ← csrf用の汎用トークン
    return render_template(
        "client/confirm_delete.html",
        client=client,
        cancel_url=cancel_url,
        csrf_token=csrf_token,
    )


# --------------------------
# Delete（削除）
# --------------------------
@client_bp.route("/<int:client_id>/delete", methods=["POST"])
def delete(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash(f"Client #{client_id} deleted.", "success")
    next_url = request.args.get("next") or url_for(
        "entrusted_book.detail", book_id=client.entrusted_book_id
    )
    return redirect(next_url)
