### client/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from db import db  # SQLAlchemyインスタンス
from apps.client.forms import ClientForm
from apps.client.models import Client
from apps.entrusted_book.models import EntrustedBook

client_bp = Blueprint('client', __name__, url_prefix='/client', template_folder='templates', static_folder='static')


@client_bp.route('/')
def index():
    clients = Client.query.order_by(Client.name).all()

    class DeleteForm(FlaskForm):
        pass

    delete_form = DeleteForm()
    return render_template('client/index.html', clients=clients, delete_form=delete_form)


@client_bp.route('/<int:client_id>')
def detail(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm()
    return render_template('client/detail.html', client=client,form=form)


@client_bp.route('/create', methods=['GET', 'POST'])
def create():
    form = ClientForm()
    form.entrusted_book_id.choices = [(b.id, b.property_name) for b in
                                      EntrustedBook.query.order_by(EntrustedBook.property_name).all()]

    if form.validate_on_submit():
        client = Client(
            entrusted_book_id=form.entrusted_book_id.data,
            client_type_id=form.client_type_id.data,
            name=form.name.data,
            name_furigana=form.name_furigana.data,
            birth_date=form.birth_date.data,
            postal_code=form.postal_code.data,
            address=form.address.data,
            phone_number=form.phone_number.data,
            fax=form.fax.data,
            email=form.email.data,
            intention_confirmed_at=form.intention_confirmed_at.data,
            note=form.note.data
        )
        db.session.add(client)
        db.session.commit()
        flash('クライアントを作成しました。')
        return redirect(url_for('client.detail', client_id=client.id))
    return render_template('client/form.html', form=form, action='create')


@client_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
def edit(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    form.entrusted_book_id.choices = [(b.id, b.property_name) for b in
                                      EntrustedBook.query.order_by(EntrustedBook.property_name).all()]

    if form.validate_on_submit():
        form.populate_obj(client)
        db.session.commit()
        flash('クライアント情報を更新しました。')
        return redirect(url_for('client.detail', client_id=client.id))
    return render_template('client/form.html', form=form, action='edit')


@client_bp.route('/<int:client_id>/delete', methods=['POST'])
def delete(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash('クライアントを削除しました。')
    return redirect(url_for('client.index'))
