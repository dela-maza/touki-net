### apps/amount/models.py
from datetime import datetime
from db import db
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict
# from apps.amount.calculator import AmountDocumentCalculator


class AmountDocument(db.Model):
    __tablename__ = "amount_document"

    id = db.Column(db.Integer, primary_key=True)
    entrusted_book_name = db.Column(db.String(255), nullable=False)
    apply_consumption_tax = db.Column(db.Boolean, default=True)
    apply_withholding = db.Column(db.Boolean, default=False)
    advance_payment = db.Column(db.Integer, nullable=True)
    item_types = db.Column(JSONB, nullable=False, server_default='[]')
    reward_amounts = db.Column(JSONB, nullable=False, server_default='[]')
    expense_amounts = db.Column(JSONB, nullable=False, server_default='[]')
    note = db.Column(db.Text, nullable=True)
    estimate_date = db.Column(db.Date, nullable=True)
    invoice_date = db.Column(db.Date, nullable=True)
    receipt_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="amount_documents")

    def set_items_normalized(
            self,
            item_types_list: list[str],
            reward_list: list[int],
            expense_list: list[int],
    ) -> None:
        """
        項目・報酬・実費の3配列を同じ長さに正規化して保存する。
        - 未入力は "" / 0 で埋める
        - None は 0/"" に変換
        """
        item_types = [s if s is not None else "" for s in (item_types_list or [])]
        rewards = [int(x or 0) for x in (reward_list or [])]
        expenses = [int(x or 0) for x in (expense_list or [])]

        max_len = max(len(item_types), len(rewards), len(expenses), 0)
        item_types.extend([""] * (max_len - len(item_types)))
        rewards.extend([0] * (max_len - len(rewards)))
        expenses.extend([0] * (max_len - len(expenses)))

        self.item_types = item_types
        self.reward_amounts = rewards
        self.expense_amounts = expenses

    def get_items(self) -> Dict[str, list]:
        return {
            "item_types": self.item_types or [],
            "reward_amounts": self.reward_amounts or [],
            "expense_amounts": self.expense_amounts or [],
        }

    def iter_items(self):
        a = self.item_types or []
        b = self.reward_amounts or []
        c = self.expense_amounts or []
        return zip(a, b, c)

    @staticmethod
    def format_number(value: int) -> str:
        return f"{value:,}" if isinstance(value, int) else ""


    def __repr__(self):
        return f"<AmountDocument id={self.id} client_id={self.client_id} created_at={self.created_at}>"
