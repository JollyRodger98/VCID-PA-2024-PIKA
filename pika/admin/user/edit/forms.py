from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from flask_babel import lazy_gettext as _l

class EditNameForm(FlaskForm):
    """Form for setting or editing the user's name."""
    first_name = StringField(_l('First Name'), render_kw={"class": "form-control", "autocomplete": "give-name"})
    last_name = StringField(_l('Last Name'), render_kw={"class": "form-control", "autocomplete": "family-name"})
    save = SubmitField(_l('Save'), render_kw={"class": "btn btn-outline-primary"})


class EditEmailForm(FlaskForm):
    """Form for editing the user's email."""
    email = StringField(_l('E-Mail'), render_kw={"class": "form-control", "autocomplete": "email"})
    save = SubmitField(_l('Save'), render_kw={"class": "btn btn-outline-primary"})


class EditPasswordForm(FlaskForm):
    """Form setting a new password for the user."""
    old_password = PasswordField(_l('Old Password'), render_kw={
        "class": "form-control", "autocomplete": "current-password"
    })
    new_password = PasswordField(_l('New Password'), render_kw={
        "class": "form-control", "autocomplete": "new-password"
    })
    new_password_confirm = PasswordField(_l('Confirm New Password'), render_kw={
        "class": "form-control", "autocomplete": "new-password"}
                                         )
    submit = SubmitField(_l('Save'), render_kw={"class": "btn btn-outline-primary"})
