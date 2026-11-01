"""Exit flows through the real blueprint: only the leaver files and withdraws, stewards finish, the record ports.

Rules: src/neos_agent/api/AGENTS.md "Emergency and exit". The test middleware resolves the caller's
memberships from the database the way main._load_ecosystems does (active rows authorize), so a
member whose exit is confirmed loses that ecosystem's scope exactly as in production.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.api.errors import register_api_errors
from neos_agent.api.exit import exit_api_bp
from neos_agent.db.models import (
    AdviceEntry, AdviceLog, Agreement, AgreementMemberConsent, Base, ConsentParticipant, ConsentRecord, Ecosystem,
    ExitRecord, Member, MemberStatusTransition, Proposal, TestReport, User,
)
from neos_agent.services.agreement_consent import agreement_consent_summary

OASIS = uuid.UUID(int=0x0A)
DELTA = uuid.UUID(int=0x0D)
AGREEMENT = uuid.UUID(int=0xA6)

PEOPLE = {
    "ada": {OASIS: ("active", "mod")},  # steward
    "ari": {OASIS: ("active", "admin")},  # second steward
    "ben": {OASIS: ("active", "user"), DELTA: ("active", "user")},
    "cy": {OASIS: ("active", "user")},
    "eve": {OASIS: ("pending_consent", "user")},
    "fay": {DELTA: ("active", "user")},
}


def _user(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"exit.{name}")


def _row(name: str, ecosystem: uuid.UUID = OASIS) -> uuid.UUID:
    return uuid.uuid5(_user(name), str(ecosystem))


async def _seed(factory) -> None:
    async with factory() as session:
        session.add_all([Ecosystem(id=OASIS, name="Oasis", status="active"),
                         Ecosystem(id=DELTA, name="Delta", status="active")])
        session.add_all([User(id=_user(name), display_name=name.title()) for name in PEOPLE])
        await session.flush()
        for name, rows in PEOPLE.items():
            for ecosystem, (status, role) in rows.items():
                session.add(Member(
                    id=_row(name, ecosystem), ecosystem_id=ecosystem, user_id=_user(name),
                    member_id=f"MEM-{name}-{ecosystem.int}", display_name=name.title(),
                    current_status=status, role=role,
                ))
        await session.commit()


def _app(factory) -> Sanic:
    app = Sanic(f"test-exit-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        async with factory() as session:
            rows = (await session.execute(
                select(Member).where(Member.user_id == _user(who)).order_by(Member.created_at)
            )).scalars().all()
        authorized = [row.ecosystem_id for row in rows if row.current_status == "active"]
        request.ctx.user = User(id=_user(who), display_name=who.title())
        request.ctx.member = next((row for row in rows if row.current_status == "active"), rows[0])
        request.ctx.authorized_ecosystem_ids = authorized
        request.ctx.selected_ecosystem_ids = [OASIS] if OASIS in authorized else authorized[:1]

    app.blueprint(exit_api_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await _seed(factory)
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


async def _call(env, method: str, who: str, path: str, body: dict | None = None):
    client = env.app.asgi_client
    kwargs = {"headers": {"x-test-as": who}}
    if method == "post":
        kwargs["json"] = body or {}
    _, response = await getattr(client, method)(f"/api/v1/exit{path}", **kwargs)
    return response


async def _file(env, who: str = "ben", **body):
    return await _call(env, "post", who, "/", {"ecosystem_id": str(OASIS), "reason": "Moving valleys.", **body})


async def _move(env, who: str, exit_id: str, status: str):
    return await _call(env, "post", who, f"/{exit_id}/status", {"new_status": status})


async def _status(env, exit_id) -> str:
    async with env.db() as session:
        return (await session.get(ExitRecord, uuid.UUID(str(exit_id)))).status


# --- Filing: self only ---------------------------------------------------------


async def test_a_member_files_their_own_exit_and_the_page_gets_what_it_reads(env):
    filed = await _file(env, "ben", exit_type="urgent")
    assert filed.status == 201, filed.text
    body = filed.json
    assert (body["member_name"], body["reason"], body["status"]) == ("Ben", "Moving valleys.", "declared")
    assert date.fromisoformat(body["target_completion_date"]) - date.fromisoformat(body["declared_date"]) == timedelta(days=7)
    assert body["caller_is_leaver"] is True and body["allowed_next"] == ["cancelled"]
    listed = await _call(env, "get", "cy", "/?q=valleys")  # search used to raise on a missing column
    assert [(item["member_name"], item["reason"]) for item in listed.json["items"]] == [("Ben", "Moving valleys.")]
    again = await _file(env, "ben")
    assert again.status == 409 and again.json["exit_id"] == body["id"]


@pytest.mark.parametrize("who, body, status", [
    ("cy", {"member_id": str(_row("ben"))}, 403),  # filing for someone else
    ("eve", {}, 403),                              # pending consent is not an active member
    ("fay", {}, 403),                              # no row in Oasis
    ("ben", {"exit_type": "eventually"}, 400),
])
async def test_filing_refusals(env, who, body, status):
    response = await _file(env, who, **body)
    assert response.status == status, response.text
    async with env.db() as session:
        assert (await session.execute(select(ExitRecord))).scalars().all() == []


# --- Moves: the leaver withdraws, a steward (not the leaver) finishes -----------


@pytest.mark.parametrize("who, to, status", [
    ("ben", "cancelled", 200),   # the leaver withdraws
    ("ada", "cancelled", 403),   # a steward cannot cancel someone's exit
    ("cy", "cancelled", 403),
    ("ada", "unwinding", 200),   # a steward starts the handoff
    ("ben", "unwinding", 403),
    ("cy", "unwinding", 403),
    ("ada", "completed", 200),   # a steward confirms the departure
    ("ben", "completed", 403),   # the leaver cannot self-complete
    ("cy", "completed", 403),
])
async def test_who_may_move_an_exit(env, who, to, status):
    filed = await _file(env, "ben")
    response = await _move(env, who, filed.json["id"], to)
    assert response.status == status, response.text
    assert await _status(env, filed.json["id"]) == (to if status == 200 else "declared")


async def test_a_steward_leaving_needs_another_steward_to_confirm(env):
    filed = await _file(env, "ada")
    assert (await _move(env, "ada", filed.json["id"], "completed")).status == 403
    assert (await _move(env, "ari", filed.json["id"], "completed")).status == 200


async def test_data_export_or_any_free_text_never_overwrites_the_status(env):
    filed = await _file(env, "ben")
    response = await _move(env, "ada", filed.json["id"], "export_requested")
    assert response.status == 400
    assert await _status(env, filed.json["id"]) == "declared"
    closed = await _move(env, "ben", filed.json["id"], "cancelled")
    assert closed.status == 200
    assert (await _move(env, "ben", filed.json["id"], "declared")).status == 409  # terminal


async def test_confirmed_departure_marks_the_member_exited_and_drops_them_from_consent(env):
    async with env.db() as session:
        session.add(Agreement(id=AGREEMENT, ecosystem_id=OASIS, agreement_id="AGR-1", type="policy",
                              title="Garden rota", status="active"))
        await session.commit()
        before = (await agreement_consent_summary(session, await session.get(Agreement, AGREEMENT)))["required"]
    filed = await _file(env, "ben")
    handoff = await _move(env, "ada", filed.json["id"], "unwinding")
    assert handoff.json["coordinator_id"] == str(_row("ada"))
    done = await _move(env, "ada", filed.json["id"], "completed")
    assert done.json["completed_date"] is not None
    async with env.db() as session:
        ben = await session.get(Member, _row("ben"))
        transition = (await session.execute(select(MemberStatusTransition))).scalar_one()
        after = (await agreement_consent_summary(session, await session.get(Agreement, AGREEMENT)))["required"]
    assert ben.current_status == "exited"
    assert (transition.from_status, transition.to_status, transition.member_id) == ("active", "exited", ben.id)
    assert after == before - 1
    # Ben no longer holds Oasis scope, but can still open his own exit record.
    own = await _call(env, "get", "ben", f"/{filed.json['id']}")
    assert own.status == 200 and own.json["status"] == "completed"


# --- Portable record ------------------------------------------------------------


async def _seed_governance_trail(env, *, linked: bool = True) -> None:
    """Ben's proposal, advice and consent; `linked=False` stores his advice and consent by name only (legacy rows)."""
    ben = _row("ben") if linked else None
    async with env.db() as session:
        proposal = Proposal(id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id="PROP-1", type="policy",
                            title="Share the tools", status="consent", proposer_member_id=_row("ben"))
        others = Proposal(id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id="PROP-2", type="policy",
                          title="Cy's plan", status="consent", proposer_member_id=_row("cy"))
        session.add_all([proposal, others])
        await session.flush()
        log = AdviceLog(id=uuid.uuid4(), proposal_id=others.id)
        record = ConsentRecord(id=uuid.uuid4(), proposal_id=proposal.id, consent_mode="consent")
        session.add_all([log, record])
        await session.flush()
        session.add_all([
            AdviceEntry(id=uuid.uuid4(), advice_log_id=log.id, advisor="Ben", advice_text="Start smaller.", member_id=ben),
            AdviceEntry(id=uuid.uuid4(), advice_log_id=log.id, advisor="Ada", advice_text="Ada's advice."),
            ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Ben", position="consent",
                               member_id=ben),
            ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Cy", position="object",
                               reason="Cy's private objection"),
            Agreement(id=AGREEMENT, ecosystem_id=OASIS, agreement_id="AGR-1", type="policy", title="Garden rota",
                      status="active"),
        ])
        await session.flush()
        session.add(AgreementMemberConsent(id=uuid.uuid4(), agreement_id=AGREEMENT, member_id=_row("ben"),
                                           agreement_version="1.0", attestation="I consent.",
                                           attested_at=datetime(2026, 10, 1)))
        await session.commit()


async def test_the_leaver_downloads_their_own_record_and_the_status_is_untouched(env):
    await _seed_governance_trail(env)
    filed = await _file(env, "ben")
    response = await _call(env, "get", "ben", f"/{filed.json['id']}/portable-record")
    assert response.status == 200, response.text
    record = response.json
    assert {m["ecosystem"] for m in record["memberships"]} == {"Oasis", "Delta"}
    assert [p["proposal_id"] for p in record["proposals_authored"]] == ["PROP-1"]
    assert [a["advice"] for a in record["advice_given"]] == ["Start smaller."]
    assert [(c["proposal_id"], c["position"]) for c in record["consent_positions"]] == [("PROP-1", "consent")]
    assert [a["agreement_id"] for a in record["agreements_consented"]] == ["AGR-1"]
    assert "Cy's private objection" not in response.text and "Ada's advice." not in response.text
    detail = await _call(env, "get", "ben", f"/{filed.json['id']}")
    assert (detail.json["status"], detail.json["data_export_requested"]) == ("declared", True)
    assert detail.json["data_export_completed"] is not None


@pytest.mark.parametrize("who, status", [("cy", 403), ("ada", 403), ("fay", 404)])
async def test_nobody_else_downloads_a_portable_record(env, who, status):
    filed = await _file(env, "ben")
    response = await _call(env, "get", who, f"/{filed.json['id']}/portable-record")
    assert response.status == status, response.text
    async with env.db() as session:
        assert (await session.get(ExitRecord, uuid.UUID(filed.json["id"]))).data_export_requested is False


OTHER_BEN = uuid.UUID(int=0xB3)


@pytest.mark.parametrize("namesake", [False, True])  # unique or shared, a name never claims a row
async def test_rows_follow_the_member_id_and_name_only_rows_are_left_out(env, namesake):
    await _seed_governance_trail(env, linked=False)  # Ben's legacy advice and consent rows carry no member id
    async with env.db() as session:
        if namesake:  # e.g. someone renamed to "Ben" after the old rows were written
            session.add(User(id=uuid.UUID(int=0xB2), display_name="Ben"))
            await session.flush()
            session.add(Member(id=OTHER_BEN, ecosystem_id=OASIS, user_id=uuid.UUID(int=0xB2),
                               member_id="MEM-other-ben", display_name="ben ", current_status="active"))
        proposal = Proposal(id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id="PROP-3", type="policy",
                            title="Night watch", status="consent", proposer_member_id=_row("cy"))
        session.add(proposal)
        await session.flush()
        record = ConsentRecord(id=uuid.uuid4(), proposal_id=proposal.id, consent_mode="consent")
        log = AdviceLog(id=uuid.uuid4(), proposal_id=proposal.id)
        session.add_all([record, log, TestReport(id=uuid.uuid4(), proposal_id=proposal.id, outcome="passed",
                                                  reporter_member_id=_row("ben"))])
        await session.flush()
        session.add_all([
            ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Ben", position="consent",
                               member_id=_row("ben")),
            ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Ben", position="object",
                               reason="The other Ben's objection", member_id=OTHER_BEN if namesake else _row("cy")),
            AdviceEntry(id=uuid.uuid4(), advice_log_id=log.id, advisor="Ben", advice_text="Rotate weekly.",
                        member_id=_row("ben")),
        ])
        await session.commit()
    filed = await _file(env, "ben")
    response = await _call(env, "get", "ben", f"/{filed.json['id']}/portable-record")
    record = response.json
    assert [(c["proposal_id"], c["position"]) for c in record["consent_positions"]] == [("PROP-3", "consent")]
    assert [a["advice"] for a in record["advice_given"]] == ["Rotate weekly."]
    assert [(t["proposal_id"], t["outcome"]) for t in record["test_reports_filed"]] == [("PROP-3", "passed")]
    assert "The other Ben's objection" not in response.text
    # Name-only rows are left out and counted, never guessed: a name can belong to someone else.
    assert "Start smaller." not in response.text
    assert [(entry["ecosystem"], entry["rows"]) for entry in record["omitted"]] == [("Oasis", 2)]
    assert [p["proposal_id"] for p in record["proposals_authored"]] == ["PROP-1"]
