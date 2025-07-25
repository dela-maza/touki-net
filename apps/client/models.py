### client/models.py
from datetime import datetime
from db import db
from enum import Enum

class ClientType(Enum):
    RIGHT_HOLDER = 1
    OBLIGATION_HOLDER = 2
    APPLICANT = 3

    @property
    def label(self):
        return {
            ClientType.RIGHT_HOLDER: "権利者",
            ClientType.OBLIGATION_HOLDER: "義務者",
            ClientType.APPLICANT: "申請人"
        }[self]

    @classmethod
    def from_id(cls, _id: int) -> 'ClientType':
        try:
            return cls(_id)
        except ValueError:
            return cls.RIGHT_HOLDER


class Client(db.Model):
    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    client_type_id = db.Column(db.Integer, nullable=False, default=ClientType.RIGHT_HOLDER.value)
    name = db.Column(db.String(255), nullable=False)
    name_furigana = db.Column(db.String(255), nullable=True)
    birth_date = db.Column(db.DateTime, nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    fax = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    intention_confirmed_at = db.Column(db.DateTime, nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    # EntrustBook(1)-Client(他）とのリレーション
    entrusted_book_id = db.Column(db.Integer, db.ForeignKey('entrusted_book.id'), nullable=False)
    entrusted_book = db.relationship('EntrustedBook', back_populates='clients')
    # AmountDocument（他）-Client（１）とのリレーション
    amount_documents = db.relationship('AmountDocument', back_populates='client', cascade="all, delete-orphan")

    @property
    def client_type(self) -> ClientType:
        return ClientType.from_id(self.client_type_id)