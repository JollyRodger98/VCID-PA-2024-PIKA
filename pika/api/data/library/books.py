"""Data models for book data. Includes some data permutations."""
from __future__ import annotations

from typing import Optional, List

from pydantic import Field

from .base import BookBase, SeriesBase, AuthorBase


class BookAuthor(AuthorBase):
    """Author data used when nested in a book data model."""
    author_id: int


class BookSeries(SeriesBase):
    """Series data used when nested in a book data model."""
    series_id: int


class BookData(BookBase):
    """Standard object used to store book data."""
    series: Optional["BookSeries"]
    authors: List["BookAuthor"] = Field(min_length=1)

    def api_payload(self):
        """Generate API payload from pydantic model."""
        payload = {
            "title": self.title,
            "release_date": self.release_date.isoformat(),
            "synopsis": self.synopsis,
            "read_status": self.read_status,
            # pylint: disable=not-an-iterable
            "authors": [{"author_id": int(_author.author_id)} for _author in self.authors],
            "cover": self.cover,
            "volume_nr": self.volume_nr and float(self.volume_nr),
        }
        if self.series:
            payload.update({"series": {"series_id": int(self.series.series_id)}})
        else:
            payload.update({"series": None})

        return payload
