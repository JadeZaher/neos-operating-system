"""Add users table and refactor members/auth_sessions to reference users.

Splits identity (auth) from membership (ecosystem context):
- Creates `users` table for platform-wide identity
- Adds `user_id` FK on `members` pointing to `users`
- Changes `auth_sessions` to reference `users` instead of `members`
- Removes auth-specific columns from `members` (did, username, password_hash, etc.)

Revision ID: 006_add_users_table
Revises: 005_add_shared_ecosystem_ids
Create Date: 2026-05-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "006_add_users_table"
down_revision = "005_add_shared_ecosystem_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("did", sa.String(500), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("profile_picture", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("did"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_did", "users", ["did"])
    op.create_index("ix_users_oauth_id", "users", ["oauth_id"])

    # 2. Migrate existing members data into users
    # Create a user for each unique DID (or unique member without DID)
    op.execute("""
        INSERT INTO users (id, did, username, password_hash, oauth_provider, oauth_id,
                          display_name, phone, profile_picture, created_at, updated_at)
        SELECT DISTINCT ON (COALESCE(did, id::text))
            gen_random_uuid(), did, username, password_hash, oauth_provider, oauth_id,
            display_name, phone, profile_picture, created_at, updated_at
        FROM members
        ORDER BY COALESCE(did, id::text), created_at ASC
    """)

    # 3. Add user_id column to members (nullable initially for migration)
    op.add_column("members", sa.Column("user_id", sa.Uuid(), nullable=True))

    # 4. Backfill user_id on members by matching DID or falling back to other identifiers
    op.execute("""
        UPDATE members m
        SET user_id = u.id
        FROM users u
        WHERE (m.did IS NOT NULL AND u.did = m.did)
           OR (m.did IS NULL AND m.username IS NOT NULL AND u.username = m.username)
           OR (m.did IS NULL AND m.username IS NULL AND u.oauth_id IS NOT NULL
               AND u.oauth_id = m.oauth_id AND u.oauth_provider = m.oauth_provider)
    """)

    # For any members that still have no user_id (edge case), create users for them
    op.execute("""
        INSERT INTO users (id, display_name, created_at, updated_at)
        SELECT gen_random_uuid(), m.display_name, m.created_at, m.updated_at
        FROM members m
        WHERE m.user_id IS NULL
    """)
    # This second pass is a safety net — link remaining orphans by display_name match
    op.execute("""
        UPDATE members m
        SET user_id = u.id
        FROM users u
        WHERE m.user_id IS NULL
          AND u.display_name = m.display_name
          AND u.did IS NULL AND u.username IS NULL
    """)

    # 5. Make user_id NOT NULL and add FK + index
    op.alter_column("members", "user_id", nullable=False)
    op.create_foreign_key("fk_members_user_id", "members", "users", ["user_id"], ["id"])
    op.create_index("ix_members_user_id", "members", ["user_id"])

    # 6. Drop old unique constraint and create new one
    op.execute("ALTER TABLE members DROP CONSTRAINT IF EXISTS uq_member_ecosystem_did")
    op.create_unique_constraint("uq_member_ecosystem_user", "members", ["ecosystem_id", "user_id"])

    # 7. Remove auth columns from members
    op.drop_column("members", "did")
    op.drop_column("members", "username")
    op.drop_column("members", "password_hash")
    op.drop_column("members", "oauth_provider")
    op.drop_column("members", "oauth_id")
    op.drop_column("members", "phone")
    op.drop_column("members", "profile_picture")

    # 8. Update auth_sessions: add user_id, backfill, drop member_id and did
    op.add_column("auth_sessions", sa.Column("user_id", sa.Uuid(), nullable=True))

    # Backfill auth_sessions.user_id from members
    op.execute("""
        UPDATE auth_sessions a
        SET user_id = m.user_id
        FROM members m
        WHERE a.member_id = m.id
    """)

    # Delete orphaned sessions (member was deleted)
    op.execute("DELETE FROM auth_sessions WHERE user_id IS NULL")

    op.alter_column("auth_sessions", "user_id", nullable=False)
    op.create_foreign_key("fk_auth_sessions_user_id", "auth_sessions", "users", ["user_id"], ["id"])
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])

    # Drop old columns and index
    op.execute("DROP INDEX IF EXISTS ix_auth_sessions_member_id")
    op.drop_column("auth_sessions", "member_id")
    op.drop_column("auth_sessions", "did")


def downgrade() -> None:
    # Re-add columns to auth_sessions
    op.add_column("auth_sessions", sa.Column("member_id", sa.Uuid(), nullable=True))
    op.add_column("auth_sessions", sa.Column("did", sa.String(500), nullable=True))

    # Re-add columns to members
    op.add_column("members", sa.Column("did", sa.String(500), nullable=True))
    op.add_column("members", sa.Column("username", sa.String(100), nullable=True))
    op.add_column("members", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("members", sa.Column("oauth_provider", sa.String(50), nullable=True))
    op.add_column("members", sa.Column("oauth_id", sa.String(255), nullable=True))
    op.add_column("members", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("members", sa.Column("profile_picture", sa.String(500), nullable=True))

    # Backfill from users
    op.execute("""
        UPDATE members m
        SET did = u.did, username = u.username, password_hash = u.password_hash,
            oauth_provider = u.oauth_provider, oauth_id = u.oauth_id,
            phone = u.phone, profile_picture = u.profile_picture
        FROM users u
        WHERE m.user_id = u.id
    """)

    # Drop user_id from members
    op.drop_constraint("uq_member_ecosystem_user", "members")
    op.drop_constraint("fk_members_user_id", "members")
    op.drop_column("members", "user_id")

    # Restore auth_sessions
    op.execute("""
        UPDATE auth_sessions a
        SET member_id = m.id
        FROM members m, users u
        WHERE a.user_id = u.id AND m.did = u.did
    """)
    op.drop_constraint("fk_auth_sessions_user_id", "auth_sessions")
    op.drop_column("auth_sessions", "user_id")

    # Drop users table
    op.drop_table("users")
