"""Form used for posting and editing community items."""
from flask_wtf import FlaskForm
from wtforms.fields.simple import TextAreaField, SubmitField, HiddenField, StringField, EmailField
from wtforms.validators import DataRequired, InputRequired
from flask_babel import lazy_gettext as _l


class PostForm(FlaskForm):
    """Form for posting new thread posts."""
    content = TextAreaField(_l('Content'), validators=[InputRequired()], render_kw={"class": "form-control", "rows": 5})
    post = SubmitField(_l("Post"), render_kw={"class": "btn btn-success"})


class EditPostForm(PostForm):
    """Form for editing post content."""
    post_id = HiddenField(validators=[DataRequired()])
    author_id = HiddenField(validators=[DataRequired()])


class ContactForm(FlaskForm):
    """Form for handling data used to send an email."""
    subject = StringField(_l('Subject'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    message = TextAreaField(_l('Message'), validators=[InputRequired()], render_kw={"class_": "form-control", "rows": 6})
    email = EmailField(_l('Sender Email'), validators=[InputRequired()],
                       render_kw={"class_": "form-control", "autocomplete": "email"})
    send = SubmitField(_l('Send'), render_kw={"class": "btn btn-primary"})
