"""G-Care flows: conflict cases, repair follow-up and governance health audits.

Drives the real conflicts and safeguards blueprints over in-memory SQLite, acting as
different members. Rules under test: src/neos_agent/api/AGENTS.md "Conflict care" and
"Audits"; each owner default is a constant in api/policy.py and has a test that goes red
if flipped.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api import policy
from neos_agent.api.conflicts import REPAIR_NEEDS_CONFIRMATION, conflicts_api_bp, next_checkin
from neos_agent.api.errors import register_api_errors
from neos_agent.api.safeguards import safeguards_api_bp
from neos_agent.db.models import Base, ConflictCase, Ecosystem, Member, RepairAgreementRecord, User

ECO = uuid.UUID("0000000c-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000000c-0000-0000-0000-000000000002")


@dataclass(frozen=True)
class Person:
    user_id: uuid.UUID
    member_id: uuid.UUID
    name: str
    role: str


def _person(key: str, name: str, role: str) -> Person:
    return Person(
        user_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"care.{key}.user"),
        member_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"care.{key}.member"),
        name=name,
        role=role,
    )


PEOPLE = {
    "ada": _person("ada", "Ada", "user"),  # reports the case
    "ben": _person("ben", "Ben", "user"),  # unrelated member
    "cy": _person("cy", "Cy", "user"),  # becomes facilitator
    "dee": _person("dee", "Dee", "user"),  # named party
    "mo": _person("mo", "Mo", "mod"),  # ecosystem steward
}
OLU = _person("olu", "Olu", "user")  # member of River only


async def _seed(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
    session.add(Ecosystem(id=RIVER, name="River House", status="active"))
    for p in (*PEOPLE.values(), OLU):
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for key, p in PEOPLE.items():
        session.add(Member(
            id=p.member_id, ecosystem_id=ECO, user_id=p.user_id, member_id=f"MEM-{key.upper()}",
            display_name=p.name, current_status="active", role=p.role,
        ))
    session.add(Member(
        id=OLU.member_id, ecosystem_id=RIVER, user_id=OLU.user_id, member_id="MEM-OLU",
        display_name=OLU.name, current_status="active", role=OLU.role,
    ))
    await session.commit()


def _create_app() -> Sanic:
    app = Sanic(f"test-care-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        p, home = (OLU, RIVER) if who == "olu" else (PEOPLE[who], ECO)
        request.ctx.member = Member(
            id=p.member_id, ecosystem_id=home, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role=p.role,
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [home]
        request.ctx.authorized_ecosystem_ids = [home]

    app.blueprint(conflicts_api_bp)
    app.blueprint(safeguards_api_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await _seed(session)
    app = _create_app()
    app.ctx.db = session_factory
    yield SimpleNamespace(app=app, db=session_factory)
    await engine.dispose()


async def _call(app: Sanic, method: str, who: str, url: str, **kwargs):
    _, resp = await getattr(app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    return resp


async def _report(app: Sanic, who: str = "ada", **fields) -> dict:
    body = {"ecosystem_id": str(ECO), "title": "Dishes left again", "description": "Third time this week.",
            "party_member_ids": [str(PEOPLE["dee"].member_id)], **fields}
    resp = await _call(app, "post", who, "/api/v1/conflicts", json=body)
    assert resp.status == 201, resp.text
    return resp.json


# ---------------------------------------------------------------------------
# Reporting and next step
# ---------------------------------------------------------------------------


async def test_reporter_is_the_caller_and_the_case_says_who_picks_it_up(env):
    spoofed = str(PEOPLE["ben"].member_id)
    case = await _report(env.app, reporter_id=spoofed)
    assert case["reporter_id"] == str(PEOPLE["ada"].member_id)
    assert case["reporter_name"] == "Ada"
    assert case["status"] == "reported" and case["stage"] == "Reported"
    assert "steward" in case["next_step"] and "48" not in case["next_step"]
    assert case["decided_by"] == "A steward of this ecosystem"

    # Reporting needs a membership in that ecosystem.
    outsider = await _call(env.app, "post", "olu", "/api/v1/conflicts", json={"ecosystem_id": str(ECO), "title": "x"})
    assert outsider.status == 403


# ---------------------------------------------------------------------------
# Who can read a harm report
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("viewer, status", [
    ("ada", 200),  # the reporter
    ("mo", 200),  # triage steward
    ("dee", 200),  # named party
    ("ben", 404),  # another member of the ecosystem
    ("olu", 404),  # a member of another ecosystem
])
async def test_harm_reports_are_visible_to_parties_and_triage_stewards_only(env, viewer, status):
    case = await _report(env.app)
    detail = await _call(env.app, "get", viewer, f"/api/v1/conflicts/{case['id']}")
    assert detail.status == status, detail.text
    listed = await _call(env.app, "get", viewer, "/api/v1/conflicts")
    assert listed.status == 200
    assert (case["id"] in [item["id"] for item in listed.json["items"]]) == (status == 200)
    assert listed.json["total"] == (1 if status == 200 else 0)


async def test_assigned_facilitator_can_read_and_move_the_case(env):
    case = await _report(env.app)
    url = f"/api/v1/conflicts/{case['id']}"
    assert (await _call(env.app, "get", "cy", url)).status == 404

    assign = await _call(env.app, "put", "mo", url, json={"status": "triaged", "tier": 2, "facilitator_id": str(PEOPLE["cy"].member_id)})
    assert assign.status == 200, assign.text
    assert assign.json["facilitator_name"] == "Cy"

    mine = await _call(env.app, "get", "cy", url)
    assert mine.status == 200 and mine.json["caller_can_triage"] is True
    assert mine.json["allowed_next"] == ["in_progress", "resolved", "closed"]
    assert "mediation" in mine.json["next_step"] and "Cy" in mine.json["next_step"]
    started = await _call(env.app, "put", "cy", url, json={"status": "in_progress"})
    assert started.status == 200 and started.json["status"] == "in_progress"


async def test_facilitator_must_be_an_active_member_who_is_not_a_party(env):
    case = await _report(env.app)
    url = f"/api/v1/conflicts/{case['id']}"
    for who in ("dee", "olu"):
        member_id = (PEOPLE.get(who) or OLU).member_id
        resp = await _call(env.app, "put", "mo", url, json={"facilitator_id": str(member_id)})
        assert resp.status == 400, (who, resp.text)


async def test_party_access_follows_member_id_never_a_display_name(env):
    case = await _report(env.app)
    url = f"/api/v1/conflicts/{case['id']}"
    async with env.db() as session:  # Ben renames himself to the party's name
        ben = await session.get(Member, PEOPLE["ben"].member_id)
        ben.display_name = "Dee"
        await session.commit()
    assert (await _call(env.app, "get", "ben", url)).status == 404
    assert (await _call(env.app, "get", "dee", url)).status == 200  # the real party, by id
    assert (await _call(env.app, "get", "dee", url)).json["party_names"] == ["Dee"]


async def test_party_ids_must_belong_to_the_ecosystem(env):
    body = {"ecosystem_id": str(ECO), "title": "x", "party_member_ids": [str(OLU.member_id)]}
    resp = await _call(env.app, "post", "ada", "/api/v1/conflicts", json=body)
    assert resp.status == 400
    case = await _report(env.app)
    edit = await _call(env.app, "put", "mo", f"/api/v1/conflicts/{case['id']}", json={"party_member_ids": [str(OLU.member_id)]})
    assert edit.status == 400


# ---------------------------------------------------------------------------
# Who can triage and move a case
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("actor, body, expected", [
    ("mo", {"status": "triaged", "tier": 1}, 200),  # steward triages
    ("ada", {"status": "triaged"}, 403),  # the reporter cannot triage their own case
    ("ada", {"title": "Dishes left, again"}, 200),  # but may correct their text
    ("ada", {"tier": 3}, 403),
    ("ada", {"status": "closed"}, 200),  # or withdraw it
    ("dee", {"status": "closed"}, 403),  # a party may read but not decide
])
async def test_who_can_change_a_case(env, actor, body, expected):
    case = await _report(env.app)
    resp = await _call(env.app, "put", actor, f"/api/v1/conflicts/{case['id']}", json=body)
    assert resp.status == expected, resp.text


async def test_a_steward_named_as_a_party_cannot_triage_their_own_case(env):
    case = await _report(env.app, party_member_ids=[str(PEOPLE["mo"].member_id)])
    url = f"/api/v1/conflicts/{case['id']}"
    assert (await _call(env.app, "get", "mo", url)).status == 200  # a party reads it
    assert (await _call(env.app, "put", "mo", url, json={"status": "triaged"})).status == 403


async def test_case_follows_its_lifecycle_and_resolving_needs_a_summary(env):
    case = await _report(env.app)
    url = f"/api/v1/conflicts/{case['id']}"
    skipped = await _call(env.app, "put", "mo", url, json={"status": "resolved", "resolution_summary": "ok"})
    assert skipped.status == 409 and skipped.json["allowed"] == ["triaged", "closed"]

    assert (await _call(env.app, "put", "mo", url, json={"status": "triaged"})).status == 200
    assert (await _call(env.app, "put", "mo", url, json={"status": "resolved"})).status == 400
    done = await _call(env.app, "put", "mo", url, json={"status": "resolved", "resolution_summary": "Rota agreed."})
    assert done.status == 200
    assert done.json["resolved_date"] == dt.date.today().isoformat()
    assert "closes the case" in done.json["next_step"]


async def test_a_case_with_an_unrecognized_status_asks_a_steward_instead_of_reading_closed(env):
    """Statuses older writers left behind (r6c1e8a4f2d7 normalizes the known ones) stay workable."""
    case = await _report(env.app)
    async with env.db() as session:
        (await session.get(ConflictCase, uuid.UUID(case["id"]))).status = "paused"
        await session.commit()
    url = f"/api/v1/conflicts/{case['id']}"
    stray = await _call(env.app, "get", "mo", url)
    assert (stray.json["stage"], stray.json["decided_by"]) == ("Needs a steward to review", "A steward of this ecosystem")
    assert stray.json["allowed_next"] == ["triaged", "in_progress", "resolved", "closed"]
    listed = await _call(env.app, "get", "ada", "/api/v1/conflicts")
    assert [item["stage"] for item in listed.json["items"]] == ["Needs a steward to review"]
    assert (await _call(env.app, "put", "ada", url, json={"status": "in_progress"})).status == 403  # reporter
    moved = await _call(env.app, "put", "mo", url, json={"status": "in_progress"})
    assert (moved.status, moved.json["stage"]) == (200, "In progress")


# ---------------------------------------------------------------------------
# Owner decisions: each is a constant that changes behaviour
# ---------------------------------------------------------------------------


async def test_owner_default_triage_role_is_one_constant(env, monkeypatch):
    case = await _report(env.app)
    url = f"/api/v1/conflicts/{case['id']}"
    monkeypatch.setattr(policy, "CONFLICT_TRIAGE_MIN_ROLE", "admin")
    assert (await _call(env.app, "put", "mo", url, json={"status": "triaged"})).status == 404  # a mod no longer sees the case
    monkeypatch.setattr(policy, "CONFLICT_TRIAGE_MIN_ROLE", "mod")
    assert (await _call(env.app, "put", "mo", url, json={"status": "triaged"})).status == 200


async def test_owner_default_parties_can_read_is_one_constant(env, monkeypatch):
    case = await _report(env.app)
    monkeypatch.setattr(policy, "CONFLICT_PARTIES_CAN_VIEW", False)
    assert (await _call(env.app, "get", "dee", f"/api/v1/conflicts/{case['id']}")).status == 404


# ---------------------------------------------------------------------------
# Repair follow-up
# ---------------------------------------------------------------------------


async def _case_with_repair(app: Sanic) -> tuple[str, dict]:
    case = await _report(app)
    url = f"/api/v1/conflicts/{case['id']}"
    assert (await _call(app, "put", "mo", url, json={"status": "triaged"})).status == 200
    resp = await _call(app, "post", "mo", f"{url}/repair", json={"title": "Dish rota", "commitments": ["Wash after dinner"]})
    assert resp.status == 201, resp.text
    return case["id"], resp.json


async def test_repair_check_ins_are_scheduled_and_fulfilling_needs_confirmation(env):
    case_id, repair = await _case_with_repair(env.app)
    today = dt.date.today()
    assert [repair[f"checkin_{d}_date"] for d in (30, 60, 90)] == [(today + dt.timedelta(days=d)).isoformat() for d in (30, 60, 90)]
    assert repair["next_checkin_date"] == repair["checkin_30_date"] and repair["next_checkin_overdue"] is False

    url = f"/api/v1/conflicts/{case_id}/repair/{repair['id']}"
    note = await _call(env.app, "put", "mo", url, json={"checkin_30_notes": "Going well."})
    assert note.json["next_checkin_date"] == repair["checkin_60_date"]

    unconfirmed = await _call(env.app, "put", "mo", url, json={"status": "fulfilled"})
    assert unconfirmed.status == 400 and unconfirmed.json["error"] == REPAIR_NEEDS_CONFIRMATION

    fulfilled = await _call(env.app, "put", "mo", url, json={"status": "fulfilled", "confirmed_by_parties": True})
    assert fulfilled.status == 200
    assert fulfilled.json["completed_date"] == today.isoformat()
    assert fulfilled.json["next_checkin_date"] is None


async def test_only_triage_authority_records_repair(env):
    case_id, repair = await _case_with_repair(env.app)
    url = f"/api/v1/conflicts/{case_id}/repair/{repair['id']}"
    assert (await _call(env.app, "put", "ada", url, json={"checkin_30_notes": "x"})).status == 403
    assert (await _call(env.app, "post", "ada", f"/api/v1/conflicts/{case_id}/repair", json={"title": "x"})).status == 403
    assert (await _call(env.app, "put", "ben", url, json={"checkin_30_notes": "x"})).status == 404


def test_overdue_check_in_is_the_first_unnoted_scheduled_date():
    today = dt.date(2026, 11, 1)
    repair = RepairAgreementRecord(
        status="active", checkin_30_date=dt.date(2026, 10, 1), checkin_30_notes="done",
        checkin_60_date=dt.date(2026, 10, 25), checkin_90_date=dt.date(2027, 1, 1),
    )
    assert next_checkin(repair, today) == (dt.date(2026, 10, 25), True)
    repair.checkin_60_notes = "ok"
    assert next_checkin(repair, today) == (dt.date(2027, 1, 1), False)


# ---------------------------------------------------------------------------
# Audits a human can finish
# ---------------------------------------------------------------------------

# G-Maint: publishing needs every indicator that has data rated; here stewards exist (GHI-05) and GHI-08 is a count.
RATED = [
    {"indicator_id": "GHI-01", "indicator_name": "Proposal Authorship Diversity", "status": "healthy"},
    {"indicator_id": "GHI-02", "indicator_name": "Approval Rate by Role", "status": "warning"},
    {"indicator_id": "GHI-05", "indicator_name": "Leadership tenure", "status": "healthy"},
    {"indicator_id": "GHI-08", "indicator_name": "Cross-unit engagement", "status": "warning"},
]


async def _start_audit(app: Sanic, who: str = "ben", **fields) -> dict:
    resp = await _call(app, "post", who, "/api/v1/safeguards/audits", json={"ecosystem_id": str(ECO), **fields})
    assert resp.status == 201, resp.text
    return resp.json


async def test_a_member_audits_and_publishing_sets_the_score(env):
    draft = await _start_audit(env.app, audit_scope="indicators")
    assert draft["auditor"] == "Ben" and draft["auditor_ids"] == [str(PEOPLE["ben"].member_id)]
    assert draft["findings"] is None and draft["caller_can_edit"] is True  # no permanent "AI analysis pending"

    summary = (await _call(env.app, "get", "ben", "/api/v1/safeguards")).json
    assert summary["health_score"] is None  # a draft never sets the score
    assert [a["id"] for a in summary["recent_audits"]] == [draft["id"]]

    url = f"/api/v1/safeguards/audits/{draft['id']}"
    assert (await _call(env.app, "post", "ben", f"{url}/publish")).status == 400  # nothing rated yet
    edited = await _call(env.app, "put", "ben", url, json={"indicator_scores": RATED, "findings": "Mixed."})
    assert edited.status == 200 and edited.json["findings"] == "Mixed."

    published = await _call(env.app, "post", "ben", f"{url}/publish")
    assert published.status == 200, published.text
    assert published.json["status"] == "completed" and published.json["overall_health_score"] == 75
    assert published.json["caller_can_edit"] is False

    summary = (await _call(env.app, "get", "ben", "/api/v1/safeguards")).json
    assert summary["health_score"] == 75
    assert (await _call(env.app, "put", "ben", url, json={"findings": "Changed"})).status == 409


@pytest.mark.parametrize("actor, expected", [("ben", 200), ("mo", 403), ("ada", 403), ("olu", 404)])
async def test_only_the_recording_auditor_can_edit_or_publish(env, actor, expected):
    draft = await _start_audit(env.app, indicator_scores=RATED)
    url = f"/api/v1/safeguards/audits/{draft['id']}"
    assert (await _call(env.app, "put", actor, url, json={"findings": "Mine now"})).status == expected
    assert (await _call(env.app, "post", actor, f"{url}/publish")).status == expected
