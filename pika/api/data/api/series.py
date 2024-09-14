"""Series data model for API"""
from typing import Optional, List

from pydantic import BaseModel, Field

from .books import BaseApiBookDTO


class ApiSeriesDTO(BaseModel):
    """Series data model for API input (pseudo JSON schema)."""
    title: str
    books: Optional[List[BaseApiBookDTO]] = Field(default=None, min_items=1)
