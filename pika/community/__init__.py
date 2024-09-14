"""PIKA community"""
# pylint: disable=wrong-import-position,cyclic-import
from flask import Blueprint

bp = Blueprint('community', __name__, template_folder='templates', static_folder='static')

from . import routes

__all__ = ['bp']
