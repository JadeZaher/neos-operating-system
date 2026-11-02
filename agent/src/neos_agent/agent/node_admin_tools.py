"""Explicit node-support tools; see agent/NODE_SUPPORT.md."""
from __future__ import annotations

import hashlib
import json
import uuid

from pydantic import ValidationError
from sqlalchemy import select

from neos_agent.api.errors import ApiError
from neos_agent.api.schemas.node_admin import SupportCommandRequest, SupportProposalPrepareRequest
from neos_agent.db.models import Ecosystem
from neos_agent.services.node_admin import audit_event, authorize, execute_command, inspect_resource, list_resources, log_failure, organization_for, public_reason, resource_key, resource_spec, serialize_resource
from neos_agent.services.node_admin_catalog import catalog_entry, registry

TOOL_NAMES = frozenset({"node_support_catalog", "node_support_list", "node_support_inspect", "node_support_command", "node_support_prepare_proposal"})


async def validate_support_context(factory, caller_user_id, support_context):
    if not isinstance(support_context, dict) or support_context.get("enabled") is not True:
        return None
    try:
        organization_id = uuid.UUID(str(support_context.get("organization_id")))
        reason = public_reason(support_context.get("reason"))
        async with factory() as session:
            await authorize(session, caller_user_id)
            if await session.get(Ecosystem, organization_id) is None:
                return None
        return {"enabled": True, "organization_id": str(organization_id), "reason": reason}
    except (ApiError, ValueError, TypeError):
        return None


async def definitions_for_node_admin(factory, caller_user_id, support_context):
    if await validate_support_context(factory, caller_user_id, support_context) is None:
        return []
    resources = registry()
    resource_parameter = {"type": "string", "enum": sorted(resources), "description": "Use the exact canonical resource key from this enum; do not singularize or invent aliases."}
    actions = sorted({action for spec in resources.values() for action in spec.actions if action != "inspect"})
    definitions = [
        {"name": "node_support_prepare_proposal", "description": "PREFERRED tool to PREPARE a NEW ORGANIZATION PROPOSAL FOR REVIEW. Pass only the user's title, proposed change, rationale and optional proposal type. This does NOT create or write anything: it returns the exact server confirmation card. Call it BEFORE asking for approval. The server supplies draft status, selected organization, actual administrator and provenance; never pass those fields. Only a later user confirmation can create the frozen draft.", "input_schema": SupportProposalPrepareRequest.model_json_schema()},
        {"name": "node_support_list", "description": "Find record IDs by resource type and search in the selected support organization, including parent-scoped records. Bounded and publicly audited; inspect the exact result before correcting it.", "input_schema": {"type": "object", "properties": {"resource_type": {"type": "string"}, "search": {"type": "string"}, "page": {"type": "integer", "minimum": 1}}, "required": ["resource_type"], "additionalProperties": False}},
        {"name": "node_support_catalog", "description": "Without resource_type, receive the complete compact resource/action index. With an exact resource_type, receive ALL fields and required values for that resource. Fetch its targeted schema before creating/correcting it; this read is audited.", "input_schema": {"type": "object", "properties": {"resource_type": resource_parameter}, "additionalProperties": False}},
        {"name": "node_support_inspect", "description": "Inspect a support resource in the organization selected for support. Private content stays out of the public audit; your access is recorded.", "input_schema": {"type": "object", "properties": {"resource_type": {"type": "string"}, "resource_id": {"type": "string"}}, "required": ["resource_type", "resource_id"], "additionalProperties": False}},
        {"name": "node_support_command", "description": "PREPARE FOR REVIEW an administrative correction or organization proposal. Calling this tool from the model DOES NOT WRITE the change: it freezes the exact target and values and returns the server review/confirmation card. ALWAYS call this tool BEFORE asking the user to approve or go ahead; a prose-only review cannot be approved. Do not wait for approval before calling. Fetch the targeted catalog schema and inspect existing records first. The server alone applies the frozen change after a later user confirmation; never impersonate member consent.", "input_schema": {"type": "object", "properties": {"resource_type": {"type": "string"}, "resource_id": {"type": "string"}, "action": {"type": "string"}, "values": {"type": "object"}, "expected_version": {"type": "string", "description": "Exact version returned by inspecting the existing target; omit for create."}}, "required": ["resource_type", "action", "values"], "additionalProperties": False}},
    ]
    for definition in definitions:
        properties = definition["input_schema"]["properties"]
        if "resource_type" in properties:
            properties["resource_type"] = resource_parameter
        if "action" in properties:
            properties["action"] = {"type": "string", "enum": actions, "description": "Use an action declared for this exact resource by node_support_catalog(resource_type)."}
    return definitions


async def execute_node_admin_tool(name, args, *, factory, caller_user_id, support_context, confirmed_keys=frozenset(), agent_session_id=None):
    context = None
    organization = None
    correlation_id = None
    try:
        context = await validate_support_context(factory, caller_user_id, support_context)
        if context is None or name not in TOOL_NAMES:
            raise ApiError(403, "Choose explicit node support mode, organization and reason as a current node administrator")
        if not isinstance(args, dict):
            raise ApiError(400, "Invalid support tool arguments")
        organization = uuid.UUID(context["organization_id"])
        correlation_id = str(uuid.UUID(str(agent_session_id))) if agent_session_id else None
        if name == "node_support_list":
            if set(args) - {"resource_type", "search", "page"}:
                raise ApiError(400, "Support lookup cannot change its identity, organization or reason")
            result = await list_resources(factory, caller_user_id, args.get("resource_type"), organization_id=organization, search=args.get("search", ""), page=args.get("page", 1),
                                          source="agent", reason=context["reason"], correlation_id=correlation_id)
            return {"success": True, "data": result}
        if name == "node_support_catalog":
            if set(args) - {"resource_type"}:
                raise ApiError(400, "The support catalog accepts only its canonical resource_type")
            resources = registry()
            spec = resource_spec(args["resource_type"]) if args.get("resource_type") else None
            async with factory() as session:
                actor = await authorize(session, caller_user_id)
                session.add(audit_event(actor, "catalog", "node_support", organization_id=organization, reason=context["reason"], source="agent", correlation_id=correlation_id))
                await session.commit()
            if spec is None:
                data = {"resource_actions": {key: value.actions for key, value in sorted(resources.items())}, "organization_id": str(organization),
                        "next_step": "Call node_support_catalog with the exact resource_type to obtain its complete field schema before a command."}
            else:
                entry = catalog_entry(spec)
                data = {"resource_type": spec.key, "actions": spec.actions, "organization_id": str(organization),
                        "fields": {field["name"]: {key: value for key, value in field.items() if key not in {"name", "label"}} for field in entry["fields"] if field["editable"] and field["name"] != "ecosystem_id"},
                        "next_step": "Only writable fields are shown. Organization, actor, record IDs, provenance and timestamps are server-managed. For a new proposal prefer node_support_prepare_proposal with its flat fields. Inspect existing records for their version."}
            return {"success": True, "complete_support_schema": True, "data": data}
        if name == "node_support_prepare_proposal":
            proposal = SupportProposalPrepareRequest.model_validate({key: value for key, value in args.items() if key != "confirmed"})
            args = {"resource_type": "proposals", "action": "create", "values": {**proposal.model_dump(), "status": "draft"},
                    **({"confirmed": args["confirmed"]} if "confirmed" in args else {})}
        allowed = {"resource_type", "resource_id"} if name == "node_support_inspect" else {"resource_type", "resource_id", "action", "values", "expected_version", "confirmed"}
        if set(args) - allowed:
            raise ApiError(400, "Support tool arguments cannot change the acting identity, organization or reason")
        spec = resource_spec(args.get("resource_type"))
        if args.get("resource_id") and args.get("action") != "restore_evidence":
            async with factory() as session:
                await authorize(session, caller_user_id)
                row = await session.get(spec.model, resource_key(spec, args["resource_id"]))
                if row is None:
                    raise ApiError(404, "Support resource not found")
                target_org = await organization_for(session, row)
                if target_org is not None and target_org != organization:
                    raise ApiError(409, "Change the explicit support organization before acting on this resource")
        if name == "node_support_inspect":
            result = await inspect_resource(factory, caller_user_id, spec.key, args.get("resource_id"), context["reason"], source="agent", correlation_id=correlation_id)
            return {"success": True, "data": result}
        data = {key: value for key, value in args.items() if key != "confirmed"}
        data.update(organization_id=str(organization), reason=context["reason"])
        command = SupportCommandRequest.model_validate(data)
        if command.action not in spec.actions or command.action == "inspect":
            raise ApiError(400, "Unsupported support command")
        permitted_fields = {"archive_id"} if command.action == "restore_evidence" else spec.editable - {"ecosystem_id"}
        if set(command.values) - permitted_fields:
            raise ApiError(400, "This correction contains fields outside the support allowlist", {"writable_fields": sorted(permitted_fields)})
        review_values = json.dumps(command.values, sort_keys=True, indent=2, ensure_ascii=False)
        if len(review_values) > 3000:
            raise ApiError(400, "This correction is too large to review in chat. Apply it in the Node support console, where the full patch can be reviewed before saving")
        frozen = json.dumps({"name": name, "args": data}, sort_keys=True, separators=(",", ":"))
        key = "node_support:" + hashlib.sha256(frozen.encode()).hexdigest()
        if args.get("confirmed") is not True or key not in (confirmed_keys or frozenset()):
            question = (f"Confirm this publicly audited node support correction.\nAction: {command.action}\nResource: {command.resource_type}"
                        f"\nTarget: {command.resource_id or 'new record'}\nOrganization: {organization}\nPublic reason: {context['reason']}"
                        f"\nExact values:\n{review_values}")
            return {"success": False, "needs_confirmation": question, "confirmation_key": key, "error": "No change made. Ask the user to confirm this exact support action."}
        return {"success": True, "data": await execute_command(factory, caller_user_id, command, source="agent", correlation_id=correlation_id)}
    except (ApiError, ValidationError, ValueError, TypeError) as exc:
        try:
            await log_failure(factory, caller_user_id, "agent_support_request", "node_support", outcome="denied" if isinstance(exc, ApiError) and exc.status == 403 else "failed", source="agent", organization_id=organization, reason=context["reason"] if context else "Technical support", correlation_id=correlation_id)
        except Exception:
            return {"success": False, "error": "Support audit is unavailable; no correction was committed"}
        return {"success": False, "error": exc.message if isinstance(exc, ApiError) else "Invalid support tool request", **(exc.extra if isinstance(exc, ApiError) else {})}
    except Exception:
        try:
            await log_failure(factory, caller_user_id, "agent_support_request", "node_support", outcome="failed", source="agent", organization_id=organization, reason=context["reason"] if context else "Technical support", correlation_id=correlation_id)
        except Exception:
            return {"success": False, "error": "Support audit is unavailable; no correction was committed"}
        return {"success": False, "error": "The support correction could not be saved; no correction was committed"}
