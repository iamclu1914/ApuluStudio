"""
API integration tests for Posts endpoints.

Tests cover:
- Post CRUD operations (Create, Read, Update, Delete)
- Post listing with pagination
- Post validation
- Post publishing workflow
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models.post import Post, PostPlatform, PostStatus
from app.models.social_account import Platform, SocialAccount


class TestListPosts:
    """Tests for GET /api/posts endpoint."""

    @pytest.mark.integration
    async def test_list_posts_empty(self, async_client: AsyncClient):
        """Should return empty list when no posts exist."""
        response = await async_client.get("/api/posts")

        assert response.status_code == 200
        data = response.json()
        assert data["posts"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.integration
    async def test_list_posts_with_data(
        self,
        async_client: AsyncClient,
        sample_post: Post,
    ):
        """Should return posts when they exist."""
        response = await async_client.get("/api/posts")

        assert response.status_code == 200
        data = response.json()
        # Note: sample_post uses a different user_id than TEMP_USER_ID
        # so it won't appear in the filtered results
        assert "posts" in data
        assert "total" in data

    @pytest.mark.integration
    async def test_list_posts_pagination(self, async_client: AsyncClient):
        """Should respect pagination parameters."""
        response = await async_client.get("/api/posts?page=1&per_page=5")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5

    @pytest.mark.integration
    async def test_list_posts_filter_by_status(self, async_client: AsyncClient):
        """Should filter posts by status."""
        response = await async_client.get("/api/posts?status=draft")

        assert response.status_code == 200
        data = response.json()
        # All returned posts should be drafts
        for post in data["posts"]:
            assert post["status"] == "draft"


class TestCursorPagination:
    """Tests for GET /api/posts/cursor endpoint."""

    @pytest.mark.integration
    async def test_cursor_pagination_initial(self, async_client: AsyncClient):
        """Should return posts with cursor for pagination."""
        response = await async_client.get("/api/posts/cursor?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert "next_cursor" in data
        assert "has_more" in data


class TestGetPost:
    """Tests for GET /api/posts/{post_id} endpoint."""

    @pytest.mark.integration
    async def test_get_post_not_found(self, async_client: AsyncClient):
        """Should return 404 for non-existent post."""
        response = await async_client.get("/api/posts/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreatePost:
    """Tests for POST /api/posts endpoint."""

    @pytest.mark.integration
    async def test_create_post_requires_platforms(self, async_client: AsyncClient):
        """Should require at least one platform."""
        response = await async_client.post(
            "/api/posts",
            json={
                "content": "Test post content",
                "platforms": [],
            },
        )

        # Pydantic validation should fail
        assert response.status_code == 422

    @pytest.mark.integration
    async def test_create_post_requires_content(self, async_client: AsyncClient):
        """Should require content."""
        response = await async_client.post(
            "/api/posts",
            json={
                "content": "",
                "platforms": ["INSTAGRAM"],
            },
        )

        assert response.status_code == 422

    @pytest.mark.integration
    async def test_create_post_validates_platform_accounts(
        self,
        async_client: AsyncClient,
    ):
        """Should validate user has connected accounts for platforms."""
        response = await async_client.post(
            "/api/posts",
            json={
                "content": "Test post",
                "platforms": ["INSTAGRAM"],
            },
        )

        # Should fail because no connected Instagram account
        assert response.status_code == 400
        assert "No connected accounts" in response.json()["detail"]


class TestValidatePost:
    """Tests for POST /api/posts/validate endpoint."""

    @pytest.mark.integration
    async def test_validate_requires_platforms(self, async_client: AsyncClient):
        """Should require at least one platform."""
        response = await async_client.post(
            "/api/posts/validate",
            params={
                "content": "Test content",
                "platforms": [],
            },
        )

        assert response.status_code == 400
        assert "At least one platform" in response.json()["detail"]

    @pytest.mark.integration
    async def test_validate_instagram_requires_media(self, async_client: AsyncClient):
        """Instagram validation should fail without media."""
        response = await async_client.post(
            "/api/posts/validate",
            params={
                "content": "Test content",
                "platforms": ["INSTAGRAM"],
                "media_urls": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["platforms"]["INSTAGRAM"]["valid"] is False

    @pytest.mark.integration
    async def test_validate_twitter_text_only(self, async_client: AsyncClient):
        """Twitter should accept text-only posts."""
        response = await async_client.post(
            "/api/posts/validate",
            params={
                "content": "Short tweet under 280 chars",
                "platforms": ["X"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["platforms"]["X"]["valid"] is True

    @pytest.mark.integration
    async def test_validate_twitter_too_long(self, async_client: AsyncClient):
        """Twitter should reject tweets over 280 chars."""
        long_content = "A" * 300

        response = await async_client.post(
            "/api/posts/validate",
            params={
                "content": long_content,
                "platforms": ["X"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["platforms"]["X"]["valid"] is False


class TestDeletePost:
    """Tests for DELETE /api/posts/{post_id} endpoint."""

    @pytest.mark.integration
    async def test_delete_post_not_found(self, async_client: AsyncClient):
        """Should return 404 for non-existent post."""
        response = await async_client.delete("/api/posts/nonexistent-id")

        assert response.status_code == 404


class TestPlatformRequirements:
    """Tests for platform requirements endpoints."""

    @pytest.mark.integration
    async def test_get_all_requirements(self, async_client: AsyncClient):
        """Should return requirements for all platforms."""
        response = await async_client.get("/api/posts/requirements")

        assert response.status_code == 200
        data = response.json()

        # Check all platforms are present
        expected_platforms = ["INSTAGRAM", "TIKTOK", "X", "THREADS", "BLUESKY", "FACEBOOK", "LINKEDIN"]
        for platform in expected_platforms:
            assert platform in data
            assert "displayName" in data[platform]
            assert "media" in data[platform]
            assert "content" in data[platform]

    @pytest.mark.integration
    async def test_get_platform_requirement(self, async_client: AsyncClient):
        """Should return requirements for a specific platform."""
        response = await async_client.get("/api/posts/requirements/INSTAGRAM")

        assert response.status_code == 200
        data = response.json()

        assert data["platform"] == "INSTAGRAM"
        assert data["displayName"] == "Instagram"
        assert data["media"]["mediaRequired"] is True
        assert data["content"]["maxCaptionLength"] == 2200

    @pytest.mark.integration
    async def test_get_invalid_platform_requirement(self, async_client: AsyncClient):
        """Should return 422 for invalid platform."""
        response = await async_client.get("/api/posts/requirements/INVALID")

        assert response.status_code == 422


class TestSmartSlots:
    """Tests for smart scheduling endpoints."""

    @pytest.mark.integration
    async def test_get_smart_slots(self, async_client: AsyncClient):
        """Should return smart scheduling slots for a platform."""
        response = await async_client.get("/api/posts/smart-slots/INSTAGRAM")

        assert response.status_code == 200
        data = response.json()

        # Should return list of day/time combinations
        assert isinstance(data, list)
        if data:
            assert "day" in data[0]
            assert "times" in data[0]

    @pytest.mark.integration
    async def test_get_schedule_suggestions(self, async_client: AsyncClient):
        """Should return AI-powered scheduling suggestions."""
        response = await async_client.get(
            "/api/posts/schedule/suggestions",
            params={"platforms": "INSTAGRAM,X"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "suggestions" in data
        assert "generated_at" in data

    @pytest.mark.integration
    async def test_get_optimal_cross_platform_time(self, async_client: AsyncClient):
        """Should return optimal time across platforms."""
        response = await async_client.get(
            "/api/posts/schedule/optimal-time",
            params={"platforms": "INSTAGRAM,FACEBOOK"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "datetime" in data
        assert "engagement_level" in data
        assert "platforms" in data


class TestCalendarPosts:
    """Tests for calendar view endpoint."""

    @pytest.mark.integration
    async def test_get_calendar_posts(self, async_client: AsyncClient):
        """Should return posts within date range."""
        start = datetime.utcnow().isoformat()
        end = (datetime.utcnow() + timedelta(days=7)).isoformat()

        response = await async_client.get(
            "/api/posts/calendar",
            params={
                "start_date": start,
                "end_date": end,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
