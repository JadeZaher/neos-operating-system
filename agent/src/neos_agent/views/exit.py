"""Exit process views for the NEOS dashboard (Layer X).

Blueprint: exit_bp, url_prefix="/dashboard/exit"

Handles voluntary exit initiation, commitment unwinding tracker,
portable record export, and exit process status management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import ExitRecord
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id, escape_like

logger = logging.getLogger(__name__)

exit_bp = Blueprint("exit", url_prefix="/dashboard/exit")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to an ExitRecord select statement."""
    if eco_ids:
        stmt = stmt.where(ExitRecord.ecosystem_id.in_(eco_ids))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(ExitRecord.status == status)

    exit_type = request.args.get("exit_type")
    if exit_type:
        stmt = stmt.where(ExitRecord.exit_type == exit_type)

    search = request.args.get("q")
    if search:
        pattern = f"%{escape_like(search)}%"
        stmt = stmt.where(ExitRecord.departure_notice.ilike(pattern))

    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@exit_bp.get("/")
async def list_exits(request: Request):
    """GET /dashboard/exit -- list exit processes."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(ExitRecord).order_by(ExitRecord.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            exits = result.scalars().all()
    except Exception:
        logger.exception("Failed to load exit list")
        exits = []
        total = 0

    content = await render(
        "dashboard/exit/list.html",
        request=request,
        exits=exits,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="exit",
    )
    return html(content)


@exit_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/exit/new -- exit initiation form."""
    content = await render(
        "dashboard/exit/form.html",
        request=request,
        exit_record=None,
        active_page="exit",
    )
    return html(content)


@exit_bp.post("/")
async def create_exit(request: Request):
    """POST /dashboard/exit -- initiate an exit process."""
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/exit/form.html",
            request=request,
            exit_record=None,
            active_page="exit",
            error="Invalid or unauthorised ecosystem.",
        )
        return html(content, status=403)
    try:
        exit_type = form.get("exit_type", "standard")
        now = datetime.utcnow()
        cooling_days = 30 if exit_type == "standard" else 7

        async with request.app.ctx.db() as session:
            record = ExitRecord(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                member_id=uuid.UUID(form.get("member_id")),
                exit_type=exit_type,
                status="declared",
                declared_date=now.date(),
                target_completion_date=(now + timedelta(days=cooling_days)).date(),
                commitment_inventory=[],
                unwinding_status={},
                departure_notice=form.get("reason", ""),
            )
            session.add(record)
            await session.commit()
            new_id = record.id
    except Exception:
        logger.exception("Failed to create exit record")
        content = await render(
            "dashboard/exit/form.html",
            request=request,
            exit_record=None,
            error="Failed to initiate exit process.",
            active_page="exit",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/exit/{new_id}")


@exit_bp.get("/<exit_uuid:uuid>")
async def detail(request: Request, exit_uuid: uuid.UUID):
    """GET /dashboard/exit/{id} -- exit process detail with unwinding tracker."""
    try:
        async with request.app.ctx.db() as session:
            record = await get_scoped_entity(session, ExitRecord, exit_uuid, request)
            if record is None:
                content = await render(
                    "dashboard/exit/detail.html",
                    request=request,
                    exit_record=None,
                    error="Exit record not found.",
                    active_page="exit",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load exit detail")
        content = await render(
            "dashboard/exit/detail.html",
            request=request,
            exit_record=None,
            error="Failed to load exit record.",
            active_page="exit",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/exit/detail.html",
        request=request,
        exit_record=record,
        active_page="exit",
    )
    return html(content)


@exit_bp.post("/<exit_uuid:uuid>/status")
async def status_transition(request: Request, exit_uuid: uuid.UUID):
    """POST /dashboard/exit/{id}/status -- transition exit status."""
    form = request.form
    new_status = form.get("new_status")

    if not new_status:
        return html(
            await render(
                "dashboard/exit/detail.html",
                request=request,
                exit_record=None,
                error="new_status is required.",
                active_page="exit",
            ),
            status=400,
        )

    try:
        async with request.app.ctx.db() as session:
            record = await get_scoped_entity(session, ExitRecord, exit_uuid, request)
            if record is None:
                return html(
                    await render(
                        "dashboard/exit/detail.html",
                        request=request,
                        exit_record=None,
                        error="Exit record not found.",
                        active_page="exit",
                    ),
                    status=404,
                )

            old_status = record.status
            record.status = new_status

            if new_status == "completed":
                record.completed_date = datetime.utcnow().date()

            await session.commit()
            logger.info(
                "Exit %s status: %s -> %s",
                exit_uuid, old_status, new_status,
            )
    except Exception:
        logger.exception("Failed to transition exit status")
        return html(
            await render(
                "dashboard/exit/detail.html",
                request=request,
                exit_record=None,
                error="Failed to update status.",
                active_page="exit",
            ),
            status=500,
        )

    return redirect(f"/dashboard/exit/{exit_uuid}")


@exit_bp.get("/filter")
async def filter_exits(request: Request):
    """GET /dashboard/exit/filter -- htmx filtered exit list fragment."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(ExitRecord).order_by(ExitRecord.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            exits = result.scalars().all()
    except Exception:
        logger.exception("Failed to filter exits")
        exits = []
        total = 0

    fragment = await render(
        "dashboard/exit/_list_rows.html",
        request=request,
        exits=exits,
        total=total,
        offset=offset,
        limit=limit,
    )
    return html(fragment)
