"""Utility functions for Pika API."""
from typing import Literal

from pydantic import ValidationError

from pika.models import Books
from .data import BaseApiBookDTO, ApiBookDTO, ApiSeriesDTO, ApiAuthorDTO

DTO = {
    "book": ApiBookDTO,
    "series": ApiSeriesDTO,
    "author": ApiAuthorDTO,
}


class APIValidationError(Exception):
    """Exception raised when validation of DTO fails."""

    def __init__(self, errors: list):
        super().__init__("Input data failed the validation.")
        self.errors = errors


def validate_dto(request_data: dict,
                 dto: Literal['book', 'series', 'author']) -> ApiBookDTO | ApiSeriesDTO | ApiAuthorDTO:
    """
    Validate input data against DTO.

    :raises APIValidationError: When pydantic ``.model_validate()`` of :class:`pydantic.BaseModel` method fails.

    :param request_data: Raw request data.
    :param dto: Type of DTO to validate against.
    :return: This return the validated DTO or raises an exception with details about the error.
    """
    try:
        data = DTO[dto].model_validate(request_data)
        return data
    except ValidationError as exc:
        error_data = []
        for _error in exc.errors():
            error = {"type": _error["type"], "location": "/".join(_error["loc"]), "message": _error["msg"]}
            error_data.append(error)
        raise APIValidationError(errors=error_data) from exc


class BookNotFound(Exception):
    """Raised when a book is not found in the database."""
    def __init__(self, book_id, book_title) -> None:
        super().__init__(f"Book {book_id} not found.")
        self.book_id = book_id
        self.book_title = book_title


def new_books_list(books: list[BaseApiBookDTO]) -> list[Books]:
    """
    Generate a list of ORM book objects from the API input data. Queries the database for books and raises an
    exception if an error occurs.

    :raises BookNotFound: When *any* book in the list is not found in the database.

    :param books: A list of DTO book objects.
    :return: A list of ORM book objects.
    """
    new_books = []
    for book in books:
        response = Books.query.get(book.book_id)
        if response is None:
            raise BookNotFound(book.book_id, book.title)
        new_books.append(response)
    return new_books
