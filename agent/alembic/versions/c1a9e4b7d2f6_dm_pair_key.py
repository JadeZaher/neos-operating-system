"""Direct-message pair key.

Additive. Adds nullable ``conversations.dm_pair_key`` and a unique index on it.
Existing rows stay NULL, including duplicate direct threads: the index allows
many NULLs, so this revision does not delete, merge, or rewrite any row.
A second upgrade adds nothing. Downgrade drops the index and the column.
"""
from alembic import op
import sqlalchemy as sa

revision = "c1a9e4b7d2f6"
down_revision = "b8d3f1a6c4e2"
branch_labels = None
depends_on = None

INDEX = "uq_conversations_dm_pair_key"


def _has_column(bind) -> bool:
    return "dm_pair_key" in {column["name"] for column in sa.inspect(bind).get_columns("conversations")}


def _has_index(bind) -> bool:
    inspector = sa.inspect(bind)
    names = {index["name"] for index in inspector.get_indexes("conversations")}
    names.update(constraint["name"] for constraint in inspector.get_unique_constraints("conversations"))
    return INDEX in names


def upgrade():
    bind = op.get_bind()
    if "conversations" not in sa.inspect(bind).get_table_names():
        return
    if not _has_column(bind):
        op.add_column("conversations", sa.Column("dm_pair_key", sa.String(80), nullable=True))
    if not _has_index(bind):
        op.create_index(INDEX, "conversations", ["dm_pair_key"], unique=True)


def downgrade():
    bind = op.get_bind()
    if "conversations" not in sa.inspect(bind).get_table_names():
        return
    if _has_index(bind):
        op.drop_index(INDEX, table_name="conversations")
    if _has_column(bind):
        op.drop_column("conversations", "dm_pair_key")
