from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class MemberForm(FlaskForm):
    """Form for member creation/editing."""
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    is_active = BooleanField('Active')
    church_status = StringField('Church Status', validators=[Optional()])
    submit = SubmitField('Save')
