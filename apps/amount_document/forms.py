### apps/amount_document/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, BooleanField, TextAreaField, DateField,
    IntegerField, FieldList, HiddenField
)
from wtforms.validators import DataRequired, Optional
from apps.amount_document.constants import MIN_ENTRIES


class AmountDocumentForm(FlaskForm):

    # client_id = HiddenField(validators=[DataRequired()])  # client_idの隠しフィールド
    entrusted_book_name = StringField('受託簿名', validators=[DataRequired()])
    apply_consumption_tax = BooleanField('消費税有', default=True)
    apply_withholding = BooleanField('源泉徴収有', default=False)
    advance_payment = IntegerField('前払金', validators=[Optional()])
    item_types = FieldList(
        StringField('種別', validators=[Optional()]),
        min_entries=MIN_ENTRIES
    )
    reward_amounts = FieldList(
        IntegerField('報酬額', validators=[Optional()]),
        min_entries=MIN_ENTRIES
    )
    expense_amounts = FieldList(
        IntegerField('実費額', validators=[Optional()]),
        min_entries=MIN_ENTRIES
    )
    note = TextAreaField('備考', validators=[Optional()])
    estimate_date = DateField('見積日', validators=[Optional()])
    invoice_date = DateField('請求日', validators=[Optional()])
    receipt_date = DateField('領収日', validators=[Optional()])
    client_id = HiddenField()# client_idの受渡用隠しフィールド
