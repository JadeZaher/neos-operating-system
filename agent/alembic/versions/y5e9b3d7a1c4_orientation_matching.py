"""Private orientation chat and consent-scoped matching; see api/ORIENTATION_MATCHING.md."""
from alembic import op

revision = "y5e9b3d7a1c4"
down_revision = "x4d8a2c6f0b3"
branch_labels = None
depends_on = None


def upgrade():
    from neos_agent.db.models import OrientationChatSession, MatchingConsent, EcosystemMatchingProfile, MatchingAnswers, MatchingAssessment
    bind = op.get_bind()
    for model in (OrientationChatSession, MatchingConsent, EcosystemMatchingProfile, MatchingAnswers, MatchingAssessment):
        model.__table__.create(bind, checkfirst=True)


def downgrade():
    from neos_agent.db.models import OrientationChatSession, MatchingConsent, EcosystemMatchingProfile, MatchingAnswers, MatchingAssessment
    bind = op.get_bind()
    for model in (MatchingAssessment, MatchingAnswers, EcosystemMatchingProfile, MatchingConsent, OrientationChatSession):
        model.__table__.drop(bind, checkfirst=True)
