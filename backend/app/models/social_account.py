from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Integer, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
import logging

from app.core.database import Base
from app.core.encryption import encrypt_token, decrypt_token, EncryptionError, is_encrypted

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import PostPlatform


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for transparent encryption of string fields.

    Values are encrypted before being stored in the database and decrypted
    when retrieved. This provides at-rest encryption for sensitive data
    like OAuth tokens.

    Note: If ENCRYPTION_KEY is not configured, values are stored as plaintext
    with a warning logged. This allows development without encryption setup.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Encrypt value before storing in database."""
        if value is None:
            return None

        try:
            return encrypt_token(value)
        except EncryptionError as e:
            # In development without encryption key, store plaintext with warning
            logger.warning(
                f"Encryption not configured, storing token in plaintext: {e}"
            )
            return value

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Decrypt value when reading from database."""
        if value is None:
            return None

        # Check if value appears to be encrypted
        if not is_encrypted(value):
            # Value is plaintext (pre-migration or encryption disabled)
            logger.debug("Token appears to be plaintext (not encrypted)")
            return value

        try:
            return decrypt_token(value)
        except EncryptionError as e:
            logger.error(f"Failed to decrypt token: {e}")
            # Return None rather than corrupted/encrypted data
            # This will require the user to re-authenticate
            raise


class Platform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    THREADS = "THREADS"
    BLUESKY = "BLUESKY"
    LINKEDIN = "LINKEDIN"
    X = "X"
    TIKTOK = "TIKTOK"

    @classmethod
    def _missing_(cls, value):
        """Allow case-insensitive lookup."""
        if isinstance(value, str):
            upper = value.upper()
            for member in cls:
                if member.value == upper:
                    return member
        return None


class AspectRatioPreference(str, Enum):
    """Preferred aspect ratio for image uploads."""
    ORIGINAL = "original"      # Don't crop, keep original
    SQUARE = "1:1"             # 1080x1080
    PORTRAIT = "4:5"           # 1080x1350 (Instagram best)
    LANDSCAPE = "16:9"         # 1920x1080
    VERTICAL = "9:16"          # 1080x1920 (Stories/Reels/TikTok)

    @classmethod
    def _missing_(cls, value):
        """Allow flexible lookup."""
        if isinstance(value, str):
            # Try exact match first
            for member in cls:
                if member.value == value:
                    return member
            # Try case-insensitive
            lower = value.lower()
            for member in cls:
                if member.value.lower() == lower or member.name.lower() == lower:
                    return member
        return None


class SocialAccount(Base):
    """Connected social media accounts."""

    __tablename__ = "social_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # Platform info
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform, name="platform", create_type=False))
    platform_user_id: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # OAuth tokens (encrypted at rest using Fernet symmetric encryption)
    access_token: Mapped[str] = mapped_column(EncryptedString)
    refresh_token: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Platform-specific data
    page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # FB/IG

    # Media preferences (stored as string for flexibility)
    preferred_aspect_ratio: Mapped[str] = mapped_column(
        String(20),
        default="original",
    )

    # Analytics cache
    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    following_count: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="social_accounts")
    post_platforms: Mapped[list["PostPlatform"]] = relationship(
        "PostPlatform", back_populates="social_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SocialAccount {self.platform.value}:{self.username}>"
