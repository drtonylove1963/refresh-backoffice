from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from wtforms.widgets import PasswordInput

class VisitorForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=20)])
    visit_date = DateField('Visit Date', validators=[DataRequired()])

class ChildForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    special_instructions = TextAreaField('Special Instructions')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')