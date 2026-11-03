"""Community engagement privacy, policy and transaction contracts."""
from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import uuid

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from neos_agent.api.communities import communities_api_bp
from neos_agent.api.engagement import engagement_api_bp, require_engagement_write
from neos_agent.api.errors import ApiError, register_api_errors
from neos_agent.db.models import (
    CircleMembership, Collaboration, Conversation, ConversationParticipant, Domain,
    Ecosystem, Member, Proposal, SharesNeeds, Team, TeamMembership, User,
)
from neos_agent.db.models.engagement import (
    EngagementEvent, EngagementInboxItem, EngagementPreference, EngagementSubscription, NotificationContact,
)
from neos_agent.services import engagement as service


async def seed_world(factory):
    ids = {name: uuid.uuid4() for name in (
        "eco", "other_eco", "hidden_eco", "owner", "peer", "other", "dual", "stranger",
        "owner_member", "peer_member", "other_member", "dual_member", "dual_other_member",
        "domain", "target_domain", "team", "proposal", "collab", "post", "conversation")}
    async with factory() as session:
        session.add_all([
            Ecosystem(id=ids["eco"], name="Community One", visibility="public", status="active", description="Shared purpose"),
            Ecosystem(id=ids["other_eco"], name="Community Two", visibility="public", status="active"),
            Ecosystem(id=ids["hidden_eco"], name="Hidden community sentinel", visibility="private", status="active"),
        ])
        for name in ("owner", "peer", "other", "dual", "stranger"):
            session.add(User(id=ids[name], username="engagement-" + name, display_name=name, phone="private-phone"))
        await session.flush()
        for name, user, ecosystem in (
            ("owner_member", "owner", "eco"), ("peer_member", "peer", "eco"), ("other_member", "other", "other_eco"),
            ("dual_member", "dual", "eco"), ("dual_other_member", "dual", "other_eco"),
        ):
            session.add(Member(id=ids[name], user_id=ids[user], ecosystem_id=ids[ecosystem],
                member_id=name, display_name=user, current_status="active", role="user"))
        await session.flush()
        session.add_all([
            Domain(id=ids["domain"], ecosystem_id=ids["eco"], domain_id="workshop", name="Workshop", status="active"),
            Domain(id=ids["target_domain"], ecosystem_id=ids["other_eco"], domain_id="garden", name="Garden", status="active"),
            Team(id=ids["team"], ecosystem_id=ids["eco"], name="Workshop team", is_active=True),
            Proposal(id=ids["proposal"], ecosystem_id=ids["eco"], proposal_id="PROP-ENG", type="policy",
                title="Private proposal sentinel", status="advice", proposer_member_id=ids["owner_member"]),
            Conversation(id=ids["conversation"], ecosystem_id=ids["eco"], created_by=ids["owner_member"],
                         type="dm", title="Private message title sentinel"),
        ])
        await session.flush()
        for member, domain in (("owner_member", "domain"), ("peer_member", "domain"),
                               ("other_member", "target_domain"), ("dual_member", "domain"),
                               ("dual_other_member", "target_domain")):
            session.add(CircleMembership(domain_id=ids[domain], member_id=ids[member], status="active"))
        session.add_all([
            TeamMembership(team_id=ids["team"], member_id=ids["peer_member"]),
            SharesNeeds(id=ids["post"], ecosystem_id=ids["eco"], domain_id=ids["domain"],
                        author_member_id=ids["owner_member"], type="need", title="Public opportunity",
                        description="Private body not in preview", visibility="public", status="active"),
            Collaboration(id=ids["collab"], source_domain_id=ids["domain"], target_domain_id=ids["target_domain"],
                          title="Shared workshop", status="active", proposed_by_member_id=ids["owner_member"]),
            ConversationParticipant(conversation_id=ids["conversation"], member_id=ids["owner_member"]),
            ConversationParticipant(conversation_id=ids["conversation"], member_id=ids["peer_member"]),
        ])
        await session.commit()
    return ids


@pytest_asyncio.fixture
async def engagement_world(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    return factory, await seed_world(factory)


async def make_event(session, ids, *, key="proposal-one", kind="proposal", family="governance", audience=None):
    return await service.record_event(session, event_key=key, family=family, event_type=family + ".changed",
        source_kind=kind, source_id=ids[{"collaboration": "collab", "share": "post"}.get(kind, kind)],
        ecosystem_id=ids["eco"], actor_user_id=ids["owner"], audience_user_ids=audience)


async def test_event_and_domain_write_rollback_atomically(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        proposal = await session.get(Proposal, ids["proposal"])
        proposal.title = "Rolled back mutation"
        await make_event(session, ids)
        await session.rollback()
    async with factory() as session:
        assert await session.scalar(select(func.count(EngagementEvent.id))) == 0
        assert (await session.get(Proposal, ids["proposal"])).title == "Private proposal sentinel"


async def test_event_replay_idempotent_but_new_occurrence_preserved(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        first = await make_event(session, ids)
        repeated = await make_event(session, ids)
        second = await make_event(session, ids, key="proposal-return-to-advice")
        assert first.id == repeated.id and first.id != second.id
        await session.commit()
        assert await session.scalar(select(func.count(EngagementEvent.id))) == 2


async def assert_untargeted_event_appears_in_activity(factory, ids):
    async with factory() as session:
        event = await make_event(session, ids)
        event_id = event.id
        await make_event(session, ids, key="private-targeted", audience=[ids["peer"]])
        await session.commit()
    async with factory() as session:
        assert await session.scalar(select(EngagementEvent.id).where(
            EngagementEvent.audience_user_ids.is_(None))) == event_id
        page = await service.activity_page(session, ids["peer"])
        assert [item["id"] for item in page["items"]] == [str(event_id)]


async def test_untargeted_recorded_event_appears_in_activity(engagement_world):
    await assert_untargeted_event_appears_in_activity(*engagement_world)


@pytest.mark.parametrize("old_families,old_channels,old_muted,new_families,new_channels", [
    (["governance"], ["in_app"], False, ["governance"], ["in_app", "email"]),
    (["opportunities"], ["email"], False, ["opportunities", "governance"], ["email"]),
    (["opportunities"], ["email"], False, ["governance"], ["email"]),
    ([], [], True, ["governance"], ["email"]),
    (["governance"], ["email"], True, ["governance"], ["email"]),
])
async def test_widening_follow_does_not_backfill_external_events(engagement_world, monkeypatch,
        old_families, old_channels, old_muted, new_families, new_channels):
    factory, ids = engagement_world
    now = service.utcnow()
    async with factory() as session:
        preference = await service.get_preference(session, ids["peer"], create=True)
        preference.email_enabled = True
        preference.channel_enabled_at = {"email": service.stamp(now - timedelta(days=2))}
        session.add(NotificationContact(user_id=ids["peer"], channel="email", destination="owner@example.test",
            destination_hash="verified-address", verified_at=now, generation=1))
        row = EngagementSubscription(user_id=ids["peer"], scope_kind="ecosystem", scope_id=ids["eco"],
            event_families=old_families, channels=old_channels, muted=old_muted, frequency="daily",
            created_at=now - timedelta(days=1))
        session.add(row)
        old_event = await make_event(session, ids)
        changed_at = now + timedelta(seconds=10)
        monkeypatch.setattr(service, "utcnow", lambda: changed_at)
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem",
            "scope_id": str(ids["eco"]), "event_families": new_families, "channels": new_channels})
        assert row.created_at == changed_at
        assert "email" not in {choice["channel"] for choice in await service.delivery_candidates(session, ids["peer"], old_event)}
        monkeypatch.setattr(service, "utcnow", lambda: changed_at + timedelta(seconds=1))
        new_event = await make_event(session, ids, key="after-follow-expansion")
        assert "email" in {choice["channel"] for choice in await service.delivery_candidates(session, ids["peer"], new_event)}


@pytest.mark.parametrize("families,channels", [
    (["governance", "opportunities"], ["email", "in_app"]),
    (["governance"], ["email"]),
])
async def test_unchanged_or_narrowed_follow_preserves_activation(engagement_world, families, channels):
    factory, ids = engagement_world
    activation = service.utcnow() - timedelta(days=1)
    async with factory() as session:
        row = EngagementSubscription(user_id=ids["peer"], scope_kind="ecosystem", scope_id=ids["eco"],
            event_families=["governance", "opportunities"], channels=["email", "in_app"], muted=False,
            frequency="daily", created_at=activation)
        session.add(row)
        await session.flush()
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem",
            "scope_id": str(ids["eco"]), "event_families": families, "channels": channels})
        assert row.created_at == activation


async def test_private_visibility_is_rechecked_after_membership_revocation(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        event = await make_event(session, ids)
        assert await service.event_view(session, ids["stranger"], event) is None
        assert await service.event_view(session, ids["peer"], event)
        await service.fanout_pending(session)
        member = await session.get(Member, ids["peer_member"])
        member.current_status = "exited"
        await session.flush()
        assert await service.event_view(session, ids["peer"], event) is None
        page = await service.inbox_page(session, ids["peer"])
        assert page["items"] == [] and page["unread_count"] == 0


async def test_shared_governance_scope_and_cross_ecosystem_collaboration_deduplicate(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        proposal = await session.get(Proposal, ids["proposal"])
        proposal.shared_ecosystem_ids = [str(ids["other_eco"])]
        governance = await make_event(session, ids)
        assert await service.event_view(session, ids["other"], governance)
        event = await make_event(session, ids, key="collab-one", kind="collaboration", family="collaboration")
        scopes = await service.event_scopes(session, event)
        assert ("domain", ids["domain"]) in scopes and ("domain", ids["target_domain"]) in scopes
        await service.fanout_pending(session)
        await service.fanout_pending(session)
        rows = (await session.scalars(select(EngagementInboxItem).where(
            EngagementInboxItem.event_id == event.id))).all()
        assert {row.user_id for row in rows} == {ids["peer"], ids["other"], ids["dual"]}
        assert len(rows) == 3


async def test_private_message_has_recipient_only_generic_inbox(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        event = await make_event(session, ids, kind="conversation", family="messages",
                                 audience=[ids["peer"]])
        assert await service.event_view(session, ids["peer"], event, community=True) is None
        assert await service.event_view(session, ids["other"], event) is None
        await service.fanout_pending(session)
        inbox = await service.inbox_page(session, ids["peer"])
        assert len(inbox["items"]) == 1
        assert inbox["items"][0]["title"] == "Conversation update"
        assert "sentinel" not in str(inbox)
        assert inbox["items"][0]["url"] == "/messaging?conversation=" + str(ids["conversation"])
        assert (await service.activity_page(session, ids["peer"]))["items"] == []


async def test_source_withdrawal_and_disabled_user_hide_old_updates(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        event = await make_event(session, ids, kind="share", family="opportunities")
        assert await service.event_view(session, ids["peer"], event)
        (await session.get(SharesNeeds, ids["post"])).status = "withdrawn"
        await session.flush()
        assert await service.event_view(session, ids["peer"], event) is None
        proposal_event = await make_event(session, ids, key="gov")
        (await session.get(User, ids["peer"])).disabled_at = service.utcnow()
        await session.flush()
        assert await service.event_view(session, ids["peer"], proposal_event) is None


async def test_preferences_exist_without_device_and_require_real_readiness(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        result = await service.update_preference(session, ids["stranger"],
            {"timezone": "America/Denver", "quiet_start": "22:00", "quiet_end": "08:00"}, {})
        await session.commit()
        assert result["timezone"] == "America/Denver" and not result["email_enabled"]
        with pytest.raises(ApiError) as refused:
            await service.update_preference(session, ids["stranger"], {"email_enabled": True},
                                            {"channels": {"email": {"state": "pending_setup"}}})
        assert refused.value.status == 409


@pytest.mark.parametrize("body", [
    {"timezone": "Not/AZone"}, {"email_enabled": "true"}, {"quiet_start": "25:00", "quiet_end": "06:00"},
    {"quiet_start": "22:00"}, {"paused_until": "2026-11-02T12:00:00"}, {"owner_id": "someone"},
])
async def test_preference_shape_rejected(engagement_world, body):
    factory, ids = engagement_world
    async with factory() as session:
        with pytest.raises(ApiError):
            await service.update_preference(session, ids["peer"], body, {})


async def test_subscriptions_fastest_match_mute_and_per_channel_consent(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        preference = await service.get_preference(session, ids["peer"], create=True)
        preference.email_enabled = True
        preference.channel_enabled_at = {"email": service.stamp(service.utcnow() - timedelta(seconds=1))}
        session.add(NotificationContact(user_id=ids["peer"], channel="email", destination="owner@example.test",
            destination_hash="verified-address", verified_at=service.utcnow(), generation=1))
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem", "scope_id": str(ids["eco"]),
            "event_families": ["governance"], "channels": ["email"], "frequency": "daily"})
        await service.save_subscription(session, ids["peer"], {"scope_kind": "proposal", "scope_id": str(ids["proposal"]),
            "event_families": ["governance"], "channels": ["email"], "frequency": "immediate"})
        event = await make_event(session, ids)
        choices = await service.delivery_candidates(session, ids["peer"], event)
        assert next(row for row in choices if row["channel"] == "email")["frequency"] == "immediate"
        await service.save_subscription(session, ids["peer"], {"scope_kind": "proposal", "scope_id": str(ids["proposal"]),
            "event_families": [], "channels": [], "muted": True})
        assert await service.delivery_candidates(session, ids["peer"], event) == []


async def test_activation_does_not_backfill_old_events_and_read_is_not_consumption(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        event = await make_event(session, ids)
        preference = await service.get_preference(session, ids["peer"], create=True)
        preference.email_enabled = True
        preference.channel_enabled_at = {"email": service.stamp(event.occurred_at + timedelta(seconds=1))}
        session.add(NotificationContact(user_id=ids["peer"], channel="email", destination="owner@example.test",
            destination_hash="verified-address", verified_at=service.utcnow(), generation=1))
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem", "scope_id": str(ids["eco"]),
            "event_families": ["governance"], "channels": ["email", "in_app"], "frequency": "daily"})
        choices = await service.delivery_candidates(session, ids["peer"], event)
        assert [row["channel"] for row in choices] == ["in_app"]
        await service.fanout_pending(session)
        item = await session.scalar(select(EngagementInboxItem).where(EngagementInboxItem.user_id == ids["peer"]))
        await service.mark_inbox(session, ids["peer"], [item.id])
        assert (await session.get(Proposal, ids["proposal"])).status == "advice"
        with pytest.raises(ApiError):
            await service.mark_inbox(session, ids["other"], [item.id])


async def test_follow_target_scope_requires_real_participation(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        with pytest.raises(ApiError):
            await service.save_subscription(session, ids["stranger"], {"scope_kind": "ecosystem",
                "scope_id": str(ids["eco"]), "event_families": ["governance"], "channels": ["in_app"]})
        assert await service.scope_options(session, ids["peer"], "team", ident=ids["team"])
        with pytest.raises(ApiError):
            await service.scope_options(session, ids["owner"], "team", ident=ids["team"])
        with pytest.raises(ApiError):
            await service.scope_options(session, ids["peer"], "arbitrary-topic")


async def test_following_public_post_reaches_outside_ecosystem_member(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        await service.save_subscription(session, ids["other"], {"scope_kind": "share", "scope_id": str(ids["post"]),
            "event_families": ["opportunities"], "channels": ["in_app"]})
        event = await make_event(session, ids, kind="share", family="opportunities")
        await service.fanout_pending(session)
        assert await session.scalar(select(EngagementInboxItem.id).where(
            EngagementInboxItem.event_id == event.id, EngagementInboxItem.user_id == ids["other"]))


async def test_inbox_pagination_and_malformed_cursor(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        for number in range(3):
            await make_event(session, ids, key="page-" + str(number))
        await service.fanout_pending(session)
        first = await service.inbox_page(session, ids["peer"], limit=2)
        second = await service.inbox_page(session, ids["peer"], limit=2, cursor=first["next_cursor"])
        assert len(first["items"]) == 2 and len(second["items"]) == 1
        assert set(item["id"] for item in first["items"]).isdisjoint(item["id"] for item in second["items"])
        with pytest.raises(ApiError):
            await service.inbox_page(session, ids["peer"], cursor="not-a-cursor")


@pytest.mark.parametrize("headers,status", [
    ({"content-type": "application/json", "origin": "https://evil.example"}, 403),
    ({"content-type": "application/json", "origin": "null"}, 403),
    ({"content-type": "text/plain", "origin": "https://neos.example"}, 415),
    ({"content-type": "application/json", "sec-fetch-site": "cross-site"}, 403),
    ({"content-type": "application/json", "origin": "https://neos.example"}, None),
    ({"content-type": "application/json"}, None),
])
def test_mutation_boundary_requires_json_and_trusted_browser_origin(headers, status):
    user = SimpleNamespace(id=uuid.uuid4(), disabled_at=None)
    request = SimpleNamespace(ctx=SimpleNamespace(user=user), headers=headers,
        app=SimpleNamespace(ctx=SimpleNamespace(settings=SimpleNamespace(
            FRONTEND_URL="https://neos.example", CORS_ORIGINS="https://neos.example"))))
    returned, error = require_engagement_write(request)
    assert (error.status if error else None) == status
    assert returned == user if status is None else returned is None


@pytest_asyncio.fixture
async def engagement_app(engagement_world):
    factory, ids = engagement_world
    app = Sanic("engagement-" + uuid.uuid4().hex)
    app.config.ASSET_DIR = ""
    app.ctx.db = factory
    app.ctx.settings = SimpleNamespace(FRONTEND_URL="https://neos.example", CORS_ORIGINS="https://neos.example")
    app.blueprint(engagement_api_bp)
    app.blueprint(communities_api_bp)
    register_api_errors(app)

    @app.on_request
    async def auth(request):
        key = request.headers.get("x-test-user")
        async with factory() as session:
            request.ctx.user = await session.get(User, ids[key]) if key in ids else None
    yield app, factory, ids


async def test_public_preview_contains_only_public_minimal_fields(engagement_app):
    app, factory, ids = engagement_app
    _, response = await app.asgi_client.get("/api/v1/communities")
    assert response.status == 200
    assert {item["id"] for item in response.json["items"]} == {str(ids["eco"]), str(ids["other_eco"])}
    _, detail = await app.asgi_client.get("/api/v1/communities/" + str(ids["eco"]))
    assert detail.status == 200 and detail.json["opportunities"] == []
    assert detail.json["opportunities_require_sign_in"] is True
    _, detail = await app.asgi_client.get("/api/v1/communities/" + str(ids["eco"]), headers={"x-test-user": "peer"})
    assert detail.status == 200 and len(detail.json["opportunities"]) == 1
    assert detail.json["opportunities_require_sign_in"] is False
    assert "private-phone" not in str(detail.json) and "Private body" not in str(detail.json)
    _, hidden = await app.asgi_client.get("/api/v1/communities/" + str(ids["hidden_eco"]))
    assert hidden.status == 404
    async with factory() as session:
        (await session.get(SharesNeeds, ids["post"])).visibility = "ecosystem"
        await session.commit()
    _, detail = await app.asgi_client.get("/api/v1/communities/" + str(ids["eco"]))
    assert detail.json["opportunities"] == []


async def test_guest_denied_and_cross_origin_subscription_never_saved(engagement_app):
    app, factory, ids = engagement_app
    _, guest = await app.asgi_client.get("/api/v1/engagement/preferences")
    assert guest.status == 401
    _, refused = await app.asgi_client.post("/api/v1/engagement/subscriptions",
        headers={"x-test-user": "peer", "origin": "https://evil.example"}, json={
            "scope_kind": "ecosystem", "scope_id": str(ids["eco"]),
            "event_families": ["governance"], "channels": ["in_app"]})
    assert refused.status == 403
    async with factory() as session:
        assert await session.scalar(select(func.count(EngagementSubscription.id))) == 0


async def test_explicit_family_choices_override_implicit_community_inbox(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem", "scope_id": str(ids["eco"]),
            "event_families": ["governance"], "channels": ["in_app"]})
        event = await make_event(session, ids, kind="share", family="opportunities")
        assert await service.delivery_candidates(session, ids["peer"], event) == []
        assert await service.delivery_candidates(session, ids["stranger"], event) == []
        await service.fanout_pending(session)
        assert (await service.inbox_page(session, ids["peer"]))["items"] == []


async def test_external_only_follow_has_hidden_receipt_without_in_app_delivery(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        preference = await service.get_preference(session, ids["peer"], create=True)
        preference.email_enabled = True
        preference.channel_enabled_at = {"email": service.stamp(service.utcnow() - timedelta(seconds=1))}
        session.add(NotificationContact(user_id=ids["peer"], channel="email", destination="owner@example.test",
            destination_hash="verified-address", verified_at=service.utcnow(), generation=1))
        await service.save_subscription(session, ids["peer"], {"scope_kind": "ecosystem", "scope_id": str(ids["eco"]),
            "event_families": ["governance"], "channels": ["email"], "frequency": "daily"})
        event = await make_event(session, ids)
        assert [row["channel"] for row in await service.delivery_candidates(session, ids["peer"], event)] == ["email"]
        await service.fanout_pending(session)
        receipt = await session.scalar(select(EngagementInboxItem).where(
            EngagementInboxItem.user_id == ids["peer"], EngagementInboxItem.event_id == event.id))
        assert receipt is not None and receipt.in_app_visible is False
        inbox = await service.inbox_page(session, ids["peer"])
        assert inbox["items"] == [] and inbox["unread_count"] == 0
        with pytest.raises(ApiError):
            await service.mark_inbox(session, ids["peer"], [receipt.id])


async def test_direct_message_in_app_opt_out_preserves_explicit_email_follow(engagement_world):
    factory, ids = engagement_world
    async with factory() as session:
        preference = await service.get_preference(session, ids["peer"], create=True)
        preference.direct_messages = False
        preference.email_enabled = True
        preference.channel_enabled_at = {"email": service.stamp(service.utcnow() - timedelta(seconds=1))}
        session.add(NotificationContact(user_id=ids["peer"], channel="email", destination="owner@example.test",
            destination_hash="verified-address", verified_at=service.utcnow(), generation=1))
        await service.save_subscription(session, ids["peer"], {"scope_kind": "conversation", "scope_id": str(ids["conversation"]),
            "event_families": ["messages"], "channels": ["email", "in_app"], "frequency": "immediate"})
        event = await make_event(session, ids, kind="conversation", family="messages", audience=[ids["peer"]])
        assert [row["channel"] for row in await service.delivery_candidates(session, ids["peer"], event)] == ["email"]
