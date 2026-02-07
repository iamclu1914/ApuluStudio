from datetime import datetime
from pydantic import BaseModel, Field

from app.models.social_account import Platform


class CommentResponse(BaseModel):
    """Schema for comment response."""
    id: str
    platform: Platform
    platform_comment_id: str
    content: str
    author_username: str
    author_avatar_url: str | None
    likes_count: int
    is_read: bool
    is_replied: bool
    posted_at: datetime
    post_url: str | None = None

    class Config:
        from_attributes = True


class CommentReply(BaseModel):
    """Schema for replying to a comment."""
    content: str = Field(..., min_length=1, max_length=2200)


class MentionResponse(BaseModel):
    """Schema for mention response."""
    id: str
    platform: Platform
    mention_type: str
    content: str | None
    author_username: str
    author_avatar_url: str | None
    post_url: str | None
    is_read: bool
    mentioned_at: datetime

    class Config:
        from_attributes = True


class InboxItem(BaseModel):
    """Unified inbox item (comment or mention)."""
    id: str
    type: str  # "comment" or "mention"
    platform: Platform
    content: str | None
    author_username: str
    author_avatar_url: str | None
    is_read: bool
    timestamp: datetime
    post_url: str | None = None
    # Comment-specific
    is_replied: bool | None = None
    likes_count: int | None = None


class InboxResponse(BaseModel):
    """Paginated unified inbox."""
    items: list[InboxItem]
    total: int
    unread_count: int
    page: int
    per_page: int
    has_next: bool
