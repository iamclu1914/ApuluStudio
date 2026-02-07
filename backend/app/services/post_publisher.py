"""
Post Publisher - Core publishing logic for social media posts.

Handles the orchestration of publishing posts to multiple platforms,
including media processing, status updates, and error handling.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post, PostPlatform, PostStatus
from app.models.social_account import SocialAccount, Platform
from app.services.platform_factory import PlatformFactory
from app.services.storage_service import StorageService
from app.services.media_utils import get_default_aspect_ratio
from app.core.logger import logger


class PostPublisher:
    """
    Service for publishing posts to social media platforms.

    Responsibilities:
    - Orchestrate publishing to multiple platforms
    - Handle media processing (auto-cropping)
    - Update post and platform statuses
    - Error handling and logging
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the post publisher.

        Args:
            db: Async database session for status updates
        """
        self.db = db
        self._platform_factory = PlatformFactory()

    async def publish_post(self, post: Post) -> dict[str, Any]:
        """
        Publish a post to all its target platforms.

        Orchestrates the publishing process for each platform target,
        handling media processing, API calls, and status updates.

        Args:
            post: The Post model instance to publish

        Returns:
            Dictionary mapping platform post IDs to results
        """
        results = {}

        # Update post status to publishing
        post.status = PostStatus.PUBLISHING
        await self.db.commit()

        # Process each platform target
        for post_platform in post.platforms:
            if post_platform.status != PostStatus.SCHEDULED:
                continue

            result = await self._publish_to_platform(post, post_platform)
            results[post_platform.id] = result

        # Update master post status based on results
        await self._update_master_post_status(post)

        return results

    async def _publish_to_platform(
        self,
        post: Post,
        post_platform: PostPlatform,
    ) -> dict[str, Any]:
        """
        Publish a post to a single platform.

        Args:
            post: The master Post instance
            post_platform: The platform-specific post entry

        Returns:
            Result dictionary with success status and details
        """
        # Get the social account
        account_query = select(SocialAccount).where(
            SocialAccount.id == post_platform.social_account_id
        )
        account_result = await self.db.execute(account_query)
        account = account_result.scalar_one_or_none()

        if not account:
            post_platform.status = PostStatus.FAILED
            post_platform.error_message = "Social account not found"
            return {"success": False, "error": "Account not found"}

        # Get the platform service
        service = self._platform_factory.get_service(account.platform)
        if not service:
            post_platform.status = PostStatus.FAILED
            post_platform.error_message = f"Unsupported platform: {account.platform}"
            return {"success": False, "error": "Unsupported platform"}

        # Determine content to post
        content = post_platform.content or post.content

        try:
            # Determine Instagram post type from post.post_type
            instagram_post_type = self._get_instagram_post_type(account.platform, post)

            if post.media_urls and len(post.media_urls) > 0:
                # Process image with auto-cropping if needed
                image_url = await self._process_media_for_platform(
                    post.media_urls[0],
                    account,
                    post.user_id,
                )

                # Image/video post
                result = await service.post_image(
                    content=content,
                    image_url=image_url,
                    access_token=account.access_token,
                    user_id=account.platform_user_id,
                    page_id=account.page_id,
                    handle=account.username,
                    person_urn=f"urn:li:person:{account.platform_user_id}",
                    post_type=instagram_post_type,
                )
            else:
                # Text-only post
                result = await service.post_text(
                    content=content,
                    access_token=account.access_token,
                    user_id=account.platform_user_id,
                    page_id=account.page_id,
                    handle=account.username,
                    person_urn=f"urn:li:person:{account.platform_user_id}",
                )

            # Update platform post status
            if result.success:
                post_platform.status = PostStatus.PUBLISHED
                post_platform.platform_post_id = result.platform_post_id
                post_platform.platform_post_url = result.platform_post_url
                post_platform.published_at = datetime.utcnow()
            else:
                post_platform.status = PostStatus.FAILED
                post_platform.error_message = result.error_message

            return {
                "success": result.success,
                "platform": account.platform.value,
                "post_id": result.platform_post_id,
                "url": result.platform_post_url,
                "error": result.error_message,
            }

        except Exception as e:
            post_platform.status = PostStatus.FAILED
            post_platform.error_message = str(e)
            logger.error(
                "Platform publish failed",
                platform=account.platform.value,
                error=str(e),
                exc_info=True,
            )
            return {"success": False, "error": str(e)}

    async def _process_media_for_platform(
        self,
        image_url: str,
        account: SocialAccount,
        user_id: str,
    ) -> str:
        """
        Process media for a specific platform, applying auto-cropping if configured.

        Args:
            image_url: Original image URL
            account: Social account with platform preferences
            user_id: User ID for storage path

        Returns:
            Processed image URL (cropped if applicable, original otherwise)
        """
        logger.info(
            "Checking auto-crop",
            preferred_aspect_ratio=account.preferred_aspect_ratio,
            original_url=image_url[:80] if image_url else None,
        )

        target_ratio = account.preferred_aspect_ratio
        if not target_ratio or target_ratio == "original":
            target_ratio = get_default_aspect_ratio(account.platform)

        # Try to use preprocessed variant first
        variant_url = await self._get_variant_url_if_exists(
            image_url=image_url,
            platform_key=account.platform.value.lower(),
        )
        if variant_url:
            return variant_url

        if not target_ratio or target_ratio == "original":
            return image_url

        try:
            logger.info(
                "Starting auto-crop",
                aspect_ratio=target_ratio,
            )

            cropped_url = await self._auto_crop_image(
                image_url=image_url,
                aspect_ratio=target_ratio,
                user_id=user_id,
            )

            logger.info(
                "Auto-crop result",
                cropped_url=cropped_url[:80] if cropped_url else None,
            )

            if cropped_url:
                logger.info(
                    "Auto-cropped image for publishing",
                    platform=account.platform.value,
                    aspect_ratio=target_ratio,
                )
                return cropped_url

        except Exception as e:
            logger.warning(
                "Failed to auto-crop image, using original",
                error=str(e),
            )

        return image_url

    async def _get_variant_url_if_exists(
        self,
        image_url: str,
        platform_key: str,
    ) -> str | None:
        """Check for a preprocessed variant URL for the platform."""
        from app.core.http_client import get_http_client, get_http_client_context

        variant_url = StorageService.build_variant_url(image_url, platform_key)
        if not variant_url:
            return None

        try:
            try:
                client = get_http_client()
                response = await client.head(variant_url, timeout=10.0)
            except RuntimeError:
                async with get_http_client_context() as client:
                    response = await client.head(variant_url, timeout=10.0)

            if response.status_code == 200:
                return variant_url

            if response.status_code in [403, 404]:
                return None

            # Fallback to a lightweight GET if HEAD isn't supported
            try:
                client = get_http_client()
                response = await client.get(
                    variant_url,
                    headers={"Range": "bytes=0-0"},
                    timeout=10.0,
                )
            except RuntimeError:
                async with get_http_client_context() as client:
                    response = await client.get(
                        variant_url,
                        headers={"Range": "bytes=0-0"},
                        timeout=10.0,
                    )

            if response.status_code in [200, 206]:
                return variant_url

        except Exception:
            return None

        return None

    async def _auto_crop_image(
        self,
        image_url: str,
        aspect_ratio: str,
        user_id: str,
    ) -> str | None:
        """
        Download image, crop to aspect ratio, re-upload, return new URL.

        Args:
            image_url: Original image URL (Supabase storage)
            aspect_ratio: Target aspect ratio (e.g., "4:5", "1:1")
            user_id: User ID for storage path

        Returns:
            New image URL if cropped, None if failed or no crop needed
        """
        from app.core.http_client import get_http_client, get_http_client_context

        # Download original image using shared client
        try:
            client = get_http_client()
            response = await client.get(image_url, timeout=60.0)
        except RuntimeError:
            # Fallback to temporary client
            async with get_http_client_context() as client:
                response = await client.get(image_url, timeout=60.0)
        response.raise_for_status()
        image_data = response.content

        # Crop and upload
        storage = StorageService()
        result = await storage.upload_image(
            file_data=image_data,
            file_name="auto_cropped.jpg",
            content_type="image/jpeg",
            user_id=user_id,
            aspect_ratio=aspect_ratio,
        )

        if result.get("success") and result.get("cropped"):
            return result.get("url")

        return None

    def _get_instagram_post_type(self, platform: Platform, post: Post) -> str | None:
        """
        Determine Instagram-specific post type.

        Args:
            platform: The target platform
            post: The post being published

        Returns:
            Instagram post type string or None for non-Instagram platforms
        """
        if platform != Platform.INSTAGRAM:
            return None

        if post.post_type.value in ["story", "reel"]:
            return post.post_type.value
        return "feed"  # Default to feed

    async def _update_master_post_status(self, post: Post) -> None:
        """
        Update master post status based on platform results.

        Args:
            post: The Post instance to update
        """
        all_published = all(
            pp.status == PostStatus.PUBLISHED
            for pp in post.platforms
        )
        any_published = any(
            pp.status == PostStatus.PUBLISHED
            for pp in post.platforms
        )

        if all_published:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
        elif any_published:
            # Partial success - some platforms published
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
        else:
            post.status = PostStatus.FAILED

        await self.db.commit()
