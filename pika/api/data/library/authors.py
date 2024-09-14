"""Data models for author data. Includes some data permutations."""
from __future__ import annotations

from typing import Optional, List

from pydantic import computed_field

from .base import BookBase, SeriesBase, AuthorBase


class AuthorBook(BookBase):
    """Book data used when nested in an author data model."""
    series: Optional["SeriesBase"]


class AuthorData(AuthorBase):
    """Standard object used to store author data."""
    books: Optional[List["AuthorBook"]]

    @computed_field
    def series(self) -> Optional[List["SeriesBase"]]:
        """Compiles a list of all series in which the current author has books."""
        series = []
        for book in self.books:
            if book.series:
                series.append(book.series)
        return list(set(s for s in series))
