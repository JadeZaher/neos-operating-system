"""JSON API blueprint for the Discover feed, shares and needs, and collaborations.

Blueprint: discover_api_bp, url_prefix="/api/v1/discover"

The feed aggregates public quizzes and ecosystems. Shares, needs and collaborations are thin wrappers over
`services/exchange.py` (one visibility rule, one status table, respond, approve/end); see api/AGENTS.md
"Exchange (G-Exchange)".
"""

from __future__ import annotations

import logging
import re
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import case, false, func, select

from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import (
    Collaboration,
    Domain,
    Ecosystem,
    Member,
    SharesNeeds,
)
from neos_agent.api.errors import ApiError
from neos_agent.api.guards import authenticated, caller_user_id
from neos_agent.api.helpers import parse_pagination
from neos_agent.services import exchange
from neos_agent.services.member_lifecycle import counts_as_member

logger = logging.getLogger(__name__)

discover_api_bp = Blueprint("discover_api", url_prefix="/api/v1/discover")


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _shares_needs_stats(stats) -> dict:
    return {
        "total": stats.total or 0,
        "shares": stats.shares or 0,
        "needs": stats.needs or 0,
        "solutions": stats.solutions or 0,
        "active": stats.active or 0,
        "fulfilled": stats.fulfilled or 0,
        "withdrawn": stats.withdrawn or 0,
    }


# --- Endpoints ---


@discover_api_bp.get("/")
@authenticated
async def discover_feed(request: Request):
    """GET /api/v1/discover -- Discover quizzes and ecosystems.

    Query params:
        q        – search term (matches quiz title / ecosystem name+description)
        tab      – "all" (default), "quizzes", "ecosystems"
        mode     – quiz mode filter (standard, assessment, …)
        tag      – ecosystem tag filter
        page     – pagination page (default 1)
        per_page – items per section (default 12, max 50)
    """
    search = request.args.get("q", "").strip()
    tab = request.args.get("tab", "all")
    mode_filter = request.args.get("mode")
    tag_filter = request.args.get("tag")
    page_request = parse_pagination(request, default=12, cap=50)
    page, per_page, offset = page_request.page, page_request.per_page, page_request.offset

    result: dict = {}

    async with request.app.ctx.db() as session:
        # ---- Quizzes section ----
        if tab in ("all", "quizzes"):
            try:
                q_filters = [
                    Quiz.is_published.is_(True),
                    Quiz.visibility == "public",
                ]
                if search:
                    pattern = f"%{_escape_like(search)}%"
                    q_filters.append(Quiz.title.ilike(pattern))
                if mode_filter:
                    q_filters.append(Quiz.mode == mode_filter)

                # total
                total_q = await session.execute(
                    select(func.count(Quiz.id)).where(*q_filters)
                )
                quiz_total = total_q.scalar() or 0

                # items
                stmt = (
                    select(Quiz)
                    .where(*q_filters)
                    .order_by(Quiz.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                )
                rows = (await session.execute(stmt)).scalars().all()

                # Gather completion counts per quiz for social proof
                quiz_ids = [q.id for q in rows]
                completions_map: dict[uuid.UUID, int] = {}
                if quiz_ids:
                    comp_rows = await session.execute(
                        select(
                            QuizResult.quiz_id,
                            func.count(QuizResult.id).label("cnt"),
                        )
                        .where(QuizResult.quiz_id.in_(quiz_ids))
                        .group_by(QuizResult.quiz_id)
                    )
                    for row in comp_rows:
                        completions_map[row.quiz_id] = row.cnt

                # Course name lookup
                course_ids = list({q.course_id for q in rows if q.course_id})
                course_names: dict[uuid.UUID, str] = {}
                if course_ids:
                    c_rows = await session.execute(
                        select(Course.id, Course.title).where(Course.id.in_(course_ids))
                    )
                    for r in c_rows:
                        course_names[r.id] = r.title

                quizzes = []
                for q in rows:
                    quizzes.append({
                        "id": str(q.id),
                        "title": q.title,
                        "description": q.description,
                        "mode": q.mode,
                        "time_limit": q.time_limit,
                        "passing_score": q.passing_score,
                        "allow_retakes": q.allow_retakes,
                        "completions": completions_map.get(q.id, 0),
                        "course_name": course_names.get(q.course_id) if q.course_id else None,
                        "created_at": q.created_at.isoformat() if q.created_at else None,
                    })

                result["quizzes"] = {
                    "items": quizzes,
                    "total": quiz_total,
                    "page": page,
                    "per_page": per_page,
                }
            except Exception:
                logger.exception("Failed to load quizzes section in discover feed")
                result["quizzes"] = {"items": [], "total": 0, "page": page, "per_page": per_page}

        # ---- Ecosystems section ----
        if tab in ("all", "ecosystems"):
            e_filters = [Ecosystem.visibility == "public"]
            if search:
                pattern = f"%{_escape_like(search)}%"
                e_filters.append(
                    Ecosystem.name.ilike(pattern)
                    | Ecosystem.description.ilike(pattern)
                )
            if tag_filter:
                # tags is a JSON array; use a cast to TEXT + LIKE for portability
                from sqlalchemy import Text as SAText
                e_filters.append(
                    func.cast(Ecosystem.tags, SAText()).ilike(
                        f'%"{_escape_like(tag_filter)}"%'
                    )
                )

            total_e = await session.execute(
                select(func.count(Ecosystem.id)).where(*e_filters)
            )
            eco_total = total_e.scalar() or 0

            stmt = (
                select(Ecosystem)
                .where(*e_filters)
                .order_by(Ecosystem.name.asc())
                .offset(offset)
                .limit(per_page)
            )
            eco_rows = (await session.execute(stmt)).scalars().all()

            # Member counts
            eco_ids = [e.id for e in eco_rows]
            member_counts: dict[uuid.UUID, int] = {}
            if eco_ids:
                mc_rows = await session.execute(
                    select(
                        Member.ecosystem_id,
                        func.count(Member.id).label("cnt"),
                    )
                    .where(Member.ecosystem_id.in_(eco_ids), counts_as_member())
                    .group_by(Member.ecosystem_id)
                )
                for r in mc_rows:
                    member_counts[r.ecosystem_id] = r.cnt

            ecosystems = []
            for e in eco_rows:
                ecosystems.append({
                    "id": str(e.id),
                    "name": e.name,
                    "description": e.description,
                    "status": e.status,
                    "logo_url": e.logo_url,
                    "location": e.location,
                    "tags": e.tags if isinstance(e.tags, list) else [],
                    "member_count": member_counts.get(e.id, 0),
                    "founded_date": e.founded_date.isoformat() if e.founded_date else None,
                    "website": e.website,
                })

            result["ecosystems"] = {
                "items": ecosystems,
                "total": eco_total,
                "page": page,
                "per_page": per_page,
            }

    return json(result)



# ---------------------------------------------------------------------------
# Shares / Needs (G-Exchange): rules live in services/exchange.py
# ---------------------------------------------------------------------------


async def _viewer(session, request: Request) -> exchange.Viewer:
    return await exchange.load_viewer(session, caller_user_id(request))


def _post_id(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise ApiError(400, "Invalid ID") from None


def _body(request: Request) -> dict:
    body = request.json if request.body else {}
    if not isinstance(body, dict):
        raise ApiError(400, "JSON object required")
    return body


def _publication_filters(request: Request, *, default_status: str | None) -> list:
    """q, type, category, ecosystem_id, domain_id and status (`all` = every status the caller may see)."""
    filters = []
    search = request.args.get("q", "").strip()
    if search:
        pattern = f"%{_escape_like(search)}%"
        filters.append(SharesNeeds.title.ilike(pattern) | SharesNeeds.description.ilike(pattern))
    if request.args.get("type"):
        filters.append(SharesNeeds.type == request.args.get("type"))
    if request.args.get("category"):
        filters.append(SharesNeeds.category == request.args.get("category"))
    for name, column in (("ecosystem_id", SharesNeeds.ecosystem_id), ("domain_id", SharesNeeds.domain_id)):
        raw = request.args.get(name)
        if raw:
            try:
                filters.append(column == uuid.UUID(raw))
            except ValueError:
                raise ApiError(400, f"Invalid {name}") from None
    status = request.args.get("status") or default_status
    if status and status != "all":
        if status not in exchange.PUBLICATION_STATUSES:
            raise ApiError(400, "Unknown status", {"allowed": [*exchange.PUBLICATION_STATUSES, "all"]})
        filters.append(SharesNeeds.status == status)
    return filters


async def _page_of_posts(session, stmt, request: Request, viewer, *, default: int, cap: int) -> dict:
    page = parse_pagination(request, default=default, cap=cap)
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar() or 0
    rows = (await session.execute(
        stmt.order_by(SharesNeeds.created_at.desc(), SharesNeeds.id).offset(page.offset).limit(page.per_page)
    )).scalars().all()
    return {"items": await exchange.publication_payloads(session, rows, viewer), "total": total,
            "page": page.page, "per_page": page.per_page}


@discover_api_bp.get("/shares-needs")
@authenticated
async def list_shares_needs(request: Request):
    """GET /api/v1/discover/shares-needs -- what the caller may see across ecosystems (active by default, never hidden)."""
    filters = _publication_filters(request, default_status=exchange.OPEN)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        stmt = select(SharesNeeds).where(exchange.visible_clause(viewer), SharesNeeds.hidden_at.is_(None), *filters)
        return json(await _page_of_posts(session, stmt, request, viewer, default=20, cap=50))


@discover_api_bp.get("/shares-needs/admin")
@authenticated
async def admin_list_shares_needs(request: Request):
    """GET /api/v1/discover/shares-needs/admin -- the caller's moderation list: posts in ecosystems they steward."""
    filters = _publication_filters(request, default_status=None)
    hidden = request.args.get("hidden")
    if hidden in ("true", "false"):
        filters.append(SharesNeeds.hidden_at.isnot(None) if hidden == "true" else SharesNeeds.hidden_at.is_(None))
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        moderated = sorted(viewer.steward_ecosystems, key=str)
        scope = SharesNeeds.ecosystem_id.in_(moderated) if moderated else false()
        result = await _page_of_posts(session, select(SharesNeeds).where(scope, *filters), request, viewer,
                                      default=50, cap=100)
        stats = (await session.execute(select(
            func.count(SharesNeeds.id).label("total"),
            func.sum(case((SharesNeeds.type == "share", 1), else_=0)).label("shares"),
            func.sum(case((SharesNeeds.type == "need", 1), else_=0)).label("needs"),
            func.sum(case((SharesNeeds.type == "solution", 1), else_=0)).label("solutions"),
            func.sum(case((SharesNeeds.status == "active", 1), else_=0)).label("active"),
            func.sum(case((SharesNeeds.status == "fulfilled", 1), else_=0)).label("fulfilled"),
            func.sum(case((SharesNeeds.status == "withdrawn", 1), else_=0)).label("withdrawn"),
            func.sum(case((SharesNeeds.hidden_at.isnot(None), 1), else_=0)).label("hidden"),
        ).where(scope))).first()
        names = dict((await session.execute(
            select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(moderated)))).all()) if moderated else {}
    return json({**result, "stats": {**_shares_needs_stats(stats), "hidden": stats.hidden or 0},
                 "moderated_ecosystems": [{"id": str(eco), "name": names.get(eco)} for eco in moderated]})


@discover_api_bp.get("/shares-needs/<sn_id:str>")
@authenticated
async def get_share_need(request: Request, sn_id: str):
    """GET /api/v1/discover/shares-needs/<id> -- one post under the visibility rule (404 outside it)."""
    post_id = _post_id(sn_id)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.load_visible(session, viewer, post_id)
        return json(await exchange.publication_payload(session, record, viewer))


async def _write_post(request: Request, sn_id: str, write, *, status: int = 200):
    """Load the post FOR UPDATE under the visibility rule, run `write(session, viewer, record)`, commit, respond."""
    post_id = _post_id(sn_id)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.load_visible(session, viewer, post_id, for_update=True)
        await write(session, viewer, record)
        await session.commit()
        await session.refresh(record)
        return json(await exchange.publication_payload(session, record, viewer), status=status)


@discover_api_bp.put("/shares-needs/<sn_id:str>")
@authenticated
async def update_share_need(request: Request, sn_id: str):
    """PUT /api/v1/discover/shares-needs/<id> -- the author edits; a post never moves ecosystem or domain."""
    body = _body(request)
    return await _write_post(request, sn_id, lambda s, v, r: exchange.update_publication(s, v, r, body))


@discover_api_bp.post("/shares-needs/<sn_id:str>/status")
@authenticated
async def update_share_need_status(request: Request, sn_id: str):
    """POST /api/v1/discover/shares-needs/<id>/status {status, note?, fulfilled_by_member_id?} -- the author's moves."""
    body = _body(request)
    return await _write_post(request, sn_id, lambda s, v, r: exchange.move_publication(
        s, v, r, body.get("status"), note=body.get("note"), fulfilled_by=body.get("fulfilled_by_member_id")))


@discover_api_bp.post("/shares-needs/<sn_id:str>/hide")
@authenticated
async def hide_share_need(request: Request, sn_id: str):
    """POST /api/v1/discover/shares-needs/<id>/hide {reason} -- a steward of its ecosystem hides it, recorded."""
    body = _body(request)
    return await _write_post(request, sn_id, lambda s, v, r: exchange.hide_publication(s, v, r, body.get("reason")))


@discover_api_bp.post("/shares-needs/<sn_id:str>/restore")
@authenticated
async def restore_share_need(request: Request, sn_id: str):
    """POST /api/v1/discover/shares-needs/<id>/restore -- a steward of its ecosystem shows it again."""
    return await _write_post(request, sn_id, exchange.restore_publication)


@discover_api_bp.delete("/shares-needs/<sn_id:str>")
@authenticated
async def delete_share_need(request: Request, sn_id: str):
    """DELETE /api/v1/discover/shares-needs/<id> -- only the author, and only while nobody has answered."""
    post_id = _post_id(sn_id)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.load_visible(session, viewer, post_id, for_update=True)
        await exchange.delete_publication(session, viewer, record)
        await session.commit()
    return json({"ok": True, "message": "Share/Need deleted"})


@discover_api_bp.post("/shares-needs/<sn_id:str>/respond")
@authenticated
async def respond_to_share_need(request: Request, sn_id: str):
    """POST /api/v1/discover/shares-needs/<id>/respond {message} -- a direct conversation with the poster, tagged."""
    post_id = _post_id(sn_id)
    message = _body(request).get("message")
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.load_visible(session, viewer, post_id, for_update=True)
        conversation_id, created = await exchange.respond(session, viewer, record, message,
                                                          preferred_row=getattr(request.ctx, "member", None))
        await session.commit()
        post = await exchange.publication_payload(session, record, viewer)
    return json({"conversation_id": str(conversation_id), "created": created, "post": post},
                status=201 if created else 200)


@discover_api_bp.post("/shares-needs")
@authenticated
async def create_share_need(request: Request):
    """POST /api/v1/discover/shares-needs -- publish as the caller's row in that ecosystem (gates, validation, duplicates)."""
    body = _body(request)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.publish(session, viewer, body)
        await session.commit()
        await session.refresh(record)
        return json(await exchange.publication_payload(session, record, viewer), status=201)


# ---------------------------------------------------------------------------
# Collaborations (G-Exchange)
# ---------------------------------------------------------------------------


@discover_api_bp.get("/collaborations")
@authenticated
async def list_collaborations(request: Request):
    page = parse_pagination(request, default=20, cap=50)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        result = await exchange.search_collaborations(session, viewer, query=request.args.get("q", ""),
            status=request.args.get("status") or "active", tier=request.args.get("engagement_tier"),
            page=page.page, limit=page.per_page)
        return json(result)


@discover_api_bp.get("/collaborations/<collaboration_id:uuid>")
@authenticated
async def get_collaboration(request: Request, collaboration_id: uuid.UUID):
    """Detail with approvals, the awaited side and the caller's buttons (proposed ones: either side only)."""
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record, sides = await exchange.load_collaboration(session, viewer, collaboration_id)
        return json(await exchange.collaboration_payload(session, viewer, record, sides))


@discover_api_bp.post("/collaborations")
@authenticated
async def propose_collaboration(request: Request):
    """POST /api/v1/discover/collaborations -- any active member of the source ecosystem proposes; proposer recorded."""
    body = _body(request)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record = await exchange.propose_collaboration(session, viewer, body)
        await session.commit()
        record, sides = await exchange.load_collaboration(session, viewer, record.id)
        return json(await exchange.collaboration_payload(session, viewer, record, sides), status=201)


async def _approve(request: Request, collaboration_id: uuid.UUID):
    ecosystem_id = _body(request).get("ecosystem_id")
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record, sides = await exchange.load_collaboration(session, viewer, collaboration_id, for_update=True)
        await exchange.approve_collaboration(session, viewer, record, sides, ecosystem_id)
        await session.commit()
        return json(await exchange.collaboration_payload(session, viewer, record, sides))


@discover_api_bp.post("/collaborations/<collaboration_id:uuid>/approve")
@authenticated
async def approve_collaboration(request: Request, collaboration_id: uuid.UUID):
    """POST .../approve {ecosystem_id?} -- a steward approves their side; the row is locked first (one approval)."""
    return await _approve(request, collaboration_id)


@discover_api_bp.post("/collaborations/<collaboration_id:uuid>/activate")
@authenticated
async def activate_collaboration(request: Request, collaboration_id: uuid.UUID):
    """Older name of /approve (same rule)."""
    return await _approve(request, collaboration_id)


@discover_api_bp.post("/collaborations/<collaboration_id:uuid>/end")
@authenticated
async def end_collaboration(request: Request, collaboration_id: uuid.UUID):
    """POST .../end {outcome: completed|dissolved, reason} -- a steward of either side (the proposer while proposed)."""
    body = _body(request)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record, sides = await exchange.load_collaboration(session, viewer, collaboration_id, for_update=True)
        await exchange.end_collaboration(session, viewer, record, sides, body.get("outcome"), body.get("reason"))
        await session.commit()
        return json(await exchange.collaboration_payload(session, viewer, record, sides))


@discover_api_bp.post("/collaborations/<collaboration_id:uuid>/review")
@authenticated
async def review_collaboration(request: Request, collaboration_id: uuid.UUID):
    """POST .../review {note, next_review_date?} -- a steward of either side records a review of an active one."""
    body = _body(request)
    async with request.app.ctx.db() as session:
        viewer = await _viewer(session, request)
        record, sides = await exchange.load_collaboration(session, viewer, collaboration_id, for_update=True)
        await exchange.review_collaboration(session, viewer, record, sides, body.get("note"), body.get("next_review_date"))
        await session.commit()
        return json(await exchange.collaboration_payload(session, viewer, record, sides))
