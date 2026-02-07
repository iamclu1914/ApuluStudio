"""Add preferred_aspect_ratio to social_accounts

Revision ID: add_aspect_ratio_001
Revises: postgres_patterns_optimization
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_aspect_ratio_001'
down_revision: Union[str, None] = 'postgres_patterns_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add preferred_aspect_ratio column with default 'original'
    op.add_column(
        'social_accounts',
        sa.Column(
            'preferred_aspect_ratio',
            sa.String(20),
            nullable=False,
            server_default='original'
        )
    )


def downgrade() -> None:
    op.drop_column('social_accounts', 'preferred_aspect_ratio')
