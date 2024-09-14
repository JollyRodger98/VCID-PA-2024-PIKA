"""Library data objects"""
from .authors import AuthorData
from .base import BookBase, SeriesBase, AuthorBase
from .books import BookData
from .series import SeriesData

__all__ = ['BookData', 'SeriesData', 'AuthorData', 'BookBase', 'SeriesBase', 'AuthorBase']
