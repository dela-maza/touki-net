# apps/register/commerce/__init__.py

from flask import Blueprint
from .pdf.views import register_commerce_pdf_bp

register_commerce_bp = Blueprint(
    "register_commerce",
    __name__,
    url_prefix="/commerce",
    template_folder="templates/commerce",
    static_folder="static",
)

register_commerce_bp.register_blueprint(register_commerce_pdf_bp)
