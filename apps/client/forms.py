### apps/client/forms.py
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, TextAreaField, SelectField, IntegerField,SubmitField
)
from wtforms.validators import (
    DataRequired, Optional, Email, Length, NumberRange, ValidationError
)

# ← ここを models ではなく constants から取る
from apps.client.constants import EntityType, ClientType
from wtforms.validators import Optional, Length, Regexp


# 共通バリデータ
MAX_LEN_255 = Length(max=255)
MAX_LEN_50 = Length(max=50)
MAX_LEN_20 = Length(max=20)


def get_client_type_choices() -> list[tuple[int, str]]:
    return [(ct.value, ct.label) for ct in ClientType]


class ClientForm(FlaskForm):
    entrusted_book_id = SelectField(
        "Entrusted Book",
        coerce=int,
        validators=[DataRequired()],
    )

    entity_type_id = SelectField(
        "区分",
        choices=[
            (EntityType.INDIVIDUAL.value, "個人"),
            (EntityType.CORPORATION.value, "法人"),
        ],
        coerce=int,
        default=EntityType.INDIVIDUAL.value,
    )

    client_type_id = SelectField(
        "Client Type",
        choices=get_client_type_choices(),
        coerce=int,
        default=ClientType.RIGHT_HOLDER.value,
        validators=[DataRequired()],
    )

    # 基本情報
    name = StringField("Name", validators=[DataRequired(), MAX_LEN_255])
    name_kana = StringField("Kana", validators=[Optional(), MAX_LEN_255])
    birth_date = DateField("Birth Date", format="%Y-%m-%d", validators=[Optional()])

    # 住所・連絡先
    postal_code = StringField("ZIP Code", validators=[Optional(), MAX_LEN_20])
    address = StringField("Address", validators=[Optional(), MAX_LEN_255])
    phone_number = StringField("Phone Number", validators=[Optional(), MAX_LEN_50])
    fax = StringField("Fax", validators=[Optional(), MAX_LEN_50])
    email = StringField("Email", validators=[Optional(), Email(), MAX_LEN_255])

    # その他
    intention_confirmed_at = DateField("Intent Confirmation Date", format="%Y-%m-%d", validators=[Optional()])
    note = TextAreaField("Notes", validators=[Optional()])

    # 持分（equity）
    equity_numerator = IntegerField(
        "Equity Numerator (分子)",
        validators=[Optional(), NumberRange(min=0, message="0 以上で入力してください")],
    )
    equity_denominator = IntegerField(
        "Equity Denominator (分母)",
        validators=[Optional(), NumberRange(min=1, message="1 以上で入力してください")],
    )

    # 法人用
    representative_title = StringField(
        "代表者肩書",
        validators=[Optional(), Length(max=50)],
        default="代表取締役"  # ★ デフォルトを指定
    )
    representative_name = StringField(
        "代表者名",
        validators=[Optional(), Length(max=255)]
    )
    company_number = StringField(
        "会社法人等番号（12桁）",
        validators=[Optional(), Length(min=12, max=12, message="12桁で入力してください")]
    )

    # ------- 追加バリデーション -------
    def validate(self, extra_validators=None) -> bool:
        ok = super().validate(extra_validators=extra_validators)

        # 分子/分母は「両方空」or「両方あり」
        num = self.equity_numerator.data
        den = self.equity_denominator.data
        if (num is None) ^ (den is None):  # どちらか一方だけ
            msg = "分子/分母は両方入力するか両方空にしてください。"
            self.equity_numerator.errors.append(msg)
            self.equity_denominator.errors.append(msg)
            ok = False

        # 会社法人等番号（入っていれば 12 桁の数字に正規化・検証）
        raw = (self.company_number.data or "").strip()
        if raw:
            digits = "".join(ch for ch in raw if ch.isdigit())
            if len(digits) != 12:
                self.company_number.errors.append("会社法人等番号は数字12桁で入力してください。")
                ok = False
            else:
                # 正規化してフォーム値を置き換え（保存側でそのまま使える）
                self.company_number.data = digits

        return ok

class CorporateProfileForm(FlaskForm):
    representative_title = StringField("代表者肩書", validators=[Optional(), Length(max=50)])
    representative_name  = StringField("代表者名",   validators=[Optional(), Length(max=100)])
    # 会社法人等番号は 12 桁に（あなたのルールに合わせて）
    company_number = StringField(
        "会社法人等番号（12桁）",
        validators=[Optional(), Regexp(r"^\d{12}$", message="12桁の数字で入力してください")]
    )
    submit = SubmitField("保存")


class AddressChangeForm(FlaskForm):
    old_address = TextAreaField("旧住所", validators=[Optional(), Length(max=1000)],
                                render_kw={"rows": 3})
    new_address = TextAreaField("新住所", validators=[Optional(), Length(max=1000)],
                                render_kw={"rows": 3})
    change_date = DateField("住所変更日", validators=[Optional()], format="%Y-%m-%d")
    submit = SubmitField("保存")