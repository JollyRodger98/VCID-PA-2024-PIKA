"""Settings for user account"""
# pylint: disable=wrong-import-position
from flask import Blueprint

bp = Blueprint('user', __name__)

from .profile.routes import bp as profile_bp

bp.register_blueprint(profile_bp, url_prefix='/profile')

from .edit.routes import bp as edit_bp

bp.register_blueprint(edit_bp, url_prefix='/edit')

__all__ = ['bp']
