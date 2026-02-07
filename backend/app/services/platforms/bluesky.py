import asyncio
import logging
from functools import partial
from typing import Any

from atproto import Client, models
from atproto_client.exceptions import (
    UnauthorizedError as AtprotoUnauthorizedError,
    RequestErrorBase,
)
from atproto_core.exceptions import AtProtocolError

from app.services.platforms.base import (
    BasePlatformService,
    PostResult,
    CommentResult,
    EngagementData,
)
from app.models.social_account import Platform
from app.services.media_processor import MediaProcessor
from app.core.exceptions import ExternalServiceError


logger = logging.getLogger(__name__)


class BlueskyService(BasePlatformService):
    """Bluesky (AT Protocol) platform service.

    Uses asyncio.to_thread() to run synchronous atproto client calls
    without blocking the event loop.
    """

    platform = Platform.BLUESKY

    def __init__(self):
        self._client: Client | None = None

    async def _run_sync(self, func, *args, **kwargs) -> Any:
        """Run a synchronous function in a thread pool executor.

        This prevents blocking the event loop when calling synchronous
        atproto client methods.

        Args:
            func: The synchronous function to run
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            ExternalServiceError: If the atproto call fails
        """
        try:
            # Use partial to bind kwargs since to_thread doesn't support them directly
            if kwargs:
                func_with_kwargs = partial(func, *args, **kwargs)
                return await asyncio.to_thread(func_with_kwargs)
            return await asyncio.to_thread(func, *args)
        except AtprotoUnauthorizedError as e:
            details = self._format_atproto_error(e)
            logger.error(f"[Bluesky] Authentication failed: {details}")
            raise ExternalServiceError("Bluesky", f"Authentication failed: {details}")
        except RequestErrorBase as e:
            details = self._format_atproto_error(e)
            logger.error(f"[Bluesky] Request error: {details}")
            raise ExternalServiceError("Bluesky", details)
        except AtProtocolError as e:
            details = self._format_atproto_error(e)
            logger.error(f"[Bluesky] AT Protocol error: {details}")
            raise ExternalServiceError("Bluesky", details)
        except Exception as e:
            logger.error(f"[Bluesky] Unexpected error in sync call: {repr(e)}")
            raise

    def _format_atproto_error(self, error: Exception) -> str:
        parts = [type(error).__name__]
        response = getattr(error, "response", None)
        if response is not None:
            parts.append(f"status={getattr(response, 'status_code', 'unknown')}")
            content = getattr(response, "content", None)
            if content is not None:
                err_code = getattr(content, "error", None)
                err_msg = getattr(content, "message", None)
                if err_code:
                    parts.append(f"error={err_code}")
                if err_msg:
                    parts.append(f"message={err_msg}")
                elif isinstance(content, (bytes, bytearray)):
                    parts.append(f"content={content[:200]!r}")
                else:
                    parts.append(f"content={content!r}")

        raw = str(error)
        if raw:
            parts.append(f"details={raw}")
        return " | ".join(parts)

    async def _get_client(self, handle: str, app_password: str) -> Client:
        """Get authenticated Bluesky client.

        Runs the synchronous login in a thread pool to avoid blocking.
        """
        if not handle:
            raise ExternalServiceError("Bluesky", "Missing handle for account")
        if not app_password:
            raise ExternalServiceError("Bluesky", "Missing app password for account")
        client = Client()
        await self._run_sync(client.login, handle, app_password)
        return client

    async def post_text(
        self,
        content: str,
        access_token: str,  # For Bluesky, this is the app password
        handle: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post text content to Bluesky."""
        try:
            client = await self._get_client(handle, access_token)
            response = await self._run_sync(client.send_post, text=content)

            # Extract the post URI and convert to web URL
            post_uri = response.uri
            # Format: at://did:plc:xxx/app.bsky.feed.post/xxx
            parts = post_uri.split("/")
            rkey = parts[-1]

            logger.info(f"[Bluesky] Successfully posted text to {handle}")
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=post_uri,
                platform_post_url=f"https://bsky.app/profile/{handle}/post/{rkey}",
                raw_response={"uri": post_uri, "cid": response.cid},
            )
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"[Bluesky] Failed to post text: {e}")
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def post_image(
        self,
        content: str,
        image_url: str,
        access_token: str,
        handle: str = None,
        alt_text: str = "",
        **kwargs: Any,
    ) -> PostResult:
        """Post an image with caption to Bluesky."""
        try:
            client = await self._get_client(handle, access_token)

            # Process image to meet Bluesky's 1MB limit
            processor = MediaProcessor(Platform.BLUESKY)
            processed = await processor.process_image_from_url(image_url)

            if processed.was_modified:
                logger.info(f"[Bluesky] Image processed: {', '.join(processed.modifications)}")
                logger.info(f"[Bluesky] Final size: {processed.width}x{processed.height}, {processed.file_size_bytes / 1024:.1f}KB")

            img_data = processed.data

            # Upload the image blob (sync operation)
            upload = await self._run_sync(client.upload_blob, img_data)

            # Create post with image embed
            images = [models.AppBskyEmbedImages.Image(
                alt=alt_text or "Image uploaded via Apulu Studio",
                image=upload.blob,
            )]
            embed = models.AppBskyEmbedImages.Main(images=images)

            response = await self._run_sync(client.send_post, text=content, embed=embed)

            post_uri = response.uri
            parts = post_uri.split("/")
            rkey = parts[-1]

            logger.info(f"[Bluesky] Successfully posted image to {handle}")
            return PostResult(
                success=True,
                platform=self.platform,
                platform_post_id=post_uri,
                platform_post_url=f"https://bsky.app/profile/{handle}/post/{rkey}",
                raw_response={"uri": post_uri, "cid": response.cid},
            )
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"[Bluesky] Failed to post image: {e}")
            return PostResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def post_video(
        self,
        content: str,
        video_url: str,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> PostResult:
        """Post a video - Bluesky has limited video support."""
        # Bluesky video support is still evolving
        # For now, post as text with link
        content_with_link = f"{content}\n\n{video_url}"
        return await self.post_text(
            content=content_with_link,
            access_token=access_token,
            handle=handle,
        )

    async def delete_post(
        self,
        post_id: str,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> bool:
        """Delete a post from Bluesky."""
        try:
            client = await self._get_client(handle, access_token)
            # post_id is the AT URI
            await self._run_sync(client.delete_post, post_id)
            logger.info(f"[Bluesky] Successfully deleted post {post_id}")
            return True
        except Exception as e:
            logger.error(f"[Bluesky] Failed to delete post {post_id}: {e}")
            return False

    async def get_engagement(
        self,
        post_id: str,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> EngagementData:
        """Get engagement metrics for a Bluesky post."""
        try:
            client = await self._get_client(handle, access_token)

            # Get the post thread to access metrics (sync operation)
            thread = await self._run_sync(client.get_post_thread, uri=post_id)
            post = thread.thread.post

            return EngagementData(
                likes=post.like_count or 0,
                comments=post.reply_count or 0,
                shares=post.repost_count or 0,
                impressions=0,  # Not available in Bluesky API
                reach=0,
            )
        except Exception as e:
            logger.warning(f"[Bluesky] Failed to get engagement for {post_id}: {e}")
            return EngagementData()

    async def reply_to_comment(
        self,
        comment_id: str,
        content: str,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> CommentResult:
        """Reply to a post/comment on Bluesky."""
        try:
            client = await self._get_client(handle, access_token)

            # Get the parent post for reply reference (sync operation)
            thread = await self._run_sync(client.get_post_thread, uri=comment_id)
            parent = thread.thread.post

            # Create reply
            reply_ref = models.AppBskyFeedPost.ReplyRef(
                parent=models.create_strong_ref(parent),
                root=models.create_strong_ref(parent),
            )

            response = await self._run_sync(client.send_post, text=content, reply_to=reply_ref)

            logger.info(f"[Bluesky] Successfully replied to {comment_id}")
            return CommentResult(
                success=True,
                platform=self.platform,
                comment_id=response.uri,
            )
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"[Bluesky] Failed to reply to comment {comment_id}: {e}")
            return CommentResult(
                success=False,
                platform=self.platform,
                error_message=str(e),
            )

    async def get_comments(
        self,
        post_id: str,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> list[dict]:
        """Get replies to a Bluesky post."""
        try:
            client = await self._get_client(handle, access_token)
            thread = await self._run_sync(client.get_post_thread, uri=post_id)

            comments = []
            if hasattr(thread.thread, 'replies') and thread.thread.replies:
                for reply in thread.thread.replies:
                    if hasattr(reply, 'post'):
                        comments.append({
                            "id": reply.post.uri,
                            "content": reply.post.record.text,
                            "author_id": reply.post.author.did,
                            "author_username": reply.post.author.handle,
                            "author_avatar": reply.post.author.avatar,
                            "likes_count": reply.post.like_count or 0,
                            "created_at": reply.post.indexed_at,
                        })

            return comments
        except Exception as e:
            logger.warning(f"[Bluesky] Failed to get comments for {post_id}: {e}")
            return []

    async def get_profile(
        self,
        access_token: str,
        handle: str = None,
        **kwargs: Any,
    ) -> dict:
        """Get the authenticated user's Bluesky profile."""
        try:
            client = await self._get_client(handle, access_token)
            profile = await self._run_sync(client.get_profile, handle)

            return {
                "id": profile.did,
                "username": profile.handle,
                "display_name": profile.display_name,
                "avatar_url": profile.avatar,
                "followers_count": profile.followers_count or 0,
                "following_count": profile.follows_count or 0,
                "posts_count": profile.posts_count or 0,
            }
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"[Bluesky] Failed to get profile for {handle}: {e}")
            # Re-raise with more context instead of silently failing
            raise ExternalServiceError("Bluesky", f"Authentication failed: {str(e)}")

    async def refresh_token(
        self,
        refresh_token: str,
        **kwargs: Any,
    ) -> dict:
        """Bluesky uses app passwords, no refresh needed."""
        # App passwords don't expire
        return {"access_token": refresh_token}
