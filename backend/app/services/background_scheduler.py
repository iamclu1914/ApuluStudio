"""
Background Scheduler - Automatic post publishing service.

Runs as a background task within the FastAPI application to:
1. Check for scheduled posts that are due
2. Automatically publish them to their target platforms
3. Handle retries for failed posts
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.logger import logger
from app.models.post import Post, PostPlatform, PostStatus
from app.services.scheduler_service import SchedulerService


class BackgroundScheduler:
    """
    Background scheduler that periodically checks for and publishes due posts.

    Runs as an asyncio task within the FastAPI application lifecycle.
    """

    def __init__(self, check_interval: int = 60):
        """
        Initialize the background scheduler.

        Args:
            check_interval: Seconds between checks for due posts (default: 60)
        """
        self.check_interval = check_interval
        self._task: asyncio.Task | None = None
        self._running = False
        self._on_publish_callback: Callable | None = None

    def set_publish_callback(self, callback: Callable):
        """Set a callback to be called when a post is published."""
        self._on_publish_callback = callback

    async def start(self):
        """Start the background scheduler."""
        if self._running:
            logger.warning("Background scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info(
            "Background scheduler started",
            check_interval=self.check_interval,
        )

    async def stop(self):
        """Stop the background scheduler gracefully."""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("Background scheduler stopped")

    async def _run_scheduler(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_publish_due_posts()
            except Exception as e:
                logger.error(
                    "Error in scheduler loop",
                    error=str(e),
                    exc_info=True,
                )

            # Wait for next check interval
            await asyncio.sleep(self.check_interval)

    async def _check_and_publish_due_posts(self):
        """Check for due posts and publish them."""
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()

            # Find all scheduled posts that are due
            query = (
                select(Post)
                .where(
                    and_(
                        Post.status == PostStatus.SCHEDULED,
                        Post.scheduled_at <= now,
                    )
                )
                .options(
                    selectinload(Post.platforms).selectinload(PostPlatform.social_account)
                )
            )

            result = await db.execute(query)
            due_posts = list(result.scalars().all())

            if not due_posts:
                return

            logger.info(
                "Found due posts to publish",
                count=len(due_posts),
            )

            # Create scheduler service and publish each post
            scheduler = SchedulerService(db)

            for post in due_posts:
                try:
                    logger.info(
                        "Publishing scheduled post",
                        post_id=post.id,
                        scheduled_at=post.scheduled_at.isoformat() if post.scheduled_at else None,
                        platforms=[pp.social_account.platform.value for pp in post.platforms if pp.social_account],
                    )

                    results = await scheduler.publish_post(post)

                    # Log results
                    success_count = sum(1 for r in results.values() if r.get("success"))
                    fail_count = len(results) - success_count

                    logger.info(
                        "Post publish completed",
                        post_id=post.id,
                        success_count=success_count,
                        fail_count=fail_count,
                        results=results,
                    )

                    # Call callback if set
                    if self._on_publish_callback:
                        try:
                            await self._on_publish_callback(post, results)
                        except Exception as e:
                            logger.error(
                                "Error in publish callback",
                                error=str(e),
                            )

                except Exception as e:
                    logger.error(
                        "Failed to publish post",
                        post_id=post.id,
                        error=str(e),
                        exc_info=True,
                    )

                    # Mark post as failed
                    post.status = PostStatus.FAILED
                    await db.commit()

    async def check_now(self):
        """Manually trigger a check for due posts (useful for testing)."""
        await self._check_and_publish_due_posts()

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running


# Singleton instance
background_scheduler = BackgroundScheduler(check_interval=60)


async def start_scheduler():
    """Start the background scheduler."""
    await background_scheduler.start()


async def stop_scheduler():
    """Stop the background scheduler."""
    await background_scheduler.stop()
