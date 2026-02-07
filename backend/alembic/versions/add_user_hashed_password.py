"""Add hashed_password to users table

Revision ID: add_hashed_password_001
Revises: add_aspect_ratio_001
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_hashed_password_001'
down_revision: Union[str, None] = 'add_aspect_ratio_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add hashed_password column to users table
    # Nullable to support existing users without passwords (e.g., OAuth-only users)
    op.add_column(
        'users',
        sa.Column(
            'hashed_password',
            sa.String(255),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
