"""Allowlisted support surfaces; see services/AGENTS.md, Node support."""
from __future__ import annotations

from dataclasses import dataclass
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON

from neos_agent.db.models import Base
import neos_agent.db.course_models  # noqa: F401


# Each entry declares the fields that technical support can correct.
WRITABLE = {
    "users": "username display_name disabled_at profile_picture headline bio location website social_links skills interests projects",
    "ecosystems": "name description status visibility logo_url location mission tagline sector ethos_type slug external_url image_url parent_ethos_id is_public is_active phase map_url map_type map_title external_links",
    "members": "ecosystem_id user_id member_id display_name current_status role profile onboarding_status skills_offered skills_needed interests privacy",
    "domains": "ecosystem_id domain_id name purpose status steward_id parent_domain_id current_steward version metric_definitions elements",
    "domain_elements": "domain_id element_name element_value",
    "domain_metrics": "domain_id metric target measurement_method",
    "proposals": "ecosystem_id type decision_type title affected_domain urgency proposed_change rationale advice_deadline consent_deadline test_duration governing_agreement_id amends_agreement_id act_policy status",
    "agreements": "ecosystem_id agreement_id title type status text affected_parties domain hierarchy_level parent_agreement_id review_date sunset_date ratification_date requires_explicit_consent prerequisite_scopes prerequisite_domain_ids alignment_points act_policy",
    "decision_records": "ecosystem_id record_id date holding ratio_decidendi obiter_dicta deliberation_summary source_skill source_layer artifact_type artifact_reference domain precedent_level status overruled_by superseded_by related_records review_date",
    "conflict_cases": "ecosystem_id case_id title status severity scope tier root_cause_category urgency safety_flag description facilitator_id domain triage_notes resolution_summary resolved_date",
    "repair_agreement_records": "conflict_case_id title status commitments responsible_party checkin_30_date checkin_60_date checkin_90_date completed_date",
    "emergency_states": "ecosystem_id state auto_revert_at half_open_entered_at recovery_entered_at closed_at post_review_status notes authority_days",
    "exit_records": "ecosystem_id member_id status exit_type declared_date target_completion_date coordinator_id commitment_inventory unwinding_status data_export_requested data_export_completed departure_notice re_entry_eligible completed_date notes",
    "governance_health_audits": "ecosystem_id audit_id status audit_date audit_period_start audit_period_end next_audit_date next_audit_due trigger_type",
    "shares_needs": "ecosystem_id author_member_id domain_id type title description category visibility tags status status_reason",
    "collaborations": "source_domain_id target_domain_id title description status engagement_tier terms linked_shares_needs required_agreement_ids review_date end_reason",
    "compliance_summaries": "ecosystem_id summary_id status period_start period_end summary findings recommendations",
    "courses": "title description sort_order ecosystem_id domain_id is_onboarding_required",
    "quizzes": "ecosystem_id course_id domain_id team_id title description mode survey_json time_limit passing_score allow_retakes visibility is_published is_entry_quiz",
    "quiz_assignments": "quiz_id member_id due_date status assigned_at",
    "quiz_progress": "quiz_id member_id current_question_index answers started_at",
    "user_tags": "member_id quiz_result_id tag_key tag_value tag_category data_type numeric_value",
    "user_badges": "member_id badge_key badge_name badge_description badge_category badge_icon strength source_tag_keys",
    "profile_tiles": "member_id submission_id type data layout_index is_visible",
    "journey_maps": "ecosystem_id slug title description sector_alignment role_types min_alignment_score content_sequence exit_package step_count is_default is_active",
    "user_journey_progress": "member_id ecosystem_id journey_map_id orientation_path current_step completed_steps status completed_at",
    "ethos_user_access": "member_id ecosystem_id role_in_ethos access_level",
    "badge_definitions": "ecosystem_id badge_key badge_name badge_description badge_category badge_icon strength is_active",
    "teams": "ecosystem_id name description is_active",
    "team_members": "team_id member_id role",
    "circle_memberships": "ecosystem_id domain_id member_id circle_id role status",
    "ctc_handoff": "member_id ready_for_neos_den",
    "app_settings": "key value",
    "conversations": "ecosystem_id type title",
    "conversation_participants": "conversation_id member_id role muted last_read_at",
    "messages": "deleted_at",
    "agent_sessions": "archived status ended_at",
    "member_onboarding": "member_id facilitator mentor_id checklist_items completion_percentage",
    "member_decisions": "state",
}
WRITABLE["ecosystems"] += " uaf_agreement_id"
WRITABLE["agreements"] += " act_policy"

# Human attestations and historical artifacts retain their original evidence.
EVIDENCE = frozenset({
    "member_status_transitions", "member_alignment_events", "agreement_versions", "agreement_ratification_records",
    "agreement_ceremonies", "agreement_member_consents", "agreement_requirements", "amendment_records", "review_records",
    "advice_logs", "advice_entries", "advice_non_respondents", "consent_records", "consent_participants",
    "consent_integration_rounds", "consent_objections_addressed", "test_reports", "test_success_criteria",
    "decision_dissent_records", "decision_participants", "decision_semantic_tags", "collaboration_approvals",
    "quiz_results", "conversation_links",
})
SECURITY = frozenset({"auth_sessions", "auth_challenges", "agent_tokens", "push_subscriptions"})
INTERNAL = frozenset({"node_admins", "node_admin_actions", "node_admin_snapshots"})
INTERNAL = INTERNAL | {"orientation_chat_sessions", "matching_consents", "ecosystem_matching_profiles", "matching_answers", "matching_assessments"}
SECRET_FIELDS = frozenset({"password_hash", "phone", "oauth_id", "share_token", "token_hash", "token", "challenge", "challenge_text", "endpoint", "p256dh", "p256dh_key", "auth_key", "auth", "keys", "subscription", "subscription_json", "secret", "session_id", "auth_session_id", "ip_address", "user_agent", "cookie", "access_token", "refresh_token"})
SETTING_KEYS = frozenset({"ctc_map", "sharesneeds_categories", "shares_needs_categories"})
LIST_FIELDS = ("id", "name", "title", "display_name", "username", "badge_name", "user_id", "member_id", "ecosystem_id", "status", "current_status", "active", "is_active", "archived", "created_at", "updated_at")


@dataclass(frozen=True)
class SupportResource:
    key: str
    model: type
    editable: frozenset[str]
    category: str

    @property
    def actions(self):
        if self.category == "security":
            return ["revoke"]
        if self.category == "evidence":
            return ["inspect", "archive_evidence", "restore_evidence"]
        actions = ["inspect"]
        if self.editable:
            actions += ["update"]
            if any(name in self.editable for name in ("status", "current_status", "state")):
                actions += ["override_state"]
            required = [c.name for c in self.model.__table__.columns if not c.nullable and not c.primary_key and c.default is None and c.server_default is None]
            supplied = set(self.editable) | {"proposal_id", "support_created_by_user_id", "support_action_id"}
            if set(required) <= supplied and self.key not in {"messages", "agent_sessions", "member_decisions", "conversation_participants", "quiz_progress"}:
                actions += ["create"]
        return actions


def registry() -> dict[str, SupportResource]:
    resources = {}
    for mapper in Base.registry.mappers:
        model = mapper.class_
        key = model.__tablename__
        if key in INTERNAL:
            continue
        if key not in WRITABLE and key not in EVIDENCE and key not in SECURITY:
            # A new model requires an explicit support policy before exposure.
            continue
        columns = set(model.__table__.columns.keys())
        editable = frozenset(WRITABLE.get(key, "").split()) & columns
        resources[key] = SupportResource(key, model, editable - SECRET_FIELDS, "security" if key in SECURITY else "evidence" if key in EVIDENCE else "state")
    return resources


def field_type(column):
    if column.foreign_keys:
        return "reference"
    if isinstance(column.type, Boolean):
        return "boolean"
    if isinstance(column.type, (Integer, Float)):
        return "number"
    if isinstance(column.type, DateTime):
        return "datetime"
    if isinstance(column.type, Date):
        return "date"
    if isinstance(column.type, JSON):
        return "json"
    return "text"


def catalog_entry(spec):
    fields = []
    for column in spec.model.__table__.columns:
        if column.name in SECRET_FIELDS:
            continue
        editable = column.name in spec.editable
        entry = {"name": column.name, "label": column.name.replace("_", " ").capitalize(), "type": field_type(column), "editable": editable,
                 "required": not column.nullable and column.default is None and column.server_default is None and not column.primary_key}
        if column.foreign_keys:
            entry["reference"] = next(iter(column.foreign_keys)).target_fullname.split(".")[0]
        if spec.key == "ecosystems" and column.name == "uaf_agreement_id":
            entry["type"], entry["reference"] = "reference", "agreements"
        if spec.key == "members" and column.name == "role":
            entry["options"] = ["user", "mod", "admin", "owner"]
        if spec.key == "app_settings" and column.name == "key":
            entry["options"] = sorted(SETTING_KEYS)
        fields.append(entry)
    if spec.category == "evidence":
        fields.append({"name": "archive_id", "label": "Archive ID to restore", "type": "text", "editable": True, "required": False})
    return {"key": spec.key, "label": spec.key.replace("_", " ").title(), "organization_scoped": "ecosystem_id" in spec.model.__table__.columns,
            "fields": fields, "actions": spec.actions, "listing_fields": [name for name in LIST_FIELDS if name in spec.model.__table__.columns], "category": spec.category}
