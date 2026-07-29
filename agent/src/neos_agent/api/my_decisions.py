"""JSON API blueprint for member decisions (user-owned decision substrate).

Blueprint: my_decisions_api_bp, url_prefix="/api/v1/my-decisions"

A MemberDecision is one member's personal decision about a subject
(agreement | proposal | share | need), doubling as a follow-up task with a
personal state. This API is inherently own-rows-only: the caller only ever
sees and edits their OWN decisions — other people's rows 404 (not 403), so
existence is never leaked. Distinct from DecisionRecord (the ecosystem
artifact ledger minted by completed ACT processes).

Identity model: a user has ONE Member row per ecosystem. Subject validation
always resolves the caller's Member row in the SUBJECT's ecosystem — never
`limit(1)` across ecosystems.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import (
    Agreement,
    Member,
    MemberDecision,
    Proposal,
    SharesNeeds,
)

from .helpers import require_auth

logger = logging.getLogger(__name__)

my_decisions_api_bp = Blueprint("my_decisions_api", url_prefix="/api/v1/my-decisions")

SUBJECT_TYPES = ("agreement", "proposal", "share", "need")
DECISION_STATES = ("intended", "in_progress", "done", "follow_up", "dropped")

# Subject must be in a decision-able state to open a decision on it.
_REQUIRED_SUBJECT_STATUS = {"agreement": "active", "proposal": "ratified"}


def _to_dict(d: MemberDecision, subject_title: str | None = None) -> dict:
    return {
        "id": str(d.id),
        "ecosystem_id": str(d.ecosystem_id),
        "subject_type": d.subject_type,
        "subject_id": str(d.subject_id),
        "decision": d.decision,
        "state": d.state,
        "notes": d.notes,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "subject_title": subject_title,
    }


async def _caller_members(session, user_id: uuid.UUID) -> list[Member]:
    """ALL of the caller's Member rows — one per ecosystem."""
    result = await session.execute(select(Member).where(Member.user_id == user_id))
    return list(result.scalars().all())


async def _resolve_subject_titles(session, decisions: list[MemberDecision]) -> dict[uuid.UUID, str]:
    """Batch-resolve subject titles per subject_type (one query per type)."""
    titles: dict[uuid.UUID, str] = {}
    by_type: dict[str, list[uuid.UUID]] = {}
    for d in decisions:
        by_type.setdefault(d.subject_type, []).append(d.subject_id)

    for subject_type, ids in by_type.items():
        if subject_type == "agreement":
            rows = await session.execute(select(Agreement.id, Agreement.title).where(Agreement.id.in_(ids)))
        elif subject_type == "proposal":
            rows = await session.execute(select(Proposal.id, Proposal.title).where(Proposal.id.in_(ids)))
        else:  # share | need
            rows = await session.execute(select(SharesNeeds.id, SharesNeeds.title).where(SharesNeeds.id.in_(ids)))
        for subject_id, title in rows.all():
            titles[subject_id] = title
    return titles


async def _validate_subject(session, subject_type: str, subject_id: uuid.UUID):
    """Return (ecosystem_id, None) if the subject exists and is decision-able,
    or (None, error_response). Membership is checked by the caller."""
    if subject_type == "agreement":
        subject = await session.get(Agreement, subject_id)
        required = _REQUIRED_SUBJECT_STATUS[subject_type]
    elif subject_type == "proposal":
        subject = await session.get(Proposal, subject_id)
        required = _REQUIRED_SUBJECT_STATUS[subject_type]
    else:  # share | need
        subject = await session.get(SharesNeeds, subject_id)
        required = "active"
        if subject is not None and subject.type != subject_type:
            return None, json(
                {"error": f"Subject {subject_id} is a '{subject.type}', not a '{subject_type}'"},
                status=400,
            )

    if subject is None:
        return None, json({"error": f"{subject_type.capitalize()} not found"}, status=404)
    if subject.status != required:
        return None, json(
            {"error": f"Cannot record a decision on a {subject_type} with status "
                      f"'{subject.status}' (must be '{required}')"},
            status=400,
        )
    return subject.ecosystem_id, None


@my_decisions_api_bp.get("/")
async def list_my_decisions(request: Request):
    """GET /api/v1/my-decisions -- the caller's decisions across their ecosystems.

    Query params: state, subject_type, ecosystem_id (must be one of theirs).
    Newest first.
    """
    member, err = require_auth(request)
    if err:
        return err

    user = getattr(request.ctx, "user", None)
    if user is None:
        return json({"error": "Authentication required"}, status=401)

    state = request.args.get("state")
    if state and state not in DECISION_STATES:
        return json({"error": f"state must be one of {', '.join(DECISION_STATES)}"}, status=400)
    subject_type = request.args.get("subject_type")
    if subject_type and subject_type not in SUBJECT_TYPES:
        return json({"error": f"subject_type must be one of {', '.join(SUBJECT_TYPES)}"}, status=400)
    subject_id_raw = request.args.get("subject_id")
    subject_id = None
    if subject_id_raw:
        try:
            subject_id = uuid.UUID(subject_id_raw)
        except ValueError:
            return json({"error": "subject_id must be a UUID"}, status=400)
    ecosystem_id_raw = request.args.get("ecosystem_id")
    ecosystem_id = None
    if ecosystem_id_raw:
        try:
            ecosystem_id = uuid.UUID(ecosystem_id_raw)
        except ValueError:
            return json({"error": "ecosystem_id must be a UUID"}, status=400)

    async with request.app.ctx.db() as session:
        members = await _caller_members(session, user.id)
        member_ids = [m.id for m in members]
        if ecosystem_id is not None and ecosystem_id not in {m.ecosystem_id for m in members}:
            return json({"error": "Not a member of that ecosystem"}, status=403)
        if not member_ids:
            return json({"items": []})

        stmt = (
            select(MemberDecision)
            .where(MemberDecision.member_id.in_(member_ids))
            .order_by(MemberDecision.created_at.desc())
        )
        if state:
            stmt = stmt.where(MemberDecision.state == state)
        if subject_type:
            stmt = stmt.where(MemberDecision.subject_type == subject_type)
        if subject_id is not None:
            stmt = stmt.where(MemberDecision.subject_id == subject_id)
        if ecosystem_id is not None:
            stmt = stmt.where(MemberDecision.ecosystem_id == ecosystem_id)

        decisions = list((await session.execute(stmt)).scalars().all())
        titles = await _resolve_subject_titles(session, decisions)

    return json({"items": [_to_dict(d, titles.get(d.subject_id)) for d in decisions]})


@my_decisions_api_bp.post("/")
async def create_my_decision(request: Request):
    """POST /api/v1/my-decisions -- record the caller's decision on a subject.

    Accepts JSON: {subject_type, subject_id, decision (3-500 chars), notes?}
    ecosystem_id/member_id resolve from the subject and the caller's Member
    row IN THE SUBJECT'S ECOSYSTEM. 409 if the caller already has a
    non-dropped decision on the same subject.
    """
    member, err = require_auth(request)
    if err:
        return err

    user = getattr(request.ctx, "user", None)
    if user is None:
        return json({"error": "Authentication required"}, status=401)

    body = request.json or {}
    subject_type = str(body.get("subject_type") or "").strip()
    if subject_type not in SUBJECT_TYPES:
        return json({"error": f"subject_type must be one of {', '.join(SUBJECT_TYPES)}"}, status=400)
    try:
        subject_id = uuid.UUID(str(body.get("subject_id") or ""))
    except ValueError:
        return json({"error": "subject_id must be a UUID"}, status=400)
    decision_text = str(body.get("decision") or "").strip()
    if not 3 <= len(decision_text) <= 500:
        return json({"error": "decision must be 3-500 characters"}, status=400)
    notes = body.get("notes")
    notes = str(notes).strip() if notes is not None else None

    async with request.app.ctx.db() as session:
        ecosystem_id, err_resp = await _validate_subject(session, subject_type, subject_id)
        if err_resp:
            return err_resp

        # The caller's Member row IN THE SUBJECT'S ECOSYSTEM — never limit(1)
        # across ecosystems.
        owner = await session.scalar(
            select(Member).where(
                Member.user_id == user.id,
                Member.ecosystem_id == ecosystem_id,
            )
        )
        if owner is None:
            return json({"error": "Not a member of that ecosystem"}, status=403)

        existing = await session.scalar(
            select(MemberDecision).where(
                MemberDecision.member_id == owner.id,
                MemberDecision.subject_type == subject_type,
                MemberDecision.subject_id == subject_id,
                MemberDecision.state != "dropped",
            )
        )
        if existing is not None:
            return json(
                {"error": "You already have a decision on this subject — edit the existing one",
                 "existing_decision_id": str(existing.id)},
                status=409,
            )

        decision = MemberDecision(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            member_id=owner.id,
            subject_type=subject_type,
            subject_id=subject_id,
            decision=decision_text,
            state="intended",
            notes=notes or None,
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        titles = await _resolve_subject_titles(session, [decision])
        return json(_to_dict(decision, titles.get(decision.subject_id)), status=201)


async def _get_own_decision(request: Request, decision_id: uuid.UUID):
    """Return (decision, None) if found AND owned by the caller, else
    (None, 404_response) — own-rows-only API, never leak existence."""
    user = getattr(request.ctx, "user", None)
    if user is None:
        return None, json({"error": "Authentication required"}, status=401)

    async with request.app.ctx.db() as session:
        decision = await session.get(MemberDecision, decision_id)
        if decision is None:
            return None, json({"error": "Decision not found"}, status=404)
        owner_user_id = await session.scalar(
            select(Member.user_id).where(Member.id == decision.member_id)
        )
        if owner_user_id != user.id:
            return None, json({"error": "Decision not found"}, status=404)
    # Detached-safe: only column attributes are used downstream.
    return decision, None


@my_decisions_api_bp.get("/<decision_id:uuid>")
async def get_my_decision(request: Request, decision_id: uuid.UUID):
    """GET /api/v1/my-decisions/:id -- one of the caller's own decisions."""
    member, err = require_auth(request)
    if err:
        return err

    decision, err_resp = await _get_own_decision(request, decision_id)
    if err_resp:
        return err_resp

    async with request.app.ctx.db() as session:
        titles = await _resolve_subject_titles(session, [decision])
    return json(_to_dict(decision, titles.get(decision.subject_id)))


@my_decisions_api_bp.put("/<decision_id:uuid>")
async def update_my_decision(request: Request, decision_id: uuid.UUID):
    """PUT /api/v1/my-decisions/:id -- edit the caller's own decision.

    Accepts JSON: {decision?, state?, notes?} — state must be one of the
    five values; decision 3-500 chars when present.
    """
    member, err = require_auth(request)
    if err:
        return err

    decision, err_resp = await _get_own_decision(request, decision_id)
    if err_resp:
        return err_resp

    body = request.json or {}
    new_text = body.get("decision")
    new_state = body.get("state")
    new_notes = body.get("notes", None)
    if new_text is None and new_state is None and "notes" not in body:
        return json({"error": "No fields supplied"}, status=400)
    if new_text is not None:
        new_text = str(new_text).strip()
        if not 3 <= len(new_text) <= 500:
            return json({"error": "decision must be 3-500 characters"}, status=400)
    if new_state is not None and new_state not in DECISION_STATES:
        return json({"error": f"state must be one of {', '.join(DECISION_STATES)}"}, status=400)

    async with request.app.ctx.db() as session:
        decision = await session.get(MemberDecision, decision_id)
        if new_text is not None:
            decision.decision = new_text
        if new_state is not None:
            decision.state = new_state
        if "notes" in body:
            decision.notes = str(new_notes).strip() if new_notes is not None else None
        await session.commit()
        await session.refresh(decision)

        titles = await _resolve_subject_titles(session, [decision])
        return json(_to_dict(decision, titles.get(decision.subject_id)))


@my_decisions_api_bp.delete("/<decision_id:uuid>")
async def delete_my_decision(request: Request, decision_id: uuid.UUID):
    """DELETE /api/v1/my-decisions/:id -- hard-delete the caller's own decision."""
    member, err = require_auth(request)
    if err:
        return err

    decision, err_resp = await _get_own_decision(request, decision_id)
    if err_resp:
        return err_resp

    async with request.app.ctx.db() as session:
        decision = await session.get(MemberDecision, decision_id)
        await session.delete(decision)
        await session.commit()

    return json({"deleted": True, "id": str(decision_id)})
