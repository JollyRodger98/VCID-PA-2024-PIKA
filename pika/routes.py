"""Global routes and context injections"""
import os
from hashlib import md5

from flask import current_app, render_template, send_from_directory, request, g, redirect, url_for, session
from flask_login import current_user, login_required
from werkzeug.exceptions import HTTPException

from pika.api import BookData, SeriesData, AuthorData
from pika.auth.forms import LoginForm
from pika.models import Books, Series, Authors
from .forms import SearchForm


@current_app.context_processor
def inject_login_form() -> dict[str, LoginForm]:
    """Inject Login form for navbar login"""
    return {"login_form": LoginForm(prefix="nav")}


@current_app.context_processor
def inject_active():
    """Inject active page based on blueprint and path"""
    active_pages = {}
    if request.path == "/" and request.blueprint is None:
        active_pages.update({"home_active": True})
    if request.blueprint == "library":
        active_pages.update({'library_active': True})
    if request.blueprint == "community":
        active_pages.update({'community_active': True})
    return {"active_pages": active_pages}


# def handle_exception(e):
#     if isinstance(e, HTTPException):
#         return e
#
#     current_app.logger.critical(e)
#     return "<h1>A server error occurred</h1>", 500


@current_app.errorhandler(HTTPException)
def http_exception(e):
    """Handle all HTTP exceptions."""
    status_code = e.code

    if status_code not in [401, 404]:
        return e

    if status_code == 404:
        title = f'<i class=\"bi bi-file-earmark me-2\"></i>{e.name}'
        message = "The requested Page was not found on the server."
    else:
        title = e.name
        message = e.description

    # noinspection PyUnresolvedReferences
    return render_template(f"errors/{status_code}.html", title=title, description=message), e.code


@current_app.before_request
def before_request():
    """Make search form globally available."""
    if current_user.is_authenticated:
        g.search_form = SearchForm()


@current_app.route('/')
def index():
    """Redirect root path to home page"""
    recent_releases = Books.query.order_by(Books.release_date.desc()).limit(10).all()
    recent_releases = [BookData.from_orm(book) for book in recent_releases]
    return render_template("index.html", recent_releases=recent_releases)


@current_app.route('/search')
@login_required
def search():
    """Endpoint to search for library objects and return result page."""
    if not g.search_form.validate():
        return redirect(url_for('index'))
    results, total = Books.search(g.search_form.q.data, 1, 10)
    book_results = []
    if not total == 0:
        for book in results.all():
            book_results.append(BookData.from_orm(book))

    results, total = Series.search(g.search_form.q.data, 1, 10)
    series_results = []
    if not total == 0:
        for series in results.all():
            series_results.append(SeriesData.from_orm(series))

    results, total = Authors.search(g.search_form.q.data, 1, 10)
    author_results = []
    if not total == 0:
        for author in results.all():
            author_results.append(AuthorData.from_orm(author))

    return render_template(
        "search.html",
        query=g.search_form.q.data,
        book_results=book_results,
        series_results=series_results,
        author_results=author_results,
        total=total)


@current_app.route("/favicon.ico")
def favicon():
    """Serve the favicon file"""
    return send_from_directory(os.path.join(current_app.root_path, 'static/img'), "favicon.png")


@current_app.route("/icon")
def icon():
    """Serve the user icon file"""
    url = f'https://www.gravatar.com/avatar/{md5(current_user.email.encode()).hexdigest()}?d=identicon'
    return redirect(url)


@current_app.route('/language', methods=['GET'])
def language():
    session['lang'] = request.args.get('lang')
    return redirect(request.referrer)

# @current_app.route('/send_mail', methods=['GET'])
# def test_endpoint():
#     from auth.mail import send_email
#     from datetime import datetime, timedelta, timezone
#     import jwt
#     token = jwt.encode(
#         {'user_id': 1, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
#         key=current_app.config['SECRET_KEY'],
#         algorithm='HS256'
#     )
#
#     send_email('twaldesbuehl@gmail.com',
#                'Activate PIKA Account',
#                render_template('mail/activation/activation.txt',
#                                username=current_user.username,
#                                token=token),
#                render_template('mail/activation/activation.html',
#                                username=current_user.username,
#                                token=token)
#                )
#     return redirect(url_for('index'))
