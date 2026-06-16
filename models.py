from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, String, Integer, Text

from datetime import datetime, UTC

from database import Base



class User(Base):
    __tablename__ = "users"

    # Mapped[int] is typehint for our IDE
    # index=True makes ids auto increment
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[int] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)

    # we are only storing image name and not whole path because that decouples our database from file structure
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None
    )
    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"   # We should seperate our default content from user uploaded

    # forward reference - referecing 'Post' without defining it. in python 3.14 this is fine
    # in older versions we need to import annotations from __future__ at top
    posts: Mapped[list[Post]] = relationship(
        back_populates="author",    # allows us to do "user.posts" to get their posts
        cascade="all, delete-orphan",   # IMP - deletes all the posts when user is deleted. if a post is somehow removed from the relationship it will be cleaned up.
    )  


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),     # This links posts to users
        nullable=False,
        index=True,     # Index is like index in a textbook. Without it the database looks up every row for matches
    )
    # Primary keys get indexed automatically but foreign key dont. Tradeoff is slightly slower Writes
    
    date_posted: Mapped[datetime] = mapped_column(      
        DateTime(timezone=True),    # Sqlite defalt stores datetime as text but in postgres we will use timestamp TZ
        default = lambda: datetime.now(UTC),
    )
    author: Mapped[User] = relationship(back_populates="posts")     # allows us to do "post.author" to get that user back




