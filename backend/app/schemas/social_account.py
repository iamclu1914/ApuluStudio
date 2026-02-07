from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.social_account import Platform


class SocialAccountCreate(BaseModel):
    """Schema for creating a social account (internal use)."""
    platform: Platform
    platform_user_id: str
    username: str
    display_name: str | None = None
    profile_url: str | None = None
    avatar_url: str | None = None
    access_token: str
    refresh_token: str | None = None
    token_expires_at: datetime | None = None
    page_id: str | None = None


class SocialAccountResponse(BaseModel):
    """Schema for social account response."""
    id: str
    platform: str  # Serialize as lowercase string for frontend compatibility
    username: str
    display_name: str | None
    profile_url: str | None
    avatar_url: str | None
    follower_count: int
    following_count: int
    is_active: bool
    last_synced: datetime | None
    created_at: datetime
    preferred_aspect_ratio: str | None = "original"

    model_config = ConfigDict(from_attributes=True)

    @field_validator('platform', mode='before')
    @classmethod
    def convert_platform_to_lowercase(cls, v):
        """Convert Platform enum to lowercase string."""
        if hasattr(v, 'value'):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator('preferred_aspect_ratio', mode='before')
    @classmethod
    def convert_aspect_ratio(cls, v):
        """Convert AspectRatioPreference enum to string."""
        if hasattr(v, 'value'):
            return v.value
        return v or "original"


class OAuthCallback(BaseModel):
    """OAuth callback data."""
    code: str
    state: str | None = None


class OAuthStartResponse(BaseModel):
    """Response when starting OAuth flow."""
    auth_url: str
    state: str


class ConnectionStatus(BaseModel):
    """Status of platform connections."""
    platform: str  # Lowercase string for frontend compatibility
    connected: bool
    account: SocialAccountResponse | None = None
    requires_reconnect: bool = False

    model_config = ConfigDict(from_attributes=True)
