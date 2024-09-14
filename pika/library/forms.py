"""Forms for editing and adding books in the library blueprint."""
import requests
from flask import url_for, g, current_app
from flask_babel import lazy_gettext as _l, lazy_ngettext as _ln
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.datetime import DateField
from wtforms.fields.numeric import DecimalField
from wtforms.fields.simple import StringField, BooleanField, TextAreaField, SubmitField, HiddenField, URLField
from wtforms.validators import InputRequired, Optional

from .widgets import SubmitButton

ICON_ADD_NEXT = """
<div class="position-relative d-inline-block">
    <i class="bi bi-plus-lg fw-bolder"></i>
    <i class="bi bi-plus-lg position-absolute opacity-75" style="left: 2px; top: -3px;"></i>
</div>
"""
DEFAULT_INPUT_CLASS = "form-control"


def populate_series_choices():
    """Populates choices for series select field."""
    headers = {'Authorization': f'Bearer {g.token}'}
    response = requests.get(url_for("api.series.get_series_all", _external=True),
                            timeout=current_app.config.get('REQUEST_TIMEOUT'), headers=headers).json()
    data = response["data"]
    data.sort(key=lambda _series: _series["title"])
    choices = (('', _l('Choose...')), *((series["series_id"], series["title"]) for series in data))
    return choices


def populate_author_choices():
    """Populates choices for authors select field."""
    headers = {'Authorization': f'Bearer {g.token}'}
    response = requests.get(url_for("api.authors.get_authors_all", _external=True),
                            timeout=current_app.config.get('REQUEST_TIMEOUT'), headers=headers).json()
    data = response["data"]
    data.sort(key=lambda _author: _author["last_name"])
    choices = (('', _l('Choose...')),
               *((author["author_id"], f"{author["last_name"]}, {author["first_name"] or ""}") for author in data))
    return choices


class BookForm(FlaskForm):
    """Base class for book forms."""
    title = StringField(_l('Title*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    authors = SelectMultipleField(_l('Author*'), validators=[InputRequired()], choices=populate_author_choices,
                                  render_kw={"class_": "form-select", "size": 10})
    series = SelectField(_ln('Series', 'Series', 1), validators=[Optional()], choices=populate_series_choices,
                         render_kw={"class_": "form-select", "size": 10})
    volume_nr = DecimalField(_l('Volume Number'), validators=[Optional()],
                             render_kw={"step": 0.01, "min": 0, "class_": "form-control"})
    release_date = DateField(_l('Release Date*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    synopsis = TextAreaField(_l('Synopsis'), render_kw={"rows": 5, "class_": "form-control"})
    read_status = BooleanField(_l('Read Status'), render_kw={"class_": "form-check-input"})
    cover = FileField(_l('Book Cover*'), validators=[FileAllowed(['jpg', 'png'])], render_kw={"class_": "form-control"})

    def api_payload(self) -> dict[str, str | None]:
        """
        Generate payload for API from form data.
        :return Payload data
        :rtype: dict[str, str]
        """
        payload = {
            "title": self.data['title'],
            "release_date": self.data['release_date'].isoformat(),
            "synopsis": self.data['synopsis'],
            "read_status": self.data['read_status'],
            "authors": [{"author_id": int(_id)} for _id in self.data['authors']],
            "cover": self.data['cover'],
            "volume_nr": self.data['volume_nr'] and float(self.data['volume_nr']),
        }

        if self.data["series"]:
            payload.update({"series": {"series_id": int(self.data["series"])}})
        else:
            payload.update({"series": None})

        return payload


class AddBookForm(BookForm):
    """Form for adding a new book."""
    add = SubmitField(_l('Add'), widget=SubmitButton(icon='<i class="bi bi-plus-lg"></i>'))
    add_next = SubmitField(_l('Add Next'), widget=SubmitButton(icon=ICON_ADD_NEXT))


class EditBookForm(BookForm):
    """Form for editing a book."""
    book_id = HiddenField('Book ID')
    update = SubmitField(_l('Update'), widget=SubmitButton())


class DeleteBookForm(FlaskForm):
    """Form for deleting a book."""


class AddSeriesForm(FlaskForm):
    """Form for adding a series."""
    title = StringField(_l('Title*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    add = SubmitField(_l('Add'), widget=SubmitButton(icon='<i class="bi bi-plus-lg"></i>'))
    add_next = SubmitField(_l('Add Next'), widget=SubmitButton(icon=ICON_ADD_NEXT))


class EditSeriesForm(FlaskForm):
    """Form for editing a series"""
    title = StringField(_l('Title*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    update = SubmitField(_l('Update'), widget=SubmitButton())


class DeleteSeriesForm(FlaskForm):
    """Form for deleting a series"""


class AddAuthorForm(FlaskForm):
    """Form for adding a new author."""
    first_name = StringField(_l('First Name'), render_kw={"class_": "form-control"})
    last_name = StringField(_l('Last Name*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    add = SubmitField(_l('Add'), widget=SubmitButton(icon='<i class="bi bi-plus-lg"></i>'))
    add_next = SubmitField(_l('Add Next'), widget=SubmitButton(icon=ICON_ADD_NEXT))


class EditAuthorForm(FlaskForm):
    """Form to edit authors"""
    first_name = StringField(_l('First Name'), render_kw={"class_": "form-control"})
    last_name = StringField(_l('Last Name*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    update = SubmitField(_l('Update'), widget=SubmitButton())


class DeleteAuthorForm(FlaskForm):
    """Form to delete authors."""


class DeleteCoverForm(FlaskForm):
    """Form to delete book cover."""


class DownloadCoverForm(FlaskForm):
    """Form to download book cover."""


class ImportFromURLForm(FlaskForm):
    """Form to import from books from URL."""
    import_url = URLField(_l('Import URL*'), validators=[InputRequired()], render_kw={"class_": "form-control"})
    import_submit = SubmitField(_l('Import'), render_kw={"class_": "btn btn-primary"})
