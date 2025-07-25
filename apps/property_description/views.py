### property_description/views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
from apps.property_description.forms import UploadPDFForm
property_bp = Blueprint(
    'property',
    __name__,
    url_prefix='/property',
    template_folder='templates/property',
    static_folder='static/property',
    static_url_path='/property/static'
)
# test
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # apps/property_description/uploads

@property_bp.route('/upload', methods=['GET', 'POST'])
def upload_pdf():
    form = UploadPDFForm()
    if form.validate_on_submit():
        file = form.pdf_file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # ここでPDF解析関数を呼ぶ例
        # result = extract_real_estate_display_as_dict(filepath)

        flash('ファイルアップロード成功: ' + filename)
        return redirect(url_for('property.upload_pdf'))

    return render_template('upload.html', form=form)