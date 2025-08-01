### amount_document/models.py
from db import db
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB


class AmountDocumentType(Enum):
    ESTIMATE = 1
    INVOICE = 2
    RECEIPT = 3

    @property
    def label(self):
        return {
            AmountDocumentType.ESTIMATE: "見積",
            AmountDocumentType.INVOICE: "請求",
            AmountDocumentType.RECEIPT: "領収",
        }[self]

    @classmethod
    def from_id(cls, _id: int) -> "AmountDocumentType":
        try:
            return cls(_id)
        except ValueError:
            return cls.ESTIMATE


MIN_ENTRIES = 20


class AmountDocument(db.Model):
    __tablename__ = "amount_document"

    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.Integer, nullable=False, default=AmountDocumentType.ESTIMATE.value)
    entrusted_book_name = db.Column(db.String(255), nullable=False)

    has_stamp = db.Column(db.Boolean, default=False)
    apply_consumption_tax = db.Column(db.Boolean, default=True)
    apply_withholding = db.Column(db.Boolean, default=False)

    advance_payment = db.Column(db.Integer, nullable=True)

    # すべてJSONB型で統一
    item_types = db.Column(JSONB, nullable=True)
    reward_amounts = db.Column(JSONB, nullable=True)
    expense_amounts = db.Column(JSONB, nullable=True)

    note = db.Column(db.Text, nullable=True)
    issued_date = db.Column(db.Date, nullable=True)

    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="amount_documents")

    def set_items(self, item_types_list, reward_list, expense_list):
        """各明細リストをJSON形式で保存（すでにJSONBなのでそのまま）"""
        self.item_types = item_types_list or []
        self.reward_amounts = reward_list or []
        self.expense_amounts = expense_list or []

    def get_items(self):
        """JSONBフィールドからそのまま取得。空の場合は空リストを返す。"""
        return {
            "item_types": self.item_types or [],
            "reward_amounts": self.reward_amounts or [],
            "expense_amounts": self.expense_amounts or [],
        }
