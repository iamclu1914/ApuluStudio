"""
LATE API integration for Instagram, Threads, TikTok, and X.

LATE (https://getlate.dev) is a service that provides simplified API access
to platforms that require complex verification processes. It handles:
- Instagram posting (Meta Business verification already done)
- Threads posting (Meta Business verification already done)
- TikTok posting (TikTok developer approval already done)
- X/Twitter posting (API access already configured)

Free tier: 10 posts/month shared across all platforms
Paid tier: $19/month for 120 posts
"""

import httpx
from datetime import datetime
from typing import Any

from app.services.platforms.base import (
    BasePlatformService,
    PostResult,
    CommentResult,
    EngagementData,
)
from app.models.social_account import Platform
from app.core.http_client import get_http_client, get_http_client_context
from app.core.exceptions import (
    PlatformError,
    PlatformAuthenticationError,
    PlatformRateLimitError,
    PlatformAPIError,
    ValidationError,
)
from app.core.logger import logger


class LateAPIError(PlatformAPIError):
    """Exception for LATE API errors."""

    def __init__(
        self,
        message: str,
        platform: str = "late",
        status_code: int = None,
        response: dict = None,
    ):
        super().__init__(
            platform=platform,
            message=message,
            status_code=status_code,
            raw_response=response,
        )


def _check_late_response(
    response: httpx.Response,
    platform: str,
) -> dict:
    """
    Check LATE API response for errors and raise appropriate exceptions.

    Returns:
        Parsed response data if successful

    Raises:
        PlatformAuthenticationError: For auth/API key errors
        PlatformRateLimitError: For rate limit errors
        LateAPIError: For other API errors
    """
    try:
        data = response.json() if response.text else {}
    except Exception:
        data = {}

    if response.status_code in [200, 201]:
        # LATE may return 200 but with failed status
        if data.get("status") == "failed" or data.get("error"):
            raise LateAPIError(
                message=data.get("error") or data.get("message", "LATE API error"),
                platform=platform,
                status_code=response.status_code,
                response=data,
            )
        return data

    error_message = data.get("error") or data.get("message", f"LATE API error: HTTP {response.status_code}")

    # Authentication errors
    if response.status_code == 401:
        raise PlatformAuthenticationError(
            platform=platform,
            message=f"LATE API authentication failed: {error_message}",
            raw_response=data,
        )

    # Rate limiting
    if response.status_code == 429:
        raise PlatformRateLimitError(
            platform=platform,
            message=f"LATE API rate limit exceeded: {error_message}",
            raw_response=data,
        )

    # Permission errors
    if response.status_code == 403:
        raise LateAPIError(
            message=f"LATE API permission denied: {error_message}",
            platform=platform,
            status_code=403,
            response=data,
        )

    # Generic API error
    raise LateAPIError(
        message=error_message,
        platform=platform,
        status_code=response.status_code,
        response=data,
    )


class LateService(BasePlatformService):
    """
    LATE API service for Instagram, Threads, TikTok, and X.

    LATE API Reference:
    - Base URL: https://getlate.dev/api/v1
    - Auth: Bearer token in Authorization header
    - Endpoints:
        - GET /accounts - List connected accounts
        - POST /posts - Create a post
        - GET /posts - List posts
        - DELETE /posts/:id - Delete a post
    """

    API_BASE = "https://getlate.dev/api/v1"

    def __init__(self, platform: Platform, api_key: str = None):
        """
        Initialize LATE service for a specific platform.

        Args:
            platform: The target platform (INSTAGRAM, THREADS, TIKTOK, or X)
            api_key: LATE API key (if not provided, will use settings)
        """
        supported = [Platform.INSTAGRAM, Platform.THREADS, Platform.TIKTOK, Platform.X]
        if platform not in supported:
            raise ValidationError(f"LATE service only supports Instagram, Threads, TikTok, and X. Got: {platform}")

        self.platform = platform
        self._api_key = api_key

    # Marker used in social_accounts table to indicate LATE-managed accounts
    LATE_MANAGED_MARKER = "LATE_MANAGED"

    def _get_client(self) -> httpx.AsyncClient | None:
        """Get the shared HTTP client."""
        try:
            return get_http_client()
        except RuntimeError:
            return None

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make an HTTP request using the shared client with fallback.

        Uses the global pooled client if available, otherwise creates a temporary one.
        """
        client = self._get_client()
        if client:
            return await client.request(method, url, **kwargs)
        else:
            async with get_http_client_context() as temp_client:
                return await temp_client.request(method, url, **kwargs)

    def _get_api_key(self, access_token: str = None) -> str:
        """Get the LATE API key."""
        # If access_token is the LATE_MANAGED marker, use settings
        if access_token == self.LATE_MANAGED_MARKER:
            access_token = None

        # Priority: passed token > instance key > settings
        if access_token:
            return access_token
        if self._api_key:
            return self._api_key

        # Fall back to settings
        from app.core.config import get_settings
        settings = get_settings()
        if not settings.late_api_key:
            raise PlatformAuthenticationError(
                platform="late",
                message="LATE API key not configured",
            )
        return settings.late_api_key

    def _get_headers(self, api_key: str) -> dict:
        """Get HTTP headers for LATE API requests."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _platform_to_late_type(self) -> str:
        """Convert Platform enum to LATE platform type."""
        mapping = {
            Platform.INSTAGRAM: "instagram",
            Platform.THREADS: "threads",
            Platform.TIKTOK: "tiktok",
            Platform.X: "twitter",  # LATE uses "twitter" not "x"
        }
        return mapping.get(self.platform, self.platform.value)

    def _get_tiktok_settings(self) -> dict:
        """Get required TikTok-specific settings for posting."""
        return {
            "privacy_level": "PUBLIC_TO_EVERYONE",  # or "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"
            "allow_comment": True,
            "allow_duet": True,
            "allow_stitch": True,
            "content_preview_confirmed": True,  # Required consent
            "express_consent_given": True,  # Required consent
        }

    async def get_accounts(self, api_key: str = None) -> list[dict]:
        """
        Get all connected accounts from LATE.

        Returns:
            List of account dictionaries with:
            - _id: LATE account ID (use this for posting)
            - platform: Platform type (instagram, threads, tiktok, twitter)
            - username: Platform username
            - displayName: Display name
            - isActive: Whether account is active
        """
        key = self._get_api_key(api_key)

        try:
            response = await self._request(
                "GET",
                f"{self.API_BASE}/accounts",
                headers=self._get_headers(key),
                timeout=30.0,
            )
            data = _check_late_response(response, "late")
            return data.get("accounts", [])

        except PlatformError:
            raise
        except httpx.TimeoutException:
            raise LateAPIError(
                message="LATE API request timed out",
                platform="late",
            )
        except httpx.RequestError as e:
            raise LateAPIError(
                message=f"Network error contacting LATE API: {str(e)}",
                platform="late",
            )

    # Alias for backward compatibility
    async def get_profiles(self, api_key: str = None) -> list[dict]:
        """Alias for get_accounts (backward compatibility)."""
        return await self.get_accounts(api_key)

    async def get_account_for_platform(self, api_key: str = None) -> dict | None:
        """
        Get the LATE account for this service's platform.

        Returns:
            Account dict or None if not found
        """
        accounts = await self.get_accounts(api_key)
        platform_type = self._platform_to_late_type()

        for account in accounts:
            if account.get("platform") == platform_type and account.get("isActive"):
                return account

        return None

    # Alias for backward compatibility
    async def get_profile_for_platform(self, api_key: str = None) -> dict | None:
        """Alias for get_account_for_platform (backward compatibility)."""
        return await self.get_account_for_platform(api_key)

    async def post_text(
        self,
        content: str,
        access_token: str = None,  # LATE API key
        late_profile_id: str = None,  # LATE profile ID
        user_id: str = None,  # Alias for late_profile_id (scheduler compatibility)
        scheduled_at: datetime = None,
        **kwargs: Any,
    ) -> PostResult:
        """
        Post text content via LATE API.

        Args:
            content: Text content to post
            access_token: LATE API key
            late_profile_id: LATE profile ID for the target account
            user_id: Alias for late_profile_id (for scheduler compatibility)
            scheduled_at: Optional datetime to schedule the post
        """
        try:
            api_key = self._get_api_key(access_token)
            platform_type = self._platform_to_late_type()

            # Get account ID - accept either parameter name
            late_account_id = late_profile_id or user_id
            if not late_account_id:
                account = await self.get_account_for_platform(api_key)
                if not account:
                    return PostResult(
                        success=False,
                        platform=self.platform,
                        error_message=f"No {self.platform.value} account connected in LATE",
                    )
                late_account_id = account.get("_id")

            # Build request payload using correct LATE API format
            payload = {
                "content": content,
                "platforms": [
                    {
                        "platform": platform_type,
                        "accountId": late_account_id,
                    }
                ],
                "publishNow": scheduled_at is None,
            }

            # Add scheduling if provided
            if scheduled_at:
                payload["scheduledFor"] = scheduled_at.isoformat()

            response = await self._request(
                "POST",
                f"{self.API_BASE}/posts",
                headers=self._get_headers(api_key),
                json=payload,
                timeout=60.0,
            )

            result = _check_late_response(response, self.platform.value)

            # Check platform results for failures
            post_data = result.get("post", {})
            platform_results = result.get("platformResults", [])

            # Check if any platform failed
            failed_platforms = [p for p in platform_results if p.get("status") == "failed"]
            if failed_platforms:
                error_msg = failed_platforms[0].get("error", "Publishing failed")
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=error_msg,
                    raw_response=result,
                )

            # Extract post info from response
            post_id = post_data.get("_id") or result.get("id") or result.get("postId")
            post_url = result.get("url") or result.get("postUrl")

            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=str(post_id) if post_id else None,
                platform_post_url=post_url,
                raw_response=result,
            )

        except PlatformError as e:
            logger.error(f"LATE API error posting text", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response if hasattr(e, "raw_response") else None,
            )
        except httpx.TimeoutException:
            logger.error(f"LATE API timeout posting text", platform=self.platform.value)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message="LATE API request timed out",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting via LATE", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Network error: {str(e)}",
            )

    async def post_image(
        self,
        content: str,
        image_url: str,
        access_token: str = None,
        late_profile_id: str = None,
        user_id: str = None,  # Alias for late_profile_id (scheduler compatibility)
        alt_text: str = "",
        scheduled_at: datetime = None,
        post_type: str = None,  # "feed", "story", "reel" for Instagram
        **kwargs: Any,
    ) -> PostResult:
        """
        Post an image with caption via LATE API.

        Args:
            content: Caption text
            image_url: URL of the image to post
            access_token: LATE API key
            late_profile_id: LATE profile ID for the target account
            user_id: Alias for late_profile_id (for scheduler compatibility)
            alt_text: Alternative text for the image
            scheduled_at: Optional datetime to schedule the post
            post_type: For Instagram - "feed", "story", or "reel"
        """
        try:
            api_key = self._get_api_key(access_token)
            platform_type = self._platform_to_late_type()

            # Get account ID - accept either parameter name
            late_account_id = late_profile_id or user_id
            if not late_account_id:
                account = await self.get_account_for_platform(api_key)
                if not account:
                    return PostResult(
                        success=False,
                        platform=self.platform,
                        error_message=f"No {self.platform.value} account connected in LATE",
                    )
                late_account_id = account.get("_id")

            # Build request payload using correct LATE API format
            media_item = {
                "type": "image",
                "url": image_url,
            }

            platform_config = {
                "platform": platform_type,
                "accountId": late_account_id,
            }

            # Add Instagram-specific post type (feed, story, reel)
            if self.platform == Platform.INSTAGRAM and post_type:
                platform_config["postType"] = post_type.lower()

            payload = {
                "content": content,
                "mediaItems": [media_item],
                "platforms": [platform_config],
                "publishNow": scheduled_at is None,
            }

            # Add scheduling if provided
            if scheduled_at:
                payload["scheduledFor"] = scheduled_at.isoformat()

            # Add TikTok-specific settings if posting to TikTok
            if self.platform == Platform.TIKTOK:
                payload["tiktokSettings"] = self._get_tiktok_settings()

            response = await self._request(
                "POST",
                f"{self.API_BASE}/posts",
                headers=self._get_headers(api_key),
                json=payload,
                timeout=120.0,  # Longer timeout for media uploads
            )

            result = _check_late_response(response, self.platform.value)

            # Check platform results for failures
            post_data = result.get("post", {})
            platform_results = result.get("platformResults", [])

            failed_platforms = [p for p in platform_results if p.get("status") == "failed"]
            if failed_platforms:
                error_msg = failed_platforms[0].get("error", "Publishing failed")
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=error_msg,
                    raw_response=result,
                )

            post_id = post_data.get("_id") or result.get("id") or result.get("postId")
            post_url = result.get("url") or result.get("postUrl")

            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=str(post_id) if post_id else None,
                platform_post_url=post_url,
                raw_response=result,
            )

        except PlatformError as e:
            logger.error(f"LATE API error posting image", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response if hasattr(e, "raw_response") else None,
            )
        except httpx.TimeoutException:
            logger.error(f"LATE API timeout posting image", platform=self.platform.value)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message="LATE API request timed out",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting image via LATE", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Network error: {str(e)}",
            )

    async def post_video(
        self,
        content: str,
        video_url: str,
        access_token: str = None,
        late_profile_id: str = None,
        user_id: str = None,  # Alias for late_profile_id (scheduler compatibility)
        scheduled_at: datetime = None,
        post_type: str = None,  # "feed", "story", "reel" for Instagram
        **kwargs: Any,
    ) -> PostResult:
        """
        Post a video with caption via LATE API.

        Note: TikTok is primarily video-based, so this is especially
        relevant for that platform. Instagram Reels are also video posts.

        Args:
            content: Caption text
            video_url: URL of the video to post
            access_token: LATE API key
            late_profile_id: LATE profile ID for the target account
            user_id: Alias for late_profile_id (for scheduler compatibility)
            scheduled_at: Optional datetime to schedule the post
            post_type: For Instagram - "feed", "story", or "reel"
        """
        try:
            api_key = self._get_api_key(access_token)
            platform_type = self._platform_to_late_type()

            # Get account ID - accept either parameter name
            late_account_id = late_profile_id or user_id
            if not late_account_id:
                account = await self.get_account_for_platform(api_key)
                if not account:
                    return PostResult(
                        success=False,
                        platform=self.platform,
                        error_message=f"No {self.platform.value} account connected in LATE",
                    )
                late_account_id = account.get("_id")

            # Build request payload using correct LATE API format
            media_item = {
                "type": "video",
                "url": video_url,
            }

            platform_config = {
                "platform": platform_type,
                "accountId": late_account_id,
            }

            # Add Instagram-specific post type (feed, story, reel)
            # For video posts, default to reel if not specified
            if self.platform == Platform.INSTAGRAM:
                platform_config["postType"] = post_type.lower() if post_type else "reel"

            payload = {
                "content": content,
                "mediaItems": [media_item],
                "platforms": [platform_config],
                "publishNow": scheduled_at is None,
            }

            # Add scheduling if provided
            if scheduled_at:
                payload["scheduledFor"] = scheduled_at.isoformat()

            # Add TikTok-specific settings if posting to TikTok
            if self.platform == Platform.TIKTOK:
                payload["tiktokSettings"] = self._get_tiktok_settings()

            response = await self._request(
                "POST",
                f"{self.API_BASE}/posts",
                headers=self._get_headers(api_key),
                json=payload,
                timeout=300.0,  # 5 minute timeout for video uploads
            )

            result = _check_late_response(response, self.platform.value)

            # Check platform results for failures
            post_data = result.get("post", {})
            platform_results = result.get("platformResults", [])

            failed_platforms = [p for p in platform_results if p.get("status") == "failed"]
            if failed_platforms:
                error_msg = failed_platforms[0].get("error", "Publishing failed")
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=error_msg,
                    raw_response=result,
                )

            post_id = post_data.get("_id") or result.get("id") or result.get("postId")
            post_url = result.get("url") or result.get("postUrl")

            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=str(post_id) if post_id else None,
                platform_post_url=post_url,
                raw_response=result,
            )

        except PlatformError as e:
            logger.error(f"LATE API error posting video", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response if hasattr(e, "raw_response") else None,
            )
        except httpx.TimeoutException:
            logger.error(f"LATE API timeout posting video", platform=self.platform.value)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message="LATE API request timed out",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting video via LATE", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Network error: {str(e)}",
            )

    async def delete_post(
        self,
        post_id: str,
        access_token: str = None,
        **kwargs: Any,
    ) -> bool:
        """
        Delete a post via LATE API.

        Args:
            post_id: The LATE post ID to delete
            access_token: LATE API key
        """
        try:
            api_key = self._get_api_key(access_token)

            response = await self._request(
                "DELETE",
                f"{self.API_BASE}/posts/{post_id}",
                headers=self._get_headers(api_key),
                timeout=30.0,
            )

            return response.status_code in [200, 204]

        except Exception as e:
            logger.error(f"Error deleting LATE post", post_id=post_id, error=str(e))
            return False

    async def get_posts(self, access_token: str = None) -> list[dict]:
        """
        Get all posts from LATE.

        Args:
            access_token: LATE API key

        Returns:
            List of post dictionaries
        """
        try:
            api_key = self._get_api_key(access_token)

            response = await self._request(
                "GET",
                f"{self.API_BASE}/posts",
                headers=self._get_headers(api_key),
                timeout=30.0,
            )

            if response.status_code != 200:
                return []

            return response.json()

        except Exception as e:
            logger.error(f"Error getting LATE posts", error=str(e))
            return []

    async def get_engagement(
        self,
        post_id: str,
        access_token: str = None,
        **kwargs: Any,
    ) -> EngagementData:
        """
        Get engagement metrics for a post.

        Note: LATE may not provide engagement metrics directly.
        This would need to be fetched from the platform's analytics API.
        """
        # LATE doesn't provide engagement metrics
        # Return empty data for now
        return EngagementData()

    async def reply_to_comment(
        self,
        comment_id: str,
        content: str,
        access_token: str = None,
        **kwargs: Any,
    ) -> CommentResult:
        """
        Reply to a comment.

        Note: LATE may not support comment replies - this is a posting API.
        """
        return CommentResult(
            success=False,
            platform=self.platform,
            error_message="Comment replies not supported via LATE API",
        )

    async def get_comments(
        self,
        post_id: str,
        access_token: str = None,
        **kwargs: Any,
    ) -> list[dict]:
        """
        Get comments for a post.

        Note: LATE may not support fetching comments.
        """
        return []

    async def get_profile(
        self,
        access_token: str = None,
        **kwargs: Any,
    ) -> dict:
        """
        Get the authenticated profile for this platform.
        """
        try:
            account = await self.get_account_for_platform(access_token)

            if not account:
                raise PlatformAPIError(
                    platform=self.platform.value,
                    message=f"No {self.platform.value} account connected in LATE",
                )

            return {
                "id": account.get("_id"),
                "username": account.get("username"),
                "display_name": account.get("displayName") or account.get("username"),
                "avatar_url": account.get("profilePicture") or account.get("avatar"),
                "platform": self.platform.value,
            }
        except PlatformError:
            raise
        except Exception as e:
            raise PlatformAPIError(
                platform=self.platform.value,
                message=f"LATE API error: {str(e)}",
            )

    async def refresh_token(
        self,
        refresh_token: str,
        **kwargs: Any,
    ) -> dict:
        """
        Refresh token - not applicable for LATE API.
        LATE uses a single API key, not OAuth tokens.
        """
        # LATE API keys don't expire in the same way
        return {"access_token": refresh_token}
