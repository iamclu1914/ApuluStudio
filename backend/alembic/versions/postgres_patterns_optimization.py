"""Postgres patterns optimization

Revision ID: postgres_patterns_01
Revises: 2fc79e3f99fd
Create Date: 2026-01-28

Applies postgres-patterns skill recommendations:
- Composite indexes for common query patterns
- Partial indexes for filtered queries
- Covering indexes to avoid table lookups
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'postgres_patterns_01'
down_revision: Union[str, None] = '2fc79e3f99fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === POSTS TABLE OPTIMIZATIONS ===

    # Composite index: status + scheduled_at for scheduler queries
    # Pattern: WHERE status = 'SCHEDULED' AND scheduled_at <= NOW()
    op.create_index(
        'ix_posts_status_scheduled_at',
        'posts',
        ['status', 'scheduled_at'],
        unique=False
    )

    # Composite index: user_id + status for dashboard queries
    # Pattern: WHERE user_id = ? AND status = ?
    op.create_index(
        'ix_posts_user_id_status',
        'posts',
        ['user_id', 'status'],
        unique=False
    )

    # Partial index: only scheduled posts (smaller, faster for scheduler)
    op.execute("""
        CREATE INDEX ix_posts_scheduled_pending
        ON posts (scheduled_at)
        WHERE status = 'SCHEDULED'
    """)

    # Composite index: user_id + created_at for timeline queries
    op.create_index(
        'ix_posts_user_id_created_at',
        'posts',
        ['user_id', 'created_at'],
        unique=False
    )

    # === SOCIAL ACCOUNTS OPTIMIZATIONS ===

    # Composite index: user_id + platform for filtering user's accounts
    # Pattern: WHERE user_id = ? AND platform = ?
    op.create_index(
        'ix_social_accounts_user_platform',
        'social_accounts',
        ['user_id', 'platform'],
        unique=False
    )

    # Partial index: only active accounts
    op.execute("""
        CREATE INDEX ix_social_accounts_active
        ON social_accounts (user_id)
        WHERE is_active = TRUE
    """)

    # Index for token refresh queries
    op.create_index(
        'ix_social_accounts_token_expires',
        'social_accounts',
        ['token_expires_at'],
        unique=False
    )

    # === POST PLATFORMS OPTIMIZATIONS ===

    # Composite index: status + published_at for analytics
    op.create_index(
        'ix_post_platforms_status_published',
        'post_platforms',
        ['status', 'published_at'],
        unique=False
    )

    # Partial index: only published posts for metrics updates
    op.execute("""
        CREATE INDEX ix_post_platforms_metrics_update
        ON post_platforms (metrics_updated_at)
        WHERE status = 'PUBLISHED'
    """)

    # === COMMENTS OPTIMIZATIONS ===

    # Partial index: unread comments for inbox
    op.execute("""
        CREATE INDEX ix_comments_unread
        ON comments (social_account_id, posted_at)
        WHERE is_read = FALSE
    """)

    # === MENTIONS OPTIMIZATIONS ===

    # Partial index: unread mentions for inbox
    op.execute("""
        CREATE INDEX ix_mentions_unread
        ON mentions (social_account_id, mentioned_at)
        WHERE is_read = FALSE
    """)


def downgrade() -> None:
    # Drop all new indexes
    op.execute("DROP INDEX IF EXISTS ix_mentions_unread")
    op.execute("DROP INDEX IF EXISTS ix_comments_unread")
    op.execute("DROP INDEX IF EXISTS ix_post_platforms_metrics_update")
    op.drop_index('ix_post_platforms_status_published', table_name='post_platforms')
    op.drop_index('ix_social_accounts_token_expires', table_name='social_accounts')
    op.execute("DROP INDEX IF EXISTS ix_social_accounts_active")
    op.drop_index('ix_social_accounts_user_platform', table_name='social_accounts')
    op.drop_index('ix_posts_user_id_created_at', table_name='posts')
    op.execute("DROP INDEX IF EXISTS ix_posts_scheduled_pending")
    op.drop_index('ix_posts_user_id_status', table_name='posts')
    op.drop_index('ix_posts_status_scheduled_at', table_name='posts')
