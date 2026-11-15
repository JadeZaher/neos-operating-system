"""Public owner contact, and who may start a direct conversation with that owner.

The contact is the external admin when one is active, else an internal admin.
With no active admin the payload is null. Payloads carry that person's display
name, role label and member id.
A pending account can message that owner and no other member.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers course tables quizzes reference
from neos_agent.api.communities import communities_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.messaging import messaging_api_bp
from neos_agent.api.orientation import orientation_api_bp
from neos_agent.db.models import Base, Conversation, Ecosystem, EcosystemAdmin, Member, User
from neos_agent.messaging.handlers import _last_message_times

HARBOR = uuid.UUID("0000000c-0000-0000-0000-000000000001")
QUIET = uuid.UUID("0000000c-0000-0000-0000-000000000002")
DORMANT = uuid.UUID("0000000c-0000-0000-0000-000000000003")
PRIVATE = uuid.UUID("0000000c-0000-0000-0000-000000000004")
OTHER = uuid.UUID("0000000c-0000-0000-0000-000000000005")

# Names, business keys and account fields that must not leave the owner contact.
SENTINELS = (
    "SENTINEL-ADMIN", "SENTINEL-SECOND-OWNER", "SENTINEL-MEMBER", "SENTINEL-PENDING",
    "SENTINEL-OUTSIDER", "SENTINEL-QUIET", "SENTINEL-DISABLED", "SENTINEL-PRIVATE",
    "SENTINEL-ADA-DID", "SENTINEL-ADA-PHONE", "SENTINEL-EMAIL@example.test",
    "MEM-SENTINEL-ADMIN", "MEM-SENTINEL-SECOND", "MEM-SENTINEL-MEMBER", "MEM-SENTINEL-PENDING",
    "MEM-ADA",
)

PEOPLE = {
    "ada": SimpleNamespace(name="Ada", role="owner", status="active", ecosystems=[HARBOR],
                           did="did:neos:SENTINEL-ADA-DID", phone="SENTINEL-ADA-PHONE",
                           created_at=datetime(2020, 1, 1)),
    "dee": SimpleNamespace(name="SENTINEL-SECOND-OWNER", role="owner", status="active", ecosystems=[HARBOR],
                           created_at=datetime(2024, 6, 1)),
    "bea": SimpleNamespace(name="SENTINEL-ADMIN", role="admin", status="active", ecosystems=[HARBOR]),
    "cai": SimpleNamespace(name="SENTINEL-MEMBER", role="user", status="active", ecosystems=[HARBOR]),
    "noa": SimpleNamespace(name="SENTINEL-PENDING", role="user", status="pending_consent", ecosystems=[HARBOR]),
    "oli": SimpleNamespace(name="SENTINEL-OUTSIDER", role="user", status="active", ecosystems=[OTHER]),
    "quiet": SimpleNamespace(name="SENTINEL-QUIET", role="user", status="active", ecosystems=[QUIET]),
    "disabled": SimpleNamespace(name="SENTINEL-DISABLED", role="owner", status="active", ecosystems=[DORMANT],
                                disabled_at=datetime(2023, 1, 1)),
    "hidden": SimpleNamespace(name="SENTINEL-PRIVATE", role="owner", status="active", ecosystems=[PRIVATE]),
}
USER_IDS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"owner-contact.{key}.user") for key in PEOPLE}
MEMBER_IDS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"owner-contact.{key}.member") for key in PEOPLE}


@pytest.fixture(autouse=True)
def _clear_message_rate():
    _last_message_times.clear()
    yield
    _last_message_times.clear()


async def _seed(session: AsyncSession) -> None:
    session.add_all([
        Ecosystem(id=HARBOR, name="Harbor", status="active", visibility="public",
                  contact_email="SENTINEL-EMAIL@example.test", description="A public harbor"),
        Ecosystem(id=QUIET, name="Quiet", status="active", visibility="public"),
        Ecosystem(id=DORMANT, name="Dormant", status="active", visibility="public"),
        Ecosystem(id=PRIVATE, name="Private Harbor", status="active", visibility="private"),
        Ecosystem(id=OTHER, name="Other Shore", status="active", visibility="public"),
    ])
    for key, person in PEOPLE.items():
        session.add(User(
            id=USER_IDS[key], display_name=person.name, did=getattr(person, "did", None),
            phone=getattr(person, "phone", None), disabled_at=getattr(person, "disabled_at", None),
        ))
    await session.flush()
    for key, person in PEOPLE.items():
        session.add(Member(
            id=MEMBER_IDS[key], ecosystem_id=person.ecosystems[0], user_id=USER_IDS[key],
            member_id=f"MEM-{person.name}" if key != "ada" else "MEM-ADA",
            display_name=person.name, current_status=person.status, role=person.role,
            created_at=getattr(person, "created_at", datetime(2022, 1, 1)),
        ))
    await session.flush()
    for designation in ("internal", "external"):
        session.add(EcosystemAdmin(
            ecosystem_id=HARBOR, member_id=MEMBER_IDS["ada"], designation=designation,
            appointed_by_member_id=MEMBER_IDS["ada"],
        ))
    await session.commit()


def _create_app() -> Sanic:
    app = Sanic(f"test-owner-contact-{uuid.uuid4().hex[:8]}")
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        key = request.headers.get("x-test-as")
        if not key:
            return
        person = PEOPLE[key]
        active = [ecosystem_id for ecosystem_id in person.ecosystems if person.status == "active"]
        request.ctx.user = User(id=USER_IDS[key], display_name=person.name, disabled_at=getattr(person, "disabled_at", None))
        request.ctx.member = Member(
            id=MEMBER_IDS[key], ecosystem_id=person.ecosystems[0], user_id=USER_IDS[key],
            member_id="MEM-AUTH", display_name=person.name, current_status=person.status, role=person.role,
        )
        request.ctx.selected_ecosystem_ids = list(active)
        request.ctx.authorized_ecosystem_ids = list(active)

    for blueprint in (communities_api_bp, ecosystems_api_bp, orientation_api_bp, messaging_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def app():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await _seed(session)
    application = _create_app()
    application.ctx.db = session_factory
    yield application
    await engine.dispose()


async def _call(app: Sanic, method: str, who: str | None, url: str, **kwargs):
    headers = {"x-test-as": who} if who else {}
    _, response = await getattr(app.asgi_client, method)(url, headers=headers, **kwargs)
    return response


def _assert_owner(owner: dict) -> None:
    assert set(owner) == {"id", "display_name", "role"}
    assert owner == {"id": str(MEMBER_IDS["ada"]), "display_name": "Ada", "role": "external"}


def _assert_no_sentinels(body: str) -> None:
    for secret in SENTINELS:
        assert secret not in body
    for key in ("bea", "dee", "cai", "noa", "oli", "quiet", "disabled", "hidden"):
        assert str(USER_IDS[key]) not in body
        assert str(MEMBER_IDS[key]) not in body
    assert str(USER_IDS["ada"]) not in body


async def test_public_payloads_expose_only_the_owner_contact(app):
    listing = await _call(app, "get", None, "/api/v1/communities")
    assert listing.status == 200
    assert {item["id"] for item in listing.json["items"]} == {str(HARBOR), str(QUIET), str(DORMANT), str(OTHER)}
    assert all("owner" not in item for item in listing.json["items"])
    _assert_no_sentinels(listing.text)

    community = await _call(app, "get", None, f"/api/v1/communities/{HARBOR}")
    assert community.status == 200
    _assert_owner(community.json["owner"])
    # Harbor has four active members and one pending row. The count is active only.
    assert community.json["member_count"] == 4
    _assert_no_sentinels(community.text)
    quiet = await _call(app, "get", None, f"/api/v1/communities/{QUIET}")
    dormant = await _call(app, "get", None, f"/api/v1/communities/{DORMANT}")
    assert quiet.json["owner"] is None and dormant.json["owner"] is None
    _assert_no_sentinels(quiet.text)
    _assert_no_sentinels(dormant.text)
    hidden = await _call(app, "get", None, f"/api/v1/communities/{PRIVATE}")
    assert hidden.status == 404
    _assert_no_sentinels(hidden.text)

    ethos = await _call(app, "get", "noa", f"/api/v1/orientation/ethos/{HARBOR}")
    assert ethos.status == 200
    _assert_owner(ethos.json["owner"])
    assert ethos.json["member_count"] == 4
    _assert_no_sentinels(ethos.text)
    quiet_ethos = await _call(app, "get", "noa", f"/api/v1/orientation/ethos/{QUIET}")
    dormant_ethos = await _call(app, "get", "noa", f"/api/v1/orientation/ethos/{DORMANT}")
    assert quiet_ethos.json["owner"] is None and dormant_ethos.json["owner"] is None
    _assert_no_sentinels(quiet_ethos.text)
    _assert_no_sentinels(dormant_ethos.text)
    assert (await _call(app, "get", "noa", f"/api/v1/orientation/ethos/{PRIVATE}")).status == 404

    detail = await _call(app, "get", "noa", f"/api/v1/ecosystems/{HARBOR}")
    assert detail.status == 200
    _assert_owner(detail.json["owner"])
    assert detail.json["member_count"] == 4
    assert (await _call(app, "get", "noa", f"/api/v1/ecosystems/{QUIET}")).json["owner"] is None


async def test_pending_account_can_message_only_the_owner(app):
    body = {"type": "dm", "participant_ids": [str(MEMBER_IDS["ada"])]}
    opened = await _call(app, "post", "noa", "/api/v1/messaging/conversations", json=body)
    assert opened.status == 201
    conversation_id = opened.json["id"]
    assert {person["id"] for person in opened.json["participants"]} == {str(MEMBER_IDS["ada"]), str(MEMBER_IDS["noa"])}

    again = await _call(app, "post", "noa", "/api/v1/messaging/conversations", json=body)
    assert again.status == 200 and again.json["id"] == conversation_id
    async with app.ctx.db() as session:
        assert await session.scalar(select(func.count(Conversation.id))) == 1

    sent = await _call(app, "post", "noa", f"/api/v1/messaging/conversations/{conversation_id}/messages",
                       json={"content": "How do I finish joining?"})
    assert sent.status == 201 and sent.json["content"] == "How do I finish joining?"
    listed = await _call(app, "get", "noa", "/api/v1/messaging/conversations")
    assert [row["id"] for row in listed.json["conversations"]] == [conversation_id]
    owner_list = await _call(app, "get", "ada", "/api/v1/messaging/conversations")
    (thread,) = [row for row in owner_list.json["conversations"] if row["id"] == conversation_id]
    assert thread["unread_count"] == 1

    for other in ("bea", "dee", "cai"):
        refused = await _call(app, "post", "noa", "/api/v1/messaging/conversations",
                              json={"type": "dm", "participant_ids": [str(MEMBER_IDS[other])]})
        assert refused.status == 403
        assert refused.json["error"] == "An active membership in this ecosystem is required to start a conversation."
    outsider = await _call(app, "post", "oli", "/api/v1/messaging/conversations",
                           json={"type": "dm", "participant_ids": [str(MEMBER_IDS["bea"])]})
    assert outsider.status == 404
    private = await _call(app, "post", "oli", "/api/v1/messaging/conversations",
                          json={"type": "dm", "participant_ids": [str(MEMBER_IDS["hidden"])]})
    assert private.status == 404
    reached = await _call(app, "post", "oli", "/api/v1/messaging/conversations", json=body)
    assert reached.status == 201
    assert {person["id"] for person in reached.json["participants"]} == {str(MEMBER_IDS["ada"]), str(MEMBER_IDS["oli"])}
    async with app.ctx.db() as session:
        assert await session.scalar(select(func.count(Conversation.id))) == 2


async def test_signed_out_cannot_start_a_conversation(app):
    refused = await _call(app, "post", None, "/api/v1/messaging/conversations",
                          json={"type": "dm", "participant_ids": [str(MEMBER_IDS["ada"])]})
    assert refused.status == 401
    assert refused.json["error"] == "Authentication required"
    follow = await _call(app, "post", None, f"/api/v1/messaging/conversations/{uuid.uuid4()}/messages",
                         json={"content": "Hello"})
    assert follow.status == 401


async def test_active_members_still_message_other_members(app):
    first = await _call(app, "post", "cai", "/api/v1/messaging/conversations",
                        json={"type": "dm", "participant_ids": [str(MEMBER_IDS["bea"])]})
    assert first.status == 201
    second = await _call(app, "post", "cai", "/api/v1/messaging/conversations",
                         json={"type": "dm", "participant_ids": [str(MEMBER_IDS["bea"])]})
    assert second.status == 201 and second.json["id"] != first.json["id"]
    sent = await _call(app, "post", "cai", f"/api/v1/messaging/conversations/{first.json['id']}/messages",
                       json={"content": "Are you coming to the harbor meeting?"})
    assert sent.status == 201
    pending = await _call(app, "get", "noa", "/api/v1/messaging/conversations")
    assert pending.json["conversations"] == []
    hidden = await _call(app, "get", "noa", f"/api/v1/messaging/conversations/{first.json['id']}")
    assert hidden.status == 404


async def test_pending_send_uses_the_existing_rate_limit(app):
    opened = await _call(app, "post", "noa", "/api/v1/messaging/conversations",
                         json={"type": "dm", "participant_ids": [str(MEMBER_IDS["ada"])]})
    assert opened.status == 201
    _last_message_times[MEMBER_IDS["noa"]] = [datetime.now().timestamp()] * 10
    limited = await _call(app, "post", "noa", f"/api/v1/messaging/conversations/{opened.json['id']}/messages",
                          json={"content": "One more"})
    assert limited.status == 429
    assert limited.json["error"] == "Rate limit exceeded"

    peer = await _call(app, "post", "cai", "/api/v1/messaging/conversations",
                       json={"type": "dm", "participant_ids": [str(MEMBER_IDS["bea"])]})
    assert peer.status == 201
    _last_message_times[MEMBER_IDS["cai"]] = [datetime.now().timestamp()] * 10
    sent = await _call(app, "post", "cai", f"/api/v1/messaging/conversations/{peer.json['id']}/messages",
                       json={"content": "Still fine"})
    assert sent.status == 201
