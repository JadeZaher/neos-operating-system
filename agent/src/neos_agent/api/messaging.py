"""JSON API blueprint for messaging.

Blueprint: messaging_api_bp, url_prefix="/api/v1/messaging"

Provides REST endpoints for initial data loading of conversations and messages.
Real-time delivery is handled by the WebSocket at /messaging/ws.
Returns JSON responses only.
"""

from __future__ import annotations

import uuid

from sanic import Blueprint, json
from sanic.request import Request

from neos_agent.api.errors import ApiError
from neos_agent.api.guards import authenticated, caller_user_id
from neos_agent.api.helpers import get_ecosystem_ids, parse_pagination
from neos_agent.api.schemas.messaging import CreateConversationRequest
from neos_agent.services import member_messaging as messaging


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

messaging_api_bp = Blueprint("messaging_api", url_prefix="/api/v1/messaging")


@messaging_api_bp.get("/conversations")
@authenticated
async def list_conversations(request: Request):
    async with request.app.ctx.db() as session:
        rows = await messaging.list_threads(session, caller_user_id(request), get_ecosystem_ids(request), limit=None)
        return json({"conversations": rows})


@messaging_api_bp.get("/conversations/<conversation_id:uuid>")
@authenticated
async def get_conversation(request: Request, conversation_id: uuid.UUID):
    async with request.app.ctx.db() as session:
        detail = await messaging.read_thread(session, caller_user_id(request), conversation_id)
        await session.commit()
        return json(detail)


@messaging_api_bp.post("/conversations")
@authenticated
async def create_conversation(request: Request):
    try:
        create_req = CreateConversationRequest(**(request.json or {}))
    except Exception as exc:
        raise ApiError(400, f"Invalid request: {exc}") from exc
    eco_ids = get_ecosystem_ids(request)
    async with request.app.ctx.db() as session:
        prepared = await messaging.prepare_thread(session, caller_user_id(request), eco_ids[0] if eco_ids else None,
            create_req.participant_ids, type=create_req.type, title=create_req.title)
        conversation = await messaging.open_thread(session, prepared)
        detail = await messaging.read_thread(session, caller_user_id(request), conversation.id)
        await session.commit()
        return json(detail, status=201)


@messaging_api_bp.post("/conversations/<conversation_id:uuid>/messages")
@authenticated
async def send_message(request: Request, conversation_id: uuid.UUID):
    async with request.app.ctx.db() as session:
        prepared = await messaging.prepare_message(session, caller_user_id(request), conversation_id, (request.json or {}).get("content"))
        result = await messaging.post_message(session, prepared)
        await session.commit()
        await messaging.broadcast_committed(session)
        return json(result, status=201)


@messaging_api_bp.get("/conversations/<conversation_id:uuid>/messages")
@authenticated
async def list_messages(request: Request, conversation_id: uuid.UUID):
    page = parse_pagination(request, default=50)
    async with request.app.ctx.db() as session:
        detail = await messaging.read_thread(session, caller_user_id(request), conversation_id, page=page.page, limit=page.per_page)
        await session.commit()
        return json({"messages": detail["messages"], "total": detail["total_messages"]})


@messaging_api_bp.get("/search")
@authenticated
async def search_messages(request: Request):
    async with request.app.ctx.db() as session:
        messages = await messaging.search_thread_messages(session, caller_user_id(request), get_ecosystem_ids(request), request.args.get("q", ""))
        return json({"messages": messages})


@messaging_api_bp.get("/members")
@authenticated
async def list_members_for_picker(request: Request):
    async with request.app.ctx.db() as session:
        members = await messaging.find_recipients(session, caller_user_id(request), limit=None)
        return json({"members": members})
