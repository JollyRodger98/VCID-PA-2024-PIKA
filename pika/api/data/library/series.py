"""Data models for series data. Includes some data permutations."""
from __future__ import annotations

from typing import Optional, List

from pydantic import computed_field

from .base import BookBase, SeriesBase, AuthorBase


class SeriesBook(BookBase):
    """Book data used when nested in a series data model."""
    authors: Optional[List["AuthorBase"]]


class SeriesData(SeriesBase):
    """Standard object used to store series data."""
    books: Optional[List["SeriesBook"]]

    @computed_field
    def book_count(self) -> int:
        """Computed pydantic field for book count in each series."""
        return len(self.books)
