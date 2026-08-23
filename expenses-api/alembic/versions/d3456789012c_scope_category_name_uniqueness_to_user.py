"""Scope category name uniqueness to user

Revision ID: d3456789012c
Revises: c2345678901b
Create Date: 2026-08-23 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d3456789012c"
down_revision: str | Sequence[str] | None = "c2345678901b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)
    op.create_unique_constraint("uq_categories_user_id_name", "categories", ["user_id", "name"])


def downgrade() -> None:
    op.drop_constraint("uq_categories_user_id_name", "categories", type_="unique")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)
