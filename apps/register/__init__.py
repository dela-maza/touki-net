# apps/register/__init__.py
from flask import Blueprint
from .commerce import register_commerce_bp
from .real_estate import register_real_estate_bp

register_bp = Blueprint(
    "register",
    __name__,
    url_prefix="/register",
    template_folder="templates",
    static_folder="static",
)

# サブルート登録
register_bp.register_blueprint(register_commerce_bp)
register_bp.register_blueprint(register_real_estate_bp)