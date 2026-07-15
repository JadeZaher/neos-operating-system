"""JSON API blueprint for the Discover feed.

Blueprint: discover_api_bp, url_prefix="/api/v1/discover"

Aggregates public quizzes and ecosystems so users can browse and
find content to engage with.  Authentication is required but the
endpoint intentionally returns *all* public content, not just items
scoped to the caller's ecosystem.
"""

from __future__ import annotations

import logging
import re
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import Ecosystem, Member, SharesNeeds, Collaboration, Domain
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, require_admin

logger = logging.getLogger(__name__)

discover_api_bp = Blueprint("discover_api", url_prefix="/api/v1/discover")


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


# --- Endpoints ---


@discover_api_bp.get("/")
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
    member, err = require_auth(request)
    if err:
        return err

    search = request.args.get("q", "").strip()
    tab = request.args.get("tab", "all")
    mode_filter = request.args.get("mode")
    tag_filter = request.args.get("tag")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 12))))
    offset = (page - 1) * per_page

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
                    .where(Member.ecosystem_id.in_(eco_ids))
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
# Shares / Needs
# ---------------------------------------------------------------------------


@discover_api_bp.get("/shares-needs")
async def list_shares_needs(request: Request):
    """GET /api/v1/discover/shares-needs -- Cross-ecosystem shares & needs discovery.

    Query params:
        q            – search term (matches title / description)
        type         – filter by "share" or "need"
        category     – category filter
        ecosystem_id – filter to a specific ecosystem UUID
        page         – pagination page (default 1)
        per_page     – items per page (default 20, max 50)
    """
    member, err = require_auth(request)
    if err:
        return err

    search = request.args.get("q", "").strip()
    type_filter = request.args.get("type")
    category_filter = request.args.get("category")
    ecosystem_id_filter = request.args.get("ecosystem_id")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 20))))
    offset = (page - 1) * per_page

    filters = [SharesNeeds.visibility == "public", SharesNeeds.status == "active"]
    if search:
        pattern = f"%{_escape_like(search)}%"
        filters.append(SharesNeeds.title.ilike(pattern) | SharesNeeds.description.ilike(pattern))
    if type_filter:
        filters.append(SharesNeeds.type == type_filter)
    if category_filter:
        filters.append(SharesNeeds.category == category_filter)
    if ecosystem_id_filter:
        try:
            filters.append(SharesNeeds.ecosystem_id == uuid.UUID(ecosystem_id_filter))
        except ValueError:
            return json({"error": "Invalid ecosystem_id"}, status=400)

    async with request.app.ctx.db() as session:
        total_row = await session.execute(
            select(func.count(SharesNeeds.id)).where(*filters)
        )
        total = total_row.scalar() or 0

        stmt = (
            select(SharesNeeds)
            .where(*filters)
            .order_by(SharesNeeds.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        rows = (await session.execute(stmt)).scalars().all()

        # Bulk-load domain names
        domain_ids = list({r.domain_id for r in rows})
        domain_names: dict[uuid.UUID, str] = {}
        if domain_ids:
            d_rows = await session.execute(
                select(Domain.id, Domain.domain_id).where(Domain.id.in_(domain_ids))
            )
            for d in d_rows:
                domain_names[d.id] = d.domain_id

        # Bulk-load ecosystem names
        eco_ids = list({r.ecosystem_id for r in rows})
        eco_names: dict[uuid.UUID, str] = {}
        if eco_ids:
            e_rows = await session.execute(
                select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(eco_ids))
            )
            for e in e_rows:
                eco_names[e.id] = e.name

        items = []
        for r in rows:
            items.append({
                "id": str(r.id),
                "ecosystem_id": str(r.ecosystem_id),
                "ecosystem_name": eco_names.get(r.ecosystem_id),
                "domain_id": str(r.domain_id),
                "domain_name": domain_names.get(r.domain_id),
                "type": r.type,
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "capacity": r.capacity,
                "tags": r.tags if isinstance(r.tags, list) else [],
                "visibility": r.visibility,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    return json({"items": items, "total": total, "page": page, "per_page": per_page})


# ---------------------------------------------------------------------------
# Shares / Needs — Admin Management
# ---------------------------------------------------------------------------


@discover_api_bp.get("/shares-needs/admin")
async def admin_list_shares_needs(request: Request):
    """GET /api/v1/discover/shares-needs/admin -- Admin list of ALL shares & needs.

    Unlike the public endpoint, this returns items regardless of visibility or status.
    Query params:
        q            – search term
        type         – filter by "share" or "need"
        category     – category filter
        status       – status filter (active, fulfilled, withdrawn)
        ecosystem_id – filter to a specific ecosystem UUID
        page         – pagination page (default 1)
        per_page     – items per page (default 50, max 100)
    """
    member, err = require_admin(request)
    if err:
        return err

    search = request.args.get("q", "").strip()
    type_filter = request.args.get("type")
    category_filter = request.args.get("category")
    status_filter = request.args.get("status")
    ecosystem_id_filter = request.args.get("ecosystem_id")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    offset = (page - 1) * per_page

    filters = []
    if search:
        pattern = f"%{_escape_like(search)}%"
        filters.append(SharesNeeds.title.ilike(pattern) | SharesNeeds.description.ilike(pattern))
    if type_filter:
        filters.append(SharesNeeds.type == type_filter)
    if category_filter:
        filters.append(SharesNeeds.category == category_filter)
    if status_filter:
        filters.append(SharesNeeds.status == status_filter)
    if ecosystem_id_filter:
        try:
            filters.append(SharesNeeds.ecosystem_id == uuid.UUID(ecosystem_id_filter))
        except ValueError:
            return json({"error": "Invalid ecosystem_id"}, status=400)

    async with request.app.ctx.db() as session:
        total_row = await session.execute(
            select(func.count(SharesNeeds.id)).where(*filters)
        )
        total = total_row.scalar() or 0

        stmt = (
            select(SharesNeeds)
            .where(*filters)
            .order_by(SharesNeeds.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        rows = (await session.execute(stmt)).scalars().all()

        # Bulk-load domain names
        domain_ids = list({r.domain_id for r in rows})
        domain_names: dict[uuid.UUID, str] = {}
        if domain_ids:
            d_rows = await session.execute(
                select(Domain.id, Domain.domain_id).where(Domain.id.in_(domain_ids))
            )
            for d in d_rows:
                domain_names[d.id] = d.domain_id

        # Bulk-load ecosystem names
        eco_ids = list({r.ecosystem_id for r in rows})
        eco_names: dict[uuid.UUID, str] = {}
        if eco_ids:
            e_rows = await session.execute(
                select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(eco_ids))
            )
            for e in e_rows:
                eco_names[e.id] = e.name

        # Stats
        stats_row = await session.execute(
            select(
                func.count(SharesNeeds.id).label("total"),
                func.sum(func.case((SharesNeeds.type == "share", 1), else_=0)).label("shares"),
                func.sum(func.case((SharesNeeds.type == "need", 1), else_=0)).label("needs"),
                func.sum(func.case((SharesNeeds.status == "active", 1), else_=0)).label("active"),
                func.sum(func.case((SharesNeeds.status == "fulfilled", 1), else_=0)).label("fulfilled"),
                func.sum(func.case((SharesNeeds.status == "withdrawn", 1), else_=0)).label("withdrawn"),
            )
        )
        stats = stats_row.first()

        items = []
        for r in rows:
            items.append({
                "id": str(r.id),
                "ecosystem_id": str(r.ecosystem_id),
                "ecosystem_name": eco_names.get(r.ecosystem_id),
                "domain_id": str(r.domain_id),
                "domain_name": domain_names.get(r.domain_id),
                "type": r.type,
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "capacity": r.capacity,
                "tags": r.tags if isinstance(r.tags, list) else [],
                "visibility": r.visibility,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    return json({
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "stats": {
            "total": stats.total or 0,
            "shares": stats.shares or 0,
            "needs": stats.needs or 0,
            "active": stats.active or 0,
            "fulfilled": stats.fulfilled or 0,
            "withdrawn": stats.withdrawn or 0,
        },
    })


async def _require_auth_for_shares_needs(request: Request, session, sn_uuid: uuid.UUID):
    """Authorise access to a SharesNeeds record.

    Returns (member, record, None) on success or (None, None, error_response).
    Admins (co_creator / builder) can access any record.  Regular authenticated
    users can access records that belong to an ecosystem they are a member of.
    """
    member, err = require_auth(request)
    if err:
        return None, None, err

    record = await session.get(SharesNeeds, sn_uuid)
    if not record:
        return None, None, json({"error": "Share/Need not found"}, status=404)

    # Admins can always proceed
    if member.profile in ("co_creator", "builder"):
        return member, record, None

    # Regular members: must belong to the record's ecosystem
    membership = await session.execute(
        select(Member).where(
            Member.ecosystem_id == record.ecosystem_id,
            Member.user_id == member.user_id,
        )
    )
    if not membership.scalars().first():
        return None, None, json({"error": "You are not a member of this ecosystem"}, status=403)

    return member, record, None


@discover_api_bp.put("/shares-needs/<sn_id:str>")
async def update_share_need(request: Request, sn_id: str):
    """PUT /api/v1/discover/shares-needs/<id> -- Update a share or need.

    Accessible by admins (co_creator/builder) and ecosystem members.
    """
    try:
        sn_uuid = uuid.UUID(sn_id)
    except ValueError:
        return json({"error": "Invalid ID"}, status=400)

    body = request.json or {}
    # Regular members may not reassign ecosystem_id or domain_id
    member, err = require_auth(request)
    if err:
        return err
    is_admin = member.profile in ("co_creator", "builder")
    allowed_fields = {"title", "description", "category", "capacity", "tags", "visibility"}
    if is_admin:
        allowed_fields |= {"domain_id", "ecosystem_id"}
    update_data = {k: v for k, v in body.items() if k in allowed_fields}

    if not update_data:
        return json({"error": "No valid fields to update"}, status=400)

    async with request.app.ctx.db() as session:
        member, record, auth_err = await _require_auth_for_shares_needs(request, session, sn_uuid)
        if auth_err:
            return auth_err

        for key, value in update_data.items():
            setattr(record, key, value)

        await session.commit()
        await session.refresh(record)

    return json({
        "id": str(record.id),
        "ecosystem_id": str(record.ecosystem_id),
        "domain_id": str(record.domain_id),
        "type": record.type,
        "title": record.title,
        "description": record.description,
        "category": record.category,
        "capacity": record.capacity,
        "tags": record.tags if isinstance(record.tags, list) else [],
        "visibility": record.visibility,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    })


@discover_api_bp.post("/shares-needs/<sn_id:str>/status")
async def update_share_need_status(request: Request, sn_id: str):
    """POST /api/v1/discover/shares-needs/<id>/status -- Change status.

    Accessible by admins (co_creator/builder) and ecosystem members.
    """
    try:
        sn_uuid = uuid.UUID(sn_id)
    except ValueError:
        return json({"error": "Invalid ID"}, status=400)

    body = request.json or {}
    new_status = body.get("status")
    if new_status not in ("active", "fulfilled", "withdrawn"):
        return json({"error": "Status must be 'active', 'fulfilled', or 'withdrawn'"}, status=400)

    async with request.app.ctx.db() as session:
        member, record, auth_err = await _require_auth_for_shares_needs(request, session, sn_uuid)
        if auth_err:
            return auth_err

        old_status = record.status
        record.status = new_status
        await session.commit()
        await session.refresh(record)

    return json({
        "id": str(record.id),
        "type": record.type,
        "title": record.title,
        "status": record.status,
        "previous_status": old_status,
    })


@discover_api_bp.delete("/shares-needs/<sn_id:str>")
async def delete_share_need(request: Request, sn_id: str):
    """DELETE /api/v1/discover/shares-needs/<id> -- Delete a share or need.

    Accessible by admins (co_creator/builder) and ecosystem members.
    """
    try:
        sn_uuid = uuid.UUID(sn_id)
    except ValueError:
        return json({"error": "Invalid ID"}, status=400)

    async with request.app.ctx.db() as session:
        member, record, auth_err = await _require_auth_for_shares_needs(request, session, sn_uuid)
        if auth_err:
            return auth_err

        await session.delete(record)
        await session.commit()

    return json({"ok": True, "message": "Share/Need deleted"})


@discover_api_bp.post("/shares-needs")
async def create_share_need(request: Request):
    """POST /api/v1/discover/shares-needs -- Create a new share or need (authenticated).

    Body (JSON):
        ecosystem_id  – UUID of the ecosystem (required)
        domain_id     – UUID of the domain (required)
        type          – "share" or "need" (required)
        title         – display title (required)
        description   – optional detail text
        category      – technology | resources | skills | knowledge | infrastructure | funding | space | labor | other
        capacity      – availability level
        tags          – list of strings
        visibility    – "public" (default), "ecosystem", "private"
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    eco_id_str = body.get("ecosystem_id")
    domain_id_str = body.get("domain_id")
    sn_type = body.get("type")
    title = (body.get("title") or "").strip()

    if not eco_id_str or not domain_id_str or not sn_type or not title:
        return json({"error": "ecosystem_id, domain_id, type, and title are required"}, status=400)
    if sn_type not in ("share", "need"):
        return json({"error": "type must be 'share' or 'need'"}, status=400)

    try:
        eco_id = uuid.UUID(eco_id_str)
        domain_id = uuid.UUID(domain_id_str)
    except ValueError:
        return json({"error": "Invalid UUID in ecosystem_id or domain_id"}, status=400)

    async with request.app.ctx.db() as session:
        # Validate the authenticated member belongs to the requested ecosystem
        member_check = await session.execute(
            select(Member).where(
                Member.ecosystem_id == eco_id,
                Member.user_id == member.user_id,
            )
        )
        if not member_check.scalars().first():
            return json({"error": "You are not a member of the specified ecosystem"}, status=403)

        record = SharesNeeds(
            id=uuid.uuid4(),
            ecosystem_id=eco_id,
            domain_id=domain_id,
            type=sn_type,
            title=title,
            description=body.get("description"),
            category=body.get("category"),
            capacity=body.get("capacity"),
            tags=body.get("tags"),
            visibility=body.get("visibility", "public"),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return json({
        "id": str(record.id),
        "ecosystem_id": str(record.ecosystem_id),
        "domain_id": str(record.domain_id),
        "type": record.type,
        "title": record.title,
        "description": record.description,
        "category": record.category,
        "capacity": record.capacity,
        "tags": record.tags if isinstance(record.tags, list) else [],
        "visibility": record.visibility,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }, status=201)


# ---------------------------------------------------------------------------
# Collaborations
# ---------------------------------------------------------------------------


@discover_api_bp.get("/collaborations")
async def list_collaborations(request: Request):
    """GET /api/v1/discover/collaborations -- Active collaborations for discovery.

    Query params:
        q               – search term (matches title / description)
        status          – filter by status (proposed, active, completed, dissolved)
        engagement_tier – filter by tier (observe, cooperate, federate, integrate)
        page            – pagination page (default 1)
        per_page        – items per page (default 20, max 50)
    """
    member, err = require_auth(request)
    if err:
        return err

    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status")
    tier_filter = request.args.get("engagement_tier")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(50, max(1, int(request.args.get("per_page", 20))))
    offset = (page - 1) * per_page

    filters = []
    if search:
        pattern = f"%{_escape_like(search)}%"
        filters.append(
            Collaboration.title.ilike(pattern) | Collaboration.description.ilike(pattern)
        )
    if status_filter:
        filters.append(Collaboration.status == status_filter)
    else:
        # Default: only active collaborations for public discovery
        filters.append(Collaboration.status == "active")
    if tier_filter:
        filters.append(Collaboration.engagement_tier == tier_filter)

    async with request.app.ctx.db() as session:
        total_row = await session.execute(
            select(func.count(Collaboration.id)).where(*filters)
        )
        total = total_row.scalar() or 0

        stmt = (
            select(Collaboration)
            .where(*filters)
            .order_by(Collaboration.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        rows = (await session.execute(stmt)).scalars().all()

        # Bulk-load domain names for both source and target
        all_domain_ids = list({r.source_domain_id for r in rows} | {r.target_domain_id for r in rows})
        domain_info: dict[uuid.UUID, dict] = {}
        if all_domain_ids:
            d_rows = await session.execute(
                select(Domain.id, Domain.domain_id, Domain.ecosystem_id).where(
                    Domain.id.in_(all_domain_ids)
                )
            )
            for d in d_rows:
                domain_info[d.id] = {"name": d.domain_id, "ecosystem_id": d.ecosystem_id}

        # Bulk-load ecosystem names
        eco_ids = list({v["ecosystem_id"] for v in domain_info.values() if v.get("ecosystem_id")})
        eco_names: dict[uuid.UUID, str] = {}
        if eco_ids:
            e_rows = await session.execute(
                select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(eco_ids))
            )
            for e in e_rows:
                eco_names[e.id] = e.name

        items = []
        for r in rows:
            src = domain_info.get(r.source_domain_id, {})
            tgt = domain_info.get(r.target_domain_id, {})
            items.append({
                "id": str(r.id),
                "title": r.title,
                "description": r.description,
                "status": r.status,
                "engagement_tier": r.engagement_tier,
                "source_domain_id": str(r.source_domain_id),
                "source_domain_name": src.get("name"),
                "source_ecosystem_id": str(src["ecosystem_id"]) if src.get("ecosystem_id") else None,
                "source_ecosystem_name": eco_names.get(src.get("ecosystem_id")) if src.get("ecosystem_id") else None,
                "target_domain_id": str(r.target_domain_id),
                "target_domain_name": tgt.get("name"),
                "target_ecosystem_id": str(tgt["ecosystem_id"]) if tgt.get("ecosystem_id") else None,
                "target_ecosystem_name": eco_names.get(tgt.get("ecosystem_id")) if tgt.get("ecosystem_id") else None,
                "started_date": r.started_date.isoformat() if r.started_date else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    return json({"items": items, "total": total, "page": page, "per_page": per_page})


@discover_api_bp.post("/collaborations")
async def propose_collaboration(request: Request):
    """POST /api/v1/discover/collaborations -- Propose a new collaboration (authenticated).

    Body (JSON):
        source_domain_id  – UUID of the proposing domain (required)
        target_domain_id  – UUID of the target domain (required)
        title             – display title (required)
        description       – optional detail
        engagement_tier   – observe | cooperate (default) | federate | integrate
        terms             – optional JSON object with collaboration-specific terms
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    src_id_str = body.get("source_domain_id")
    tgt_id_str = body.get("target_domain_id")
    title = (body.get("title") or "").strip()

    if not src_id_str or not tgt_id_str or not title:
        return json({"error": "source_domain_id, target_domain_id, and title are required"}, status=400)

    try:
        src_id = uuid.UUID(src_id_str)
        tgt_id = uuid.UUID(tgt_id_str)
    except ValueError:
        return json({"error": "Invalid UUID in source_domain_id or target_domain_id"}, status=400)

    async with request.app.ctx.db() as session:
        # Resolve source domain to get its ecosystem
        src_domain_row = await session.execute(
            select(Domain).where(Domain.id == src_id)
        )
        src_domain = src_domain_row.scalars().first()
        if not src_domain:
            return json({"error": "source_domain_id not found"}, status=404)

        # Validate the authenticated member belongs to the source domain's ecosystem
        member_check = await session.execute(
            select(Member).where(
                Member.ecosystem_id == src_domain.ecosystem_id,
                Member.user_id == member.user_id,
            )
        )
        if not member_check.scalars().first():
            return json({"error": "You are not a member of the source domain's ecosystem"}, status=403)

        # Validate target domain exists
        tgt_domain_row = await session.execute(
            select(Domain).where(Domain.id == tgt_id)
        )
        if not tgt_domain_row.scalars().first():
            return json({"error": "target_domain_id not found"}, status=404)

        record = Collaboration(
            id=uuid.uuid4(),
            source_domain_id=src_id,
            target_domain_id=tgt_id,
            title=title,
            description=body.get("description"),
            engagement_tier=body.get("engagement_tier", "cooperate"),
            terms=body.get("terms"),
            status="proposed",
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return json({
        "id": str(record.id),
        "source_domain_id": str(record.source_domain_id),
        "target_domain_id": str(record.target_domain_id),
        "title": record.title,
        "description": record.description,
        "status": record.status,
        "engagement_tier": record.engagement_tier,
        "terms": record.terms,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }, status=201)
