"""JSON API blueprint for decision record management.

Blueprint: decisions_api_bp, url_prefix="/api/v1/decisions"

Provides read-only access to the governance decision log including
dissent records, semantic tags, and participant information.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    DecisionDissentRecord,
    DecisionParticipant,
    DecisionRecord,
    DecisionSemanticTag,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class DissentRecordSchema(BaseModel):
    id: uuid.UUID
    objector: str
    objection: str | None = None
    resolution: str | None = None
    notes: str | None = None


class ParticipantSchema(BaseModel):
    id: uuid.UUID
    name: str
    role: str | None = None
    position: str | None = None


class SemanticTagSchema(BaseModel):
    id: uuid.UUID
    topic: dict | None = None
    affected_parties: dict | None = None
    ecosystem_scope: str | None = None
    urgency_at_time: str | None = None
    related_precedents: dict | None = None


class DecisionListItem(BaseModel):
    id: uuid.UUID
    record_id: str
    date: date | None = None
    holding: str | None = None
    source_skill: str | None = None
    source_layer: int | None = None
    domain: str | None = None
    precedent_level: str | None = None
    status: str
    created_at: datetime


class DecisionDetail(DecisionListItem):
    ecosystem_id: uuid.UUID
    ratio_decidendi: str | None = None
    obiter_dicta: str | None = None
    deliberation_summary: str | None = None
    artifact_type: str | None = None
    artifact_reference: str | None = None
    overruled_by: str | None = None
    superseded_by: str | None = None
    related_records: dict | None = None
    review_date: date | None = None
    recorder: str | None = None
    recorder_role: str | None = None
    verification_by: str | None = None
    verification_date: date | None = None
    updated_at: datetime
    dissent_records: list[DissentRecordSchema] = []
    participants: list[ParticipantSchema] = []
    semantic_tags: list[SemanticTagSchema] = []


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

decisions_api_bp = Blueprint("decisions_api", url_prefix="/api/v1/decisions")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_auth(request: Request):
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json_module.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json_module.JSONDecodeError, ValueError):
            pass
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _decision_to_list_item(d: DecisionRecord) -> dict:
    return DecisionListItem(
        id=d.id,
        record_id=d.record_id,
        date=d.date,
        holding=d.holding,
        source_skill=d.source_skill,
        source_layer=d.source_layer,
        domain=d.domain,
        precedent_level=d.precedent_level,
        status=d.status,
        created_at=d.created_at,
    ).model_dump(mode="json")


def _decision_to_detail(d: DecisionRecord) -> dict:
    return DecisionDetail(
        id=d.id,
        record_id=d.record_id,
        date=d.date,
        holding=d.holding,
        source_skill=d.source_skill,
        source_layer=d.source_layer,
        domain=d.domain,
        precedent_level=d.precedent_level,
        status=d.status,
        created_at=d.created_at,
        ecosystem_id=d.ecosystem_id,
        ratio_decidendi=d.ratio_decidendi,
        obiter_dicta=d.obiter_dicta,
        deliberation_summary=d.deliberation_summary,
        artifact_type=d.artifact_type,
        artifact_reference=d.artifact_reference,
        overruled_by=d.overruled_by,
        superseded_by=d.superseded_by,
        related_records=d.related_records,
        review_date=d.review_date,
        recorder=d.recorder,
        recorder_role=d.recorder_role,
        verification_by=d.verification_by,
        verification_date=d.verification_date,
        updated_at=d.updated_at,
        dissent_records=[
            DissentRecordSchema(
                id=dr.id,
                objector=dr.objector,
                objection=dr.objection,
                resolution=dr.resolution,
                notes=dr.notes,
            )
            for dr in (d.dissent_records or [])
        ],
        participants=[
            ParticipantSchema(
                id=p.id,
                name=p.name,
                role=p.role,
                position=p.position,
            )
            for p in (d.participants or [])
        ],
        semantic_tags=[
            SemanticTagSchema(
                id=t.id,
                topic=t.topic,
                affected_parties=t.affected_parties,
                ecosystem_scope=t.ecosystem_scope,
                urgency_at_time=t.urgency_at_time,
                related_precedents=t.related_precedents,
            )
            for t in (d.semantic_tags or [])
        ],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@decisions_api_bp.get("/")
async def list_decisions(request: Request):
    """GET /api/v1/decisions -- Paginated decision list with filtering.

    Query params: status, domain, source_layer,
    q (search record_id/holding),
    page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(DecisionRecord).order_by(DecisionRecord.created_at.desc())

        if eco_ids:
            stmt = stmt.where(DecisionRecord.ecosystem_id.in_(eco_ids))

        status = request.args.get("status")
        if status:
            stmt = stmt.where(DecisionRecord.status == status)

        domain = request.args.get("domain")
        if domain:
            pattern = f"%{_escape_like(domain)}%"
            stmt = stmt.where(DecisionRecord.domain.ilike(pattern))

        source_layer = request.args.get("source_layer")
        if source_layer:
            try:
                stmt = stmt.where(DecisionRecord.source_layer == int(source_layer))
            except ValueError:
                pass

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    DecisionRecord.record_id.ilike(pattern),
                    DecisionRecord.holding.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        decisions = result.scalars().all()

    return json({
        "items": [_decision_to_list_item(d) for d in decisions],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@decisions_api_bp.get("/<decision_id:uuid>")
async def get_decision(request: Request, decision_id: uuid.UUID):
    """GET /api/v1/decisions/:id -- Decision detail with relationships.

    Eager-loads dissent_records, participants, semantic_tags.
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(DecisionRecord)
            .options(
                selectinload(DecisionRecord.dissent_records),
                selectinload(DecisionRecord.participants),
                selectinload(DecisionRecord.semantic_tags),
            )
            .where(DecisionRecord.id == decision_id)
        )
        if eco_ids:
            stmt = stmt.where(DecisionRecord.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        d = result.scalar_one_or_none()

    if d is None:
        return json({"error": "Decision record not found"}, status=404)

    return json(_decision_to_detail(d))
