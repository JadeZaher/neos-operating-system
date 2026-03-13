"""add_ecosystem_directory_fields

Revision ID: b3e1f7a2c4d9
Revises: a9ac90dc36b7
Create Date: 2026-03-08 19:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e1f7a2c4d9'
down_revision: Union[str, None] = 'a9ac90dc36b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ecosystems', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('ecosystems', sa.Column('website', sa.String(length=500), nullable=True))
    op.add_column('ecosystems', sa.Column('logo_url', sa.String(length=500), nullable=True))
    op.add_column('ecosystems', sa.Column('founded_date', sa.Date(), nullable=True))
    op.add_column('ecosystems', sa.Column('tags', sa.JSON(), nullable=True))
    op.add_column('ecosystems', sa.Column('contact_email', sa.String(length=255), nullable=True))
    op.add_column('ecosystems', sa.Column('governance_summary', sa.Text(), nullable=True))
    op.add_column('ecosystems', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='public'))


def downgrade() -> None:
    op.drop_column('ecosystems', 'visibility')
    op.drop_column('ecosystems', 'governance_summary')
    op.drop_column('ecosystems', 'contact_email')
    op.drop_column('ecosystems', 'tags')
    op.drop_column('ecosystems', 'founded_date')
    op.drop_column('ecosystems', 'logo_url')
    op.drop_column('ecosystems', 'website')
    op.drop_column('ecosystems', 'location')
