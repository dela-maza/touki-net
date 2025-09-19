### apps/__init__.py
import os
from pathlib import Path
import configparser
from flask import Flask
import settings
from db import db
from apps.template_filters import register_template_filters
from apps.entrusted_book.views import entrusted_book_bp
from apps.client.views import client_bp
from apps.documents.amount.views import amount_bp
from apps.documents.required.views import required_bp
from apps.documents.delivery.views import delivery_bp
from apps.documents.origin.views import origin_bp
from apps.property_description.views import property_bp
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from flask import redirect, url_for, flash


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

    # --- CSRF ---
    csrf = CSRFProtect()
    csrf.init_app(app)  # これで全POST/PUT/PATCH/DELETEにCSRFチェック

    # @app.context_processor:jinja2で呼び出せる関数を定義
    # 関数自身を返せないから、関数内で関数を定義し、辞書に包んで返してる
    @app.context_processor
    def inject_csrf():
        """テンプレで手書きフォームに使う用の csrf_token() を提供"""
        return {"csrf_token": generate_csrf}

    #  CSRFの検証が失敗すると、CSRFErrorが発生し、デフォルトではエラー理由と400レスポンスを返す。
    #  Flaskのerrorhandler()を使用して、エラーレスポンスをカスタマイズす
    @app.errorhandler(CSRFError)
    def handle_csrf(e):
        """デフォは400で真っ白になるので、flashして戻す"""
        flash("不正なリクエスト（CSRF）です。もう一度操作してください。", "danger")
        return redirect(url_for("entrusted_book.index")), 303

    # --- 拡張の初期化 ---
    db.init_app(app)

    # --- Jinja フィルター登録（和暦など） ---
    register_template_filters(app)

    # --- グローバル設定の読み込み ---
    # project_root/config/ の ini を読み込む
    project_root = Path(__file__).resolve().parent.parent
    office_ini = _load_ini_dict(project_root / "config" / "office.ini")
    tax_ini = _load_ini_dict(project_root / "config" / "tax.ini")

    # Python側からも使えるよう app.config に格納
    app.config["OFFICE"] = office_ini.get("OFFICE", {})
    app.config["BANK"] = office_ini.get("BANK", {})  # OFFICE と同じ ini に入れている想定（なければ空）
    # TAX_RATE セクションを float/int にキャストして dict 化
    app.config["TAX_RATE"] = {
        k: (float(v) if "." in v else int(v))
        for k, v in tax_ini.get("TAX_RATE", {}).items()
    }

    @app.context_processor
    def inject_globals():
        """
        @app.context_processor
        Jinja2 のレンダリング時に利用できるグローバル変数を注入する。
        テンプレート内では {{ tax.consumption_tax }} のように参照可能。
        関数名は何でもよい

        注意:
        - ここで返した値はテンプレート専用。Python コードからは参照しないこと。
        - Python 側で参照したい場合は current_app.config["TAX_RATE"] 等を利用すること。
        """
        return {
            "office": app.config["OFFICE"],
            "bank": app.config["BANK"],
            "tax": app.config["TAX_RATE"],
            "app_name": "司法書士ネットシステム",
        }

    # --- Blueprint 登録 ---
    app.register_blueprint(entrusted_book_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(amount_bp)
    app.register_blueprint(required_bp)
    app.register_blueprint(delivery_bp)
    app.register_blueprint(origin_bp)

    return app
