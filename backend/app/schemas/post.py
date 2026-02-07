from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal

from app.models.post import PostStatus, PostType
from app.models.social_account import Platform


class PostCreate(BaseModel):
    """Schema for creating a new post."""
    content: str = Field(..., min_length=1, max_length=5000)
    post_type: PostType = PostType.TEXT
    media_urls: list[str] | None = None
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None
    platforms: list[Platform] = Field(..., min_length=1)

    # AI generation tracking
    ai_generated: bool = False
    ai_prompt: str | None = None


class PostUpdate(BaseModel):
    """Schema for updating a post."""
    content: str | None = Field(None, min_length=1, max_length=5000)
    hashtags: list[str] | None = None
    scheduled_at: datetime | None = None
    status: PostStatus | None = None


class PlatformPostResponse(BaseModel):
    """Platform-specific post data."""
    id: str
    platform: Platform
    username: str
    status: PostStatus
    content: str | None
    platform_post_url: str | None
    likes_count: int
    comments_count: int
    shares_count: int
    published_at: datetime | None
    error_message: str | None

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Schema for post response."""
    id: str
    content: str
    post_type: PostType
    media_urls: list[str] | None
    thumbnail_url: str | None
    hashtags: list[str] | None
    status: PostStatus
    scheduled_at: datetime | None
    published_at: datetime | None
    ai_generated: bool
    created_at: datetime
    updated_at: datetime
    platforms: list[PlatformPostResponse]

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Paginated list of posts (offset-based)."""
    posts: list[PostResponse]
    total: int
    page: int
    per_page: int
    has_next: bool


class PostCursorResponse(BaseModel):
    """Cursor-paginated list of posts.

    Uses cursor pagination for O(1) performance.
    Pass next_cursor as cursor param to get next page.
    """
    posts: list[PostResponse]
    next_cursor: str | None
    has_more: bool


class CaptionGenerateRequest(BaseModel):
    """Request for AI caption generation."""
    topic: str = Field(..., min_length=3, max_length=500)
    url: str | None = None
    tone: Literal["professional", "witty", "casual"] | None = None
    platform: Platform | None = None
    include_hashtags: bool = True
    max_length: int | None = None


class CaptionVariation(BaseModel):
    """Single caption variation."""
    tone: str
    caption: str
    hashtags: list[str]
    character_count: int


class CaptionGenerateResponse(BaseModel):
    """Response with generated captions."""
    topic: str
    variations: list[CaptionVariation]
    generated_at: datetime
