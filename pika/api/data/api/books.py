"""Book data model for API"""
import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class BaseApiBookDTO(BaseModel):
    """Base model for API DTO book data."""
    book_id: int
    title: str = None
    volume_nr: Optional[float] = None
    read_status: bool = None
    release_date: datetime.date = None
    synopsis: Optional[str] = None
    cover: Optional[str] = None


class ApiBookDTO(BaseModel):
    """Book data model for API input (pseudo JSON schema)."""

    class _ApiAuthorDTO(BaseModel):
        author_id: int
        first_name: str = None
        last_name: str = None

    class _ApiSeriesDTO(BaseModel):
        series_id: int
        title: str = None

    title: str
    series: Optional[_ApiSeriesDTO]
    authors: List[_ApiAuthorDTO] = Field(min_items=1)
    volume_nr: Optional[float] = None
    read_status: bool = False
    release_date: datetime.date = datetime.date.today()
    synopsis: Optional[str] = None
    cover: Optional[str] = None
