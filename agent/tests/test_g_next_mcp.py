"""G-Next: MCP agreement acts that would put an agreement in force wait for the owner's confirm (chat parity).

Separate module so an environment without the `mcp` package skips only this file. Contract:
src/neos_agent/agent/AGENTS.md "Confirmation of irreversible acts".
"""

from __future__ import annotations

import datetime as dt
import re
import uuid

import pytest

pytest.importorskip("mcp.server.fastmcp")

from sqlalchemy import func, select  # noqa: E402

from neos_agent import mcp_server  # noqa: E402
from neos_agent.api.agreements import CEREMONY_DENIED  # noqa: E402
from neos_agent.db.models import Agreement, AgreementCeremony, AgreementMemberConsent, User  # noqa: E402

from .test_g_next import HOUSE_RULES, OASIS_MEMBERS, PEOPLE, env  # noqa: E402,F401


@pytest.fixture
def acting(env, monkeypatch):
    who: dict = {}

    async def fake_caller(ctx):
        p = PEOPLE[who["key"]]
        return mcp_server.Caller(user=User(id=p.user_id, display_name=p.name), token=None)

    monkeypatch.setattr(mcp_server, "_caller", fake_caller)
    monkeypatch.setattr(mcp_server, "_db", lambda: env.db)
    return who


async def _agreement(env, *, status: str, evidence: int = 0, consented: tuple[str, ...] = ()) -> None:
    """House rules in `status`, with test evidence already on record and the named members' consent."""
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    async with env.db() as session:
        (await session.get(Agreement, HOUSE_RULES)).status = status
        for _ in range(evidence):
            session.add(AgreementCeremony(id=uuid.uuid4(), agreement_id=HOUSE_RULES, stage="test", outcome="evidence",
                                          evidence="The rules held for a month.", completed_at=now))
        for key in consented:
            session.add(AgreementMemberConsent(id=uuid.uuid4(), agreement_id=HOUSE_RULES, member_id=PEOPLE[key].member_id,
                                               agreement_version="1.0", attestation="I agree to the house rules.",
                                               attested_at=now))
        await session.commit()


async def _status(env) -> str:
    async with env.db() as session:
        return (await session.get(Agreement, HOUSE_RULES)).status


async def _count(env, model) -> int:
    async with env.db() as session:
        return await session.scalar(select(func.count()).select_from(model).where(model.agreement_id == HOUSE_RULES))


async def test_test_evidence_that_would_put_an_agreement_in_force_waits_for_confirm(env, acting):
    await _agreement(env, status="test")
    acting["key"] = "ben"
    before = await _count(env, AgreementCeremony)
    asked = await mcp_server.record_agreement_ceremony(str(HOUSE_RULES), "test", "Quiet all month", ctx=None)
    assert "goes into force" in asked["needs_confirmation"] and asked["status"] == "test"
    assert (await _status(env), await _count(env, AgreementCeremony)) == ("test", before)  # nothing written

    done = await mcp_server.record_agreement_ceremony(str(HOUSE_RULES), "test", "Quiet all month", ctx=None, confirm=True)
    assert (done["status"], done["auto_transitions"]) == ("active", ["test->active"])
    with pytest.raises(ValueError, match="only be recorded while the agreement is in advice"):  # REST's stage rule
        await mcp_server.record_agreement_ceremony(str(HOUSE_RULES), "advice", "Late advice", ctx=None)


async def test_only_the_consent_that_completes_the_cascade_into_force_waits_for_confirm(env, acting):
    await _agreement(env, status="consent", evidence=1,
                     consented=tuple(key for key in OASIS_MEMBERS if key not in ("ben", "cy")))
    acting["key"] = "ben"  # Cy is still outstanding, so Ben's consent completes nothing
    written = await mcp_server.attest_agreement_consent(str(HOUSE_RULES), "I agree to the house rules.", ctx=None)
    assert "needs_confirmation" not in written and written["status"] == "consent"

    acting["key"] = "cy"  # the last consent: consent -> test -> active with the evidence on record
    asked = await mcp_server.attest_agreement_consent(str(HOUSE_RULES), "I agree to the house rules.", ctx=None)
    assert "goes into force" in asked["needs_confirmation"]
    assert (await _status(env), await _count(env, AgreementMemberConsent)) == ("consent", len(OASIS_MEMBERS) - 1)
    done = await mcp_server.attest_agreement_consent(str(HOUSE_RULES), "I agree to the house rules.", ctx=None, confirm=True)
    assert done["status"] == "active"


async def test_a_ceremony_into_force_refuses_first_then_waits_for_confirm(env, acting):
    await _agreement(env, status="under_review", evidence=1)
    acting["key"] = "ben"  # not a ceremony steward: refused outright, never asked
    with pytest.raises(ValueError, match=re.escape(CEREMONY_DENIED)):
        await mcp_server.transition_agreement(str(HOUSE_RULES), "active", "Reviewed and kept", ctx=None)

    acting["key"] = "ari"
    asked = await mcp_server.transition_agreement(str(HOUSE_RULES), "active", "Reviewed and kept", ctx=None)
    assert "binding for every member of Oasis" in asked["needs_confirmation"]
    assert await _status(env) == "under_review"
    done = await mcp_server.transition_agreement(str(HOUSE_RULES), "active", "Reviewed and kept", ctx=None, confirm=True)
    assert done["status"] == "active"
