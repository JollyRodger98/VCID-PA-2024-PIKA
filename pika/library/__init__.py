"""Library module of the flask app"""
# pylint: disable=wrong-import-position,cyclic-import
import requests
from flask import Blueprint

bp = Blueprint('library', __name__, template_folder="templates", static_folder="static")

session = requests.Session()
session.headers = {"Content-Type": "application/json"}

from . import routes

from .books import bp as books_bp
bp.register_blueprint(books_bp, url_prefix="/books")

from .series import bp as series_bp
bp.register_blueprint(series_bp, url_prefix="/series")

from .authors import bp as authors_bp
bp.register_blueprint(authors_bp, url_prefix="/authors")

__all__ = ['bp']
