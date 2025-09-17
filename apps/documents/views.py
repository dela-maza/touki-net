# apps/documents/views.py
from typing import Optional
from flask import Blueprint, render_template, request
from sqlalchemy import select, literal, union_all, and_
from db import db
from apps.entrusted_book.models import EntrustedBook
from apps.client.models import Client
from apps.documents.constants import DocumentType
from apps.documents.amount.models import AmountDocument
from apps.documents.required.models import RequiredDocument
from apps.documents.delivery.models import DeliveryDocument
from apps.documents.origin.models import OriginDocument

# --------------------------
# ブループリント
# --------------------------
documents_bp = Blueprint(
    "documents",
    __name__,
    url_prefix="/documents",
    template_folder="templates",
    static_folder="static",
)

# --------------------------
# Index（一覧）
# --------------------------
@documents_bp.route("/")
def index():
    # クエリ取得（任意）
    client_id: Optional[int] = request.args.get("client_id", type=int)
    entrusted_book_id: Optional[int] = request.args.get("entrusted_book_id", type=int)

    client = Client.query.get(client_id) if client_id is not None else None
    if entrusted_book_id is not None:
        entrusted_book = EntrustedBook.query.get(entrusted_book_id)
    else:
        entrusted_book = client.entrusted_book if client and client.entrusted_book_id else None

    # ---- Amount Document（金銭帳票） ----
    a = (
        select(
            AmountDocument.id.label("id"),
            AmountDocument.entrusted_book_name.label("title"),
            AmountDocument.created_at.label("created_at"),
            literal(DocumentType.AMOUNT.value).label("document_type"),
        )
        .join(Client, AmountDocument.client_id == Client.id)
    )

    # ---- Required Document（必要書類） ----
    r = (
        select(
            RequiredDocument.id.label("id"),
            RequiredDocument.entrusted_book_name.label("title"),
            RequiredDocument.created_at.label("created_at"),
            literal(DocumentType.REQUIRED.value).label("document_type"),
        )
        .join(Client, RequiredDocument.client_id == Client.id)
    )

    # ---- Delivery Document（納品書） ----
    d = (
        select(
            DeliveryDocument.id.label("id"),
            DeliveryDocument.entrusted_book_name.label("title"),
            DeliveryDocument.created_at.label("created_at"),
            literal(DocumentType.DELIVERY.value).label("document_type"),  # ★ enum に DELIVERY が必要
        )
        .join(Client, DeliveryDocument.client_id == Client.id)
    )

    # ---- Origin Document（登記原因証明情報）----
    o = (
        select(
            OriginDocument.id.label("id"),
            # タイトルはとりあえず「不動産の表示」にしておく（長ければ後で省略表示）
            OriginDocument.real_estate_description.label("title"),
            OriginDocument.created_at.label("created_at"),
            literal(DocumentType.ORIGIN.value).label("document_type"),
        )
        .join(Client, OriginDocument.client_id == Client.id)
    )

    # ---- フィルタ ----
    if client_id is not None:
        a = a.where(and_(AmountDocument.client_id == client_id))
        r = r.where(and_(RequiredDocument.client_id == client_id))
        d = d.where(and_(DeliveryDocument.client_id == client_id))
        o = o.where(and_(OriginDocument.client_id == client_id))

    if entrusted_book_id:
        a = a.where(and_(Client.entrusted_book_id == entrusted_book_id))
        r = r.where(and_(Client.entrusted_book_id == entrusted_book_id))
        d = d.where(and_(Client.entrusted_book_id == entrusted_book_id))
        o = o.where(and_(Client.entrusted_book_id == entrusted_book_id))


    # ---- UNION（amount / required / delivery / origin）----
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
        "documents/index.html",
        documents=documents,
        entrusted_book=entrusted_book,
        client=client,
    )