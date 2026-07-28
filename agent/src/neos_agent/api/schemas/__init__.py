"""Pydantic v2 response schemas for the NEOS agent API.

All schemas are organized by domain. Import directly from submodules
or use this package for backward-compatible imports.
"""

# Common
from .common import ApiError, HealthResponse, SkillItem, SkillsResponse

# Auth & ecosystem identity
from .auth import (
    AuthChallengeResponse,
    AuthMeResponse,
    AuthVerifyResponse,
    EcosystemSummary,
    LoginRequest,
    MemberSummary,
    SetCredentialsRequest,
    SetCredentialsResponse,
    UserSummary,
)

# Ecosystems
from .ecosystems import EcosystemCreateRequest, EcosystemDetail, EcosystemStewardItem, EcosystemUpdateRequest

# Dashboard
from .dashboard import ActivityItem, DashboardSummary, SummaryCard

# Agreements
from .agreements import (
    AgreementCreateRequest,
    AgreementConsentRequest,
    AgreementConsentWithdrawalRequest,
    AgreementCeremonySchema,
    AgreementConsentSummary,
    AgreementDetail,
    AgreementHistoryResponse,
    AgreementListItem,
    AgreementMemberConsentSchema,
    AgreementUpdateRequest,
    AgreementVersionSchema,
    AmendmentRecordSchema,
    RatificationRecordSchema,
    ReviewRecordSchema,
)

# Proposals
from .proposals import (
    AdviceEntryCreateRequest,
    AdviceEntrySchema,
    AdviceLogSchema,
    ConsentParticipantSchema,
    ConsentPositionRequest,
    ConsentRecordSchema,
    ProposalCreateRequest,
    ProposalDetail,
    ProposalListItem,
    ProposalUpdateRequest,
    TestReportSchema,
    TestSuccessCriterionSchema,
)

# Members
from .members import (
    MemberCreateRequest,
    MemberDetail,
    MemberListItem,
    MemberProfileResponse,
    MemberUpdateRequest,
    OnboardingChecklistItem,
    OnboardingSnapshot,
    RoleUpdateRequest,
    StatusTransitionRequest,
)

# Domains
from .domains import (
    DomainCreateRequest,
    DomainDetail,
    DomainElementSchema,
    DomainListItem,
    DomainMetricSchema,
    DomainUpdateRequest,
)

# Decisions
from .decisions import (
    DecisionDetail,
    DecisionListItem,
    DissentRecordSchema,
    ParticipantSchema,
    SemanticTagSchema,
)

# Conflicts
from .conflicts import (
    ConflictCreateRequest,
    ConflictDetail,
    ConflictListItem,
    ConflictUpdateRequest,
    RepairAgreementSchema,
    RepairCreateRequest,
    RepairUpdateRequest,
)

# Exit
from .exit import ExitCreateRequest, ExitDetail, ExitListItem, ExitStatusRequest

# Safeguards
from .safeguards import AuditCreateRequest, AuditDetail, AuditListItem, HealthSummary

# Onboarding
from .onboarding import CeremonyState, OnboardingListItem, SectionConsentRequest

# Quizzes
from .quizzes import (
    QuizCreateRequest,
    QuizDetail,
    QuizListItem,
    QuizResultItem,
    QuizSubmitRequest,
    QuizUpdateRequest,
    UserBadgeItem,
    UserTagItem,
)

# Messaging
from .messaging import (
    ConversationDetailSchema,
    ConversationSummary,
    CreateConversationRequest,
    MemberPickerItem,
    MessageSchema,
    ParticipantSummary,
)
