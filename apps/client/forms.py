# apps/client/forms.py
from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, TextAreaField, SelectField, IntegerField
)
from wtforms.validators import (
    DataRequired, Optional, Email, Length, NumberRange, ValidationError
)
from apps.client.models import EntityType,ClientType

# 共通バリデータ
MAX_LEN_255 = Length(max=255)
MAX_LEN_50  = Length(max=50)
MAX_LEN_20  = Length(max=20)

def get_client_type_choices():
    # Enum -> (value, label)
    return [(ct.value, ct.label) for ct in ClientType]

class ClientForm(FlaskForm):
    entrusted_book_id = SelectField(
        "Entrusted Book",
        coerce=int,
        validators=[DataRequired()]
    )
    entity_type_id = SelectField(
        "区分",
        choices=[(EntityType.INDIVIDUAL.value, "個人"),
                 (EntityType.CORPORATION.value, "法人")],
        coerce=int,
        default=EntityType.INDIVIDUAL.value,
    )
    client_type_id = SelectField(
        "Client Type",
        choices=get_client_type_choices(),
        coerce=int,
        default=ClientType.RIGHT_HOLDER.value,
        validators=[DataRequired()]
    )

    # 基本情報
    name       = StringField("Client Name", validators=[DataRequired(), MAX_LEN_255])
    name_kana  = StringField("kana",        validators=[Optional(), MAX_LEN_255])
    birth_date = DateField("Birth Date", format="%Y-%m-%d", validators=[Optional()])

    # 住所・連絡先
    postal_code  = StringField("ZIP Code",    validators=[Optional(), MAX_LEN_20])
    address      = StringField("Address",     validators=[Optional(), MAX_LEN_255])
    phone_number = StringField("Phone Number",validators=[Optional(), MAX_LEN_50])
    fax          = StringField("Fax",         validators=[Optional(), MAX_LEN_50])
    email        = StringField("Mail",        validators=[Optional(), Email(), MAX_LEN_255])

    # その他
    intention_confirmed_at = DateField("Intent Confirmation Date", format="%Y-%m-%d", validators=[Optional()])
    note = TextAreaField("Notes", validators=[Optional()])

    # --- 追加: 持分（equity） ---
    # 分子/分母はどちらも未入力 or どちらも入力のどちらかに制約
    equity_numerator = IntegerField(
        "Equity Numerator (分子)",
        validators=[Optional(), NumberRange(min=0, message="0 以上で入力してください")]
    )
    equity_denominator = IntegerField(
        "Equity Denominator (分母)",
        validators=[Optional(), NumberRange(min=1, message="1 以上で入力してください")]
    )
    equity_note = StringField(  # 例: 「持分他」などの補足に
        "Equity Note",
        validators=[Optional(), MAX_LEN_255]
    )

    # 法人用
    representative_title = StringField("代表者肩書", validators=[Optional(), Length(max=50)])
    representative_name  = StringField("代表者名",   validators=[Optional(), Length(max=255)])
    company_number       = StringField("法人番号（13桁）",
                                       validators=[Optional(), Length(min=13, max=13)])

    # クロスフィールド・バリデーション
    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators) # まず親クラスの validate を呼ぶ

        num = self.equity_numerator.data
        den = self.equity_denominator.data

        # どちらか片方だけの入力は禁止
        if (num is None and den is not None) or (num is not None and den is None):
            self.equity_numerator.errors.append("分子/分母は両方入力するか両方空にしてください。")
            self.equity_denominator.errors.append("分子/分母は両方入力するか両方空にしてください。")
            ok = False

        # 0/分母 も許容したくない場合はここで弾く（必要に応じて）
        if num is not None and den is not None:
            if den == 0:
                self.equity_denominator.errors.append("分母は 1 以上で入力してください。")
                ok = False
            return ok

        num = self.equity_numerator.data
        den = self.equity_denominator.data

        # どちらか片方だけの入力は禁止
        if (num is None and den is not None) or (num is not None and den is None):
            self.equity_numerator.errors.append("分子/分母は両方入力するか両方空にしてください。")
            self.equity_denominator.errors.append("分子/分母は両方入力するか両方空にしてください。")
            ok = False

        # 0/分母 も許容したくない場合はここで弾く（必要に応じて）
        if num is not None and den is not None:
            if den == 0:
                self.equity_denominator.errors.append("分母は 1 以上で入力してください。")
                ok = False
        return ok