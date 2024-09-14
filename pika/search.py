"""Functions to manage the elasticsearch indices"""
from flask import current_app

from pika import db


def add_to_index(index: str, model: db.Model):
    """
    Add data to index from searchable fields in ORM models.
    :param index: Elasticsearch index name
    :param model: SQLAlchemy model object
    :return:
    """
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)


def remove_from_index(index: str, model: db.Model):
    """
    Remove data to index from searchable fields in ORM models.
    :param index: Elasticsearch index name
    :param model: SQLAlchemy model object
    """
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index: str, query: str, page: int, per_page: int):
    """
    Query elasticsearch index with given query.
    :param index: Elasticsearch index name
    :param query: Search query
    :param page: Page number
    :param per_page: Items per page
    :return:
    """
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*'], "fuzziness": "AUTO", "prefix_length": 2}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
