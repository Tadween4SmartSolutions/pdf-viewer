from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        if not re.match(r'^[a-zA-Z0-9_]+$', username.data):
            raise ValidationError('Username can only contain letters, numbers, and underscores.')

class PDFUploadForm(FlaskForm):
    file = FileField('PDF File', validators=[DataRequired()])
    title = StringField('Title')
    author = StringField('Author')
    subject = StringField('Subject')
    is_public = BooleanField('Make Public', default=True)
    submit = SubmitField('Upload PDF')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    search_in = SelectField('Search In', choices=[
        ('filename', 'Filename'),
        ('content', 'Content'),
        ('all', 'All')
    ], default='all')
    submit = SubmitField('Search')