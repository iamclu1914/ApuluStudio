"""Background scheduler for syncing LATE-connected accounts."""

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.constants import TEMP_USER_ID
from app.core.database import AsyncSessionLocal
from app.core.logger import logger
from app.models.user import User
from app.services.late_sync import sync_late_accounts_for_user


class LateSyncScheduler:
    """Background task that periodically syncs LATE accounts."""

    def __init__(self, sync_interval: int = 300):
        self.sync_interval = sync_interval
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        if self._running:
            logger.warning("LATE sync scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("LATE sync scheduler started", sync_interval=self.sync_interval)

    async def stop(self):
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("LATE sync scheduler stopped")

    async def _run(self):
        while self._running:
            try:
                await self._sync_once()
            except Exception as e:
                logger.error("Error in LATE sync scheduler", error=str(e), exc_info=True)

            await asyncio.sleep(self.sync_interval)

    async def _sync_once(self):
        settings = get_settings()

        if not settings.late_api_key:
            logger.info("Skipping LATE sync - API key not configured")
            return

        user_id = settings.late_sync_user_id or (TEMP_USER_ID if settings.debug else None)
        if not user_id:
            logger.info("Skipping LATE sync - no sync user configured")
            return

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User.id).where(User.id == user_id))
            if result.scalar_one_or_none() is None:
                logger.warning("Skipping LATE sync - user not found", user_id=user_id)
                return

            sync_result = await sync_late_accounts_for_user(
                db=db,
                user_id=user_id,
                api_key=settings.late_api_key,
            )

        logger.info(
            "LATE sync completed",
            synced=len(sync_result["synced"]),
            errors=len(sync_result["errors"] or []),
        )

    @property
    def is_running(self) -> bool:
        return self._running


_settings = get_settings()
late_sync_scheduler = LateSyncScheduler(sync_interval=_settings.late_sync_interval_seconds)


async def start_late_sync_scheduler():
    await late_sync_scheduler.start()


async def stop_late_sync_scheduler():
    await late_sync_scheduler.stop()
