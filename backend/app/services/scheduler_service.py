"""
Scheduler Service - Post scheduling coordinator.

Handles scheduling logic, due post queries, and smart timing suggestions.
Delegates actual publishing to PostPublisher.
"""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post, PostPlatform, PostStatus
from app.models.social_account import SocialAccount, Platform
from app.services.post_publisher import PostPublisher


class SchedulerService:
    """
    Service for scheduling and coordinating post publication.

    Responsibilities:
    - Schedule posts for future publication
    - Query for posts due for publishing
    - Cancel and reschedule posts
    - Provide smart timing suggestions

    Note: Actual publishing is delegated to PostPublisher.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the scheduler service.

        Args:
            db: Async database session
        """
        self.db = db
        self._publisher = PostPublisher(db)

    async def get_due_posts(self) -> list[Post]:
        """
        Get all posts that are due for publishing.

        Returns:
            List of Post instances with scheduled_at <= now
        """
        now = datetime.utcnow()

        query = select(Post).where(
            and_(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_at <= now,
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def publish_post(self, post: Post) -> dict[str, Any]:
        """
        Publish a post to all its target platforms.

        Delegates to PostPublisher for actual publishing logic.

        Args:
            post: The Post instance to publish

        Returns:
            Dictionary mapping platform post IDs to results
        """
        return await self._publisher.publish_post(post)

    async def schedule_post(
        self,
        user_id: str,
        content: str,
        platforms: list[Platform],
        scheduled_at: datetime,
        media_urls: list[str] | None = None,
        hashtags: list[str] | None = None,
        platform_content: dict[Platform, str] | None = None,
    ) -> Post:
        """
        Create and schedule a new post.

        Args:
            user_id: The user's ID
            content: Post content/caption
            platforms: List of target platforms
            scheduled_at: When to publish the post
            media_urls: Optional list of media URLs
            hashtags: Optional list of hashtags
            platform_content: Optional per-platform content overrides

        Returns:
            The created Post instance

        Raises:
            ValueError: If no connected accounts for specified platforms
        """
        # Get user's social accounts for the target platforms
        accounts_query = select(SocialAccount).where(
            and_(
                SocialAccount.user_id == user_id,
                SocialAccount.platform.in_(platforms),
                SocialAccount.is_active == True,
            )
        )
        result = await self.db.execute(accounts_query)
        accounts = {acc.platform: acc for acc in result.scalars().all()}

        if not accounts:
            raise ValueError("No connected accounts for the specified platforms")

        # Create the master post
        post = Post(
            id=str(uuid.uuid4()),
            user_id=user_id,
            content=content,
            media_urls=media_urls,
            hashtags=hashtags,
            scheduled_at=scheduled_at,
            status=PostStatus.SCHEDULED,
        )
        self.db.add(post)

        # Create platform-specific entries
        for platform in platforms:
            if platform not in accounts:
                continue

            account = accounts[platform]
            platform_specific_content = (
                platform_content.get(platform) if platform_content else None
            )

            post_platform = PostPlatform(
                id=str(uuid.uuid4()),
                post_id=post.id,
                social_account_id=account.id,
                content=platform_specific_content,
                hashtags=hashtags,
                status=PostStatus.SCHEDULED,
            )
            self.db.add(post_platform)

        await self.db.commit()
        await self.db.refresh(post)
        return post

    def get_smart_slots(
        self,
        platform: Platform | None = None,
        timezone: str = "UTC",
    ) -> list[dict] | dict:
        """
        Get suggested best times to post based on general engagement data.

        Args:
            platform: Optional specific platform (returns all if None)
            timezone: User's timezone (not yet implemented)

        Returns:
            List of time slots for specific platform, or dict of all platforms
        """
        # These are general best practices - in production, personalize based on user data
        general_best_times = {
            Platform.INSTAGRAM: [
                {"day": "Monday", "times": ["11:00", "14:00", "19:00"]},
                {"day": "Tuesday", "times": ["10:00", "14:00", "19:00"]},
                {"day": "Wednesday", "times": ["11:00", "15:00", "19:00"]},
                {"day": "Thursday", "times": ["10:00", "14:00", "19:00"]},
                {"day": "Friday", "times": ["10:00", "14:00", "17:00"]},
                {"day": "Saturday", "times": ["09:00", "11:00", "19:00"]},
                {"day": "Sunday", "times": ["10:00", "14:00", "19:00"]},
            ],
            Platform.FACEBOOK: [
                {"day": "Monday", "times": ["09:00", "13:00", "16:00"]},
                {"day": "Tuesday", "times": ["09:00", "13:00", "16:00"]},
                {"day": "Wednesday", "times": ["09:00", "13:00", "15:00"]},
                {"day": "Thursday", "times": ["09:00", "12:00", "15:00"]},
                {"day": "Friday", "times": ["09:00", "11:00", "14:00"]},
                {"day": "Saturday", "times": ["09:00", "12:00", "15:00"]},
                {"day": "Sunday", "times": ["09:00", "12:00", "15:00"]},
            ],
            Platform.LINKEDIN: [
                {"day": "Tuesday", "times": ["08:00", "10:00", "12:00"]},
                {"day": "Wednesday", "times": ["08:00", "10:00", "12:00"]},
                {"day": "Thursday", "times": ["08:00", "10:00", "14:00"]},
            ],
            Platform.BLUESKY: [
                {"day": "Monday", "times": ["09:00", "12:00", "18:00"]},
                {"day": "Tuesday", "times": ["09:00", "12:00", "18:00"]},
                {"day": "Wednesday", "times": ["09:00", "12:00", "18:00"]},
                {"day": "Thursday", "times": ["09:00", "12:00", "18:00"]},
                {"day": "Friday", "times": ["09:00", "12:00", "17:00"]},
            ],
            Platform.THREADS: [
                {"day": "Monday", "times": ["10:00", "13:00", "19:00"]},
                {"day": "Tuesday", "times": ["10:00", "13:00", "19:00"]},
                {"day": "Wednesday", "times": ["10:00", "13:00", "19:00"]},
                {"day": "Thursday", "times": ["10:00", "13:00", "19:00"]},
                {"day": "Friday", "times": ["10:00", "13:00", "17:00"]},
                {"day": "Saturday", "times": ["10:00", "12:00", "19:00"]},
                {"day": "Sunday", "times": ["10:00", "12:00", "19:00"]},
            ],
            Platform.TIKTOK: [
                {"day": "Monday", "times": ["12:00", "15:00", "19:00"]},
                {"day": "Tuesday", "times": ["09:00", "12:00", "19:00"]},
                {"day": "Wednesday", "times": ["12:00", "15:00", "19:00"]},
                {"day": "Thursday", "times": ["12:00", "15:00", "21:00"]},
                {"day": "Friday", "times": ["15:00", "17:00", "21:00"]},
                {"day": "Saturday", "times": ["11:00", "19:00", "21:00"]},
                {"day": "Sunday", "times": ["11:00", "15:00", "19:00"]},
            ],
            Platform.X: [
                {"day": "Monday", "times": ["08:00", "12:00", "17:00"]},
                {"day": "Tuesday", "times": ["08:00", "12:00", "17:00"]},
                {"day": "Wednesday", "times": ["08:00", "12:00", "17:00"]},
                {"day": "Thursday", "times": ["08:00", "12:00", "17:00"]},
                {"day": "Friday", "times": ["08:00", "12:00", "16:00"]},
                {"day": "Saturday", "times": ["09:00", "12:00", "15:00"]},
                {"day": "Sunday", "times": ["09:00", "12:00", "15:00"]},
            ],
        }

        if platform:
            return general_best_times.get(platform, [])

        # Return all platforms
        return {p.value: times for p, times in general_best_times.items()}
