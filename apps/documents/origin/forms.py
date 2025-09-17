# apps/documents/origin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, HiddenField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from apps.documents.origin.constants import CauseType


class OriginDocumentForm(FlaskForm):
    client_id = HiddenField(validators=[DataRequired()])

    real_estate_description = TextAreaField(
        "不動産の表示",
        validators=[DataRequired(message="不動産の表示は必須です")]
    )

    # 当事者（テキストエリア: 1行1名）
    right_holders = TextAreaField(
        "権利者（甲）", validators=[DataRequired()],
        render_kw={"rows": 6,
                   "placeholder": "（例）\n（1/2）東京都…　山田太郎\n（1/2）東京都…　山田花子"}
    )
    obligation_holders = TextAreaField(
        "義務者（乙）", validators=[DataRequired()],
        render_kw={"rows": 6, "placeholder": "（例）\n（1/1）東京都…　佐藤次郎"}
    )

    # 登記原因
    cause_type = SelectField("登記原因", choices=CauseType.choices(), coerce=int, validators=[DataRequired()])
    cause_suffix = StringField(
        "補足",
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "必要に応じて追記"}
    )
    cause_text = TextAreaField("登記原因の事実または法律行為",
                               validators=[Optional()], render_kw={"rows": 6})

    contract_date = DateField("契約日", validators=[Optional()], format="%Y-%m-%d")
    payment_date = DateField("決済日", validators=[Optional()], format="%Y-%m-%d")

    submit = SubmitField("保存")
