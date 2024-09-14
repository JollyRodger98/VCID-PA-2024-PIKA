"""Application setup scripts"""
# pylint: disable=import-outside-toplevel,unused-import
import sys

import tzlocal
from elasticsearch import Elasticsearch
from flask import Flask, session, request
from flask_babel import lazy_gettext as _l, Babel
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


def generate_base_uri(app: Flask) -> str:
    """
    Generate a database URI string without a default database
    :param app: Flask app
    :return: Database URI string
    """
    return (f"mysql+pymysql://{app.config["PIKA_MYSQL_DB_USER"]}:{app.config["PIKA_MYSQL_DB_PASSWORD"]}@"
            f"{app.config["PIKA_MYSQL_DB_HOST"]}:{app.config["PIKA_MYSQL_DB_PORT"]}")


def check_db_connection(app: Flask):
    """
    Checks if database connection is successful.
    :param app: Flask app
    """
    engine = create_engine(app.config.get("BASE_URI"))
    try:
        engine.connect()
        app.logger.info("Database: Connected successfully")
    except OperationalError as e:
        if e.orig.args[0] == 2003:
            app.logger.error("Database: Database connection unsuccessful")
            app.logger.debug(e)
            sys.exit(1)
        app.logger.critical("Database: Unknown connection error")


def setup_db(app: Flask, db: SQLAlchemy):
    """Setup script for application database"""
    app.logger.info("Setting up database...")
    check_db_connection(app)

    with app.app_context():
        db.init_app(app)
        Migrate(app, db)


def setup_flask_login(app: Flask, login_manager: LoginManager):
    """Setup for Flask login"""
    app.logger.info("Setting up Flask login...")
    with app.app_context():
        from pika.models import Users
        login_manager.login_view = 'auth.login_page'
        login_manager.login_message = _l('Please log in to access this page.')
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id: int):
            return Users.query.get(int(user_id))


def setup_elasticsearch(app: Flask):
    """Setup for Elasticsearch"""
    app.logger.info("Setting up Elasticsearch...")
    with app.app_context():
        if app.config['ELASTICSEARCH_URL']:
            app.elasticsearch = Elasticsearch(
                [app.config['ELASTICSEARCH_URL']],
                basic_auth=("elastic", app.config['ELASTICSEARCH_PASSWORD']),
                ca_certs=app.config['ELASTICSEARCH_CERT_PATH'],
                # verify_certs=False
            )


def setup_babel(app: Flask, babel: Babel):
    def locale_selector():
        if session.get('lang'):
            if request.args.get('lang'):
                session['lang'] = request.args.get('lang')
                app.logger.info('Set language: %s', session['lang'])
            app.logger.debug('Language: %s', session['lang'])
            return session['lang']

        return request.accept_languages.best_match(app.config['LANGUAGES'])

    def timezone_selector():
        return tzlocal.get_localzone()

    babel.init_app(app, locale_selector=locale_selector, timezone_selector=timezone_selector)

    # babel.init_app(app, locale_selector=locale_selector)

