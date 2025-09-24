# apps/commerce/commerce/pdf/forms.py
from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired

class PDFUploadForm(FlaskForm):
    file = FileField(
        "PDFファイルを選択",
        validators=[
            FileRequired(message="ファイルを選択してください。"),
            FileAllowed(["pdf"], message="PDFのみアップロードできます。"),
        ],
    )
    submit = SubmitField("解析する")