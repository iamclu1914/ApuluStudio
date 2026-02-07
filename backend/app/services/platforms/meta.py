"""Meta (Instagram, Facebook, Threads) platform service with connection pooling."""

import httpx
from typing import Any

from app.services.platforms.base import (
    BasePlatformService,
    PostResult,
    CommentResult,
    EngagementData,
)
from app.models.social_account import Platform
from app.core.config import get_settings
from app.core.http_client import get_http_client, get_http_client_context
from app.core.exceptions import (
    PlatformError,
    PlatformAuthenticationError,
    PlatformRateLimitError,
    PlatformAPIError,
    NetworkError,
)
from app.core.logger import logger

settings = get_settings()


def _parse_meta_error(response_data: dict) -> tuple[str, str | None]:
    """
    Parse error message and code from Meta API response.

    Returns:
        Tuple of (error_message, error_code)
    """
    error = response_data.get("error", {})
    message = error.get("message", "Unknown Meta API error")
    code = error.get("code")
    return message, code


def _check_meta_response(
    response: httpx.Response,
    platform: Platform,
) -> dict:
    """
    Check Meta API response for errors and raise appropriate exceptions.

    Returns:
        Parsed response data if successful

    Raises:
        PlatformAuthenticationError: For auth/token errors
        PlatformRateLimitError: For rate limit errors
        PlatformAPIError: For other API errors
    """
    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code == 200 and "error" not in data:
        return data

    message, error_code = _parse_meta_error(data)

    # Check for authentication errors
    if response.status_code == 401 or error_code in [190, 102, 104]:
        raise PlatformAuthenticationError(
            platform=platform.value,
            message=f"Meta API authentication failed: {message}",
            raw_response=data,
        )

    # Check for rate limiting
    if response.status_code == 429 or error_code in [4, 17, 341]:
        raise PlatformRateLimitError(
            platform=platform.value,
            message=f"Meta API rate limit exceeded: {message}",
            raw_response=data,
        )

    # Check for permission errors
    if response.status_code == 403 or error_code in [10, 200, 230]:
        raise PlatformAPIError(
            platform=platform.value,
            message=f"Meta API permission denied: {message}",
            platform_error_code=error_code,
            status_code=403,
            raw_response=data,
        )

    # Generic API error
    raise PlatformAPIError(
        platform=platform.value,
        message=message,
        platform_error_code=error_code,
        status_code=response.status_code,
        raw_response=data,
    )


class MetaService(BasePlatformService):
    """Meta (Instagram, Facebook, Threads) platform service with connection pooling."""

    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, platform: Platform = Platform.INSTAGRAM):
        self.platform = platform

    def _get_client(self) -> httpx.AsyncClient:
        """Get the shared HTTP client."""
        try:
            return get_http_client()
        except RuntimeError:
            # Fallback for when global client isn't initialized
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

    async def post_text(
        self,
        content: str,
        access_token: str,
        page_id: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post text content (Facebook only - IG requires media)."""
        if self.platform == Platform.INSTAGRAM:
            return PostResult(
                success=False,
                platform=self.platform,
                error_message="Instagram requires an image or video for posts",
            )

        try:
            response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{page_id}/feed",
                data={
                    "message": content,
                    "access_token": access_token,
                },
            )
            data = _check_meta_response(response, self.platform)

            if "id" in data:
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=data["id"],
                    platform_post_url=f"https://facebook.com/{data['id']}",
                    raw_response=data,
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=data.get("error", {}).get("message", "Unknown error"),
                    raw_response=data,
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting text", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response,
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout posting to Meta", platform=self.platform.value)
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Request timed out: {str(e)}",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting to Meta", platform=self.platform.value, error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Network error: {str(e)}",
            )

    async def post_image(
        self,
        content: str,
        image_url: str,
        access_token: str,
        user_id: str = None,
        page_id: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post an image with caption to Instagram or Facebook."""

        if self.platform == Platform.INSTAGRAM:
            return await self._post_instagram_image(
                content, image_url, access_token, user_id
            )
        elif self.platform == Platform.FACEBOOK:
            return await self._post_facebook_image(
                content, image_url, access_token, page_id
            )
        elif self.platform == Platform.THREADS:
            return await self._post_threads(
                content, image_url, access_token, user_id
            )

        return PostResult(
            success=False,
            platform=self.platform,
            error_message=f"Unsupported platform: {self.platform}",
        )

    async def _post_instagram_image(
        self,
        content: str,
        image_url: str,
        access_token: str,
        user_id: str,
    ) -> PostResult:
        """Post image to Instagram using two-step container process."""
        try:
            # Step 1: Create media container
            create_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/media",
                data={
                    "image_url": image_url,
                    "caption": content,
                    "access_token": access_token,
                },
            )
            create_data = _check_meta_response(create_response, self.platform)

            if "id" not in create_data:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=create_data.get("error", {}).get("message", "Container creation failed"),
                    raw_response=create_data,
                )

            container_id = create_data["id"]

            # Step 2: Publish the container
            publish_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            publish_data = _check_meta_response(publish_response, self.platform)

            if "id" in publish_data:
                media_id = publish_data["id"]
                # Get permalink
                permalink = await self._get_instagram_permalink(
                    media_id, access_token
                )

                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=media_id,
                    platform_post_url=permalink,
                    raw_response=publish_data,
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=publish_data.get("error", {}).get("message", "Publish failed"),
                    raw_response=publish_data,
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting Instagram image", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Network error posting Instagram image", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def _post_facebook_image(
        self,
        content: str,
        image_url: str,
        access_token: str,
        page_id: str,
    ) -> PostResult:
        """Post image to Facebook Page."""
        try:
            response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{page_id}/photos",
                data={
                    "url": image_url,
                    "caption": content,
                    "access_token": access_token,
                },
            )
            data = _check_meta_response(response, self.platform)

            if "id" in data:
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=data["id"],
                    platform_post_url=f"https://facebook.com/{data['id']}",
                    raw_response=data,
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=data.get("error", {}).get("message", "Unknown error"),
                    raw_response=data,
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting Facebook image", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Network error posting Facebook image", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def _post_threads(
        self,
        content: str,
        image_url: str | None,
        access_token: str,
        user_id: str,
    ) -> PostResult:
        """Post to Threads."""
        try:
            # Step 1: Create container
            data = {
                "media_type": "IMAGE" if image_url else "TEXT",
                "text": content,
                "access_token": access_token,
            }
            if image_url:
                data["image_url"] = image_url

            create_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/threads",
                data=data,
            )
            create_data = _check_meta_response(create_response, Platform.THREADS)

            if "id" not in create_data:
                return PostResult(
                    success=False,
                    platform=Platform.THREADS,
                    error_message=create_data.get("error", {}).get("message", "Container creation failed"),
                )

            container_id = create_data["id"]

            # Step 2: Publish
            publish_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/threads_publish",
                data={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            publish_data = _check_meta_response(publish_response, Platform.THREADS)

            if "id" in publish_data:
                return PostResult(
                    success=True,
                    platform=Platform.THREADS,
                    platform_post_id=publish_data["id"],
                    platform_post_url=f"https://threads.net/t/{publish_data['id']}",
                    raw_response=publish_data,
                )
            else:
                return PostResult(
                    success=False,
                    platform=Platform.THREADS,
                    error_message=publish_data.get("error", {}).get("message", "Publish failed"),
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting to Threads", error=str(e))
            return PostResult(
                success=False,
                platform=Platform.THREADS,
                error_message=e.message,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Network error posting to Threads", error=str(e))
            return PostResult(
                success=False,
                platform=Platform.THREADS,
                error_message=str(e),
            )

    async def _get_instagram_permalink(
        self,
        media_id: str,
        access_token: str,
    ) -> str | None:
        """Get the permalink for an Instagram post."""
        try:
            response = await self._request(
                "GET",
                f"{self.GRAPH_API_BASE}/{media_id}",
                params={
                    "fields": "permalink",
                    "access_token": access_token,
                },
            )
            data = response.json()
            return data.get("permalink")
        except Exception:
            return None

    async def post_video(
        self,
        content: str,
        video_url: str,
        access_token: str,
        user_id: str = None,
        page_id: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post a video (Reel for IG)."""
        if self.platform == Platform.INSTAGRAM:
            return await self._post_instagram_reel(
                content, video_url, access_token, user_id
            )

        # Facebook video posting
        try:
            response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{page_id}/videos",
                data={
                    "file_url": video_url,
                    "description": content,
                    "access_token": access_token,
                },
            )
            data = _check_meta_response(response, self.platform)

            if "id" in data:
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=data["id"],
                    raw_response=data,
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=data.get("error", {}).get("message"),
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting video", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Network error posting video", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def _post_instagram_reel(
        self,
        content: str,
        video_url: str,
        access_token: str,
        user_id: str,
    ) -> PostResult:
        """Post a Reel to Instagram."""
        try:
            # Step 1: Create video container
            create_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": content,
                    "access_token": access_token,
                },
            )
            create_data = _check_meta_response(create_response, self.platform)

            if "id" not in create_data:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=create_data.get("error", {}).get("message"),
                )

            container_id = create_data["id"]

            # Wait for video processing (simplified - in production, poll status)
            import asyncio
            await asyncio.sleep(5)

            # Step 2: Publish
            publish_response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": access_token,
                },
            )
            publish_data = _check_meta_response(publish_response, self.platform)

            if "id" in publish_data:
                permalink = await self._get_instagram_permalink(
                    publish_data["id"], access_token
                )
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=publish_data["id"],
                    platform_post_url=permalink,
                )
            else:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=publish_data.get("error", {}).get("message"),
                )

        except PlatformError as e:
            logger.error(f"Meta API error posting Instagram Reel", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            logger.error(f"Network error posting Instagram Reel", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def delete_post(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a post."""
        try:
            response = await self._request(
                "DELETE",
                f"{self.GRAPH_API_BASE}/{post_id}",
                params={"access_token": access_token},
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting Meta post", post_id=post_id, error=str(e))
            return False

    async def get_engagement(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> EngagementData:
        """Get engagement metrics for a post."""
        try:
            fields = "like_count,comments_count,shares"
            if self.platform == Platform.INSTAGRAM:
                fields = "like_count,comments_count,impressions,reach"

            response = await self._request(
                "GET",
                f"{self.GRAPH_API_BASE}/{post_id}",
                params={
                    "fields": fields,
                    "access_token": access_token,
                },
            )
            data = response.json()

            return EngagementData(
                likes=data.get("like_count", 0),
                comments=data.get("comments_count", 0),
                shares=data.get("shares", {}).get("count", 0) if isinstance(data.get("shares"), dict) else 0,
                impressions=data.get("impressions", 0),
                reach=data.get("reach", 0),
            )
        except Exception as e:
            logger.error(f"Error getting Meta engagement", post_id=post_id, error=str(e))
            return EngagementData()

    async def reply_to_comment(
        self,
        comment_id: str,
        content: str,
        access_token: str,
        **kwargs: Any,
    ) -> CommentResult:
        """Reply to a comment."""
        try:
            response = await self._request(
                "POST",
                f"{self.GRAPH_API_BASE}/{comment_id}/replies",
                data={
                    "message": content,
                    "access_token": access_token,
                },
            )
            data = _check_meta_response(response, self.platform)

            if "id" in data:
                return CommentResult(
                    success=True,
                    platform=self.platform,
                    comment_id=data["id"],
                )
            else:
                return CommentResult(
                    success=False,
                    platform=self.platform,
                    error_message=data.get("error", {}).get("message"),
                )

        except PlatformError as e:
            return CommentResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
            )
        except (httpx.TimeoutException, httpx.RequestError) as e:
            return CommentResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def get_comments(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> list[dict]:
        """Get comments for a post."""
        try:
            response = await self._request(
                "GET",
                f"{self.GRAPH_API_BASE}/{post_id}/comments",
                params={
                    "fields": "id,text,from,like_count,timestamp",
                    "access_token": access_token,
                },
            )
            data = response.json()

            comments = []
            for comment in data.get("data", []):
                comments.append({
                    "id": comment["id"],
                    "content": comment.get("text", ""),
                    "author_id": comment.get("from", {}).get("id"),
                    "author_username": comment.get("from", {}).get("name"),
                    "likes_count": comment.get("like_count", 0),
                    "created_at": comment.get("timestamp"),
                })

            return comments
        except Exception as e:
            logger.error(f"Error getting Meta comments", post_id=post_id, error=str(e))
            return []

    async def get_profile(
        self,
        access_token: str,
        user_id: str = None,
        **kwargs: Any,
    ) -> dict:
        """Get the user's profile."""
        try:
            endpoint = user_id or "me"
            fields = "id,username,name,profile_picture_url,followers_count,follows_count,media_count"

            if self.platform == Platform.FACEBOOK:
                fields = "id,name,picture"

            response = await self._request(
                "GET",
                f"{self.GRAPH_API_BASE}/{endpoint}",
                params={
                    "fields": fields,
                    "access_token": access_token,
                },
            )
            data = response.json()

            return {
                "id": data.get("id"),
                "username": data.get("username", data.get("name")),
                "display_name": data.get("name"),
                "avatar_url": data.get("profile_picture_url", data.get("picture", {}).get("data", {}).get("url")),
                "followers_count": data.get("followers_count", 0),
                "following_count": data.get("follows_count", 0),
                "posts_count": data.get("media_count", 0),
            }
        except Exception as e:
            logger.error(f"Error getting Meta profile", error=str(e))
            return {}

    async def refresh_token(
        self,
        refresh_token: str,
        **kwargs: Any,
    ) -> dict:
        """Refresh the access token (exchange for long-lived token)."""
        try:
            response = await self._request(
                "GET",
                f"{self.GRAPH_API_BASE}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "fb_exchange_token": refresh_token,
                },
            )
            data = response.json()

            return {
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in"),
            }
        except Exception as e:
            logger.error(f"Error refreshing Meta token", error=str(e))
            return {}
