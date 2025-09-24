# apps/register/reap_estate/pdf/views.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from io import BytesIO
# from .forms import PDFUploadForm
# from .services.services import parse_corporation_registry


# --------------------------
# ブループリント
# --------------------------
register_real_estate_pdf_bp = Blueprint(
    "register_real_estate_pdf",
    __name__,
    url_prefix="/pdf"
)
