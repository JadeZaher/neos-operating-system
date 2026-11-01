"""Tests for the 14 NEOS governance tools.

All tests use the ``seeded_db`` fixture from conftest.py which provides:
- 1 ecosystem (OmniOne)
- 3 active members: Lani (steward), Kai (builder), Manu (townhall)
- 2 agreements: AGR-SHUR-2026-001 (active), AGR-GARD-2026-002 (draft)
- 1 domain: SHUR-KITCHEN (steward=Lani, 2 domain elements)
- 1 proposal: PROP-2026-001 (advice phase, consent mode)
"""

from __future__ import annotations

import uuid

from neos_agent.services.act_gates import OBJECTION_REASON_REQUIRED, proposal_gate_status
from neos_agent.agent.governance_tools import (
    check_authority,
    check_quorum,
    create_agreement_draft,
    create_decision_record,
    create_proposal,
    execute_tool,
    get_active_members,
    get_agreement,
    get_domain,
    get_tool_definitions,
    record_advice,
    record_consent_position,
    search_agreements,
    search_precedents,
    update_agreement_status,
)

# conftest seeds these users behind Kai's, Lani's and Manu's member rows (all role "user").
USER_KAI_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.kai")
USER_LANI_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.lani")
USER_MANU_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.manu")


async def _promote(db, user_id: uuid.UUID, role: str) -> None:
    """Give a seeded member an ecosystem role tier (conftest seeds every member as "user")."""
    from neos_agent.db.models import Member
    from sqlalchemy import select

    member = await db.scalar(select(Member).where(Member.user_id == user_id))
    member.role = role
    await db.flush()


# ===================================================================
# 1. search_agreements
# ===================================================================


class TestSearchAgreements:
    async def test_search_agreements_by_status(self, seeded_db):
        """Finds the active agreement when filtering by status='active'."""
        result = await search_agreements({"status": "active"}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] >= 1
        ids = [a["agreement_id"] for a in result["data"]["agreements"]]
        assert "AGR-SHUR-2026-001" in ids

    async def test_search_agreements_empty(self, seeded_db):
        """Returns helpful message when no agreements match."""
        result = await search_agreements({"status": "archived"}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert "No agreements found" in result["data"]["message"]


# ===================================================================
# 2. get_agreement
# ===================================================================


class TestGetAgreement:
    async def test_get_agreement_exists(self, seeded_db):
        """Returns all fields for an existing agreement."""
        result = await get_agreement({"agreement_id": "AGR-SHUR-2026-001"}, seeded_db)
        assert result["success"] is True
        data = result["data"]
        assert data["agreement_id"] == "AGR-SHUR-2026-001"
        assert data["title"] == "SHUR Kitchen Scheduling Agreement"
        assert data["type"] == "space"
        assert data["status"] == "active"
        assert data["proposer"] == "Kai"
        # Consent progress comes from the engine: three participating members, none has consented yet.
        assert (data["gates"]["consent"]["consented"], data["gates"]["consent"]["outstanding"]) == (0, 3)
        assert data["link"] == f"/agreements/{data['id']}"

    async def test_get_agreement_not_found(self, seeded_db):
        """Returns error for non-existent agreement."""
        result = await get_agreement({"agreement_id": "AGR-NOPE-9999-999"}, seeded_db)
        assert result["success"] is False
        assert "not found" in result["error"]


# ===================================================================
# 3. create_agreement_draft
# ===================================================================


class TestCreateAgreementDraft:
    async def test_create_agreement_draft(self, seeded_db, ecosystem_ids):
        """Creates a draft agreement with generated ID and correct defaults."""
        result = await create_agreement_draft(
            {
                "title": "Yoga Studio Hours",
                "type": "space",
                "proposer": "Kai",
                "domain": "Wellness",
                "text": "Yoga studio is open weekdays 6am-9pm, weekends 8am-8pm.",
                "affected_parties": ["Lani", "Manu"],
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
            caller_user_id=USER_KAI_ID,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["agreement_id"].startswith("AGR-WELL-")
        assert data["status"] == "draft"
        assert data["version"] == "0.1"
        assert data["review_date"] is not None

    async def test_create_agreement_draft_invalid_proposer(self, seeded_db, ecosystem_ids):
        """Rejects creation when proposer is not an active member."""
        result = await create_agreement_draft(
            {
                "title": "Ghost Agreement",
                "type": "space",
                "proposer": "NonExistentPerson",
                "domain": "Phantom",
                "text": "Body text for ghost agreement.",
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
            caller_user_id=USER_KAI_ID,
        )
        assert result["success"] is False
        assert "not an active member" in result["error"]


# ===================================================================
# 4. update_agreement_status
# ===================================================================


class TestUpdateAgreementStatus:
    async def test_update_agreement_status_valid(self, seeded_db):
        """An active admin conducts draft -> advice: a ceremony and a snapshot, the version (consent's anchor) unchanged."""
        from neos_agent.db.models import Agreement, AgreementCeremony, AgreementVersion
        from sqlalchemy import select

        await _promote(seeded_db, USER_LANI_ID, "admin")
        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "advice", "evidence": "Advice round opened at the circle"},
            seeded_db,
            caller_user_id=USER_LANI_ID,
        )
        assert result["success"] is True, result
        data = result["data"]
        assert (data["previous_status"], data["new_status"], data["version"]) == ("draft", "advice", "0.1")
        agreement = await seeded_db.scalar(select(Agreement).where(Agreement.agreement_id == "AGR-GARD-2026-002"))
        ceremony = await seeded_db.scalar(select(AgreementCeremony).where(AgreementCeremony.agreement_id == agreement.id))
        snapshot = await seeded_db.scalar(select(AgreementVersion).where(AgreementVersion.agreement_id == agreement.id))
        assert (ceremony.stage, ceremony.evidence) == ("advice", "Advice round opened at the circle")
        assert snapshot.change_reason == "Status transition: draft -> advice"

    async def test_update_agreement_status_requires_ceremony_evidence(self, seeded_db):
        """Forward ceremonies need documented evidence, as REST and MCP."""
        await _promote(seeded_db, USER_LANI_ID, "admin")
        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "advice"},
            seeded_db,
            caller_user_id=USER_LANI_ID,
        )
        assert result == {"success": False, "error": "Documented evidence is required for the advice ceremony"}
        stored = (await get_agreement({"agreement_id": "AGR-GARD-2026-002"}, seeded_db))["data"]
        assert stored["status"] == "draft"

    async def test_update_agreement_status_refuses_a_plain_member(self, seeded_db):
        """Only an active admin or owner conducts agreement ceremonies (REST rule)."""
        from neos_agent.api.agreements import CEREMONY_DENIED

        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "advice"},
            seeded_db,
            caller_user_id=USER_KAI_ID,
        )
        assert result == {"success": False, "error": CEREMONY_DENIED}
        stored = (await get_agreement({"agreement_id": "AGR-GARD-2026-002"}, seeded_db))["data"]
        assert stored["status"] == "draft"

    async def test_update_agreement_status_invalid(self, seeded_db):
        """Rejects invalid transition draft -> active with explanation."""
        await _promote(seeded_db, USER_LANI_ID, "admin")
        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "active", "evidence": "Skipping ahead to adoption"},
            seeded_db,
            caller_user_id=USER_LANI_ID,
        )
        assert result == {"success": False, "error": "Invalid transition: draft -> active. Allowed: advice."}


# ===================================================================
# 5. check_authority
# ===================================================================


class TestCheckAuthority:
    async def test_domain_stewardship_follows_steward_id(self, seeded_db):
        """policy.is_domain_steward: Lani (steward_id) stewards SHUR-KITCHEN, Kai does not."""
        for member, expected in (("Lani", True), ("Kai", False)):
            result = await check_authority({"member": member, "domain": "SHUR-KITCHEN"}, seeded_db)
            assert result["success"] is True, result
            assert result["data"]["is_domain_steward"] is expected, member


# ===================================================================
# 6. get_member_roles — tested implicitly via check_authority
# ===================================================================


# ===================================================================
# 7. create_proposal
# ===================================================================


class TestCreateProposal:
    async def test_create_proposal(self, seeded_db, ecosystem_ids):
        """Creates a draft authored by the caller, with generated ID and auto-set consent mode."""
        result = await create_proposal(
            {
                "title": "Expand kitchen hours to 10pm",
                "type": "agreement",
                "affected_domain": "SHUR-KITCHEN",
                "proposed_change": "Extend evening kitchen hours from 9pm to 10pm.",
                "rationale": "Community demand and noise assessment confirmed feasibility.",
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
            caller_user_id=USER_KAI_ID,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["proposal_id"].startswith("PROP-")
        assert data["consent_mode"] == "consent"
        assert data["status"] == "draft"
        assert data["proposer"] == "Kai"


# ===================================================================
# 8. record_advice
# ===================================================================


class TestRecordAdvice:
    async def test_record_advice(self, seeded_db):
        """Records advice entry with timestamp for proposal in advice phase."""
        result = await record_advice(
            {
                "proposal_id": "PROP-2026-001",
                "advice_text": "Consider noise impact on nearby sleeping areas.",
            },
            seeded_db,
            caller_user_id=USER_LANI_ID,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["advisor"] == "Lani"
        assert data["recorded_date"] is not None


# ===================================================================
# 9. record_consent_position
# ===================================================================


class TestRecordConsentPosition:
    async def test_record_consent_objection_requires_reason(self, seeded_db):
        """Rejects objection without a reason."""
        # First move proposal to consent phase
        from neos_agent.db.models import Proposal
        from sqlalchemy import select

        stmt = select(Proposal).where(Proposal.proposal_id == "PROP-2026-001")
        res = await seeded_db.execute(stmt)
        prop = res.scalars().first()
        prop.status = "consent"
        await seeded_db.flush()

        result = await record_consent_position(
            {
                "proposal_id": "PROP-2026-001",
                "position": "objection",
                # no reason provided
            },
            seeded_db,
            caller_user_id=USER_MANU_ID,
        )
        assert result == {"success": False, "error": OBJECTION_REASON_REQUIRED}

    async def test_record_consent_position_valid(self, seeded_db):
        """Records a valid consent position."""
        # Move to consent phase
        from neos_agent.db.models import Proposal
        from sqlalchemy import select

        stmt = select(Proposal).where(Proposal.proposal_id == "PROP-2026-001")
        res = await seeded_db.execute(stmt)
        prop = res.scalars().first()
        prop.status = "consent"
        await seeded_db.flush()

        result = await record_consent_position(
            {
                "proposal_id": "PROP-2026-001",
                "position": "consent",
            },
            seeded_db,
            caller_user_id=USER_KAI_ID,
        )
        assert result["success"] is True
        assert (result["data"]["participant"], result["data"]["position"]) == ("Kai", "consent")


# ===================================================================
# 10. check_quorum
# ===================================================================


class TestCheckQuorum:
    async def test_check_quorum_reports_the_engines_quorum(self, seeded_db):
        """The quorum is the proposal's declared one (3), not a share of the members (2 of 3 would pass)."""
        # Move proposal to consent phase and add a consent record with 2 participants
        from neos_agent.db.models import Proposal, ConsentRecord, ConsentParticipant
        from sqlalchemy import select
        import uuid as _uuid

        stmt = select(Proposal).where(Proposal.proposal_id == "PROP-2026-001")
        res = await seeded_db.execute(stmt)
        prop = res.scalars().first()
        prop.status = "consent"
        prop.act_policy = {"min_advice_rounds": 1, "consent_required": True, "consent_quorum": 3}
        await seeded_db.flush()

        cr = ConsentRecord(
            id=_uuid.uuid4(),
            proposal_id=prop.id,
            consent_mode="consent",
        )
        seeded_db.add(cr)
        await seeded_db.flush()

        # Add 2 participants (2/3 of 3 = 2)
        for name in ["Kai", "Lani"]:
            cp = ConsentParticipant(
                id=_uuid.uuid4(),
                consent_record_id=cr.id,
                name=name,
                position="consent",
                round=1,
            )
            seeded_db.add(cp)
        await seeded_db.flush()

        result = await check_quorum({"proposal_id": "PROP-2026-001"}, seeded_db)
        assert result["success"] is True
        data = result["data"]
        engine = (await proposal_gate_status(seeded_db, prop))["consent"]
        assert (data["quorum"], data["positions"]) == (engine["quorum"], engine["positions"]) == (3, 2)
        assert data["quorum_met"] is False


# ===================================================================
# 11. create_decision_record
# ===================================================================


class TestCreateDecisionRecord:
    async def test_create_decision_record(self, seeded_db, ecosystem_ids):
        """A steward records a decision with auto-generated ID and tags."""
        await _promote(seeded_db, USER_LANI_ID, "mod")
        result = await create_decision_record(
            {
                "holding": "Evening kitchen hours extended to 10pm.",
                "rationale": "Community demand and noise assessment confirmed feasibility.",
                "source_skill": "consent-process",
                "source_layer": 3,
                "domain": "SHUR-KITCHEN",
                "tags": ["kitchen", "scheduling", "evening"],
                "recorder": "Manu",
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
            caller_user_id=USER_LANI_ID,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["record_id"].startswith("DR-")
        assert data["source_skill"] == "consent-process"
        assert data["source_layer"] == 3
        assert "kitchen" in data["tags"]


# ===================================================================
# 12. search_precedents
# ===================================================================


class TestSearchPrecedents:
    async def test_search_precedents_by_domain(self, seeded_db, ecosystem_ids):
        """Finds decision records matching a domain filter."""
        # First create a record to search for
        await _promote(seeded_db, USER_LANI_ID, "mod")
        await create_decision_record(
            {
                "holding": "Kitchen hours set to 6am-9pm.",
                "rationale": "Aligns with community routines and noise ordinances.",
                "domain": "SHUR-KITCHEN",
                "tags": ["kitchen"],
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
            caller_user_id=USER_LANI_ID,
        )
        await seeded_db.flush()

        result = await search_precedents({"domain": "SHUR"}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] >= 1
        assert any(
            r["domain"] == "SHUR-KITCHEN" for r in result["data"]["records"]
        )


# ===================================================================
# 13. get_domain
# ===================================================================


class TestGetDomain:
    async def test_get_domain(self, seeded_db):
        """Returns full domain with S3 elements and domain elements."""
        result = await get_domain({"domain_id": "SHUR-KITCHEN"}, seeded_db)
        assert result["success"] is True
        data = result["data"]
        assert data["name"] == "SHUR-KITCHEN"  # no name and no "Name - " purpose: the key is the label
        assert data["steward"] == "Lani"
        assert data["purpose"] == "Community kitchen operations and scheduling"
        assert data["elements"] is not None  # JSON blob
        assert len(data["domain_elements"]) == 2  # two DomainElement rows

    async def test_get_domain_not_found(self, seeded_db):
        """Returns error for non-existent domain."""
        result = await get_domain({"domain_id": "NOPE"}, seeded_db)
        assert result["success"] is False
        assert "not found" in result["error"]


# ===================================================================
# 14. get_active_members
# ===================================================================


class TestGetActiveMembers:
    async def test_get_active_members(self, seeded_db):
        """Returns all 3 active members."""
        result = await get_active_members({}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] == 3
        names = {m["display_name"] for m in result["data"]["members"]}
        assert names == {"Lani", "Kai", "Manu"}

    async def test_get_active_members_by_profile(self, seeded_db):
        """Filters by profile correctly."""
        result = await get_active_members({"profile": "builder"}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["members"][0]["display_name"] == "Kai"


# ===================================================================
# Registry & execute_tool
# ===================================================================


class TestToolRegistry:
    def test_tool_definitions_format(self):
        """get_tool_definitions returns Claude API format."""
        defs = get_tool_definitions()
        assert len(defs) == 52  # wave C: G-Maint get_governance_health; G-Onboard join_ecosystem, attest_agreement_consent, move_member; G-Exchange find_shares_needs, publish_share_need, respond_to_share_need, update_share_need_status, approve_collaboration, end_collaboration; FX-Exchange review_collaboration; FX-Maint respond_to_health_audit
        for d in defs:
            assert "name" in d
            assert "description" in d
            assert "input_schema" in d

    async def test_execute_tool_unknown(self, seeded_db):
        """execute_tool returns error for unknown tool name."""
        result = await execute_tool("nonexistent_tool", {}, seeded_db)
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    async def test_execute_tool_dispatch(self, seeded_db):
        """execute_tool dispatches correctly to get_active_members."""
        result = await execute_tool("get_active_members", {}, seeded_db)
        assert result["success"] is True
        assert result["data"]["count"] == 3


# ===================================================================
# 17 + 18: Emergency tools (added during L2 review of S2 patch)
# ===================================================================
#
# These tests cover the get_emergency_state (tool #17) and
# declare_emergency (tool #18) handlers which were modified by the
# half-open patch. The originally claimed "5 test additions" did not
# exist in the file -- they are added here.

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from neos_agent.agent.governance_tools import (
    declare_emergency,
    get_emergency_state,
)
from neos_agent.db.models import EmergencyState

# Mirror conftest.ECO_ID — conftest is not importable as a module under pytest's
# plugin loader, so the constant is redeclared here for tests that need to
# reference the seeded ecosystem by id.
ECO_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TestGetEmergencyState:
    """Tool 17 -- each ecosystem's state in the framework's words (NEOS.md: Normal, Crisis, Recovery)."""

    async def _with(self, db, **fields):
        db.add(EmergencyState(id=uuid.uuid4(), ecosystem_id=ECO_ID, declared_by="test", actions_log=[], **fields))
        await db.commit()
        result = await get_emergency_state({}, db)
        assert result["success"] is True, result
        [state] = result["data"]["ecosystems"]
        return state

    async def test_names_normal_and_crisis_as_the_framework_does(self, seeded_db):
        now = _naive_now()
        assert (await get_emergency_state({}, seeded_db))["data"]["ecosystems"][0]["state"] == "Normal"
        crisis = await self._with(seeded_db, state="open", declared_at=now, auto_revert_at=now + timedelta(days=7))
        assert crisis["state"] == "Crisis"
        assert crisis["link"].startswith("/emergency/")

    async def test_names_recovery_with_its_review_step(self, seeded_db):
        now = _naive_now()
        recovery = await self._with(
            seeded_db, state="half_open", declared_at=now - timedelta(days=5),
            half_open_entered_at=now - timedelta(days=1), auto_revert_at=now - timedelta(days=1),
        )
        assert recovery["state"] == "Recovery"
        assert "review" in recovery["next_step"].lower()


class TestDeclareEmergencyTool:
    """Tool 18 -- declares through api/emergency.declare: confirmed first, pending until a co-signer, one at a time."""

    async def test_asks_first_then_records_a_pending_declaration_in_the_callers_name(self, seeded_db):
        args = {"declared_by": "Kai", "reason": "Severe storm: kitchen flooded"}
        asked = await declare_emergency(args, seeded_db, caller_user_id=USER_LANI_ID)
        assert asked["success"] is False and "co-sign" in asked["needs_confirmation"]
        assert (await seeded_db.scalar(select(EmergencyState))) is None

        result = await declare_emergency({**args, "confirmed": True}, seeded_db, caller_user_id=USER_LANI_ID)
        assert result["success"] is True, result
        em = await seeded_db.scalar(select(EmergencyState).where(EmergencyState.id == uuid.UUID(result["data"]["id"])))
        assert (em.state, em.declared_by) == ("pending", "Lani")  # nothing changes until a second member co-signs

    async def test_refuses_while_an_emergency_is_in_recovery(self, seeded_db):
        now = _naive_now()
        seeded_db.add(EmergencyState(
            id=uuid.uuid4(), ecosystem_id=ECO_ID, state="half_open", declared_by="prior",
            declared_at=now - timedelta(days=10), half_open_entered_at=now - timedelta(days=2),
            auto_revert_at=now - timedelta(days=2), actions_log=[],
        ))
        await seeded_db.commit()
        result = await declare_emergency(
            {"reason": "Another storm", "confirmed": True}, seeded_db, caller_user_id=USER_LANI_ID,
        )
        assert result["success"] is False
        assert "already an emergency" in result["error"].lower()
