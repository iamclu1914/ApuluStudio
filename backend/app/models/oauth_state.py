"""OAuth state storage for secure OAuth flow handling.

This model stores OAuth state tokens in the database instead of in-memory,
which provides:
- Persistence across server restarts
- Support for multiple server instances (horizontal scaling)
- Automatic expiration and cleanup
- Protection against CSRF attacks
"""
from datetime import datetime, timedelta
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.social_account import Platform


# Default expiration time for OAuth states (15 minutes)
OAUTH_STATE_EXPIRATION_MINUTES = 15


class OAuthState(Base):
    """
    Stores OAuth state tokens for CSRF protection during OAuth flows.

    OAuth state tokens are:
    - Generated when starting an OAuth flow (/connect/{platform})
    - Validated and consumed on callback (/callback/{platform})
    - Automatically expired after 15 minutes
    - Unique per OAuth flow attempt
    """

    __tablename__ = "oauth_states"

    # Primary key is the state token itself (unique, random string)
    state_token: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Platform being connected (for validation on callback)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    # User initiating the OAuth flow (for associating the account on success)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Timestamps for expiration handling
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,  # Index for efficient cleanup queries
    )

    # Optional: Store additional data needed for the callback
    # (e.g., redirect URL, scopes requested)
    additional_data: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Index for efficient cleanup of expired states
    __table_args__ = (
        Index("ix_oauth_states_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<OAuthState {self.platform} user={self.user_id} expires={self.expires_at}>"

    @classmethod
    def create_expiration(cls, minutes: int = OAUTH_STATE_EXPIRATION_MINUTES) -> datetime:
        """Calculate expiration time from now."""
        return datetime.utcnow() + timedelta(minutes=minutes)

    @property
    def is_expired(self) -> bool:
        """Check if this state token has expired."""
        return datetime.utcnow() > self.expires_at
