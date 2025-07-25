### property_description.forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length

class EntrustedBookForm(FlaskForm):
    name = StringField(
        '受託簿名',
        validators=[DataRequired(), Length(max=255)]
    )
    note = TextAreaField(
        '備考',
        validators=[Optional(), Length(max=255)]
    )