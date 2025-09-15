# apps/documents/required/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FieldList, FormField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms import Form as WTForm


class DocumentItemForm(FlaskForm):
    """
    書類1行分（名称・注意・部数）
    - 本来なら 'name' としたいが、WTForms の FormField 自体が .name 属性を持つため
      衝突してテンプレート側で `str object is not callable` エラーになる。
    - そのため 'doc_name' として定義している。
    """
    doc_name = StringField("書類名", validators=[Optional(), Length(max=255)])
    note     = StringField("補助情報", validators=[Optional(), Length(max=255)])
    copies   = StringField("枚数/区分", validators=[Optional(), Length(max=50)])


class RequiredDocumentForm(FlaskForm):
    client_id = HiddenField(validators=[DataRequired()])
    entrusted_book_name = StringField("受託簿名（注書き可）",
                                      validators=[DataRequired(), Length(max=255)])

    greeting_paragraph = TextAreaField("挨拶文（上段）", validators=[Optional()])
    main_paragraph = TextAreaField("本文（中段）", validators=[Optional()])
    closing_paragraph = TextAreaField("結び（下段）", validators=[Optional()])

    mailed_documents = FieldList(
        FormField(DocumentItemForm),
        min_entries=5, max_entries=50, label="送付書類")
    requested_return_documents = FieldList(
        FormField(DocumentItemForm),
        min_entries=5, max_entries=50, label="返送依頼書類")

    sent_date = DateField("発送日", validators=[Optional()], format="%Y-%m-%d")
    submit = SubmitField("保存")
