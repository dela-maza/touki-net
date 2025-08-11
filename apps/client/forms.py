###_client/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Optional, Email, Length
from apps.client.models import ClientType

# 共通バリデータ
MAX_LEN_255 = Length(max=255)
MAX_LEN_50 = Length(max=50)
MAX_LEN_20 = Length(max=20)

def get_client_type_choices():
    return [(ct.value, ct.label) for ct in ClientType]

class ClientForm(FlaskForm):
    entrusted_book_id = SelectField(
        'Entrusted Book',
        coerce=int,
        validators=[DataRequired()]
    )

    client_type_id = SelectField(
        'Client Type',
        choices=get_client_type_choices(),
        coerce=int,
        default=ClientType.RIGHT_HOLDER.value,
        validators=[DataRequired()]
    )

    # 基本情報
    name = StringField('Client Name', validators=[DataRequired(), MAX_LEN_255])
    name_kana = StringField('kana', validators=[Optional(), MAX_LEN_255])
    birth_date = DateField('Birth Date', format='%Y-%m-%d', validators=[Optional()])

    # 住所・連絡先
    postal_code = StringField('ZIP Code', validators=[Optional(), MAX_LEN_20])
    address = StringField('Address', validators=[Optional(), MAX_LEN_255])
    phone_number = StringField('Phone Number', validators=[Optional(), MAX_LEN_50])
    fax = StringField('Fax', validators=[Optional(), MAX_LEN_50])
    email = StringField('Mail', validators=[Optional(), Email(), MAX_LEN_255])

    # その他
    intention_confirmed_at = DateField('Intent Confirmation Date', format='%Y-%m-%d', validators=[Optional()])
    note = TextAreaField('Notes', validators=[Optional()])
