# apps/documents/origin/models.py
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import JSONB
from apps.documents.origin.constants import CauseType


class OriginDocument(db.Model):
    __tablename__ = "origin_document"

    id = db.Column(db.Integer, primary_key=True)

    # 不動産の表示
    real_estate_descriptions = db.Column(
        JSONB, nullable=False, default=list
    )

    # 当事者
    right_holders    = db.Column(db.Text, nullable=False, default="")
    obligation_holders= db.Column(db.Text, nullable=False, default="")

    # 登記の原因となる事実又は法律行為
    cause_type_id = db.Column(db.Integer,nullable=False)
    cause_fact = db.Column(db.Text, nullable=False)

    # 日付
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # リレーション
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client    = db.relationship("Client", back_populates="origin_documents")


    @property
    def cause_type(self) -> CauseType:
        try:
            return CauseType(self.cause_type_id)
        except Exception:
            return CauseType.SALE
    @property
    def real_estate_description(self) -> str:
        parts = self.real_estate_descriptions or []
        return "\n\n".join([p for p in parts if p])

    def __repr__(self) -> str:
        return f"<OriginDocument id={self.id} client_id={self.client_id}>"