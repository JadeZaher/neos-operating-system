"""Explicit support mode and publicly readable intervention history."""
from __future__ import annotations

import uuid
from functools import wraps

from pydantic import ValidationError
from sanic import Blueprint, json
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError
from neos_agent.api.schemas.node_admin import NodeAdminGrantRequest, NodeAdminRevokeRequest, SupportCommandRequest, SupportInspectRequest
from neos_agent.db.models import Ecosystem, NodeAdmin, NodeAdminAction, NodeAdminSnapshot, User
from neos_agent.db.models._base import GUID
from neos_agent.services.node_admin import PUBLIC_REASONS, audit_event, authorize, change_admin, execute_command, inspect_resource, json_value, log_failure, public_reason, resource_spec, serialize_audit, serialize_resource
from neos_agent.services.node_admin_catalog import SETTING_KEYS, catalog_entry, registry

node_admin_api_bp = Blueprint("node_admin_api", url_prefix="/api/v1/node-admin")


def actor_id(request):
    user = getattr(request.ctx, "user", None)
    return user.id if user else None


def audited(handler):
    @wraps(handler)
    async def wrapped(request, *args, **kwargs):
        try:
            body = request.json if isinstance(request.json, dict) else {}
        except Exception:
            body = {}
        try:
            organization = uuid.UUID(str(body.get("organization_id"))) if body.get("organization_id") else None
        except (ValueError, TypeError):
            organization = None
        try:
            reason = public_reason(body.get("reason", "Technical support"))
        except ApiError:
            reason = "Technical support"
        try:
            return await handler(request, *args, **kwargs)
        except (ApiError, ValidationError, IntegrityError) as exc:
            # Do not copy untrusted bodies, identifiers, database errors or private values into the public log.
            await log_failure(request.app.ctx.db, actor_id(request), "support_request", "node_support", outcome="denied" if isinstance(exc, ApiError) and exc.status in {401, 403} else "failed", organization_id=organization, reason=reason)
            if isinstance(exc, ApiError):
                return json({"error": exc.message, **exc.extra}, status=exc.status)
            return json({"error": "Invalid support request" if isinstance(exc, ValidationError) else "The correction conflicts with existing records"}, status=400 if isinstance(exc, ValidationError) else 409)
        except Exception:
            await log_failure(request.app.ctx.db, actor_id(request), "support_request", "node_support", outcome="failed", organization_id=organization, reason=reason)
            return json({"error": "Support request failed; no correction was committed"}, status=500)
    return wrapped


def pagination(request):
    try:
        page = max(1, int(request.args.get("page", 1)))
        size = min(100, max(1, int(request.args.get("per_page", 25))))
        if page > 1000000:
            raise ValueError()
        return page, size
    except ValueError:
        raise ApiError(400, "Invalid pagination") from None


@node_admin_api_bp.get("/catalog")
@audited
async def catalog(request):
    async with request.app.ctx.db() as session:
        actor = await authorize(session, actor_id(request))
        organizations = (await session.scalars(select(Ecosystem).order_by(Ecosystem.name).limit(1000))).all()
        session.add(audit_event(actor, "catalog", "node_support"))
        result = {"items": [catalog_entry(spec) for spec in sorted(registry().values(), key=lambda s: s.key)],
                  "reason_categories": sorted(PUBLIC_REASONS),
                  "organizations": [{"id": str(row.id), "name": row.name} for row in organizations]}
        await session.commit()
    return json(result)


@node_admin_api_bp.get("/resources/<kind:str>")
@audited
async def resources(request, kind):
    spec = resource_spec(kind)
    page, size = pagination(request)
    async with request.app.ctx.db() as session:
        actor = await authorize(session, actor_id(request))
        query = select(spec.model)
        org = request.args.get("organization_id")
        if org:
            try:
                org_id = uuid.UUID(org)
            except ValueError:
                raise ApiError(400, "Invalid organization identifier") from None
            if "ecosystem_id" in spec.model.__table__.columns:
                query = query.where(spec.model.ecosystem_id == org_id)
            elif kind == "ecosystems":
                query = query.where(spec.model.id == org_id)
            else:
                raise ApiError(400, "This resource is scoped through its parent; locate it by identifier")
        if kind == "app_settings":
            query = query.where(spec.model.key.in_(SETTING_KEYS))
        search = request.args.get("q", "")[:150].strip()
        if search:
            terms = []
            try:
                search_uuid = uuid.UUID(search)
            except ValueError:
                search_uuid = None
            for field in ("name", "title", "display_name", "username", "member_id", "proposal_id", "agreement_id", "badge_key", "key"):
                if field in spec.model.__table__.columns:
                    terms.append(cast(getattr(spec.model, field), String).ilike("%" + search.replace("%", "\\%").replace("_", "\\_") + "%"))
                    if search_uuid is not None and isinstance(spec.model.__table__.columns[field].type, GUID):
                        terms.append(getattr(spec.model, field) == search_uuid)
            try:
                search_id = uuid.UUID(search)
                terms.append(getattr(spec.model, next(iter(spec.model.__table__.primary_key.columns)).name) == search_id)
            except ValueError:
                pass
            if terms:
                query = query.where(or_(*terms))
            else:
                query = query.where(False)
        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        primary = next(iter(spec.model.__table__.primary_key.columns))
        rows = (await session.scalars(query.order_by(getattr(spec.model, primary.name)).offset((page - 1) * size).limit(size))).all()
        session.add(audit_event(actor, "list", kind, organization_id=uuid.UUID(org) if org else None))
        result = {"items": [serialize_resource(spec, row, listing=True) for row in rows], "total": total, "page": page, "per_page": size}
        await session.commit()
    return json(result)


@node_admin_api_bp.post("/inspect")
@audited
async def inspect(request):
    data = SupportInspectRequest.model_validate(request.json or {})
    return json(await inspect_resource(request.app.ctx.db, actor_id(request), data.resource_type, data.resource_id, data.reason))


@node_admin_api_bp.post("/commands")
@audited
async def command(request):
    data = SupportCommandRequest.model_validate(request.json or {})
    return json(await execute_command(request.app.ctx.db, actor_id(request), data))


@node_admin_api_bp.get("/admins")
@audited
async def admins(request):
    async with request.app.ctx.db() as session:
        actor = await authorize(session, actor_id(request))
        rows = (await session.execute(select(NodeAdmin, User).join(User, User.id == NodeAdmin.user_id).order_by(NodeAdmin.granted_at))).all()
        items = [{"user_id": str(admin.user_id), "display_name": user.display_name, "active": admin.active, "granted_at": json_value(admin.granted_at),
                  "granted_by_user_id": json_value(admin.granted_by_user_id), "revoked_at": json_value(admin.revoked_at)} for admin, user in rows]
        session.add(audit_event(actor, "list", "node_admins"))
        await session.commit()
    return json({"items": items})


@node_admin_api_bp.get("/users")
@audited
async def users(request):
    async with request.app.ctx.db() as session:
        actor = await authorize(session, actor_id(request))
        query = select(User)
        search = request.args.get("q", "")[:150].replace("%", "\\%").replace("_", "\\_")
        if search:
            query = query.where(or_(User.display_name.ilike(f"%{search}%"), User.username.ilike(f"%{search}%")))
        rows = (await session.scalars(query.order_by(User.display_name).limit(100))).all()
        session.add(audit_event(actor, "list", "users"))
        await session.commit()
    return json({"items": [{"id": str(user.id), "display_name": user.display_name, "username": user.username} for user in rows]})


@node_admin_api_bp.post("/admins")
@audited
async def grant(request):
    data = NodeAdminGrantRequest.model_validate(request.json or {})
    return json(await change_admin(request.app.ctx.db, actor_id(request), data.user_id, data.reason))


@node_admin_api_bp.post("/admins/<user_id:uuid>/revoke")
@audited
async def revoke(request, user_id):
    data = NodeAdminRevokeRequest.model_validate(request.json or {})
    return json(await change_admin(request.app.ctx.db, actor_id(request), user_id, data.reason, revoke=True))


@node_admin_api_bp.get("/audit")
async def audit(request):
    page, size = pagination(request)
    async with request.app.ctx.db() as session:
        query = select(NodeAdminAction)
        for name in ("actor_user_id", "organization_id", "resource_type", "resource_id", "outcome"):
            value = request.args.get(name)
            if value:
                if name.endswith("user_id") or name == "organization_id":
                    try:
                        value = uuid.UUID(value)
                    except ValueError:
                        raise ApiError(400, "Invalid audit filter") from None
                query = query.where(getattr(NodeAdminAction, name) == value)
        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        rows = (await session.scalars(query.order_by(NodeAdminAction.created_at.desc(), NodeAdminAction.id.desc()).offset((page - 1) * size).limit(size))).all()
    return json({"items": [serialize_audit(row) for row in rows], "total": total, "page": page, "per_page": size})


@node_admin_api_bp.get("/audit/<event_id:uuid>")
async def audit_detail(request, event_id):
    async with request.app.ctx.db() as session:
        event = await session.get(NodeAdminAction, event_id)
        if event is None:
            raise ApiError(404, "Support audit event not found")
        return json(serialize_audit(event))


@node_admin_api_bp.get("/roster")
async def roster(request):
    async with request.app.ctx.db() as session:
        rows = (await session.scalars(select(User).join(NodeAdmin, NodeAdmin.user_id == User.id).where(NodeAdmin.active.is_(True), User.disabled_at.is_(None)).order_by(User.display_name))).all()
    return json({"items": [{"user_id": str(user.id), "display_name": user.display_name, "profile_url": f"/users/{user.id}",
                           "node_admin_badge": {"key": "node_admin", "label": "Node admin"}} for user in rows]})


@node_admin_api_bp.get("/archives")
@audited
async def archives(request):
    page, size = pagination(request)
    async with request.app.ctx.db() as session:
        actor = await authorize(session, actor_id(request))
        query = select(NodeAdminSnapshot).where(NodeAdminSnapshot.operation == "archive_evidence")
        for name in ("resource_type", "resource_id"):
            if request.args.get(name):
                query = query.where(getattr(NodeAdminSnapshot, name) == request.args[name])
        total = await session.scalar(select(func.count()).select_from(query.subquery()))
        rows = (await session.scalars(query.order_by(NodeAdminSnapshot.created_at.desc()).offset((page - 1) * size).limit(size))).all()
        result = {"items": [{name: json_value(getattr(row, name)) for name in ("id", "action_id", "resource_type", "resource_id", "created_at")} for row in rows], "total": total}
        session.add(audit_event(actor, "list_archives", "node_support"))
        await session.commit()
    return json(result)
