### apps/entrusted_book/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, DateField,TextAreaField
from wtforms.validators import DataRequired, Optional, Length


class EntrustedBookForm(FlaskForm):
    name = StringField('name',
                       validators=[DataRequired(message="受託名は必須です"),
                                   Length(max=255)])
    note = TextAreaField('note',
                         validators=[Optional(),
                                     Length(max=255)])
    contract_date = DateField('Contract Date',
                              format="%Y-%m-%d",
                              validators=[Optional()])
    execution_date = DateField('Execution Date',
                               format="%Y-%m-%d",
                               validators=[Optional()])