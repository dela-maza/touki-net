# apps/register/forms.py
from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, SubmitField
from wtforms.validators import DataRequired

class RegisterUploadForm(FlaskForm):
    # まずは必須の3点だけ
    domain = SelectField(
        "カテゴリ",
        choices=[("commerce", "商業・法人"), ("real_estate", "不動産")],
        validators=[DataRequired()],
    )
    mode = SelectField(
        "モード",
        choices=[("pdf_to_json", "PDF → JSON"), ("json_to_html", "JSON → HTML"), ("json_to_text", "JSON → テキスト")],
        validators=[DataRequired()],
    )
    file = FileField("ファイル", validators=[DataRequired(message="ファイルを選択してください")])
    submit = SubmitField("アップロード")