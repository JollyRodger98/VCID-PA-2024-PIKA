"""REST API for book data."""
from flask import Blueprint, request
from pydantic import ValidationError
from sqlalchemy import exc

from pika import db
from pika.models import Books, Series, Authors
from .auth import token_auth
from .data import ApiResponse, BookPage, BookBase, BookData, ApiBookDTO

bp = Blueprint("books", __name__)


@bp.route('/', methods=['GET'])
@token_auth.login_required
def get_books():
    """Endpoint to get a paginated list of books."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Books.query.order_by(Books.title).paginate(page=page, per_page=per_page)
    books = [BookData.from_orm(b).model_dump() for b in query]
    page = BookPage(
        first=1,
        last=query.pages,
        has_previous=query.has_prev,
        has_next=query.has_next,
        books=books
    )

    return ApiResponse(data=page).model_dump(mode='json')


@bp.route('/all', methods=['GET'])
@token_auth.login_required
def get_books_all():
    """
    Endpoint to get all book data. Please use sparingly.
    Generally use the endpoint /books to get a list of book data. Only use this endpoint if you specifically need
    to get *all* book data.
    """
    query = Books.query.all()
    books = [BookData.from_orm(b).model_dump() for b in query]
    return ApiResponse(data=books).model_dump()


@bp.route("/<int:book_id>", methods=['GET'])
@token_auth.login_required
def get_books_book_id(book_id):
    """
    Endpoint for getting book details.
    :param book_id: ID of book to return.
    :return:
    """
    query = Books.query.get(book_id)
    if not query:
        return ApiResponse(success=False, message="Book not found.", status_code=404).model_dump(), 404
    book = BookData.from_orm(query)
    return ApiResponse(data=book).model_dump(mode='json')


@bp.route('/', methods=['POST'])
@token_auth.login_required
def post_books():
    """Endpoint to add a new book."""
    data = request.get_json()
    try:
        book = ApiBookDTO.model_validate(data)
    except ValidationError as exception:
        error_data = []
        for e in exception.errors():
            error = {"type": e["type"], "location": "/".join(e["loc"]), "message": e["msg"]}
            error_data.append(error)
        return ApiResponse(success=False, message="Validation Error", details=error_data,
                           status_code=400).model_dump(), 400

    new_book = Books(**book.model_dump(exclude={"volume_nr_as_string", "series", "authors"}))

    if book.series:
        series_query = Series.query.get(book.series.series_id)
        if not series_query:
            return ApiResponse(success=False, message="Series not found",
                               details=f"Series with ID {book.series.series_id} does not exist",
                               status_code=404).model_dump(), 404
        new_book.series = series_query

    for author in book.authors:
        author_query = Authors.query.get(author.author_id)
        if not author_query:
            return ApiResponse(success=False, message="Author not found",
                               details=f"Author with ID {author.author_id} does not exist",
                               status_code=404).model_dump(), 404
        new_book.authors.append(author_query)

    db.session.add(new_book)
    db.session.commit()

    new_book = BookData.from_orm(new_book)
    return ApiResponse(data=new_book).model_dump()


@bp.route('/<int:book_id>', methods=['PUT'])
@token_auth.login_required
def put_books(book_id):
    """
    Endpoint for updating a book.
    :param book_id: ID of the book to update.
    """
    data = request.get_json()
    try:
        book = ApiBookDTO.model_validate(data)
    except ValidationError as exception:
        error_data = []
        for e in exception.errors():
            error = {"type": e["type"], "location": "/".join(e["loc"]), "message": e["msg"]}
            error_data.append(error)
        return ApiResponse(success=False, message="Validation Error", details=error_data,
                           status_code=400).model_dump(), 400

    target_book: Books = Books.query.get(book_id)
    if not target_book:
        return ApiResponse(success=False, message="Book not found", status_code=404).model_dump(), 404

    for key, value in book.model_dump(exclude={"authors", "series"}).items():
        setattr(target_book, key, value)

    if book.series:
        series_query = Series.query.get(book.series.series_id)
        if not series_query:
            return ApiResponse(success=False, message="Series not found",
                               details=f"Series with ID {book.series.series_id} does not exist",
                               status_code=404).model_dump(), 404
        target_book.series = series_query
    elif book.series is None:
        target_book.series = None

    author_update = []
    for author in book.authors:
        author_query = Authors.query.get(author.author_id)
        if not author_query:
            return ApiResponse(success=False, message="Author not found",
                               details=f"Author with ID {author.author_id} does not exist",
                               status_code=404).model_dump(), 404
        author_update.append(author_query)
    target_book.authors = author_update

    db.session.commit()

    updated_book = BookData.from_orm(target_book)
    return ApiResponse(data=updated_book).model_dump()


@bp.route('/<int:book_id>', methods=['DELETE'])
@token_auth.login_required
def delete_books(book_id):
    """
    Endpoint for deleting a book.
    :param book_id: ID of the book to delete.
    """
    target_books: Books = Books.query.get(book_id)
    if not target_books:
        return ApiResponse(success=False, message="Book not found", status_code=404).model_dump(), 404

    deleted_book = BookBase.from_orm(target_books)

    try:
        db.session.delete(target_books)
        db.session.commit()
    except exc.SQLAlchemyError:
        msg = f"Failed to delete series '{book_id}'. Series cannot be deleted when books are still assigned to it."
        return ApiResponse(success=False, message="Delete failed",
                           details=msg,
                           status_code=400).model_dump(), 400

    return ApiResponse(data=deleted_book.model_dump()).model_dump()
