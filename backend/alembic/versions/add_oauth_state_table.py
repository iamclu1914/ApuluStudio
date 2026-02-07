"""Add oauth_states table for secure OAuth flow handling

Revision ID: add_oauth_states_001
Revises: encrypt_tokens_001
Create Date: 2026-01-31

This migration creates the oauth_states table to store OAuth state tokens
in the database instead of in-memory. This provides:
- Persistence across server restarts
- Support for multiple server instances (horizontal scaling)
- Automatic expiration and cleanup
- Better security through database-backed CSRF protection
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_oauth_states_001'
down_revision: Union[str, None] = 'encrypt_tokens_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_states table."""
    op.create_table(
        'oauth_states',
        sa.Column('state_token', sa.String(64), primary_key=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('additional_data', sa.String(1000), nullable=True),
    )

    # Create indexes for efficient querying
    op.create_index('ix_oauth_states_user_id', 'oauth_states', ['user_id'])
    op.create_index('ix_oauth_states_expires_at', 'oauth_states', ['expires_at'])

    # Add comment documenting the table purpose
    op.execute(
        "COMMENT ON TABLE oauth_states IS "
        "'Stores OAuth state tokens for CSRF protection during OAuth flows. "
        "Tokens expire after 15 minutes and should be cleaned up periodically.'"
    )


def downgrade() -> None:
    """Drop oauth_states table."""
    op.drop_index('ix_oauth_states_expires_at', table_name='oauth_states')
    op.drop_index('ix_oauth_states_user_id', table_name='oauth_states')
    op.drop_table('oauth_states')
