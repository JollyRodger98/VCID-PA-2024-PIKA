"""Data objects for library an pika API"""
from .api import BaseApiBookDTO, ApiBookDTO, ApiSeriesDTO, ApiAuthorDTO, BookPage, SeriesPage, AuthorsPage, ApiResponse
from .library import BookData, SeriesData, AuthorData, BookBase, SeriesBase, AuthorBase

__all__ = ['BaseApiBookDTO', 'ApiBookDTO', 'ApiSeriesDTO', 'ApiAuthorDTO', 'BookData', 'SeriesData', 'AuthorData',
           'BookBase', 'SeriesBase', 'AuthorBase', 'BookPage', 'SeriesPage', 'AuthorsPage', 'ApiResponse']
