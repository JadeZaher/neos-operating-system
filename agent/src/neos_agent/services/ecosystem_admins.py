"""Ecosystem cross-link admins.

Holacracy maps a circle's Lead Link (appointed inward) and Rep Link (elected outward)
onto two designations, `internal` and `external`. There is no owner column on
ecosystems. Seeded founders and `POST /ecosystems` keep `Member.role` at `user`
and record the creator as `profile="co_creator"`, usually also `Domain.steward_id`
on the root domain. That person is the default admin and holds both links until
someone else is assigned.

TODO: the external rep is elected by the ecosystem's own members (Rep Link).
Appointment by an owner or admin is the stand-in. This module does not count votes.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy import select

from neos_agent.api.errors import ApiError
from neos_agent.db.models import Domain, EcosystemAdmin, Member, MemberStatusTransition, User
from neos_agent.db.models._base import GUID
from neos_agent.services import dates

INTERNAL = "internal"
EXTERNAL = "external"
DESIGNATIONS = frozenset({INTERNAL, EXTERNAL})
ADMIN_AUDIT = "ecosystem_admin"
LAST_ADMIN = "LAST_ADMIN"
ADMIN_REQUIRED = "ADMIN_REQUIRED"


@dataclass(frozen=True)
class AdminCandidate:
    id: uuid.UUID
    created_at: dt.datetime | None
    role: str | None
    profile: str | None
    current_status: str | None
    disabled: bool


@dataclass(frozen=True)
class StewardDomain:
    id: uuid.UUID
    steward_id: uuid.UUID | None
    parent_domain_id: uuid.UUID | None
    status: str | None
    created_at: dt.datetime | None


def _when(value) -> dt.datetime:
    if value is None:
        return dt.datetime.min
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime(value.year, value.month, value.day)
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", ""))
    except ValueError:
        return dt.datetime.min


def choose_default_admin(members: list[AdminCandidate], domains: list[StewardDomain]) -> uuid.UUID | None:
    """Who becomes the default admin: owner role, else co_creator, else the lead steward.

    Eligible rows are active and not disabled. Oldest `created_at`, then id, wins a tie.
    A root domain's steward is the lead; a nested domain's steward is used only when no
    root steward qualifies. An ordinary member is not chosen.
    """
    eligible = [member for member in members if member.current_status == "active" and not member.disabled]
    eligible.sort(key=lambda member: (_when(member.created_at), str(member.id)))
    owners = [member for member in eligible if member.role == "owner"]
    if owners:
        return owners[0].id
    creators = [member for member in eligible if member.profile == "co_creator"]
    if creators:
        return creators[0].id
    by_id = {member.id: member for member in eligible}
    active = [domain for domain in domains if domain.status == "active" and domain.steward_id in by_id]

    def _order(domain: StewardDomain):
        return (_when(domain.created_at), str(domain.id))

    roots = sorted((domain for domain in active if domain.parent_domain_id is None), key=_order)
    nested = sorted((domain for domain in active if domain.parent_domain_id is not None), key=_order)
    for domain in (*roots, *nested):
        return domain.steward_id
    return None


def _audit(member_id: uuid.UUID, actor_id: uuid.UUID | None, old: str, new: str) -> MemberStatusTransition:
    return MemberStatusTransition(
        id=uuid.uuid4(), member_id=member_id, date=dates.utc_today(), trigger=ADMIN_AUDIT,
        actor_member_id=actor_id, from_status=old[:50], to_status=new[:50],
    )


async def ensure_default_admin(session, member: Member) -> None:
    """The founding member holds the Lead Link and the Rep Link until others are assigned."""
    for designation in (INTERNAL, EXTERNAL):
        exists = await session.scalar(select(EcosystemAdmin.id).where(
            EcosystemAdmin.ecosystem_id == member.ecosystem_id,
            EcosystemAdmin.member_id == member.id,
            EcosystemAdmin.designation == designation,
        ))
        if exists is not None:
            continue
        session.add(EcosystemAdmin(
            id=uuid.uuid4(), ecosystem_id=member.ecosystem_id, member_id=member.id,
            designation=designation, appointed_by_member_id=member.id,
        ))
        session.add(_audit(member.id, member.id, "none", designation))
    await session.flush()


async def _caller_can_manage(session, caller: Member | None) -> bool:
    if caller is None or caller.current_status != "active":
        return False
    if caller.role == "owner":
        return True
    held = await session.scalar(select(EcosystemAdmin.id).where(
        EcosystemAdmin.ecosystem_id == caller.ecosystem_id, EcosystemAdmin.member_id == caller.id,
    ))
    return held is not None


def _require_manager(caller: Member | None, allowed: bool) -> None:
    if not allowed:
        raise ApiError(403, "Only an owner or an ecosystem admin can change ecosystem admins.", {"code": ADMIN_REQUIRED})


async def _active_target(session, ecosystem_id: uuid.UUID, member_id: uuid.UUID) -> Member:
    member = await session.get(Member, member_id)
    if member is None or member.ecosystem_id != ecosystem_id:
        raise ApiError(404, "Member not found in this ecosystem")
    if member.current_status != "active":
        raise ApiError(409, "Only an active member can be an ecosystem admin.", {"code": "NOT_ACTIVE"})
    user = await session.get(User, member.user_id)
    if user is None or user.disabled_at is not None:
        raise ApiError(409, "That account cannot be an ecosystem admin.", {"code": "NOT_ACTIVE"})
    return member


async def _rows(session, ecosystem_id: uuid.UUID, *, lock: bool = False):
    statement = select(EcosystemAdmin).where(EcosystemAdmin.ecosystem_id == ecosystem_id)
    if lock:
        statement = statement.with_for_update()
    return list((await session.scalars(statement)).all())


def _last_admin_blocked(rows, member_id: uuid.UUID, dropping: set[str]) -> bool:
    """True when this change would leave the ecosystem with no admin."""
    remaining = {
        row.member_id for row in rows
        if not (row.member_id == member_id and row.designation in dropping)
    }
    return not remaining


async def list_admins(session, caller: Member | None, ecosystem_id: uuid.UUID) -> list[dict]:
    _require_manager(caller, await _caller_can_manage(session, caller) and caller.ecosystem_id == ecosystem_id)
    rows = await _rows(session, ecosystem_id)
    names = {}
    grouped: dict[uuid.UUID, dict] = {}
    for row in sorted(rows, key=lambda item: (str(item.member_id), item.designation)):
        if row.member_id not in names:
            member = await session.get(Member, row.member_id)
            names[row.member_id] = member.display_name if member is not None else ""
        entry = grouped.setdefault(row.member_id, {
            "id": str(row.member_id), "display_name": names[row.member_id], "designations": [],
        })
        entry["designations"].append(row.designation)
    return list(grouped.values())


async def grant_admin(session, caller: Member | None, ecosystem_id: uuid.UUID, member_id: uuid.UUID, designation: str) -> str:
    """Add one designation. Returns `created` or `exists`."""
    if caller is None or caller.ecosystem_id != ecosystem_id:
        _require_manager(caller, False)
    _require_manager(caller, await _caller_can_manage(session, caller))
    if designation not in DESIGNATIONS:
        raise ApiError(400, "designation must be 'internal' or 'external'.", {"field": "designation"})
    await _active_target(session, ecosystem_id, member_id)
    existing = await session.scalar(select(EcosystemAdmin.id).where(
        EcosystemAdmin.ecosystem_id == ecosystem_id, EcosystemAdmin.member_id == member_id,
        EcosystemAdmin.designation == designation,
    ))
    if existing is not None:
        return "exists"
    session.add(EcosystemAdmin(
        id=uuid.uuid4(), ecosystem_id=ecosystem_id, member_id=member_id, designation=designation,
        appointed_by_member_id=caller.id,
    ))
    session.add(_audit(member_id, caller.id, "none", designation))
    await session.flush()
    return "created"


async def revoke_admin(session, caller: Member | None, ecosystem_id: uuid.UUID, member_id: uuid.UUID, designation: str) -> None:
    if caller is None or caller.ecosystem_id != ecosystem_id:
        _require_manager(caller, False)
    _require_manager(caller, await _caller_can_manage(session, caller))
    if designation not in DESIGNATIONS:
        raise ApiError(400, "designation must be 'internal' or 'external'.", {"field": "designation"})
    rows = await _rows(session, ecosystem_id, lock=True)
    held = [row for row in rows if row.member_id == member_id and row.designation == designation]
    if not held:
        raise ApiError(404, "That admin designation was not found")
    if _last_admin_blocked(rows, member_id, {designation}):
        raise ApiError(409, "An ecosystem keeps at least one admin.", {"code": LAST_ADMIN})
    await session.delete(held[0])
    session.add(_audit(member_id, caller.id, designation, "none"))
    await session.flush()


async def redesignate_admin(session, caller: Member | None, ecosystem_id: uuid.UUID, member_id: uuid.UUID, designation: str) -> None:
    """Leave this admin holding exactly `designation`. They stay an admin, so the last admin is not removed."""
    if caller is None or caller.ecosystem_id != ecosystem_id:
        _require_manager(caller, False)
    _require_manager(caller, await _caller_can_manage(session, caller))
    if designation not in DESIGNATIONS:
        raise ApiError(400, "designation must be 'internal' or 'external'.", {"field": "designation"})
    await _active_target(session, ecosystem_id, member_id)
    rows = await _rows(session, ecosystem_id, lock=True)
    held = [row for row in rows if row.member_id == member_id]
    if not held:
        raise ApiError(404, "That admin designation was not found")
    current = {row.designation for row in held}
    if current == {designation}:
        return
    previous = ",".join(sorted(current))
    for row in held:
        if row.designation != designation:
            await session.delete(row)
    if designation not in current:
        session.add(EcosystemAdmin(
            id=uuid.uuid4(), ecosystem_id=ecosystem_id, member_id=member_id, designation=designation,
            appointed_by_member_id=caller.id,
        ))
    session.add(_audit(member_id, caller.id, previous, designation))
    await session.flush()


async def resolve_public_contact(session, ecosystem_id, *, lock: bool = False):
    """The public contact: external rep, else an internal admin, else an owner-tier member.

    Returns `(member, role label)` or None. The label is `external`, `internal`, or `owner`.
    Disabled accounts and non-active rows are skipped. The same result is what a direct
    message may be opened with.
    """
    enabled = select(User.id).where(User.disabled_at.is_(None))
    rows = (await session.execute(
        select(EcosystemAdmin, Member)
        .join(Member, Member.id == EcosystemAdmin.member_id)
        .where(
            EcosystemAdmin.ecosystem_id == ecosystem_id,
            Member.current_status == "active",
            Member.user_id.in_(enabled),
        )
        .order_by(EcosystemAdmin.created_at.asc(), EcosystemAdmin.id.asc())
    )).all()
    chosen = next(((admin, member) for admin, member in rows if admin.designation == EXTERNAL), None)
    label = EXTERNAL
    if chosen is None:
        chosen = next(((admin, member) for admin, member in rows if admin.designation == INTERNAL), None)
        label = INTERNAL
    member = chosen[1] if chosen is not None else None
    if member is None:
        member = await session.scalar(select(Member).where(
            Member.ecosystem_id == ecosystem_id,
            Member.role == "owner",
            Member.current_status == "active",
            Member.user_id.in_(enabled),
        ).order_by(Member.created_at.asc(), Member.id.asc()).limit(1))
        label = "owner"
    if member is None:
        return None
    if lock:
        member = await session.scalar(select(Member).where(Member.id == member.id).with_for_update())
        if member is None:
            return None
    return member, label


def backfill_admins(connection) -> int:
    """Insert the default admin's internal and external links where they are missing.

    Idempotent. Writes nothing for an ecosystem that has no owner, co_creator, or steward.
    Does not update or delete existing rows. Returns the number of links inserted.
    """
    members_table = sa.table(
        "members",
        sa.column("id", GUID()),
        sa.column("ecosystem_id", GUID()),
        sa.column("user_id", GUID()),
        sa.column("role", sa.String()),
        sa.column("profile", sa.String()),
        sa.column("current_status", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    users_table = sa.table("users", sa.column("id", GUID()), sa.column("disabled_at", sa.DateTime()))
    domains_table = sa.table(
        "domains",
        sa.column("id", GUID()),
        sa.column("ecosystem_id", GUID()),
        sa.column("steward_id", GUID()),
        sa.column("parent_domain_id", GUID()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    admins = sa.table(
        "ecosystem_admins",
        sa.column("id", GUID()),
        sa.column("ecosystem_id", GUID()),
        sa.column("member_id", GUID()),
        sa.column("designation", sa.String()),
        sa.column("appointed_by_member_id", GUID()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    transitions = sa.table(
        "member_status_transitions",
        sa.column("id", GUID()),
        sa.column("member_id", GUID()),
        sa.column("from_status", sa.String()),
        sa.column("to_status", sa.String()),
        sa.column("date", sa.Date()),
        sa.column("trigger", sa.String()),
        sa.column("notes", sa.String()),
        sa.column("actor_member_id", GUID()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    disabled = {row.id for row in connection.execute(sa.select(users_table.c.id, users_table.c.disabled_at)).all() if row.disabled_at is not None}
    grouped: dict[uuid.UUID, list[AdminCandidate]] = {}
    for row in connection.execute(sa.select(members_table)).all():
        grouped.setdefault(row.ecosystem_id, []).append(AdminCandidate(
            id=row.id, created_at=row.created_at, role=row.role, profile=row.profile,
            current_status=row.current_status, disabled=row.user_id in disabled,
        ))
    domains: dict[uuid.UUID, list[StewardDomain]] = {}
    for row in connection.execute(sa.select(domains_table)).all():
        domains.setdefault(row.ecosystem_id, []).append(StewardDomain(
            id=row.id, steward_id=row.steward_id, parent_domain_id=row.parent_domain_id,
            status=row.status, created_at=row.created_at,
        ))
    existing = {
        (row.ecosystem_id, row.member_id, row.designation)
        for row in connection.execute(sa.select(
            admins.c.ecosystem_id, admins.c.member_id, admins.c.designation,
        )).all()
    }
    inserted = 0
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    today = now.date()
    for ecosystem_id, people in grouped.items():
        chosen = choose_default_admin(people, domains.get(ecosystem_id, []))
        if chosen is None:
            continue
        for designation in (INTERNAL, EXTERNAL):
            key = (ecosystem_id, chosen, designation)
            if key in existing:
                continue
            connection.execute(sa.insert(admins).values(
                id=uuid.uuid4(), ecosystem_id=ecosystem_id, member_id=chosen, designation=designation,
                appointed_by_member_id=None, created_at=now, updated_at=now,
            ))
            connection.execute(sa.insert(transitions).values(
                id=uuid.uuid4(), member_id=chosen, from_status="none", to_status=designation, date=today,
                trigger=ADMIN_AUDIT, notes="default admin backfill", actor_member_id=None,
                created_at=now, updated_at=now,
            ))
            existing.add(key)
            inserted += 1
    return inserted
