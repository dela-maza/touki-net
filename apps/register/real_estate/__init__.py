# apps/register/real_estate/__init__.py

from flask import Blueprint
from .pdf.views import register_real_estate_pdf_bp

register_real_estate_bp = Blueprint(
    "register_real_estate",
    __name__,
    url_prefix="/real_estate",
    template_folder="templates/real_estate",
    static_folder="static",
)

register_real_estate_bp.register_blueprint(register_real_estate_pdf_bp)
