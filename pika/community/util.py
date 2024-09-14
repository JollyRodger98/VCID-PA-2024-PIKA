"""Utility functions for community blueprint"""
from flask import session

from pika import db
from pika.models import Threads


def increment_thread_view(thread_id):
    """
    Increment a thread view counter. Checks in session if page has already been viewed or not.
    :param thread_id: ID of the thread to increment view counter
    """
    if not session["threads_visited"].get(str(thread_id)):
        thread = Threads.query.get(thread_id)
        thread.views += 1
        db.session.commit()
        session["threads_visited"].setdefault(str(thread_id), True)
        session.modified = True
