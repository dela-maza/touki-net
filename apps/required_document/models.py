### apps/required_document/models.py
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict


class RequiredDocument(db.Model):
    __tablename__ = "required_document"

    id = db.Column(db.Integer, primary_key=True)
    entrusted_book_name = db.Column(db.String(255), nullable=False)
    # パラグラフ
    greeting_paragraph = db.Column(db.Text, nullable=False)  # 上段（拝啓～お礼）
    main_paragraph = db.Column(db.Text, nullable=False)  # 中段（送付書類の説明）
    closing_paragraph = db.Column(db.Text, nullable=False)  # 下段（結び・敬具）
    # 行（書類名・枚数）
    mailed_documents = db.Column(JSONB, nullable=False, server_default='[]')
    requested_return_documents = db.Column(JSONB, nullable=False, server_default='[]')
    # 日付
    sent_date = db.Column(db.Date, nullable=True)  # 送信日
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # リレーション
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="required_documents")
