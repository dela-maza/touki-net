# apps/__init__.py
import os
from pathlib import Path
import configparser
from flask import Flask
import settings
from db import db
from flask_wtf import CSRFProtect
from apps.entrusted_book.views import entrusted_book_bp
from apps.client.views import client_bp
from apps.amount_document.views import amount_document_bp
from apps.property_description.views import property_bp
from apps.template_filters import register_template_filters


def _load_ini_dict(path: Path) -> dict:
    """ini を {SECTION: {key: value}} の dict にして返す（存在しなければ空 dict）"""
    cfg = configparser.ConfigParser()
    if path.exists():
        cfg.read(path, encoding="utf-8")
    return {sec: dict(cfg[sec]) for sec in cfg.sections()}


def create_app():
    app = Flask(__name__)

    # --- 基本設定 ---
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.SQLALCHEMY_TRACK_MODIFICATIONS

    # --- アップロードフォルダ設定 ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, "..", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    # --- 拡張の初期化 ---
    csrf = CSRFProtect(app)
    db.init_app(app)

    # --- Jinja フィルター登録（和暦など） ---
    register_template_filters(app)

    # --- グローバル設定の読み込み ---
    # project_root/config/ の ini を読み込む
    project_root = Path(__file__).resolve().parent.parent
    office_ini = _load_ini_dict(project_root / "config" / "office.ini")
    tax_ini    = _load_ini_dict(project_root / "config" / "tax.ini")

    # Python側からも使えるよう app.config に格納
    app.config["OFFICE"] = office_ini.get("OFFICE", {})
    app.config["BANK"]   = office_ini.get("BANK", {})  # OFFICE と同じ ini に入れている想定（なければ空）
    # TAX_RATE セクションを float/int にキャストして dict 化
    app.config["TAX_RATE"] = {
        k: (float(v) if "." in v else int(v))
        for k, v in tax_ini.get("TAX_RATE", {}).items()
    }

    @app.context_processor
    def inject_globals():
        """
        Jinja2 のレンダリング時に利用できるグローバル変数を注入する。
        テンプレート内では {{ tax.consumption_tax }} のように参照可能。

        注意:
        - ここで返した値はテンプレート専用。Python コードからは参照しないこと。
        - Python 側で参照したい場合は current_app.config["TAX_RATE"] 等を利用すること。
        """
        return {
            "office": app.config["OFFICE"],
            "bank":   app.config["BANK"],
            "tax":    app.config["TAX_RATE"],
            "app_name": "司法書士ネットシステム",
        }

    # --- Blueprint 登録 ---
    app.register_blueprint(entrusted_book_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(amount_document_bp)
    app.register_blueprint(property_bp)

    return app