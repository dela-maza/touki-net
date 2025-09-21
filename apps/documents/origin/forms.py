# apps/documents/origin/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, HiddenField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from apps.documents.origin.constants import CauseType


class OriginDocumentForm(FlaskForm):
    client_id = HiddenField(validators=[DataRequired()])


    # 当事者（テキストエリア: 1行1名）
    right_holders = TextAreaField(
        "権利者（甲）", validators=[DataRequired()],
        render_kw={"rows": 3,
                   "placeholder": "（例）\n（1/2）東京都…　山田太郎\n（1/2）東京都…　山田花子"}
    )
    obligation_holders = TextAreaField(
        "義務者（乙）", validators=[DataRequired()],
        render_kw={"rows": 3,
                   "placeholder": "（例）\n（1/1）東京都…　佐藤次郎"}
    )

    # 登記原因
    cause_type = SelectField("登記原因",
                             choices=CauseType.choices(),
                             coerce=int,
                             validators=[DataRequired()],
                             render_kw={"style": "width:480px;" })
    cause_suffix = StringField(
        "補足",
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "必要に応じて追記",
                   "style": "width:480px;" }
    )
    cause_fact = TextAreaField("登記原因の事実または法律行為",
                               validators=[Optional()], render_kw={"rows": 4})

    # 不動産の表示
    real_estate_description_1 = TextAreaField(
        "不動産の表示１", validators=[Optional()],
        render_kw={"rows": 18,
                   "placeholder": "不動産の表示（左）",
                   "style": "width:480px;" }
    )
    real_estate_description_2 = TextAreaField(
        "不動産の表示２", validators=[Optional()],
        render_kw={"rows": 18, "placeholder": "不動産の表示（右）",
                   "style": "width:480px;" }
    )

    submit = SubmitField("保存")
