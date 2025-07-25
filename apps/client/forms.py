###_client/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, TextAreaField, SelectField
)
from wtforms.validators import DataRequired, Optional, Email, Length

from apps.client.models import ClientType  # ClientType Enumをインポート


class ClientForm(FlaskForm):
    entrusted_book_id = SelectField(
        '受託簿',
        coerce=int,
        validators=[DataRequired()]
    )

    client_type_id = SelectField(
        'クライアント種別',
        choices=[(ct.value, ct.label) for ct in ClientType],
        coerce=int,
        default=ClientType.RIGHT_HOLDER.value,
        validators=[DataRequired()]
    )

    name = StringField(
        '名前',
        validators=[DataRequired(), Length(max=255)]
    )

    name_furigana = StringField(
        'ふりがな',
        validators=[Optional(), Length(max=255)]
    )

    birth_date = DateField(
        '生年月日',
        format='%Y-%m-%d',
        validators=[Optional()]
    )

    postal_code = StringField(
        '郵便番号',
        validators=[Optional(), Length(max=20)]
    )

    address = StringField(
        '住所',
        validators=[Optional(), Length(max=255)]
    )

    phone_number = StringField(
        '電話番号',
        validators=[Optional(), Length(max=50)]
    )

    fax = StringField(
        'FAX',
        validators=[Optional(), Length(max=50)]
    )

    email = StringField(
        'メールアドレス',
        validators=[Optional(), Email(), Length(max=255)]
    )

    intention_confirmed_at = DateField(
        '意思確認日',
        format='%Y-%m-%d',
        validators=[Optional()]
    )

    note = TextAreaField(
        '備考',
        validators=[Optional()]
    )
