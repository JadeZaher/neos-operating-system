"""Configured subgroup entry quizzes and server grading provenance."""
from alembic import op
import sqlalchemy as sa

revision = "x4d8a2c6f0b3"
down_revision = "w3c7f1a9d5e2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "team_id" not in {c["name"] for c in sa.inspect(bind).get_columns("quizzes")}:
        op.add_column("quizzes", sa.Column("team_id", sa.Uuid(), nullable=True))
        op.create_index("ix_quizzes_team_id", "quizzes", ["team_id"])
        if bind.dialect.name == "postgresql":
            op.create_foreign_key("fk_quizzes_team_id", "quizzes", "teams", ["team_id"], ["id"])
    if "graded_fingerprint" not in {c["name"] for c in sa.inspect(bind).get_columns("quiz_results")}:
        op.add_column("quiz_results", sa.Column("graded_fingerprint", sa.String(64), nullable=True))
    if "completion_verified" not in {c["name"] for c in sa.inspect(bind).get_columns("quiz_results")}:
        op.add_column("quiz_results", sa.Column("completion_verified", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column("quiz_results", "completion_verified")
    op.drop_column("quiz_results", "graded_fingerprint")
    if op.get_bind().dialect.name == "postgresql":
        op.drop_constraint("fk_quizzes_team_id", "quizzes", type_="foreignkey")
    op.drop_index("ix_quizzes_team_id", table_name="quizzes")
    op.drop_column("quizzes", "team_id")
