"""PIKA RESTful API."""
# pylint: disable=wrong-import-position,cyclic-import
from flask import Blueprint

from .data import BaseApiBookDTO, ApiBookDTO, ApiSeriesDTO, ApiAuthorDTO, BookPage, SeriesPage, AuthorsPage, \
    ApiResponse, BookData, SeriesData, AuthorData, BookBase, SeriesBase, AuthorBase

bp = Blueprint('api', __name__)

from .books import bp as books_bp

bp.register_blueprint(books_bp, url_prefix="/books")

from .series import bp as series_bp

bp.register_blueprint(series_bp, url_prefix="/series")

from .authors import bp as authors_bp

bp.register_blueprint(authors_bp, url_prefix="/authors")

__all__ = ['BaseApiBookDTO', 'ApiBookDTO', 'ApiSeriesDTO', 'ApiAuthorDTO', 'BookData', 'SeriesData', 'AuthorData',
           'BookBase', 'SeriesBase', 'AuthorBase', 'BookPage', 'SeriesPage', 'AuthorsPage', 'ApiResponse', 'bp']
