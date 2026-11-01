"""Background cron jobs for governance deadlines and maintenance."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# Cron interval in seconds. Kept as a constant so tests / staging can
# override it. The auto-revert sweep relies on the parent loop ordering
# below: deadlines first, then maintenance, then emergencies, so a slow
# deadline scan cannot indefinitely starve the emergency revert sweep.
CRON_INTERVAL_SECONDS = 3600


async def run_cron_loop(app):
    """Main cron loop -- runs periodic tasks. Started by Sanic lifecycle."""
    logger.info("Cron service started")
    while True:
        try:
            await asyncio.sleep(CRON_INTERVAL_SECONDS)
            await _check_deadlines(app)
            await _cleanup_expired_sessions(app)
            await _check_compliance_regen(app)
            await _auto_revert_emergencies(app)
        except asyncio.CancelledError:
            logger.info("Cron service stopping")
            break
        except Exception:
            logger.exception("Cron job error")


async def _check_deadlines(app):
    """Check for upcoming governance deadlines and send notifications."""
    from sqlalchemy import select
    from neos_agent.db.models import Agreement
    now = datetime.now(timezone.utc).date()
    week_ahead = now + timedelta(days=7)
    try:
        async with app.ctx.db() as session:
            result = await session.execute(
                select(Agreement).where(
                    Agreement.review_date.between(now, week_ahead),
                    Agreement.status.in_(["active", "under_review"]),
                )
            )
            due_agreements = result.scalars().all()
            for agr in due_agreements:
                days_until = (agr.review_date - now).days
                if days_until <= 1:
                    logger.info("Agreement review due tomorrow: %s", agr.title)
                elif days_until <= 7:
                    logger.info("Agreement review due in %d days: %s", days_until, agr.title)
    except Exception:
        logger.exception("Deadline check failed")


async def _cleanup_expired_sessions(app):
    """Remove expired auth sessions and challenges."""
    from sqlalchemy import delete, exists, select
    from neos_agent.db.models import AgentToken, AuthSession, AuthChallenge
    now = datetime.now(timezone.utc)
    try:
        async with app.ctx.db() as session:
            # A session an agent token points to stays as that token's history (the token already died with it).
            referenced = exists(select(AgentToken.id).where(AgentToken.auth_session_id == AuthSession.id))
            result = await session.execute(
                delete(AuthSession).where(AuthSession.expires_at < now, ~referenced)
            )
            if result.rowcount:
                logger.info("Cleaned up %d expired sessions", result.rowcount)
            result = await session.execute(
                delete(AuthChallenge).where(
                    (AuthChallenge.expires_at < now) | (AuthChallenge.used.is_(True))
                )
            )
            if result.rowcount:
                logger.info("Cleaned up %d expired challenges", result.rowcount)
            await session.commit()
    except Exception:
        logger.exception("Session cleanup failed")


async def _check_compliance_regen(app):
    """Regenerate compliance summaries older than 30 days."""
    from sqlalchemy import select
    from neos_agent.db.models import ComplianceSummary, Ecosystem
    threshold = datetime.now(timezone.utc) - timedelta(days=30)
    try:
        async with app.ctx.db() as session:
            result = await session.execute(select(Ecosystem.id))
            ecosystem_ids = [r[0] for r in result.all()]
            for eco_id in ecosystem_ids:
                latest = await session.execute(
                    select(ComplianceSummary)
                    .where(ComplianceSummary.ecosystem_id == eco_id)
                    .order_by(ComplianceSummary.generated_at.desc())
                    .limit(1)
                )
                summary = latest.scalar_one_or_none()
                generated_at = summary.generated_at if summary else None
                if generated_at is not None and generated_at.tzinfo is None:
                    generated_at = generated_at.replace(tzinfo=timezone.utc)
                if generated_at is None or generated_at < threshold:
                    logger.info("Compliance summary stale for ecosystem %s -- regeneration needed", eco_id)
    except Exception:
        logger.exception("Compliance regen check failed")


async def _auto_revert_emergencies(app):
    """Emergency sweep: expired timers open -> half_open (Recovery); unsigned declarations lapse after the co-sign window.

    Recovery never auto-closes: past its window the API reports "review overdue" to stewards.
    Rationale and locking: api/AGENTS.md "Emergency and exit".
    """
    from sqlalchemy import or_, and_, select
    from neos_agent.db.models import EmergencyState
    # Local import to avoid the API layer pulling in cron at startup.
    from neos_agent.api.emergency import (
        COSIGN_WINDOW_HOURS, STATE_OPEN, STATE_PENDING,
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        async with app.ctx.db() as session:
            scan_stmt = select(EmergencyState.id).where(or_(
                and_(
                    EmergencyState.state == STATE_OPEN,
                    EmergencyState.auto_revert_at.is_not(None),
                    EmergencyState.auto_revert_at < now,
                ),
                and_(
                    EmergencyState.state == STATE_PENDING,
                    EmergencyState.declared_at < now - timedelta(hours=COSIGN_WINDOW_HOURS),
                ),
            ))
            candidate_ids = [row[0] for row in (await session.execute(scan_stmt)).all()]
            changed = 0
            for eid in candidate_ids:
                if await _lock_and_revert(session, eid, now):
                    changed += 1
            if changed:
                await session.commit()
                logger.info("Emergency sweep moved %d emergencies", changed)
    except Exception:
        logger.exception("Emergency auto-revert check failed")


async def _lock_and_revert(session, emergency_id, now) -> bool:
    """Row-lock one emergency (SKIP LOCKED), re-check it, and apply the timed move; False when nothing was due."""
    from sqlalchemy import select
    from neos_agent.db.models import EmergencyState
    from neos_agent.api.emergency import STATE_OPEN, begin_recovery, expire_if_stale, naive_utc
    try:
        stmt = (
            select(EmergencyState)
            .where(EmergencyState.id == emergency_id)
            .with_for_update(skip_locked=True)
        )
        emergency = (await session.execute(stmt)).scalar_one_or_none()
        if emergency is None:
            return False
        if expire_if_stale(emergency, now):
            logger.info("Emergency %s lapsed without a co-signer", emergency.id)
            return True
        revert_at = naive_utc(emergency.auto_revert_at)
        if emergency.state != STATE_OPEN or revert_at is None or revert_at >= now:
            return False
        begin_recovery(emergency, now, trigger="auto_revert_timer")
        logger.info("Emergency %s auto-reverted open->half_open (timer expired at %s)", emergency.id, revert_at)
        return True
    except Exception:
        logger.exception("Auto-revert lock-and-transition failed for %s", emergency_id)
        return False
