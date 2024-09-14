"""Endpoints for HTTP basic and token authentication"""
from flask import current_app
from flask_httpauth import HTTPBasicAuth
from flask_httpauth import HTTPTokenAuth

from pika import db
from pika.models import Users

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


# pylint: disable=inconsistent-return-statements
@basic_auth.verify_password
def verify_password(username, password):
    """Authenticate user for getting token."""
    user = Users.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user


@token_auth.verify_token
def verify_token(token):
    """Verify a token."""
    return Users.check_token(token) if token else None


@current_app.route('/token', methods=['POST'])
@basic_auth.login_required
def get_token():
    """Generate and return API token."""
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return {'token': token}


@current_app.route('/token', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    """Revoke API token."""
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204
