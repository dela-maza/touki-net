### apps/__init__.py
import os
from flask import Flask
import settings
from db import db
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

from apps.entrusted_book.views import entrusted_book_bp
from apps.client.views import client_bp
from apps.amount_document.views import amount_document_bp
from apps.property_description.views import property_bp

from apps.amount_document.filters import amount_document_type_label
from apps.template_filters import register_template_filters

def create_app():
    app = Flask(__name__)

    # --- 設定 ---
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

    # --- アップロードフォルダ設定 ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    # --- 拡張の初期化 ---
    csrf = CSRFProtect(app)
    db.init_app(app)
    Migrate(app, db)

    # --- Jinja フィルター登録 ---
    app.jinja_env.filters['amount_document_type_label'] = amount_document_type_label
    register_template_filters(app)  # 和暦など

    # --- Blueprint 登録 ---
    app.register_blueprint(entrusted_book_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(amount_document_bp)
    app.register_blueprint(property_bp)

    return app