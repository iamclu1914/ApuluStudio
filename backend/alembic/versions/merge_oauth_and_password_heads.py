"""Merge oauth and password migration heads.

Revision ID: merge_oauth_password_001
Revises: add_oauth_states_001, add_hashed_password_001
Create Date: 2026-02-07
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "merge_oauth_password_001"
down_revision: Union[str, Sequence[str], None] = (
    "add_oauth_states_001",
    "add_hashed_password_001",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge two independent migration branches."""


def downgrade() -> None:
    """Unmerge by downgrading to either parent head."""
