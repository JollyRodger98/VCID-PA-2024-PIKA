"""REST API for author data."""
from flask import Blueprint, request
from sqlalchemy import exc

from pika import db
from pika.models import Authors
from .auth import token_auth
from .data import ApiResponse, AuthorsPage, AuthorBase, AuthorData
from .util import validate_dto, new_books_list, APIValidationError, BookNotFound

bp = Blueprint("authors", __name__)


@bp.route('/', methods=['GET'])
@token_auth.login_required
def get_authors():
    """Endpoint to get a paginated list of authors"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Authors.query.order_by(Authors.last_name).paginate(page=page, per_page=per_page)
    authors = [AuthorData.from_orm(s).model_dump() for s in query]
    page = AuthorsPage(
        first=1,
        last=query.pages,
        has_previous=query.has_prev,
        has_next=query.has_next,
        authors=authors
    )

    return ApiResponse(data=page).model_dump()


@bp.route('/all', methods=['GET'])
@token_auth.login_required
def get_authors_all():
    """
    Endpoint to get all authors data. Please use sparingly.
    Generally use the endpoint /authors to get a list of author data. Only use this endpoint if you specifically need
    to get *all* authors data.
    """
    query = Authors.query.all()
    authors = [AuthorData.from_orm(a).model_dump() for a in query]
    return ApiResponse(data=authors).model_dump()


@bp.route('/<int:author_id>', methods=['GET'])
@token_auth.login_required
def get_authors_author_id(author_id):
    """
    Endpoint for getting a specific author.
    :param author_id: ID of the author to return.
    :return:
    """
    query = Authors.query.get(author_id)
    if query is None:
        return ApiResponse(success=False, message="Author not found.", status_code=404).model_dump(), 404
    author = AuthorData.from_orm(query)
    return ApiResponse(data=author).model_dump()


@bp.route('/', methods=['POST'])
@token_auth.login_required
def post_authors():
    """Endpoint to add a new author."""
    data = request.get_json()
    try:
        author = validate_dto(data, "author")
    except APIValidationError as exception:
        return ApiResponse(success=False, message="Validation Error", details=exception.errors,
                           status_code=400).model_dump(), 400

    new_author = Authors(**author.model_dump(exclude={"books"}))

    if author.books:
        try:
            new_books = new_books_list(author.books)
            new_author.books = new_books
        except BookNotFound as exception:
            return ApiResponse(success=False, message="Book not found",
                               details=f"Book with ID {exception.book_id} does not exist",
                               status_code=404).model_dump(), 404

    db.session.add(new_author)
    db.session.commit()

    new_author = AuthorData.from_orm(new_author)

    return ApiResponse(data=new_author).model_dump()


@bp.route('/<int:author_id>', methods=['PUT'])
@token_auth.login_required
def put_authors(author_id):
    """
    Endpoint for updating an author.
    :param author_id: ID of the author to update.
    """
    data = request.get_json()

    try:
        author = validate_dto(data, "author")
    except APIValidationError as exception:
        return ApiResponse(success=False, message="Validation Error", details=exception.errors,
                           status_code=400).model_dump(), 400

    target_author: Authors = Authors.query.get(author_id)
    if not target_author:
        return ApiResponse(success=False, message="Author not found", status_code=404).model_dump(), 404

    for key, value in author.model_dump(exclude={"books"}).items():
        setattr(target_author, key, value)

    if author.books:
        try:
            book_update = new_books_list(author.books)
            target_author.books = book_update
        except BookNotFound as exception:
            return ApiResponse(success=False, message="Author update failed",
                               details=f"Unable to assign book to author. "
                                       f"Book with ID {exception.book_id} does not exist",
                               status_code=404).model_dump(), 404

    db.session.commit()

    updated_author = AuthorData.from_orm(target_author)
    return ApiResponse(data=updated_author).model_dump()


@bp.route('/<int:author_id>', methods=['DELETE'])
@token_auth.login_required
def delete_authors(author_id):
    """
    Endpoint for deleting a author.
    :param author_id: ID of the author to delete.
    :return:
    """
    target_author: Authors = Authors.query.get(author_id)
    if not target_author:
        return ApiResponse(success=False, message="Author not found", status_code=404).model_dump(), 404

    deleted_author = AuthorBase.from_orm(target_author)

    try:
        db.session.delete(target_author)
        db.session.commit()
    except exc.SQLAlchemyError:
        msg = f"Failed to delete author '{author_id}'. Authors cannot be deleted when books are still assigned to them."
        return ApiResponse(success=False, message="Delete failed", details=msg, status_code=400).model_dump(), 400

    return ApiResponse(data=deleted_author.model_dump()).model_dump()
