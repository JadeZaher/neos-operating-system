"""Push notification service using Web Push (VAPID)."""
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_push_notification(
    endpoint: str,
    p256dh_key: str,
    auth_key: str,
    title: str,
    body: str,
    url: str | None = None,
    vapid_private_key: str | None = None,
    vapid_email: str | None = None,
) -> bool:
    """Send a Web Push notification. Returns True on success."""
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush not installed — push notifications disabled")
        return False

    if not vapid_private_key:
        logger.debug("No VAPID_PRIVATE_KEY configured — skipping push")
        return False

    subscription_info = {
        "endpoint": endpoint,
        "keys": {"p256dh": p256dh_key, "auth": auth_key},
    }
    payload = json.dumps({"title": title, "body": body, "url": url})

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": f"mailto:{vapid_email or 'neos@example.com'}"},
        )
        return True
    except Exception as e:
        logger.error("Push notification failed: %s", e)
        return False


async def notify_members(db_session, ecosystem_id, notification_type: str, title: str, body: str, url: str | None = None):
    """Send push notifications to all subscribed members in an ecosystem."""
    from sqlalchemy import select
    from neos_agent.db.models import PushSubscription, Member

    result = await db_session.execute(
        select(PushSubscription)
        .join(Member, PushSubscription.member_id == Member.id)
        .where(
            Member.ecosystem_id == ecosystem_id,
            PushSubscription.enabled.is_(True),
        )
    )
    subscriptions = result.scalars().all()

    sent = 0
    for sub in subscriptions:
        # Check if member wants this notification type
        types = sub.notification_types or {}
        if not types.get(notification_type, True):  # default to True if not set
            continue
        success = await send_push_notification(
            endpoint=sub.endpoint,
            p256dh_key=sub.p256dh_key,
            auth_key=sub.auth_key,
            title=title,
            body=body,
            url=url,
        )
        if success:
            sent += 1

    logger.info("Sent %d/%d push notifications for %s", sent, len(subscriptions), notification_type)
    return sent
