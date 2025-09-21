# apps/client/models.py
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import (
    CheckConstraint, Index, UniqueConstraint, ForeignKey, func
)
from db import db
from apps.client.constants import ClientType, EntityType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# =========================
# 1:1 法人プロフィール
# =========================
class CorporateProfile(db.Model):
    __tablename__ = "corporate_profile"

    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(
        db.Integer,
        ForeignKey("client.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    client = db.relationship("Client", back_populates="corporate_profile")

    representative_name  = db.Column(db.String(255))   # 代表者名
    representative_title = db.Column(db.String(50))    # 代表取締役 等
    company_number       = db.Column(db.String(13), index=True)  # 会社法人等番号(13桁想定)

    __table_args__ = (
        UniqueConstraint("client_id", name="uq_corporate_profile_client"),
    )

    def __repr__(self) -> str:
        return f"<CorporateProfile client_id={self.client_id} number={self.company_number or '-'}>"


# =========================
# 受託簿 - 委任者をつなぐ中間テーブル
# =========================
class ClientBookProfile(db.Model):
    __tablename__ = "client_book_profile"
    id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(db.Integer, db.ForeignKey("client.id", ondelete="CASCADE"), nullable=False)
    entrusted_book_id = db.Column(db.Integer, db.ForeignKey("entrusted_book.id", ondelete="CASCADE"), nullable=False)

    # 住所変更（案件単位での“登記簿上と現住所の差異”）
    needs_address_change = db.Column(db.Boolean, nullable=False, default=False)
    registered_address_at_filing = db.Column(db.String(255))   # 登記簿上の住所（当時）
    address_evidence_type = db.Column(db.String(50))           # '住民票', '附票' など
    address_evidence_date = db.Column(db.Date)

    __table_args__ = (
        db.UniqueConstraint("client_id", "entrusted_book_id", name="uq_client_book_profile"),
    )

    client = db.relationship("Client", backref="book_profiles")
    entrusted_book = db.relationship("EntrustedBook", backref="client_profiles")

# =========================
# クライアント
# =========================
class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)

    entity_type_id = db.Column(
        db.Integer, nullable=False,
        default=EntityType.INDIVIDUAL.value, index=True
    )
    client_type_id = db.Column(
        db.Integer, nullable=False,
        default=ClientType.RIGHT_HOLDER.value, index=True
    )

    # 基本
    name = db.Column(db.String(255), nullable=False)
    name_kana = db.Column(db.String(255))
    equity_numerator   = db.Column(db.Integer)  # >=0 or NULL
    equity_denominator = db.Column(db.Integer)  # >0  or NULL

    # 連絡先
    postal_code  = db.Column(db.String(20))
    address      = db.Column(db.String(255))
    phone_number = db.Column(db.String(50))
    fax          = db.Column(db.String(50))
    email        = db.Column(db.String(255))

    # 個人のみ
    birth_date = db.Column(db.Date)

    # 共通
    intention_confirmed_at = db.Column(db.DateTime)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=_utcnow, server_default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=_utcnow, onupdate=_utcnow, server_default=func.now())

    # 受託簿
    entrusted_book_id = db.Column(
        db.Integer, db.ForeignKey("entrusted_book.id"),
        nullable=False, index=True
    )
    entrusted_book = db.relationship("EntrustedBook", back_populates="clients")

    # 1:1 法人プロフィール
    corporate_profile = db.relationship(
        "CorporateProfile",
        uselist=False,
        back_populates="client",
        cascade="all, delete-orphan",
    )

    # documents
    amount_documents   = db.relationship("AmountDocument",   back_populates="client", cascade="all, delete-orphan")
    required_documents = db.relationship("RequiredDocument", back_populates="client", cascade="all, delete-orphan")
    delivery_documents = db.relationship("DeliveryDocument", back_populates="client", cascade="all, delete-orphan")
    origin_documents   = db.relationship("OriginDocument",   back_populates="client", cascade="all, delete-orphan")

    # --- enum ラッパ ---
    @property
    def entity_type(self) -> EntityType:
        try:
            return EntityType(self.entity_type_id)
        except Exception:
            return EntityType.INDIVIDUAL

    @property
    def client_type(self) -> ClientType:
        try:
            return ClientType(self.client_type_id)
        except Exception:
            return ClientType.RIGHT_HOLDER

    # --- 表示ヘルパ（法人は profile 経由） ---
    @property
    def honorific(self) -> str:
        return self.entity_type.honorific

    @property
    def formatted_postal_code(self) -> str:
        if not self.postal_code:
            return ""
        digits = "".join(ch for ch in str(self.postal_code) if ch.isdigit())
        return f"{digits[:3]}-{digits[3:]}" if len(digits) == 7 else self.postal_code

    def postal_code_with_mark(self) -> str:
        base = self.formatted_postal_code
        return f"〒{base}" if base else ""

    # 互換アクセサ（テンプレ修正最小化）
    @property
    def representative_name(self) -> str | None:
        return self.corporate_profile.representative_name if self.corporate_profile else None

    @property
    def representative_title(self) -> str | None:
        return self.corporate_profile.representative_title if self.corporate_profile else None

    @property
    def company_number(self) -> str | None:
        return self.corporate_profile.company_number if self.corporate_profile else None

    def company_number_display(self, hyphen: bool = True) -> str:
        num = self.company_number or ""
        digits = "".join(ch for ch in num if ch.isdigit())
        if len(digits) != 12:
            return num  # 桁数違いはそのまま返す
        return f"{digits[0:4]}-{digits[4:6]}-{digits[6:12]}" if hyphen else digits

    # ユーティリティ
    def ensure_corporate_profile(self) -> CorporateProfile:
        """法人で profile が無ければ空で作る（ビュー/フォームの簡素化用）"""
        if not self.corporate_profile:
            self.corporate_profile = CorporateProfile()
        return self.corporate_profile

    # __table_args__ : モデルに対して テーブルレベルの追加設定 を渡すための特別な属性

    # CheckConstraint : SQL の CHECK 制約をテーブルに追加。(DB が行を保存するときに「条件を満たしているか」を検査する仕組み。)
    # • equity_denominator（分母）が NULL ならOK
    # • NULLじゃなければ 0より大きい値でなければエラー
    # • 制約名は "ck_client_equity_denominator_positive"

    # •	インデックス名は ix_client_book_updated
    # •	カラムは entrusted_book_id と updated_at の複合インデックス
    # •	「受託簿ごとの更新順で並べる」処理が速くなる
    __table_args__ = (
        CheckConstraint(
            "(equity_denominator IS NULL) OR (equity_denominator > 0)",
            name="ck_client_equity_denominator_positive",
        ),
        CheckConstraint(
            "(equity_numerator IS NULL) OR (equity_numerator >= 0)",
            name="ck_client_equity_numerator_nonneg",
        ),
        Index("ix_client_book_updated", "entrusted_book_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} name={self.name} type={self.client_type.name}>"