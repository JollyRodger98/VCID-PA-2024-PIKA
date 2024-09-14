import logging
import sys

import elasticsearch
from werkzeug.security import generate_password_hash

from pika import create_app
from pika import db
from pika.config import DefaultConfig, DevelopmentConfig, ProductionConfig
from pika.models import Users, Posts, Threads, Books, Series, Authors

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)8s in %(filename)15s:%(lineno)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("elastic_transport").setLevel(logging.WARNING)

DEFAULT_THREAD_DATA = [
    {
        "title": "Book Discussion",
        "post_content": "This is a place to discuss books."
    },
    {
        "title": "Series Discussion",
        "post_content": "This is a place to discuss book series."
    },
    {
        "title": "Author Discussion",
        "post_content": "This is a place to discuss authors."
    },
    {
        "title": "Bug Reports",
        "post_content": "Any discovered bugs can be reported here."
    },
    {
        "title": "Improvement Requests",
        "post_content": "Any improvement requests or suggestions can be posted here. "
                        "They may be implemented in the future."
    },
]


def create_default_user(app):
    with app.app_context():
        user = Users()
        user.username = "Admin"
        user.password = generate_password_hash("qQc8yU6p7yToCCECjDaL", "pbkdf2:sha256")
        user.email = "pika@jollyrodger.ch"
        db.session.add(user)
        db.session.commit()
        logger.info("Created default user")
        return user


def create_default_thread(app, user: Users, thread_title, default_post):
    with app.app_context():
        thread = Threads(title=thread_title, author=user)
        post = Posts(content=default_post, thread=thread, author=user)
        db.session.add_all([thread, post])
        db.session.commit()
        logger.info(f"Created thread '{thread_title}'")


def generate_base_uri(config):
    return (f"mysql+pymysql://{config.PIKA_MYSQL_DB_USER}:{config.PIKA_MYSQL_DB_PASSWORD}"
            f"@{config.PIKA_MYSQL_DB_HOST}:{config.PIKA_MYSQL_DB_PORT}")


def setup(log_level="DEBUG"):
    if DefaultConfig.FLASK_ENV == "development":
        config = DevelopmentConfig()
    elif DefaultConfig.FLASK_ENV == "production":
        config = ProductionConfig()
    else:
        logger.error("Invalid FLASK_ENV")
        sys.exit(1)

    logger.info(f"{' Setup Script Start ':=^80}")
    uri = config.BASE_URI
    engine = db.create_engine(uri)

    # Check DB connection
    try:
        with engine.connect() as connection:
            results = connection.execute(db.text("SELECT 1"))
            if results.scalars().all() == [1]:
                logger.info(f"Database connection successful")
            else:
                raise Exception(f"Connection Error")
    except db.exc.OperationalError as exception:
        if exception.orig.args[0] == 2003:
            logger.critical(exception.args[0])
            sys.exit(1)
    except Exception as exception:
        logger.critical(exception)
        sys.exit(1)

    app = create_app()

    # Creating schemas if missing
    schemas = []
    with app.app_context():
        for _engine in db.engines.values():
            schemas.append(_engine.url.database)

    for schema in schemas:
        if not engine.dialect.has_schema(engine.connect(), schema):
            with db.orm.create_session(engine) as session:
                session.execute(db.schema.CreateSchema(schema))
                logger.debug(f"Create MySQL schema: {schema}")
        else:
            logger.debug(f"Existing MySQL schema found: {schema}")

    # Initialise ORM models
    with app.app_context():
        try:
            db.create_all()
            logger.debug("ORM models initialised")
        except Exception as exception:
            logger.critical(exception)
            logger.critical("Failed to create tables.")
            sys.exit(1)

        # Create default database entries
        if not Threads.query.all() and not Posts.query.all() and not Users.query.all():
            app.logger.info(f"No existing record found.")

            user = create_default_user(app)

            for data in DEFAULT_THREAD_DATA:
                create_default_thread(app, user, data["title"], data["post_content"])

            db.session.commit()

            app.logger.warning(f"Default community entries created.")

    # Generating Elasticsearch indices
    with app.app_context():
        for indexable in [Books, Series, Authors]:
            try:
                app.elasticsearch.indices.delete(index=indexable.__tablename__)
            except elasticsearch.NotFoundError:
                pass
            indexable.reindex()
            logger.info(f"Elastic: Indexing {indexable.__tablename__}")

    logger.info(f"{' Setup Script End ':=^80}")



if __name__ == '__main__':
    setup()
