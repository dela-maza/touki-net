### apps/documents/delivery/models.py
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import JSONB


class DeliveryDocument(db.Model):
    __tablename__ = "delivery_document"

    id = db.Column(db.Integer, primary_key=True)
    entrusted_book_name = db.Column(db.String(255), nullable=False)
    # パラグラフ
    greeting_paragraph = db.Column(db.Text, nullable=False)  # 上段（拝啓～お礼）
    closing_paragraph = db.Column(db.Text, nullable=False)  # 下段（結び・敬具）
    # 行（書類名・枚数）
    documents = db.Column(JSONB, nullable=False, server_default='[]', default=list)
    # 日付
    sent_date = db.Column(db.Date, nullable=True)  # 送信日
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # リレーション
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="delivery_documents")


    def __repr__(self):
        return f"<DeliveryDocument id={self.id} client_id={self.client_id} created_at={self.created_at}>"
