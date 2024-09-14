"""Data models used by Pika API."""
from __future__ import annotations

from typing import List, Dict

from pydantic import BaseModel, SerializeAsAny

from ..library import BookData, SeriesData, AuthorData


class LibraryPage(BaseModel):
    """Default data for paginated library objects."""
    first: int
    last: int
    has_previous: bool
    has_next: bool


class BookPage(LibraryPage):
    """Paginated list of books."""
    books: List['BookData']


class SeriesPage(LibraryPage):
    """Paginated list of book series."""
    series: List['SeriesData']


class AuthorsPage(LibraryPage):
    """Paginated list of authors."""
    authors: List['AuthorData']


class ApiResponse(BaseModel):
    """Standard response for Pika API."""
    success: bool = True
    message: str = "Success"
    details: str | List = None
    status_code: int = 200
    data: SerializeAsAny[
        Dict | List | LibraryPage | 'BookData' | 'SeriesData' | 'AuthorData'] = None
