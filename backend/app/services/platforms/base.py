from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.social_account import Platform


@dataclass
class PostResult:
    """Result of a post operation."""
    success: bool
    platform: Platform
    platform_post_id: str | None = None
    platform_post_url: str | None = None
    error_message: str | None = None
    raw_response: dict | None = None


@dataclass
class CommentResult:
    """Result of a comment/reply operation."""
    success: bool
    platform: Platform
    comment_id: str | None = None
    error_message: str | None = None


@dataclass
class EngagementData:
    """Engagement metrics from a platform."""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    impressions: int = 0
    reach: int = 0


class BasePlatformService(ABC):
    """Base class for platform-specific services."""

    platform: Platform

    @abstractmethod
    async def post_text(
        self,
        content: str,
        access_token: str,
        **kwargs: Any,
    ) -> PostResult:
        """Post text content to the platform."""
        pass

    @abstractmethod
    async def post_image(
        self,
        content: str,
        image_url: str,
        access_token: str,
        **kwargs: Any,
    ) -> PostResult:
        """Post an image with caption to the platform."""
        pass

    @abstractmethod
    async def post_video(
        self,
        content: str,
        video_url: str,
        access_token: str,
        **kwargs: Any,
    ) -> PostResult:
        """Post a video with caption to the platform."""
        pass

    @abstractmethod
    async def delete_post(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a post from the platform."""
        pass

    @abstractmethod
    async def get_engagement(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> EngagementData:
        """Get engagement metrics for a post."""
        pass

    @abstractmethod
    async def reply_to_comment(
        self,
        comment_id: str,
        content: str,
        access_token: str,
        **kwargs: Any,
    ) -> CommentResult:
        """Reply to a comment on the platform."""
        pass

    @abstractmethod
    async def get_comments(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> list[dict]:
        """Get comments for a post."""
        pass

    @abstractmethod
    async def get_profile(
        self,
        access_token: str,
        **kwargs: Any,
    ) -> dict:
        """Get the authenticated user's profile."""
        pass

    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str,
        **kwargs: Any,
    ) -> dict:
        """Refresh the access token."""
        pass
