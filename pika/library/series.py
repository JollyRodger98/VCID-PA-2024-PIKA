"""Endpoints and pages for series."""
import json

from flask import Blueprint, render_template, url_for, flash, redirect, request, abort, current_app
from flask_babel import gettext as _
from flask_login import login_required

from . import session
from .forms import AddSeriesForm, DeleteSeriesForm, EditSeriesForm
from .util import generate_pages

bp = Blueprint('series', __name__)


@bp.route('/', methods=['GET'])
@login_required
def index():
    """Page to display a paginated list of series."""
    page = request.args.get('page', 1, type=int)
    response = session.get(
        url_for("api.series.get_series", page=page, per_page=current_app.config.get('PER_PAGE'), _external=True),
        timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code)
    data = response.json()["data"]
    data["series"].sort(key=lambda x: x["title"])
    pages = generate_pages(page, 2, data["last"])
    return render_template("library/series/index.html", series_page=data, pages=pages, current_page=page)


@bp.route('/<int:series_id>', methods=['GET'])
@login_required
def details(series_id):
    """
    Page to display details of a single series.
    :param series_id: ID of the series to display.
    """
    response = session.get(url_for("api.series.get_series_series_id", series_id=series_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT'))
    if response.status_code != 200:
        abort(response.status_code, _("This series does not exist."))
    data = response.json()
    series_data = data["data"]
    series_data["books"].sort(key=lambda x: x["volume_nr"])
    return render_template("library/series/details.html", series=series_data, delete_series_form=DeleteSeriesForm())


@bp.route('/add', methods=['GET'])
@login_required
def add_page():
    """Page to add a new series."""
    form = AddSeriesForm()
    return render_template("library/series/add.html", form=form)


@bp.route('/add', methods=['POST'])
@login_required
def add_form():
    """Endpoint to handle add series form."""
    form = AddSeriesForm()

    if form.validate_on_submit():
        payload = json.dumps({"title": form.title.data})
        response = session.post(url_for("api.series.post_series", _external=True), data=payload,
                                timeout=current_app.config.get('REQUEST_TIMEOUT'))

        if response.status_code != 200:
            flash(_('Failed to add new series.'), 'danger')
            abort(response.status_code)

        if form.add_next.data is True:
            return redirect(url_for("library.series.add_page"))

        response = response.json()
        return redirect(url_for("library.series.details", series_id=response["data"]["series_id"]))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return render_template("library/series/add.html", form=form)


@bp.route('/<int:series_id>/edit', methods=['GET'])
@login_required
def edit_page(series_id):
    """
    Page for editing a series.
    :param series_id: ID of the series to edit.
    """
    response = session.get(url_for("api.series.get_series_series_id", series_id=series_id, _external=True),
                           timeout=current_app.config.get('REQUEST_TIMEOUT')).json()
    data = response["data"]

    default_data = {
        "title": data["title"],
    }

    form = EditSeriesForm(data=default_data)

    return render_template("library/series/edit.html", form=form)


@bp.route("/<int:series_id>/edit", methods=["POST"])
@login_required
def edit_form(series_id):
    """Endpoint to handle edit series form."""
    form = EditSeriesForm()
    if form.validate_on_submit():
        payload = json.dumps({
            "title": form.title.data,
        })
        response = session.put(url_for("api.series.put_series", series_id=series_id, _external=True), data=payload,
                               timeout=current_app.config.get('REQUEST_TIMEOUT'))
        if response.status_code != 200:
            flash(_("Server Error"))
            abort(response.status_code)

        response = response.json()
        return redirect(url_for("library.series.details", series_id=response["data"]["series_id"]))

    for field, message in form.errors.items():
        flash(f"{''.join(message)} ({field.title()})", "danger")

    return redirect(url_for("library.books.edit_page", series_id=series_id))


@bp.route("/<int:series_id>/delete", methods=["POST"])
@login_required
def delete_form(series_id):
    """Endpoint to handle delete series form."""
    form = DeleteSeriesForm()

    if form.validate_on_submit():
        response = session.delete(url_for("api.series.delete_series", series_id=series_id, _external=True))

        if response.status_code != 200:
            error = response.json()
            if response.status_code == 400 and error["message"].lower() == "delete failed":
                flash(_("Series cannot be deleted when books are still assigned to it."), "danger")
                return redirect(url_for("library.series.details", series_id=series_id))
            abort(response.status_code, response.text)

        flash(_("Series was deleted successfully."), "success")
        return redirect(url_for("library.series.index"))

    for error in form.errors:
        flash(f"{''.join(form.errors[error])} ({error})", "danger")

    return redirect(url_for("library.series.index"))
