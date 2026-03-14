"""Messaging blueprint with WebSocket and REST endpoints.

WebSocket endpoint for real-time messaging and REST endpoints
for conversation management, message pagination, and member picker.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime

from sanic import Blueprint
from sanic.request import Request
from sanic.response import redirect
from sanic import html as html_response
from sqlalchemy import func, select, and_
from sqlalchemy.orm import selectinload

from neos_agent.auth.middleware import verify_session_cookie
from neos_agent.db.models import (
    AuthSession,
    Conversation,
    ConversationLink,
    ConversationParticipant,
    Member,
    Message,
)
from neos_agent.messaging.connections import connection_manager
from neos_agent.messaging.handlers import (
    handle_message,
    handle_read_receipt,
    handle_typing,
)
from neos_agent.views._rendering import (
    get_selected_ecosystem_ids,
    html_fragment,
    parse_pagination,
    render,
)

logger = logging.getLogger(__name__)

messaging_bp = Blueprint("messaging", url_prefix="/messaging")

# Map of WebSocket message types to handlers
WS_HANDLERS = {
    "message": handle_message,
    "typing": handle_typing,
    "read_receipt": handle_read_receipt,
}


# ===================================================================
# REST endpoints
# ===================================================================


@messaging_bp.get("/")
async def messaging_page(request: Request):
    """GET /messaging -- main messaging page (full HTML with base.html layout)."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return redirect("/auth/login")

    # Check for ?dm= parameter to auto-open/create a DM
    dm_member_id = request.args.get("dm")
    auto_conversation_id = None
    if dm_member_id:
        try:
            target_id = uuid.UUID(dm_member_id)
            async with request.app.ctx.db() as db:
                convo = await _find_or_create_dm(db, member, target_id, request)
                if convo:
                    auto_conversation_id = str(convo.id)
        except (ValueError, Exception):
            logger.debug("Invalid dm parameter: %s", dm_member_id)

    # Check for ?conversation= parameter
    if not auto_conversation_id:
        auto_conversation_id = request.args.get("conversation")

    content = await render(
        "messaging/index.html",
        request=request,
        active_page="messaging",
        auto_conversation_id=auto_conversation_id,
    )
    return html_response(content)


@messaging_bp.get("/conversations")
async def conversation_list(request: Request):
    """GET /messaging/conversations -- conversation list (htmx partial)."""
    member = request.ctx.member
    eco_ids = get_selected_ecosystem_ids(request)

    try:
        async with request.app.ctx.db() as db:
            # Get conversations this member participates in
            participant_subq = (
                select(ConversationParticipant.conversation_id)
                .where(ConversationParticipant.member_id == member.id)
                .subquery()
            )

            stmt = (
                select(Conversation)
                .where(Conversation.id.in_(select(participant_subq)))
            )
            if eco_ids:
                stmt = stmt.where(Conversation.ecosystem_id.in_(eco_ids))

            result = await db.execute(stmt)
            conversations = result.scalars().all()

            # Enrich with last message, unread count, and participant info
            enriched = []
            for convo in conversations:
                # Last message
                last_msg_result = await db.execute(
                    select(Message)
                    .where(
                        Message.conversation_id == convo.id,
                        Message.deleted_at.is_(None),
                    )
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                last_msg = last_msg_result.scalar_one_or_none()

                # Unread count
                part_result = await db.execute(
                    select(ConversationParticipant).where(
                        ConversationParticipant.conversation_id == convo.id,
                        ConversationParticipant.member_id == member.id,
                    )
                )
                participant = part_result.scalar_one_or_none()
                unread_count = 0
                if participant and participant.last_read_at:
                    unread_result = await db.execute(
                        select(func.count()).where(
                            Message.conversation_id == convo.id,
                            Message.created_at > participant.last_read_at,
                            Message.deleted_at.is_(None),
                        )
                    )
                    unread_count = unread_result.scalar() or 0
                elif participant and participant.last_read_at is None:
                    # Never read — all messages are unread
                    unread_result = await db.execute(
                        select(func.count()).where(
                            Message.conversation_id == convo.id,
                            Message.deleted_at.is_(None),
                        )
                    )
                    unread_count = unread_result.scalar() or 0

                # For DMs, get the other participant's name
                display_title = convo.title
                if convo.type == "dm":
                    other_result = await db.execute(
                        select(Member.display_name).join(
                            ConversationParticipant,
                            ConversationParticipant.member_id == Member.id,
                        ).where(
                            ConversationParticipant.conversation_id == convo.id,
                            ConversationParticipant.member_id != member.id,
                        )
                    )
                    other_name = other_result.scalar_one_or_none()
                    display_title = other_name or "Direct Message"

                enriched.append({
                    "conversation": convo,
                    "display_title": display_title,
                    "last_message": last_msg,
                    "unread_count": unread_count,
                    "sort_key": last_msg.created_at if last_msg else convo.created_at,
                })

            # Sort by most recent message
            enriched.sort(key=lambda x: x["sort_key"], reverse=True)

    except Exception:
        logger.exception("Failed to load conversations")
        enriched = []

    fragment = await render(
        "messaging/conversation_list.html",
        request=request,
        conversations=enriched,
    )
    return html_fragment(fragment)


@messaging_bp.post("/conversations")
async def create_conversation(request: Request):
    """POST /messaging/conversations -- create a DM or group conversation."""
    member = request.ctx.member
    eco_ids = get_selected_ecosystem_ids(request)

    try:
        data = request.json or {}
    except Exception:
        data = {}

    conv_type = data.get("type", "dm")
    title = data.get("title")
    member_ids_raw = data.get("member_ids", [])
    link_entity_type = data.get("link_entity_type")
    link_entity_id = data.get("link_entity_id")

    if not member_ids_raw:
        return html_response("<p class='text-red-500'>No members selected</p>", status=400)

    try:
        target_member_ids = [uuid.UUID(mid) for mid in member_ids_raw]
    except (ValueError, TypeError):
        return html_response("<p class='text-red-500'>Invalid member IDs</p>", status=400)

    try:
        async with request.app.ctx.db() as db:
            # Verify all target members are in the same ecosystem
            for mid in target_member_ids:
                target = await db.get(Member, mid)
                if not target or (eco_ids and target.ecosystem_id not in eco_ids):
                    return html_response(
                        f"<p class='text-red-500'>Member not found or not in your ecosystem</p>",
                        status=400,
                    )

            ecosystem_id = eco_ids[0] if eco_ids else member.ecosystem_id

            if conv_type == "dm":
                if len(target_member_ids) != 1:
                    return html_response("<p class='text-red-500'>DM requires exactly 1 member</p>", status=400)
                target_id = target_member_ids[0]

                # Check for existing DM
                existing = await _find_existing_dm(db, member.id, target_id, ecosystem_id)
                if existing:
                    return html_response(
                        f'<div hx-get="/messaging/conversations/{existing.id}" hx-trigger="load" hx-target="#conversation-detail"></div>',
                    )

                # Create new DM
                convo = Conversation(
                    ecosystem_id=ecosystem_id,
                    type="dm",
                    created_by=member.id,
                )
                db.add(convo)
                await db.flush()

                db.add_all([
                    ConversationParticipant(
                        conversation_id=convo.id, member_id=member.id, role="member",
                    ),
                    ConversationParticipant(
                        conversation_id=convo.id, member_id=target_id, role="member",
                    ),
                ])

            else:
                # Group conversation
                if not title:
                    return html_response("<p class='text-red-500'>Group title required</p>", status=400)

                convo = Conversation(
                    ecosystem_id=ecosystem_id,
                    type="group",
                    title=title,
                    created_by=member.id,
                )
                db.add(convo)
                await db.flush()

                # Add creator as owner
                db.add(ConversationParticipant(
                    conversation_id=convo.id, member_id=member.id, role="owner",
                ))
                # Add other members
                for mid in target_member_ids:
                    if mid != member.id:
                        db.add(ConversationParticipant(
                            conversation_id=convo.id, member_id=mid, role="member",
                        ))

                # System message
                db.add(Message(
                    conversation_id=convo.id,
                    sender_id=member.id,
                    content=f"{member.display_name} created this conversation",
                    message_type="system",
                ))

            # Add governance link if provided
            if link_entity_type and link_entity_id:
                try:
                    db.add(ConversationLink(
                        conversation_id=convo.id,
                        entity_type=link_entity_type,
                        entity_id=uuid.UUID(link_entity_id),
                        created_by=member.id,
                    ))
                except (ValueError, TypeError):
                    pass

            await db.commit()

    except Exception:
        logger.exception("Failed to create conversation")
        return html_response("<p class='text-red-500'>Failed to create conversation</p>", status=500)

    return html_response(
        f'<div hx-get="/messaging/conversations/{convo.id}" hx-trigger="load" hx-target="#conversation-detail"></div>',
    )


@messaging_bp.get("/conversations/<conversation_id:uuid>")
async def conversation_detail(request: Request, conversation_id: uuid.UUID):
    """GET /messaging/conversations/{id} -- conversation detail with recent messages."""
    member = request.ctx.member

    try:
        async with request.app.ctx.db() as db:
            # Verify membership
            part_result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            participant = part_result.scalar_one_or_none()
            if not participant:
                return html_response("<p class='text-red-500'>Access denied</p>", status=403)

            # Load conversation
            convo = await db.get(Conversation, conversation_id)
            if not convo:
                return html_response("<p class='text-red-500'>Conversation not found</p>", status=404)

            # Load participants with member info
            parts_result = await db.execute(
                select(ConversationParticipant, Member)
                .join(Member, ConversationParticipant.member_id == Member.id)
                .where(ConversationParticipant.conversation_id == conversation_id)
            )
            participants = [
                {"participant": p, "member": m}
                for p, m in parts_result.all()
            ]

            # Load last 50 messages
            msgs_result = await db.execute(
                select(Message, Member)
                .join(Member, Message.sender_id == Member.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(50)
            )
            messages = [
                {"message": msg, "sender": sender}
                for msg, sender in reversed(msgs_result.all())
            ]

            # Load governance links
            links_result = await db.execute(
                select(ConversationLink).where(
                    ConversationLink.conversation_id == conversation_id
                )
            )
            links = links_result.scalars().all()

            # Get display title for DMs
            display_title = convo.title
            if convo.type == "dm":
                for p in participants:
                    if p["member"].id != member.id:
                        display_title = p["member"].display_name
                        break

            # Update last_read_at
            participant.last_read_at = datetime.utcnow()
            await db.commit()

    except Exception:
        logger.exception("Failed to load conversation detail")
        return html_response("<p class='text-red-500'>Failed to load conversation</p>", status=500)

    fragment = await render(
        "messaging/conversation_detail.html",
        request=request,
        conversation=convo,
        display_title=display_title,
        participants=participants,
        messages=messages,
        links=links,
        is_exited=member.current_status == "exited",
    )
    return html_fragment(fragment)


@messaging_bp.get("/conversations/<conversation_id:uuid>/messages")
async def message_list(request: Request, conversation_id: uuid.UUID):
    """GET /messaging/conversations/{id}/messages -- paginated older messages."""
    member = request.ctx.member
    offset, limit = parse_pagination(request)

    try:
        async with request.app.ctx.db() as db:
            # Verify membership
            part_result = await db.execute(
                select(ConversationParticipant.id).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            if not part_result.scalar_one_or_none():
                return html_response("", status=403)

            # Paginated messages
            msgs_result = await db.execute(
                select(Message, Member)
                .join(Member, Message.sender_id == Member.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            messages = [
                {"message": msg, "sender": sender}
                for msg, sender in reversed(msgs_result.all())
            ]

    except Exception:
        logger.exception("Failed to load messages")
        return html_response("", status=500)

    fragment = await render(
        "messaging/message_list.html",
        request=request,
        messages=messages,
    )
    return html_fragment(fragment)


@messaging_bp.post("/conversations/<conversation_id:uuid>/messages")
async def send_message_rest(request: Request, conversation_id: uuid.UUID):
    """POST /messaging/conversations/{id}/messages -- send message (REST fallback)."""
    member = request.ctx.member

    try:
        data = request.json or {}
    except Exception:
        data = {}

    content = data.get("content", "").strip()
    if not content:
        # Try form data
        content = (request.form.get("content") or "").strip()

    if not content:
        return html_response("<p class='text-red-500'>Message cannot be empty</p>", status=400)

    if len(content) > 10_000:
        return html_response("<p class='text-red-500'>Message too long</p>", status=400)

    try:
        async with request.app.ctx.db() as db:
            # Verify membership
            part_result = await db.execute(
                select(ConversationParticipant.id).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            if not part_result.scalar_one_or_none():
                return html_response("<p class='text-red-500'>Access denied</p>", status=403)

            if member.current_status == "exited":
                return html_response("<p class='text-red-500'>You have exited this ecosystem</p>", status=403)

            msg = Message(
                conversation_id=conversation_id,
                sender_id=member.id,
                content=content,
                message_type="text",
            )
            db.add(msg)
            await db.commit()
            await db.refresh(msg)

            # Broadcast via WebSocket
            participant_ids_result = await db.execute(
                select(ConversationParticipant.member_id).where(
                    ConversationParticipant.conversation_id == conversation_id
                )
            )
            participant_ids = list(participant_ids_result.scalars().all())

            payload = {
                "type": "message",
                "data": {
                    "id": str(msg.id),
                    "conversation_id": str(conversation_id),
                    "sender_id": str(member.id),
                    "sender_name": member.display_name,
                    "content": msg.content,
                    "message_type": "text",
                    "created_at": msg.created_at.isoformat(),
                },
            }
            await connection_manager.broadcast_to_participants(
                participant_ids, payload, exclude_member_id=None,
            )

    except Exception:
        logger.exception("Failed to send message")
        return html_response("<p class='text-red-500'>Failed to send</p>", status=500)

    # Return the new message as an HTML fragment
    fragment = await render(
        "messaging/message_list.html",
        request=request,
        messages=[{"message": msg, "sender": member}],
    )
    return html_fragment(fragment)


@messaging_bp.put("/conversations/<conversation_id:uuid>/messages/<message_id:uuid>")
async def edit_message(request: Request, conversation_id: uuid.UUID, message_id: uuid.UUID):
    """PUT /messaging/conversations/{id}/messages/{msg_id} -- edit own message."""
    member = request.ctx.member

    try:
        data = request.json or {}
    except Exception:
        data = {}

    new_content = data.get("content", "").strip()
    if not new_content:
        return html_response("<p class='text-red-500'>Content required</p>", status=400)

    try:
        async with request.app.ctx.db() as db:
            msg = await db.get(Message, message_id)
            if not msg or msg.conversation_id != conversation_id:
                return html_response("<p class='text-red-500'>Not found</p>", status=404)
            if msg.sender_id != member.id:
                return html_response("<p class='text-red-500'>Can only edit own messages</p>", status=403)

            msg.content = new_content
            msg.edited_at = datetime.utcnow()
            await db.commit()

            # Broadcast edit event
            participant_ids_result = await db.execute(
                select(ConversationParticipant.member_id).where(
                    ConversationParticipant.conversation_id == conversation_id
                )
            )
            participant_ids = list(participant_ids_result.scalars().all())
            await connection_manager.broadcast_to_participants(
                participant_ids,
                {
                    "type": "message_edited",
                    "data": {
                        "id": str(msg.id),
                        "conversation_id": str(conversation_id),
                        "content": new_content,
                        "edited_at": msg.edited_at.isoformat(),
                    },
                },
            )

    except Exception:
        logger.exception("Failed to edit message")
        return html_response("<p class='text-red-500'>Failed to edit</p>", status=500)

    return html_response("", status=200)


@messaging_bp.delete("/conversations/<conversation_id:uuid>/messages/<message_id:uuid>")
async def delete_message(request: Request, conversation_id: uuid.UUID, message_id: uuid.UUID):
    """DELETE /messaging/conversations/{id}/messages/{msg_id} -- soft-delete own message."""
    member = request.ctx.member

    try:
        async with request.app.ctx.db() as db:
            msg = await db.get(Message, message_id)
            if not msg or msg.conversation_id != conversation_id:
                return html_response("", status=404)
            if msg.sender_id != member.id:
                return html_response("", status=403)

            msg.deleted_at = datetime.utcnow()
            await db.commit()

            # Broadcast delete event
            participant_ids_result = await db.execute(
                select(ConversationParticipant.member_id).where(
                    ConversationParticipant.conversation_id == conversation_id
                )
            )
            participant_ids = list(participant_ids_result.scalars().all())
            await connection_manager.broadcast_to_participants(
                participant_ids,
                {
                    "type": "message_deleted",
                    "data": {
                        "id": str(msg.id),
                        "conversation_id": str(conversation_id),
                    },
                },
            )

    except Exception:
        logger.exception("Failed to delete message")
        return html_response("", status=500)

    return html_response(
        '<p class="text-gray-400 italic text-sm">This message was deleted</p>',
    )


@messaging_bp.post("/conversations/<conversation_id:uuid>/participants")
async def add_participant(request: Request, conversation_id: uuid.UUID):
    """POST /messaging/conversations/{id}/participants -- add member (group only)."""
    member = request.ctx.member

    try:
        data = request.json or {}
    except Exception:
        data = {}

    member_id_str = data.get("member_id")
    if not member_id_str:
        return html_response("<p class='text-red-500'>member_id required</p>", status=400)

    try:
        target_id = uuid.UUID(member_id_str)
    except ValueError:
        return html_response("<p class='text-red-500'>Invalid member_id</p>", status=400)

    try:
        async with request.app.ctx.db() as db:
            convo = await db.get(Conversation, conversation_id)
            if not convo:
                return html_response("", status=404)
            if convo.type == "dm":
                return html_response("<p class='text-red-500'>Cannot add members to DM</p>", status=400)

            # Verify requester is participant
            part_result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            if not part_result.scalar_one_or_none():
                return html_response("", status=403)

            # Verify target member exists in same ecosystem
            target = await db.get(Member, target_id)
            if not target or target.ecosystem_id != convo.ecosystem_id:
                return html_response("<p class='text-red-500'>Member not in ecosystem</p>", status=400)

            # Check not already a participant
            existing = await db.execute(
                select(ConversationParticipant.id).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == target_id,
                )
            )
            if existing.scalar_one_or_none():
                return html_response("<p class='text-yellow-500'>Already a member</p>", status=200)

            db.add(ConversationParticipant(
                conversation_id=conversation_id, member_id=target_id, role="member",
            ))
            db.add(Message(
                conversation_id=conversation_id,
                sender_id=member.id,
                content=f"{member.display_name} added {target.display_name}",
                message_type="system",
            ))
            await db.commit()

    except Exception:
        logger.exception("Failed to add participant")
        return html_response("", status=500)

    return html_response("", status=200)


@messaging_bp.delete("/conversations/<conversation_id:uuid>/participants/<target_member_id:uuid>")
async def remove_participant(request: Request, conversation_id: uuid.UUID, target_member_id: uuid.UUID):
    """DELETE /messaging/conversations/{id}/participants/{mid} -- remove or leave."""
    member = request.ctx.member
    is_self = target_member_id == member.id

    try:
        async with request.app.ctx.db() as db:
            convo = await db.get(Conversation, conversation_id)
            if not convo or convo.type == "dm":
                return html_response("", status=400)

            # Verify requester is participant
            requester_result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            requester_part = requester_result.scalar_one_or_none()
            if not requester_part:
                return html_response("", status=403)

            if not is_self and requester_part.role not in ("owner", "admin"):
                return html_response("<p class='text-red-500'>Not authorized</p>", status=403)

            # Remove target participant
            target_result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == target_member_id,
                )
            )
            target_part = target_result.scalar_one_or_none()
            if not target_part:
                return html_response("", status=404)

            target_member = await db.get(Member, target_member_id)
            await db.delete(target_part)

            # Owner succession if owner leaves
            if is_self and requester_part.role == "owner":
                # Find next admin, then oldest member
                next_owner_result = await db.execute(
                    select(ConversationParticipant)
                    .where(
                        ConversationParticipant.conversation_id == conversation_id,
                        ConversationParticipant.member_id != member.id,
                    )
                    .order_by(
                        # Prefer admins first, then by join date
                        ConversationParticipant.role.asc(),
                        ConversationParticipant.joined_at.asc(),
                    )
                    .limit(1)
                )
                next_owner = next_owner_result.scalar_one_or_none()
                if next_owner:
                    next_owner.role = "owner"

            action = "left" if is_self else f"was removed by {member.display_name}"
            db.add(Message(
                conversation_id=conversation_id,
                sender_id=member.id,
                content=f"{target_member.display_name if target_member else 'Member'} {action}",
                message_type="system",
            ))
            await db.commit()

    except Exception:
        logger.exception("Failed to remove participant")
        return html_response("", status=500)

    return html_response("", status=200)


@messaging_bp.post("/conversations/<conversation_id:uuid>/read")
async def mark_read(request: Request, conversation_id: uuid.UUID):
    """POST /messaging/conversations/{id}/read -- mark conversation as read."""
    member = request.ctx.member

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            participant = result.scalar_one_or_none()
            if participant:
                participant.last_read_at = datetime.utcnow()
                await db.commit()
    except Exception:
        logger.debug("Failed to mark read")

    return html_response("", status=200)


@messaging_bp.post("/conversations/<conversation_id:uuid>/link")
async def link_entity(request: Request, conversation_id: uuid.UUID):
    """POST /messaging/conversations/{id}/link -- link a governance entity."""
    member = request.ctx.member

    try:
        data = request.json or {}
    except Exception:
        data = {}

    entity_type = data.get("entity_type")
    entity_id_str = data.get("entity_id")

    if not entity_type or not entity_id_str:
        return html_response("<p class='text-red-500'>entity_type and entity_id required</p>", status=400)

    try:
        entity_id = uuid.UUID(entity_id_str)
    except ValueError:
        return html_response("<p class='text-red-500'>Invalid entity_id</p>", status=400)

    try:
        async with request.app.ctx.db() as db:
            # Verify membership
            part_result = await db.execute(
                select(ConversationParticipant.id).where(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.member_id == member.id,
                )
            )
            if not part_result.scalar_one_or_none():
                return html_response("", status=403)

            # Check for duplicate link
            existing = await db.execute(
                select(ConversationLink.id).where(
                    ConversationLink.conversation_id == conversation_id,
                    ConversationLink.entity_type == entity_type,
                    ConversationLink.entity_id == entity_id,
                )
            )
            if existing.scalar_one_or_none():
                return html_response("<p class='text-yellow-500'>Already linked</p>", status=200)

            db.add(ConversationLink(
                conversation_id=conversation_id,
                entity_type=entity_type,
                entity_id=entity_id,
                created_by=member.id,
            ))
            db.add(Message(
                conversation_id=conversation_id,
                sender_id=member.id,
                content=f"{member.display_name} linked a {entity_type}",
                message_type="governance_link",
                message_metadata={
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                },
            ))
            await db.commit()

    except Exception:
        logger.exception("Failed to link entity")
        return html_response("", status=500)

    return html_response("", status=200)


@messaging_bp.get("/members")
async def member_picker(request: Request):
    """GET /messaging/members -- member picker filtered by ecosystem."""
    member = request.ctx.member
    eco_ids = get_selected_ecosystem_ids(request)
    query = request.args.get("q", "").strip()

    try:
        async with request.app.ctx.db() as db:
            stmt = (
                select(Member)
                .where(
                    Member.id != member.id,
                    Member.current_status == "active",
                )
                .order_by(Member.display_name.asc())
            )
            if eco_ids:
                stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))
            if query:
                stmt = stmt.where(Member.display_name.ilike(f"%{query}%"))
            stmt = stmt.limit(50)

            result = await db.execute(stmt)
            members = result.scalars().all()

    except Exception:
        logger.exception("Failed to load member picker")
        members = []

    fragment = await render(
        "messaging/member_picker.html",
        request=request,
        members=members,
    )
    return html_fragment(fragment)


@messaging_bp.get("/unread-count")
async def unread_count(request: Request):
    """GET /messaging/unread-count -- total unread messages for badge."""
    member = request.ctx.member
    total = 0

    try:
        async with request.app.ctx.db() as db:
            # Get all conversations this member is in
            parts_result = await db.execute(
                select(ConversationParticipant).where(
                    ConversationParticipant.member_id == member.id
                )
            )
            participants = parts_result.scalars().all()

            for part in participants:
                if part.last_read_at:
                    count_result = await db.execute(
                        select(func.count()).where(
                            Message.conversation_id == part.conversation_id,
                            Message.created_at > part.last_read_at,
                            Message.deleted_at.is_(None),
                        )
                    )
                else:
                    count_result = await db.execute(
                        select(func.count()).where(
                            Message.conversation_id == part.conversation_id,
                            Message.deleted_at.is_(None),
                        )
                    )
                total += count_result.scalar() or 0

    except Exception:
        logger.debug("Failed to get unread count")

    if total > 0:
        return html_response(
            f'<span class="bg-red-500 text-white text-xs font-bold rounded-full px-1.5 py-0.5 ml-1">{total}</span>',
        )
    return html_response("")


@messaging_bp.get("/search")
async def search_messages(request: Request):
    """GET /messaging/search?q=... -- search messages across conversations."""
    member = request.ctx.member
    query = request.args.get("q", "").strip()

    if not query or len(query) < 2:
        return html_fragment('<div class="p-4 text-sm text-neos-muted text-center">Type at least 2 characters to search</div>')

    try:
        async with request.app.ctx.db() as db:
            # Get conversation IDs this member participates in
            participant_subq = (
                select(ConversationParticipant.conversation_id)
                .where(ConversationParticipant.member_id == member.id)
                .subquery()
            )

            # Search messages with ILIKE
            msgs_result = await db.execute(
                select(Message, Member, Conversation)
                .join(Member, Message.sender_id == Member.id)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(
                    Message.conversation_id.in_(select(participant_subq)),
                    Message.content.ilike(f"%{query}%"),
                    Message.deleted_at.is_(None),
                    Message.message_type.in_(["text", "governance_link"]),
                )
                .order_by(Message.created_at.desc())
                .limit(20)
            )
            results = [
                {"message": msg, "sender": sender, "conversation": convo}
                for msg, sender, convo in msgs_result.all()
            ]

    except Exception:
        logger.exception("Failed to search messages")
        results = []

    fragment = await render(
        "messaging/search_results.html",
        request=request,
        results=results,
        query=query,
    )
    return html_fragment(fragment)


# ===================================================================
# WebSocket endpoint
# ===================================================================


@messaging_bp.websocket("/ws")
async def messaging_ws(request: Request, ws):
    """Authenticated WebSocket endpoint for real-time messaging."""
    app = request.app
    settings = app.ctx.settings

    cookie = request.cookies.get("neos_session")
    if not cookie:
        await ws.close(code=4001, reason="Authentication required")
        return

    session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
    if not session_id:
        await ws.close(code=4001, reason="Invalid session")
        return

    member = None
    try:
        async with app.ctx.db() as db:
            result = await db.execute(
                select(AuthSession).where(
                    AuthSession.id == uuid.UUID(session_id),
                    AuthSession.expires_at > datetime.utcnow(),
                )
            )
            auth_session = result.scalar_one_or_none()
            if not auth_session:
                await ws.close(code=4001, reason="Session expired")
                return
            member = await db.get(Member, auth_session.member_id)
            if not member:
                await ws.close(code=4001, reason="Member not found")
                return
    except Exception:
        logger.exception("WebSocket auth error")
        await ws.close(code=4001, reason="Authentication error")
        return

    connection_manager.register(member.id, ws)
    logger.info("WebSocket connected: %s (%s)", member.display_name, member.id)

    async def _keepalive():
        try:
            while True:
                await asyncio.sleep(30)
                await ws.ping()
        except Exception:
            pass

    keepalive_task = asyncio.create_task(_keepalive())

    try:
        async for raw in ws:
            try:
                frame = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                await ws.send('{"type":"error","data":{"message":"Invalid JSON"}}')
                continue

            msg_type = frame.get("type")
            msg_data = frame.get("data", {})

            handler = WS_HANDLERS.get(msg_type)
            if handler:
                try:
                    await handler(ws, member, msg_data, app)
                except Exception:
                    logger.exception("Handler error for type=%s", msg_type)
                    await ws.send('{"type":"error","data":{"message":"Internal error"}}')
            else:
                await ws.send('{"type":"error","data":{"message":"Unknown message type"}}')
    except Exception:
        logger.debug("WebSocket disconnected: %s", member.id)
    finally:
        keepalive_task.cancel()
        connection_manager.unregister(member.id, ws)
        logger.info("WebSocket disconnected: %s (%s)", member.display_name, member.id)


# ===================================================================
# Helper functions
# ===================================================================


async def _find_existing_dm(db, member_id, target_id, ecosystem_id):
    """Find an existing DM conversation between two members in an ecosystem."""
    # Get all DM conversations in this ecosystem
    dms_result = await db.execute(
        select(Conversation).where(
            Conversation.ecosystem_id == ecosystem_id,
            Conversation.type == "dm",
        )
    )
    for dm in dms_result.scalars().all():
        parts_result = await db.execute(
            select(ConversationParticipant.member_id).where(
                ConversationParticipant.conversation_id == dm.id
            )
        )
        member_ids = set(parts_result.scalars().all())
        if member_ids == {member_id, target_id}:
            return dm
    return None


async def _find_or_create_dm(db, member, target_id, request):
    """Find existing DM or create new one between member and target."""
    eco_ids = get_selected_ecosystem_ids(request)
    ecosystem_id = eco_ids[0] if eco_ids else member.ecosystem_id

    existing = await _find_existing_dm(db, member.id, target_id, ecosystem_id)
    if existing:
        return existing

    # Verify target is in ecosystem
    target = await db.get(Member, target_id)
    if not target or (eco_ids and target.ecosystem_id not in eco_ids):
        return None

    convo = Conversation(
        ecosystem_id=ecosystem_id,
        type="dm",
        created_by=member.id,
    )
    db.add(convo)
    await db.flush()

    db.add_all([
        ConversationParticipant(
            conversation_id=convo.id, member_id=member.id, role="member",
        ),
        ConversationParticipant(
            conversation_id=convo.id, member_id=target_id, role="member",
        ),
    ])
    await db.commit()
    return convo


