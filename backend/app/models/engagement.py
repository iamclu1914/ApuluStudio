from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.social_account import Platform


class Comment(Base):
    """Comments from social platforms for the unified inbox."""

    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    social_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), index=True
    )
    post_platform_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("post_platforms.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    # Platform reference
    platform_comment_id: Mapped[str] = mapped_column(String(255), unique=True)
    platform_post_id: Mapped[str] = mapped_column(String(255), index=True)

    # Comment data
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[str] = mapped_column(String(255))
    author_username: Mapped[str] = mapped_column(String(255))
    author_avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Engagement
    likes_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_replied: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)

    # Reply tracking
    reply_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    posted_at: Mapped[datetime] = mapped_column(DateTime)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Comment {self.id[:8]} by @{self.author_username}>"


class Mention(Base):
    """Mentions/tags from social platforms."""

    __tablename__ = "mentions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    social_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), index=True
    )

    # Platform reference
    platform_mention_id: Mapped[str] = mapped_column(String(255), unique=True)
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Mention data
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    mention_type: Mapped[str] = mapped_column(String(50))  # post, comment, story, etc.
    author_id: Mapped[str] = mapped_column(String(255))
    author_username: Mapped[str] = mapped_column(String(255))
    author_avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Link to original
    post_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    mentioned_at: Mapped[datetime] = mapped_column(DateTime)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Mention {self.id[:8]} by @{self.author_username}>"
