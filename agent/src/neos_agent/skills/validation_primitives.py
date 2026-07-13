"""Primitive validation rules for skill pipeline execution.

This module provides common validation units that can be composed into
skill pipelines, including member resolution, ecosystem validation,
date parsing, and foreign key resolution.
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


# ============================================================================
# Validation Primitives
# ============================================================================

class ValidationError(Exception):
    """Raised when a validation rule fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_required(args: dict, fields: list[str]) -> None:
    """Validate that required fields are present and non-empty.
    
    Args:
        args: Input arguments dictionary
        fields: List of field names that must be present and non-empty
        
    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in fields:
        if field not in args or not args[field]:
            raise ValidationError(field, f"'{field}' is required")


def validate_optional(args: dict, fields: list[str]) -> None:
    """Validate that optional fields, if present, are non-empty.
    
    Args:
        args: Input arguments dictionary
        fields: List of field names that may be present
        
    Raises:
        ValidationError: If any optional field is present but empty
    """
    for field in fields:
        if field in args and not args[field]:
            raise ValidationError(field, f"'{field}' must not be empty if provided")


def validate_enum(args: dict, field: str, values: list[str]) -> None:
    """Validate that a field value is in the allowed enum values.
    
    Args:
        args: Input arguments dictionary
        field: Field name to validate
        values: List of allowed values
        
    Raises:
        ValidationError: If field value is not in allowed values
    """
    if field not in args:
        return
    
    value = args[field]
    if value not in values:
        raise ValidationError(
            field,
            f"'{value}' is not valid. Must be one of: {values}"
        )


def validate_format(args: dict, field: str, format_type: str) -> None:
    """Validate that a field matches the expected format.
    
    Args:
        args: Input arguments dictionary
        field: Field name to validate
        format_type: Format type (uuid, email, date, etc.)
        
    Raises:
        ValidationError: If field value does not match format
    """
    if field not in args or not args[field]:
        return
    
    value = args[field]
    
    if format_type == "uuid":
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValidationError(field, f"'{value}' is not a valid UUID")
    
    elif format_type == "email":
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValidationError(field, f"'{value}' is not a valid email")
    
    elif format_type == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValidationError(field, f"'{value}' is not a valid date (use YYYY-MM-DD)")
    
    elif format_type == "datetime":
        try:
            datetime.fromisoformat(value)
        except ValueError:
            raise ValidationError(field, f"'{value}' is not a valid datetime")


# ============================================================================
# Resolution Primitives
# ============================================================================

async def resolve_ecosystem(
    db: AsyncSession,
    identifier: str,
    ecosystem_ids: list | None = None
) -> Ecosystem:
    """Resolve an ecosystem by ID or name.
    
    Args:
        db: Database session
        identifier: Ecosystem ID or name
        ecosystem_ids: Optional scope of allowed ecosystem IDs
        
    Returns:
        Ecosystem instance
        
    Raises:
        ValidationError: If ecosystem not found
    """
    # Try UUID first
    try:
        eco_uuid = uuid.UUID(identifier)
        stmt = select(Ecosystem).where(Ecosystem.id == eco_uuid)
    except ValueError:
        # Try name
        stmt = select(Ecosystem).where(
            func.lower(Ecosystem.name) == identifier.lower()
        )
    
    if ecosystem_ids:
        stmt = stmt.where(Ecosystem.id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    ecosystem = result.scalars().first()
    
    if ecosystem is None:
        raise ValidationError("ecosystem", f"Ecosystem '{identifier}' not found")
    
    return ecosystem


async def resolve_member(
    db: AsyncSession,
    identifier: str,
    ecosystem_ids: list | None = None
) -> Member:
    """Resolve a member by member_id or display_name.
    
    Args:
        db: Database session
        identifier: Member ID or display name
        ecosystem_ids: Optional scope of allowed ecosystem IDs
        
    Returns:
        Member instance
        
    Raises:
        ValidationError: If member not found or not active
    """
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
        raise ValidationError(
            "member",
            f"Member '{identifier}' not found or not active"
        )
    
    return member


async def resolve_domain(
    db: AsyncSession,
    identifier: str,
    ecosystem_ids: list | None = None
) -> Domain:
    """Resolve a domain by domain_id or partial name match.
    
    Args:
        db: Database session
        identifier: Domain ID or name
        ecosystem_ids: Optional scope of allowed ecosystem IDs
        
    Returns:
        Domain instance
        
    Raises:
        ValidationError: If domain not found
    """
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
    
    return domain


async def resolve_agreement(
    db: AsyncSession,
    identifier: str,
    ecosystem_ids: list | None = None
) -> Agreement:
    """Resolve an agreement by agreement_id.
    
    Args:
        db: Database session
        identifier: Agreement business key (agreement_id)
        ecosystem_ids: Optional scope of allowed ecosystem IDs
        
    Returns:
        Agreement instance
        
    Raises:
        ValidationError: If agreement not found
    """
    stmt = select(Agreement).where(
        Agreement.agreement_id == identifier
    )
    
    if ecosystem_ids:
        stmt = stmt.where(Agreement.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    agreement = result.scalars().first()
    
    if agreement is None:
        raise ValidationError(
            "agreement",
            f"Agreement '{identifier}' not found"
        )
    
    return agreement


async def resolve_proposal(
    db: AsyncSession,
    identifier: str,
    ecosystem_ids: list | None = None
) -> Proposal:
    """Resolve a proposal by proposal_id.
    
    Args:
        db: Database session
        identifier: Proposal business key (proposal_id)
        ecosystem_ids: Optional scope of allowed ecosystem IDs
        
    Returns:
        Proposal instance
        
    Raises:
        ValidationError: If proposal not found
    """
    stmt = select(Proposal).where(
        Proposal.proposal_id == identifier
    )
    
    if ecosystem_ids:
        stmt = stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    proposal = result.scalars().first()
    
    if proposal is None:
        raise ValidationError(
            "proposal",
            f"Proposal '{identifier}' not found"
        )
    
    return proposal


# ============================================================================
# Business Key Generation
# ============================================================================

async def generate_business_key(
    db: AsyncSession,
    prefix: str,
    ecosystem_id: uuid.UUID,
    pattern: str | None = None
) -> str:
    """Generate a unique business key for a record.
    
    Args:
        db: Database session
        prefix: Key prefix (e.g., 'AGR', 'PROP')
        ecosystem_id: Ecosystem UUID
        pattern: Optional pattern for key generation
        
    Returns:
        Generated business key string
    """
    from datetime import date
    
    year = date.today().year
    
    if pattern:
        # Custom pattern (e.g., "AGR-{domain}-{year}-{seq}")
        # For now, use simple incrementing sequence
        pass
    
    # Simple pattern: PREFIX-YEAR-NNN
    # This is a simplified version - in production you'd query the specific table
    # to get the last sequence number for that prefix/year/ecosystem
    
    # For now, generate a simple UUID-based key
    # In production, this should query the actual table for the last sequence
    return f"{prefix}-{year}-{uuid.uuid4().hex[:8].upper()}"


# ============================================================================
# Transition Validation
# ============================================================================

def validate_transition(
    current_status: str,
    new_status: str,
    valid_transitions: dict[str, list[str]]
) -> None:
    """Validate that a status transition is allowed.
    
    Args:
        current_status: Current status value
        new_status: Desired new status
        valid_transitions: Dictionary mapping current status to allowed next statuses
        
    Raises:
        ValidationError: If transition is not allowed
    """
    allowed = valid_transitions.get(current_status, [])
    
    if new_status not in allowed:
        raise ValidationError(
            "status",
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Valid transitions from '{current_status}': {allowed}"
        )


# ============================================================================
# Date Parsing Helpers
# ============================================================================

def parse_date(value: str) -> date:
    """Parse a date string in ISO format.
    
    Args:
        value: Date string in YYYY-MM-DD format
        
    Returns:
        date object
        
    Raises:
        ValidationError: If date is invalid
    """
    try:
        return date.fromisoformat(value)
    except ValueError as e:
        raise ValidationError("date", f"Invalid date format: {e}")


def parse_datetime(value: str) -> datetime:
    """Parse a datetime string in ISO format.
    
    Args:
        value: Datetime string in ISO format
        
    Returns:
        datetime object
        
    Raises:
        ValidationError: If datetime is invalid
    """
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        raise ValidationError("datetime", f"Invalid datetime format: {e}")
