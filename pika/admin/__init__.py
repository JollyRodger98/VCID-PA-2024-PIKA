"""Administration of users and permissions"""
# pylint: disable=wrong-import-position
from flask import Blueprint

bp = Blueprint('admin', __name__, template_folder='templates')

from .administrator import bp as admin_bp

bp.register_blueprint(admin_bp)

from .user import bp as user_bp

bp.register_blueprint(user_bp)

__all__ = ['bp']
