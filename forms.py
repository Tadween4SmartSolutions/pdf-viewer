from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FileField, TextAreaField, SelectField, IntegerField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from wtforms.fields import DateField, TimeField
import re
from datetime import datetime, timedelta

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

class ShareForm(FlaskForm):
    # Expiration settings
    expiration_type = SelectField('Expiration', choices=[
        ('never', 'Never Expire'),
        ('date', 'Expire on Date'),
        ('days', 'Expire after Days'),
        ('downloads', 'Expire after Downloads')
    ], default='days')
    
    expires_at = DateTimeField('Expiration Date', format='%Y-%m-%d %H:%M', 
                              validators=[Optional()],
                              default=datetime.utcnow() + timedelta(days=7))
    
    days_valid = IntegerField('Days Valid', 
                             validators=[Optional(), NumberRange(min=1)],
                             default=7)
    
    max_access_count = IntegerField('Max Number of Accesses', 
                                   validators=[Optional(), NumberRange(min=1)],
                                   default=10)
    
    # Access settings
    allow_download = BooleanField('Allow Download', default=True)
    password = PasswordField('Password (Optional)', 
                            validators=[Optional(), Length(min=4)])
    
    # Share information
    description = TextAreaField('Description (Optional)',
                               validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Create Share Link')
    
    def validate(self, **kwargs):
        initial_validation = super(ShareForm, self).validate()
        if not initial_validation:
            return False
        
        if self.expiration_type.data == 'date' and not self.expires_at.data:
            self.expires_at.errors.append('Please select an expiration date')
            return False
        
        if self.expiration_type.data == 'days' and not self.days_valid.data:
            self.days_valid.errors.append('Please enter number of days')
            return False
        
        if self.expiration_type.data == 'downloads' and not self.max_access_count.data:
            self.max_access_count.errors.append('Please enter maximum number of accesses')
            return False
        
        return True