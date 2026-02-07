"""Encrypt OAuth tokens at rest

Revision ID: encrypt_tokens_001
Revises: add_aspect_ratio_001
Create Date: 2026-01-31

This migration adds documentation about token encryption.
The actual encryption is handled transparently by SQLAlchemy's TypeDecorator
in the SocialAccount model (EncryptedString type).

IMPORTANT: After deploying this migration:
1. Set the ENCRYPTION_KEY environment variable
2. Run the one-time re-encryption script to encrypt existing plaintext tokens:

   python -m app.scripts.encrypt_existing_tokens

Existing plaintext tokens will continue to work (the EncryptedString type
detects plaintext vs encrypted values), but should be re-encrypted for security.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'encrypt_tokens_001'
down_revision: Union[str, None] = 'add_aspect_ratio_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    No schema changes required.

    The EncryptedString TypeDecorator handles encryption transparently.
    Existing plaintext tokens remain readable and new tokens are encrypted.

    To encrypt existing tokens, run after migration:
        python -m app.scripts.encrypt_existing_tokens

    This is a documentation-only migration marking the addition of
    token encryption capability.
    """
    # Add a comment to the table documenting the encryption
    # Note: This is informational only - actual encryption is handled by the ORM
    op.execute(
        "COMMENT ON COLUMN social_accounts.access_token IS "
        "'OAuth access token (encrypted at rest with Fernet)'"
    )
    op.execute(
        "COMMENT ON COLUMN social_accounts.refresh_token IS "
        "'OAuth refresh token (encrypted at rest with Fernet)'"
    )


def downgrade() -> None:
    """
    Remove column comments.

    Note: This does NOT decrypt tokens. To downgrade and remove encryption:
    1. Run decrypt script to convert encrypted tokens to plaintext
    2. Remove EncryptedString type from model
    3. Run this downgrade
    """
    op.execute(
        "COMMENT ON COLUMN social_accounts.access_token IS NULL"
    )
    op.execute(
        "COMMENT ON COLUMN social_accounts.refresh_token IS NULL"
    )
