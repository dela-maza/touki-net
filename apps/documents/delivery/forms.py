# apps/documents/delivery/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FieldList, FormField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms import Form as WTForm

class DeliveryItemForm(WTForm):
    doc_name = StringField("書類名", validators=[Optional(), Length(max=255)])
    copies   = StringField("枚数",   validators=[Optional(), Length(max=50)])

class DeliveryDocumentForm(FlaskForm):
    client_id = HiddenField(validators=[DataRequired()])
    entrusted_book_name = StringField("受託簿名", validators=[DataRequired(), Length(max=255)])

    greeting_paragraph = TextAreaField("挨拶文（上段）", validators=[Optional()])
    closing_paragraph  = TextAreaField("結び（下段）", validators=[Optional()])

    documents = FieldList(FormField(DeliveryItemForm), min_entries=5, max_entries=50, label="納品書類")

    sent_date = DateField("発送日", validators=[Optional()], format="%Y-%m-%d")
    submit = SubmitField("保存")