"""Authentication forms"""
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l

class LoginForm(FlaskForm):
    """Form for logging in with a existing user account."""
    username = StringField(_l('Username'), validators=[DataRequired()], render_kw={
        "class": "form-control me-2", "placeholder": _l("Username"), "autocomplete": "username"
    })
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={
        "class": "form-control me-2", "placeholder": _l("Password"), "autocomplete": "current-password"
    })
    login = SubmitField(_l('Login'), render_kw={"class": "btn btn-outline-success me-1"})


class RegistrationForm(FlaskForm):
    """Form for registering a new user account."""
    new_username = StringField(_l('Username'), validators=[DataRequired()], render_kw={
        "class": "form-control", "placeholder": _l('Username'), "autocomplete": "username"
    })
    new_email = EmailField(_l('E-Mail'), validators=[DataRequired()], render_kw={
        "class": "form-control", "placeholder": _l('E-Mail'), "autocomplete": "email"
    })
    new_password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={
        "class": "form-control", "placeholder": _l('Password'), "autocomplete": "new-password"
    })
    new_confirm_password = PasswordField(_l('Confirm Password'), validators=[DataRequired()], render_kw={
        "class": "form-control", "placeholder": _l('Confirm Password'), "autocomplete": "new-password"
    })
    register = SubmitField(_l('Register'), render_kw={"class": "btn btn-outline-success"})
