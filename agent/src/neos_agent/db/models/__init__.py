"""Re-export all ORM model classes for convenient imports.

Existing code using `from neos_agent.db.models import X` continues to work
after the split into per-model files.
"""

# Foundation
from ._base import Base, GUID, TimestampMixin  # noqa: F401

# Models
from .engagement import (
    EngagementPreference, EngagementSubscription, EngagementEvent, EngagementInboxItem,
    NotificationContact, NotificationChallenge, EngagementPushDevice, NotificationDelivery,
    NotificationConsumption, NotificationWebhookReceipt, NotificationRateLimit,
)
from .ecosystem import Ecosystem  # noqa: F401
from .user import User  # noqa: F401
from .member import Member  # noqa: F401
from .memberdecision import MemberDecision  # noqa: F401
from .memberonboarding import MemberOnboarding  # noqa: F401
from .memberstatustransition import MemberStatusTransition  # noqa: F401
from .domain import Domain  # noqa: F401
from .domainelement import DomainElement  # noqa: F401
from .domainmetric import DomainMetric  # noqa: F401
from .agreement import Agreement  # noqa: F401
from .agreementversion import AgreementVersion  # noqa: F401
from .agreementratificationrecord import AgreementRatificationRecord  # noqa: F401
from .agreementceremony import AgreementCeremony  # noqa: F401
from .agreementmemberconsent import AgreementMemberConsent  # noqa: F401
from .agreementrequirement import AgreementRequirement  # noqa: F401
from .memberalignmentevent import MemberAlignmentEvent  # noqa: F401
from .amendmentrecord import AmendmentRecord  # noqa: F401
from .reviewrecord import ReviewRecord  # noqa: F401
from .proposal import Proposal  # noqa: F401
from .advicelog import AdviceLog  # noqa: F401
from .adviceentry import AdviceEntry  # noqa: F401
from .advicenonrespondent import AdviceNonRespondent  # noqa: F401
from .consentrecord import ConsentRecord  # noqa: F401
from .consentparticipant import ConsentParticipant  # noqa: F401
from .consentintegrationround import ConsentIntegrationRound  # noqa: F401
from .consentobjectionaddressed import ConsentObjectionAddressed  # noqa: F401
from .testreport import TestReport  # noqa: F401
from .testsuccesscriterion import TestSuccessCriterion  # noqa: F401
from .decisionrecord import DecisionRecord  # noqa: F401
from .decisiondissentrecord import DecisionDissentRecord  # noqa: F401
from .decisionparticipant import DecisionParticipant  # noqa: F401
from .decisionsemantictag import DecisionSemanticTag  # noqa: F401
from .conflictcase import ConflictCase  # noqa: F401
from .repairagreementrecord import RepairAgreementRecord  # noqa: F401
from .governancehealthaudit import GovernanceHealthAudit  # noqa: F401
from .emergencystate import EmergencyState  # noqa: F401
from .exitrecord import ExitRecord  # noqa: F401
from .agentsession import AgentSession  # noqa: F401
from .agenttoken import AgentToken  # noqa: F401
from .authsession import AuthSession  # noqa: F401
from .authchallenge import AuthChallenge  # noqa: F401
from .conversation import Conversation  # noqa: F401
from .conversationparticipant import ConversationParticipant  # noqa: F401
from .message import Message  # noqa: F401
from .conversationlink import ConversationLink  # noqa: F401
from .circlemembership import CircleMembership  # noqa: F401
from .sharesneeds import SharesNeeds  # noqa: F401
from .collaboration import Collaboration  # noqa: F401
from .collaborationapproval import CollaborationApproval  # noqa: F401
from .compliancesummary import ComplianceSummary  # noqa: F401
from .pushsubscription import PushSubscription  # noqa: F401
from .journeymap import JourneyMap  # noqa: F401
from .ethosuseraccess import EthosUserAccess  # noqa: F401
from .userjourneyprogress import UserJourneyProgress  # noqa: F401
from .badgedefinition import BadgeDefinition  # noqa: F401
from .team import Team  # noqa: F401
from .teammembership import TeamMembership  # noqa: F401
from .quizassignment import QuizAssignment  # noqa: F401
from .appsetting import AppSetting  # noqa: F401
from .ctchandoff import CtcHandoff  # noqa: F401
from .nodeadmin import NodeAdmin, NodeAdminAction, NodeAdminSnapshot  # noqa: F401
from .orientationchat import OrientationChatSession  # noqa: F401
from .matching import MatchingConsent, EcosystemMatchingProfile, MatchingAnswers, MatchingAssessment  # noqa: F401

from sqlalchemy import select as _select
from sqlalchemy.orm import column_property as _column_property
User.node_admin_active = _column_property(_select(NodeAdmin.active).where(NodeAdmin.user_id == User.id, User.disabled_at.is_(None)).correlate_except(NodeAdmin).scalar_subquery())

__all__ = [
    "OrientationChatSession", "MatchingConsent", "EcosystemMatchingProfile", "MatchingAnswers", "MatchingAssessment",
    "NodeAdmin",
    "NodeAdminAction",
    "NodeAdminSnapshot",
    "Base",
    "GUID",
    "TimestampMixin",
    "Ecosystem",
    "User",
    "Member",
    "MemberDecision",
    "MemberOnboarding",
    "MemberStatusTransition",
    "Domain",
    "DomainElement",
    "DomainMetric",
    "Agreement",
    "AgreementVersion",
    "AgreementRatificationRecord",
    "AgreementCeremony",
    "AgreementMemberConsent",
    "AgreementRequirement",
    "MemberAlignmentEvent",
    "AmendmentRecord",
    "ReviewRecord",
    "Proposal",
    "AdviceLog",
    "AdviceEntry",
    "AdviceNonRespondent",
    "ConsentRecord",
    "ConsentParticipant",
    "ConsentIntegrationRound",
    "ConsentObjectionAddressed",
    "TestReport",
    "TestSuccessCriterion",
    "DecisionRecord",
    "DecisionDissentRecord",
    "DecisionParticipant",
    "DecisionSemanticTag",
    "ConflictCase",
    "RepairAgreementRecord",
    "GovernanceHealthAudit",
    "EmergencyState",
    "ExitRecord",
    "AgentSession",
    "AuthSession",
    "AuthChallenge",
    "Conversation",
    "ConversationParticipant",
    "Message",
    "ConversationLink",
    "CircleMembership",
    "SharesNeeds",
    "Collaboration",
    "CollaborationApproval",
    "ComplianceSummary",
    "PushSubscription",
    "JourneyMap",
    "EthosUserAccess",
    "UserJourneyProgress",
    "BadgeDefinition",
    "Team",
    "TeamMembership",
    "QuizAssignment",
    "AppSetting",
    "CtcHandoff",
    "EngagementPreference", "EngagementSubscription", "EngagementEvent", "EngagementInboxItem",
    "NotificationContact", "NotificationChallenge", "EngagementPushDevice", "NotificationDelivery",
    "NotificationConsumption", "NotificationWebhookReceipt", "NotificationRateLimit",
]
