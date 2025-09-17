# apps/documents/origin/models.py
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import JSONB


class OriginDocument(db.Model):
    __tablename__ = "origin_document"

    id = db.Column(db.Integer, primary_key=True)

    # 本文系
    real_estate_description = db.Column(db.Text, nullable=False)  # 不動産の表示

    # 当事者
    right_holders    = db.Column(db.Text, nullable=False, default="")
    obligation_holders= db.Column(db.Text, nullable=False, default="")

    # 登記の原因となる事実又は法律行為
    cause_type_id = db.Column(db.Integer,nullable=False)
    cause_text = db.Column(db.Text, nullable=False)

    # 日付
    contract_date = db.Column(db.Date, nullable=True)  # 契約日
    payment_date  = db.Column(db.Date, nullable=True)  # 決済日
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # リレーション
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client    = db.relationship("Client", back_populates="origin_documents")

    def __repr__(self) -> str:
        return f"<OriginDocument id={self.id} client_id={self.client_id}>"