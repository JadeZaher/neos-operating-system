"""Configured entry requirements across enrollment, grading and subgroup entry."""
import json
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from neos_agent.api.agreements import record_member_consent
from neos_agent.api.auth import create_signup_member
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import ApiError, register_api_errors
from neos_agent.api.quizzes import quizzes_api_bp
from neos_agent.api.teams import teams_api_bp
from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import (
    Agreement, AgreementRequirement, Base, CircleMembership, Domain, Ecosystem, Member,
    NodeAdmin, NodeAdminAction, Team, TeamMembership, User,
)
from neos_agent.services.join_gates import join_gate_summary, quiz_fingerprint
from neos_agent.services.member_lifecycle import move_member, place_member


@pytest_asyncio.fixture
async def gates():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    eco, other, parent, child, team = [uuid.uuid4() for _ in range(5)]
    users = {name: uuid.uuid4() for name in ("entrant", "steward", "operator", "builder", "other")}
    async with factory() as session:
        session.add_all([Ecosystem(id=eco, name="Entry garden", visibility="public"),
                         Ecosystem(id=other, name="Other garden", visibility="public")])
        session.add_all([User(id=value, display_name=name) for name, value in users.items()])
        await session.flush()
        for name, value in users.items():
            session.add(Member(user_id=value, ecosystem_id=other if name in {"entrant", "other"} else eco,
                member_id=f"MEM-{name}", display_name=name, current_status="active",
                role="owner" if name in {"steward", "operator"} else "user",
                profile="builder" if name == "builder" else None))
        session.add(NodeAdmin(user_id=users["operator"], active=True))
        session.add(Domain(id=parent, ecosystem_id=eco, domain_id="DOM-parent", name="Parent", status="active"))
        await session.flush()
        session.add(Domain(id=child, ecosystem_id=eco, domain_id="DOM-child", name="Child", status="active", parent_domain_id=parent))
        session.add(Team(id=team, ecosystem_id=eco, name="Seed team"))
        await session.commit()
    app = Sanic(f"join-gates-{uuid.uuid4().hex}")
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def identity(request):
        name = request.headers.get("x-test-user", "entrant")
        async with factory() as session:
            request.ctx.user = await session.get(User, users[name])
            memberships = (await session.scalars(select(Member).where(Member.user_id == users[name]).order_by(Member.created_at, Member.id))).all()
            request.ctx.member = next((m for m in memberships if m.current_status == "active"), memberships[0] if memberships else None)
            request.ctx.authorized_ecosystem_ids = [m.ecosystem_id for m in memberships if m.current_status == "active"]
            request.ctx.selected_ecosystem_ids = request.ctx.authorized_ecosystem_ids
            request.ctx.is_node_admin = name == "operator"
    for blueprint in (ecosystems_api_bp, domains_api_bp, teams_api_bp, quizzes_api_bp):
        app.blueprint(blueprint)
    yield SimpleNamespace(db=factory, app=app, eco=eco, other=other, parent=parent, child=child, team=team, users=users)
    await engine.dispose()


async def call(gates, method, path, *, who="entrant", body=None):
    _, response = await getattr(gates.app.asgi_client, method)("/api/v1" + path,
        headers={"x-test-user": who}, **({"json": body} if body is not None else {}))
    return response.status, response.json


async def quiz(gates, *, scope="ecosystem", published=True, course=False):
    async with gates.db() as session:
        course_row = Course(ecosystem_id=gates.eco, domain_id=gates.parent if scope == "parent" else None,
                            title="Onboarding course", is_onboarding_required=True) if course else None
        if course_row:
            session.add(course_row)
            await session.flush()
        row = Quiz(ecosystem_id=gates.other if scope == "other" else gates.eco,
            domain_id=gates.parent if scope == "parent" and not course else gates.child if scope == "child" else None,
            team_id=gates.team if scope == "team" else None, title=f"{scope} entry", mode="standard",
            course_id=course_row.id if course_row else None, is_entry_quiz=not course, is_published=published,
            survey_json={"pages": [{"elements": [{"type": "radiogroup", "name": "entry", "title": "Choose safe practice",
                "choices": ["consent", "force"], "correctAnswer": "consent"}]}]}, passing_score=100)
        session.add(row)
        await session.commit()
        return row.id


async def member(gates, name="entrant"):
    async with gates.db() as session:
        return await session.scalar(select(Member).where(Member.user_id == gates.users[name], Member.ecosystem_id == gates.eco))


async def join(gates):
    return await call(gates, "post", f"/ecosystems/{gates.eco}/join", body={})


async def submit(gates, quiz_id, *, who="entrant", answer="consent"):
    return await call(gates, "post", f"/quizzes/{quiz_id}/submit", who=who, body={"survey_results": {"entry": answer}})


async def test_no_quiz_allows_join_and_existing_active_is_not_retroactively_demoted(gates):
    status, payload = await join(gates)
    assert status == 201 and payload["membership_status"] == "active"
    assert payload["join_gates"]["required_quizzes"] == []
    await quiz(gates, published=False)
    status, payload = await call(gates, "get", f"/ecosystems/{gates.eco}/join-gates")
    assert status == 200 and payload["join_gates"]["grandfathered"]
    assert (await member(gates)).current_status == "active"


async def test_pending_can_take_published_quiz_without_answers_and_cannot_forge_grade_or_other_member(gates):
    qid = await quiz(gates)
    status, payload = await join(gates)
    assert status == 201 and payload["status"] == "quiz_required"
    assert payload["membership_status"] == "pending_consent"
    status, detail = await call(gates, "get", f"/quizzes/{qid}")
    assert status == 200 and "correctAnswer" not in json.dumps(detail)
    status, author_candidate = await call(gates, "get", f"/quizzes/{qid}?candidate=1", who="steward")
    assert status == 200 and "correctAnswer" not in json.dumps(author_candidate)
    for spoof in ({"is_passed": True, "score": 100}, {"member_id": str(gates.users["operator"])}):
        status, _ = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": {"entry": "force"}, **spoof})
        assert status == 400
    status, failed = await submit(gates, qid, answer="force")
    assert status == 201 and failed["grading"]["is_passed"] is False
    assert (await member(gates)).current_status == "pending_consent"
    status, passed = await submit(gates, qid)
    assert status == 201 and passed["grading"]["is_passed"] is True
    assert (await member(gates)).current_status == "active"
    async with gates.db() as session:
        attempt = await session.scalar(select(QuizResult).where(QuizResult.is_passed.is_(True)))
        assert attempt.completion_verified
        assert attempt.member_id == (await member(gates)).id
        assert attempt.graded_fingerprint == quiz_fingerprint(await session.get(Quiz, qid))


@pytest.mark.parametrize("quiz_first", [True, False])
async def test_quiz_and_agreement_both_required_in_either_order(gates, quiz_first):
    qid = await quiz(gates)
    async with gates.db() as session:
        agreement = Agreement(ecosystem_id=gates.eco, agreement_id="AGR-entry", type="uaf", title="Entry agreement",
                              version="1", status="active", requires_explicit_consent=True, alignment_points=0)
        session.add(agreement)
        await session.flush()
        session.add(AgreementRequirement(agreement_id=agreement.id, target_kind="ecosystem_membership", enforcement="block_join", is_active=True))
        await session.commit()
        aid = agreement.id
    await join(gates)
    if quiz_first:
        await submit(gates, qid)
    async with gates.db() as session:
        row = await session.get(Member, (await member(gates)).id)
        await record_member_consent(session, await session.get(Agreement, aid), row, "I agree to these current terms.")
        await session.commit()
    if not quiz_first:
        assert (await member(gates)).current_status == "pending_consent"
        await submit(gates, qid)
    assert (await member(gates)).current_status == "active"


async def test_no_retakes_is_per_current_verified_version_and_preserves_prior_history(gates):
    qid = await quiz(gates)
    async with gates.db() as session:
        configured = await session.get(Quiz, qid)
        configured.allow_retakes = False
        agreement = Agreement(ecosystem_id=gates.eco, agreement_id="AGR-current-attempt", type="uaf", title="Current terms", version="1", status="active", requires_explicit_consent=True, alignment_points=0)
        session.add(agreement)
        await session.flush()
        session.add(AgreementRequirement(agreement_id=agreement.id, target_kind="ecosystem_membership", enforcement="block_join", is_active=True))
        await session.commit()
        aid = agreement.id
    await join(gates)
    assert (await submit(gates, qid))[0] == 201
    assert (await submit(gates, qid))[0] == 409
    assert (await member(gates)).current_status == "pending_consent"
    async with gates.db() as session:
        configured = await session.get(Quiz, qid)
        configured.survey_json = {"elements": [{"type": "radiogroup", "name": "entry", "title": "Revised current practice", "choices": ["consent", "force"], "correctAnswer": "consent"}]}
        row = await session.get(Member, (await member(gates)).id)
        await record_member_consent(session, await session.get(Agreement, aid), row, "I agree to the current terms.")
        await session.commit()
    assert (await member(gates)).current_status == "pending_consent"
    status, payload = await submit(gates, qid)
    assert status == 201, payload
    assert (await member(gates)).current_status == "active"
    assert (await submit(gates, qid))[0] == 409
    async with gates.db() as session:
        assert await session.scalar(select(func.count()).select_from(QuizResult).where(QuizResult.quiz_id == qid)) == 2


async def test_legacy_unverified_and_invalid_submissions_do_not_consume_current_attempt_but_valid_failure_does(gates):
    qid = await quiz(gates)
    await join(gates)
    async with gates.db() as session:
        configured = await session.get(Quiz, qid)
        configured.allow_retakes = False
        row = await session.get(Member, (await member(gates)).id)
        session.add(QuizResult(quiz_id=qid, member_id=row.id, is_passed=True, score=100, graded_fingerprint=quiz_fingerprint(configured), completion_verified=False))
        await session.commit()
    status, _ = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": {"entry": {"unsupported": True}}})
    assert status == 400
    status, payload = await submit(gates, qid, answer="force")
    assert status == 201 and payload["result"]["completion_verified"] is True and payload["result"]["is_passed"] is False
    assert (await submit(gates, qid))[0] == 409
    status, result = await call(gates, "get", f"/quiz-results/{payload['result']['id']}")
    assert status == 200 and result["attempt_policy"]["can_submit"] is False
    async with gates.db() as session:
        configured = await session.get(Quiz, qid)
        configured.survey_json = {"elements": [{"type": "text", "name": "entry", "title": "New version", "correctAnswer": "consent"}]}
        await session.commit()
    status, result = await call(gates, "get", f"/quiz-results/{payload['result']['id']}")
    assert status == 200 and result["attempt_policy"] == {"can_submit": True, "result_is_current": False, "scope": "current_verified_version"}
    assert (await submit(gates, qid))[0] == 201


async def test_unpublished_or_ungradable_configured_quiz_blocks_activation_and_legacy_pass_does_not_count(gates):
    qid = await quiz(gates, published=False)
    status, payload = await join(gates)
    assert status == 201 and payload["status"] == "quiz_unavailable"
    assert (await submit(gates, qid))[0] == 404
    async with gates.db() as session:
        row = await session.get(Member, (await member(gates)).id)
        session.add(QuizResult(quiz_id=qid, member_id=row.id, is_passed=True, score=100))
        steward = await session.scalar(select(Member).where(Member.user_id == gates.users["steward"]))
        with pytest.raises(ApiError) as refusal:
            await move_member(session, row, "active", caller=steward)
        assert refusal.value.extra["code"] == "JOIN_QUIZ_UNAVAILABLE"
        configured = await session.get(Quiz, qid)
        configured.is_published = True
        await session.commit()
    status, payload = await join(gates)
    assert status == 409 and payload["code"] == "JOIN_QUIZ_REQUIRED"
    async with gates.db() as session:
        (await session.get(Quiz, qid)).survey_json = {"pages": [{"elements": [{"name": "unsupported", "type": "unknown-widget"}]}]}
        await session.commit()
    assert (await join(gates))[1]["code"] == "JOIN_QUIZ_UNAVAILABLE"


async def test_domain_lineage_course_and_team_require_all_applicable_passes_and_exact_current_content(gates):
    await join(gates)
    eco_quiz = await quiz(gates)
    parent_quiz = await quiz(gates, scope="parent", course=True)
    child_quiz = await quiz(gates, scope="child")
    team_quiz = await quiz(gates, scope="team")
    wrong = await quiz(gates, scope="other")
    for qid in (eco_quiz, parent_quiz):
        assert (await submit(gates, qid))[0] == 201
    assert (await submit(gates, wrong))[0] == 201
    status, gate = await call(gates, "get", f"/domains/{gates.child}/join-gates")
    assert status == 200 and {q["id"] for q in gate["join_gates"]["required_quizzes"]} == {str(q) for q in (eco_quiz, parent_quiz, child_quiz)}
    assert (await call(gates, "post", f"/domains/{gates.child}/participation", body={}))[0] == 409
    assert (await submit(gates, child_quiz))[0] == 201
    assert (await call(gates, "post", f"/domains/{gates.child}/participation", body={}))[0] == 201
    assert (await call(gates, "post", f"/teams/{gates.team}/join", body={}))[0] == 409
    assert (await submit(gates, team_quiz))[0] == 201
    async with gates.db() as session:
        (await session.get(Quiz, team_quiz)).passing_score = 90
        await session.commit()
    assert (await call(gates, "post", f"/teams/{gates.team}/join", body={}))[0] == 409
    await submit(gates, team_quiz)
    assert (await call(gates, "post", f"/teams/{gates.team}/join", body={}))[0] == 201


async def test_legacy_course_only_scope_is_enforced_and_course_move_invalidates_pass(gates):
    async with gates.db() as session:
        course = Course(ecosystem_id=gates.eco, title="Legacy configured course", is_onboarding_required=True)
        session.add(course)
        await session.flush()
        configured = Quiz(course_id=course.id, ecosystem_id=None, title="Course-only entry", is_published=True,
            survey_json={"pages": [{"elements": [{"name": "entry", "correctAnswer": "consent", "type": "text"}]}]})
        session.add(configured)
        await session.commit()
        qid, course_id = configured.id, course.id
    status, payload = await join(gates)
    assert status == 201 and payload["status"] == "quiz_required"
    assert [q["id"] for q in payload["join_gates"]["required_quizzes"]] == [str(qid)]
    status, detail = await call(gates, "get", f"/quizzes/{qid}")
    assert status == 200 and "correctAnswer" not in json.dumps(detail)
    assert (await submit(gates, qid))[0] == 201
    assert (await member(gates)).current_status == "active"
    async with gates.db() as session:
        (await session.get(Course, course_id)).domain_id = gates.child
        await session.commit()
    status, payload = await call(gates, "post", f"/domains/{gates.child}/participation", body={})
    assert status == 409 and payload["code"] == "JOIN_QUIZ_REQUIRED"
    await submit(gates, qid)
    assert (await call(gates, "post", f"/domains/{gates.child}/participation", body={}))[0] == 201


async def test_only_explicit_entrant_node_admin_bypasses_quizzes_with_public_audit_no_fabricated_pass(gates):
    await quiz(gates, scope="team", published=False)
    status, receipt = await call(gates, "post", f"/teams/{gates.team}/join", who="operator", body={})
    assert status == 201 and receipt["join_gates"]["quiz_bypass"] == {"applied": True, "reason": "node_admin"}
    assert receipt["join_gates"]["required_quizzes"][0]["status"] == "bypassed"
    assert (await call(gates, "post", f"/teams/{gates.team}/join", who="builder", body={}))[0] == 409
    builder = await member(gates, "builder")
    status, _ = await call(gates, "post", f"/teams/{gates.team}/members", who="operator", body={"member_id": str(builder.id)})
    assert status == 409
    async with gates.db() as session:
        assert await session.scalar(select(func.count()).select_from(QuizResult)) == 0
        event = await session.scalar(select(NodeAdminAction).where(NodeAdminAction.action == "join_quiz_bypass"))
        assert event.actor_user_id == gates.users["operator"] and event.safe_summary["basis"] == "entrant_node_admin"
        (await session.scalar(select(NodeAdmin).where(NodeAdmin.user_id == gates.users["operator"]))).active = False
        await session.execute(TeamMembership.__table__.delete())
        await session.commit()
    assert (await call(gates, "post", f"/teams/{gates.team}/join", who="operator", body={}))[0] == 409


async def test_admin_quiz_exemption_does_not_bypass_agreement_consent(gates):
    await quiz(gates, scope="team", published=False)
    async with gates.db() as session:
        agreement = Agreement(ecosystem_id=gates.eco, agreement_id="AGR-admin", type="uaf", title="Current agreement",
                              version="1", status="active", requires_explicit_consent=True)
        session.add(agreement)
        await session.flush()
        session.add(AgreementRequirement(agreement_id=agreement.id, target_kind="ecosystem_membership", enforcement="block_join", is_active=True))
        await session.commit()
    status, refusal = await call(gates, "post", f"/teams/{gates.team}/join", who="operator", body={})
    assert status == 409 and refusal["code"] == "CONSENT_REQUIRED"
    assert refusal["join_gates"]["quiz_bypass"]["applied"]


async def test_node_admin_ecosystem_join_uses_exemption_and_never_inherits_profile_authority(gates):
    eco_id = uuid.uuid4()
    async with gates.db() as session:
        session.add(Ecosystem(id=eco_id, name="Configured entry", visibility="public"))
        await session.flush()
        session.add(Quiz(ecosystem_id=eco_id, title="Unavailable entry", is_entry_quiz=True, is_published=False))
        await session.commit()
    status, payload = await call(gates, "post", f"/ecosystems/{eco_id}/join", who="operator", body={})
    assert status == 201 and payload["membership_status"] == "active"
    assert payload["join_gates"]["quiz_bypass"]["applied"]
    status, payload = await call(gates, "post", f"/ecosystems/{eco_id}/join", who="builder", body={})
    assert status == 201 and payload["membership_status"] == "pending_consent"
    assert not payload["join_gates"]["quiz_bypass"]["applied"]


def test_join_gate_migration_preserves_active_members_and_does_not_trust_legacy_passes():
    import importlib.util
    from pathlib import Path
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect, text
    path = Path(__file__).resolve().parents[1] / "alembic/versions/x4d8a2c6f0b3_join_quiz_gates.py"
    spec = importlib.util.spec_from_file_location("join_quiz_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE quizzes (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE quiz_results (id CHAR(32) PRIMARY KEY, is_passed BOOLEAN)"))
        connection.execute(text("CREATE TABLE members (id CHAR(32) PRIMARY KEY, current_status VARCHAR(50))"))
        connection.execute(text("INSERT INTO members VALUES ('old', 'active')"))
        connection.execute(text("INSERT INTO quiz_results VALUES ('old-pass', 1)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.upgrade()
        assert "team_id" in {column["name"] for column in inspect(connection).get_columns("quizzes")}
        assert connection.scalar(text("SELECT graded_fingerprint FROM quiz_results")) is None
        assert connection.scalar(text("SELECT completion_verified FROM quiz_results")) == 0
        assert connection.scalar(text("SELECT current_status FROM members")) == "active"
    engine.dispose()


async def test_signup_rejoin_and_agent_joins_share_gate_and_do_not_change_existing_author_policy(gates):
    from neos_agent.agent.governance_tools import join_domain
    from neos_agent.api.policy import can_manage_proposal
    from neos_agent.db.models import Proposal
    qid = await quiz(gates)
    async with gates.db() as session:
        user = await session.get(User, gates.users["entrant"])
        row, missing = await create_signup_member(session, user=user, ecosystem=await session.get(Ecosystem, gates.eco),
                                                  member_id="MEM-new", display_name="Entrant")
        assert row.current_status == "pending_consent" and not missing
        row.current_status = "exited"
        await session.flush()
        returned = await place_member(session, user_id=user.id, ecosystem=await session.get(Ecosystem, gates.eco), display_name="Entrant", member_key="same")
        assert returned.member.id == row.id and row.current_status == "pending_consent"
        old = Proposal(ecosystem_id=gates.eco, proposer_member_id=row.id)
        assert can_manage_proposal(row, old)
        await session.commit()
    await submit(gates, qid)
    await quiz(gates, scope="child")
    async with gates.db() as session:
        refusal = await join_domain({"domain_id": str(gates.child)}, session, [gates.eco], caller_user_id=gates.users["entrant"])
        assert not refusal["success"] and refusal["code"] == "JOIN_QUIZ_REQUIRED"
        assert await session.scalar(select(func.count()).select_from(CircleMembership)) == 0


async def test_seed_readiness_questionnaire_requires_verified_completion_without_grading_preferences(gates):
    from scripts.seed_quizzes import _onboarding_readiness_survey
    schema = _onboarding_readiness_survey()
    questions = schema["pages"][0]["elements"]
    assert [question["type"] for question in questions] == ["boolean", "boolean", "boolean", "comment", "radiogroup"]
    assert all("correctAnswer" not in question and "isRequired" not in question for question in questions)
    async with gates.db() as session:
        configured = Quiz(ecosystem_id=gates.eco, title="Existing readiness questionnaire", mode="standard",
            survey_json=schema, is_entry_quiz=True, is_published=True)
        session.add(configured)
        await session.commit()
        qid = configured.id
    status, pending = await join(gates)
    assert status == 201 and pending["status"] == "quiz_required"
    assert pending["join_gates"]["required_quizzes"][0]["completion_mode"] == "completion"
    valid = {"read_agreements": False, "understand_consent": False, "know_steward": False,
             "expectations": "I want to participate in community decisions.", "commitment": "1-2 hours"}
    invalid = [{}, {"unknown": "answer"}, {"read_agreements": False}, {**valid, "read_agreements": "false"},
               {**valid, "expectations": "   "}, {**valid, "commitment": "invented-choice"}, {**valid, "injected": True}]
    for answers in invalid:
        status, refusal = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": answers})
        assert status == 400 and refusal["code"] in {"QUIZ_ANSWERS_INVALID", "QUIZ_ANSWERS_INCOMPLETE"}
    assert (await member(gates)).current_status == "pending_consent"
    assert (await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": valid, "completion_verified": True}))[0] == 400
    status, completed = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": valid})
    assert status == 201 and completed["result"]["completion_verified"] is True
    assert completed["grading"]["is_passed"] is None and completed["grading"]["completion_mode"] == "completion"
    assert completed["join_gates"]["required_quizzes"][0]["status"] == "completed"
    assert (await member(gates)).current_status == "active"
    async with gates.db() as session:
        result = await session.scalar(select(QuizResult).where(QuizResult.quiz_id == qid))
        assert result.is_passed is None and result.completion_verified
        assert result.member_id == (await member(gates)).id
        assert result.graded_fingerprint == quiz_fingerprint(await session.get(Quiz, qid))


@pytest.mark.parametrize("schema", [{}, {"pages": []}, {"pages": [{"elements": [{"name": "unsupported", "type": "matrixdynamic"}]}]}])
async def test_empty_or_unsupported_configured_questionnaires_remain_unavailable(gates, schema):
    async with gates.db() as session:
        configured = Quiz(ecosystem_id=gates.eco, title="Needs repair", survey_json=schema, is_entry_quiz=True, is_published=True)
        session.add(configured)
        await session.commit()
        qid = configured.id
    assert (await join(gates))[1]["status"] == "quiz_unavailable"
    status, refusal = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": {}})
    assert status == 409 and refusal["code"] == "QUIZ_CONFIGURATION_INVALID"


async def test_global_quiz_target_is_scope_context_for_actual_caller_never_an_identity_override(gates):
    await join(gates)
    local_quiz = await quiz(gates)
    async with gates.db() as session:
        shared = Quiz(title="Shared questionnaire", visibility="public", is_published=True,
                      survey_json={"elements": [{"name": "purpose", "type": "comment"}]})
        session.add(shared)
        await session.commit()
        shared_id = shared.id
    body = {"survey_results": {"purpose": "I want to learn how to participate."}, "target_ecosystem_id": str(gates.eco)}
    status, actual = await call(gates, "post", f"/quizzes/{shared_id}/submit", body=body)
    assert status == 201 and actual["result"]["member_id"] == str((await member(gates)).id)
    assert actual["result"]["completion_verified"] and actual["result"]["is_passed"] is None
    assert (await call(gates, "post", f"/quizzes/{shared_id}/submit", who="other", body=body))[0] == 404
    assert (await call(gates, "post", f"/quizzes/{shared_id}/submit", body={**body, "target_ecosystem_id": str(uuid.uuid4())}))[0] == 404
    assert (await call(gates, "post", f"/quizzes/{local_quiz}/submit", body={"survey_results": {"entry": "consent"},
        "target_ecosystem_id": str(gates.other)}))[0] == 400
    assert (await call(gates, "post", f"/quizzes/{shared_id}/submit", body={**body, "member_id": str(gates.users["operator"])}))[0] == 400
    async with gates.db() as session:
        assert await session.scalar(select(func.count()).select_from(QuizResult).where(QuizResult.quiz_id == shared_id)) == 1


@pytest.mark.parametrize("kind,choices,correct,wrong", [
    ("radiogroup", ["A", "a"], "A", "a"),
    ("dropdown", [1, "1"], 1, "1"),
    ("radiogroup", [1.0, "1"], 1.0, "1"),
    ("radiogroup", [False, "false"], False, "false"),
    ("checkbox", ["A", "a", 1, "1"], ["A", 1], ["a", "1"]),
])
async def test_submission_keeps_choice_case_and_json_types_in_grade_and_pending_gate(gates, kind, choices, correct, wrong):
    qid = await quiz(gates)
    async with gates.db() as db:
        configured = await db.get(Quiz, qid)
        configured.survey_json = {"elements": [{"type": kind, "name": "entry", "choices": choices, "correctAnswer": correct}]}
        await db.commit()
    assert (await join(gates))[1]["membership_status"] == "pending_consent"
    status, failed = await submit(gates, qid, answer=wrong)
    assert status == 201 and failed["result"]["completion_verified"] is True
    assert failed["grading"]["is_passed"] is False
    assert failed["grading"]["result_metadata"]["perQuestion"][0]["isCorrect"] is False
    assert (await member(gates)).current_status == "pending_consent"
    status, passed = await submit(gates, qid, answer=list(reversed(correct)) if isinstance(correct, list) else int(correct) if type(correct) is float else correct)
    assert status == 201 and passed["grading"]["is_passed"] is True
    assert (await member(gates)).current_status == "active"


@pytest.mark.parametrize("kind,correct,wrong", [("boolean", False, "false"), ("rating", 1, "1"), ("rating", 1, True)])
async def test_wrong_typed_boolean_and_rating_never_create_a_passing_attempt(gates, kind, correct, wrong):
    qid = await quiz(gates)
    async with gates.db() as db:
        (await db.get(Quiz, qid)).survey_json = {"elements": [{"type": kind, "name": "entry", "correctAnswer": correct}]}
        await db.commit()
    await join(gates)
    assert (await submit(gates, qid, answer=wrong))[0] == 400
    assert (await member(gates)).current_status == "pending_consent"
    async with gates.db() as db:
        assert await db.scalar(select(func.count()).select_from(QuizResult)) == 0
    assert (await submit(gates, qid, answer=correct))[1]["grading"]["is_passed"] is True


async def test_text_grading_intentionally_normalizes_whitespace_and_case(gates):
    qid = await quiz(gates)
    async with gates.db() as db:
        (await db.get(Quiz, qid)).survey_json = {"elements": [{"type": "text", "name": "entry", "correctAnswer": "Consent"}]}
        await db.commit()
    await join(gates)
    assert (await submit(gates, qid, answer="  CONSENT  "))[1]["grading"]["is_passed"] is True


async def test_own_result_by_id_uses_actual_second_membership_and_never_admin_or_steward_authority(gates):
    qid = await quiz(gates)
    await join(gates)
    target = await member(gates)
    assert target.current_status == "pending_consent"
    _, failed = await submit(gates, qid, answer="force")
    failed_id = failed["result"]["id"]
    await submit(gates, qid)
    status, result = await call(gates, "get", f"/quiz-results/{failed_id}")
    assert status == 200 and result["id"] == failed_id
    assert result["member_id"] == str(target.id) and result["is_passed"] is False
    assert result["survey_results"] == {"entry": "force"} and result["completion_verified"] is True
    assert result["quiz"]["title"] == "ecosystem entry" and "correctAnswer" not in json.dumps(result)
    for who in ("steward", "operator", "other"):
        assert (await call(gates, "get", f"/quiz-results/{failed_id}", who=who))[0] == 404
    assert (await call(gates, "get", f"/quiz-results/{uuid.uuid4()}"))[0] == 404
    assert (await call(gates, "get", f"/quiz-results/{failed_id}"))[1] == result


async def test_full_false_readiness_result_reloads_for_owner_in_pending_second_ecosystem(gates):
    qid = await quiz(gates)
    answers = {"ready": False, "available": False, "help": False, "comment": "I need time", "path": "learn"}
    async with gates.db() as db:
        (await db.get(Quiz, qid)).survey_json = {"elements": [
            *[{"name": name, "type": "boolean"} for name in ("ready", "available", "help")],
            {"name": "comment", "type": "comment"}, {"name": "path", "type": "radiogroup", "choices": ["learn", "help"]},
        ]}
        agreement = Agreement(ecosystem_id=gates.eco, agreement_id="AGR-result-owner", type="uaf", title="Entry agreement", version="1", status="active", requires_explicit_consent=True, alignment_points=0)
        db.add(agreement)
        await db.flush()
        db.add(AgreementRequirement(agreement_id=agreement.id, target_kind="ecosystem_membership", enforcement="block_join", is_active=True))
        await db.commit()
    await join(gates)
    status, submitted = await call(gates, "post", f"/quizzes/{qid}/submit", body={"survey_results": answers})
    assert status == 201 and submitted["result"]["is_passed"] is None
    assert (await member(gates)).current_status == "pending_consent"
    path = f"/quiz-results/{submitted['result']['id']}"
    for _ in range(2):
        status, result = await call(gates, "get", path)
        assert status == 200 and result["survey_results"] == answers
        assert result["completion_verified"] is True and result["is_passed"] is None
    assert (await call(gates, "get", path, who="operator"))[0] == 404


async def test_ordinary_steward_quiz_lookup_keeps_member_scope_and_cannot_enter_support_catalog(gates):
    from neos_agent.api.node_admin import node_admin_api_bp
    gates.app.blueprint(node_admin_api_bp)
    qid = await quiz(gates)
    status, available = await call(gates, "get", f"/quizzes?ecosystem_id={gates.eco}", who="steward")
    assert status == 200 and str(qid) in {item["id"] for item in available["items"]}
    status, _ = await call(gates, "get", f"/node-admin/resources/quizzes?organization_id={gates.eco}", who="steward")
    assert status == 403
