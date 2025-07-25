### amount_document/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, BooleanField, TextAreaField, DateField,
    IntegerField, FieldList, SelectField,HiddenField
)
from wtforms.validators import DataRequired, Optional
from apps.amount_document.models import AmountDocumentType,MIN_ENTRIES


class AmountDocumentForm(FlaskForm):
    document_type = SelectField(
        '書類タイプ',
        choices=[(e.value, e.label) for e in AmountDocumentType],
        coerce=int,
        default=AmountDocumentType.ESTIMATE.value
    )
    client_id = HiddenField(validators=[DataRequired()]) # client_idの隠しフィールド

    entrusted_book_name = StringField('受託簿名', validators=[DataRequired()])
    client_name = StringField('委任者名', validators=[DataRequired()])

    has_stamp = BooleanField('押印有', default=False)
    apply_consumption_tax = BooleanField('消費税あり', default=True)
    apply_withholding = BooleanField('源泉徴収あり', default=False)

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
    issued_date = DateField('作成日', format='%Y-%m-%d', validators=[Optional()])
