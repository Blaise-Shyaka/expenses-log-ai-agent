"""Seed test user for development

Revision ID: b1234567890a
Revises: a758fc557b16
Create Date: 2025-10-02 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1234567890a'
down_revision: Union[str, Sequence[str], None] = 'a758fc557b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed test user for development. TODO: Remove when auth is implemented."""
    # Insert test user with known UUID: 00000000-0000-0000-0000-000000000001
    op.execute("""
        INSERT INTO users (id, first_name, last_name, email, created_at, updated_at)
        VALUES (
            UNHEX('00000000000000000000000000000001'),
            'Test',
            'User',
            'test@example.com',
            NOW(),
            NOW()
        )
    """)


def downgrade() -> None:
    """Remove test user."""
    op.execute("""
        DELETE FROM users WHERE id = UNHEX('00000000000000000000000000000001')
    """)
