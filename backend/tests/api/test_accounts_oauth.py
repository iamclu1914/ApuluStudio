"""Integration tests for OAuth state handling on accounts routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.main import app
from app.models.oauth_state import OAuthState
from app.models.social_account import Platform, SocialAccount
from app.models.user import User


@pytest_asyncio.fixture
async def authed_client(
    async_client: AsyncClient,
    async_session: AsyncSession,
):
    """Provide an API client with an overridden authenticated user."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"oauth-{uuid.uuid4()}@example.com",
        name="OAuth Tester",
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()

    async def override_current_active_user() -> User:
        return user

    app.dependency_overrides[get_current_active_user] = override_current_active_user

    try:
        yield async_client, async_session, user
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


class TestOAuthStateStorage:
    """Tests for OAuth state creation and callback consumption."""

    @pytest.mark.integration
    async def test_connect_facebook_stores_user_bound_oauth_state(self, authed_client):
        """OAuth start should persist state with platform + user binding."""
        async_client, async_session, user = authed_client

        response = await async_client.get("/api/accounts/connect/facebook")

        assert response.status_code == 200
        payload = response.json()
        assert "state" in payload
        assert "auth_url" in payload

        state = payload["state"]
        result = await async_session.execute(
            select(OAuthState).where(OAuthState.state_token == state)
        )
        oauth_state = result.scalar_one_or_none()

        assert oauth_state is not None
        assert oauth_state.user_id == user.id
        assert oauth_state.platform == Platform.FACEBOOK.value
        assert oauth_state.expires_at > datetime.utcnow()

    @pytest.mark.integration
    async def test_meta_callback_rejects_invalid_state(self, authed_client):
        """Callback should reject unknown or consumed OAuth state tokens."""
        async_client, _, _ = authed_client

        response = await async_client.get(
            "/api/accounts/callback/meta",
            params={"code": "dummy-code", "state": "invalid-state-token"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid OAuth state"

    @pytest.mark.integration
    async def test_meta_callback_uses_state_user_and_consumes_state(self, authed_client):
        """Meta callback should create the account for the state user and consume state."""
        async_client, async_session, user = authed_client

        start_response = await async_client.get("/api/accounts/connect/facebook")
        assert start_response.status_code == 200
        state = start_response.json()["state"]

        short_token_response = MagicMock()
        short_token_response.json.return_value = {"access_token": "short-token"}

        long_token_response = MagicMock()
        long_token_response.json.return_value = {"access_token": "long-lived-token"}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            side_effect=[short_token_response, long_token_response]
        )

        profile = {
            "id": "fb-user-123",
            "username": "fbtester",
            "display_name": "FB Tester",
            "avatar_url": "https://example.com/avatar.png",
            "followers_count": 123,
            "following_count": 45,
        }

        with patch("httpx.AsyncClient") as mock_async_client, patch(
            "app.api.routes.accounts.MetaService.get_profile",
            new=AsyncMock(return_value=profile),
        ):
            mock_async_client.return_value.__aenter__.return_value = mock_http_client

            callback_response = await async_client.get(
                "/api/accounts/callback/meta",
                params={"code": "valid-code", "state": state},
            )

        assert callback_response.status_code == 200
        callback_payload = callback_response.json()
        assert callback_payload["success"] is True

        account_result = await async_session.execute(
            select(SocialAccount).where(
                and_(
                    SocialAccount.user_id == user.id,
                    SocialAccount.platform == Platform.FACEBOOK,
                )
            )
        )
        account = account_result.scalar_one_or_none()

        assert account is not None
        assert account.platform_user_id == profile["id"]
        assert account.access_token == "long-lived-token"

        state_result = await async_session.execute(
            select(OAuthState).where(OAuthState.state_token == state)
        )
        assert state_result.scalar_one_or_none() is None
