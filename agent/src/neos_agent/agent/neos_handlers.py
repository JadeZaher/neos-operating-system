"""NEOS-specific handlers for the generic pipeline framework.

This module provides domain-specific operation handlers for NEOS governance
operations that work with the generic pipeline executor.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from neos_agent.db.models import (
    Ecosystem,
    Member,
    Domain,
    Agreement,
    Proposal,
)
from neos_agent.skills.pipeline_executor import ValidationError


async def resolve_ecosystem_handler(args: dict, context: dict, db: AsyncSession) -> dict:
    """Resolve ecosystem by ID or name."""
    arg_name = args.get("arg", "ecosystem")
    identifier = context.get(arg_name) or args.get("arg_value")
    
    if not identifier:
        raise ValidationError("ecosystem", "Ecosystem identifier is required")
    
    # Try UUID first
    try:
        eco_uuid = uuid.UUID(identifier)
        stmt = select(Ecosystem).where(Ecosystem.id == eco_uuid)
    except ValueError:
        # Try name
        stmt = select(Ecosystem).where(
            func.lower(Ecosystem.name) == identifier.lower()
        )
    
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids")
    
    if ecosystem_ids:
        stmt = stmt.where(Ecosystem.id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    ecosystem = result.scalars().first()
    
    if ecosystem is None:
        raise ValidationError("ecosystem", f"Ecosystem '{identifier}' not found")
    
    return {"ecosystem_id": ecosystem.id, "ecosystem": ecosystem}


async def resolve_member_handler(args: dict, context: dict, db: AsyncSession) -> dict:
    """Resolve member by member_id or display_name."""
    arg_name = args.get("arg", "member")
    identifier = context.get(arg_name) or args.get("arg_value")
    
    if not identifier:
        raise ValidationError("member", "Member identifier is required")
    
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids")
    
    # Try member_id first
    stmt = select(Member).where(
        Member.member_id == identifier,
        Member.current_status == "active",
    )
    
    if ecosystem_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    member = result.scalars().first()
    
    # Try display_name
    if member is None:
        stmt = select(Member).where(
            func.lower(Member.display_name) == identifier.lower(),
            Member.current_status == "active",
        )
        
        if ecosystem_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(ecosystem_ids))
        
        result = await db.execute(stmt)
        member = result.scalars().first()
    
    if member is None:
        raise ValidationError("member", f"Member '{identifier}' not found or not active")
    
    return {"member_id": member.id, "member": member}


async def resolve_domain_handler(args: dict, context: dict, db: AsyncSession) -> dict:
    """Resolve domain by domain_id or name."""
    arg_name = args.get("arg", "domain")
    identifier = context.get(arg_name) or args.get("arg_value")
    
    if not identifier:
        raise ValidationError("domain", "Domain identifier is required")
    
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids")
    
    # Try exact match first
    stmt = select(Domain).where(
        func.lower(Domain.domain_id) == identifier.lower()
    )
    
    if ecosystem_ids:
        stmt = stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    domain = result.scalars().first()
    
    # Try partial match
    if domain is None:
        stmt = select(Domain).where(
            Domain.domain_id.ilike(f"%{identifier}%")
        )
        
        if ecosystem_ids:
            stmt = stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
        
        result = await db.execute(stmt)
        domain = result.scalars().first()
    
    if domain is None:
        raise ValidationError("domain", f"Domain '{identifier}' not found")
    
    return {"domain_id": domain.id, "domain": domain}


async def create_member_handler(args: dict, context: dict, db: AsyncSession) -> dict:
    """Create a new member."""
    # Access scope from context (set by executor)
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids", [])
    
    # Get or resolve ecosystem_id
    ecosystem_id = context.get("ecosystem_id")
    if not ecosystem_id and ecosystem_ids:
        ecosystem_id = ecosystem_ids[0]
    
    if not ecosystem_id:
        raise ValidationError("ecosystem_id", "No ecosystem context available")
    
    # Create member
    member = Member(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem_id,
        user_id=uuid.uuid4(),  # In real scenario, this would come from user context
        member_id=context.get("generated_key") or args.get("member_id"),
        display_name=context.get("display_name") or args.get("display_name"),
        current_status=args.get("defaults", {}).get("current_status", "prospective"),
    )
    
    db.add(member)
    await db.flush()
    
    return {
        "id": str(member.id),
        "member_id": member.member_id,
        "display_name": member.display_name,
        "current_status": member.current_status,
    }


async def create_agreement_handler(args: dict, context: dict, db: AsyncSession) -> dict:
    """Create a new agreement."""
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids")
    
    # Get or resolve ecosystem_id
    ecosystem_id = context.get("ecosystem_id")
    if not ecosystem_id and ecosystem_ids:
        ecosystem_id = ecosystem_ids[0]
    
    if not ecosystem_id:
        raise ValidationError("ecosystem_id", "No ecosystem context available")
    
    # Create agreement
    agreement = Agreement(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem_id,
        agreement_id=context.get("generated_key") or context.get("agreement_id"),
        type=context.get("type") or args.get("type"),
        title=context.get("title") or args.get("title"),
        version="0.1",
        status="draft",
        proposer=context.get("proposer") or args.get("proposer"),
        domain=context.get("domain") or args.get("domain"),
        text=context.get("text") or args.get("text"),
        created_date=date.today(),
    )
    
    db.add(agreement)
    await db.flush()
    
    return {
        "id": str(agreement.id),
        "agreement_id": agreement.agreement_id,
        "title": agreement.title,
        "status": agreement.status,
    }


# Handler registry for NEOS operations
NEOS_HANDLERS = {
    "resolve": resolve_ecosystem_handler,  # Default resolve handler
    "create": create_member_handler,  # Default create handler
}
