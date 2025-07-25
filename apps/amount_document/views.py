### amount_document/views.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from db import db
from apps.entrusted_book.models import EntrustedBook

from apps.amount_document.forms import AmountDocumentForm
from apps.amount_document.models import AmountDocument
from apps.client.models import Client

amount_document_bp = Blueprint(
    'amount_document',
    __name__,
    url_prefix='/amount-document',
    template_folder='templates',
    static_folder='static'
)


@amount_document_bp.route('/')
def index():
    documents = AmountDocument.query.order_by(AmountDocument.issued_date.desc().nullslast(),
                                              AmountDocument.id.desc()).all()
    return render_template('amount_document/index.html', documents=documents)


@amount_document_bp.route('/<int:document_id>')
def detail(document_id):
    document = AmountDocument.query.get_or_404(document_id)
    return render_template('amount_document/detail.html', document=document)


@amount_document_bp.route('/create', methods=['GET', 'POST'])
def create():
    form = AmountDocumentForm()
    client_id = request.args.get('client_id', type=int)
    entrusted_book_id = request.args.get('entrusted_book_id', type=int)


    if client_id:
        form.client_id.data = client_id
        client = Client.query.get(client_id)
        if client:
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
            issued_date=form.issued_date.data
        )
        # 明細のセット
        document.set_items(
            item_types_list=[field.data for field in form.item_types],
            reward_list=[field.data for field in form.reward_amounts],
            expense_list=[field.data for field in form.expense_amounts]
        )
        db.session.add(document)
        db.session.commit()
        flash('金額文書を作成しました。')
        return redirect(url_for('amount_document.detail', document_id=document.id))
    return render_template('amount_document/form.html', form=form)


@amount_document_bp.route('/<int:document_id>/edit', methods=['GET', 'POST'])
def edit(document_id):
    document = AmountDocument.query.get_or_404(document_id)
    form = AmountDocumentForm(obj=document)

    # フォームの明細欄に既存データをセット
    items = document.get_items()
    for i, item_type in enumerate(items.get('item_types', [])):
        if i < len(form.item_types):
            form.item_types[i].data = item_type
    for i, reward in enumerate(items.get('reward_amounts', [])):
        if i < len(form.reward_amounts):
            form.reward_amounts[i].data = reward
    for i, expense in enumerate(items.get('expense_amounts', [])):
        if i < len(form.expense_amounts):
            form.expense_amounts[i].data = expense

    if form.validate_on_submit():
        form.populate_obj(document)  # populate（充填する）：フォームの各フィールドの値を document の対応する属性にセットする
        # 例： document.document_type = form.document_type.data など
        document.set_items(
            item_types_list=[field.data for field in form.item_types],
            reward_list=[field.data for field in form.reward_amounts],
            expense_list=[field.data for field in form.expense_amounts]
        )
        db.session.commit()
        flash('金額文書を更新しました。')
        return redirect(url_for('amount_document.detail', document_id=document.id))
    return render_template('amount_document/form.html', form=form)


@amount_document_bp.route('/<int:document_id>/delete', methods=['POST'])
def delete(document_id):
    document = AmountDocument.query.get_or_404(document_id)
    db.session.delete(document)
    db.session.commit()
    flash('金額文書を削除しました。')
    return redirect(url_for('amount_document.index'))
