"""PIKA app flask setup"""
# pylint: disable=cyclic-import
import pprint
from os import environ

from flask import Flask
from flask_babel import Babel
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

from .config import DevelopmentConfig, ProductionConfig, Config
from .setup import setup_db, setup_flask_login, setup_elasticsearch, setup_babel

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
babel = Babel()


def create_app(log_level=None):
    """Create a Flask app"""
    app = Flask(__name__, template_folder='templates')
    if environ.get("FLASK_ENV") is None:
        raise KeyError("FLASK_ENV not found")

    if environ.get("FLASK_ENV") == "development":
        app.config.from_object(DevelopmentConfig)
    elif environ.get("FLASK_ENV") == "production":
        app.config.from_object(ProductionConfig)
    else:
        try:
            app.config.from_object(Config(environ.get("FLASK_ENV")))
        except Exception as e:
            raise ValueError("FLASK_ENV is invalid") from e

    if log_level:
        app.logger.setLevel(log_level)
    elif app.config["LOG_LEVEL"]:
        app.logger.setLevel(app.config["LOG_LEVEL"])
    else:
        app.logger.setLevel("INFO")
    app.logger.log(app.logger.level, 'Environment: %s', environ.get('FLASK_ENV'))
    app.logger.debug('Flask Config: %s', pprint.pformat(dict(app.config)))

    setup_db(app, db)

    setup_flask_login(app, login_manager)

    setup_elasticsearch(app)

    mail.init_app(app)

    setup_babel(app, babel)

    with app.app_context():

        # noinspection PyUnresolvedReferences
        from pika import routes  # pylint: disable=unused-import,import-outside-toplevel

        from pika.auth.routes import bp as auth_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from pika.admin import bp as admin_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(admin_bp)

        from pika.api import bp as api_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(api_bp, url_prefix='/api/v1')

        from pika.library import bp as books_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(books_bp, url_prefix='/library')

        from pika.community.routes import bp as community_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(community_bp, url_prefix='/community')

    return app
