# apps/documents/origin/views.py
from __future__ import annotations
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from db import db
from apps.entrusted_book.models import EntrustedBook
from apps.client.models import Client
from apps.utils.common import to_zenkaku_digits
from apps.client.constants import ClientType
from apps.documents.origin.constants import CauseType
from apps.documents.origin.models import OriginDocument
from apps.documents.origin.forms import OriginDocumentForm
from apps.documents.origin.config_loader import render_cause_fact

# --------------------------
# ブループリント
# --------------------------
origin_bp = Blueprint(
    "origin",
    __name__,
    url_prefix="/documents/origin",
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


def _party_text_from_book(book) -> tuple[str, str]:
    """
    受託簿のクライアント一覧から、権利者／義務者のテキストエリア初期値を生成。
    1行のフォーマット: 「（持分）住所　氏名」
      - 持分は (equity_numerator / equity_denominator) が両方あるときのみ
      - 数字は全角に変換（to_zenkaku_digits）
      - 住所や氏名が未設定なら空文字扱い
    戻り値: (right_text, obligation_text)
    """
    if not book or not getattr(book, "clients", None):
        return "", ""

    right_lines: list[str] = []
    oblig_lines: list[str] = []

    for c in book.clients:
        # 持分（全角に変換、両方あれば付ける）
        equity = ""
        num = getattr(c, "equity_numerator", None)
        den = getattr(c, "equity_denominator", None)
        if isinstance(num, int) and isinstance(den, int) and num >= 0 and den > 0:
            num_zen = to_zenkaku_digits(str(num))
            den_zen = to_zenkaku_digits(str(den))
            equity = f"（{num_zen}／{den_zen}） "

        addr = (c.address or "").strip()
        name = (c.name or "").strip()

        line = f"{equity}{addr}　{name}".strip()

        if c.client_type == ClientType.RIGHT_HOLDER:
            right_lines.append(line)
        elif c.client_type == ClientType.OBLIGATION_HOLDER:
            oblig_lines.append(line)

    right_text = "\n".join(filter(None, right_lines))
    oblig_text = "\n".join(filter(None, oblig_lines))
    return right_text, oblig_text

def _pack_descriptions(form) -> list[str]:
    """フォームの左右欄をJSON配列に詰める（空は落とす）"""
    s1 = (form.real_estate_description_1.data or "").strip()
    s2 = (form.real_estate_description_2.data or "").strip()
    out = []
    if s1: out.append(s1)
    if s2: out.append(s2)
    # どちらも空なら空配列（DB側は NOT NULL だが default=list なのでOK）
    return out

def _unpack_descriptions(doc) -> tuple[str, str]:
    """モデルのJSON配列を左右２欄に展開"""
    parts = (doc.real_estate_descriptions or [])
    left  = parts[0] if len(parts) > 0 else ""
    right = parts[1] if len(parts) > 1 else ""
    return left, right

# --------------------------
# Index（一覧）
# --------------------------
@origin_bp.route("/")
def index() -> str:
    client_id = request.args.get("client_id", type=int)
    q = (
        OriginDocument.query
        .options(joinedload(OriginDocument.client))
        .order_by(OriginDocument.created_at.desc(), OriginDocument.id.desc())
    )
    if client_id:
        q = q.filter(OriginDocument.client_id == client_id)

    documents = q.all()
    return render_template(
        "origin/index.html",
        documents=documents,
        client_id=client_id,
    )


# --------------------------
# Detail（詳細）
# --------------------------
@origin_bp.route("/<int:document_id>")
def detail(document_id: int) -> str:
    doc = (
        OriginDocument.query
        .options(joinedload(OriginDocument.client))
        .get_or_404(document_id)
    )
    return render_template("origin/detail.html", document=doc)


# --------------------------
# Create（新規）
# --------------------------
@origin_bp.route("/create", methods=["GET", "POST"])
def create():
    form = OriginDocumentForm()
    client_id = request.args.get("client_id", type=int)
    if not client_id:
        flash("クライアントが指定されていません。", "danger")
        return redirect(url_for("client.index"))

    client = Client.query.get_or_404(client_id)
    form.client_id.data = client.id
    back_url = request.args.get("back") or url_for("client.documents_index", client_id=client.id)

    book = client.entrusted_book

    if request.method == "GET":
        # 当事者初期値
        right_txt, oblig_txt = _party_text_from_book(book)
        form.right_holders.data = right_txt
        form.obligation_holders.data = oblig_txt

        # 不動産の表示（新規は空のまま：左右どちらにも入れられる）
        form.real_estate_description_1.data = ""
        form.real_estate_description_2.data = ""

        # 登記原因の初期値
        form.cause_type.data = CauseType.SALE.value
        form.cause_suffix.data = ""
        form.cause_fact.data = render_cause_fact(
            CauseType.from_id(form.cause_type.data),
            contract_date=book.contract_date,
            execution_date=book.execution_date,
        )

    if form.validate_on_submit():
        doc = OriginDocument(
            client_id=client.id,
            real_estate_descriptions=_pack_descriptions(form),  # ← ここ！
            right_holders=form.right_holders.data or "",
            obligation_holders=form.obligation_holders.data or "",
            cause_type_id=form.cause_type.data,
            cause_fact=form.cause_fact.data or "",
        )
        db.session.add(doc)
        if _commit_with_flash("登記原因証明情報を作成しました。", "登記原因証明情報の作成に失敗しました。"):
            return redirect(url_for("origin.detail", document_id=doc.id), code=303)

    elif form.is_submitted():
        for field, errs in form.errors.items():
            flash(f"{field}: {', '.join(errs)}", "danger")

    return render_template(
        "origin/form.html",
        form=form,
        client=client,
        is_edit=False,
        back_url=back_url,
    )


# --------------------------
# Edit（更新）
# --------------------------
@origin_bp.route("/<int:document_id>/edit", methods=["GET", "POST"])
def edit(document_id: int):
    doc = (
        OriginDocument.query
        .options(joinedload(OriginDocument.client))
        .get_or_404(document_id)
    )
    form = OriginDocumentForm(obj=doc)
    form.client_id.data = doc.client_id

    if request.method == "GET":
        # 既存のJSON配列を左右欄に復元
        left, right = _unpack_descriptions(doc)
        form.real_estate_description_1.data = left
        form.real_estate_description_2.data = right

    if form.validate_on_submit():
        # 左右欄 -> JSON配列
        doc.real_estate_descriptions = _pack_descriptions(form)
        doc.right_holders = form.right_holders.data or ""
        doc.obligation_holders = form.obligation_holders.data or ""
        doc.cause_type_id = form.cause_type.data
        doc.cause_fact = form.cause_fact.data or ""

        if _commit_with_flash("登記原因証明情報を更新しました。", "登記原因証明情報の更新に失敗しました。"):
            return redirect(url_for("origin.detail", document_id=doc.id))

    return render_template(
        "origin/form.html",
        form=form,
        document=doc,
        client=doc.client,
        is_edit=True,
    )


# --------------------------
# Confirm Delete（確認）
# --------------------------
@origin_bp.route("/<int:document_id>/confirm_delete")
def confirm_delete(document_id: int) -> str:
    doc = OriginDocument.query.get_or_404(document_id)
    cancel_url = url_for("documents.index", client_id=doc.client_id)
    return render_template("origin/confirm_delete.html",
                           document=doc,
                           cancel_url=cancel_url)


# --------------------------
# Delete（削除）
# --------------------------
@origin_bp.route("/<int:document_id>/delete", methods=["POST"])
def delete(document_id: int):
    doc = OriginDocument.query.get_or_404(document_id)
    client_id = doc.client_id
    db.session.delete(doc)
    if _commit_with_flash("登記原因証明情報を削除しました。", "登記原因証明情報の削除に失敗しました。"):
        return redirect(url_for("documents.index", client_id=client_id))
    return redirect(url_for("origin.detail", document_id=doc.id))
