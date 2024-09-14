"""Forms used in the user administration and settings"""
from flask_wtf import FlaskForm
from wtforms.fields.simple import HiddenField, BooleanField


class BaseHiddenForm(FlaskForm):
    """Base form for sending simple post forms with user id"""
    user_id = HiddenField()


class RenewTokenForm(BaseHiddenForm):
    """Form for renewing a token."""


class RevokeTokenForm(BaseHiddenForm):
    """Form for revoking tokens for a user."""


class EnableDisableForm(BaseHiddenForm):
    """Form for enabling or disabling a user."""


class RoleChangeForm(BaseHiddenForm):
    """Form for changing the role of a user."""
    role_assigned = BooleanField('Role Assigned', render_kw={"class": "form-control"})
    role_id = HiddenField()


class SendActivationEmailForm(BaseHiddenForm):
    """Form for sending activation email."""
