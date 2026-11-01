"""JSON API blueprint for emergencies: a co-signed declaration, a bounded timer, a Recovery people can see and finish.

Blueprint: emergency_api_bp, url_prefix="/api/v1/emergency". Rules, states and rationale:
api/AGENTS.md "Emergency and exit". The module-level transition functions are the one
implementation; REST calls them, and the assistant and cron should too.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from datetime import timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import get_authorized_ecosystem_ids, get_ecosystem_ids, parse_pagination
from neos_agent.api.policy import (
    can_complete_recovery,
    can_cosign_emergency,
    can_declare_emergency,
    can_end_emergency,
    can_review_emergency,
    can_withdraw_emergency,
    emergency_actor_ids,
    is_steward_in,
)
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.db.models import Ecosystem, EmergencyState, Member

logger = logging.getLogger(__name__)

STATE_PENDING = "pending"
STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"
STATE_CLOSED = "closed"
STATE_WITHDRAWN = "withdrawn"
# Every state that blocks a new declaration and shows the all-member banner; the
# partial unique index uq_emergency_states_one_live allows one such row per ecosystem.
ACTIVE_STATES = (STATE_PENDING, STATE_OPEN, STATE_HALF_OPEN)
JUST_DECLARED = "Someone declared an emergency here a moment ago. Open it to co-sign or withdraw it."

# Bounds, one constant each (owner-tunable); the UI reads them from GET /emergency `limits`.
DEFAULT_AUTHORITY_DAYS = 7
MAX_AUTHORITY_DAYS = 30  # the skill's default maximum duration (emergency-criteria-design step 4)
COSIGN_WINDOW_HOURS = 48
REVIEW_SCHEDULE_DAYS = 14
RECOVERY_WINDOW_DAYS = 30

REVIEW_SCHEDULED = "scheduled"
REVIEW_COMPLETE = "complete"
REVIEW_OUTCOMES = (REVIEW_SCHEDULED, REVIEW_COMPLETE)

LIMITS = {
    "default_authority_days": DEFAULT_AUTHORITY_DAYS,
    "max_authority_days": MAX_AUTHORITY_DAYS,
    "cosign_window_hours": COSIGN_WINDOW_HOURS,
    "review_schedule_days": REVIEW_SCHEDULE_DAYS,
    "recovery_window_days": RECOVERY_WINDOW_DAYS,
}

emergency_api_bp = Blueprint("emergency_api", url_prefix="/api/v1/emergency")


def _now_naive_utc() -> _dt.datetime:
    """Naive-UTC wall clock (the columns are tz-naive)."""
    return _dt.datetime.now(timezone.utc).replace(tzinfo=None)


def naive_utc(value: _dt.datetime | None) -> _dt.datetime | None:
    """Stored values may be aware (older assistant writes); compare everything as naive UTC."""
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _iso(value: _dt.datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


# --- Derived timeline: what phase, which dates, what happens next ------------


def cosign_deadline(emergency: EmergencyState) -> _dt.datetime | None:
    declared = naive_utc(emergency.declared_at)
    return declared + timedelta(hours=COSIGN_WINDOW_HOURS) if declared else None


def cosign_expired(emergency: EmergencyState, now: _dt.datetime) -> bool:
    deadline = cosign_deadline(emergency)
    return emergency.state == STATE_PENDING and deadline is not None and now > deadline


def recovery_started(emergency: EmergencyState) -> _dt.datetime | None:
    return naive_utc(emergency.half_open_entered_at or emergency.recovery_entered_at)


def live_condition(now: _dt.datetime):
    """SQL: open, in Recovery, or pending inside the co-sign window (an expired pending is dead before cron flips it)."""
    return or_(
        EmergencyState.state.in_((STATE_OPEN, STATE_HALF_OPEN)),
        and_(
            EmergencyState.state == STATE_PENDING,
            EmergencyState.declared_at > now - timedelta(hours=COSIGN_WINDOW_HOURS),
        ),
    )


def describe(emergency: EmergencyState, now: _dt.datetime) -> dict:
    """Phase, deadlines and the plain next step; the same words for the page, the banner and the assistant."""
    state = emergency.state
    started = recovery_started(emergency)
    review_schedule_by = started + timedelta(days=REVIEW_SCHEDULE_DAYS) if started else None
    review_due_at = started + timedelta(days=RECOVERY_WINDOW_DAYS) if started else None
    review_overdue = bool(
        state == STATE_HALF_OPEN and review_due_at and now > review_due_at
        and emergency.post_review_status != REVIEW_COMPLETE
    )
    if state == STATE_PENDING and cosign_expired(emergency, now):
        phase, next_step = "withdrawn", "Expired: nobody co-signed in time, so nothing changed."
    elif state == STATE_PENDING:
        phase = "pending"
        next_step = "Waiting for a second active member to co-sign. Nothing changes until someone does."
    elif state == STATE_OPEN:
        phase = "open"
        next_step = (
            "Emergency authority is in effect. It ends automatically when the timer runs out, "
            "or earlier if the declarer, the co-signer or a steward ends it."
        )
    elif state == STATE_HALF_OPEN:
        phase = "recovery"
        if emergency.post_review_status == REVIEW_COMPLETE:
            next_step = "The post-emergency review is complete. A steward can now close Recovery."
        elif emergency.post_review_status == REVIEW_SCHEDULED:
            next_step = "The post-emergency review is scheduled. Record it as complete once it has happened."
        else:
            next_step = (
                "Schedule the post-emergency review. Someone who did not declare, "
                "co-sign or end the emergency records it."
            )
        if review_overdue:
            next_step = "Review overdue. " + next_step
    elif state == STATE_WITHDRAWN:
        phase, next_step = "withdrawn", "Withdrawn before anyone co-signed. Nothing changed."
    else:
        phase, next_step = "closed", "Closed. Normal governance is fully restored."
    return {
        "phase": phase,
        "next_step": next_step,
        "cosign_deadline": _iso(cosign_deadline(emergency)) if state == STATE_PENDING else None,
        "authority_ends_at": _iso(naive_utc(emergency.auto_revert_at)) if state == STATE_OPEN else None,
        "recovery_started_at": _iso(started),
        "review_schedule_by": _iso(review_schedule_by),
        "review_due_at": _iso(review_due_at),
        "review_overdue": review_overdue,
    }


def caller_flags(emergency: EmergencyState, caller: Member | None, now: _dt.datetime) -> dict:
    """What `caller` may do with this emergency now (the page's buttons, the queue's items)."""
    live_pending = emergency.state == STATE_PENDING and not cosign_expired(emergency, now)
    in_recovery = emergency.state == STATE_HALF_OPEN
    return {
        "caller_is_steward": is_steward_in(caller, emergency.ecosystem_id),
        "caller_can_cosign": live_pending and can_cosign_emergency(caller, emergency),
        "caller_can_withdraw": live_pending and can_withdraw_emergency(caller, emergency),
        "caller_can_end": emergency.state == STATE_OPEN and can_end_emergency(caller, emergency),
        "caller_can_review": (
            in_recovery and emergency.post_review_status != REVIEW_COMPLETE
            and can_review_emergency(caller, emergency)
        ),
        "caller_can_complete_recovery": (
            in_recovery and emergency.post_review_status == REVIEW_COMPLETE
            and can_complete_recovery(caller, emergency)
        ),
    }


def _list_item(emergency: EmergencyState, now: _dt.datetime) -> dict:
    return {
        "id": str(emergency.id),
        "ecosystem_id": str(emergency.ecosystem_id),
        "state": emergency.state,
        "declared_at": _iso(naive_utc(emergency.declared_at)),
        "declared_by": emergency.declared_by,
        "co_signed_by": emergency.co_signed_by,
        "auto_revert_at": _iso(naive_utc(emergency.auto_revert_at)),
        "closed_at": _iso(naive_utc(emergency.closed_at)),
        "post_review_status": emergency.post_review_status,
        "created_at": _iso(emergency.created_at),
        **describe(emergency, now),
    }


def to_detail(
    emergency: EmergencyState, now: _dt.datetime, *, caller: Member | None = None, ecosystem_name: str | None = None,
) -> dict:
    """The detail payload: the record, its derived timeline and what the caller may do."""
    return {
        **_list_item(emergency, now),
        "ecosystem_name": ecosystem_name,
        "notes": emergency.notes,
        "criteria_met": emergency.criteria_met,
        "authority_days": emergency.authority_days,
        "co_signed_at": _iso(naive_utc(emergency.co_signed_at)),
        "half_open_entered_at": _iso(naive_utc(emergency.half_open_entered_at)),
        "recovery_entered_at": _iso(naive_utc(emergency.recovery_entered_at)),
        "pre_authorized_roles": emergency.pre_authorized_roles,
        "actions_log": emergency.actions_log if isinstance(emergency.actions_log, list) else [],
        "updated_at": _iso(emergency.updated_at),
        **caller_flags(emergency, caller, now),
    }


# --- Transitions: the one implementation (REST, assistant, cron) -------------


def _whole_days(value) -> int | None:
    """7, 7.0 and "7" are seven days; anything else (booleans, fractions, words) is None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _log(emergency: EmergencyState, action: str, now: _dt.datetime, actor: Member | None, note: str, **extra) -> None:
    log = list(emergency.actions_log) if isinstance(emergency.actions_log, list) else []
    entry = {"action": action, "timestamp": now.isoformat(), "note": note, **extra}
    if actor is not None:
        entry["actor"] = actor.display_name
        entry["actor_member_id"] = str(actor.id)
    log.append(entry)
    emergency.actions_log = log  # reassign: JSON columns do not track in-place mutation


def expire_if_stale(emergency: EmergencyState, now: _dt.datetime) -> bool:
    """pending -> withdrawn once the co-sign window has passed; True when it changed."""
    if not cosign_expired(emergency, now):
        return False
    emergency.state = STATE_WITHDRAWN
    emergency.closed_at = now
    _log(emergency, "expired", now, None,
         f"Nobody co-signed within {COSIGN_WINDOW_HOURS} hours. The declaration lapsed; nothing changed.")
    return True


def begin_recovery(emergency: EmergencyState, now: _dt.datetime, *, trigger: str, actor: Member | None = None) -> None:
    """open -> half_open. auto_revert_at keeps the authority deadline; Recovery dates derive from half_open_entered_at."""
    emergency.state = STATE_HALF_OPEN
    emergency.half_open_entered_at = now
    why = "Ended early." if trigger == "manual_resolve" else "The timer ran out."
    _log(emergency, "half_open_transition", now, actor,
         f"{why} Emergency authority stopped and Recovery started: the post-emergency review is due within "
         f"{RECOVERY_WINDOW_DAYS} days.", trigger=trigger)


async def declare(
    session, declarer: Member | None, ecosystem_id: uuid.UUID, *,
    reason: str, days: int = DEFAULT_AUTHORITY_DAYS, criteria_met=None, now: _dt.datetime | None = None,
) -> EmergencyState:
    """Record a pending declaration by `declarer` (from the authenticated caller); a co-signer opens it."""
    now = now or _now_naive_utc()
    if not can_declare_emergency(declarer, ecosystem_id):
        raise ApiError(403, "Only an active member of this ecosystem can declare an emergency.")
    reason = (reason or "").strip()
    if not reason:
        raise ApiError(400, "Say what is happening: a reason is required.")
    days = _whole_days(days)
    if days is None or not 1 <= days <= MAX_AUTHORITY_DAYS:
        raise ApiError(400, f"Emergency authority lasts between 1 and {MAX_AUTHORITY_DAYS} days.")
    rows = (await session.execute(
        select(EmergencyState).where(
            EmergencyState.ecosystem_id == ecosystem_id,
            EmergencyState.state.in_(ACTIVE_STATES),
        ).with_for_update()
    )).scalars().all()
    for row in rows:
        if expire_if_stale(row, now):
            continue
        message = {
            STATE_PENDING: "A declaration is already waiting for a co-signer. Open it to co-sign or withdraw it.",
            STATE_OPEN: "An emergency is already in effect in this ecosystem.",
            STATE_HALF_OPEN: "This ecosystem is in Recovery from an emergency. Close Recovery before declaring again.",
        }[row.state]
        raise ApiError(409, message, {"emergency_id": str(row.id)})
    emergency = EmergencyState(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem_id,
        state=STATE_PENDING,
        declared_by=declarer.display_name,
        declared_by_member_id=declarer.id,
        declared_at=now,
        notes=reason,
        criteria_met=criteria_met,
        authority_days=days,
        pre_authorized_roles=[],
        actions_log=[],
    )
    _log(emergency, "declared", now, declarer,
         f"Declared; waiting for a second active member to co-sign within {COSIGN_WINDOW_HOURS} hours. "
         f"Requested {days} days of emergency authority.")
    await session.flush()  # the stale rows flipped above leave the index before the insert
    try:
        async with session.begin_nested():  # a lost race rolls back only this insert, not the caller's work
            session.add(emergency)
    except IntegrityError:
        raise ApiError(409, JUST_DECLARED) from None
    return emergency


def cosign_refusal(cosigner: Member | None, emergency: EmergencyState, now: _dt.datetime) -> ApiError | None:
    """Why `cosigner` cannot co-sign now (checked before a confirmation is asked), or None."""
    if cosigner is not None and cosigner.id == emergency.declared_by_member_id:
        return ApiError(403, "You declared this emergency, so a second member has to co-sign it.")
    if not can_cosign_emergency(cosigner, emergency):
        return ApiError(403, "Only an active member of this ecosystem can co-sign an emergency.")
    if cosign_expired(emergency, now):
        return ApiError(409, "This declaration expired before anyone co-signed. Declare again if the emergency continues.")
    if emergency.state != STATE_PENDING:
        return ApiError(409, "This declaration is no longer waiting for a co-signer.")
    return None


async def cosign(session, cosigner: Member | None, emergency: EmergencyState, *, now: _dt.datetime | None = None) -> None:
    """pending -> open: a second active member co-signs and the timer starts now."""
    now = now or _now_naive_utc()
    if (refusal := cosign_refusal(cosigner, emergency, now)) is not None:
        raise refusal
    other = await session.scalar(select(EmergencyState.id).where(
        EmergencyState.ecosystem_id == emergency.ecosystem_id,
        EmergencyState.id != emergency.id,
        live_condition(now),
    ).limit(1))
    if other is not None:  # unreachable while the index holds; a second live emergency must never open
        raise ApiError(409, "Another emergency is already live in this ecosystem.", {"emergency_id": str(other)})
    days = emergency.authority_days or DEFAULT_AUTHORITY_DAYS
    emergency.state = STATE_OPEN
    emergency.co_signer_member_id = cosigner.id
    emergency.co_signed_by = cosigner.display_name
    emergency.co_signed_at = now
    emergency.auto_revert_at = now + timedelta(days=days)
    _log(emergency, "co_signed", now, cosigner,
         f"Co-signed. Emergency authority started and ends automatically after {days} days.")


def withdraw(caller: Member | None, emergency: EmergencyState, *, now: _dt.datetime | None = None) -> None:
    """pending -> withdrawn: the declarer or a steward takes back a declaration nobody co-signed."""
    now = now or _now_naive_utc()
    if not can_withdraw_emergency(caller, emergency):
        raise ApiError(403, "Only the member who declared it or a steward can withdraw this declaration.")
    if emergency.state != STATE_PENDING:
        raise ApiError(409, "Only a declaration still waiting for a co-signer can be withdrawn.")
    emergency.state = STATE_WITHDRAWN
    emergency.closed_at = now
    _log(emergency, "withdrawn", now, caller, "Withdrawn before anyone co-signed. Nothing changed.")


def end_authority_refusal(caller: Member | None, emergency: EmergencyState) -> ApiError | None:
    """Why `caller` cannot end emergency authority now, or None."""
    if not can_end_emergency(caller, emergency):
        return ApiError(403, (
            "Only the declarer, the co-signer or a steward can end emergency authority early. "
            "Otherwise it ends automatically when the timer runs out."
        ))
    if emergency.state != STATE_OPEN:
        return ApiError(409, "Only an emergency in effect can be ended.")
    return None


def end_authority(caller: Member | None, emergency: EmergencyState, *, now: _dt.datetime | None = None) -> None:
    """open -> half_open by hand: the declarer, the co-signer or a steward ends authority early."""
    now = now or _now_naive_utc()
    if (refusal := end_authority_refusal(caller, emergency)) is not None:
        raise refusal
    begin_recovery(emergency, now, trigger="manual_resolve", actor=caller)


def review_refusal(reviewer: Member | None, emergency: EmergencyState, *, outcome: str, summary: str) -> ApiError | None:
    """Why `reviewer` cannot record this review now, or None."""
    if outcome not in REVIEW_OUTCOMES:
        return ApiError(400, "Choose whether the review is scheduled or complete.")
    if not (summary or "").strip():
        return ApiError(400, (
            "Add a short note: when the review takes place, or what it found."
        ))
    if reviewer is not None and str(reviewer.id) in emergency_actor_ids(emergency):
        return ApiError(403, "You declared, co-signed or ended this emergency, so someone else records its review.")
    if not can_review_emergency(reviewer, emergency):
        return ApiError(403, "Only an active member of this ecosystem can record the review.")
    if emergency.state != STATE_HALF_OPEN:
        return ApiError(409, "The post-emergency review is recorded during Recovery.")
    if emergency.post_review_status == REVIEW_COMPLETE:
        return ApiError(409, "The review is already recorded as complete.")
    return None


def record_review(
    reviewer: Member | None, emergency: EmergencyState, *, outcome: str, summary: str, now: _dt.datetime | None = None,
) -> None:
    """Write post_review_status (scheduled | complete) during Recovery; emergency actors are excluded."""
    now = now or _now_naive_utc()
    summary = (summary or "").strip()
    if (refusal := review_refusal(reviewer, emergency, outcome=outcome, summary=summary)) is not None:
        raise refusal
    emergency.post_review_status = outcome
    note = "Post-emergency review scheduled." if outcome == REVIEW_SCHEDULED else "Post-emergency review complete."
    _log(emergency, "review_recorded", now, reviewer, note, outcome=outcome, summary=summary)


def complete_recovery_for(caller: Member | None, emergency: EmergencyState, *, now: _dt.datetime | None = None) -> None:
    """half_open -> closed once the review is complete: a steward closes Recovery."""
    now = now or _now_naive_utc()
    if not can_complete_recovery(caller, emergency):
        raise ApiError(403, "Only a steward of this ecosystem can close Recovery.")
    if emergency.state != STATE_HALF_OPEN:
        raise ApiError(409, "Only an emergency in Recovery can be closed.")
    if emergency.post_review_status != REVIEW_COMPLETE:
        raise ApiError(409, "Record the post-emergency review as complete first.",
                       {"next_step": describe(emergency, now)["next_step"]})
    emergency.state = STATE_CLOSED
    emergency.closed_at = now
    _log(emergency, "recovery_completed", now, caller, "Recovery closed. Normal governance is fully restored.")


# --- Handlers -----------------------------------------------------------------


async def _ecosystem_names(session, ecosystem_ids) -> dict:
    if not ecosystem_ids:
        return {}
    rows = await session.execute(select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(list(ecosystem_ids))))
    return {row.id: row.name for row in rows}


async def _detail_response(session, request: Request, emergency: EmergencyState, now: _dt.datetime) -> dict:
    caller = await caller_in(session, request, emergency.ecosystem_id)
    names = await _ecosystem_names(session, [emergency.ecosystem_id])
    return to_detail(emergency, now, caller=caller, ecosystem_name=names.get(emergency.ecosystem_id))


async def _load_for_update(session, request: Request, emergency_id: uuid.UUID) -> EmergencyState:
    """Row-locked load within the caller's authorized ecosystems (cron and a manual move cannot double-apply)."""
    statement = restrict_to_ecosystems(
        select(EmergencyState).where(EmergencyState.id == emergency_id),
        EmergencyState, get_authorized_ecosystem_ids(request),
    ).with_for_update()
    emergency = (await session.execute(statement)).scalar_one_or_none()
    if emergency is None:
        raise ApiError(404, "Emergency record not found")
    return emergency


def _json_body(request: Request) -> dict:
    body = request.json if request.body else {}
    if not isinstance(body, dict):
        raise ApiError(400, "Send a JSON object.")
    return body


@emergency_api_bp.get("/")
@authenticated
async def list_emergencies(request: Request):
    """GET /api/v1/emergency -- the live emergency per selected ecosystem, history, limits, where the caller may declare."""
    eco_ids = get_ecosystem_ids(request)
    page = parse_pagination(request)
    now = _now_naive_utc()
    async with request.app.ctx.db() as session:
        scoped = restrict_to_ecosystems(select(EmergencyState), EmergencyState, eco_ids)
        total = await session.scalar(select(func.count()).select_from(scoped.subquery())) or 0
        history = (await session.execute(
            scoped.order_by(EmergencyState.declared_at.desc(), EmergencyState.created_at.desc())
            .offset(page.offset).limit(page.per_page)
        )).scalars().all()
        live = (await session.execute(
            scoped.where(live_condition(now)).order_by(EmergencyState.declared_at.desc())
        )).scalars().all()
        names = await _ecosystem_names(session, eco_ids)
        callers = {eco_id: await caller_in(session, request, eco_id) for eco_id in eco_ids}
    live_ecosystems = {emergency.ecosystem_id for emergency in live}
    active = [
        to_detail(e, now, caller=callers.get(e.ecosystem_id), ecosystem_name=names.get(e.ecosystem_id))
        for e in live
    ]
    return json({
        "current": active[0] if active else None,
        "active": active,
        "items": [_list_item(e, now) for e in history],
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
        "limits": LIMITS,
        "caller_can_declare_in": [
            str(eco_id) for eco_id in eco_ids
            if eco_id not in live_ecosystems and can_declare_emergency(callers.get(eco_id), eco_id)
        ],
    })


@emergency_api_bp.get("/active")
@authenticated
async def active_emergencies(request: Request):
    """GET /api/v1/emergency/active -- live emergencies in EVERY ecosystem the caller is active in (the banner)."""
    eco_ids = get_authorized_ecosystem_ids(request)
    now = _now_naive_utc()
    async with request.app.ctx.db() as session:
        live = (await session.execute(
            restrict_to_ecosystems(select(EmergencyState), EmergencyState, eco_ids)
            .where(live_condition(now)).order_by(EmergencyState.declared_at.desc())
        )).scalars().all()
        names = await _ecosystem_names(session, {e.ecosystem_id for e in live})
        items = [
            to_detail(e, now, caller=await caller_in(session, request, e.ecosystem_id),
                      ecosystem_name=names.get(e.ecosystem_id))
            for e in live
        ]
    return json({"items": items})


@emergency_api_bp.get("/<emergency_id:uuid>")
@authenticated
async def get_emergency(request: Request, emergency_id: uuid.UUID):
    """GET /api/v1/emergency/:id -- detail with timeline, next step and caller flags."""
    async with request.app.ctx.db() as session:
        emergency = await get_scoped_or_404(session, request, EmergencyState, emergency_id, label="Emergency record")
        return json(await _detail_response(session, request, emergency, _now_naive_utc()))


@emergency_api_bp.post("/declare")
@authenticated
async def declare_emergency(request: Request):
    """POST /api/v1/emergency/declare {ecosystem_id, reason, auto_revert_days} -- pending until co-signed."""
    body = _json_body(request)
    try:
        ecosystem_id = uuid.UUID(str(body.get("ecosystem_id")))
    except ValueError:
        raise ApiError(400, "Choose the ecosystem the emergency is in.")
    days = body.get("auto_revert_days", DEFAULT_AUTHORITY_DAYS)
    now = _now_naive_utc()
    async with request.app.ctx.db() as session:
        declarer = await caller_in(session, request, ecosystem_id)
        emergency = await declare(
            session, declarer, ecosystem_id, reason=body.get("reason") or "", days=days,
            criteria_met=body.get("criteria_met"), now=now,
        )
        await session.commit()
        await session.refresh(emergency)  # created_at/updated_at are server-generated
        logger.info("Emergency %s declared (pending co-sign) in %s", emergency.id, ecosystem_id)
        return json(await _detail_response(session, request, emergency, now), status=201)


async def _transition(request: Request, emergency_id: uuid.UUID, apply) -> dict:
    now = _now_naive_utc()
    async with request.app.ctx.db() as session:
        emergency = await _load_for_update(session, request, emergency_id)
        caller = await caller_in(session, request, emergency.ecosystem_id)
        await apply(session, caller, emergency, now)
        await session.commit()
        await session.refresh(emergency)  # updated_at is server-generated
        logger.info("Emergency %s is now %s", emergency_id, emergency.state)
        return await _detail_response(session, request, emergency, now)


@emergency_api_bp.post("/<emergency_id:uuid>/cosign")
@authenticated
async def cosign_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/cosign -- a second active member opens the emergency; the timer starts."""
    async def apply(session, caller, emergency, now):
        await cosign(session, caller, emergency, now=now)
    return json(await _transition(request, emergency_id, apply))


@emergency_api_bp.post("/<emergency_id:uuid>/withdraw")
@authenticated
async def withdraw_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/withdraw -- take back a declaration nobody co-signed."""
    async def apply(session, caller, emergency, now):
        withdraw(caller, emergency, now=now)
    return json(await _transition(request, emergency_id, apply))


@emergency_api_bp.post("/<emergency_id:uuid>/resolve")
@authenticated
async def resolve_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/resolve -- end authority early: open -> half_open (Recovery), never closed."""
    async def apply(session, caller, emergency, now):
        end_authority(caller, emergency, now=now)
    return json(await _transition(request, emergency_id, apply))


@emergency_api_bp.post("/<emergency_id:uuid>/review")
@authenticated
async def review_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/review {outcome: scheduled|complete, summary} -- writes post_review_status."""
    body = _json_body(request)

    async def apply(session, caller, emergency, now):
        record_review(caller, emergency, outcome=body.get("outcome"), summary=body.get("summary") or "", now=now)
    return json(await _transition(request, emergency_id, apply))


@emergency_api_bp.post("/<emergency_id:uuid>/complete-recovery")
@authenticated
async def complete_recovery(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/complete-recovery -- half_open -> closed after a complete review."""
    async def apply(session, caller, emergency, now):
        complete_recovery_for(caller, emergency, now=now)
    return json(await _transition(request, emergency_id, apply))
