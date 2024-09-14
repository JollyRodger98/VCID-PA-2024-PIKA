"""General pages and endpoints for the library blueprint."""

import requests
from bs4 import BeautifulSoup
from flask import render_template, url_for, redirect, abort, current_app, g
from flask_login import login_required, current_user

from pika import db
from pika.models import Series, Authors
from . import bp, session
from .forms import AddBookForm, ImportFromURLForm
from .util import parse_goodreads_soup

PER_PAGE = current_app.config.get('PER_PAGE_ITEMS')
REQUEST_TIMEOUT = current_app.config.get('REQUEST_TIMEOUT')


@bp.errorhandler(404)
def page_not_found(error):
    """Handle Not Found error for Book, Series and Authors."""
    title = f'<i class=\"bi bi-question-circle me-2\"></i>{error.name}'
    return render_template("errors/404.html", title=title, description=error.description), 404


@bp.before_request
def before_request():
    """Check API token and load if missing"""
    if current_user.is_authenticated:
        current_app.logger.debug('API token: user is authenticated')
        current_app.logger.debug('API token: %s', current_user.token)
        g.token = current_user.token
        if not current_user.check_token(g.token):
            g.token = current_user.get_token()
            db.session.commit()
            current_app.logger.debug('API token new: %s', g.token)
        session.headers.update({"Authorization": f"Bearer {g.token}"})


@bp.route("/import/goodreads", methods=["GET"])
@login_required
def import_from_goodreads_page():
    """Page for importing books from goodreads.com"""
    form = ImportFromURLForm()
    return render_template("library/goodreads_import.html", form=form)


@bp.route("/import/preview", methods=["POST"])
@login_required
def import_from_goodreads_form():
    """
    Endpoint to handle import book form. Currently only works for goodreads.com.
    """
    form = ImportFromURLForm()
    if form.validate_on_submit():
        response = requests.get(form.import_url.data, timeout=REQUEST_TIMEOUT)

        if response.status_code != 200:
            abort(response.status_code, response.text)

        soup = BeautifulSoup(response.text, "html.parser")
        goodreads_data = parse_goodreads_soup(soup)

        default_data = {
            "title": goodreads_data["title"],
            "release_date": goodreads_data["release_date"],
            "synopsis": goodreads_data["synopsis"],
            "volume_nr": goodreads_data["volume_nr"],
        }

        authors_result, total = Authors.search(goodreads_data["author_name"], 1, 10)
        if total != 0:
            author = authors_result.first()
            default_data["authors"] = (_author for _author in [author.author_id])

        series_result, total = Series.search(goodreads_data["series_title"], 1, 10)
        if total != 0:
            series = series_result.first()
            default_data.update({"series": series.series_id})

        book_form = AddBookForm(data=default_data, formdata=None)
        return render_template("library/books/add.html", form=book_form)

    return redirect(url_for("library.import_from_goodreads_page"))
