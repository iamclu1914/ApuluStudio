from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.social_account import SocialAccount


class PostStatus(str, Enum):
    """Status of a scheduled post."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class PostType(str, Enum):
    """Type of content being posted."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class Post(Base):
    """Master post that can be cross-posted to multiple platforms."""

    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text)  # Master caption/text
    post_type: Mapped[PostType] = mapped_column(SQLEnum(PostType), default=PostType.TEXT)

    # Media (stored in Supabase Storage)
    media_urls: Mapped[list | None] = mapped_column(JSON, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # AI-generated content
    ai_generated: Mapped[bool] = mapped_column(default=False)
    ai_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status (indexed for faster filtering)
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus), default=PostStatus.DRAFT, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="posts")
    platforms: Mapped[list["PostPlatform"]] = relationship(
        "PostPlatform", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Post {self.id[:8]} - {self.status.value}>"


class PostPlatform(Base):
    """Platform-specific version of a post with engagement metrics."""

    __tablename__ = "post_platforms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    post_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    social_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), index=True
    )

    # Platform-specific content (may differ from master)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashtags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Platform post reference
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform_post_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus), default=PostStatus.DRAFT
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Engagement metrics (cached)
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metrics_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="platforms")
    social_account: Mapped["SocialAccount"] = relationship(
        "SocialAccount", back_populates="post_platforms"
    )

    def __repr__(self) -> str:
        return f"<PostPlatform {self.id[:8]} - {self.status.value}>"
