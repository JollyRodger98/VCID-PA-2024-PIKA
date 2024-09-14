"""Base data models for library data"""
import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class BookBase(BaseModel):
    """Base data model for books."""
    model_config = ConfigDict(from_attributes=True)
    book_id: int = None
    title: str
    release_date: datetime.date
    read_status: bool
    volume_nr: Optional[float | int]
    synopsis: Optional[str]
    cover: Optional[str]

    @computed_field
    def volume_nr_as_string(self) -> Optional[str]:
        """Computed pydantic field for formatted string representation of volume number"""
        if isinstance(self.volume_nr, float):
            if self.volume_nr.is_integer():
                return f"{self.volume_nr:.0f}"
            return f"{self.volume_nr}"
        return None


class SeriesBase(BaseModel):
    """Base data model for series."""

    def __hash__(self) -> int:
        return hash((type(self),) + tuple(self.__dict__.values()))

    model_config = ConfigDict(from_attributes=True)
    series_id: int = None
    title: str


class AuthorBase(BaseModel):
    """Base data model for authors."""
    model_config = ConfigDict(from_attributes=True)
    author_id: int = None
    first_name: Optional[str]
    last_name: str

    @computed_field
    def full_name(self) -> str:
        """Computed pydantic field for the full name of the author."""
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name
