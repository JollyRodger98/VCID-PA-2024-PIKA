"""Application configuration"""
import tomllib
from os import path, environ

from dotenv import load_dotenv

base_dir = path.abspath(path.dirname(__name__))
load_dotenv(path.join(base_dir, ".env"))
with open(path.join(base_dir, "config.toml"), "rb") as file:
    toml_config = tomllib.load(file)


class DefaultConfig:  # pylint: disable=too-few-public-methods
    """Default configuration"""
    FLASK_ENV = environ.get("FLASK_ENV", "development")
    DEBUG = False
    LOG_LEVEL = "INFO"
    REQUEST_TIMEOUT = 60
    PER_PAGE_ITEMS = 20
    LANGUAGES = ["de_CH", 'en_CH', 'en']


class DevelopmentConfig(DefaultConfig):  # pylint: disable=too-few-public-methods
    """Development configuration"""
    env_config = toml_config["development"]
    LOG_LEVEL = env_config["log_level"].upper()

    # Flask
    DEBUG = env_config["flask"]["debug"]
    SECRET_KEY = env_config["flask"]["secret_key"]

    # SQLAlchemy
    BASE_URI = env_config["sqlalchemy"]["uri"]
    PIKA_COMMUNITY_DEFAULT_DATA = env_config["sqlalchemy"]["create_default_records"]
    SQLALCHEMY_DATABASE_URI = f"{env_config["sqlalchemy"]["uri"]}/{env_config["sqlalchemy"]["database"]}"

    # Elastic
    ELASTICSEARCH_URL = env_config["elastic"]["url"]
    ELASTICSEARCH_PASSWORD = env_config["elastic"]["password"]
    ELASTICSEARCH_CERT_PATH = env_config["elastic"]["ca_path"]

    # Mail
    MAIL_SERVER = env_config['mail']['server']
    MAIL_PORT = env_config['mail']['port']
    MAIL_USE_TLS = env_config['mail']['use_tls']
    MAIL_USERNAME = env_config['mail']['username']
    MAIL_PASSWORD = env_config['mail']['password']


class ProductionConfig(DefaultConfig):  # pylint: disable=too-few-public-methods
    """Production configuration"""
    env_config = toml_config["production"]
    LOG_LEVEL = env_config["log_level"].upper()

    # Flask
    DEBUG = env_config["flask"]["debug"]
    SECRET_KEY = env_config["flask"]["secret_key"]

    # SQLAlchemy
    BASE_URI = env_config["sqlalchemy"]["uri"]
    PIKA_COMMUNITY_DEFAULT_DATA = env_config["sqlalchemy"]["create_default_records"]
    SQLALCHEMY_DATABASE_URI = f"{env_config["sqlalchemy"]["uri"]}/{env_config["sqlalchemy"]["database"]}"

    # Elastic
    ELASTICSEARCH_URL = env_config["elastic"]["url"]
    ELASTICSEARCH_PASSWORD = env_config["elastic"]["password"]
    ELASTICSEARCH_CERT_PATH = env_config["elastic"]["ca_path"]

    # Mail
    MAIL_SERVER = env_config['mail']['server']
    MAIL_PORT = env_config['mail']['port']
    MAIL_USE_TLS = env_config['mail']['use_tls']
    MAIL_USERNAME = env_config['mail']['username']
    MAIL_PASSWORD = env_config['mail']['password']


# pylint: disable=invalid-name
class Config(DefaultConfig):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Configuration"""

    def __init__(self, config_name):
        env_config = toml_config[config_name]
        self.LOG_LEVEL = env_config["log_level"].upper()

        # Flask
        self.DEBUG = env_config["flask"]["debug"]
        self.SECRET_KEY = env_config["flask"]["secret_key"]

        # SQLAlchemy
        self.BASE_URI = env_config["sqlalchemy"]["uri"]
        self.PIKA_COMMUNITY_DEFAULT_DATA = env_config["sqlalchemy"]["create_default_records"]
        self.SQLALCHEMY_DATABASE_URI = f"{env_config["sqlalchemy"]["uri"]}/{env_config["sqlalchemy"]["database"]}"

        # Elastic
        self.ELASTICSEARCH_URL = env_config["elastic"]["url"]
        self.ELASTICSEARCH_PASSWORD = env_config["elastic"]["password"]
        self.ELASTICSEARCH_CERT_PATH = env_config["elastic"]["ca_path"]

        # Mail
        self.MAIL_SERVER = env_config['mail']['server']
        self.MAIL_PORT = env_config['mail']['port']
        self.MAIL_USE_TLS = env_config['mail']['use_tls']
        self.MAIL_USERNAME = env_config['mail']['username']
        self.MAIL_PASSWORD = env_config['mail']['password']
