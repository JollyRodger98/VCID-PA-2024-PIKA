"""Endpoints and pages for books."""
import json
import os.path
from datetime import date

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, send_from_directory, \
    current_app
from flask_babel import gettext as _
from flask_login import login_required
from werkzeug.datastructures import FileStorage

from pika.api import BookData
from . import session
from .forms import AddBookForm, DeleteBookForm, DeleteCoverForm, DownloadCoverForm, EditBookForm
from .util import generate_pages, put_book_payload

bp = Blueprint('books', __name__)


@bp.route('/books', methods=['GET'])
@login_required
def index():
    """Page wit a paginated list of all books."""
    page = request.args.get('page', 1, type=int)
    response = session.get(
        url_for("api.books.get_books", page=page, per_page=current_app.config.get('PER_PAGE'), _external=True),
        timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code)
    data = response.json()["data"]

    pages = generate_pages(page, 1, data["last"])
    books = [BookData.model_validate(book) for book in data["books"]]
    last_page = data.get("last")

    return render_template("library/books/index.html", books=books, pages=pages, current_page=page,
                           last_page=last_page)


@bp.route('/books/<int:book_id>', methods=['GET'])
@login_required
def details(book_id):
    """
    Page to display all details to a single book.
    :param book_id: ID of the book to display.
    :return:
    """
    response = session.get(url_for("api.books.get_books_book_id", book_id=book_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code, _("This book does not exist."))

    book_data = BookData.model_validate(response.json()['data'])
    return render_template("library/books/details.html", book=book_data, delete_cover_form=DeleteCoverForm(),
                           download_cover_form=DownloadCoverForm(), delete_book_form=DeleteBookForm())


@bp.route('/books/add', methods=['GET'])
@login_required
def add_page():
    """Page to add a book."""
    form = AddBookForm()
    return render_template("library/books/add.html", form=form)


@bp.route('/books/add', methods=['POST'])
@login_required
def add_form():
    """Endpoint to handle the add book form."""
    form = AddBookForm()

    if form.validate_on_submit():
        payload = form.api_payload()
        payload.update({"cover": None})

        response = session.post(url_for("api.books.post_books", _external=True), data=json.dumps(payload),
                                timeout=current_app.config.get('REQUEST_TIMEOUT'))

        if response.status_code != 200:
            flash(_("Server Error"))
            abort(response.status_code, response.text)

        if form.add_next.data is True:
            return redirect(url_for("library.books.add_page"))

        response = response.json()
        return redirect(url_for("library.books.details", book_id=response["data"]["book_id"]))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field})")

    return render_template("library/books/add.html", form=form)


@bp.route("/books/<int:book_id>/edit", methods=["GET"])
@login_required
def edit_page(book_id):
    """
    Page to edit a book.
    :param book_id:
    :return:
    """
    response = session.get(url_for("api.books.get_books_book_id", book_id=book_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
    data = response["data"]

    default_data = {
        "book_id": book_id,
        "title": data["title"],
        "series": data["series"] and data["series"]["series_id"],  # Returns series_id if key 'series' is *not* None
        "volume_nr": data["volume_nr"],
        "authors": (author["author_id"] for author in data["authors"]),
        "synopsis": data["synopsis"],
        "release_date": date.fromisoformat(data["release_date"]),
        "read_status": data["read_status"],
    }

    form = EditBookForm(data=default_data)
    return render_template("library/books/edit.html", form=form)


@bp.route("/books/<int:book_id>/edit", methods=["POST"])
@login_required
def edit_form(book_id):
    """
    Endpoint to handle the edit book form.
    :param book_id: ID of the book to edit.
    """

    form = EditBookForm()
    if form.validate_on_submit():
        response = session.get(url_for("api.books.get_books_book_id", book_id=book_id, _external=True),
                               timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
        book_data = BookData.model_validate(response["data"])
        payload = put_book_payload(form, book_data)

        response = session.put(url_for("api.books.put_books", book_id=book_id, _external=True),
                               data=json.dumps(payload), timeout=current_app.config.get('REQUEST_TIMEOUT'))
        if response.status_code != 200:
            abort(response.status_code)

        if isinstance(form.cover.data, FileStorage):
            file_name = payload.get("cover")
            form.cover.data.save(os.path.join(bp.static_folder, file_name))
            if book_data.cover:
                os.remove(os.path.join(bp.static_folder, book_data.cover))

        response = response.json()
        return redirect(url_for("library.books.details", book_id=response["data"]["book_id"]))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return redirect(url_for("library.books.edit_page", book_id=book_id))


@bp.route("/books/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_form(book_id: int):
    """
    Endpoint to handle the delete book form.
    :param book_id: ID of the book to delete.
    """
    form = DeleteBookForm()
    if form.validate_on_submit():
        response = session.delete(url_for("api.books.delete_books", book_id=book_id, _external=True))
        if response.status_code != 200:
            abort(response.status_code)

        deleted_book = response.json().get("data")
        if deleted_book["cover"]:
            os.remove(os.path.join(bp.static_folder, deleted_book["cover"]))

        return redirect(url_for("library.books.index"))

    for error in form.errors:
        flash(f"{''.join(form.errors[error])} ({error})", "danger")
    return redirect(url_for("library.books.details", book_id=book_id))


@bp.route("books/<int:book_id>/cover/delete", methods=["POST"])
@login_required
def cover_delete(book_id: int):
    """Endpoint to delete a book cover."""
    form = DeleteCoverForm()
    if form.validate_on_submit():
        response = session.get(url_for("api.books.get_books_book_id", book_id=book_id, _external=True),
                               timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
        book_data = BookData.model_validate(response["data"])
        if book_data.cover is None:
            flash(_("This book does not have a cover image."), "warning")
            return redirect(url_for("library.books.details", book_id=book_id))
        payload = book_data.api_payload()
        payload.update({"cover": None})
        response = session.put(url_for("api.books.put_books", book_id=book_id, _external=True),
                               data=json.dumps(payload), timeout=current_app.config.get('REQUEST_TIMEOUT'))

        if response.status_code != 200:
            abort(response.status_code)

        os.remove(os.path.join(bp.static_folder, book_data.cover))
        return redirect(url_for("library.books.details", book_id=book_id))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return redirect(url_for("library.books.details", book_id=book_id))


@bp.route("books/<int:book_id>/cover/download", methods=["POST"])
@login_required
def cover_download(book_id: int):
    """Endpoint to send book cover image for downloading."""
    form = DownloadCoverForm()
    if form.validate_on_submit():
        response = session.get(url_for("api.books.get_books_book_id", book_id=book_id, _external=True),
                               timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
        book_data = response["data"]

        if book_data.get("cover") is None:
            flash(_("This book does not have a cover image."), "warning")
            return redirect(url_for("library.books.details", book_id=book_id))

        return send_from_directory(bp.static_folder, book_data.get("cover"), as_attachment=True)

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return redirect(url_for("library.books.details", book_id=book_id))
