### apps/entrusted_book/models.py
from datetime import datetime
from db import db


class EntrustedBook(db.Model):
    __tablename__ = 'entrusted_book'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text, nullable=True)

    contract_date = db.Column(db.Date, nullable=True) # 契約日
    execution_date  = db.Column(db.Date, nullable=True) # 実行日
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # EntrustedBook(1) - Client(多) の関係を表す
    clients = db.relationship(
        'Client',
        back_populates='entrusted_book',  # Clientモデル側で対応するリレーション名に合わせる
        cascade='all, delete-orphan',  # all:子（Client）にも連鎖（cascade）させる delete-orphan:孤児（orphan）になった子を削除する
        lazy='selectin'  #  N+1 を防ぎつつ必要なときにだけロードできるので、EntrustedBook ↔ Client の関係には相性がいい
    )
