"""Sync LATE-connected accounts into Apulu."""

from datetime import datetime
import uuid
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.social_account import SocialAccount, Platform
from app.services.platforms.late import LateService


async def sync_late_accounts_for_user(
    db: AsyncSession,
    user_id: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Sync LATE-connected accounts into Apulu for a specific user.

    Returns a dict with keys: synced, errors, message.
    """
    settings = get_settings()
    resolved_api_key = api_key or settings.late_api_key

    if not resolved_api_key:
        raise ValueError("LATE API key not configured")

    # Platform mapping from LATE to our Platform enum
    late_to_platform = {
        "instagram": Platform.INSTAGRAM,
        "threads": Platform.THREADS,
        "tiktok": Platform.TIKTOK,
        "x": Platform.X,
        "twitter": Platform.X,  # LATE uses "twitter"
    }

    synced: list[dict[str, Any]] = []
    errors: list[str] = []

    # Use any LATE service to fetch accounts (they all use the same API)
    late_service = LateService(Platform.INSTAGRAM)
    accounts = await late_service.get_accounts(resolved_api_key)

    for account in accounts:
        late_platform = account.get("platform", "").lower()
        platform = late_to_platform.get(late_platform)

        if not platform:
            errors.append(f"Unknown platform: {late_platform}")
            continue

        # Skip inactive accounts
        if not account.get("isActive", True):
            continue

        late_account_id = account.get("_id")
        username = account.get("username") or account.get("handle") or ""
        display_name = account.get("displayName") or account.get("display_name") or username
        avatar_url = account.get("profilePicture") or account.get("avatar") or account.get("profile_picture")

        # Extract follower count from LATE metadata
        metadata = account.get("metadata", {})
        profile_data = metadata.get("profileData", {})
        follower_count = profile_data.get("followersCount", 0)
        following_count = profile_data.get("followingCount", 0)

        # Skip avatar_url if too long (DB column is VARCHAR 500)
        # Truncating would break the URL, so we set it to None
        if avatar_url and len(avatar_url) > 500:
            avatar_url = None

        # Check if account already exists
        existing_query = select(SocialAccount).where(
            and_(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == platform,
            )
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Update existing account
            existing.platform_user_id = late_account_id
            existing.username = username
            existing.display_name = display_name
            existing.avatar_url = avatar_url
            existing.access_token = LateService.LATE_MANAGED_MARKER
            existing.follower_count = follower_count
            existing.following_count = following_count
            existing.last_synced = datetime.utcnow()
            existing.is_active = True
            synced.append({
                "platform": platform.value,
                "username": username,
                "followers": follower_count,
                "action": "updated",
            })
        else:
            # Create new account
            new_account = SocialAccount(
                id=str(uuid.uuid4()),
                user_id=user_id,
                platform=platform,
                platform_user_id=late_account_id,
                username=username,
                display_name=display_name,
                avatar_url=avatar_url,
                access_token=LateService.LATE_MANAGED_MARKER,
                follower_count=follower_count,
                following_count=following_count,
                last_synced=datetime.utcnow(),
            )
            db.add(new_account)
            synced.append({
                "platform": platform.value,
                "username": username,
                "followers": follower_count,
                "action": "created",
            })

    await db.commit()

    return {
        "synced": synced,
        "errors": errors,
        "message": f"Synced {len(synced)} account(s) from LATE",
    }
