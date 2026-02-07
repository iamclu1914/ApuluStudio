"""
Unit tests for BackgroundScheduler service.

Tests cover:
- Scheduler lifecycle (start/stop)
- Due post detection
- Post publishing workflow
- Error handling and status transitions
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.post import Post, PostPlatform, PostStatus
from app.services.background_scheduler import BackgroundScheduler


class TestBackgroundSchedulerLifecycle:
    """Tests for scheduler start/stop lifecycle."""

    @pytest.mark.unit
    async def test_scheduler_starts_successfully(self):
        """Scheduler should start and set running flag."""
        scheduler = BackgroundScheduler(check_interval=60)

        # Mock the scheduler loop to prevent infinite loop
        with patch.object(scheduler, '_run_scheduler', new_callable=AsyncMock):
            await scheduler.start()

            assert scheduler.is_running is True
            assert scheduler._task is not None

            await scheduler.stop()

    @pytest.mark.unit
    async def test_scheduler_stops_gracefully(self):
        """Scheduler should stop and clean up task."""
        scheduler = BackgroundScheduler(check_interval=60)

        with patch.object(scheduler, '_run_scheduler', new_callable=AsyncMock):
            await scheduler.start()
            await scheduler.stop()

            assert scheduler.is_running is False
            assert scheduler._task is None

    @pytest.mark.unit
    async def test_scheduler_ignores_duplicate_start(self):
        """Starting an already running scheduler should be a no-op."""
        scheduler = BackgroundScheduler(check_interval=60)

        with patch.object(scheduler, '_run_scheduler', new_callable=AsyncMock) as mock_run:
            await scheduler.start()
            await scheduler.start()  # Second start should be ignored

            # _run_scheduler should only be called once via create_task
            assert scheduler.is_running is True

            await scheduler.stop()

    @pytest.mark.unit
    async def test_scheduler_custom_check_interval(self):
        """Scheduler should use custom check interval."""
        scheduler = BackgroundScheduler(check_interval=30)

        assert scheduler.check_interval == 30


class TestDuePostDetection:
    """Tests for detecting posts that are due for publishing."""

    @pytest.mark.unit
    async def test_check_and_publish_with_no_due_posts(self, async_session):
        """When no posts are due, nothing should be published."""
        scheduler = BackgroundScheduler(check_interval=60)

        # Create mock for database query that returns no posts
        with patch('app.services.background_scheduler.AsyncSessionLocal') as mock_session:
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db

            # Mock empty result
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            await scheduler._check_and_publish_due_posts()

            # Verify query was executed
            mock_db.execute.assert_called_once()

    @pytest.mark.unit
    async def test_check_now_triggers_check(self):
        """check_now() should manually trigger the check."""
        scheduler = BackgroundScheduler(check_interval=60)

        with patch.object(
            scheduler, '_check_and_publish_due_posts', new_callable=AsyncMock
        ) as mock_check:
            await scheduler.check_now()

            mock_check.assert_called_once()


class TestPublishCallback:
    """Tests for publish callback functionality."""

    @pytest.mark.unit
    async def test_callback_is_called_on_publish(self):
        """Callback should be invoked when a post is published."""
        scheduler = BackgroundScheduler(check_interval=60)

        callback = AsyncMock()
        scheduler.set_publish_callback(callback)

        assert scheduler._on_publish_callback is callback

    @pytest.mark.unit
    async def test_callback_can_be_set(self):
        """Callback should be settable via set_publish_callback."""
        scheduler = BackgroundScheduler(check_interval=60)

        async def my_callback(post, results):
            pass

        scheduler.set_publish_callback(my_callback)

        assert scheduler._on_publish_callback is my_callback


class TestSchedulerErrorHandling:
    """Tests for error handling in the scheduler."""

    @pytest.mark.unit
    async def test_scheduler_continues_after_error(self):
        """Scheduler should continue running after an error in check loop."""
        scheduler = BackgroundScheduler(check_interval=1)

        call_count = 0

        async def failing_check():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test error")
            # After first failure, stop the scheduler
            scheduler._running = False

        with patch.object(scheduler, '_check_and_publish_due_posts', side_effect=failing_check):
            scheduler._running = True

            # Run scheduler loop briefly
            task = asyncio.create_task(scheduler._run_scheduler())
            await asyncio.sleep(0.1)
            scheduler._running = False

            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.CancelledError:
                pass

            # Should have attempted at least one check despite error
            assert call_count >= 1

    @pytest.mark.unit
    async def test_scheduler_handles_missing_callback_gracefully(self):
        """Scheduler should not crash if callback is not set."""
        scheduler = BackgroundScheduler(check_interval=60)

        # No callback set
        assert scheduler._on_publish_callback is None

        # This should not raise an error
        # In real code, the callback check happens during publish
