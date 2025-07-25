from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

class UploadPDFForm(FlaskForm):
    pdf_file = FileField('PDFファイルを選択してください', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDFファイルのみアップロードできます')
    ])
    submit = SubmitField('アップロード')