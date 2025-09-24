# apps/entrusted_book/views.py
from __future__ import annotations
from sqlalchemy.orm import selectinload
from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from apps.common.forms import CSRFOnlyForm
from apps.entrusted_book.forms import EntrustedBookForm
from apps.entrusted_book.models import EntrustedBook
from db import db

entrusted_book_bp = Blueprint(
    "entrusted_book",
    __name__,
    url_prefix="/entrusted-book",
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


# --------------------------
# Index（一覧）
# --------------------------
@entrusted_book_bp.route("/")
def index():
    books = EntrustedBook.query.order_by(EntrustedBook.name).all()
    return render_template("entrusted_book/index.html", books=books)


# --------------------------
# Detail（詳細）
# --------------------------
@entrusted_book_bp.route("/<int:book_id>")
def detail(book_id: int):
    book = (EntrustedBook.query
            .options(selectinload(EntrustedBook.clients))
            .get_or_404(book_id))
    return render_template("entrusted_book/overview.html", book=book, clients=book.clients)


# --------------------------
# Create（新規）
# --------------------------
@entrusted_book_bp.route("/create", methods=["GET", "POST"])
def create():
    form = EntrustedBookForm()

    if form.validate_on_submit():
        book = EntrustedBook(
            name=form.name.data,
            note=form.note.data,
            contract_date=form.contract_date.data,
            execution_date=form.execution_date.data,
        )
        db.session.add(book)
        if _commit_with_flash("受託簿を作成しました。", "受託簿の作成に失敗しました。"):
            return redirect(url_for("entrusted_book.detail", book_id=book.id), code=303)

    elif form.is_submitted():
        # バリデーションNG時の詳細メッセージ
        for field, errs in form.errors.registry_item():
            flash(f"{field}: {', '.join(errs)}", "danger")

    return render_template(
        "entrusted_book/form.html",
        form=form,
        back_url=url_for("entrusted_book.index"),
        title="Create Entrusted Book",
        is_edit=False,
    )


# --------------------------
# Edit（更新）
# --------------------------
@entrusted_book_bp.route("/<int:book_id>/edit", methods=["GET", "POST"])
def edit(book_id: int):
    book = EntrustedBook.query.get_or_404(book_id)
    form = EntrustedBookForm(obj=book)

    if form.validate_on_submit():
        form.populate_obj(book)
        if _commit_with_flash("受託簿を更新しました。", "受託簿の更新に失敗しました。"):
            return redirect(url_for("entrusted_book.detail", book_id=book.id), code=303)

    elif form.is_submitted():
        for field, errs in form.errors.registry_item():
            flash(f"{field}: {', '.join(errs)}", "danger")

    return render_template(
        "entrusted_book/form.html",
        form=form,
        back_url=url_for("entrusted_book.detail", book_id=book.id),
        title="Edit Entrusted Book",
        is_edit=True,
    )


# --------------------------
# Confirm Delete（確認）
# --------------------------
@entrusted_book_bp.route("/<int:book_id>/confirm_delete")
def confirm_delete(book_id: int):
    form = CSRFOnlyForm()  # ← これで hidden_tag() が使える
    book = EntrustedBook.query.get_or_404(book_id)
    return render_template("entrusted_book/confirm_delete.html",
                           book=book, form=form)


# --------------------------
# Delete（削除）
# --------------------------
@entrusted_book_bp.route("/<int:book_id>/delete", methods=["POST"])
def delete(book_id: int):
    from apps.common.forms import CSRFOnlyForm
    form = CSRFOnlyForm()  # confirm_delete()からおくられてきたformを再定義
    if not form.validate_on_submit():  # CSRF NG 時はここで弾ける
        flash("不正なリクエストです。（CSRF）", "danger")
        return redirect(url_for("entrusted_book.detail", book_id=book_id))

    book = EntrustedBook.query.get_or_404(book_id)
    db.session.delete(book)
    if _commit_with_flash("受託簿を削除しました。", "受託簿の削除に失敗しました。"):
        return redirect(url_for("entrusted_book.index"))
    return redirect(url_for("entrusted_book.detail", book_id=book_id))
