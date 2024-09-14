"""Authentication utilities and custom functionalities."""
import functools

from flask import abort
from flask_login import current_user


def role_required(roles):
    """Decorator function for checking if a user ha a role."""
    def decorator_role_required(func):
        @functools.wraps(func)
        def wrapper_role_required(*args, **kwargs):
            for user_role in current_user.get_roles():
                if user_role in roles:
                    return func(*args, **kwargs)
            return abort(401, 'You are not authorized to access this resource.<br>'
                              'If this is mistake, please contact your administrator.')

        return wrapper_role_required

    return decorator_role_required
