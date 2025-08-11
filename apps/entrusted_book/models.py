### apps/entrusted_book/models.py
from datetime import datetime
from db import db


class EntrustedBook(db.Model):
    __tablename__ = 'entrusted_book'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)  # 受託簿名は必須にするのがおすすめ
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # EntrustedBook(1) - Client(多) の関係を表す
    clients = db.relationship(
        'Client',
        back_populates='entrusted_book',  # Clientモデル側で対応するリレーション名に合わせる
        cascade='all, delete-orphan',  # all:子（Client）にも連鎖（cascade）させる delete-orphan:孤児（orphan）になった子を削除する
        lazy='select'  # 遅延ロード設定（必要に応じて変更）
    )
