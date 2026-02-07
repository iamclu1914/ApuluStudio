from datetime import datetime, timedelta
from typing import Annotated
import uuid
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.models.social_account import SocialAccount, Platform
from app.models.oauth_state import OAuthState
from app.schemas.social_account import (
    SocialAccountResponse,
    OAuthStartResponse,
    ConnectionStatus,
)
from app.services.platforms.bluesky import BlueskyService
from app.services.platforms.meta import MetaService
from app.services.platforms.linkedin import LinkedInService
from app.services.platforms.late import LateService
from app.services.late_sync import sync_late_accounts_for_user
from app.api.deps import CurrentActiveUser

router = APIRouter()

settings = get_settings()

async def _cleanup_expired_oauth_states(db: AsyncSession) -> None:
    """Delete expired OAuth states to keep the table small."""
    await db.execute(
        delete(OAuthState).where(OAuthState.expires_at < datetime.utcnow())
    )


async def _create_oauth_state(
    db: AsyncSession,
    user_id: str,
    platform: Platform,
) -> str:
    """Persist a one-time OAuth state token bound to user + platform."""
    await _cleanup_expired_oauth_states(db)

    state = secrets.token_urlsafe(32)
    db.add(
        OAuthState(
            state_token=state,
            platform=platform.value,
            user_id=user_id,
            expires_at=OAuthState.create_expiration(),
        )
    )
    await db.commit()
    return state


async def _consume_oauth_state(
    db: AsyncSession,
    state: str,
) -> OAuthState | None:
    """
    Fetch and invalidate an OAuth state token.

    State tokens are single-use to prevent replay attacks.
    """
    result = await db.execute(
        select(OAuthState).where(OAuthState.state_token == state)
    )
    oauth_state = result.scalar_one_or_none()
    if oauth_state is None:
        return None

    is_expired = oauth_state.is_expired
    await db.delete(oauth_state)
    await db.commit()

    if is_expired:
        return None

    return oauth_state


@router.get("", response_model=list[SocialAccountResponse])
async def list_accounts(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all connected social accounts."""
    query = (
        select(SocialAccount)
        .where(SocialAccount.user_id == current_user.id)
        .order_by(SocialAccount.created_at.desc())
    )
    result = await db.execute(query)
    accounts = list(result.scalars().all())
    return accounts


@router.get("/status")
async def get_connection_status(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConnectionStatus]:
    """Get connection status for all platforms."""
    query = select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    result = await db.execute(query)
    accounts = {acc.platform: acc for acc in result.scalars().all()}

    statuses = []
    for platform in Platform:
        account = accounts.get(platform)
        requires_reconnect = False

        if account and account.token_expires_at:
            requires_reconnect = account.token_expires_at < datetime.utcnow()

        statuses.append(ConnectionStatus(
            platform=platform.value.lower(),  # Lowercase for frontend compatibility
            connected=account is not None and account.is_active,
            account=account if account else None,
            requires_reconnect=requires_reconnect,
        ))

    return statuses


# LATE API Integration Routes (must be before /{account_id} to avoid route conflicts)

@router.post("/sync/late")
async def sync_late_accounts(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Sync LATE-connected accounts into Apulu.

    Fetches all accounts from LATE API and creates/updates corresponding
    social accounts in the database.
    """
    if not settings.late_api_key:
        raise HTTPException(
            status_code=400,
            detail="LATE API key not configured. Add LATE_API_KEY to your .env file."
        )

    try:
        result = await sync_late_accounts_for_user(
            db=db,
            user_id=current_user.id,
            api_key=settings.late_api_key,
        )
        return {
            "success": True,
            "synced": result["synced"],
            "errors": result["errors"] if result["errors"] else None,
            "message": result["message"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync LATE accounts: {str(e)}")


@router.get("/late/profiles")
async def get_late_profiles():
    """
    Get accounts directly from LATE API (without syncing to database).
    Useful for checking what's connected in LATE.
    """
    if not settings.late_api_key:
        raise HTTPException(
            status_code=400,
            detail="LATE API key not configured"
        )

    try:
        late_service = LateService(Platform.INSTAGRAM)
        accounts = await late_service.get_accounts(settings.late_api_key)
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dynamic routes (must be after specific routes)

@router.get("/{account_id}", response_model=SocialAccountResponse)
async def get_account(
    account_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a single connected account."""
    query = select(SocialAccount).where(
        and_(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.patch("/{account_id}")
async def update_account_preferences(
    account_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    preferred_aspect_ratio: str = None,
):
    """
    Update account preferences.

    Args:
        preferred_aspect_ratio: One of: original, 1:1, 4:5, 16:9, 9:16
    """
    query = select(SocialAccount).where(
        and_(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if preferred_aspect_ratio:
        valid_ratios = ["original", "1:1", "4:5", "16:9", "9:16"]
        if preferred_aspect_ratio not in valid_ratios:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid aspect ratio. Choose from: {', '.join(valid_ratios)}"
            )
        account.preferred_aspect_ratio = preferred_aspect_ratio

    await db.commit()

    return {
        "success": True,
        "account_id": account.id,
        "preferred_aspect_ratio": account.preferred_aspect_ratio,
    }


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Disconnect a social account."""
    query = select(SocialAccount).where(
        and_(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await db.delete(account)
    await db.commit()

    return {"success": True}


# OAuth flows


@router.get("/connect/bluesky")
async def connect_bluesky_start():
    """Start Bluesky connection - returns instructions."""
    return {
        "message": "Bluesky uses App Passwords instead of OAuth",
        "instructions": [
            "1. Go to bsky.app/settings/app-passwords",
            "2. Create a new App Password",
            "3. Use POST /accounts/connect/bluesky with your handle and app_password",
        ],
    }


@router.post("/connect/bluesky")
async def connect_bluesky(
    handle: str,
    app_password: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Connect Bluesky account using App Password."""
    service = BlueskyService()

    # Verify credentials and get profile
    try:
        profile = await service.get_profile(
            access_token=app_password,
            handle=handle,
        )

        if not profile.get("id"):
            raise HTTPException(status_code=401, detail="Invalid Bluesky credentials")

        # Check if already connected
        existing_query = select(SocialAccount).where(
            and_(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == Platform.BLUESKY,
            )
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing
            existing.access_token = app_password
            existing.username = profile["username"]
            existing.display_name = profile.get("display_name")
            existing.avatar_url = profile.get("avatar_url")
            existing.platform_user_id = profile["id"]
            existing.follower_count = profile.get("followers_count", 0)
            existing.following_count = profile.get("following_count", 0)
            existing.last_synced = datetime.utcnow()
            existing.is_active = True
            await db.commit()
            return {"success": True, "account_id": existing.id}

        # Create new
        account = SocialAccount(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            platform=Platform.BLUESKY,
            platform_user_id=profile["id"],
            username=profile["username"],
            display_name=profile.get("display_name"),
            avatar_url=profile.get("avatar_url"),
            access_token=app_password,
            follower_count=profile.get("followers_count", 0),
            following_count=profile.get("following_count", 0),
            last_synced=datetime.utcnow(),
        )
        db.add(account)
        await db.commit()

        return {"success": True, "account_id": account.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connect/instagram")
async def connect_instagram_start(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OAuthStartResponse:
    """Start Instagram OAuth flow."""
    state = await _create_oauth_state(db, current_user.id, Platform.INSTAGRAM)

    # Instagram uses Facebook Login
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={settings.meta_app_id}"
        f"&redirect_uri={settings.backend_url}/api/accounts/callback/meta"
        f"&state={state}"
        f"&scope=instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
    )

    return OAuthStartResponse(auth_url=auth_url, state=state)


@router.get("/connect/facebook")
async def connect_facebook_start(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OAuthStartResponse:
    """Start Facebook OAuth flow."""
    state = await _create_oauth_state(db, current_user.id, Platform.FACEBOOK)

    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={settings.meta_app_id}"
        f"&redirect_uri={settings.backend_url}/api/accounts/callback/meta"
        f"&state={state}"
        f"&scope=pages_show_list,pages_read_engagement,pages_manage_posts"
    )

    return OAuthStartResponse(auth_url=auth_url, state=state)


@router.get("/connect/linkedin")
async def connect_linkedin_start(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OAuthStartResponse:
    """Start LinkedIn OAuth flow."""
    state = await _create_oauth_state(db, current_user.id, Platform.LINKEDIN)

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={settings.linkedin_client_id}"
        f"&redirect_uri={settings.backend_url}/api/accounts/callback/linkedin"
        f"&state={state}"
        f"&scope=openid%20profile%20email%20w_member_social"
    )

    return OAuthStartResponse(auth_url=auth_url, state=state)


@router.get("/callback/meta")
async def meta_oauth_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle Meta (Instagram/Facebook) OAuth callback."""
    import httpx

    # Verify state
    state_data = await _consume_oauth_state(db, state)
    if state_data is None:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        platform = Platform(state_data.platform)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state platform") from exc

    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.get(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                params={
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "redirect_uri": f"{settings.backend_url}/api/accounts/callback/meta",
                    "code": code,
                },
            )
            token_data = token_response.json()

            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="Failed to get access token")

            access_token = token_data["access_token"]

            # Exchange for long-lived token
            long_token_response = await client.get(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "fb_exchange_token": access_token,
                },
            )
            long_token_data = long_token_response.json()
            long_lived_token = long_token_data.get("access_token", access_token)

            # Get profile
            service = MetaService(platform)
            profile = await service.get_profile(access_token=long_lived_token)

            if not profile.get("id"):
                raise HTTPException(status_code=400, detail="Failed to get profile")

            # For Instagram, we need to get the IG user ID from connected pages
            ig_user_id = None
            page_id = None

            if platform == Platform.INSTAGRAM:
                # Get pages and find connected Instagram account
                pages_response = await client.get(
                    "https://graph.facebook.com/v19.0/me/accounts",
                    params={"access_token": long_lived_token},
                )
                pages_data = pages_response.json()

                for page in pages_data.get("data", []):
                    page_id = page["id"]
                    page_token = page["access_token"]

                    # Get Instagram account connected to this page
                    ig_response = await client.get(
                        f"https://graph.facebook.com/v19.0/{page_id}",
                        params={
                            "fields": "instagram_business_account",
                            "access_token": page_token,
                        },
                    )
                    ig_data = ig_response.json()

                    if "instagram_business_account" in ig_data:
                        ig_user_id = ig_data["instagram_business_account"]["id"]
                        break

                if not ig_user_id:
                    raise HTTPException(
                        status_code=400,
                        detail="No Instagram Business account found. Connect an Instagram account to a Facebook Page first.",
                    )

            # Save account using user_id bound to the OAuth state.
            account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=state_data.user_id,
                platform=platform,
                platform_user_id=ig_user_id or profile["id"],
                username=profile.get("username", profile.get("display_name", "")),
                display_name=profile.get("display_name"),
                avatar_url=profile.get("avatar_url"),
                access_token=long_lived_token,
                page_id=page_id,
                follower_count=profile.get("followers_count", 0),
                following_count=profile.get("following_count", 0),
                last_synced=datetime.utcnow(),
            )
            db.add(account)
            await db.commit()

            # Redirect to frontend
            return {"success": True, "redirect": f"{settings.frontend_url}/settings?connected={platform.value}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback/linkedin")
async def linkedin_oauth_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle LinkedIn OAuth callback."""
    import httpx

    # Verify state
    state_data = await _consume_oauth_state(db, state)
    if state_data is None:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": f"{settings.backend_url}/api/accounts/callback/linkedin",
                    "client_id": settings.linkedin_client_id,
                    "client_secret": settings.linkedin_client_secret,
                },
            )
            token_data = token_response.json()

            if "access_token" not in token_data:
                raise HTTPException(status_code=400, detail="Failed to get access token")

            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)

            # Get profile
            service = LinkedInService()
            profile = await service.get_profile(access_token=access_token)

            if not profile.get("id"):
                raise HTTPException(status_code=400, detail="Failed to get profile")

            # Save account using user_id bound to the OAuth state.
            account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=state_data.user_id,
                platform=Platform.LINKEDIN,
                platform_user_id=profile["id"],
                username=profile.get("username", profile.get("email", "").split("@")[0]),
                display_name=profile.get("display_name"),
                avatar_url=profile.get("avatar_url"),
                access_token=access_token,
                refresh_token=token_data.get("refresh_token"),
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                last_synced=datetime.utcnow(),
            )
            db.add(account)
            await db.commit()

            return {"success": True, "redirect": f"{settings.frontend_url}/settings?connected=linkedin"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/sync")
async def sync_account(
    account_id: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Sync account data (followers, etc.)."""
    query = select(SocialAccount).where(
        and_(
            SocialAccount.id == account_id,
            SocialAccount.user_id == current_user.id,
        )
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get service and fetch profile
    services = {
        Platform.BLUESKY: BlueskyService(),
        Platform.INSTAGRAM: MetaService(Platform.INSTAGRAM),
        Platform.FACEBOOK: MetaService(Platform.FACEBOOK),
        Platform.LINKEDIN: LinkedInService(),
    }

    service = services.get(account.platform)
    if not service:
        raise HTTPException(status_code=400, detail="Platform not supported")

    try:
        profile = await service.get_profile(
            access_token=account.access_token,
            handle=account.username,
            user_id=account.platform_user_id,
        )

        account.follower_count = profile.get("followers_count", account.follower_count)
        account.following_count = profile.get("following_count", account.following_count)
        account.avatar_url = profile.get("avatar_url", account.avatar_url)
        account.last_synced = datetime.utcnow()

        await db.commit()

        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
