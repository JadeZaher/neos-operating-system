"""add public profiles and share authors

Revision ID: g8c5d1e4f2a7
Revises: f7b4c9a2e5d8
Create Date: 2026-07-27 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g8c5d1e4f2a7"
down_revision: Union[str, Sequence[str], None] = "f7b4c9a2e5d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("headline", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("website", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("social_links", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("skills", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("interests", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("projects", sa.JSON(), nullable=True))

    op.add_column(
        "shares_needs",
        sa.Column("author_member_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_shares_needs_author_member_id_members",
        "shares_needs",
        "members",
        ["author_member_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_shares_needs_author_member_id",
        "shares_needs",
        ["author_member_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_shares_needs_author_member_id", table_name="shares_needs")
    op.drop_constraint(
        "fk_shares_needs_author_member_id_members",
        "shares_needs",
        type_="foreignkey",
    )
    op.drop_column("shares_needs", "author_member_id")

    op.drop_column("users", "projects")
    op.drop_column("users", "interests")
    op.drop_column("users", "skills")
    op.drop_column("users", "social_links")
    op.drop_column("users", "website")
    op.drop_column("users", "location")
    op.drop_column("users", "bio")
    op.drop_column("users", "headline")
