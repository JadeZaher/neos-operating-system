"""Tests for the 14 NEOS governance tools.

All tests use the ``seeded_db`` fixture from conftest.py which provides:
- 1 ecosystem (OmniOne)
- 3 active members: Lani (steward), Kai (builder), Manu (townhall)
- 2 agreements: AGR-SHUR-2026-001 (active), AGR-GARD-2026-002 (draft)
- 1 domain: SHUR-KITCHEN (steward=Lani, 2 domain elements)
- 1 proposal: PROP-2026-001 (advice phase, consent mode)
"""

from __future__ import annotations

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
        assert "ratification_records" in data

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
        )
        assert result["success"] is False
        assert "not an active member" in result["error"]


# ===================================================================
# 4. update_agreement_status
# ===================================================================


class TestUpdateAgreementStatus:
    async def test_update_agreement_status_valid(self, seeded_db):
        """Transitions draft -> advice correctly and bumps version."""
        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "advice"},
            seeded_db,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["previous_status"] == "draft"
        assert data["new_status"] == "advice"
        # Version should be bumped from 0.1 to 0.2
        assert data["version"] == "0.2"

    async def test_update_agreement_status_invalid(self, seeded_db):
        """Rejects invalid transition draft -> active with explanation."""
        result = await update_agreement_status(
            {"agreement_id": "AGR-GARD-2026-002", "new_status": "active"},
            seeded_db,
        )
        assert result["success"] is False
        assert "Cannot transition" in result["error"]
        assert "advice" in result["error"]  # valid target should be listed


# ===================================================================
# 5. check_authority
# ===================================================================


class TestCheckAuthority:
    async def test_check_authority_authorized(self, seeded_db):
        """Steward Lani is authorized in SHUR-KITCHEN domain."""
        result = await check_authority(
            {"member": "Lani", "domain": "SHUR-KITCHEN", "action": "update_schedule"},
            seeded_db,
        )
        assert result["success"] is True
        assert result["data"]["authorized"] is True
        assert result["data"]["role_source"] == "domain_steward"

    async def test_check_authority_unauthorized(self, seeded_db):
        """Kai has no stewardship in SHUR-KITCHEN."""
        result = await check_authority(
            {"member": "Kai", "domain": "SHUR-KITCHEN", "action": "update_schedule"},
            seeded_db,
        )
        assert result["success"] is True
        assert result["data"]["authorized"] is False
        assert "no stewardship role" in result["data"]["reason"].lower()


# ===================================================================
# 6. get_member_roles — tested implicitly via check_authority
# ===================================================================


# ===================================================================
# 7. create_proposal
# ===================================================================


class TestCreateProposal:
    async def test_create_proposal(self, seeded_db, ecosystem_ids):
        """Creates a proposal with generated ID and auto-set consent mode."""
        result = await create_proposal(
            {
                "title": "Expand kitchen hours to 10pm",
                "type": "agreement",
                "proposer": "Kai",
                "affected_domain": "SHUR-KITCHEN",
                "proposed_change": "Extend evening kitchen hours from 9pm to 10pm.",
                "rationale": "Community demand and noise assessment confirmed feasibility.",
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
        )
        assert result["success"] is True
        data = result["data"]
        assert data["proposal_id"].startswith("PROP-")
        assert data["consent_mode"] == "consent"
        assert data["status"] == "created"


# ===================================================================
# 8. record_advice
# ===================================================================


class TestRecordAdvice:
    async def test_record_advice(self, seeded_db):
        """Records advice entry with timestamp for proposal in advice phase."""
        result = await record_advice(
            {
                "proposal_id": "PROP-2026-001",
                "advisor": "Lani",
                "advice_text": "Consider noise impact on nearby sleeping areas.",
            },
            seeded_db,
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
                "participant": "Manu",
                "position": "objection",
                # no reason provided
            },
            seeded_db,
        )
        assert result["success"] is False
        assert "reason is required" in result["error"].lower()

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
                "participant": "Kai",
                "position": "consent",
            },
            seeded_db,
        )
        assert result["success"] is True
        assert result["data"]["position"] == "consent"


# ===================================================================
# 10. check_quorum
# ===================================================================


class TestCheckQuorum:
    async def test_check_quorum_consent_mode(self, seeded_db):
        """Checks 2/3 threshold for consent mode with 3 active members."""
        # Move proposal to consent phase and add a consent record with 2 participants
        from neos_agent.db.models import Proposal, ConsentRecord, ConsentParticipant
        from sqlalchemy import select
        import uuid as _uuid

        stmt = select(Proposal).where(Proposal.proposal_id == "PROP-2026-001")
        res = await seeded_db.execute(stmt)
        prop = res.scalars().first()
        prop.status = "consent"
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
        assert data["total_deciding_body"] == 3
        assert data["present_count"] == 2
        assert data["required_count"] == 2  # int(3 * 2/3) = 2
        assert data["quorum_met"] is True
        assert data["consent_mode"] == "consent"


# ===================================================================
# 11. create_decision_record
# ===================================================================


class TestCreateDecisionRecord:
    async def test_create_decision_record(self, seeded_db, ecosystem_ids):
        """Creates a decision record with auto-generated ID and tags."""
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
        await create_decision_record(
            {
                "holding": "Kitchen hours set to 6am-9pm.",
                "rationale": "Aligns with community routines and noise ordinances.",
                "domain": "SHUR-KITCHEN",
                "tags": ["kitchen"],
            },
            seeded_db,
            ecosystem_ids=ecosystem_ids,
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
        assert data["domain_id"] == "SHUR-KITCHEN"
        assert data["current_steward"] == "Lani"
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
        assert len(defs) == 29
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


class TestGetEmergencyState:
    """Tool 17 -- circuit-breaker introspection."""

    async def test_returns_closed_when_no_record(self, seeded_db):
        result = await get_emergency_state({}, seeded_db)
        assert result["success"] is True
        assert result["data"]["state"] == "closed"
        assert "CLOSED" in result["data"]["message"]

    async def test_returns_open_when_active(self, seeded_db):
        now = datetime.now(timezone.utc)
        em = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=ECO_ID,
            state="open",
            declared_by="test",
            declared_at=now,
            auto_revert_at=now + timedelta(days=30),
            actions_log=[],
        )
        seeded_db.add(em)
        await seeded_db.commit()
        result = await get_emergency_state({}, seeded_db)
        assert result["success"] is True
        assert result["data"]["state"] == "open"
        assert "OPEN" in result["data"]["message"]

    async def test_returns_half_open_state(self, seeded_db):
        now = datetime.now(timezone.utc)
        em = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=ECO_ID,
            state="half_open",
            declared_by="test",
            declared_at=now - timedelta(days=5),
            half_open_entered_at=now - timedelta(days=1),
            auto_revert_at=now + timedelta(days=29),
            actions_log=[],
        )
        seeded_db.add(em)
        await seeded_db.commit()
        result = await get_emergency_state({}, seeded_db)
        assert result["success"] is True
        assert result["data"]["state"] == "half_open"
        assert "HALF_OPEN" in result["data"]["message"]


class TestDeclareEmergencyTool:
    """Tool 18 -- declare_emergency invariant: only one active emergency
    per ecosystem at a time.
    """

    async def test_creates_open_state_with_30_day_auto_revert(self, seeded_db):
        args = dict()
        args["declared_by"] = "Lani"
        args["notes"] = "Severe storm: kitchen flooded"
        result = await declare_emergency(args, seeded_db)
        assert result["success"] is True
        assert result["data"]["state"] == "open"
        assert result["data"]["id"]
        # The auto_revert_at must be set 30 days out.
        em_id_str = result["data"]["id"]
        loaded = await seeded_db.execute(
            select(EmergencyState).where(EmergencyState.id == uuid.UUID(em_id_str))
        )
        em = loaded.scalar_one()
        assert em.state == "open"
        assert em.auto_revert_at is not None
        assert em.declared_at is not None
        delta = em.auto_revert_at - em.declared_at
        assert 29 <= delta.days <= 31

    async def test_rejects_when_emergency_already_open(self, seeded_db):
        now = datetime.now(timezone.utc)
        em = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=ECO_ID,
            state="open",
            declared_by="prior",
            declared_at=now - timedelta(hours=1),
            auto_revert_at=now + timedelta(days=29),
            actions_log=[],
        )
        seeded_db.add(em)
        await seeded_db.commit()
        args = dict()
        args["declared_by"] = "Lani"
        result = await declare_emergency(args, seeded_db)
        assert result["success"] is False
        assert "already active" in result["error"].lower()

    async def test_rejects_when_half_open_recovery_active(self, seeded_db):
        now = datetime.now(timezone.utc)
        em = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=ECO_ID,
            state="half_open",
            declared_by="prior",
            declared_at=now - timedelta(days=10),
            half_open_entered_at=now - timedelta(days=2),
            auto_revert_at=now + timedelta(days=28),
            actions_log=[],
        )
        seeded_db.add(em)
        await seeded_db.commit()
        args = dict()
        args["declared_by"] = "Lani"
        result = await declare_emergency(args, seeded_db)
        assert result["success"] is False
        assert "already active" in result["error"].lower()
