"""Endpoints and pages for books."""
import json

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_login import login_required
from flask_babel import lazy_gettext as _l, gettext as _, lazy_ngettext as _ln

from . import session
from .forms import AddAuthorForm, DeleteAuthorForm, EditAuthorForm
from .util import generate_pages

bp = Blueprint('authors', __name__)


@bp.route('/authors', methods=['GET'])
@login_required
def index():
    """Page with a paginated list of authors."""
    page = request.args.get('page', 1, type=int)
    response = session.get(
        url_for("api.authors.get_authors", page=page, per_page=current_app.config.get('PER_PAGE'), _external=True),
        timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code)
    data = response.json()["data"]
    data["authors"].sort(key=lambda x: x["last_name"])
    pages = generate_pages(page, 2, data["last"])
    return render_template("library/authors/index.html", authors_page=data, pages=pages, current_page=page)


@bp.route('/authors/<int:author_id>', methods=['GET'])
@login_required
def details(author_id):
    """
    Page to display the author's books and series.
    :param author_id: ID of the author to display.
    """
    response = session.get(url_for("api.authors.get_authors_author_id", author_id=author_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code, _("This author does not exist."))
    data = response.json()
    author_data = data["data"]
    return render_template("library/authors/details.html", author=author_data, delete_author_form=DeleteAuthorForm())


@bp.route('/authors/add', methods=['GET'])
@login_required
def add_page():
    """Page for adding a new author."""
    form = AddAuthorForm()
    return render_template("library/authors/add.html", form=form)


@bp.route('/authors/add', methods=['POST'])
@login_required
def add_form():
    """Endpoint to handle add authors form."""
    form = AddAuthorForm()

    if form.validate_on_submit():
        payload = json.dumps({
            "first_name": form.first_name.data or None,
            "last_name": form.last_name.data
        })
        response = session.post(url_for("api.authors.post_authors", _external=True), data=payload,
                                timeout=current_app.config.get('REQUEST_TIMEOUT'))

        if response.status_code != 200:
            flash(_('Failed to add new author.'), 'danger')
            abort(response.status_code)

        if form.add_next.data is True:
            return redirect(url_for("library.authors.add_page"))

        response = response.json()
        return redirect(url_for("library.authors.details", author_id=response["data"]["author_id"]), )

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return render_template("library/authors/add.html", form=form)


@bp.route("/authors/<int:author_id>/edit", methods=["GET"])
@login_required
def edit_page(author_id):
    """
    Page for editing an author.
    :param author_id: ID of the author to edit.
    """
    response = session.get(url_for("api.authors.get_authors_author_id", author_id=author_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
    data = response["data"]

    default_data = {
        "first_name": data["first_name"],
        "last_name": data["last_name"],
    }

    form = EditAuthorForm(data=default_data)

    return render_template("library/authors/edit.html", form=form)


@bp.route("/authors/<int:author_id>/edit", methods=["POST"])
@login_required
def edit_form(author_id):
    """
    Endpoint for handling edit author form.
    :param author_id: ID of the author to edit.
    """
    form = EditAuthorForm()
    if form.validate_on_submit():
        payload = json.dumps({
            "first_name": form.first_name.data or None,
            "last_name": form.last_name.data
        })
        headers = {"Content-Type": "application/json"}
        response = session.put(url_for("api.authors.put_authors", author_id=author_id, _external=True),
                               headers=headers, data=payload, timeout=current_app.config.get('REQUEST_TIMEOUT'))
        if response.status_code != 200:
            flash(_("Server Error"))
            abort(response.status_code)

        response = response.json()
        return redirect(url_for("library.authors.details", author_id=response["data"]["author_id"]))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return redirect(url_for("library.authors.edit_page", author_id=author_id))


@bp.route("/authors/<int:author_id>/delete", methods=["POST"])
@login_required
def delete_form(author_id):
    """Endpoint for handling delete author form."""
    form = DeleteAuthorForm()

    if form.validate_on_submit():
        response = session.delete(url_for("api.authors.delete_authors", author_id=author_id, _external=True))

        if response.status_code != 200:
            error = response.json()
            if response.status_code == 400 and error["message"].lower() == "delete failed":
                flash(_("Authors cannot be deleted when books are still assigned to them."), "danger")
                return redirect(url_for("library.authors.details", author_id=author_id))
            abort(response.status_code, response.text)

        flash(_("Author was deleted successfully."), "success")
        return redirect(url_for("library.authors.index"))

    for error in form.errors:
        flash(f"{''.join(form.errors[error])} ({error})", "danger")

    return redirect(url_for("library.authors.index"))
