"""JSON API blueprint for agreement management.

Blueprint: agreements_api_bp, url_prefix="/api/v1/agreements"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Agreement,
    AgreementRatificationRecord,
    AgreementVersion,
    AmendmentRecord,
    ReviewRecord,
)

from .helpers import require_auth, get_ecosystem_ids, apply_ecosystem_filter, serialize_shared_ecosystem_ids
from neos_agent.services.fingerprint import generate_fingerprint
from .schemas import (
    AgreementCreateRequest,
    AgreementDetail,
    AgreementHistoryResponse,
    AgreementListItem,
    AgreementUpdateRequest,
    AgreementVersionSchema,
    AmendmentRecordSchema,
    RatificationRecordSchema,
    ReviewRecordSchema,
)

logger = logging.getLogger(__name__)

agreements_api_bp = Blueprint("agreements_api", url_prefix="/api/v1/agreements")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters."""
    return re.sub(r"([%_\\])", r"\\\1", value)


def _apply_filters(stmt, request: Request, eco_ids: list[uuid.UUID] | None = None):
    """Apply optional query-param filters to an Agreement select statement."""
    if eco_ids:
        stmt = apply_ecosystem_filter(stmt, Agreement, eco_ids)

    agreement_type = request.args.get("type")
    if agreement_type:
        stmt = stmt.where(Agreement.type == agreement_type)

    status = request.args.get("status")
    if status:
        stmt = stmt.where(Agreement.status == status)

    domain = request.args.get("domain")
    if domain:
        stmt = stmt.where(Agreement.domain.ilike(f"%{_escape_like(domain)}%"))

    search = request.args.get("q")
    if search:
        pattern = f"%{_escape_like(search)}%"
        stmt = stmt.where(
            or_(
                Agreement.title.ilike(pattern),
                Agreement.agreement_id.ilike(pattern),
            )
        )

    return stmt


def _agreement_to_list_item(a: Agreement) -> dict:
    """Convert an Agreement ORM instance to a serialisable dict."""
    return AgreementListItem(
        id=a.id,
        agreement_id=a.agreement_id,
        ecosystem_id=a.ecosystem_id,
        type=a.type,
        title=a.title,
        version=a.version,
        status=a.status,
        proposer=a.proposer,
        domain=a.domain,
        hierarchy_level=a.hierarchy_level,
        review_date=a.review_date,
        sunset_date=a.sunset_date,
        created_at=a.created_at,
    ).model_dump(mode="json")


def _agreement_to_detail(a: Agreement) -> dict:
    """Convert an Agreement ORM instance (with ratification_records loaded)
    to a serialisable AgreementDetail dict."""
    ratifications = [
        RatificationRecordSchema(
            id=r.id,
            participant=r.participant,
            role=r.role,
            position=r.position,
            date=r.date,
        )
        for r in (a.ratification_records or [])
    ]
    data = AgreementDetail(
        id=a.id,
        agreement_id=a.agreement_id,
        type=a.type,
        title=a.title,
        version=a.version,
        status=a.status,
        proposer=a.proposer,
        domain=a.domain,
        hierarchy_level=a.hierarchy_level,
        review_date=a.review_date,
        sunset_date=a.sunset_date,
        created_at=a.created_at,
        ecosystem_id=a.ecosystem_id,
        text=a.text,
        affected_parties=a.affected_parties,
        parent_agreement_id=a.parent_agreement_id,
        ratification_date=a.ratification_date,
        created_date=a.created_date,
        updated_at=a.updated_at,
        ratification_records=[r.model_dump(mode="json") for r in ratifications],
    ).model_dump(mode="json")
    data["version_fingerprint"] = a.version_fingerprint
    return data


def _bump_version(agreement: Agreement) -> None:
    """Increment the minor version number (e.g. 1.0 -> 1.1)."""
    parts = agreement.version.split(".")
    if len(parts) == 2:
        major, minor = parts
        agreement.version = f"{major}.{int(minor) + 1}"
    else:
        agreement.version = agreement.version + ".1"


def _snapshot_agreement(agreement: Agreement, change_reason: str | None = None, changed_by: str | None = None) -> AgreementVersion:
    """Create an immutable snapshot of the current agreement state."""
    return AgreementVersion(
        id=uuid.uuid4(),
        agreement_id=agreement.id,
        version=agreement.version,
        status=agreement.status,
        title=agreement.title,
        text=agreement.text,
        type=agreement.type,
        proposer=agreement.proposer,
        domain=agreement.domain,
        hierarchy_level=agreement.hierarchy_level,
        affected_parties=agreement.affected_parties,
        review_date=agreement.review_date,
        sunset_date=agreement.sunset_date,
        ratification_date=agreement.ratification_date,
        version_fingerprint=agreement.version_fingerprint,
        change_reason=change_reason,
        changed_by=changed_by,
    )


# Valid status transitions: current -> allowed targets (ACT lifecycle)
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"advice"},
    "advice": {"consent"},
    "consent": {"test", "active"},
    "test": {"active"},
    "active": {"under_review"},
    "under_review": {"sunset", "active"},
    "sunset": {"archived"},
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@agreements_api_bp.get("/")
async def list_agreements(request: Request):
    """GET /api/v1/agreements -- paginated list with filters.

    Query params: type, status, domain, q, page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as db:
        stmt = select(Agreement).order_by(Agreement.created_at.desc())
        stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await db.execute(stmt)
        agreements = result.scalars().all()

    return json({
        "items": [_agreement_to_list_item(a) for a in agreements],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@agreements_api_bp.get("/<agreement_id:uuid>")
async def get_agreement(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id -- detail with ratification records.

    Verifies ecosystem ownership.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

    return json(_agreement_to_detail(agreement))


@agreements_api_bp.post("/")
async def create_agreement(request: Request):
    """POST /api/v1/agreements -- create a new agreement.

    Accepts JSON: AgreementCreateRequest
    Returns JSON: AgreementDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = AgreementCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Verify the ecosystem_id is in the member's scope
    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    agreement_id_str = f"AGR-{short_id}"

    async with request.app.ctx.db() as db:
        agreement = Agreement(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            agreement_id=agreement_id_str,
            type=create_req.type,
            title=create_req.title,
            version="1.0",
            status="draft",
            proposer=create_req.proposer,
            domain=create_req.domain,
            text=create_req.text,
            hierarchy_level=create_req.hierarchy_level,
            affected_parties=create_req.affected_parties,
            review_date=create_req.review_date,
            sunset_date=create_req.sunset_date,
            created_date=_dt.date.today(),
        )
        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )
        db.add(agreement)
        await db.commit()

        # Reload with ratification records for response
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

    return json(_agreement_to_detail(agreement), status=201)


@agreements_api_bp.put("/<agreement_id:uuid>")
async def update_agreement(request: Request, agreement_id: uuid.UUID):
    """PUT /api/v1/agreements/:id -- update an agreement.

    Accepts JSON: AgreementUpdateRequest (only non-None fields are applied).
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = AgreementUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        # Save snapshot of current state before applying changes
        change_reason = body.get("change_reason", "Manual edit")
        snapshot = _snapshot_agreement(agreement, change_reason=change_reason, changed_by=body.get("changed_by"))
        db.add(snapshot)

        update_data = update_req.model_dump(exclude_none=True)
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        for field, value in update_data.items():
            setattr(agreement, field, value)

        # Bump version
        _bump_version(agreement)

        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )

        await db.commit()
        await db.refresh(agreement)

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

    return json(_agreement_to_detail(agreement))


@agreements_api_bp.post("/<agreement_id:uuid>/status")
async def status_transition(request: Request, agreement_id: uuid.UUID):
    """POST /api/v1/agreements/:id/status -- transition agreement status.

    Accepts JSON: {"status": "ratified"}
    Valid transitions: draft->ratified, ratified->archived, archived->draft.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    new_status = body.get("status")
    if not new_status:
        return json({"error": "\"status\" field is required"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        allowed = _VALID_TRANSITIONS.get(agreement.status, set())
        if new_status not in allowed:
            return json(
                {"error": f"Invalid transition: {agreement.status} -> {new_status}"},
                status=400,
            )

        # Snapshot before status change
        snapshot = _snapshot_agreement(
            agreement,
            change_reason=f"Status transition: {agreement.status} -> {new_status}",
            changed_by=body.get("changed_by"),
        )
        db.add(snapshot)

        old_status = agreement.status
        agreement.status = new_status

        if new_status == "ratified" and agreement.ratification_date is None:
            agreement.ratification_date = _dt.date.today()

        await db.commit()
        await db.refresh(agreement)

        logger.info(
            "Agreement %s status: %s -> %s",
            agreement_id, old_status, new_status,
        )

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

    return json(_agreement_to_detail(agreement))


@agreements_api_bp.get("/<agreement_id:uuid>/history")
async def get_history(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id/history -- amendment and review history.

    Returns JSON: AgreementHistoryResponse
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        # Verify agreement exists and is in scope
        agr_stmt = select(Agreement.id).where(Agreement.id == agreement_id)
        if eco_ids:
            agr_stmt = agr_stmt.where(Agreement.ecosystem_id.in_(eco_ids))
        exists = await db.scalar(agr_stmt)
        if exists is None:
            return json({"error": "Agreement not found"}, status=404)

        # Load amendments
        amend_result = await db.execute(
            select(AmendmentRecord)
            .where(AmendmentRecord.parent_agreement_id == agreement_id)
            .order_by(AmendmentRecord.date.desc())
        )
        amendments = amend_result.scalars().all()

        # Load reviews
        review_result = await db.execute(
            select(ReviewRecord)
            .where(ReviewRecord.agreement_id == agreement_id)
            .order_by(ReviewRecord.date.desc())
        )
        reviews = review_result.scalars().all()

        # Load versions
        version_result = await db.execute(
            select(AgreementVersion)
            .where(AgreementVersion.agreement_id == agreement_id)
            .order_by(AgreementVersion.created_at.desc())
        )
        versions = version_result.scalars().all()

    response = AgreementHistoryResponse(
        amendments=[
            AmendmentRecordSchema(
                id=a.id,
                amendment_id=a.amendment_id,
                amendment_type=a.amendment_type,
                proposed_by=a.proposed_by,
                date=a.date,
                changes=a.changes,
                rationale=a.rationale,
                status=a.status,
                new_agreement_version=a.new_agreement_version,
                created_at=a.created_at,
            )
            for a in amendments
        ],
        reviews=[
            ReviewRecordSchema(
                id=r.id,
                review_id=r.review_id,
                review_type=r.review_type,
                trigger=r.trigger,
                date=r.date,
                outcome=r.outcome,
                next_review_date=r.next_review_date,
                created_at=r.created_at,
            )
            for r in reviews
        ],
        versions=[
            AgreementVersionSchema(
                id=v.id,
                agreement_id=v.agreement_id,
                version=v.version,
                status=v.status,
                title=v.title,
                text=v.text,
                type=v.type,
                proposer=v.proposer,
                domain=v.domain,
                hierarchy_level=v.hierarchy_level,
                affected_parties=v.affected_parties,
                review_date=v.review_date,
                sunset_date=v.sunset_date,
                ratification_date=v.ratification_date,
                version_fingerprint=v.version_fingerprint,
                change_reason=v.change_reason,
                changed_by=v.changed_by,
                created_at=v.created_at,
            )
            for v in versions
        ],
    )

    return json(response.model_dump(mode="json"))


@agreements_api_bp.post("/<agreement_id:uuid>/rollback/<version_id:uuid>")
async def rollback_agreement(request: Request, agreement_id: uuid.UUID, version_id: uuid.UUID):
    """POST /api/v1/agreements/:id/rollback/:version_id -- restore agreement to a previous version.

    Creates a snapshot of the current state, then restores from the specified version.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        # Load current agreement
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        # Load the target version
        ver_result = await db.execute(
            select(AgreementVersion).where(
                AgreementVersion.id == version_id,
                AgreementVersion.agreement_id == agreement_id,
            )
        )
        target_version = ver_result.scalar_one_or_none()

        if target_version is None:
            return json({"error": "Version not found"}, status=404)

        # Snapshot current state before rollback
        snapshot = _snapshot_agreement(
            agreement,
            change_reason=f"Rollback to version {target_version.version}",
            changed_by=(request.json or {}).get("changed_by"),
        )
        db.add(snapshot)

        # Restore fields from target version
        agreement.version = target_version.version
        agreement.status = target_version.status
        agreement.title = target_version.title
        agreement.text = target_version.text
        agreement.type = target_version.type
        agreement.proposer = target_version.proposer
        agreement.domain = target_version.domain
        agreement.hierarchy_level = target_version.hierarchy_level
        agreement.affected_parties = target_version.affected_parties
        agreement.review_date = target_version.review_date
        agreement.sunset_date = target_version.sunset_date
        agreement.ratification_date = target_version.ratification_date
        agreement.version_fingerprint = target_version.version_fingerprint

        await db.commit()
        await db.refresh(agreement)

        logger.info("Agreement %s rolled back to version %s", agreement_id, target_version.version)

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

    return json(_agreement_to_detail(agreement))
