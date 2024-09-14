"""Database models"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Protocol

import sqlalchemy as sa
from flask_login import UserMixin
from sqlalchemy import orm as so
from werkzeug.security import check_password_hash

from pika import db
from .search import query_index, add_to_index, remove_from_index


class Role(db.Model):  # pylint: disable=too-few-public-methods
    """ORM model for user role."""
    __tablename__ = 'roles'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(20))


class UserRole(db.Model):  # pylint: disable=too-few-public-methods
    """ORM model for many-to-many relationship users and roles"""
    __tablename__ = 'user_roles'
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('roles.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class Users(db.Model, UserMixin):
    """ORM model for users"""
    __tablename__ = 'users'
    user_id: so.Mapped[int] = so.mapped_column(primary_key=True, autoincrement=True)

    username: so.Mapped[str] = so.mapped_column(sa.String(20), unique=True)
    password: so.Mapped[str] = so.mapped_column(sa.String(255))
    email: so.Mapped[str] = so.mapped_column(sa.String(255), unique=True)

    first_name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))
    last_name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    last_login: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))
    created_at: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))

    active: so.Mapped[bool] = so.mapped_column(default=True)

    token: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    roles: so.Mapped[List[Role]] = so.relationship(secondary='user_roles', backref='users')

    posts: so.Mapped[List[Posts]] = so.relationship(backref='author')
    threads: so.Mapped[List[Threads]] = so.relationship(backref='author')

    @property
    def is_active(self) -> bool:
        """Property used by `UserMixin` to get user status."""
        return self.active

    def get_id(self) -> int:
        """Function used by `UserMixin` to get user id."""
        return self.user_id

    def get_token(self, expires_in: int = 3600) -> str:
        """
        Generate or refresh user API token.
        :param expires_in: Lifetime of the API token in seconds.
        :type expires_in: int
        :return: User API token.
        :rtype: str
        """
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        """Revoke user API token."""
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    def check_password(self, password: str) -> bool:
        """
        Check if password matches user password hash.
        :param password: Password to check
        :type password: str
        :return: True or False
        :rtype: bool
        """
        return check_password_hash(self.password, password)

    def get_roles(self) -> List[str]:
        """
        Return a list with all user role names.
        :return: List of role names as strings.
        :rtype: list[str]
        """
        return [role.name for role in self.roles]

    def get_last_login(self) -> datetime:
        """Return the last login date and time of the user with local timezone."""
        return self.last_login.replace(tzinfo=timezone.utc).astimezone()

    def get_created_at(self) -> datetime:
        """Return the creation date and time of the user with local timezone."""
        return self.created_at.replace(tzinfo=timezone.utc).astimezone()

    @staticmethod
    def check_token(token: str) -> Users | None:
        """
        Check if token is valid.
        :param token: API authentication token
        :type token: str
        :return: user object if token is valid, else None
        :rtype: User | None
        """
        user = db.session.scalar(sa.select(Users).where(Users.token == token))
        if user.token is None or user.token_expiration is None:
            return None
        if user is None or user.token_expiration.replace(
                tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user


class Posts(db.Model):  # pylint: disable=too-few-public-methods
    """ORM model for community thread posts."""
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.thread_id'), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete="SET NULL"), nullable=True)

    def get_created_at(self) -> datetime:
        """Return the creation date and time of the post with local timezone."""
        return self.created.replace(tzinfo=timezone.utc).astimezone()


class Threads(db.Model):
    """ORM models for community threads."""
    __tablename__ = 'threads'
    thread_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(255))
    created: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))
    last_updated: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))
    views: so.Mapped[int] = so.mapped_column(default=0)
    posts: so.Mapped[List[Posts]] = so.relationship(backref='thread')
    author_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('users.user_id', ondelete='SET NULL'))

    def get_created_at(self) -> datetime:
        """Return the creation date and time of the thread with local timezone."""
        return self.created.replace(tzinfo=timezone.utc).astimezone()

    def get_last_update(self) -> datetime:
        """Return the date and timeof the last update of this thread with local timezone."""
        return self.last_updated.replace(tzinfo=timezone.utc).astimezone()


class Searchable(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol interface for SearchableMixin"""
    __tablename__: str
    id: so.Mapped[int]


class SearchableMixin:
    """Mixin for SQLAlchemy ORM objects."""

    @classmethod
    def search(cls: Searchable, expression: str, page: int, per_page: int) -> tuple[List | sa.ScalarResult, int]:
        """
        Search the elasticsearch index.
        :param expression: Search expression.
        :type expression: str
        :param page: Page number of results to return.
        :type page: int
        :param per_page: Number of results per page.
        :type per_page: int
        :return: List of search results.
        :rtype: tuple[List | sa.ScalarResult, int]
        """
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for index, _id in enumerate(ids):
            when.append((_id, index))
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    # pylint: disable=protected-access
    @classmethod
    def before_commit(cls: Searchable, session):
        """Make session data available for after commiting changes."""
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls: Searchable, session):
        """Add data to elasticsearch index after commit."""
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                obj: Searchable
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                obj: Searchable
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                obj: Searchable
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls: Searchable):
        """Add all model objects to elasticsearch index"""
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)


class Authors(db.Model, SearchableMixin):
    """ORM model for authors of books"""
    __tablename__ = 'library_authors'
    __searchable__ = ['first_name', 'last_name']
    author_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    id = so.synonym("author_id")
    first_name: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))
    last_name: so.Mapped[str] = so.mapped_column(sa.String(255))

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return f"{self.last_name}"

    def __repr__(self):
        full_name = self.last_name
        if self.first_name:
            full_name = f"{self.first_name} {self.last_name}"
        return f'<Author {repr(full_name)}>'


class BooksAuthors(db.Model):  # pylint: disable=too-few-public-methods
    """ORM model for relationship between books and authors"""
    __tablename__ = 'library_books_authors'
    book_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('library_books.book_id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True
    )
    author_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('library_authors.author_id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True
    )

    def all_authors(self) -> list[dict[str, str | int]]:
        """
        Return simple dictionary of all authors.
        :return: List of authors.
        :rtype: list[dict[str, str | int]]
        """
        all_authors = []
        for author in self.query.all():
            all_authors.append(
                {'author_id': author.author_id, 'first_name': author.first_name, 'last_name': author.last_name})
        return all_authors


class Books(db.Model, SearchableMixin):
    """ORM model for book data."""
    __tablename__ = 'library_books'
    __searchable__ = ['title']
    book_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    id = so.synonym("book_id")
    title: so.Mapped[str] = so.mapped_column(sa.String(255))
    release_date: so.Mapped[date]
    read_status: so.Mapped[bool]
    authors: so.Mapped[List[Authors]] = so.relationship(secondary='library_books_authors', backref='books',
                                                        passive_deletes=True)
    series_id: so.Mapped[Optional[int]] = so.mapped_column(
        sa.ForeignKey('library_series.series_id', ondelete="RESTRICT", onupdate='CASCADE'))
    volume_nr: so.Mapped[Optional[float]]
    synopsis: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    cover: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Book {repr(self.title)}>'


class Series(db.Model, SearchableMixin):
    """ORM Model for book series"""
    __tablename__ = 'library_series'
    __searchable__ = ['title']
    series_id: so.Mapped[int] = so.mapped_column(primary_key=True)
    id = so.synonym("series_id")
    title: so.Mapped[str] = so.mapped_column(sa.String(255))
    books: so.Mapped[List[Books]] = so.relationship(backref='series', passive_deletes=True)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Series {repr(self.title)}>'


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
