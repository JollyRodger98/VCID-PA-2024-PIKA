"""PIKA Authentication"""
# pylint: disable=wrong-import-position,cyclic-import
from flask import Blueprint

from .mail import send_email
from .utils import role_required

bp = Blueprint('auth', __name__, template_folder='templates')

from . import routes

__all__ = ['send_email', 'role_required', 'bp']
