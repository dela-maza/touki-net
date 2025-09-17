# apps/client/models.py
from apps.client.constants import ClientType
from datetime import datetime
from db import db
from enum import Enum

# 定数
MAX_LEN_NAME = 255
MAX_LEN_POSTAL = 20
MAX_LEN_PHONE = 50
MAX_LEN_EMAIL = 255


class Client(db.Model):
    """クライアント情報モデル"""
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    client_type_id = db.Column(db.Integer, nullable=False, default=ClientType.RIGHT_HOLDER.value)
    name = db.Column(db.String(MAX_LEN_NAME), nullable=False)
    name_kana = db.Column(db.String(MAX_LEN_NAME), nullable=True)
    # 持分（NULLなら未設定）
    equity_numerator = db.Column(db.Integer, nullable=True)  # 分子 (>=0)
    equity_denominator = db.Column(db.Integer, nullable=True)  # 分母 (>0)

    birth_date = db.Column(db.Date, nullable=True)
    postal_code = db.Column(db.String(MAX_LEN_POSTAL), nullable=True)
    address = db.Column(db.String(MAX_LEN_NAME), nullable=True)
    phone_number = db.Column(db.String(MAX_LEN_PHONE), nullable=True)
    fax = db.Column(db.String(MAX_LEN_PHONE), nullable=True)
    email = db.Column(db.String(MAX_LEN_EMAIL), nullable=True)
    intention_confirmed_at = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # EntrustBook(1)-Client(他）とのリレーション
    entrusted_book_id = db.Column(
        db.Integer,
        db.ForeignKey('entrusted_book.id'),
        nullable=False)
    entrusted_book = db.relationship(
        'EntrustedBook',
        back_populates='clients')

    # AmountDocument(多)-Client(1) リレーション
    amount_documents = db.relationship(
        'AmountDocument',
        back_populates='client',
        cascade="all, delete-orphan")

    # RequiredDocument(多)-Client(1) リレーション
    required_documents = db.relationship(
        "RequiredDocument",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    # DeliveryDocument(多)-Client(1) リレーション
    delivery_documents = db.relationship(
        "DeliveryDocument",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    # OriginDocument(多)-Client(1) リレーション ← ★追加
    origin_documents = db.relationship(
        "OriginDocument",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    @property
    def client_type(self) -> ClientType:
        """Enumとしてのクライアント種別"""
        return ClientType.from_id(self.client_type_id)

    def __repr__(self):
        return f"<Client id={self.id} name={self.name} type={self.client_type.label}>"
