"""Data models for community and user data. Includes some data permutations."""
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, computed_field, EmailStr


class UserBase(BaseModel):
    """Base model for user data."""
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    last_login: datetime
    created_at: datetime
    active: bool

    def get_created_at(self) -> datetime:
        """Return datetime of user creation with local timezone."""
        return self.created_at.replace(tzinfo=timezone.utc).astimezone()

    def get_last_login(self) -> datetime:
        """Return datetime of user last login with local timezone."""
        return self.last_login.replace(tzinfo=timezone.utc).astimezone()


class User(UserBase):
    """Standard object to store user information."""
    posts: List["PostBase"]
    threads: List["ThreadBase"]

    @computed_field
    def posts_count(self) -> int:
        """Computed pydantic field for a count of posts by this user."""
        return len(self.posts)


class ThreadBase(BaseModel):
    """Base model for threads."""
    model_config = ConfigDict(from_attributes=True)
    thread_id: int
    title: str
    created: datetime
    last_updated: datetime
    views: int

    def get_created_at(self):
        """Return datetime of thread creation with local timezone."""
        return self.created.replace(tzinfo=timezone.utc).astimezone()

    def get_last_updated(self):
        """Return datetime of last update of thread with local timezone."""
        return self.last_updated.replace(tzinfo=timezone.utc).astimezone()


class Thread(ThreadBase):
    """Standard object to store thread information."""
    posts: List["ThreadPost"]
    author: Optional["UserBase"]

    @computed_field
    def post_count(self) -> int:
        """Computed pydantic field for a count of posts in this thread."""
        return len(self.posts)


class PostBase(BaseModel):
    """Base data model for posts."""
    model_config = ConfigDict(from_attributes=True)
    post_id: int
    content: str
    created: datetime

    def get_created_at(self) -> datetime:
        """Return datetime of post creation with local timezone."""
        return self.created.replace(tzinfo=timezone.utc).astimezone()


class ThreadPost(PostBase):
    """Thread data used when nested in a post data model."""
    author: Optional["UserBase"]


class Post(PostBase):
    """Standard object to store post data."""
    thread: "ThreadBase"
