"""Drop credential columns from users table

Revision ID: c2345678901b
Revises: b1234567890a
Create Date: 2026-07-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2345678901b"
down_revision: str | Sequence[str] | None = "b1234567890a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_users_hashed_password"), table_name="users")
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_column("users", "hashed_password")
    op.drop_column("users", "google_id")

    op.alter_column("users", "first_name", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("users", "last_name", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "last_name", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("users", "first_name", existing_type=sa.String(length=255), nullable=False)

    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=False)
    op.create_index(op.f("ix_users_hashed_password"), "users", ["hashed_password"], unique=False)
