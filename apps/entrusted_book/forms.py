### apps/entrusted_form/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length


class EntrustedBookForm(FlaskForm):
    name = StringField('name',
                       validators=[DataRequired(message="受託名は必須です"),
                                   Length(max=255)])
    note = TextAreaField('note',
                         validators=[Optional(),
                                     Length(max=255)])
