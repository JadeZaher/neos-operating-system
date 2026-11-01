"""G-Maint: agreement reviews, one date rule, governance health and its authority (uxqa/governance/wave-c.md).

Drives the real agreements, proposals, safeguards, compliance, domains and next-steps blueprints over in-memory
SQLite as different members, plus the assistant through `execute_tool`. Each owner decision or default of
2026-11-01 has a row here that goes red if it is flipped. Contracts: services/AGENTS.md and api/AGENTS.md
"Maintenance and health (G-Maint)".
"""

from __future__ import annotations

import datetime as dt
import os
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.agent.governance_tools import execute_tool
from neos_agent.api.agreements import agreements_api_bp
from neos_agent.api.compliance import compliance_api_bp
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.proposals import proposals_api_bp
from neos_agent.api.safeguards import safeguards_api_bp
from neos_agent.auth.ecosystem_scope import EcosystemScope
from neos_agent.db.models import (
    AdviceEntry, AdviceLog, Agreement, AgreementMemberConsent, AgreementVersion, Base, Collaboration,
    ComplianceSummary, ConsentParticipant, ConsentRecord, DecisionRecord, Domain, Ecosystem, EmergencyState,
    GovernanceHealthAudit, Member, MemberStatusTransition, Proposal, ReviewRecord, User,
)
from neos_agent.services import dates
from neos_agent.services.next_steps import ADVICE_DEADLINE_STEWARD_PROMPT, Clock, waiting_for

OASIS = uuid.UUID("0000000f-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000000f-0000-0000-0000-000000000002")
SOLO = uuid.UUID("0000000f-0000-0000-0000-000000000003")
FRESH = uuid.UUID("0000000f-0000-0000-0000-000000000004")  # FX-Maint: its founder is its only member
FERN = uuid.UUID("0000000f-0000-0000-0000-000000000005")  # FX-Maint: a founder and one plain member
NAMES = {OASIS: "Oasis", RIVER: "River House", SOLO: "Solo", FRESH: "Fresh Start", FERN: "Fern Valley"}
HOUSE = uuid.UUID("0000000f-0000-0000-0000-0000000000a1")
GARDEN = uuid.UUID("0000000f-0000-0000-0000-0000000000d1")
KITCHEN = uuid.UUID("0000000f-0000-0000-0000-0000000000d2")


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    rows: tuple  # (ecosystem, role, status) per membership
    profile: str | None = None  # a co_creator/builder row administers its ecosystem (policy.can_administer_ecosystem)

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-health.{self.key}.user")

    def member_id(self, ecosystem: uuid.UUID | None = None) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-health.{self.key}.{ecosystem or self.rows[0][0]}")

    @property
    def active(self) -> list[uuid.UUID]:
        return [eco for eco, _, status in self.rows if status == "active"]


PEOPLE = {p.key: p for p in (
    Person("ada", "Ada", ((OASIS, "user", "active"),)),
    Person("ben", "Ben", ((OASIS, "user", "active"),)),  # records audits
    Person("amara", "Amara", ((OASIS, "user", "active"),)),  # stewards the Garden domain
    Person("mo", "Mo", ((OASIS, "mod", "active"),)),  # ecosystem steward, stewards the Kitchen domain
    Person("ari", "Ari", ((OASIS, "admin", "active"),)),  # conducts agreement ceremonies
    Person("pia", "Pia", ((OASIS, "user", "pending_consent"),)),  # waits at the consent gate
    Person("olu", "Olu", ((RIVER, "user", "active"),)),  # another ecosystem only
    Person("dee", "Dee", ((OASIS, "user", "active"), (RIVER, "user", "active"))),  # member of both
    Person("sam", "Sam", ((SOLO, "mod", "active"),)),  # the only member of Solo
    Person("fran", "Fran", ((FRESH, "user", "active"),), profile="co_creator"),  # founded Fresh Start, alone there
    Person("finn", "Finn", ((FERN, "user", "active"),), profile="co_creator"),  # founded Fern Valley
    Person("fay", "Fay", ((FERN, "user", "active"),)),  # a plain member of Fern Valley
    Person("eve", "Eve", ((OASIS, "user", "exited"),)),  # left Oasis
)}
NOW = dates.utc_now()
TODAY = dates.aoe_today(NOW)


@pytest.fixture(autouse=True)
def _one_clock():
    """Every server date decision reads NOW (F16b: a run crossing 12:00 UTC no longer shifts aoe_today mid-module)."""
    with patch("neos_agent.services.dates.utc_now", return_value=NOW):
        yield


def _noon(day: dt.date) -> dt.datetime:
    """Noon UTC on `day`: by then the day before has ended everywhere (services/dates)."""
    return dt.datetime.combine(day, dt.time(12, 0))


async def _seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=eco, name=name, status="active") for eco, name in NAMES.items()])
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for p in PEOPLE.values():
        for eco, role, status in p.rows:
            session.add(Member(
                id=p.member_id(eco), ecosystem_id=eco, user_id=p.user_id, member_id=f"MEM-{p.key.upper()}-{NAMES[eco][:2]}",
                display_name=p.name, current_status=status, role=role, profile=p.profile,
                created_at=NOW - dt.timedelta(days=20) if p.key == "pia" else None,
            ))
    await session.flush()  # members before the domains that name them (PostgreSQL enforces the FK; SQLite does not)
    session.add(Agreement(id=HOUSE, ecosystem_id=OASIS, agreement_id="AGR-HOUSE", type="organizational",
                          title="House rules", version="1.0", status="active", text="Quiet after ten.",
                          review_date=TODAY + dt.timedelta(days=10)))
    session.add_all([
        Domain(id=GARDEN, ecosystem_id=OASIS, domain_id="DOM-GARDEN", name="Garden", status="active",
               steward_id=PEOPLE["amara"].member_id(), current_steward="Amara"),
        Domain(id=KITCHEN, ecosystem_id=OASIS, domain_id="DOM-KITCHEN", name="Kitchen", status="active",
               steward_id=PEOPLE["mo"].member_id(), current_steward="Mo"),
    ])
    await session.commit()


def _create_app(factory) -> Sanic:
    app = Sanic(f"test-g-health-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def sign_in(request):
        p = PEOPLE[request.headers["x-test-as"]]
        eco, role, status = p.rows[0]
        request.ctx.member = Member(id=p.member_id(eco), ecosystem_id=eco, user_id=p.user_id, member_id="MEM-AUTH",
                                    display_name=p.name, current_status=status, role=role, profile=p.profile)
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = list(p.active)  # main._load_ecosystems drops pending rows
        request.ctx.authorized_ecosystem_ids = list(p.active)
        request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems(
            [SimpleNamespace(id=e, name=NAMES[e]) for e in p.active], list(p.active))

    for blueprint in (agreements_api_bp, proposals_api_bp, safeguards_api_bp, compliance_api_bp, domains_api_bp,
                      next_steps_api_bp):
        app.blueprint(blueprint)
    return app


async def _build(url: str = "sqlite+aiosqlite://", **engine_args):
    """A fresh seeded schema: (engine, env with app and db)."""
    engine = create_async_engine(url, echo=False, **engine_args)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    return engine, SimpleNamespace(app=_create_app(factory), db=factory)


@pytest_asyncio.fixture
async def env():
    engine, world = await _build()
    yield world
    await engine.dispose()


async def _call(env, method: str, who: str, url: str, expect: int | None = None, **kwargs):
    _, resp = await getattr(env.app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    if expect is not None:
        assert resp.status == expect, (method, url, who, resp.status, resp.text)
    return resp


async def _add(env, *rows) -> None:
    async with env.db() as session:
        session.add_all(rows)
        await session.commit()


async def _agreement(env, *, status: str, review_date=None, sunset_date=None, title: str = "Kitchen rota",
                     type_: str = "organizational") -> uuid.UUID:
    agreement_id = uuid.uuid4()
    await _add(env, Agreement(id=agreement_id, ecosystem_id=OASIS, agreement_id=f"AGR-{agreement_id.hex[:6].upper()}",
                              type=type_, title=title, version="1.0", status=status, text="Who cooks when.",
                              review_date=review_date, sunset_date=sunset_date))
    return agreement_id


async def _row(env, model, record_id):
    async with env.db() as session:
        return await session.get(model, record_id)


async def _queue(env, who: str, now: dt.datetime | None = None) -> list[dict]:
    """The caller's queue at `now` (the REST route has no clock argument, so time travel calls the service)."""
    async with env.db() as session:
        return await waiting_for(session, PEOPLE[who].user_id, now=now)


def _actions(items: list[dict], record_id=None) -> dict[str, dict]:
    return {item["action"]: item for item in items if record_id is None or item["id"] == str(record_id)}


# ---------------------------------------------------------------------------
# C1: a review ends in renewal or sunset, with findings, a record and the next date
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_review_ends_in_renewal_with_findings_a_review_record_and_the_next_date(env):
    agreement = await _agreement(env, status="active", review_date=TODAY - dt.timedelta(days=3))
    status = f"/api/v1/agreements/{agreement}/status"

    await _call(env, "post", "ada", status, json={"status": "under_review"}, expect=403)
    await _call(env, "post", "mo", status, json={"status": "under_review"}, expect=403)  # a mod is not a ceremony steward
    await _call(env, "post", "ari", status, json={"status": "under_review"}, expect=200)

    refused = await _call(env, "post", "ari", status, json={"status": "active"}, expect=400)
    assert refused.json["code"] == "FINDINGS_REQUIRED"  # D1: the page sent nothing and got an unreadable 400
    past = await _call(env, "post", "ari", status, expect=400, json={
        "status": "active", "evidence": "Still fits how we cook.", "next_review_date": TODAY.isoformat()})
    assert past.json["code"] == "REVIEW_DATE_INVALID"

    renewed = (await _call(env, "post", "ari", status, expect=200, json={
        "status": "active", "evidence": "Members still rely on it; no change needed."})).json
    next_review = dates.add_months(TODAY, 24)  # organizational: REVIEW_INTERVAL_MONTHS
    assert (renewed["status"], renewed["review_date"], renewed["review_overdue"]) == ("active", next_review.isoformat(), False)

    review = (await _call(env, "get", "ada", f"/api/v1/agreements/{agreement}/history", expect=200)).json["reviews"][0]
    assert {key: review[key] for key in ("outcome", "findings", "conducted_by", "next_review_date", "review_type", "on_time")} == {
        "outcome": "renewed", "findings": "Members still rely on it; no change needed.", "conducted_by": "Ari",
        "next_review_date": next_review.isoformat(), "review_type": "scheduled", "on_time": False,
    }
    banner = (await _call(env, "get", "ari", f"/api/v1/explain/agreement/{agreement}", expect=200)).json
    assert (banner["due"], banner["overdue"]) == (next_review.isoformat(), False)

    # A chosen next date wins over the default.
    await _call(env, "post", "ari", status, json={"status": "under_review"}, expect=200)
    chosen = TODAY + dt.timedelta(days=100)
    again = (await _call(env, "post", "ari", status, expect=200, json={
        "status": "active", "evidence": "Reviewed again after the rota changed.", "next_review_date": chosen.isoformat()})).json
    assert again["review_date"] == chosen.isoformat()


@pytest.mark.asyncio
async def test_sunset_needs_findings_ends_sixty_days_later_and_then_asks_an_admin_to_archive(env):
    agreement = await _agreement(env, status="under_review", review_date=TODAY + dt.timedelta(days=5))
    status = f"/api/v1/agreements/{agreement}/status"

    refused = await _call(env, "post", "ari", status, json={"status": "sunset"}, expect=400)
    assert refused.json["code"] == "FINDINGS_REQUIRED"  # framework G: no sunset without the review's findings
    ended = (await _call(env, "post", "ari", status, expect=200, json={
        "status": "sunset", "evidence": "The new rota agreement replaces it."})).json
    ends_on = TODAY + dt.timedelta(days=60)  # owner default: sunset_date = today + 60
    assert (ended["status"], ended["sunset_date"]) == ("sunset", ends_on.isoformat())
    review = (await _call(env, "get", "ari", f"/api/v1/agreements/{agreement}/history", expect=200)).json["reviews"][0]
    assert (review["outcome"], review["on_time"], review["next_review_date"]) == ("sunset", True, None)

    assert "archive_agreement" not in _actions(await _queue(env, "ari"), agreement)
    # F5: the 60-day notice is enforced: archiving at once is refused, and the page says when it opens.
    early = await _call(env, "post", "ari", status, json={"status": "archived"}, expect=409)
    assert (early.json["code"], early.json["sunset_date"]) == ("SUNSET_NOT_ENDED", ends_on.isoformat())
    [archive_move] = (await _call(env, "get", "ari", f"/api/v1/explain/agreement/{agreement}", expect=200)).json["your_moves"]
    assert (archive_move["move"], archive_move["ready"]) == ("archived", False)
    assert ends_on.isoformat() in archive_move["blocked"]
    async with env.db() as session:  # the assistant is refused with the same words
        chat = await execute_tool("update_agreement_status", {"agreement_id": str(agreement), "new_status": "archived",
                                  "confirmed": True}, session, [OASIS], caller_user_id=PEOPLE["ari"].user_id)
    assert chat["success"] is False and ends_on.isoformat() in chat["error"]

    after = _noon(ends_on + dt.timedelta(days=1))
    archive = _actions(await _queue(env, "ari", after), agreement)["archive_agreement"]
    # F13: available, not late: no past date for the bell to print as "Due <date>"; `why` names the end.
    assert (archive["due"], archive["overdue"]) == (None, False) and ends_on.isoformat() in archive["why"]
    assert not _actions(await _queue(env, "mo", after), agreement)  # admins and owners only
    assert not _actions(await _queue(env, "ada", after), agreement)
    with patch("neos_agent.services.dates.utc_now", return_value=after):
        banner = (await _call(env, "get", "ari", f"/api/v1/explain/agreement/{agreement}", expect=200)).json
        assert (banner["due_label"], banner["your_moves"][0]["ready"]) == ("Sunset ended", True)
        await _call(env, "post", "ari", status, json={"status": "archived"}, expect=200)


# ---------------------------------------------------------------------------
# C2: rollback only where editing is allowed, and never status or dates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rollback_restores_draft_terms_only_and_is_refused_on_an_agreement_in_force(env):
    created = (await _call(env, "post", "ada", "/api/v1/agreements/", expect=201, json={
        "ecosystem_id": str(OASIS), "type": "organizational", "title": "Tool library", "text": "Borrow for a week."})).json
    draft = created["id"]
    assert created["review_date"] == dates.add_months(TODAY, 24).isoformat()  # D7: new agreements come due
    await _call(env, "put", "ada", f"/api/v1/agreements/{draft}", json={"text": "Borrow for two weeks."}, expect=200)
    history = (await _call(env, "get", "ada", f"/api/v1/agreements/{draft}/history", expect=200)).json
    assert history["caller_can_rollback"] is True
    first = next(v for v in history["versions"] if v["text"] == "Borrow for a week.")
    restored = (await _call(env, "post", "ada", f"/api/v1/agreements/{draft}/rollback/{first['id']}", expect=200)).json
    assert (restored["text"], restored["status"], restored["review_date"]) == (
        "Borrow for a week.", "draft", created["review_date"])

    for state in ("active", "under_review"):
        agreement = await _agreement(env, status=state, review_date=TODAY + dt.timedelta(days=30))
        old = uuid.uuid4()
        await _add(env, AgreementVersion(id=old, agreement_id=agreement, version="0.9", status="active",
                                          title="Kitchen rota", text="Old text.", type="organizational",
                                          hierarchy_level="domain", review_date=TODAY - dt.timedelta(days=400)))
        for who in ("ada", "ari"):
            refused = await _call(env, "post", who, f"/api/v1/agreements/{agreement}/rollback/{old}", expect=409)
            assert refused.json["code"] == "ROLLBACK_LOCKED"
        kept = await _row(env, Agreement, agreement)
        assert (kept.status, kept.version, kept.text) == (state, "1.0", "Who cooks when.")
        history = (await _call(env, "get", "ada", f"/api/v1/agreements/{agreement}/history", expect=200)).json
        assert history["caller_can_rollback"] is False


@pytest.mark.asyncio
async def test_a_registered_proposal_becomes_an_agreement_with_a_review_date(env):
    proposal = uuid.uuid4()
    await _add(env, Proposal(id=proposal, ecosystem_id=OASIS, proposal_id="PROP-REG", type="policy", title="Compost",
                             status="ratified", proposer="Ada", proposer_member_id=PEOPLE["ada"].member_id(),
                             proposed_change="Compost in the garden.", ratified_text="Compost in the garden."))
    await _call(env, "post", "mo", f"/api/v1/proposals/{proposal}/register-agreement", expect=201)
    agreement = await _row(env, Agreement, (await _row(env, Proposal, proposal)).registered_agreement_id)
    assert agreement.review_date == dates.add_months(TODAY, 12)  # D7: registration never left it undated


# ---------------------------------------------------------------------------
# C3: review due in the queue (admins and owners, 14 days ahead) and on the registry (everyone)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_review_due_reaches_admins_fourteen_days_ahead_and_the_registry_flags_it_for_everyone(env):
    later = await _agreement(env, status="active", review_date=TODAY + dt.timedelta(days=20), title="Later rules")
    start = _actions(await _queue(env, "ari"), HOUSE)["start_review"]  # House rules: due in 10 days
    assert (start["due"], start["overdue"]) == ((TODAY + dt.timedelta(days=10)).isoformat(), False)
    assert "start_review" not in _actions(await _queue(env, "ari"), later)  # 20 days out: not yet
    for who in ("mo", "ada"):  # owner default: admins and owners only (a mod could not start it)
        assert "start_review" not in _actions(await _queue(env, who))

    after = _noon(TODAY + dt.timedelta(days=12))  # House rules' date has ended everywhere
    items = await _queue(env, "ari", after)
    assert _actions(items, HOUSE)["start_review"]["overdue"] is True
    assert _actions(items, later)["start_review"]["overdue"] is False  # now within 14 days
    with patch("neos_agent.services.dates.utc_now", return_value=after):
        listed = {i["id"]: i["review_overdue"] for i in
                  (await _call(env, "get", "ada", "/api/v1/agreements/", expect=200)).json["items"]}
        banner = (await _call(env, "get", "ada", f"/api/v1/explain/agreement/{HOUSE}", expect=200)).json
    assert (listed[str(HOUSE)], listed[str(later)]) == (True, False)
    assert (banner["state"], banner["overdue"]) == ("Active", True)  # overdue never takes it out of force
    assert "was due" in banner["next_step"]

    status = f"/api/v1/agreements/{HOUSE}/status"
    await _call(env, "post", "ari", status, json={"status": "under_review"}, expect=200)
    assert "finish_review" in _actions(await _queue(env, "ari"), HOUSE)
    await _call(env, "post", "ari", status, json={"status": "active", "evidence": "Quiet hours still work."}, expect=200)
    assert not _actions(await _queue(env, "ari"), HOUSE)


# ---------------------------------------------------------------------------
# C4: one date rule, decided by the server
# ---------------------------------------------------------------------------

DUE = dt.date(2026, 11, 1)
PLUS_14 = dt.timezone(dt.timedelta(hours=14))


@pytest.mark.parametrize("now, passed", [
    (dt.datetime(2026, 11, 2, 11, 59), False),  # 23:59 on 1 Nov at UTC-12: still the due day somewhere
    (dt.datetime(2026, 11, 2, 12, 0), True),  # 1 Nov has ended everywhere (owner default: anywhere on Earth)
    (dt.datetime(2026, 11, 2, 13, 0, tzinfo=PLUS_14), False),  # a UTC+14 caller's 2 Nov: not passed for UTC-12
])
def test_a_date_only_due_date_passes_when_its_day_has_ended_everywhere(now, passed):
    assert dates.date_passed(DUE, now) is passed


def test_the_utc_plus_14_row_is_the_instant_not_the_wall_clock():
    # 3 Nov 01:00 at UTC+14 is 2 Nov 11:00 UTC, i.e. 1 Nov 23:00 at UTC-12: the due day has not ended there.
    assert dates.date_passed(DUE, dt.datetime(2026, 11, 3, 1, 59, tzinfo=PLUS_14)) is False
    assert dates.date_passed(DUE, dt.datetime(2026, 11, 3, 2, 0, tzinfo=PLUS_14)) is True


@pytest.mark.parametrize("due, now, passed", [
    (dt.datetime(2026, 11, 1, 10, 0), dt.datetime(2026, 11, 1, 9, 59), False),  # a timestamp passes at its instant
    (dt.datetime(2026, 11, 1, 10, 0), dt.datetime(2026, 11, 1, 10, 1), True),
    (dt.datetime(2026, 11, 1, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=2))), dt.datetime(2026, 11, 1, 10, 1), True),
])
def test_timestamps_compare_in_utc(due, now, passed):
    assert dates.date_passed(due, now) is passed


def test_the_queue_clock_honours_now_for_today():
    assert Clock.at(dt.datetime(2026, 11, 2, 11, 59)).today == DUE  # wave-B LOW: `today` ignored `now`
    assert Clock.at(dt.datetime(2026, 11, 2, 12, 0)).today == dt.date(2026, 11, 2)


@pytest.mark.asyncio
async def test_a_steward_may_close_advice_for_the_proposer_only_once_the_deadline_ended_everywhere(env):
    proposal, log = uuid.uuid4(), uuid.uuid4()
    await _add(env, Proposal(id=proposal, ecosystem_id=OASIS, proposal_id="PROP-ADV", type="policy", title="Bike shed",
                             status="advice", proposer="Ada", proposer_member_id=PEOPLE["ada"].member_id(),
                             proposed_change="Paint it green.", advice_deadline=DUE))
    await _add(env, AdviceLog(id=log, proposal_id=proposal))
    await _add(env, AdviceEntry(id=uuid.uuid4(), advice_log_id=log, advisor="Ben", member_id=PEOPLE["ben"].member_id(),
                                advice_text="Green is fine."))
    before = _actions(await _queue(env, "mo", dt.datetime(2026, 11, 2, 11, 0)), proposal)
    after = _actions(await _queue(env, "mo", dt.datetime(2026, 11, 2, 12, 0)), proposal)
    assert "close_advice" not in before
    assert after["close_advice"]["what"] == ADVICE_DEADLINE_STEWARD_PROMPT


# ---------------------------------------------------------------------------
# C5: the snapshot computes the framework values (statuses stay human)
# ---------------------------------------------------------------------------


def _ago(days: int) -> dt.datetime:
    return NOW - dt.timedelta(days=days)


async def _seed_indicators(env) -> None:
    ada, ben, mo = (PEOPLE[k].member_id() for k in ("ada", "ben", "mo"))
    proposals = [("P1", ada, "ratified"), ("P2", ada, "ratified"), ("P3", ada, "ratified"),
                 ("P4", mo, "ratified"), ("P5", mo, "withdrawn"), ("P6", mo, "withdrawn"), ("P7", mo, "ratified")]
    ids = {key: uuid.uuid4() for key, *_ in proposals}
    rows = [Proposal(id=ids[key], ecosystem_id=OASIS, proposal_id=key, type="policy", title=key, status=state,
                     proposer_member_id=author, created_at=_ago(10)) for key, author, state in proposals]
    rows.append(Proposal(id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id="OLD", type="policy", title="Old, stalled",
                         status="consent", proposer_member_id=ada, consent_deadline=TODAY - dt.timedelta(days=3),
                         created_at=_ago(200)))  # outside the period; stalled in consent
    reviewed, renewed = uuid.uuid4(), uuid.uuid4()
    rows += [
        Agreement(id=reviewed, ecosystem_id=OASIS, agreement_id="AGR-MISSED", type="organizational", title="Missed",
                  version="1.0", status="active", review_date=TODAY - dt.timedelta(days=5)),
        Agreement(id=renewed, ecosystem_id=OASIS, agreement_id="AGR-ONTIME", type="organizational", title="On time",
                  version="1.0", status="active", review_date=TODAY + dt.timedelta(days=300)),
        ReviewRecord(id=uuid.uuid4(), ecosystem_id=OASIS, review_id="REV-1", agreement_id=renewed, review_type="scheduled",
                     outcome="renewed", evaluation={"findings": "Fine.", "due_date": (TODAY - dt.timedelta(days=20)).isoformat(),
                                                    "on_time": True}),
        MemberStatusTransition(id=uuid.uuid4(), member_id=mo, from_status="role:user", to_status="role:mod",
                               date=TODAY - dt.timedelta(days=400), trigger="role_grant"),
        Collaboration(id=uuid.uuid4(), source_domain_id=GARDEN, target_domain_id=KITCHEN, title="Herbs for the kitchen",
                      created_at=_ago(3)),
    ]
    for member in (ada, ben, mo):  # this period: three members took part
        rows.append(AgreementMemberConsent(id=uuid.uuid4(), agreement_id=renewed, member_id=member, agreement_version="1.0",
                                           attestation="I consent.", attested_at=_ago(5)))
    for member in (ada, ben):  # the 90 days before: two
        rows.append(AgreementMemberConsent(id=uuid.uuid4(), agreement_id=reviewed, member_id=member, agreement_version="1.0",
                                           attestation="I consent.", attested_at=_ago(100)))
    await _add(env, *rows)
    p4_record, p5_record = uuid.uuid4(), uuid.uuid4()
    await _add(env, ConsentRecord(id=p4_record, proposal_id=ids["P4"], consent_mode="consent", created_at=_ago(10)),
               ConsentRecord(id=p5_record, proposal_id=ids["P5"], consent_mode="consent", created_at=_ago(10)))
    await _add(env,
               ConsentParticipant(id=uuid.uuid4(), consent_record_id=p4_record, name="Ben", member_id=ben,
                                  position="object", reason="Too fast.", created_at=_ago(10)),
               ConsentParticipant(id=uuid.uuid4(), consent_record_id=p5_record, name="Ada", member_id=ada,
                                  position="withdrawn", reason="Unclear cost.", created_at=_ago(10)),
               AdviceLog(id=uuid.uuid4(), proposal_id=ids["P4"], summary="Sent back from consent for revision by Mo (v1.1)",
                         proposer_modifications="Slower rollout.", created_at=_ago(9)))


@pytest.mark.asyncio
async def test_the_snapshot_computes_each_framework_indicator_from_records(env):
    await _seed_indicators(env)
    snapshot = (await _call(env, "get", "ada", f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}", expect=200)).json
    values = {i["indicator_id"]: (i["measured_value"], i["band"]) for i in snapshot["indicators"]}
    assert values == {
        "GHI-01": (29, "critical"),  # 2 authors of 7 proposals in the period
        "GHI-02": (2.0, "healthy"),  # others 3/3 ratified vs leadership 2/4
        "GHI-03": (None, None),  # not computable yet: no resource records
        "GHI-04": (50.0, "healthy"),  # 3 members took part against 2 in the prior 90 days
        "GHI-05": (4, "critical"),  # Mo has been a steward for 400 days
        "GHI-06": (50, "warning"),  # 1 of 2 objections led to a send-back
        "GHI-07": (50, "critical"),  # 1 of 2 reviews due in the period was on time
        "GHI-08": (1.0, "critical"),  # one collaboration between domains
    }
    assert next(i for i in snapshot["indicators"] if i["indicator_id"] == "GHI-03")["computable"] is False
    assert next(i for i in snapshot["indicators"] if i["indicator_id"] == "GHI-05")["detail"].startswith("Mo")
    attention = {item["key"]: item["count"] for item in snapshot["attention"]}
    assert (attention["reviews_overdue"], attention["stalled_proposals"], attention["waiting_newcomers"]) == (1, 1, 1)

    await _call(env, "get", "olu", f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}", expect=404)
    await _call(env, "get", "pia", f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}", expect=404)


# ---------------------------------------------------------------------------
# C6: the auditor is not a steward of the audited ecosystem (owner decision 2026-11-01)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("who, ecosystem, expect, code", [
    ("ben", OASIS, 201, None),
    ("mo", OASIS, 403, "AUDITOR_NOT_INDEPENDENT"),  # a steward, while non-stewards could audit
    ("ari", OASIS, 403, "AUDITOR_NOT_INDEPENDENT"),
    ("olu", OASIS, 403, None),  # another ecosystem
    ("pia", OASIS, 403, None),  # pending consent
    ("sam", SOLO, 201, None),  # nobody else is active there: a self-assessment
])
async def test_who_may_record_an_audit(env, who, ecosystem, expect, code):
    resp = await _call(env, "post", who, "/api/v1/safeguards/audits", json={"ecosystem_id": str(ecosystem)}, expect=expect)
    assert resp.json.get("code") == code
    if expect == 201:
        assert resp.json["self_assessment"] is (who == "sam")


# ---------------------------------------------------------------------------
# C5 publish and C8: values freeze; members see labelled results; drafts never count
# ---------------------------------------------------------------------------


async def _draft(env, who: str, ecosystem=OASIS) -> str:
    return (await _call(env, "post", who, "/api/v1/safeguards/audits", json={"ecosystem_id": str(ecosystem)},
                        expect=201)).json["id"]


async def _rate(env, who: str, audit_id: str, overrides: dict | None = None, skip: set = frozenset()) -> None:
    """Rate every indicator that has data now (healthy unless overridden), except `skip`."""
    snapshot = (await _call(env, "get", who, f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}", expect=200)).json
    ratings = [{"indicator_id": i["indicator_id"], "indicator_name": i["name"],
                "status": (overrides or {}).get(i["indicator_id"], "healthy")}
               for i in snapshot["indicators"] if i["measured_value"] is not None and i["indicator_id"] not in skip]
    await _call(env, "put", who, f"/api/v1/safeguards/audits/{audit_id}", json={"indicator_scores": ratings}, expect=200)


async def _publish(env, who: str = "ben", overrides: dict | None = None) -> dict:
    audit_id = await _draft(env, who)
    await _rate(env, who, audit_id, overrides)
    return (await _call(env, "post", who, f"/api/v1/safeguards/audits/{audit_id}/publish", expect=200)).json


async def _proposals(env, *authors: str) -> None:
    await _add(env, *[Proposal(id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id=f"P-{uuid.uuid4().hex[:6]}", type="policy",
                               title="A proposal", status="draft", proposer_member_id=PEOPLE[a].member_id(),
                               created_at=_ago(2)) for a in authors])


@pytest.mark.asyncio
async def test_publishing_needs_every_rating_with_data_and_freezes_the_values(env):
    await _proposals(env, "ada", "ben")
    audit_id = await _draft(env, "ben")
    await _rate(env, "ben", audit_id, skip={"GHI-01"})
    refused = await _call(env, "post", "ben", f"/api/v1/safeguards/audits/{audit_id}/publish", expect=400)
    assert (refused.json["code"], refused.json["missing"]) == ("RATINGS_MISSING", ["GHI-01"])
    assert "Proposal authorship diversity" in refused.json["error"]

    await _rate(env, "ben", audit_id, {"GHI-01": "warning"})
    published = (await _call(env, "post", "ben", f"/api/v1/safeguards/audits/{audit_id}/publish", expect=200)).json
    rows = {row["indicator_id"]: row for row in published["indicator_scores"]}
    assert len(rows) == 8  # every indicator frozen, GHI-03 as "not computable yet"
    assert {k: rows["GHI-01"][k] for k in ("measured_value", "status", "trend", "unit")} == {
        "measured_value": 100, "status": "warning", "trend": "baseline", "unit": "%"}
    assert (rows["GHI-03"]["computable"], rows["GHI-03"]["measured_value"]) == (False, None)

    await _proposals(env, "ada", "ada")  # later data: 2 authors of 4 proposals
    detail = (await _call(env, "get", "ada", f"/api/v1/safeguards/audits/{audit_id}", expect=200)).json
    assert next(r for r in detail["indicator_scores"] if r["indicator_id"] == "GHI-01")["measured_value"] == 100
    second = await _publish(env, "dee")
    later = next(r for r in second["indicator_scores"] if r["indicator_id"] == "GHI-01")
    assert (later["measured_value"], later["prior_value"], later["trend"]) == (50, 100, "degrading")


@pytest.mark.asyncio
async def test_members_read_each_ecosystems_published_result_and_never_a_draft(env):
    published = await _publish(env, "ben")
    await _draft(env, "ben")  # a newer draft must not replace the published result

    summary = (await _call(env, "get", "ada", "/api/v1/safeguards", expect=200)).json
    [oasis] = summary["ecosystems"]
    assert (oasis["ecosystem"], oasis["latest_audit"]["id"], oasis["published_on"]) == (
        "Oasis", published["id"], dates.utc_today().isoformat())
    assert (oasis["audit_due"], oasis["audit_overdue"]) == (
        (dates.utc_today() + dt.timedelta(days=90)).isoformat(), False)
    assert oasis["caller_can_record_audit"] is True
    mo = (await _call(env, "get", "mo", "/api/v1/safeguards", expect=200)).json["ecosystems"][0]
    assert mo["caller_can_record_audit"] is False

    both = (await _call(env, "get", "dee", "/api/v1/safeguards", expect=200)).json
    assert [(e["ecosystem"], e["latest_audit"] and e["latest_audit"]["id"]) for e in both["ecosystems"]] == [
        ("Oasis", published["id"]), ("River House", None)]
    assert both["latest_audit"] is None  # D12: no single score across two ecosystems

    olu = (await _call(env, "get", "olu", "/api/v1/safeguards", expect=200)).json
    assert [e["ecosystem"] for e in olu["ecosystems"]] == ["River House"]
    await _call(env, "get", "olu", f"/api/v1/safeguards/audits/{published['id']}", expect=404)
    await _call(env, "get", "olu", f"/api/v1/explain/audit/{published['id']}", expect=404)
    banner = (await _call(env, "get", "ada", f"/api/v1/explain/audit/{published['id']}", expect=200)).json
    assert (banner["state"], banner["due"]) == ("Published", oasis["audit_due"])


# ---------------------------------------------------------------------------
# C7: audit due and critical indicators reach stewards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stewards_are_told_an_audit_is_due_and_to_respond_to_critical_ratings_only(env):
    soon = _noon(TODAY + dt.timedelta(days=80))  # never audited: due a quarter after the ecosystem began
    assert "audit_due" in _actions(await _queue(env, "mo", soon))
    assert "audit_due" not in _actions(await _queue(env, "ada", soon))

    await _proposals(env, "ada", "ben")
    warned = await _publish(env, "ben", {"GHI-01": "warning"})
    assert "respond_to_audit" not in _actions(await _queue(env, "mo"))  # owner default: warnings show on the page only
    async with env.db() as session:  # it was published yesterday (SQLite stamps to the second: no same-day tie)
        (await session.get(GovernanceHealthAudit, uuid.UUID(warned["id"]))).audit_date -= dt.timedelta(days=1)
        await session.commit()
    critical = await _publish(env, "dee", {"GHI-01": "critical"})
    respond = _actions(await _queue(env, "mo"))["respond_to_audit"]
    assert respond["id"] == critical["id"] and "Proposal authorship diversity" in respond["why"]
    assert "respond_to_audit" not in _actions(await _queue(env, "ada"))

    closed = NOW + dt.timedelta(days=5)  # an emergency that ended after the audit brings the next one forward
    await _add(env, EmergencyState(id=uuid.uuid4(), ecosystem_id=OASIS, state="closed", closed_at=closed))
    entry = (await _call(env, "get", "ada", "/api/v1/safeguards", expect=200)).json["ecosystems"][0]
    assert entry["audit_due"] == (closed.date() + dt.timedelta(days=30)).isoformat()


# ---------------------------------------------------------------------------
# C9: compliance stops inventing scores and leaking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_compliance_scores_only_what_it_measures_and_stays_in_its_ecosystem(env):
    await _add(env, ComplianceSummary(id=uuid.uuid4(), ecosystem_id=OASIS, summary="Oasis summary", score_data={}),
               Agreement(id=uuid.uuid4(), ecosystem_id=RIVER, agreement_id="AGR-RIVER", type="organizational",
                         title="River draft", version="1.0", status="draft"))
    await _call(env, "get", "pia", "/api/v1/compliance/latest", expect=404)  # D10: pending-only read Oasis's summary
    assert (await _call(env, "get", "pia", "/api/v1/compliance/history", expect=200)).json["total"] == 0

    with patch("neos_agent.api.compliance.is_ai_enabled", return_value=False):
        await _call(env, "post", "dee", "/api/v1/compliance/generate", json={}, expect=400)  # two selected: say which
        await _call(env, "post", "olu", "/api/v1/compliance/generate", json={"ecosystem_id": str(OASIS)}, expect=404)
        made = (await _call(env, "post", "dee", "/api/v1/compliance/generate", json={"ecosystem_id": str(OASIS)},
                            expect=201)).json
    assert made["ecosystem_id"] == str(OASIS)
    # Oasis has one agreement, in force; River's draft would halve it. Domains exist, but nothing is invented.
    assert made["score_data"] == {"agreement_coverage": 100, "domain_health": None, "process_adherence": None,
                                  "conflict_resolution": None}


# ---------------------------------------------------------------------------
# C10: a domain's steward or status changes by a steward of the ecosystem, with a recorded reason
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_domain_steward_and_status_changes_are_a_stewards_act_with_a_record(env):
    ben = str(PEOPLE["ben"].member_id())
    garden = f"/api/v1/domains/{GARDEN}"
    refused = await _call(env, "put", "amara", garden, json={"steward_id": ben, "reason": "I am moving away."}, expect=403)
    assert refused.json["code"] == "DOMAIN_AUTHORITY_DENIED"  # D15: the domain steward handed off their own domain
    await _call(env, "put", "amara", garden, json={"purpose": "Grow food together"}, expect=200)  # still edits it
    missing = await _call(env, "put", "mo", garden, json={"steward_id": ben}, expect=400)
    assert missing.json["code"] == "REASON_REQUIRED"
    await _call(env, "put", "mo", garden, json={"steward_id": str(PEOPLE["olu"].member_id())}, expect=400)
    moved = (await _call(env, "put", "mo", garden, json={"steward_id": ben, "reason": "Amara asked to hand it on."},
                         expect=200)).json
    assert moved["current_steward"] == "Ben"
    await _call(env, "put", "mo", f"/api/v1/domains/{KITCHEN}", expect=403,
                json={"status": "sunset", "reason": "We no longer cook together."})  # Mo stewards the Kitchen
    await _call(env, "put", "ari", f"/api/v1/domains/{KITCHEN}", expect=200,
                json={"status": "sunset", "reason": "We no longer cook together."})

    async with env.db() as session:
        records = {(r.source_skill, r.ratio_decidendi, r.recorder) for r in
                   (await session.execute(select(DecisionRecord).where(DecisionRecord.artifact_type == "domain"))).scalars()}
    assert records == {("role-transfer", "Amara asked to hand it on.", "Mo"),
                       ("role-sunset", "We no longer cook together.", "Ari")}


# ---------------------------------------------------------------------------
# Assistant parity: the same engine and the same auditor rule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_assistant_ends_reviews_with_findings_and_follows_the_auditor_rule(env):
    agreement = await _agreement(env, status="under_review", review_date=TODAY + dt.timedelta(days=2))
    async with env.db() as session:
        missing = await execute_tool("update_agreement_status", {"agreement_id": str(agreement), "new_status": "active",
                                     "confirmed": True}, session, [OASIS], caller_user_id=PEOPLE["ari"].user_id)
        assert missing["success"] is False and "findings" in missing["error"]
        done = await execute_tool("update_agreement_status", {
            "agreement_id": str(agreement), "new_status": "active", "confirmed": True,
            "findings": "It still serves the kitchen."}, session, [OASIS], caller_user_id=PEOPLE["ari"].user_id)
        assert done["success"] is True and done["data"]["review_date"] == dates.add_months(TODAY, 24).isoformat()
        steward = await execute_tool("create_safeguard_audit", {"findings": "Looks fine."}, session, [OASIS],
                                     caller_user_id=PEOPLE["mo"].user_id)
        assert (steward["success"], steward.get("code")) == (False, "AUDITOR_NOT_INDEPENDENT")
        drafted = await execute_tool("create_safeguard_audit", {"findings": "Looks fine.", "overall_health_score": 100},
                                     session, [OASIS], caller_user_id=PEOPLE["ben"].user_id)
        read = await execute_tool("get_governance_health", {}, session, [OASIS], caller_user_id=PEOPLE["ada"].user_id)
        await session.commit()
    assert (await _row(env, GovernanceHealthAudit, uuid.UUID(drafted["data"]["id"]))).overall_health_score is None  # D14
    assert len(read["data"]["indicators"]) == 8
    async with env.db() as session:
        review = await session.scalar(select(ReviewRecord).where(ReviewRecord.agreement_id == agreement))
    assert (review.outcome, review.evaluation["findings"]) == ("renewed", "It still serves the kitchen.")


# ---------------------------------------------------------------------------
# FX-Maint (wave-c fix wave): uxqa/governance/wave-c-review-authority.md and wave-c-review-flows.md
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_an_admin_who_has_not_consented_gets_the_consent_act_never_a_status_move(env):
    # F2: the explanation's `attest` move fell into the review dialog ("Archive this agreement?") and posted
    # {"status": "attest"} (400). It is the consent act, marked as such, and the consent flow it points to works.
    moves = (await _call(env, "get", "ari", f"/api/v1/explain/agreement/{HOUSE}", expect=200)).json["your_moves"]
    assert [(m["move"], m.get("kind")) for m in moves] == [("under_review", None), ("attest", "consent")]
    await _call(env, "post", "ari", f"/api/v1/agreements/{HOUSE}/status", json={"status": "attest"}, expect=400)
    await _call(env, "post", "ari", f"/api/v1/agreements/{HOUSE}/consent", expect=201,
                json={"attestation": "I have read the house rules and consent."})
    moves = (await _call(env, "get", "ari", f"/api/v1/explain/agreement/{HOUSE}", expect=200)).json["your_moves"]
    assert [m["move"] for m in moves] == ["under_review"]


@pytest.mark.asyncio
async def test_a_review_move_on_a_stale_page_is_refused_not_applied_twice(env):
    # A4 (the lock's read): a ceremony checks the row's committed status under FOR UPDATE; a move made from a page
    # that no longer matches it is a 409, never a second ReviewRecord. The PostgreSQL race is the next test.
    from neos_agent.api.agreements import transition_agreement
    from neos_agent.services.act_gates import TransitionRefused

    agreement = await _agreement(env, status="under_review", review_date=TODAY + dt.timedelta(days=3))
    async with env.db() as stale:
        page = await stale.get(Agreement, agreement)  # what the second admin's page loaded
        caller = await stale.get(Member, PEOPLE["ari"].member_id())
        await _call(env, "post", "ari", f"/api/v1/agreements/{agreement}/status", expect=200,
                    json={"status": "active", "evidence": "Kept: it still works for us."})
        with pytest.raises(TransitionRefused) as refused:
            await transition_agreement(stale, page, to="sunset", caller=caller, evidence="End it, the rota moved on.")
    assert (refused.value.status, refused.value.extra["code"]) == (409, "AGREEMENT_CHANGED")
    async with env.db() as session:
        outcomes = [r.outcome for r in (await session.execute(
            select(ReviewRecord).where(ReviewRecord.agreement_id == agreement))).scalars()]
    assert outcomes == ["renewed"]


POSTGRES_URL = os.environ.get("NEOS_TEST_POSTGRES_URL")


@pytest.mark.skipif(not POSTGRES_URL, reason="needs NEOS_TEST_POSTGRES_URL (a disposable PostgreSQL database)")
@pytest.mark.asyncio
async def test_two_admins_ending_one_review_at_once_on_postgres():
    # A4: renew and sunset at the same moment. Both requests have loaded the agreement (the barrier) before either
    # moves it; the row lock lets exactly one through, and the other is a clean 409 with one ReviewRecord in all.
    import asyncio
    import sqlalchemy as sa
    from neos_agent.api import agreements as agreements_api

    schema = f"fxmaint_{uuid.uuid4().hex[:12]}"
    admin = create_async_engine(POSTGRES_URL)
    async with admin.begin() as conn:
        await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
    engine = None
    try:
        engine, world = await _build(POSTGRES_URL, connect_args={"server_settings": {"search_path": schema}})
        agreement = await _agreement(world, status="under_review", review_date=TODAY + dt.timedelta(days=3))
        url = f"/api/v1/agreements/{agreement}/status"
        both_loaded = asyncio.Barrier(2)
        real_load = agreements_api.get_scoped_or_404

        async def load_then_wait(*args, **kwargs):
            row = await real_load(*args, **kwargs)
            await both_loaded.wait()
            return row

        with patch.object(agreements_api, "get_scoped_or_404", load_then_wait):
            results = await asyncio.gather(
                _call(world, "post", "ari", url, json={"status": "active", "evidence": "Keep it: it still works."}),
                _call(world, "post", "ari", url, json={"status": "sunset", "evidence": "End it: the rota moved on."}),
            )
        assert sorted(r.status for r in results) == [200, 409], [r.text for r in results]
        assert next(r for r in results if r.status == 409).json["code"] == "AGREEMENT_CHANGED"
        async with world.db() as session:
            reviews = (await session.execute(select(ReviewRecord).where(ReviewRecord.agreement_id == agreement))).scalars().all()
            row = await session.get(Agreement, agreement)
        assert len(reviews) == 1
        assert (row.status, reviews[0].outcome) in {("active", "renewed"), ("sunset", "sunset")}
        assert (row.sunset_date is None) is (row.status == "active")  # never active with a sunset date
    finally:
        if engine is not None:
            await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("who, ecosystem, expect, self_assessment", [
    ("fran", FRESH, 201, True),  # A5/F8: a founder alone records a self-assessment, never an "independent" audit
    ("finn", FERN, 403, None),  # a founder (co_creator, role user) is its steward while a plain member can audit
    ("fay", FERN, 201, False),  # the plain member is the independent auditor
])
async def test_a_founder_is_a_steward_of_their_ecosystem_for_the_audit(env, who, ecosystem, expect, self_assessment):
    resp = await _call(env, "post", who, "/api/v1/safeguards/audits", json={"ecosystem_id": str(ecosystem)}, expect=expect)
    if expect == 201:
        assert resp.json["self_assessment"] is self_assessment
    else:
        assert resp.json["code"] == "AUDITOR_NOT_INDEPENDENT"


@pytest.mark.asyncio
async def test_a_founder_hears_the_audit_is_due_and_the_plain_member_does_not(env):
    soon = _noon(TODAY + dt.timedelta(days=80))  # never audited: due a quarter after the ecosystem began
    finn = _actions(await _queue(env, "finn", soon))
    assert "Ask a member who is not a steward" in finn["audit_due"]["why"]
    assert finn["audit_due"]["title"] == "Governance health of Fern Valley"  # F14
    assert "audit_due" not in _actions(await _queue(env, "fay", soon))


async def _audit_row(env, *, auditor: str, touched: dt.datetime, ecosystem=OASIS) -> uuid.UUID:
    audit_id = uuid.uuid4()
    await _add(env, GovernanceHealthAudit(
        id=audit_id, ecosystem_id=ecosystem, audit_id=f"AUDIT-{audit_id.hex[:6].upper()}", auditor=PEOPLE[auditor].name,
        auditor_ids=[str(PEOPLE[auditor].member_id(ecosystem))], status="draft", trigger_type="human",
        audit_scope="full", created_at=touched, updated_at=touched))
    return audit_id


@pytest.mark.asyncio
async def test_an_abandoned_or_stale_draft_stops_silencing_the_audit_due_reminder(env):
    # F6: one forgotten draft (or one whose auditor left) silenced audit_due for every steward for good.
    soon = _noon(TODAY + dt.timedelta(days=80))  # the queue reads the clock at `soon`; drafts age against it
    gone = await _audit_row(env, auditor="eve", touched=soon - dt.timedelta(days=1))  # its auditor has left Oasis
    assert "draft by Eve" in _actions(await _queue(env, "mo", soon))["audit_due"]["why"]

    async with env.db() as session:
        await session.delete(await session.get(GovernanceHealthAudit, gone))
        await session.commit()
    stale = await _audit_row(env, auditor="ben", touched=soon - dt.timedelta(days=40))  # untouched for 40 days
    assert "audit_due" in _actions(await _queue(env, "mo", soon))
    live = await _audit_row(env, auditor="dee", touched=soon - dt.timedelta(days=3))  # someone is recording it now
    assert "audit_due" not in _actions(await _queue(env, "mo", soon))

    # Abandoning: the auditor or a steward, with a recorded reason; never a plain member.
    url = f"/api/v1/safeguards/audits/{live}/abandon"
    await _call(env, "post", "ada", url, json={"reason": "Nobody asked for it."}, expect=403)
    short = await _call(env, "post", "dee", url, json={"reason": "no"}, expect=400)
    assert short.json["field"] == "reason"
    detail = (await _call(env, "get", "mo", f"/api/v1/safeguards/audits/{live}", expect=200)).json
    assert (detail["caller_can_abandon"], detail["caller_can_edit"]) == (True, False)
    done = (await _call(env, "post", "mo", url, json={"reason": "Dee moved to River House full time."}, expect=200)).json
    assert (done["status"], done["abandonment"]["note"], done["abandonment"]["recorded_by"]) == (
        "abandoned", "Dee moved to River House full time.", "Mo")
    await _call(env, "post", "dee", url, json={"reason": "Abandon it again."}, expect=409)
    await _call(env, "put", "dee", f"/api/v1/safeguards/audits/{live}", json={"findings": "x"}, expect=409)
    banner = (await _call(env, "get", "ada", f"/api/v1/explain/audit/{live}", expect=200)).json
    assert banner["state"] == "Abandoned" and "Dee moved" in banner["next_step"]
    assert "audit_due" in _actions(await _queue(env, "mo", soon))  # the abandoned draft holds nothing now
    assert "finish_audit" not in _actions(await _queue(env, "dee", soon))
    await _call(env, "post", "ben", f"/api/v1/safeguards/audits/{stale}/abandon", expect=200,
                json={"reason": "Started it and never finished; starting again."})  # its own auditor may too
    async with env.db() as session:
        records = {(r.source_skill, r.recorder) for r in (await session.execute(
            select(DecisionRecord).where(DecisionRecord.artifact_type == "audit"))).scalars()}
    assert records == {("audit-abandonment", "Mo"), ("audit-abandonment", "Ben")}


@pytest.mark.asyncio
async def test_stewards_clear_the_critical_item_by_recording_their_response(env):
    # F7: respond_to_audit cleared only when a newer audit was published (about 90 days later).
    await _proposals(env, "ada", "ben")
    critical = await _publish(env, "ben", {"GHI-01": "critical"})
    respond = _actions(await _queue(env, "mo"))["respond_to_audit"]
    assert respond["title"] == "Governance health of Oasis"  # F14: never the scope ("full")
    assert "respond_to_audit" in _actions(await _queue(env, "ari"))
    url = f"/api/v1/safeguards/audits/{critical['id']}/respond"
    await _call(env, "post", "ada", url, json={"note": "We will rotate authorship."}, expect=403)
    assert (await _call(env, "post", "mo", url, json={"note": "ok"}, expect=400)).json["field"] == "note"
    river = uuid.uuid4()
    await _add(env, Proposal(id=river, ecosystem_id=RIVER, proposal_id="PROP-RIVER", type="policy", title="River rota",
                             status="draft"))
    elsewhere = await _call(env, "post", "mo", url, expect=400,
                            json={"note": "We answer with a proposal.", "proposal_id": str(river)})
    assert elsewhere.json["field"] == "proposal_id"
    answer = uuid.uuid4()
    await _add(env, Proposal(id=answer, ecosystem_id=OASIS, proposal_id="PROP-ROTATE", type="policy",
                             title="Rotate who drafts proposals", status="draft",
                             proposer_member_id=PEOPLE["mo"].member_id()))

    async with env.db() as session:  # the assistant records it, naming the proposal by its key
        asked = await execute_tool("respond_to_health_audit", {"note": "Authorship rotates monthly from now on.",
                                   "proposal": "PROP-ROTATE"}, session, [OASIS], caller_user_id=PEOPLE["mo"].user_id,
                                   confirmed_keys=frozenset())
        assert "needs_confirmation" in asked
        done = await execute_tool("respond_to_health_audit", {"note": "Authorship rotates monthly from now on.",
                                  "proposal": "PROP-ROTATE", "confirmed": True}, session, [OASIS],
                                  caller_user_id=PEOPLE["mo"].user_id)
        await session.commit()
    assert done["success"] is True, done
    for who in ("mo", "ari"):
        assert "respond_to_audit" not in _actions(await _queue(env, who))
    detail = (await _call(env, "get", "ada", f"/api/v1/safeguards/audits/{critical['id']}", expect=200)).json
    assert (detail["response"]["note"], detail["response"]["recorded_by"], detail["response"]["proposal"]["proposal_id"]) == (
        "Authorship rotates monthly from now on.", "Mo", "PROP-ROTATE")
    assert detail["caller_can_respond"] is False
    again = await _call(env, "post", "ari", url, json={"note": "A second response."}, expect=409)
    assert again.json["code"] == "ALREADY_RESPONDED"

    # The response names the proposal without becoming its decision: ratifying it still mints its own record.
    from neos_agent.services.act_gates import record_proposal_decision
    async with env.db() as session:
        proposal = await session.get(Proposal, answer)
        minted = await record_proposal_decision(session, proposal)
        await session.commit()
    assert (minted.artifact_type, minted.source_proposal_id) == ("proposal", answer)


@pytest.mark.asyncio
async def test_publish_freezes_the_same_period_the_form_previewed_from_one_bound(env):
    # F11: with only the period start set, the snapshot showed start..start+89 but publish froze start..today.
    await _proposals(env, "ada", "ben")
    start = TODAY - dt.timedelta(days=30)
    preview = (await _call(env, "get", "ben", f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}&from={start}",
                           expect=200)).json["period"]
    audit_id = await _draft(env, "ben")
    await _call(env, "put", "ben", f"/api/v1/safeguards/audits/{audit_id}", expect=200,
                json={"audit_period_start": start.isoformat()})
    await _rate(env, "ben", audit_id)
    published = (await _call(env, "post", "ben", f"/api/v1/safeguards/audits/{audit_id}/publish", expect=200)).json
    assert {"start": published["audit_period_start"], "end": published["audit_period_end"]} == preview
    assert preview["end"] == (start + dt.timedelta(days=89)).isoformat()


@pytest.mark.parametrize("now, overdue", [
    (dt.datetime(2026, 11, 2, 11, 59), False),  # the check-in day (1 Nov) has not ended at UTC-12 yet
    (dt.datetime(2026, 11, 2, 12, 0), True),
])
def test_a_repair_check_in_is_overdue_by_the_one_date_rule(now, overdue):
    # F18: the case page read the server's local date.today(); the queue reads anywhere-on-Earth.
    from neos_agent.api.conflicts import next_checkin

    repair = SimpleNamespace(status="active", checkin_30_date=DUE, checkin_30_notes=None, checkin_60_date=None,
                             checkin_60_notes=None, checkin_90_date=None, checkin_90_notes=None)
    with patch("neos_agent.services.dates.utc_now", return_value=now):
        assert next_checkin(repair) == (DUE, overdue)


@pytest.mark.asyncio
async def test_a_steward_closes_advice_through_rest_only_once_the_deadline_ended_everywhere(env):
    # Hand-off: transition_proposal decided the advice deadline with the server's local date.today().
    proposal, log = uuid.uuid4(), uuid.uuid4()
    await _add(env, Proposal(id=proposal, ecosystem_id=OASIS, proposal_id="PROP-REST", type="policy", title="Gate",
                             status="advice", proposer="Ada", proposer_member_id=PEOPLE["ada"].member_id(),
                             proposed_change="Fit a gate.", advice_deadline=DUE))
    await _add(env, AdviceLog(id=log, proposal_id=proposal))
    await _add(env, AdviceEntry(id=uuid.uuid4(), advice_log_id=log, advisor="Ben", member_id=PEOPLE["ben"].member_id(),
                                advice_text="A gate is fine."))
    url = f"/api/v1/proposals/{proposal}/status"
    with patch("neos_agent.services.dates.utc_now", return_value=dt.datetime(2026, 11, 2, 11, 0)):
        early = await _call(env, "post", "mo", url, json={"status": "consent"}, expect=403)
        detail = (await _call(env, "get", "mo", f"/api/v1/proposals/{proposal}", expect=200)).json
    assert early.json["code"] == "ADVICE_CLOSE_PROPOSER_ONLY" and detail["gates"]["advice"]["deadline_passed"] is False
    with patch("neos_agent.services.dates.utc_now", return_value=dt.datetime(2026, 11, 2, 12, 0)):
        await _call(env, "post", "mo", url, json={"status": "consent"}, expect=200)


@pytest.mark.asyncio
async def test_the_shown_steward_follows_the_chosen_member_and_is_never_typed(env):
    # Hand-off (review-flows "domain form"): DomainForm edited the free-text current_steward that the page shows, so a
    # domain's own steward could "hand it on" with no reason or record while the rule guarded steward_id.
    garden = f"/api/v1/domains/{GARDEN}"
    renamed = await _call(env, "put", "amara", garden, json={"current_steward": "Ben"}, expect=400)
    assert renamed.json["code"] == "STEWARD_NAME_FOLLOWS"
    await _call(env, "put", "amara", garden, json={"current_steward": "Amara", "purpose": "Grow food"}, expect=200)
    flags = {who: (await _call(env, "get", who, garden, expect=200)).json["caller_can_change_authority"]
             for who in ("amara", "mo", "ada")}
    assert flags == {"amara": False, "mo": True, "ada": False}

    async with env.db() as session:  # a legacy row whose text drifted from its steward
        (await session.get(Domain, KITCHEN)).current_steward = "Someone else"
        await session.commit()
    listed = {i["id"]: i["current_steward"]
              for i in (await _call(env, "get", "ada", "/api/v1/domains/", expect=200)).json["items"]}
    assert listed[str(KITCHEN)] == "Mo"

    made = (await _call(env, "post", "mo", "/api/v1/domains/", expect=201, json={
        "ecosystem_id": str(OASIS), "name": "Tools", "purpose": "Share tools",
        "steward_id": str(PEOPLE["ben"].member_id()), "current_steward": "Typed name"})).json
    assert made["current_steward"] == "Ben"
    outsider = await _call(env, "post", "mo", "/api/v1/domains/", expect=400, json={
        "ecosystem_id": str(OASIS), "name": "Boats", "purpose": "Share boats", "steward_id": str(PEOPLE["olu"].member_id())})
    assert outsider.json["field"] == "steward_id"
