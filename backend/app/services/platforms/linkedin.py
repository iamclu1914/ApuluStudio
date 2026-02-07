"""LinkedIn platform service with connection pooling."""

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
)
from app.core.logger import logger

settings = get_settings()


def _check_linkedin_response(
    response: httpx.Response,
) -> dict:
    """
    Check LinkedIn API response for errors and raise appropriate exceptions.

    Returns:
        Parsed response data if successful

    Raises:
        PlatformAuthenticationError: For auth/token errors
        PlatformRateLimitError: For rate limit errors
        PlatformAPIError: For other API errors
    """
    try:
        data = response.json() if response.text else {}
    except Exception:
        data = {}

    if response.status_code in [200, 201, 204]:
        return data

    message = data.get("message", f"LinkedIn API error: HTTP {response.status_code}")
    service_error_code = data.get("serviceErrorCode")

    # Authentication errors
    if response.status_code == 401 or service_error_code in [65600, 65601]:
        raise PlatformAuthenticationError(
            platform="linkedin",
            message=f"LinkedIn authentication failed: {message}",
            raw_response=data,
        )

    # Rate limiting
    if response.status_code == 429:
        raise PlatformRateLimitError(
            platform="linkedin",
            message=f"LinkedIn API rate limit exceeded: {message}",
            raw_response=data,
        )

    # Permission errors
    if response.status_code == 403:
        raise PlatformAPIError(
            platform="linkedin",
            message=f"LinkedIn permission denied: {message}",
            platform_error_code=service_error_code,
            status_code=403,
            raw_response=data,
        )

    # Generic API error
    raise PlatformAPIError(
        platform="linkedin",
        message=message,
        platform_error_code=service_error_code,
        status_code=response.status_code,
        raw_response=data,
    )


class LinkedInService(BasePlatformService):
    """LinkedIn platform service with connection pooling."""

    platform = Platform.LINKEDIN
    API_BASE = "https://api.linkedin.com/v2"
    REST_API_BASE = "https://api.linkedin.com/rest"

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

    def _get_rest_headers(self, access_token: str) -> dict:
        """Get headers for LinkedIn REST API requests."""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401",
        }

    async def post_text(
        self,
        content: str,
        access_token: str,
        person_urn: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post text content to LinkedIn."""
        try:
            response = await self._request(
                "POST",
                f"{self.REST_API_BASE}/posts",
                headers=self._get_rest_headers(access_token),
                json={
                    "author": person_urn,
                    "commentary": content,
                    "visibility": "PUBLIC",
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                        "targetEntities": [],
                        "thirdPartyDistributionChannels": [],
                    },
                    "lifecycleState": "PUBLISHED",
                },
            )

            if response.status_code in [200, 201]:
                # Extract post ID from response headers
                post_id = response.headers.get("x-restli-id", "")
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=post_id,
                    platform_post_url=f"https://www.linkedin.com/feed/update/{post_id}",
                    raw_response=response.json() if response.text else {},
                )
            else:
                _check_linkedin_response(response)
                # If _check_linkedin_response doesn't raise, return failure
                error_data = response.json() if response.text else {}
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message=error_data.get("message", f"HTTP {response.status_code}"),
                    raw_response=error_data,
                )

        except PlatformError as e:
            logger.error(f"LinkedIn API error posting text", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response,
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout posting to LinkedIn")
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Request timed out: {str(e)}",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting to LinkedIn", error=str(e))
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
        person_urn: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post an image with text to LinkedIn."""
        try:
            # Step 1: Initialize upload
            init_response = await self._request(
                "POST",
                f"{self.REST_API_BASE}/images?action=initializeUpload",
                headers=self._get_rest_headers(access_token),
                json={
                    "initializeUploadRequest": {
                        "owner": person_urn,
                    }
                },
            )

            if init_response.status_code != 200:
                _check_linkedin_response(init_response)
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message="Failed to initialize image upload",
                )

            init_data = init_response.json()
            upload_url = init_data["value"]["uploadUrl"]
            image_urn = init_data["value"]["image"]

            # Step 2: Download and upload image
            img_response = await self._request("GET", image_url)
            img_data = img_response.content

            upload_response = await self._request(
                "PUT",
                upload_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/octet-stream",
                },
                content=img_data,
            )

            if upload_response.status_code not in [200, 201]:
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message="Failed to upload image",
                )

            # Step 3: Create post with image
            post_response = await self._request(
                "POST",
                f"{self.REST_API_BASE}/posts",
                headers=self._get_rest_headers(access_token),
                json={
                    "author": person_urn,
                    "commentary": content,
                    "visibility": "PUBLIC",
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                        "targetEntities": [],
                        "thirdPartyDistributionChannels": [],
                    },
                    "content": {
                        "media": {
                            "id": image_urn,
                        }
                    },
                    "lifecycleState": "PUBLISHED",
                },
            )

            if post_response.status_code in [200, 201]:
                post_id = post_response.headers.get("x-restli-id", "")
                return PostResult(
                    success=True,
                    platform=self.platform,
                    platform_post_id=post_id,
                    platform_post_url=f"https://www.linkedin.com/feed/update/{post_id}",
                )
            else:
                _check_linkedin_response(post_response)
                return PostResult(
                    success=False,
                    platform=self.platform,
                    error_message="Failed to create post",
                )

        except PlatformError as e:
            logger.error(f"LinkedIn API error posting image", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=e.message,
                raw_response=e.raw_response,
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout posting image to LinkedIn")
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Request timed out: {str(e)}",
            )
        except httpx.RequestError as e:
            logger.error(f"Network error posting image to LinkedIn", error=str(e))
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=f"Network error: {str(e)}",
            )

    async def post_video(
        self,
        content: str,
        video_url: str,
        access_token: str,
        person_urn: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post a video to LinkedIn - simplified, posts as link."""
        # Full video upload is complex; for MVP, post as link
        content_with_link = f"{content}\n\n{video_url}"
        return await self.post_text(
            content=content_with_link,
            access_token=access_token,
            person_urn=person_urn,
        )

    async def delete_post(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a LinkedIn post."""
        try:
            response = await self._request(
                "DELETE",
                f"{self.REST_API_BASE}/posts/{post_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "LinkedIn-Version": "202401",
                },
            )
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error deleting LinkedIn post", post_id=post_id, error=str(e))
            return False

    async def get_engagement(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> EngagementData:
        """Get engagement metrics - LinkedIn API has limited access."""
        # LinkedIn's engagement API requires special permissions
        # Return empty for MVP
        return EngagementData()

    async def reply_to_comment(
        self,
        comment_id: str,
        content: str,
        access_token: str,
        **kwargs: Any,
    ) -> CommentResult:
        """Reply to a LinkedIn comment."""
        # LinkedIn comment API requires specific permissions
        return CommentResult(
            success=False,
            platform=self.platform,
            error_message="LinkedIn comment replies require additional API permissions",
        )

    async def get_comments(
        self,
        post_id: str,
        access_token: str,
        **kwargs: Any,
    ) -> list[dict]:
        """Get comments - requires Marketing API access."""
        return []

    async def get_profile(
        self,
        access_token: str,
        **kwargs: Any,
    ) -> dict:
        """Get the authenticated user's LinkedIn profile."""
        try:
            response = await self._request(
                "GET",
                f"{self.API_BASE}/userinfo",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
            )
            data = response.json()

            return {
                "id": data.get("sub"),
                "username": data.get("email", "").split("@")[0],
                "display_name": data.get("name"),
                "avatar_url": data.get("picture"),
                "email": data.get("email"),
                "person_urn": f"urn:li:person:{data.get('sub')}",
            }
        except Exception as e:
            logger.error(f"Error getting LinkedIn profile", error=str(e))
            return {}

    async def refresh_token(
        self,
        refresh_token: str,
        **kwargs: Any,
    ) -> dict:
        """Refresh the LinkedIn access token."""
        try:
            response = await self._request(
                "POST",
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.linkedin_client_id,
                    "client_secret": settings.linkedin_client_secret,
                },
            )
            data = response.json()

            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
            }
        except Exception as e:
            logger.error(f"Error refreshing LinkedIn token", error=str(e))
            return {}
