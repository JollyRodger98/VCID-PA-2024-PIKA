"""REST API for series data."""
from flask import Blueprint, request
from sqlalchemy import exc

from pika import db
from pika.models import Series
from .auth import token_auth
from .data import ApiResponse, SeriesPage, SeriesBase, SeriesData
from .util import validate_dto, new_books_list, APIValidationError, BookNotFound

bp = Blueprint("series", __name__)


@bp.route('/', methods=['GET'])
@token_auth.login_required
def get_series():
    """Endpoint to get a paginated series list."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Series.query.order_by(Series.title).paginate(page=page, per_page=per_page)
    series = [SeriesData.from_orm(s).model_dump() for s in query]
    page = SeriesPage(
        first=1,
        last=query.pages,
        has_previous=query.has_prev,
        has_next=query.has_next,
        series=series
    )

    return ApiResponse(data=page).model_dump()


@bp.route('/all', methods=['GET'])
@token_auth.login_required
def get_series_all():
    """
    Endpoint to get all series data. Please use sparingly.
    Generally use the endpoint /series to get a list of series data. Only use this endpoint if you specifically need
    to get *all* series data.
    """
    query = Series.query.all()
    series = [SeriesData.from_orm(s).model_dump() for s in query]
    return ApiResponse(data=series).model_dump()


@bp.route('/<int:series_id>', methods=['GET'])
@token_auth.login_required
def get_series_series_id(series_id):
    """
    Endpoint for getting series data.
    :param series_id: ID of series to return.
    """
    query = Series.query.get(series_id)
    if not query:
        return ApiResponse(success=False, message="Series not found.", status_code=404).model_dump(), 404
    series = SeriesData.from_orm(query)
    return ApiResponse(data=series).model_dump()


@bp.route('/', methods=['POST'])
@token_auth.login_required
def post_series():
    """Endpoint to add a new series."""
    data = request.get_json()
    try:
        series = validate_dto(data, "series")
    except APIValidationError as exception:
        return ApiResponse(success=False, message="Validation Error", details=exception.errors,
                           status_code=400).model_dump(), 400

    new_series = Series(**series.model_dump(exclude={"books"}))

    if series.books:
        try:
            new_books = new_books_list(series.books)
            new_series.books = new_books
        except BookNotFound as exception:
            return ApiResponse(success=False, message="Book not found",
                               details=f"Book with ID {exception.book_id} does not exist",
                               status_code=404).model_dump(), 404

    db.session.add(new_series)
    db.session.commit()

    new_series = SeriesData.from_orm(new_series)
    return ApiResponse(data=new_series).model_dump()


@bp.route('/<int:series_id>', methods=['PUT'])
@token_auth.login_required
def put_series(series_id):
    """
    Endpoint for updating a series.
    :param series_id: ID of series to update.
    """
    data = request.get_json()

    try:
        series = validate_dto(data, "series")
    except APIValidationError as exception:
        return ApiResponse(success=False, message="Validation Error", details=exception.errors,
                           status_code=400).model_dump(), 400

    target_series: Series = Series.query.get(series_id)
    if not target_series:
        return ApiResponse(success=False, message="Series not found", status_code=404).model_dump(), 404

    for key, value in series.model_dump(exclude={"books"}).items():
        setattr(target_series, key, value)

    # book_update = []
    if series.books:
        try:
            book_update = new_books_list(series.books)
            target_series.books = book_update
        except BookNotFound as exception:
            return ApiResponse(success=False, message="Series update failed",
                               details=f"Unable to assign book to series. "
                                       f"Book with ID {exception.book_id} does not exist",
                               status_code=404).model_dump(), 404

    db.session.commit()

    updated_series = SeriesData.from_orm(target_series)
    return ApiResponse(data=updated_series).model_dump()


@bp.route('/<int:series_id>', methods=['DELETE'])
@token_auth.login_required
def delete_series(series_id):
    """
    Endpoint for deleting a series.
    :param series_id: ID of series to delete.
    """
    target_series: Series = Series.query.get(series_id)
    if not target_series:
        return ApiResponse(success=False, message="Series not found", status_code=404).model_dump(), 404

    deleted_series = SeriesBase.from_orm(target_series)

    try:
        db.session.delete(target_series)
        db.session.commit()
    except exc.SQLAlchemyError:
        msg = f"Failed to delete series '{series_id}'. Series cannot be deleted when books are still assigned to it."
        return ApiResponse(success=False, message="Delete failed",
                           details=msg,
                           status_code=400).model_dump(), 400

    return ApiResponse(data=deleted_series.model_dump()).model_dump()
