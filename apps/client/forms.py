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
        '受託簿',
        coerce=int,
        validators=[DataRequired()]
    )

    client_type_id = SelectField(
        'クライアント種別',
        choices=get_client_type_choices(),
        coerce=int,
        default=ClientType.RIGHT_HOLDER.value,
        validators=[DataRequired()]
    )

    # 基本情報
    name = StringField('名前', validators=[DataRequired(), MAX_LEN_255])
    name_furigana = StringField('ふりがな', validators=[Optional(), MAX_LEN_255])
    birth_date = DateField('生年月日', format='%Y-%m-%d', validators=[Optional()])

    # 住所・連絡先
    postal_code = StringField('郵便番号', validators=[Optional(), MAX_LEN_20])
    address = StringField('住所', validators=[Optional(), MAX_LEN_255])
    phone_number = StringField('電話番号', validators=[Optional(), MAX_LEN_50])
    fax = StringField('FAX', validators=[Optional(), MAX_LEN_50])
    email = StringField('メールアドレス', validators=[Optional(), Email(), MAX_LEN_255])

    # その他
    intention_confirmed_at = DateField('意思確認日', format='%Y-%m-%d', validators=[Optional()])
    note = TextAreaField('備考', validators=[Optional()])
