"""Node support's public discovery and privileged User-based API boundary."""
from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select

from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthSession, NodeAdminAction, User
from .test_platform_admin import SECRET, _call, platform, db  # noqa: F401


async def test_nonadmin_support_denial_is_publicly_auditable(platform, db):
    response = await _call(platform, "finn", "get", "/api/v1/node-admin/catalog")
    assert response.status == 403
    public = await _call(platform, "anon", "get", "/api/v1/node-admin/audit?outcome=denied")
    assert public.status == 200
    assert any(item["resource_type"] == "node_support" for item in public.json["items"])
    assert "value" not in str(public.json["items"])


async def test_memberless_operator_has_auth_flag_badge_and_public_roster_then_disable_revokes_access(platform, db):
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    async with db() as session:
        session.add(User(id=user_id, display_name="Support without membership", did="did:key:support-nomember"))
        await session.flush()
        session.add(AuthSession(id=session_id, user_id=user_id, expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
        await session.commit()
    granted = await _call(platform, "lani", "post", "/api/v1/node-admin/admins", {"user_id": str(user_id), "reason": "Access management"})
    assert granted.status == 200
    platform.cookies["supportnomember"] = make_session_cookie(str(session_id), SECRET)
    me = await _call(platform, "supportnomember", "get", "/api/v1/auth/me")
    assert me.status == 200 and me.json["member"] is None
    assert me.json["user"]["id"] == str(user_id) and me.json["is_node_admin"] and me.json["is_platform_admin"]
    catalog = await _call(platform, "supportnomember", "get", "/api/v1/node-admin/catalog")
    assert catalog.status == 200 and len(catalog.json["reason_categories"]) == 7
    roster = await _call(platform, "anon", "get", "/api/v1/node-admin/roster")
    entry = next(item for item in roster.json["items"] if item["user_id"] == str(user_id))
    assert set(entry) == {"user_id", "display_name", "profile_url", "node_admin_badge"}
    inspected = await _call(platform, "lani", "post", "/api/v1/node-admin/inspect", {"resource_type": "users", "resource_id": str(user_id), "reason": "Account recovery"})
    disabled = await _call(platform, "lani", "post", "/api/v1/node-admin/commands", {"resource_type": "users", "resource_id": str(user_id), "action": "update", "reason": "Account recovery",
        "values": {"disabled_at": datetime.now().isoformat()}, "expected_version": inspected.json["resource"]["version"]})
    assert disabled.status == 200
    assert (await _call(platform, "supportnomember", "get", "/api/v1/node-admin/catalog")).status == 401
    roster = await _call(platform, "anon", "get", "/api/v1/node-admin/roster")
    assert str(user_id) not in {item["user_id"] for item in roster.json["items"]}


async def test_legacy_global_mutations_have_targeted_attempt_and_completion(platform, db):
    response = await _call(platform, "lani", "put", "/api/v1/settings", {"key": "ctc_map", "value": {"private_body": "legacy-private-sentinel"}})
    assert response.status == 200
    async with db() as session:
        rows = (await session.scalars(select(NodeAdminAction).where(NodeAdminAction.resource_type == "app_settings", NodeAdminAction.source == "legacy").order_by(NodeAdminAction.created_at.desc()))).all()
    assert any(row.outcome == "attempted" for row in rows) and any(row.outcome == "completed" and row.correlation_id for row in rows)
    assert all("legacy-private-sentinel" not in str(row.safe_summary) for row in rows)
