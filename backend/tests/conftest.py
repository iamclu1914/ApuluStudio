"""
Shared pytest fixtures for Apulu Suite backend tests.

This module provides:
- Async database session fixtures
- Test client fixtures
- Sample data factories
- Mock fixtures for external services
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.post import Post, PostPlatform, PostStatus
from app.models.social_account import SocialAccount
from app.models.user import User
from app.schemas.post import PostCreate

# Test database URL (in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def async_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# =============================================================================
# Sample Data Factories
# =============================================================================

@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user creation data."""
    return {
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest_asyncio.fixture
async def sample_user(async_session: AsyncSession, sample_user_data) -> User:
    """Create a sample user in the database."""
    user = User(**sample_user_data)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
def sample_post_data() -> dict[str, Any]:
    """Sample post creation data."""
    return {
        "content": "Test post content for social media #testing",
        "platforms": ["instagram", "twitter"],
        "media_urls": [],
    }


@pytest.fixture
def sample_post_create(sample_post_data) -> PostCreate:
    """Sample PostCreate schema instance."""
    return PostCreate(**sample_post_data)


@pytest_asyncio.fixture
async def sample_post(
    async_session: AsyncSession,
    sample_user: User,
    sample_post_data
) -> Post:
    """Create a sample post in the database."""
    post = Post(
        content=sample_post_data["content"],
        user_id=sample_user.id,
        status=PostStatus.DRAFT,
    )
    async_session.add(post)
    await async_session.commit()
    await async_session.refresh(post)
    return post


@pytest.fixture
def sample_social_account_data() -> dict[str, Any]:
    """Sample social account data."""
    return {
        "platform": "instagram",
        "platform_user_id": "123456789",
        "username": "testuser",
        "access_token": "test_access_token",
    }


@pytest_asyncio.fixture
async def sample_social_account(
    async_session: AsyncSession,
    sample_user: User,
    sample_social_account_data
) -> SocialAccount:
    """Create a sample social account in the database."""
    account = SocialAccount(
        **sample_social_account_data,
        user_id=sample_user.id,
    )
    async_session.add(account)
    await async_session.commit()
    await async_session.refresh(account)
    return account


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_platform_service() -> MagicMock:
    """Mock platform service for testing without external API calls."""
    mock = MagicMock()
    mock.post_text = AsyncMock(return_value={"id": "mock_post_123", "success": True})
    mock.post_image = AsyncMock(return_value={"id": "mock_post_456", "success": True})
    mock.post_video = AsyncMock(return_value={"id": "mock_post_789", "success": True})
    mock.get_engagement = AsyncMock(return_value={
        "likes": 100,
        "comments": 25,
        "shares": 10,
    })
    return mock


@pytest.fixture
def mock_ai_service() -> MagicMock:
    """Mock AI service for testing content generation."""
    mock = MagicMock()
    mock.generate_caption = AsyncMock(return_value="AI generated caption #trending")
    mock.suggest_hashtags = AsyncMock(return_value=["#social", "#media", "#marketing"])
    mock.optimize_timing = AsyncMock(return_value="2024-12-15T10:00:00Z")
    return mock


@pytest.fixture
def mock_storage_service() -> MagicMock:
    """Mock storage service for testing media uploads."""
    mock = MagicMock()
    mock.upload_file = AsyncMock(return_value="https://storage.example.com/media/test.jpg")
    mock.delete_file = AsyncMock(return_value=True)
    mock.get_signed_url = AsyncMock(return_value="https://storage.example.com/signed/test.jpg")
    return mock
