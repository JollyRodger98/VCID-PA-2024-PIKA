"""Author data model for API"""
from typing import Optional, List

from pydantic import BaseModel, Field

from .books import BaseApiBookDTO


class ApiAuthorDTO(BaseModel):
    """Author data model for API input (pseudo JSON schema)."""
    first_name: Optional[str]
    last_name: str
    books: Optional[List[BaseApiBookDTO]] = Field(default=None, min_items=1)
