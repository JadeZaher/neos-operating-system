"""Add course, quiz, badge, tag, and profile tile tables.

Revision ID: 001_add_courses
Revises: e6a3b8c2d1f5
Create Date: 2026-04-04 00:00:00.000000
"""
from alembic import op

revision = "001_add_courses"
down_revision = "e6a3b8c2d1f5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id UUID PRIMARY KEY, ecosystem_id UUID NOT NULL REFERENCES ecosystems(id),
        domain_id UUID REFERENCES domains(id), title VARCHAR(500) NOT NULL,
        description TEXT, created_by UUID REFERENCES members(id),
        is_onboarding_required BOOLEAN NOT NULL DEFAULT FALSE,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_courses_ecosystem_id ON courses(ecosystem_id);

    CREATE TABLE IF NOT EXISTS quizzes (
        id UUID PRIMARY KEY, course_id UUID REFERENCES courses(id),
        title VARCHAR(500) NOT NULL, description TEXT,
        mode VARCHAR(50) NOT NULL DEFAULT 'standard', survey_json JSONB,
        time_limit INTEGER, passing_score INTEGER,
        allow_retakes BOOLEAN NOT NULL DEFAULT TRUE,
        visibility VARCHAR(50) NOT NULL DEFAULT 'public',
        is_published BOOLEAN NOT NULL DEFAULT FALSE,
        created_by UUID REFERENCES members(id),
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_quizzes_course_id ON quizzes(course_id);

    CREATE TABLE IF NOT EXISTS quiz_results (
        id UUID PRIMARY KEY, quiz_id UUID NOT NULL REFERENCES quizzes(id),
        member_id UUID NOT NULL REFERENCES members(id),
        survey_results JSONB, score FLOAT, is_passed BOOLEAN,
        time_spent INTEGER, result_metadata JSONB, completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_quiz_results_quiz_id ON quiz_results(quiz_id);

    CREATE TABLE IF NOT EXISTS quiz_progress (
        id UUID PRIMARY KEY, quiz_id UUID NOT NULL REFERENCES quizzes(id),
        member_id UUID NOT NULL REFERENCES members(id),
        current_question_index INTEGER NOT NULL DEFAULT 0,
        answers JSONB, started_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_tags (
        id UUID PRIMARY KEY, member_id UUID NOT NULL REFERENCES members(id),
        quiz_result_id UUID REFERENCES quiz_results(id),
        tag_key VARCHAR(255) NOT NULL, tag_value VARCHAR(500),
        tag_category VARCHAR(100), data_type VARCHAR(50), numeric_value FLOAT,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS user_badges (
        id UUID PRIMARY KEY, member_id UUID NOT NULL REFERENCES members(id),
        badge_key VARCHAR(255) NOT NULL, badge_name VARCHAR(255) NOT NULL,
        badge_description TEXT, badge_category VARCHAR(100),
        badge_icon VARCHAR(255), strength FLOAT,
        source_tag_keys JSONB, earned_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS profile_tiles (
        id UUID PRIMARY KEY, member_id UUID NOT NULL REFERENCES members(id),
        submission_id UUID, type VARCHAR(50) NOT NULL,
        data JSONB, layout_index INTEGER NOT NULL DEFAULT 0,
        is_visible BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
    );
    """)


def downgrade():
    for table in ['profile_tiles', 'user_badges', 'user_tags', 'quiz_progress', 'quiz_results', 'quizzes', 'courses']:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
