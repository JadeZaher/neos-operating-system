from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from neos_agent.db.models import DecisionSemanticTag


async def _get_first_ecosystem_id(
    db: AsyncSession, ecosystem_ids: list | None = None
) -> uuid.UUID | None:
    """Return the first ecosystem ID from the caller's scope.

    If no scope is provided, fall back to looking up the lone active ecosystem.
    Returns None only when no scope is given AND the DB doesn't contain
    exactly one ecosystem.
    """
    from neos_agent.db.models import Ecosystem
    
    if ecosystem_ids:
        return ecosystem_ids[0]
    stmt = select(Ecosystem.id).limit(2)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if len(rows) == 1:
        return rows[0]
    return None



async def create_decisionsemantictag(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """Create a new DecisionSemanticTag record."""
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    
    # Validate required fields
    required = []
    for field in required:
        if field not in args or not args[field]:
            return {"success": False, "error": f"'{field}' is required."}
    
    # Create instance
    instance = DecisionSemanticTag(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        **{k: v for k, v in args.items() if k in required}
    )
    db.add(instance)
    await db.flush()
    
    return {
        "success": True,
        "data": {
            "id": str(instance.id),
            "message": "DecisionSemanticTag created successfully.",
        },
    }



async def get_decisionsemantictag_by_id(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """Get DecisionSemanticTag by internal UUID id."""
    id_str = args.get("id", "")
    if not id_str:
        return {"success": False, "error": "id is required."}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {"success": False, "error": "Invalid UUID format for id."}
    
    stmt = select(DecisionSemanticTag).where(DecisionSemanticTag.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where(DecisionSemanticTag.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {"success": False, "error": f"DecisionSemanticTag not found."}
    
    # Convert to dict (simplified - could use serializer)
    data = {
        "id": str(instance.id),
        "ecosystem_id": str(instance.ecosystem_id),
    }
    # Add other fields dynamically
    mapper = sqlalchemy_inspect(DecisionSemanticTag)
    for column in mapper.columns:
        if column.key not in ("id", "ecosystem_id"):
            value = getattr(instance, column.key)
            if isinstance(value, (date, datetime)):
                data[column.key] = str(value)
            elif isinstance(value, uuid.UUID):
                data[column.key] = str(value)
            else:
                data[column.key] = value
    
    return {"success": True, "data": data}



async def get_decisionsemantictag_by_decision_record_id(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """Get DecisionSemanticTag by business key decision_record_id."""
    key_value = args.get("decision_record_id", "")
    if not key_value:
        return {"success": False, "error": "decision_record_id is required."}
    
    stmt = select(DecisionSemanticTag).where(DecisionSemanticTag.decision_record_id == key_value)
    if ecosystem_ids:
        stmt = stmt.where(DecisionSemanticTag.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {"success": False, "error": f"DecisionSemanticTag with decision_record_id='{key_value}' not found."}
    
    # Convert to dict
    data = {
        "id": str(instance.id),
        "decision_record_id": getattr(instance, business_key),
        "ecosystem_id": str(instance.ecosystem_id),
    }
    
    return {"success": True, "data": data}



async def list_decisionsemantictag(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """List DecisionSemanticTag records with optional filtering."""
    stmt = select(DecisionSemanticTag)
    
    if ecosystem_ids:
        stmt = stmt.where(DecisionSemanticTag.ecosystem_id.in_(ecosystem_ids))
    
    # Apply filters from args (simple equality filters)
    mapper = sqlalchemy_inspect(DecisionSemanticTag)
    for column in mapper.columns:
        if column.key in args and args[column.key]:
            stmt = stmt.where(getattr(DecisionSemanticTag, column.key) == args[column.key])
    
    # Apply limit
    limit = args.get("limit", 50)
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    instances = result.scalars().all()
    
    # Convert to list of dicts
    items = []
    for instance in instances:
        data = {
            "id": str(instance.id),
            "ecosystem_id": str(instance.ecosystem_id),
        }
        for column in mapper.columns:
            if column.key not in ("id", "ecosystem_id"):
                value = getattr(instance, column.key)
                if isinstance(value, (date, datetime)):
                    data[column.key] = str(value)
                elif isinstance(value, uuid.UUID):
                    data[column.key] = str(value)
                else:
                    data[column.key] = value
        items.append(data)
    
    return {
        "success": True,
        "data": {
            "items": items,
            "count": len(items),
        },
    }



async def update_decisionsemantictag(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """Update DecisionSemanticTag by id."""
    id_str = args.get("id", "")
    if not id_str:
        return {"success": False, "error": "id is required."}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {"success": False, "error": "Invalid UUID format for id."}
    
    stmt = select(DecisionSemanticTag).where(DecisionSemanticTag.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where(DecisionSemanticTag.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {"success": False, "error": f"DecisionSemanticTag not found."}
    
    # Update fields from args (excluding id and ecosystem_id)
    for key, value in args.items():
        if key not in ("id", "ecosystem_id") and hasattr(instance, key):
            setattr(instance, key, value)
    
    await db.flush()
    
    return {
        "success": True,
        "data": {
            "id": str(instance.id),
            "message": "DecisionSemanticTag updated successfully.",
        },
    }



async def delete_decisionsemantictag(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    """Delete DecisionSemanticTag by id."""
    id_str = args.get("id", "")
    if not id_str:
        return {"success": False, "error": "id is required."}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {"success": False, "error": "Invalid UUID format for id."}
    
    stmt = select(DecisionSemanticTag).where(DecisionSemanticTag.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where(DecisionSemanticTag.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {"success": False, "error": f"DecisionSemanticTag not found."}
    
    await db.delete(instance)
    await db.flush()
    
    return {
        "success": True,
        "data": {
            "id": str(id_uuid),
            "message": "DecisionSemanticTag deleted successfully.",
        },
    }
