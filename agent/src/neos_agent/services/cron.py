"""Background cron jobs for governance deadlines and maintenance."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def run_cron_loop(app):
    """Main cron loop — runs periodic tasks. Started by Sanic lifecycle."""
    logger.info("Cron service started")

    while True:
        try:
            await asyncio.sleep(3600)  # Check every hour
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
    from neos_agent.db.models import Agreement, Proposal

    now = datetime.now(timezone.utc).date()
    week_ahead = now + timedelta(days=7)
    day_ahead = now + timedelta(days=1)

    try:
        async with app.ctx.db() as session:
            # Agreements with upcoming review dates
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
            # Delete expired sessions
            result = await session.execute(
                delete(AuthSession).where(AuthSession.expires_at < now)
            )
            if result.rowcount:
                logger.info("Cleaned up %d expired sessions", result.rowcount)

            # Delete expired/used challenges
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
    from sqlalchemy import select, func
    from neos_agent.db.models import ComplianceSummary, Ecosystem

    threshold = datetime.now(timezone.utc) - timedelta(days=30)

    try:
        async with app.ctx.db() as session:
            # Find ecosystems with stale or missing compliance summaries
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

                if summary is None or summary.generated_at < threshold:
                    logger.info("Compliance summary stale for ecosystem %s — regeneration needed", eco_id)
                    # Actual regeneration would call the compliance API internally
                    # For now, just log — the compliance endpoint handles generation
    except Exception:
        logger.exception("Compliance regen check failed")


async def _auto_revert_emergencies(app):
    """Auto-revert open emergencies whose auto_revert_at timer has expired.

    Per emergency-reversion SKILL.md section C: when the auto-reversion timer
    expires, the emergency MUST transition to half_open (Recovery) regardless
    of whether exit criteria have been met.  This satisfies NEOS Principle 4:
    'Emergency authority automatically expires.'

    Transitions each expired open emergency to half_open, records the trigger
    as 'auto_revert_timer' in the actions_log, and sets half_open_entered_at.
    """
    from sqlalchemy import select, update
    from neos_agent.db.models import EmergencyState

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        async with app.ctx.db() as session:
            stmt = select(EmergencyState).where(
                EmergencyState.state == "open",
                EmergencyState.auto_revert_at.is_not(None),
                EmergencyState.auto_revert_at < now,
            )
            result = await session.execute(stmt)
            expired = result.scalars().all()

            for emergency in expired:
                old_revert_at = emergency.auto_revert_at
                emergency.state = "half_open"
                emergency.half_open_entered_at = now
                # Recovery window: 30 days per SKILL.md section E step 3.
                emergency.auto_revert_at = now + timedelta(days=30)

                # Append auto-trigger audit note
                log = emergency.actions_log or []
                if isinstance(log, dict):
                    log = []
                log.append({
                    "action": "half_open_transition",
                    "timestamp": now.isoformat(),
                    "trigger": "auto_revert_timer",
                    "note": (
                        f"Auto-reversion timer expired (was {old_revert_at.isoformat()}). "
                        "Emergency authority automatically ceased. Recovery state entered. "
                        "30-day ratification window started."
                    ),
                })
                emergency.actions_log = log

                logger.info(
                    "Emergency %s auto-reverted open→half_open (timer expired at %s)",
                    emergency.id,
                    old_revert_at,
                )

            if expired:
                await session.commit()
                logger.info("Auto-reverted %d expired emergencies to half_open", len(expired))
    except Exception:
        logger.exception("Emergency auto-revert check failed")
