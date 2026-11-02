"""Ordinary member workflow tools; see agent/AGENTS.md, Personal operator workflows."""
from __future__ import annotations

import hashlib
import json
import uuid

from pydantic import ValidationError
from sqlalchemy import func, select

from neos_agent.api import conflicts, exit as exits, safeguards
from neos_agent.api.errors import ApiError
from neos_agent.api.policy import is_exit_leaver
from neos_agent.api.schemas.conflicts import ConflictUpdateRequest, RepairUpdateRequest
from neos_agent.api.schemas.safeguards import AuditUpdateRequest
from neos_agent.db.models import Domain, GovernanceHealthAudit, RepairAgreementRecord
from neos_agent.services import exchange, member_messaging as messaging


def _uuid(value, label):
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise ApiError(400, f"Choose the {label} from its list or page.")


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _ok(data, *, link=None, next_step=None, message=None):
    return {"success": True, "data": {**data, **({"link": link} if link else {}),
        **({"next_step": next_step} if next_step else {}), **({"message": message} if message else {})}}


def _ask(args, key, question, keys):
    from neos_agent.agent.governance_tools import _needs_confirmation
    return _needs_confirmation(args, key, question, keys)


async def _audit(db, key, scope, user_id):
    from neos_agent.agent import governance_tools as g
    audit = await g._find(db, GovernanceHealthAudit, key, "audit_id", scope, title_field=None)
    if audit is None:
        raise ApiError(404, "Audit not found")
    await db.refresh(audit, with_for_update=True)
    caller = await g._caller_row(db, user_id, audit.ecosystem_id)
    if caller is None or caller.current_status != "active":
        raise ApiError(404, "Audit not found")
    return audit, caller


async def _visible_target_domain(db, viewer, key):
    record_id = None
    try:
        record_id = uuid.UUID(str(key))
    except (ValueError, TypeError):
        pass
    stmt = select(Domain).where(exchange.collaboration_domain_clause(viewer))
    stmt = stmt.where(Domain.id == record_id) if record_id else stmt.where(func.lower(Domain.name) == str(key).strip().lower()).limit(2)
    rows = list((await db.scalars(stmt)).all())
    if len(rows) != 1:
        raise ApiError(404, "Choose one visible target group from find_collaboration_domains; the name is missing or not unique.")
    return rows[0]


async def _run(name, args, db, scope, user_id, keys):
    from neos_agent.agent import governance_tools as g

    if name == "list_conversations":
        page = max(1, int(args.get("page", 1)))
        rows = await messaging.list_threads(db, user_id, scope, page=page)
        for row in rows:
            row["link"] = f"/messaging?conversation={row['id']}"
            row["name"] = row["title"] or "Chat with " + ", ".join(person["display_name"] for person in row["participants"])
        return _ok({"conversations": rows, "count": len(rows), "page": page, "per_page": 50, "may_have_more": len(rows) == 50})
    if name == "get_conversation":
        record_id = _uuid(args.get("conversation_id"), "conversation")
        detail = await messaging.read_thread(db, user_id, record_id, page=args.get("page", 1), limit=args.get("limit", 30))
        detail["name"] = detail["title"] or "Chat with " + ", ".join(person["display_name"] for person in detail["participants"])
        return _ok(detail, link=f"/messaging?conversation={record_id}", next_step="Read the messages, or ask to send your own reply.")
    if name == "search_messages":
        page = max(1, int(args.get("page", 1)))
        rows = await messaging.search_thread_messages(db, user_id, scope, args.get("query"), page=page)
        for row in rows:
            row["link"] = f"/messaging?conversation={row['conversation_id']}"
        return _ok({"messages": rows, "count": len(rows), "page": page, "per_page": 50, "may_have_more": len(rows) == 50})
    if name == "find_message_members":
        rows = await messaging.find_recipients(db, user_id, query=args.get("query", ""))
        return _ok({"members": rows, "count": len(rows)}, next_step="Choose the exact member and ecosystem before starting a conversation.")
    if name == "create_conversation":
        ecosystem_id, error = await g._target_ecosystem(db, scope, args)
        if ecosystem_id is None:
            raise ApiError(400, error)
        prepared = await messaging.prepare_thread(db, user_id, ecosystem_id, args.get("participant_ids"),
            type=args.get("type", "dm"), title=args.get("title"))
        creator, recipients, kind, title = prepared
        payload = {"creator": str(creator.id), "recipients": [
            {"id": str(row.id), "user_id": str(row.user_id), "name": row.display_name} for row in recipients], "type": kind, "title": title}
        initial = args.get("message")
        if initial is not None and (not isinstance(initial, str) or not initial.strip() or len(initial) > 10000):
            raise ApiError(400, "Write the initial message in 1 to 10000 characters, or leave it out.")
        question = f"Start a {'direct' if kind == 'dm' else 'group'} conversation with {', '.join(row.display_name for row in recipients)}"
        question += f" and send this exact message: {initial}" if initial else ". No message will be sent yet."
        asked = _ask(args, "create_conversation:" + _fingerprint(payload), question, keys)
        if asked:
            return asked
        conversation = await messaging.open_thread(db, prepared)
        if initial is not None:
            await messaging.post_message(db, await messaging.prepare_message(db, user_id, conversation.id, initial))
        detail = await messaging.read_thread(db, user_id, conversation.id)
        detail["name"] = title or "Chat with " + ", ".join(row.display_name for row in recipients)
        return _ok(detail, link=f"/messaging?conversation={conversation.id}", message="Your conversation is ready.", next_step="Read it or send your next message.")
    if name == "send_message":
        conversation_id = _uuid(args.get("conversation_id"), "conversation")
        prepared = await messaging.prepare_message(db, user_id, conversation_id, args.get("content"))
        people = await messaging.participants(db, conversation_id)
        recipients = [row for row in people if row["id"] != str(prepared[1].id)]
        key = f"send_message:{conversation_id}:" + _fingerprint(await messaging.recipient_binding(db, conversation_id, prepared[1].id))
        asked = _ask(args, key, f"Send this exact message to {', '.join(row['display_name'] for row in recipients)}: {prepared[2]}", keys)
        if asked:
            return asked
        message = await messaging.post_message(db, prepared)
        return _ok({**message, "conversation_id": str(conversation_id)}, link=f"/messaging?conversation={conversation_id}",
            message="Your message was sent.", next_step="The people in this conversation can now read it.")
    if name == "find_collaboration_domains":
        viewer = await exchange.load_viewer(db, user_id)
        rows = await exchange.collaboration_domains(db, viewer, args.get("query", ""))
        return _ok({"domains": rows, "count": len(rows)}, next_step="Choose your source group and one target group.")
    if name == "find_collaborations":
        viewer = await exchange.load_viewer(db, user_id)
        result = await exchange.search_collaborations(db, viewer, query=args.get("query", ""), status=args.get("status", "active"), tier=args.get("engagement_tier"), page=args.get("page", 1))
        result["items"] = [g._collaboration_brief(row) for row in result["items"]]
        return _ok(result)
    if name == "get_collaboration":
        viewer = await exchange.load_viewer(db, user_id)
        found = await g._find_collaboration(db, viewer, args.get("collaboration"))
        if found is None:
            raise ApiError(404, "Collaboration not found")
        record, sides = found
        return _ok(await exchange.collaboration_payload(db, viewer, record, sides), link=f"/discover/collaborations/{record.id}")
    if name == "propose_collaboration":
        viewer = await exchange.load_viewer(db, user_id)
        source = await g._find_domain(db, args.get("source_domain"), scope)
        if source is None:
            raise ApiError(404, "Your source group was not found in the selected ecosystems.")
        target = await _visible_target_domain(db, viewer, args.get("target_domain"))
        body = {key: args[key] for key in ("title", "description", "engagement_tier", "terms", "review_date", "linked_share_need_id") if key in args}
        body.update(source_domain_id=str(source.id), target_domain_id=str(target.id))
        values, proposer, sides = await exchange.prepare_collaboration(db, viewer, body)
        source_approval = exchange._may_approve(proposer, sides.source.ecosystem_id, sides, proposer.user_id)
        question = f"Propose '{values['title']}' between {g.domain_display_name(source)} and {g.domain_display_name(target)}? "
        question += "Your source-side steward approval will be recorded; the other side still has to approve." if source_approval else "Its page will show the steward approval still needed."
        asked = _ask(args, "propose_collaboration:" + _fingerprint({"values": values, "source_approval": source_approval}), question, keys)
        if asked:
            return asked
        record = await exchange.propose_collaboration(db, viewer, body)
        record, sides = await exchange.load_collaboration(db, viewer, record.id)
        return _ok(await exchange.collaboration_payload(db, viewer, record, sides), link=f"/discover/collaborations/{record.id}",
            message="Your collaboration proposal is recorded.", next_step="The page shows which side still needs approval.")
    if name in {"get_health_audit", "update_health_audit", "publish_health_audit", "abandon_health_audit"}:
        audit, caller = await _audit(db, args.get("audit_id"), scope, user_id)
        link = f"/safeguards/audits/{audit.id}"
        if name == "update_health_audit":
            if not args.get("changes"):
                raise ApiError(400, "Say which draft fields or ratings you want to change.")
            fields = AuditUpdateRequest(**args.get("changes", {})).model_dump(exclude_none=True)
            if set(args.get("changes", {})) - set(AuditUpdateRequest.model_fields):
                raise ApiError(400, "Only draft audit fields may be edited.")
            safeguards.edit_audit_record(audit, caller, fields)
            await db.flush()
        elif name == "publish_health_audit":
            plan = await safeguards.prepare_audit_publication(db, audit, caller)
            signature = {"audit": str(audit.id), "plan": plan, "findings": audit.findings,
                         "scope": audit.audit_scope, "recommendations": audit.structured_recommendations}
            asked = _ask(args, "publish_health_audit:" + _fingerprint(signature),
                f"Publish the rated audit '{audit.audit_id}'? Its measured values and ratings will be frozen and visible to this ecosystem.", keys)
            if asked:
                return asked
            await safeguards.publish_audit_record(db, audit, caller, plan)
        elif name == "abandon_health_audit":
            reason = await safeguards.prepare_audit_abandonment(db, audit, caller, args.get("reason"))
            asked = _ask(args, f"abandon_health_audit:{audit.id}", f"Abandon draft '{audit.audit_id}' and record this reason: {reason}", keys)
            if asked:
                return asked
            await safeguards.abandon_audit_draft(db, audit, caller, reason)
            await db.flush()
        await db.refresh(audit)
        return _ok(await safeguards.audit_detail_payload(db, audit, caller), link=link,
            next_step="Review the audit on its page." if audit.status != "draft" else "Review the ratings and findings; publishing needs your confirmation.")
    if name in {"update_exit_status", "export_portable_record"}:
        record = await g._find_exit(db, str(args.get("exit_id") or ""), scope, user_id)
        if record is None:
            raise ApiError(404, "Exit record not found")
        await db.refresh(record, with_for_update=True)
        caller = await g._caller_row(db, user_id, record.ecosystem_id)
        if name == "export_portable_record":
            if not is_exit_leaver(caller, record):
                raise ApiError(403, "Only the person leaving can download their portable record.")
            return _ok({"id": str(record.id), "title": "Download your portable record", "download_ready": True,
                "downloaded": False}, link=f"/api/v1/exit/{record.id}/portable-record",
                next_step="Open this private link to download your own records as JSON. A link alone does not mark the download complete.")
        new_status = args.get("new_status")
        exits.validate_exit_move(record, caller, new_status)
        asked = _ask(args, f"update_exit_status:{record.id}:{record.status}:{new_status}",
            f"Record this exit as {new_status}? " + ("This ends the membership and clears its roles and agreement consents." if new_status == "completed" else "This records your chosen next step."), keys)
        if asked:
            return asked
        await exits.apply_exit_move(db, record, caller, new_status)
        await db.refresh(record)
        member_name = await exits._member_name(db, record.member_id)
        return _ok(exits.to_detail(record, member_name, caller), link=f"/exit/{record.id}", message=f"The exit is now {new_status}.")
    if name in {"update_conflict_case", "update_repair_agreement"}:
        case, caller = await g._find_visible_case(db, args.get("case_id"), scope, user_id)
        if case is None:
            raise ApiError(404, "Conflict case not found")
        await db.refresh(case, with_for_update=True)
        supplied = args.get("changes", {})
        if not isinstance(supplied, dict) or not supplied:
            raise ApiError(400, "changes must contain the named fields you want to update")
        if name == "update_conflict_case":
            if set(supplied) - set(ConflictUpdateRequest.model_fields):
                raise ApiError(400, "Choose only fields from the conflict form.")
            fields = ConflictUpdateRequest(**supplied).model_dump(exclude_none=True)
            changes = await conflicts.prepare_case_update(db, case, caller, fields)
            key = f"update_conflict_case:{case.id}:{case.status}:" + _fingerprint(changes)
            asked = _ask(args, key, f"Update case '{case.title}' with these changes: {json.dumps(supplied, ensure_ascii=False)}", keys)
            if asked:
                return asked
            await conflicts.apply_case_update(db, case, caller, fields)
            case = await conflicts._reload(db, case.id)
            return _ok(await conflicts._conflict_to_detail(db, case, caller), link=f"/conflicts/{case.id}", message="Your case update is recorded.")
        repair_id = _uuid(args.get("repair_id"), "repair agreement")
        repair = await db.scalar(select(RepairAgreementRecord).where(RepairAgreementRecord.id == repair_id,
            RepairAgreementRecord.conflict_case_id == case.id).with_for_update())
        if set(supplied) - set(RepairUpdateRequest.model_fields):
            raise ApiError(400, "Choose only repair check-in fields.")
        fields = RepairUpdateRequest(**supplied).model_dump(exclude_none=True)
        changes = await conflicts.prepare_repair_update(case, caller, repair, fields)
        asked = _ask(args, f"update_repair_agreement:{repair_id}:{repair.status}:" + _fingerprint(changes),
            f"Record this repair check-in for '{repair.title}': {json.dumps(supplied, ensure_ascii=False)}", keys)
        if asked:
            return asked
        await conflicts.apply_repair_update(db, case, caller, repair, fields)
        await db.refresh(repair)
        return _ok(conflicts._repair_to_schema(repair).model_dump(mode="json"), link=f"/conflicts/{case.id}", message="Your repair check-in is recorded.")
    raise ApiError(400, "Unknown operator tool")


READ_TOOLS = frozenset({"list_conversations", "get_conversation", "search_messages", "find_message_members",
    "find_collaboration_domains", "find_collaborations", "get_collaboration", "get_health_audit", "export_portable_record"})
CONFIRMED_TOOLS = frozenset({"create_conversation", "send_message", "propose_collaboration", "publish_health_audit",
    "abandon_health_audit", "update_exit_status", "update_conflict_case", "update_repair_agreement"})


def _string(description):
    return {"type": "string", "description": description}


def _schema(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


_ID = _string("The record UUID from a successful lookup or its page.")
_CHANGES = {"type": "object", "description": "Only the exact named form fields the member asked to change; do not invent facts or commitments."}
_CONFLICT_CHANGES = {**ConflictUpdateRequest.model_json_schema(), "description": "Exact conflict form fields. To resolve, include status: resolved AND the supplied resolution_summary in the same prepared payload. To close, include status: closed. A resolution_summary alone only edits the text; it does not resolve the case. Never use summary as a field name."}
_CONFIRMED = {"type": "boolean", "description": "Omit initially. The server executes the frozen payload only after the member confirms in a later turn."}
_PAGE = {"type": "integer", "minimum": 1, "description": "Page of results, starting at 1; ask for later pages if more may exist."}
SPECS = {
    "list_conversations": ("List a page of the signed-in member's conversations and unread counts in the selected scope, plus their cross-ecosystem post replies.", _schema({"page": _PAGE})),
    "get_conversation": ("Read recent messages only from a conversation the actual member participates in. This marks the served messages read.", _schema({"conversation_id": _ID, "page": {"type": "integer", "minimum": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}}, ["conversation_id"])),
    "search_messages": ("Search a page of the member's own visible conversations, never all platform messages.", _schema({"query": _string("Words from message text."), "page": _PAGE}, ["query"])),
    "find_message_members": ("Find active recipients by name in ecosystems where the caller is active. If names repeat, ask which person/ecosystem.", _schema({"query": _string("Part of the recipient's display name.")})),
    "create_conversation": ("Start a direct or group conversation as the actual member. Always include message: the exact supplied text for an atomic create-and-send request, or an empty string only when the member wants no initial message. Never silently prepare an empty conversation when asked to send. Resolve recipients first; confirmation binds the complete first payload.", _schema({"ecosystem": _string("The selected ecosystem's name; ask when several are selected."), "participant_ids": {"type": "array", "items": _ID, "minItems": 1, "maxItems": 20}, "type": {"type": "string", "enum": ["dm", "group"]}, "title": _string("Optional member-chosen title."), "message": _string("Required explicit intent: exact text the member chose to send, or empty string for intentionally no initial message."), "confirmed": _CONFIRMED}, ["participant_ids", "message"])),
    "send_message": ("Send the member's exact text to an existing conversation; resolve and read it first. Never write as another person. Confirmation binds text and the current participants.", _schema({"conversation_id": _ID, "content": _string("The exact text to send, chosen by the member."), "confirmed": _CONFIRMED}, ["conversation_id", "content"])),
    "find_collaboration_domains": ("Find active groups that can be collaboration targets: public ecosystems or ones the caller belongs to. No private outside groups are returned.", _schema({"query": _string("Words in the group's name or purpose.")})),
    "find_collaborations": ("Discover visible collaborations with their sides and status; private proposed partnerships remain restricted to their participants' ecosystems.", _schema({"query": _string("Words in title or description."), "status": {"type": "string", "enum": ["active", "proposed", "completed", "dissolved", "all"]}, "engagement_tier": _string("Optional observe, cooperate, federate or integrate filter."), "page": _PAGE})),
    "get_collaboration": ("Read one visible collaboration's terms, approvals and next actions by UUID or exact unique title.", _schema({"collaboration": _ID}, ["collaboration"])),
    "propose_collaboration": ("Propose collaboration between the member's source group and a visible target group through the normal exchange rules. Ask for their title and terms; do not invent commitments. Preflight resolves only the given IDs; it does not substitute for an explicitly requested find/list. Complete requested existing-collaboration and group searches even when IDs were provided. Confirmation required; proposal does not approve both sides.", _schema({"source_domain": _ID, "target_domain": _ID, "title": _string("The member's chosen title."), "description": _string("The member's proposed purpose."), "engagement_tier": {"type": "string", "enum": ["observe", "cooperate", "federate", "integrate"]}, "terms": {"type": "object"}, "review_date": _string("Optional YYYY-MM-DD chosen by the member."), "linked_share_need_id": _ID, "confirmed": _CONFIRMED}, ["source_domain", "target_domain", "title"])),
    "get_health_audit": ("Read a scoped governance audit and its ratings, author and available actions.", _schema({"audit_id": _ID}, ["audit_id"])),
    "update_health_audit": ("Edit only the actual auditor's draft. changes may contain audit_scope, audit_period_start/end, indicator_scores, findings, structured_recommendations. Record the member's own ratings; never invent ratings.", _schema({"audit_id": _ID, "changes": _CHANGES}, ["audit_id", "changes"])),
    "publish_health_audit": ("Publish the actual auditor's rated draft after independence and complete-rating validation; freeze computed values. Confirmation binds the complete current publication plan.", _schema({"audit_id": _ID, "confirmed": _CONFIRMED}, ["audit_id"])),
    "abandon_health_audit": ("Abandon an audit draft as its auditor or a steward, with an at-least-eight-character recorded reason. Requires confirmation.", _schema({"audit_id": _ID, "reason": _string("The member's reason, at least 8 characters."), "confirmed": _CONFIRMED}, ["audit_id", "reason"])),
    "update_exit_status": ("Follow an exit through its real moves: only the leaver cancels; another steward starts handoff or confirms completion. No minimum wait or permission to choose exit. Confirmation required.", _schema({"exit_id": _ID, "new_status": {"type": "string", "enum": ["unwinding", "completed", "cancelled"]}, "confirmed": _CONFIRMED}, ["exit_id", "new_status"])),
    "export_portable_record": ("Get the actual private download link for the caller's own portable governance records, including after departure. Does not put the export in model context or claim the download occurred.", _schema({"exit_id": _ID}, ["exit_id"])),
    "update_conflict_case": ("Update a visible case through the shared form and lifecycle rules. Reporter can correct title/description/domain or close their report; a non-party steward/facilitator manages moves. For a requested resolution, prepare changes.status=resolved together with changes.resolution_summary in the first call. Merely editing resolution_summary leaves the stage unchanged. All updates are confirmed.", _schema({"case_id": _ID, "changes": _CONFLICT_CHANGES, "confirmed": _CONFIRMED}, ["case_id", "changes"])),
    "update_repair_agreement": ("Record a repair check-in through the same facilitator/steward rules as its form. changes may include checkin_30/60/90_notes/date, commitments, title, responsible_party, status. Fulfilled needs confirmed_by_parties:true only if the member explicitly reports both parties agreed; never infer it from a generic yes. Requires confirmation.", _schema({"case_id": _ID, "repair_id": _ID, "changes": _CHANGES, "confirmed": _CONFIRMED}, ["case_id", "repair_id", "changes"])),
}


def definitions(tool_type):
    result = []
    for name, (description, schema) in SPECS.items():
        def handler_for(tool_name):
            async def handler(args, db, ecosystem_ids=None, *, caller_user_id=None, confirmed_keys=frozenset()):
                if caller_user_id is None:
                    from neos_agent.agent.governance_tools import CALLER_REQUIRED
                    return {"success": False, "error": CALLER_REQUIRED}
                properties = SPECS[tool_name][1]["properties"]
                if set(args) - set(properties):
                    return {"success": False, "error": "Unknown fields cannot change the acting member or tool scope."}
                try:
                    return await _run(tool_name, args, db, ecosystem_ids, caller_user_id, confirmed_keys)
                except ApiError as error:
                    return {"success": False, "error": error.message, **error.extra}
                except (ValidationError, ValueError, TypeError):
                    return {"success": False, "error": "Check the supplied fields and use the record's current form values."}
            return handler
        result.append(tool_type(name=name, description=description, parameters=schema, handler=handler_for(name)))
    return result
