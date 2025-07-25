
### entrusted_book/view.py
from flask import Blueprint, render_template, redirect, url_for, flash
from apps.entrusted_book.forms import EntrustedBookForm
from apps.entrusted_book.models import EntrustedBook
from db import db

entrusted_book_bp = Blueprint(
    'entrusted_book',
    __name__,
    url_prefix='/entrusted-book',
    template_folder='templates',
    static_folder='static'
)


@entrusted_book_bp.route('/')
def index():
    books = EntrustedBook.query.order_by(EntrustedBook.name).all()
    return render_template('entrusted_book/index.html', books=books)


@entrusted_book_bp.route('/create', methods=['GET', 'POST'])
def create():
    form = EntrustedBookForm()
    if form.validate_on_submit():
        book = EntrustedBook(
            name=form.name.data,
            note=form.note.data
        )
        db.session.add(book)
        db.session.commit()
        flash('受託簿を作成しました。')
        return redirect(url_for('entrusted_book.index'))
    return render_template('entrusted_book/form.html', form=form)


@entrusted_book_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
def edit(book_id):
    book = EntrustedBook.query.get_or_404(book_id)
    form = EntrustedBookForm(obj=book)
    if form.validate_on_submit():
        form.populate_obj(book)
        db.session.commit()
        flash('受託簿情報を更新しました。')
        return redirect(url_for('entrusted_book.index'))
    return render_template('entrusted_book/form.html', form=form)

@entrusted_book_bp.route('/<int:book_id>')
def detail(book_id):
    book = EntrustedBook.query.get_or_404(book_id)
    return render_template('entrusted_book/detail.html', book=book)

@entrusted_book_bp.route('/<int:book_id>/confirm_delete')
def confirm_delete(book_id):
    form = EntrustedBookForm()
    book = EntrustedBook.query.get_or_404(book_id)
    return render_template('entrusted_book/confirm_delete.html', book=book,form=form)


@entrusted_book_bp.route('/<int:book_id>/delete', methods=['POST'])
def delete(book_id):
    book = EntrustedBook.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('受託簿を削除しました。')
    return redirect(url_for('entrusted_book.index'))