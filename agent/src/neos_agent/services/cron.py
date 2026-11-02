"""Background cron jobs for governance deadlines and maintenance."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# Cron interval in seconds. Kept as a constant so tests / staging can
# override it. "Due" (reviews, audits, deadlines) is derived per request by
# services/next_steps, never by a job: the log-only deadline and compliance
# scans were deleted (G-Maint); only maintenance and the emergency sweep run.
CRON_INTERVAL_SECONDS = 3600


async def run_cron_loop(app):
    """Main cron loop -- runs periodic tasks. Started by Sanic lifecycle."""
    logger.info("Cron service started")
    while True:
        try:
            await asyncio.sleep(CRON_INTERVAL_SECONDS)
            await _cleanup_expired_sessions(app)
            await _auto_revert_emergencies(app)
            from neos_agent.services.matching import cleanup_private_discovery
            await cleanup_private_discovery(app.ctx.db)
        except asyncio.CancelledError:
            logger.info("Cron service stopping")
            break
        except Exception:
            logger.exception("Cron job error")


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
