"""Committed occurrence coverage across real producer paths."""
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from neos_agent.agent.governance_tools import join_domain
from neos_agent.api.agreements import register_ratified_proposal
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.auth.middleware import is_public_route
from neos_agent.db.models import (
    Agreement, AgreementCeremony, CircleMembership, Ecosystem, User, Member, Domain,
    SharesNeeds, Message, Proposal, EngagementEvent,
)
from neos_agent.services import exchange, member_messaging
from neos_agent.services.act_gates import _enter_proposal_stage
from neos_agent.services.engagement import event_view, record_event


@pytest_asyncio.fixture
async def community(db_session):
    eco = Ecosystem(id=uuid.uuid4(), name="Notification fixture", status="active", visibility="public")
    users = [User(id=uuid.uuid4(), display_name=name) for name in ("Author", "Responder", "Observer")]
    db_session.add_all([eco, *users])
    await db_session.flush()
    members = [Member(id=uuid.uuid4(), user_id=user.id, ecosystem_id=eco.id, member_id=f"MEM-{i}",
                      display_name=user.display_name, current_status="active", role="user") for i,user in enumerate(users)]
    db_session.add_all(members)
    domain = Domain(id=uuid.uuid4(), ecosystem_id=eco.id, domain_id="DOM-NOTIFY", name="Garden", status="active")
    db_session.add(domain)
    await db_session.commit()
    return SimpleNamespace(eco=eco, users=users, members=members, domain=domain)


async def test_all_message_producers_record_exact_private_recipients(db_session, community):
    c = community
    post = SharesNeeds(id=uuid.uuid4(), ecosystem_id=c.eco.id, domain_id=c.domain.id,
                       author_member_id=c.members[0].id, type="share", title="Seed workshop",
                       description="Fixture only", visibility="public", status=exchange.OPEN)
    db_session.add(post)
    await db_session.commit()
    viewer = await exchange.load_viewer(db_session, c.users[1].id)
    conversation_id, created = await exchange.respond(db_session, viewer, post, "Private first response")
    assert created
    again, created = await exchange.respond(db_session, viewer, post, "Private followup")
    assert again == conversation_id and not created
    prepared = await member_messaging.prepare_message(db_session, c.users[0].id, conversation_id, "Private reply")
    await member_messaging.post_message(db_session, prepared)
    await db_session.commit()
    messages = (await db_session.scalars(select(Message))).all()
    events = (await db_session.scalars(select(EngagementEvent))).all()
    assert len(messages) == len(events) == 3
    assert {e.event_key for e in events} == {f"message:{m.id}" for m in messages}
    for event in events:
        message = next(m for m in messages if event.event_key == f"message:{m.id}")
        expected = c.users[1].id if message.sender_id == c.members[0].id else c.users[0].id
        assert event.audience_user_ids == [str(expected)]
        assert await event_view(db_session, c.users[2].id, event) is None
        assert await event_view(db_session, expected, event, community=True) is None
        view = await event_view(db_session, expected, event)
        assert view is not None
        assert "Private" not in str(view)
        replay = await record_event(db_session, event_key=event.event_key, family="messages",
            event_type=event.event_type, source_kind="conversation", source_id=conversation_id,
            audience_user_ids=event.audience_user_ids)
        assert replay.id == event.id
    assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 3


async def test_proposal_return_to_advice_is_new_occurrence_and_rollback_erases_events(db_session, community):
    c = community
    proposal = Proposal(id=uuid.uuid4(), ecosystem_id=c.eco.id, proposal_id="PROP-NOTIFY",
                        type="operational", title="Workshop", status="draft", proposer_member_id=c.members[0].id)
    db_session.add(proposal)
    await db_session.commit()
    await _enter_proposal_stage(db_session, proposal, "advice", actor=c.members[0])
    await _enter_proposal_stage(db_session, proposal, "consent", actor=c.members[0])
    await _enter_proposal_stage(db_session, proposal, "advice", actor=c.members[0], evidence="Revise the proposal")
    events = (await db_session.scalars(select(EngagementEvent).order_by(EngagementEvent.created_at))).all()
    assert [event.event_type for event in events] == ["proposal.advice", "proposal.consent", "proposal.advice"]
    assert len({event.event_key for event in events}) == 3
    await db_session.rollback()
    assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 0


@pytest.mark.parametrize("producer", ["rest", "operator"])
async def test_domain_join_producers_emit_once_and_ignore_already_joined(db_session, community, producer):
    c = community
    if producer == "rest":
        app = Sanic("engagement-domain-" + uuid.uuid4().hex)
        app.ctx.db = async_sessionmaker(db_session.bind, expire_on_commit=False)
        app.blueprint(domains_api_bp)
        register_api_errors(app)

        @app.on_request
        async def authenticate(request):
            request.ctx.user = c.users[0]
            request.ctx.member = c.members[0]
            request.ctx.selected_ecosystem_ids = [c.eco.id]
            request.ctx.authorized_ecosystem_ids = [c.eco.id]

        async def join():
            _, response = await app.asgi_client.post(f"/api/v1/domains/{c.domain.id}/participation", json={})
            assert response.status == 201, response.text
    else:
        async def join():
            result = await join_domain({"domain_id": str(c.domain.id)}, db_session,
                                       [c.eco.id], caller_user_id=c.users[0].id)
            assert result["success"], result
            await db_session.commit()

    await join()
    await join()
    events = (await db_session.scalars(select(EngagementEvent))).all()
    assert len(events) == 1
    assert (events[0].family, events[0].event_type, events[0].source_id, events[0].actor_user_id) == (
        "community", "domain.participation_changed", c.domain.id, c.users[0].id,
    )
    assert await db_session.scalar(select(func.count()).select_from(CircleMembership)) == 1


@pytest.mark.parametrize("reactivation", [False, True])
async def test_operator_domain_join_and_event_rollback_together(db_session, community, reactivation):
    c = community
    domain_id, member_id, user_id, ecosystem_id = c.domain.id, c.members[0].id, c.users[0].id, c.eco.id
    if reactivation:
        db_session.add(CircleMembership(domain_id=domain_id, member_id=member_id, status="inactive"))
        await db_session.commit()
    result = await join_domain({"domain_id": str(domain_id)}, db_session,
                               [ecosystem_id], caller_user_id=user_id)
    assert result["success"], result
    assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 1
    await db_session.rollback()
    assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 0
    participation = await db_session.scalar(select(CircleMembership).where(
        CircleMembership.domain_id == domain_id, CircleMembership.member_id == member_id))
    assert (participation.status if participation else None) == ("inactive" if reactivation else None)


@pytest.mark.parametrize("amendment", [False, True])
@pytest.mark.parametrize("commit", [False, True])
async def test_registration_events_bind_ceremony_and_share_domain_transaction(db_session, community, amendment, commit):
    c = community
    c.members[0].role = "mod"
    agreement_id = uuid.uuid4() if amendment else None
    if amendment:
        db_session.add(Agreement(id=agreement_id, ecosystem_id=c.eco.id, agreement_id="AGR-ORIGINAL",
            title="Existing workshop terms", type="policy", status="active", version="1.0", text="Original terms"))
    proposal = Proposal(id=uuid.uuid4(), ecosystem_id=c.eco.id, proposal_id="PROP-REGISTER-EVENT",
        title="Workshop terms", type="policy", status="ratified", ratified_text="Approved workshop terms",
        amends_agreement_id=agreement_id, proposer_member_id=c.members[1].id)
    db_session.add(proposal)
    await db_session.commit()
    proposal_id, actor_id, observer_id = proposal.id, c.users[0].id, c.users[1].id

    agreement = await register_ratified_proposal(db_session, proposal, caller=c.members[0])
    registered_id = agreement.id
    event = (await db_session.scalars(select(EngagementEvent))).one()
    ceremony = (await db_session.scalars(select(AgreementCeremony).where(
        AgreementCeremony.agreement_id == registered_id, AgreementCeremony.outcome == "registered"))).one()
    action = "amended" if amendment else "registered"
    assert event.event_key == f"agreement:{registered_id}:{action}:{ceremony.id}"
    assert (event.family, event.event_type, event.actor_user_id) == ("governance", f"agreement.{action}", actor_id)
    assert (await event_view(db_session, observer_id, event))["source_id"] == str(registered_id)

    if commit:
        await db_session.commit()
        assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 1
        assert (await db_session.get(Proposal, proposal_id)).registered_agreement_id == registered_id
        persisted = await db_session.get(Agreement, registered_id)
        assert persisted.status == "active" and persisted.text == "Approved workshop terms"
    else:
        await db_session.rollback()
        assert await db_session.scalar(select(func.count()).select_from(EngagementEvent)) == 0
        assert await db_session.scalar(select(func.count()).select_from(AgreementCeremony)) == 0
        assert (await db_session.get(Proposal, proposal_id)).registered_agreement_id is None
        persisted = await db_session.get(Agreement, registered_id)
        assert (persisted.text if persisted else None) == ("Original terms" if amendment else None)


def test_public_engagement_routes_are_method_and_path_bounded():
    community_id = str(uuid.uuid4())
    assert is_public_route("/api/v1/communities", "GET")
    assert is_public_route(f"/api/v1/communities/{community_id}", "GET")
    assert not is_public_route("/api/v1/communities", "POST")
    assert not is_public_route("/api/v1/communities/private/export", "GET")
    assert is_public_route("/api/v1/engagement/unsubscribe", "POST")
    assert is_public_route("/api/v1/engagement/webhooks/resend", "POST")
    assert not is_public_route("/api/v1/engagement/webhooks/resend", "GET")
    assert not is_public_route("/api/v1/engagement/webhooks/resend/anything", "POST")
    assert not is_public_route("/api/v1/engagement/inbox", "GET")
