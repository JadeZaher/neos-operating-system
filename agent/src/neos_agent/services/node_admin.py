"""Audited node support commands; see services/AGENTS.md, Node support."""
from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, JSON, String, and_, cast, delete, func, or_, select, update

from neos_agent.api.errors import ApiError
from neos_agent.db.models import AppSetting, AuthSession, Base, Ecosystem, Member, NodeAdmin, NodeAdminAction, NodeAdminSnapshot, Proposal, User
from neos_agent.db.models._base import GUID
from neos_agent.services.node_admin_catalog import EVIDENCE, SECRET_FIELDS, SETTING_KEYS, catalog_entry, registry

LOCK_KEY = "node_admin_support_lock"
PUBLIC_REASONS = frozenset({"Technical support", "Account recovery", "Organization support", "Agent testing", "Data correction", "Access management", "Service recovery"})
BADGE = {"key": "node_admin", "label": "Node admin"}
BOOTSTRAP_KEY = "node_admin_bootstrap_complete"


async def initialize_node_support(factory, configured_user_ids=""):
    identifiers = sorted({uuid.UUID(value.strip()) for value in configured_user_ids.split(",") if value.strip()}, key=str)
    if not identifiers:
        return
    async with factory() as session:
        await lock_support(session)
        if await session.scalar(select(AppSetting.id).where(AppSetting.key == BOOTSTRAP_KEY)) is not None:
            return
        if await session.scalar(select(func.count()).select_from(NodeAdmin)):
            return
        users = [await session.get(User, identifier) for identifier in identifiers]
        if any(user is None or user.disabled_at is not None for user in users):
            raise ValueError("A configured node bootstrap user does not exist")
        for user in users:
            if not await user_has_login(session, user):
                raise ValueError("A configured node bootstrap user has no usable sign-in method")
        for user in users:
            session.add(NodeAdmin(user_id=user.id, active=True))
            event = audit_event(None, "bootstrap_admin", "node_admins", user.id, reason="Access management", source="bootstrap", fields=["active"], summary={"basis": "explicit_server_bootstrap"})
            event.actor_name = "Server bootstrap"
            session.add(event)
        session.add(AppSetting(key=BOOTSTRAP_KEY, value={"version": 1}))
        await session.commit()


def public_reason(value):
    if not isinstance(value, str) or not 3 <= len(value.strip()) <= 500:
        raise ApiError(400, "A support reason of 3 to 500 characters is required")
    # Public reason labels never copy private case text, credentials or contact details.
    return value.strip() if value.strip() in PUBLIC_REASONS else "Technical support"


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def json_value(value):
    if isinstance(value, (uuid.UUID, date, datetime)):
        return str(value) if isinstance(value, uuid.UUID) else value.isoformat()
    return value


async def is_node_admin(session, user_id):
    return user_id is not None and await session.scalar(select(NodeAdmin.user_id).join(User, User.id == NodeAdmin.user_id).where(NodeAdmin.user_id == user_id, NodeAdmin.active.is_(True), User.disabled_at.is_(None))) is not None


async def lock_support(session):
    values = {"id": uuid.uuid4(), "key": LOCK_KEY, "value": {"version": 1}}
    if session.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    await session.execute(insert(AppSetting).values(**values).on_conflict_do_nothing(index_elements=["key"]))
    await session.execute(update(AppSetting).where(AppSetting.key == LOCK_KEY).values(value={"version": 1}))


async def authorize(session, user_id, *, locked=True):
    if user_id is None:
        raise ApiError(401, "Authentication required")
    if locked:
        await lock_support(session)
    if not await is_node_admin(session, user_id):
        raise ApiError(403, "Node administrator access required")
    user = await session.get(User, user_id)
    if user is None:
        raise ApiError(403, "Node administrator identity is unavailable")
    return user


def audit_event(actor, action, kind, resource_id=None, organization_id=None, *, reason="Technical support", outcome="completed", source="ui", fields=(), summary=None, correlation_id=None):
    return NodeAdminAction(id=uuid.uuid4(), actor_user_id=actor.id if actor else None,
                           actor_name=actor.display_name if actor else "Unauthenticated caller", action=action,
                           resource_type=kind, resource_id=str(resource_id) if resource_id else None, organization_id=organization_id,
                           reason=reason, outcome=outcome, source=source if source in {"ui", "agent", "bootstrap", "legacy"} else "ui",
                           changed_fields=sorted(fields), safe_summary=summary or {}, correlation_id=correlation_id)


def serialize_audit(row):
    return {name: json_value(getattr(row, name)) for name in ("id", "created_at", "actor_user_id", "actor_name", "action", "resource_type", "resource_id", "organization_id", "reason", "outcome", "source", "changed_fields", "safe_summary", "correlation_id")}


async def log_failure(factory, user_id, action, kind, resource_id=None, *, outcome="denied", source="ui", correlation_id=None, organization_id=None, reason="Technical support"):
    # The failed mutation's transaction must be rolled back before this independent commit.
    async with factory() as session:
        actor = await session.get(User, user_id) if user_id else None
        session.add(audit_event(actor, action, kind, resource_id, organization_id=organization_id, reason=public_reason(reason), outcome=outcome, source=source, correlation_id=correlation_id))
        await session.commit()


def resource_spec(key):
    spec = registry().get(key)
    if spec is None:
        raise ApiError(404, "Unknown support resource")
    return spec


def resource_key(spec, value):
    column = next(iter(spec.model.__table__.primary_key.columns))
    try:
        return uuid.UUID(str(value)) if isinstance(column.type, GUID) else value
    except (ValueError, TypeError):
        raise ApiError(400, "Invalid resource identifier") from None


def serialize_resource(spec, row, *, listing=False):
    names = catalog_entry(spec)["listing_fields"] if listing else [c.name for c in spec.model.__table__.columns if c.name not in SECRET_FIELDS]
    if spec.category == "security":
        names = [name for name in names if name in {"id", "user_id", "member_id", "label", "expires_at", "revoked_at", "enabled", "created_at", "last_used_at"}]
    result = {name: json_value(getattr(row, name)) for name in names}
    primary = next(iter(spec.model.__table__.primary_key.columns))
    result["id"] = str(getattr(row, primary.name))
    complete = {column.name: json_value(getattr(row, column.name)) for column in spec.model.__table__.columns if column.name not in SECRET_FIELDS}
    result["version"] = hashlib.sha256(json.dumps(complete, sort_keys=True, default=str).encode()).hexdigest()
    return result


def private_row(row):
    return {column.name: json_value(getattr(row, column.name)) for column in row.__table__.columns if column.name not in SECRET_FIELDS}


async def archive_rows(session, root):
    rows, visited = [], set()
    allowed = EVIDENCE | {"user_tags", "profile_tiles"}
    models = [mapper.class_ for mapper in Base.registry.mappers]
    async def visit(row):
        primary = next(iter(row.__table__.primary_key.columns))
        identifier = getattr(row, primary.name)
        marker = (row.__tablename__, str(identifier))
        if marker in visited:
            return
        visited.add(marker)
        if len(visited) > 500:
            raise ApiError(409, "This evidence subtree needs a smaller targeted repair")
        for model in models:
            for column in model.__table__.columns:
                if not any(fk.target_fullname == f"{row.__tablename__}.{primary.name}" for fk in column.foreign_keys):
                    continue
                children = (await session.scalars(select(model).where(getattr(model, column.name) == identifier))).all()
                if children and model.__tablename__ not in allowed:
                    raise ApiError(409, "This evidence is referenced by another feature; repair that reference first")
                for child in children:
                    await visit(child)
        rows.append({"resource_type": row.__tablename__, "values": private_row(row)})
    await visit(root)
    return rows


async def alignment_adjustment(session, rows, direction):
    for entry in rows:
        if entry["resource_type"] != "member_alignment_events":
            continue
        values = entry["values"]
        member = await session.get(Member, uuid.UUID(values["member_id"]))
        if member is not None:
            member.agreement_alignment_score = max(0, member.agreement_alignment_score + direction * values["delta"])


async def evidence_command(session, actor, spec, data, row, reason, source, correlation_id):
    archive_id = None
    if data.action == "archive_evidence":
        if data.values:
            raise ApiError(400, "Evidence archival accepts no replacement human statements")
        rows = await archive_rows(session, row)
        organization = await organization_for(session, row)
    else:
        if set(data.values) != {"archive_id"}:
            raise ApiError(400, "Restoring evidence requires the archive_id from its support receipt")
        try:
            archive_id = uuid.UUID(str(data.values["archive_id"]))
        except (ValueError, TypeError):
            raise ApiError(400, "Invalid archive identifier") from None
        archive = await session.get(NodeAdminSnapshot, archive_id)
        if archive is None or archive.operation != "archive_evidence" or archive.resource_type != spec.key or archive.resource_id != str(data.resource_id):
            raise ApiError(409, "The archive does not match this evidence resource")
        rows = archive.snapshot["rows"]
        organization = uuid.UUID(archive.snapshot["organization_id"]) if archive.snapshot.get("organization_id") else None
    if data.organization_id and organization and data.organization_id != organization:
        raise ApiError(409, "The evidence belongs to another support organization")
    event = audit_event(actor, data.action, spec.key, data.resource_id, organization, reason=reason, source=source, correlation_id=correlation_id,
                        fields=["administrative_archival" if data.action == "archive_evidence" else "administrative_restoration"], summary={"administrative_correction": True, "records_affected": len(rows)})
    models = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}
    if data.action == "archive_evidence":
        archive_id = uuid.uuid4()
        session.add(NodeAdminSnapshot(id=archive_id, action_id=event.id, resource_type=spec.key, resource_id=str(data.resource_id), operation=data.action,
                                      snapshot={"rows": rows, "organization_id": str(organization) if organization else None}))
        for entry in rows:
            model = models[entry["resource_type"]]
            primary = next(iter(model.__table__.primary_key.columns))
            await session.execute(delete(model).where(getattr(model, primary.name) == resource_key(resource_spec(entry["resource_type"]), entry["values"][primary.name])).execution_options(synchronize_session=False))
        await alignment_adjustment(session, rows, -1)
    else:
        for entry in reversed(rows):
            child_spec = resource_spec(entry["resource_type"])
            primary = next(iter(child_spec.model.__table__.primary_key.columns))
            values = {name: convert_value(child_spec.model.__table__.columns[name], value) for name, value in entry["values"].items()}
            if await session.get(child_spec.model, values[primary.name]) is not None:
                raise ApiError(409, "An original evidence row already exists; restoration will not overwrite it")
            await session.execute(child_spec.model.__table__.insert().values(**values))
        await alignment_adjustment(session, rows, 1)
    session.add(event)
    await session.commit()
    return {"resource": {"id": str(data.resource_id), "archived": data.action == "archive_evidence", "archive_id": str(archive_id)}, "audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"}


async def organization_for(session, row, seen=None):
    seen = set() if seen is None else seen
    marker = (row.__tablename__, str(getattr(row, "id", "")))
    if marker in seen:
        return None
    seen.add(marker)
    if isinstance(row, Ecosystem):
        return row.id
    if hasattr(row, "ecosystem_id"):
        return row.ecosystem_id
    models = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}
    for name in ("proposal_id", "agreement_id", "domain_id", "source_domain_id", "team_id", "member_id", "conflict_case_id", "conversation_id", "advice_log_id", "consent_record_id", "integration_round_id", "test_report_id", "decision_record_id", "quiz_id", "course_id", "collaboration_id"):
        column = row.__table__.columns.get(name)
        if column is None or not column.foreign_keys or getattr(row, name, None) is None:
            continue
        target = next(iter(column.foreign_keys)).target_fullname.split(".")[0]
        parent = await session.get(models[target], getattr(row, name))
        if parent is not None:
            found = await organization_for(session, parent, seen)
            if found is not None:
                return found
    return None


async def validate_references(session, spec, values, organization_id):
    models = {mapper.class_.__tablename__: mapper.class_ for mapper in Base.registry.mappers}
    for name, value in values.items():
        column = spec.model.__table__.columns[name]
        if value is None or not column.foreign_keys:
            continue
        target = next(iter(column.foreign_keys)).target_fullname.split(".")[0]
        referenced = await session.get(models[target], value)
        if referenced is None:
            raise ApiError(400, f"Reference '{name}' does not exist")
        reference_org = await organization_for(session, referenced)
        cross_link = spec.key == "collaborations" and name == "target_domain_id"
        if organization_id and reference_org and reference_org != organization_id and not cross_link:
            raise ApiError(400, f"Reference '{name}' belongs to another organization")


def convert_value(column, value):
    if value is None:
        if not column.nullable:
            raise ApiError(400, f"{column.name} is required")
        return None
    try:
        if isinstance(column.type, GUID):
            return uuid.UUID(str(value))
        if isinstance(column.type, Boolean):
            if not isinstance(value, bool):
                raise ValueError()
        elif isinstance(column.type, Integer):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError()
        elif isinstance(column.type, Float):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError()
        elif isinstance(column.type, DateTime):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        elif isinstance(column.type, Date):
            return date.fromisoformat(value)
        elif isinstance(column.type, JSON):
            import json
            if len(json.dumps(value, allow_nan=False)) > 64000:
                raise ValueError()
        else:
            if not isinstance(value, str) or len(value) > (getattr(column.type, "length", None) or 50000):
                raise ValueError()
            if not column.nullable and not value.strip():
                raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ApiError(400, f"Invalid value for '{column.name}'") from None
    return value


async def inspect_resource(factory, user_id, key, identifier, reason, *, source="ui", correlation_id=None):
    reason = public_reason(reason)
    spec = resource_spec(key)
    async with factory() as session:
        actor = await authorize(session, user_id)
        row = await session.get(spec.model, resource_key(spec, identifier))
        if row is None:
            raise ApiError(404, "Support resource not found")
        if key == "app_settings" and row.key not in SETTING_KEYS:
            raise ApiError(403, "This setting is managed on the server")
        organization = await organization_for(session, row)
        event = audit_event(actor, "inspect", key, identifier, organization, reason=reason, source=source, correlation_id=correlation_id)
        session.add(event)
        payload = serialize_resource(spec, row)
        await session.commit()
        return {"resource": payload, "audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"}


async def list_resources(factory, user_id, key, *, organization_id=None, search="", page=1, per_page=25, source="ui", reason="Technical support", correlation_id=None):
    spec = resource_spec(key)
    if not isinstance(page, int) or not 1 <= page <= 1000000:
        raise ApiError(400, "Invalid support page")
    per_page = min(50, max(1, int(per_page)))
    search = str(search or "")[:150].strip()
    async with factory() as session:
        actor = await authorize(session, user_id)
        query = select(spec.model)
        direct_scope = "ecosystem_id" in spec.model.__table__.columns or key == "ecosystems"
        if organization_id and direct_scope:
            query = query.where((spec.model.id if key == "ecosystems" else spec.model.ecosystem_id) == organization_id)
        if key == "app_settings":
            query = query.where(spec.model.key.in_(SETTING_KEYS))
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
                terms.append(getattr(spec.model, next(iter(spec.model.__table__.primary_key.columns)).name) == uuid.UUID(search))
            except ValueError:
                pass
            query = query.where(or_(*terms) if terms else False)
        primary = next(iter(spec.model.__table__.primary_key.columns))
        query = query.order_by(getattr(spec.model, primary.name))
        parent_scoped = bool(organization_id and not direct_scope and key not in {"users", "auth_sessions", "auth_challenges", "agent_tokens", "app_settings"})
        truncated = False
        if parent_scoped:
            candidates = (await session.scalars(query.limit(1001))).all()
            truncated = len(candidates) > 1000
            rows = []
            for row in candidates[:1000]:
                if await organization_for(session, row) == organization_id:
                    rows.append(row)
            total = len(rows)
            rows = rows[(page - 1) * per_page:page * per_page]
        else:
            total = await session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
            rows = (await session.scalars(query.offset((page - 1) * per_page).limit(per_page))).all()
        event = audit_event(actor, "list", key, organization_id=organization_id, source=source, reason=public_reason(reason), correlation_id=correlation_id)
        session.add(event)
        payload = {"items": [serialize_resource(spec, row, listing=True) for row in rows], "total": total, "page": page, "per_page": per_page,
                   "truncated": truncated, "audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"}
        if truncated:
            payload["message"] = "Narrow the search; only the first 1000 matching parent-scoped candidates were considered"
        await session.commit()
        return payload


async def execute_command(factory, user_id, data, *, source="ui", correlation_id=None):
    key, action, identifier = data.resource_type, data.action, data.resource_id
    reason = public_reason(data.reason)
    spec = resource_spec(key)
    if action not in spec.actions or action == "inspect":
        raise ApiError(400, "Unsupported support command")
    async with factory() as session:
        actor = await authorize(session, user_id)
        row = None if action == "create" else await session.get(spec.model, resource_key(spec, identifier), with_for_update=True)
        if action not in {"create", "restore_evidence"} and row is None:
            raise ApiError(404, "Support resource not found")
        if action == "restore_evidence" and row is not None:
            raise ApiError(409, "The original evidence still exists; restoration cannot overwrite it")
        if row is not None and data.expected_version is None:
            raise ApiError(409, "Inspect the resource and supply its version before making a correction")
        if row is not None and serialize_resource(spec, row)["version"] != data.expected_version:
            raise ApiError(409, "The resource changed; inspect it again before applying this correction")
        if action in {"archive_evidence", "restore_evidence"}:
            return await evidence_command(session, actor, spec, data, row, reason, source, correlation_id)
        organization = data.organization_id
        existing_org = await organization_for(session, row) if row is not None else None
        if existing_org and organization and existing_org != organization:
            raise ApiError(409, "The resource belongs to another organization")
        organization = existing_org or organization
        if "ecosystem_id" in spec.model.__table__.columns and not spec.model.__table__.columns["ecosystem_id"].nullable and spec.key != "ecosystems" and organization is None:
            raise ApiError(400, "Choose the organization for this support action")
        if organization is not None and await session.get(Ecosystem, organization) is None:
            raise ApiError(400, "Organization does not exist")
        if row is not None and data.expected_version is not None and serialize_resource(spec, row)["version"] != data.expected_version:
            raise ApiError(409, "The resource changed; inspect it again before applying this correction")
        supplied = data.values or {}
        if set(supplied) - spec.editable:
            raise ApiError(400, "The command contains fields outside the support allowlist")
        values = {name: convert_value(spec.model.__table__.columns[name], value) for name, value in supplied.items()}
        if action == "override_state" and (not values or set(values) - {"status", "current_status", "state"}):
            raise ApiError(400, "A state correction accepts only status, current_status or state")
        if key == "members":
            if "role" in values and values["role"] not in {"user", "mod", "admin", "owner"}:
                raise ApiError(400, "Unknown organization role")
            if "profile" in values and values["profile"] not in {None, "townhall", "collaborator", "builder", "co_creator"}:
                raise ApiError(400, "Unknown member profile")
        if key == "users" and row is not None and values.get("disabled_at") is not None and await is_node_admin(session, row.id):
            if not await remaining_usable_admins(session, row.id):
                raise ApiError(409, "The last usable node administrator cannot be disabled")
        if key == "users" and "username" in values and not values["username"]:
            raise ApiError(400, "A support username correction cannot remove the sign-in name")
        if key in {"user_badges", "badge_definitions"} and values.get("badge_key") == "node_admin":
            raise ApiError(400, "The Node admin badge comes only from a node administrator assignment")
        if key == "app_settings" and (values.get("key", getattr(row, "key", None)) not in SETTING_KEYS):
            raise ApiError(403, "This setting is managed on the server")
        if row is not None and "ecosystem_id" in values and values["ecosystem_id"] != existing_org:
            raise ApiError(400, "An existing resource cannot be moved between organizations")
        if action == "create" and "ecosystem_id" in spec.model.__table__.columns:
            values["ecosystem_id"] = organization
        await validate_references(session, spec, values, organization)
        if organization is None and action == "create":
            organization = await organization_for(session, spec.model(**values))
            await validate_references(session, spec, values, organization)
        before_private = private_row(row) if row is not None and spec.category != "security" else None
        event = audit_event(actor, action, key, identifier, organization, reason=reason, source=source, fields=values,
                            summary={"administrative_correction": True}, correlation_id=correlation_id)
        if action == "revoke":
            if key == "agent_tokens":
                row.revoked_at = now()
            elif key == "push_subscriptions":
                row.enabled = False
            elif key == "auth_sessions":
                row.expires_at = now()
            elif key == "auth_challenges":
                row.used = True
                row.expires_at = now()
            else:
                await session.delete(row)
            event.changed_fields = ["revoked"]
            payload = {"id": str(identifier), "revoked": True}
        else:
            if key == "agreements" and row is not None:
                from neos_agent.api.agreements import _snapshot_agreement, _bump_version
                session.add(_snapshot_agreement(row, change_reason=f"Administrative correction; support audit {event.id}", changed_by=f"{actor.display_name} (Node admin)"))
                _bump_version(row)
            if action == "create":
                values["id"] = uuid.uuid4()
                if key == "proposals":
                    values.update(proposal_id=f"SUP-{uuid.uuid4().hex[:12]}", proposer=f"{actor.display_name} (node admin, on behalf of organization)",
                                  proposer_member_id=None, support_created_by_user_id=actor.id, support_action_id=event.id)
                missing = [c.name for c in spec.model.__table__.columns if not c.nullable and not c.primary_key and c.default is None and c.server_default is None and c.name not in values]
                if missing:
                    raise ApiError(400, "Required fields: " + ", ".join(missing))
                row = spec.model(**values)
                session.add(row)
            else:
                if not values:
                    raise ApiError(400, "Choose at least one field to correct")
                for name, value in values.items():
                    setattr(row, name, value)
            if key == "agreements":
                from neos_agent.api.agreements import _regenerate_fingerprint
                _regenerate_fingerprint(row)
            await session.flush()
            await session.refresh(row)
            event.resource_id = str(getattr(row, next(iter(spec.model.__table__.primary_key.columns)).name))
            event.safe_summary = {"administrative_correction": True}
            payload = serialize_resource(spec, row)
        if spec.category != "security":
            session.add(NodeAdminSnapshot(action_id=event.id, resource_type=key, resource_id=event.resource_id, operation=action,
                                          snapshot={"before": before_private, "after": private_row(row)}))
        if key in {"users", "auth_sessions"}:
            await session.flush()
            if not await remaining_usable_admins(session, None):
                raise ApiError(409, "This correction would remove the last usable node administrator sign-in")
        session.add(event)
        await session.commit()
        return {"resource": payload, "audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"}


async def change_admin(factory, actor_id, target_id, reason, *, revoke=False):
    reason = public_reason(reason)
    async with factory() as session:
        actor = await authorize(session, actor_id)
        target = await session.get(User, target_id)
        if target is None:
            raise ApiError(404, "User not found")
        if not revoke and target.disabled_at is not None:
            raise ApiError(409, "Reactivate this user before granting node administrator authority")
        if not revoke and not await user_has_login(session, target):
            raise ApiError(409, "This user needs a usable sign-in method before receiving node administrator authority")
        assignment = await session.get(NodeAdmin, target_id)
        if revoke:
            if assignment is None or not assignment.active:
                raise ApiError(409, "This user is not an active node administrator")
            remaining = await remaining_usable_admins(session, target_id)
            if not remaining:
                raise ApiError(409, "The last node administrator cannot be revoked; assign another first")
            assignment.active, assignment.revoked_at, assignment.revoked_by_user_id = False, now(), actor.id
        elif assignment is not None and assignment.active:
            raise ApiError(409, "This user is already a node administrator")
        elif assignment is not None:
            assignment.active, assignment.granted_at, assignment.granted_by_user_id = True, now(), actor.id
            assignment.revoked_at, assignment.revoked_by_user_id = None, None
        else:
            session.add(NodeAdmin(user_id=target_id, active=True, granted_by_user_id=actor.id))
        event = audit_event(actor, "revoke_admin" if revoke else "grant_admin", "node_admins", target_id, reason=reason, fields=["active"])
        session.add(event)
        await session.commit()
        return {"user_id": str(target_id), "active": not revoke, "audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"}


async def remaining_usable_admins(session, excluded_user_id):
    usable = or_(and_(User.did.is_not(None), User.did != ""), and_(User.username.is_not(None), User.username != "", User.password_hash.is_not(None), User.password_hash != ""),
                 and_(User.oauth_provider.is_not(None), User.oauth_provider != "", User.oauth_id.is_not(None), User.oauth_id != ""),
                 select(AuthSession.id).where(AuthSession.user_id == User.id, AuthSession.expires_at > now()).exists())
    return await session.scalar(select(func.count()).select_from(NodeAdmin).join(User, User.id == NodeAdmin.user_id).where(
        NodeAdmin.active.is_(True), NodeAdmin.user_id != excluded_user_id, User.disabled_at.is_(None), usable))


async def user_has_login(session, user):
    if user.disabled_at is not None:
        return False
    if user.did or (user.username and user.password_hash) or (user.oauth_provider and user.oauth_id):
        return True
    return await session.scalar(select(AuthSession.id).where(AuthSession.user_id == user.id, AuthSession.expires_at > now()).limit(1)) is not None


async def support_provenance(session, proposal):
    actor_id = getattr(proposal, "support_created_by_user_id", None)
    if actor_id is None:
        return None
    actor = await session.get(User, actor_id)
    return {"actor_user_id": str(actor_id), "actor_name": actor.display_name if actor else "Node administrator",
            "organization_id": str(proposal.ecosystem_id), "action_id": str(proposal.support_action_id)}
