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
    from sqlalchemy import delete
    from neos_agent.db.models import AuthSession, AuthChallenge
    now = datetime.now(timezone.utc)
    try:
        async with app.ctx.db() as session:
            result = await session.execute(
                delete(AuthSession).where(AuthSession.expires_at < now)
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
    """Auto-revert open emergencies whose auto_revert_at timer has expired.

    Per emergency-reversion SKILL.md section C: when the auto-reversion
    timer expires, the emergency MUST transition to half_open (Recovery)
    regardless of whether exit criteria have been met. This satisfies
    NEOS Principle 4: 'Emergency authority automatically expires.'

    Concurrency notes:
    - Each candidate row is re-locked individually with SELECT ... FOR
      UPDATE SKIP LOCKED so a concurrent /resolve call (which also takes
      a row lock) cannot double-transition the same record. SKIP LOCKED
      ensures two overlapping cron passes do not block each other; the
      second pass simply finds nothing.
    - The state is re-checked inside the lock; if a manual /resolve
      transitioned the row to half_open between our scan and our lock
      acquisition, we skip it (no double audit entry).
    - On engines that do not support row locks (e.g. SQLite in tests),
      the lock hint is a no-op and the post-lock state check is what
      enforces the invariant.
    """
    from sqlalchemy import select
    from neos_agent.db.models import EmergencyState
    # Local import to avoid the API layer pulling in cron at startup.
    from neos_agent.api.emergency import (
        STATE_OPEN, STATE_HALF_OPEN, RECOVERY_WINDOW_DAYS,
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    try:
        async with app.ctx.db() as session:
            scan_stmt = select(EmergencyState.id).where(
                EmergencyState.state == STATE_OPEN,
                EmergencyState.auto_revert_at.is_not(None),
                EmergencyState.auto_revert_at < now,
            )
            scan_result = await session.execute(scan_stmt)
            candidate_ids = [row[0] for row in scan_result.all()]
            reverted = 0
            for eid in candidate_ids:
                locked = await _lock_and_revert(session, eid, now,
                                                STATE_OPEN, STATE_HALF_OPEN,
                                                RECOVERY_WINDOW_DAYS)
                if locked:
                    reverted += 1
            if reverted:
                await session.commit()
                logger.info("Auto-reverted %d expired emergencies to half_open", reverted)
    except Exception:
        logger.exception("Emergency auto-revert check failed")


async def _lock_and_revert(session, emergency_id, now, state_open,
                           state_half_open, recovery_window_days):
    """Take a row lock on a single emergency, re-check state, and
    transition open -> half_open if still applicable.

    Returns True if the row was transitioned, False if a concurrent
    actor beat us to it (in which case we leave the row alone).
    """
    from sqlalchemy import select
    from neos_agent.db.models import EmergencyState
    try:
        stmt = (
            select(EmergencyState)
            .where(EmergencyState.id == emergency_id)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        emergency = result.scalar_one_or_none()
        if emergency is None:
            return False
        if emergency.state != state_open:
            return False
        if emergency.auto_revert_at is None or emergency.auto_revert_at >= now:
            return False
        old_revert_at = emergency.auto_revert_at
        emergency.state = state_half_open
        emergency.half_open_entered_at = now
        emergency.auto_revert_at = now + timedelta(days=recovery_window_days)
        log = emergency.actions_log or []
        if isinstance(log, dict):
            log = []
        entry = dict()
        entry["action"] = "half_open_transition"
        entry["timestamp"] = now.isoformat()
        entry["trigger"] = "auto_revert_timer"
        entry["note"] = (
            "Auto-reversion timer expired (was " + old_revert_at.isoformat() + "). "
            "Emergency authority automatically ceased. Recovery state entered. "
            "30-day ratification window started."
        )
        log.append(entry)
        emergency.actions_log = log
        logger.info(
            "Emergency %s auto-reverted open->half_open (timer expired at %s)",
            emergency.id, old_revert_at,
        )
        return True
    except Exception:
        logger.exception("Auto-revert lock-and-transition failed for %s", emergency_id)
        return False
