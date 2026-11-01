"""Shares, needs and collaborations: one visibility rule, one status table, respond, approve and end.

REST (`api/discover.py`, the shares-needs lists of `api/domains.py`, `api/ecosystems.py`, `api/profiles.py`),
the queue (`services/next_steps.py` "# G-Exchange"), the MCP server and the chat assistant all call these
functions, so the surfaces cannot drift. Rationale: services/AGENTS.md "Exchange (G-Exchange)".
Nothing here commits; callers own the transaction.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass

from sqlalchemy import and_, false, func, or_, select, update

from neos_agent.api.errors import ApiError
from neos_agent.api.policy import (
    can_approve_collaboration,
    can_delete_publication,
    can_edit_publication,
    can_end_collaboration,
    can_moderate_publication,
    can_review_collaboration,
    can_see_publication,
    is_active_member_in,
    is_exchange_steward,
    is_publication_author,
)
from neos_agent.db.models import (
    CircleMembership,
    Collaboration,
    CollaborationApproval,
    Conversation,
    ConversationLink,
    ConversationParticipant,
    Domain,
    Ecosystem,
    Member,
    Message,
    SharesNeeds,
)
from neos_agent.services import dates as _dates
from neos_agent.services.agreement_consent import missing_agreement_consents, required_agreements_for_scope

# Vocabulary; the client mirrors it (lib/sharesneeds-vocab.ts, lib/exchange.ts).
PUBLICATION_TYPES = ("share", "need", "solution")
PUBLICATION_VISIBILITIES = ("public", "ecosystem", "domain")
RETIRED_VISIBILITY = "private"  # the old spelling of "domain"; s3e8b1d7c4a2 rewrote stored rows
PUBLICATION_CATEGORIES = ("technology", "resources", "skills", "knowledge", "infrastructure", "funding", "space",
                          "labor", "other")
PUBLICATION_STATUSES = ("active", "fulfilled", "withdrawn")
OPEN = "active"
# Lifecycle table (the author's moves; moderators hide instead): from -> {to: label}. active -> active renews.
PUBLICATION_MOVES: dict[str, dict[str, str]] = {
    "active": {"fulfilled": "Mark fulfilled", "withdrawn": "Withdraw", "active": "Keep it open"},
    "fulfilled": {"active": "Reopen"},
    "withdrawn": {"active": "Reopen"},
}
STALE_AFTER_DAYS = 90  # owner default: no auto-expiry; the author is asked "Still open?"
AUTHOR_LEFT = "author left"
NO_AUTHOR = "No author on record (legacy post)"
SHARE_NEED_LINK = "share_need"  # ConversationLink.entity_type of a response conversation
TITLE_MAX, TEXT_MAX, SHORT_MAX, TAGS_MAX, MESSAGE_MAX, REASON_MAX = 255, 20_000, 100, 50, 10_000, 2_000
EDITABLE_FIELDS = ("type", "title", "description", "category", "capacity", "tags", "visibility")

COLLABORATION_TIERS = ("observe", "cooperate", "federate", "integrate")
COLLABORATION_STATUSES = ("proposed", "active", "completed", "dissolved")
END_OUTCOMES: dict[str, tuple[str, ...]] = {"proposed": ("dissolved",), "active": ("completed", "dissolved")}
REVIEW_AFTER_DAYS = 365  # an activated collaboration without a review date gets one a year out

# Machine codes the client and the assistant branch on.
OWN_POST = "OWN_POST"
POST_CLOSED = "POST_CLOSED"
AUTHOR_INACTIVE = "AUTHOR_INACTIVE"
CONSENT_PENDING = "CONSENT_PENDING"
MEMBERSHIP_REQUIRED = "MEMBERSHIP_REQUIRED"
AUTHOR_ONLY = "AUTHOR_ONLY"
MODERATOR_ONLY = "MODERATOR_ONLY"
REASON_REQUIRED = "REASON_REQUIRED"
MOVE_NOT_ALLOWED = "MOVE_NOT_ALLOWED"
NOT_A_RESPONDER = "NOT_A_RESPONDER"
HAS_RESPONSES = "HAS_RESPONSES"
DUPLICATE_POST = "DUPLICATE_POST"
CANNOT_MOVE = "CANNOT_MOVE"
ALREADY_HIDDEN, NOT_HIDDEN = "ALREADY_HIDDEN", "NOT_HIDDEN"
PARTICIPATION_REQUIRED = "PARTICIPATION_REQUIRED"
SAME_DOMAIN = "SAME_DOMAIN"
DOMAIN_NOT_ACTIVE = "DOMAIN_NOT_ACTIVE"
ACTIVE_DOMAIN = "active"  # Domain.status that takes new posts and collaborations (others: archived)
NOT_PROPOSED, APPROVE_DENIED, SIDE_REQUIRED, ALREADY_APPROVED = (
    "NOT_PROPOSED", "APPROVE_DENIED", "SIDE_REQUIRED", "ALREADY_APPROVED")
END_DENIED, END_NOT_ALLOWED = "END_DENIED", "END_NOT_ALLOWED"
REVIEW_DENIED, NOT_ACTIVE = "REVIEW_DENIED", "NOT_ACTIVE"

POST_NOT_FOUND = "Share/Need not found"
COLLABORATION_NOT_FOUND = "Collaboration not found"
_TYPE_WORDS = {"share": "share", "need": "need", "solution": "solution"}


def _now() -> _dt.datetime:
    """Naive UTC, as the DateTime columns store it."""
    return _dt.datetime.now(_dt.UTC).replace(tzinfo=None)


def _bad(field: str, message: str, **extra) -> ApiError:
    return ApiError(400, message, {"field": field, **extra})


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


# ---------------------------------------------------------------------------
# Who is looking: the facts the one visibility rule reads
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Viewer:
    """A signed-in user across every membership (rows of any status, oldest first) and what they may see through them."""

    user_id: uuid.UUID | None
    rows: tuple = ()
    active_ecosystems: frozenset = frozenset()
    steward_ecosystems: frozenset = frozenset()
    domains: frozenset = frozenset()  # domains they take part in or steward, through an active row

    @property
    def member_ids(self) -> frozenset:
        return frozenset(row.id for row in self.rows)

    def row_in(self, ecosystem_id) -> Member | None:
        """Their row in `ecosystem_id` (the request-free caller_in)."""
        return next((row for row in self.rows if row.ecosystem_id == ecosystem_id), None)

    def row_by_id(self, member_id) -> Member | None:
        return next((row for row in self.rows if row.id == member_id), None)

    def active_rows(self) -> list[Member]:
        return [row for row in self.rows if row.current_status == "active"]


ANONYMOUS = Viewer(user_id=None)


async def load_viewer(session, user_id: uuid.UUID | None) -> Viewer:
    """Every member row of the user and the ecosystems/domains the visibility rule grants through the active ones."""
    if user_id is None:
        return ANONYMOUS
    rows = tuple((await session.execute(
        select(Member).where(Member.user_id == user_id).order_by(Member.created_at, Member.id)
    )).scalars())
    active = [row for row in rows if row.current_status == "active"]
    active_ids = [row.id for row in active]
    domains: set = set()
    if active_ids:
        domains |= set((await session.execute(select(CircleMembership.domain_id).where(
            CircleMembership.member_id.in_(active_ids), CircleMembership.status == "active",
        ))).scalars())
        domains |= set((await session.execute(select(Domain.id).where(Domain.steward_id.in_(active_ids)))).scalars())
    return Viewer(
        user_id=user_id, rows=rows,
        active_ecosystems=frozenset(row.ecosystem_id for row in active),
        steward_ecosystems=frozenset(row.ecosystem_id for row in active if is_exchange_steward(row, row.ecosystem_id)),
        domains=frozenset(domains),
    )


def visible_clause(viewer: Viewer):
    """policy.can_see_publication as one SQL condition, for every list (Discover, domain, ecosystem, profile)."""
    if viewer.user_id is None:
        return false()
    clauses = []
    if viewer.rows:
        clauses.append(SharesNeeds.author_member_id.in_(list(viewer.member_ids)))
    if viewer.steward_ecosystems:
        clauses.append(SharesNeeds.ecosystem_id.in_(list(viewer.steward_ecosystems)))
    open_rules = [SharesNeeds.visibility == "public"]
    if viewer.active_ecosystems:
        open_rules.append(and_(SharesNeeds.visibility == "ecosystem",
                               SharesNeeds.ecosystem_id.in_(list(viewer.active_ecosystems))))
    if viewer.domains:
        open_rules.append(and_(SharesNeeds.visibility.in_(("domain", RETIRED_VISIBILITY)),
                               SharesNeeds.domain_id.in_(list(viewer.domains))))
    clauses.append(and_(SharesNeeds.hidden_at.is_(None), or_(*open_rules)))
    return or_(*clauses)


async def load_visible(session, viewer: Viewer, post_id: uuid.UUID, *, for_update: bool = False) -> SharesNeeds:
    """One post the viewer may see (404 otherwise, the same body as a missing one); FOR UPDATE for writes."""
    stmt = select(SharesNeeds).where(SharesNeeds.id == post_id)
    if for_update:
        stmt = stmt.with_for_update()
    record = (await session.execute(stmt)).scalar_one_or_none()
    if record is None or not can_see_publication(viewer, record):
        raise ApiError(404, POST_NOT_FOUND)
    return record


def author_row(viewer: Viewer, record: SharesNeeds) -> Member | None:
    """The viewer's row that wrote the post, if any."""
    return viewer.row_by_id(record.author_member_id) if record.author_member_id is not None else None


def open_since(record: SharesNeeds) -> _dt.datetime:
    """When the post last became (or was confirmed) open: the 90-day check-in and the card's age count from here."""
    if record.status == OPEN and record.status_changed_at is not None:
        return record.status_changed_at
    return record.created_at or _now()


# ---------------------------------------------------------------------------
# Payload: one shape for every list, the detail and every write
# ---------------------------------------------------------------------------


async def _responders(session, post_ids) -> dict[uuid.UUID, dict[uuid.UUID, uuid.UUID]]:
    """post id -> {responder member id: their conversation id}, oldest first."""
    found: dict[uuid.UUID, dict[uuid.UUID, uuid.UUID]] = {}
    if post_ids:
        for link in (await session.execute(select(ConversationLink).where(
            ConversationLink.entity_type == SHARE_NEED_LINK, ConversationLink.entity_id.in_(list(post_ids)),
        ).order_by(ConversationLink.created_at))).scalars():
            found.setdefault(link.entity_id, {}).setdefault(link.created_by, link.conversation_id)
    return found


async def response_count(session, post_id: uuid.UUID) -> int:
    """How many people answered the post (one linked conversation each)."""
    return len((await _responders(session, [post_id])).get(post_id, {}))


def respond_blocked(viewer: Viewer, record: SharesNeeds, author: Member | None) -> str | None:
    """Why this viewer cannot answer the post now (a machine code), or None; respond() refuses in the same order."""
    if record.author_member_id is not None and record.author_member_id in viewer.member_ids:
        return OWN_POST
    if record.status != OPEN or record.hidden_at is not None:
        return POST_CLOSED
    if author is None or author.current_status != "active":
        return AUTHOR_INACTIVE
    if not viewer.active_ecosystems:
        return CONSENT_PENDING if any(r.current_status == "pending_consent" for r in viewer.rows) else MEMBERSHIP_REQUIRED
    return None


def allowed_moves(viewer: Viewer, record: SharesNeeds) -> list[dict]:
    """The author's moves from PUBLICATION_MOVES now; nobody else has any."""
    if not can_edit_publication(author_row(viewer, record), record):
        return []
    return [{"status": to, "label": label} for to, label in PUBLICATION_MOVES.get(record.status, {}).items()]


async def publication_payloads(session, records, viewer: Viewer, *, now: _dt.datetime | None = None) -> list[dict]:
    """Posts as the API sends them, with the viewer's flags; a few bulk queries per page."""
    from neos_agent.api.domains import domain_display_name  # api.domains imports this module

    records = list(records)
    if not records:
        return []
    now = now or _now()
    domains = {d.id: d for d in (await session.execute(
        select(Domain).where(Domain.id.in_({r.domain_id for r in records})))).scalars()}
    ecosystems = dict((await session.execute(
        select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_({r.ecosystem_id for r in records})))).all())
    responders = await _responders(session, [r.id for r in records])
    people_ids = {pid for r in records for pid in (r.author_member_id, r.fulfilled_by_member_id, r.hidden_by_member_id)}
    people_ids |= {pid for found in responders.values() for pid in found}
    people_ids.discard(None)
    people = {m.id: m for m in (await session.execute(select(Member).where(Member.id.in_(people_ids)))).scalars()} \
        if people_ids else {}

    def name(member_id) -> str | None:
        person = people.get(member_id)
        return person.display_name if person is not None else None

    payloads = []
    for r in records:
        domain = domains.get(r.domain_id)
        author = people.get(r.author_member_id)
        answered = responders.get(r.id, {})
        caller = viewer.row_in(r.ecosystem_id)
        writer = author_row(viewer, r)
        is_author = writer is not None
        moderator = can_moderate_publication(caller, r)
        blocked = respond_blocked(viewer, r, author)
        own_conversation = next((conv for rid, conv in answered.items() if rid in viewer.member_ids), None)
        hidden = r.hidden_at is not None
        payloads.append({
            "id": str(r.id), "type": r.type, "title": r.title, "description": r.description,
            "category": r.category, "capacity": r.capacity, "tags": r.tags if isinstance(r.tags, list) else [],
            "visibility": "domain" if r.visibility == RETIRED_VISIBILITY else r.visibility, "status": r.status,
            "ecosystem_id": str(r.ecosystem_id), "ecosystem_name": ecosystems.get(r.ecosystem_id),
            "domain_id": str(r.domain_id), "domain_name": domain_display_name(domain) if domain else None,
            "author_member_id": str(r.author_member_id) if r.author_member_id else None,
            "author_name": author.display_name if author is not None else None,
            "created_at": _iso(r.created_at), "updated_at": _iso(r.updated_at),
            "age_days": max(0, (now.date() - open_since(r).date()).days),
            "status_reason": r.status_reason, "status_changed_at": _iso(r.status_changed_at),
            "fulfilled_by_member_id": str(r.fulfilled_by_member_id) if r.fulfilled_by_member_id else None,
            "fulfilled_by_name": name(r.fulfilled_by_member_id),
            "hidden": hidden,
            "hidden_reason": r.hidden_reason if hidden else None,
            "hidden_at": _iso(r.hidden_at),
            "hidden_by_name": name(r.hidden_by_member_id) if hidden else None,
            "response_count": len(answered) if (is_author or moderator) else None,
            "responders": [{"member_id": str(rid), "name": name(rid)} for rid in answered] if is_author else [],
            "caller_is_author": is_author,
            "caller_can_edit": can_edit_publication(writer, r),
            "caller_can_moderate": moderator,
            "caller_can_manage": is_author or moderator,
            "caller_can_delete": can_delete_publication(writer, r, answered=bool(answered)),
            "caller_can_respond": blocked is None,
            "respond_blocked": blocked,
            "caller_has_responded": own_conversation is not None,
            "caller_conversation_id": str(own_conversation) if own_conversation else None,
            "allowed_next": allowed_moves(viewer, r),
        })
    return payloads


async def publication_payload(session, record: SharesNeeds, viewer: Viewer) -> dict:
    return (await publication_payloads(session, [record], viewer))[0]


# ---------------------------------------------------------------------------
# Validation (the client's required fields: lib/required-fields.ts via useRequiredFields)
# ---------------------------------------------------------------------------


def _optional_text(body: dict, field: str, limit: int, label: str) -> str | None:
    value = body.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise _bad(field, f"{label} must be text.")
    value = value.strip()
    if len(value) > limit:
        raise _bad(field, f"Keep the {label.lower()} to {limit} characters.")
    return value or None


def _uuid_field(body: dict, field: str, label: str) -> uuid.UUID:
    """A required id field: 400 naming the field when it is missing or not a UUID (never a 500)."""
    raw = body.get(field)
    if not isinstance(raw, (str, uuid.UUID)) or not str(raw).strip():
        raise _bad(field, f"Choose the {label.lower()}.")
    try:
        return uuid.UUID(str(raw).strip())
    except ValueError:
        raise _bad(field, f"{label} is not a valid id.") from None


def clean_publication_fields(body: dict, *, partial: bool) -> dict:
    """Checked, trimmed post fields (400 with `field` naming the first bad one); `partial` for edits."""
    out: dict = {}
    if not partial or "type" in body:
        if body.get("type") not in PUBLICATION_TYPES:
            raise _bad("type", "Choose whether this is a share, a need or a solution.", allowed=list(PUBLICATION_TYPES))
        out["type"] = body["type"]
    if not partial or "title" in body:
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            raise _bad("title", "Give it a title.")
        if len(title.strip()) > TITLE_MAX:
            raise _bad("title", f"Keep the title to {TITLE_MAX} characters.")
        out["title"] = title.strip()
    if "description" in body:
        out["description"] = _optional_text(body, "description", TEXT_MAX, "Description")
    if "category" in body:
        category = _optional_text(body, "category", SHORT_MAX, "Category")
        if category is not None and category.lower() not in PUBLICATION_CATEGORIES:
            raise _bad("category", "Choose one of the listed categories.", allowed=list(PUBLICATION_CATEGORIES))
        out["category"] = category.lower() if category else None
    if "capacity" in body:
        out["capacity"] = _optional_text(body, "capacity", SHORT_MAX, "Capacity")
    if "tags" in body:
        tags = body.get("tags")
        if tags is None:
            out["tags"] = None
        elif (not isinstance(tags, list) or len(tags) > TAGS_MAX
              or any(not isinstance(t, str) or not t.strip() or len(t.strip()) > SHORT_MAX for t in tags)):
            raise _bad("tags", f"Use up to {TAGS_MAX} tags of up to {SHORT_MAX} characters each.")
        else:
            out["tags"] = [t.strip() for t in tags]
    if not partial or "visibility" in body:
        visibility = body.get("visibility", "public") if not partial else body.get("visibility")
        if visibility == RETIRED_VISIBILITY:
            visibility = "domain"
        if visibility not in PUBLICATION_VISIBILITIES:
            raise _bad("visibility", "Choose who can see it.", allowed=list(PUBLICATION_VISIBILITIES))
        out["visibility"] = visibility
    return out


def _clean_reason(value, *, required: bool, field: str = "reason") -> str | None:
    if value is not None and not isinstance(value, str):
        raise _bad(field, "The reason must be text.")
    text = (value or "").strip()
    if required and not text:
        raise ApiError(400, "Give a reason; it is recorded with the change.", {"code": REASON_REQUIRED, "field": field})
    if len(text) > REASON_MAX:
        raise _bad(field, f"Keep the reason to {REASON_MAX} characters.")
    return text or None


# ---------------------------------------------------------------------------
# Membership and publishing gates
# ---------------------------------------------------------------------------


async def _ecosystem_name(session, ecosystem_id) -> str:
    return (await session.scalar(select(Ecosystem.name).where(Ecosystem.id == ecosystem_id))) or "this ecosystem"


async def require_active_member(session, member: Member | None, ecosystem_id, doing: str) -> Member:
    """An ACTIVE row in `ecosystem_id`; a pending newcomer gets CONSENT_PENDING (they read, never act)."""
    if is_active_member_in(member, ecosystem_id):
        return member
    where = await _ecosystem_name(session, ecosystem_id)
    if member is not None and member.current_status == "pending_consent":
        raise ApiError(403, f"Your membership in {where} is still waiting for your consent to its agreements. "
                            f"Until you give it, you can read shares and needs but not {doing}.",
                       {"code": CONSENT_PENDING})
    raise ApiError(403, f"Only an active member of {where} can {doing} there.", {"code": MEMBERSHIP_REQUIRED})


# What an archived domain refuses, in the words of the act ("edit" is not here: an existing post can still be corrected).
_INACTIVE_DOMAIN_WORDS = {
    "post": "so nothing new can be posted there. Choose an active domain.",
    "reopen": "so a post there cannot be reopened. Post it again in an active domain.",
    "collaborate": "so it cannot join a new collaboration. Choose an active domain.",
}


def require_active_domain(domain: Domain, field: str, doing: str) -> None:
    """409 DOMAIN_NOT_ACTIVE when `domain` is archived (any status but active) and `doing` is in _INACTIVE_DOMAIN_WORDS."""
    if domain.status != ACTIVE_DOMAIN and doing in _INACTIVE_DOMAIN_WORDS:
        raise ApiError(409, f"{domain.name or 'This domain'} is {domain.status or 'not active'}, "
                            f"{_INACTIVE_DOMAIN_WORDS[doing]}",
                       {"code": DOMAIN_NOT_ACTIVE, "field": field, "status": domain.status})


async def publishing_gate(session, author: Member, ecosystem_id, domain_id, *, doing: str = "post") -> None:
    """A domain of this ecosystem, active unless `doing` is "edit", then domain participation and agreement consent
    when the domain gates publishing (create "post", "edit" an open post, "reopen")."""
    domain = await session.get(Domain, domain_id)
    if domain is None or domain.ecosystem_id != ecosystem_id:
        raise _bad("domain_id", "Choose a domain of this ecosystem.")
    require_active_domain(domain, "domain_id", doing)
    if not await required_agreements_for_scope(session, ecosystem_id, "domain", domain_id):
        return
    participation = await session.scalar(select(CircleMembership.id).where(
        CircleMembership.domain_id == domain_id, CircleMembership.member_id == author.id,
        CircleMembership.status == "active",
    ))
    if participation is None:
        raise ApiError(403, "Active domain participation is required to publish a share or need",
                       {"code": PARTICIPATION_REQUIRED})
    missing = await missing_agreement_consents(session, author.id, ecosystem_id, "domain", domain_id)
    if missing:
        raise ApiError(409, "Agreement consent is required before publishing in this domain", {
            "required_agreements": [{"id": str(a.id), "title": a.title, "version": a.version} for a in missing],
        })


# ---------------------------------------------------------------------------
# Posts: publish, edit, move, hide/restore, delete, respond, exit
# ---------------------------------------------------------------------------


async def publish(session, viewer: Viewer, body) -> SharesNeeds:
    """Create a post as the caller's row in the named ecosystem; duplicates of an open post are 409 DUPLICATE_POST."""
    if not isinstance(body, dict):
        raise ApiError(400, "JSON object required")
    ecosystem_id = _uuid_field(body, "ecosystem_id", "Ecosystem")
    domain_id = _uuid_field(body, "domain_id", "Domain")
    fields = clean_publication_fields(body, partial=False)
    caller = await require_active_member(session, viewer.row_in(ecosystem_id), ecosystem_id, "post shares or needs")
    await publishing_gate(session, caller, ecosystem_id, domain_id)
    # The author's row lock serializes two identical submits, so the duplicate check below holds under a race.
    await session.execute(select(Member.id).where(Member.id == caller.id).with_for_update())
    existing = await session.scalar(select(SharesNeeds.id).where(
        SharesNeeds.author_member_id == caller.id, SharesNeeds.type == fields["type"],
        SharesNeeds.domain_id == domain_id, SharesNeeds.status == OPEN,
        func.lower(SharesNeeds.title) == fields["title"].lower(),
    ))
    if existing is not None:
        raise ApiError(409, "You already have this open post in this domain.",
                       {"code": DUPLICATE_POST, "existing_id": str(existing)})
    record = SharesNeeds(id=uuid.uuid4(), ecosystem_id=ecosystem_id, domain_id=domain_id,
                         author_member_id=caller.id, status=OPEN, **fields)
    session.add(record)
    await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


def _author_or_refuse(viewer: Viewer, record: SharesNeeds, doing: str) -> Member:
    writer = author_row(viewer, record)
    if can_edit_publication(writer, record):
        return writer
    if can_moderate_publication(viewer.row_in(record.ecosystem_id), record):
        raise ApiError(403, f"Only the author can {doing}. As a steward you can hide it with a reason.",
                       {"code": AUTHOR_ONLY})
    raise ApiError(403, f"Only the author can {doing}.", {"code": AUTHOR_ONLY})


async def update_publication(session, viewer: Viewer, record: SharesNeeds, body) -> SharesNeeds:
    """Edit the author's own post; a post never moves to another ecosystem or domain (400 CANNOT_MOVE)."""
    if not isinstance(body, dict):
        raise ApiError(400, "JSON object required")
    writer = _author_or_refuse(viewer, record, "edit this post")
    for key in ("ecosystem_id", "domain_id"):
        if key in body and str(body[key]) != str(getattr(record, key)):
            raise ApiError(400, "A post stays in its ecosystem and domain. Withdraw it and post again there.",
                           {"code": CANNOT_MOVE, "field": key})
    fields = clean_publication_fields({k: v for k, v in body.items() if k in EDITABLE_FIELDS}, partial=True)
    if not fields:
        raise ApiError(400, "No valid fields to update")
    for key, value in fields.items():
        setattr(record, key, value)
    if record.status == OPEN:
        await publishing_gate(session, await require_active_member(
            session, writer, record.ecosystem_id, "change an open post"), record.ecosystem_id, record.domain_id,
            doing="edit")
    await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


async def move_publication(session, viewer: Viewer, record: SharesNeeds, to: str, *, note=None,
                           fulfilled_by=None) -> SharesNeeds:
    """One move from PUBLICATION_MOVES by the author (409 with `allowed` otherwise), recorded with who, when, why."""
    writer = _author_or_refuse(viewer, record, "change this post's status")
    moves = PUBLICATION_MOVES.get(record.status, {})
    if to not in moves:
        raise ApiError(409, f"A post that is {record.status} cannot move to {to}.",
                       {"code": MOVE_NOT_ALLOWED, "allowed": list(moves)})
    note = _clean_reason(note, required=False, field="note")
    responder = None
    if to == "fulfilled" and fulfilled_by not in (None, ""):
        try:
            responder = uuid.UUID(str(fulfilled_by))
        except ValueError:
            responder = None
        answered = (await _responders(session, [record.id])).get(record.id, {})
        if responder not in answered:
            raise ApiError(400, "Name someone who answered this post, or leave it blank.",
                           {"code": NOT_A_RESPONDER, "field": "fulfilled_by_member_id"})
    if to == OPEN and record.status != OPEN:  # reopening: the author must still meet the publishing rules
        if not is_active_member_in(writer, record.ecosystem_id):
            raise ApiError(409, "You need an active membership in this ecosystem to reopen the post.",
                           {"code": AUTHOR_INACTIVE})
        await publishing_gate(session, writer, record.ecosystem_id, record.domain_id, doing="reopen")
    record.status = to
    record.status_reason = note
    record.status_changed_by_member_id = writer.id
    record.status_changed_at = _now()
    record.fulfilled_by_member_id = responder
    await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


def _moderator_or_refuse(viewer: Viewer, record: SharesNeeds) -> Member:
    caller = viewer.row_in(record.ecosystem_id)
    if not can_moderate_publication(caller, record):
        raise ApiError(403, "Only a steward of this post's ecosystem can hide or restore it.",
                       {"code": MODERATOR_ONLY})
    return caller


async def hide_publication(session, viewer: Viewer, record: SharesNeeds, reason) -> SharesNeeds:
    """A steward hides a post with a recorded reason (owner decision: restorable, never a delete)."""
    moderator = _moderator_or_refuse(viewer, record)
    reason = _clean_reason(reason, required=True)
    if record.hidden_at is not None:
        raise ApiError(409, "This post is already hidden.", {"code": ALREADY_HIDDEN})
    record.hidden_at, record.hidden_by_member_id, record.hidden_reason = _now(), moderator.id, reason
    await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


async def restore_publication(session, viewer: Viewer, record: SharesNeeds) -> SharesNeeds:
    """A steward shows a hidden post again; the last hide's actor and reason stay on the row as its trail."""
    _moderator_or_refuse(viewer, record)
    if record.hidden_at is None:
        raise ApiError(409, "This post is not hidden.", {"code": NOT_HIDDEN})
    record.hidden_at = None
    await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


async def delete_publication(session, viewer: Viewer, record: SharesNeeds) -> None:
    """Hard delete (owner decision): only the author, and only while nobody has answered."""
    writer = _author_or_refuse(viewer, record, "delete this post")
    if not can_delete_publication(writer, record, answered=await response_count(session, record.id) > 0):
        raise ApiError(409, "Someone has answered this post, so it stays on record. Withdraw it instead.",
                       {"code": HAS_RESPONSES})
    await session.delete(record)
    await session.flush()


def _responder_row(viewer: Viewer, ecosystem_id, preferred: Member | None) -> Member | None:
    """Their active row in the post's ecosystem, else the session's row when active, else their oldest active row."""
    own = viewer.row_in(ecosystem_id)
    if own is not None and own.current_status == "active":
        return own
    if preferred is not None:
        row = viewer.row_by_id(preferred.id)
        if row is not None and row.current_status == "active":
            return row
    return next(iter(viewer.active_rows()), None)


async def respond(session, viewer: Viewer, record: SharesNeeds, message, *,
                  preferred_row: Member | None = None) -> tuple[uuid.UUID, bool]:
    """Answer a post: open (or reuse) a direct conversation with its author's row, tagged to the post.

    Returns (conversation id, created). Load `record` FOR UPDATE so one responder never opens two conversations.
    """
    if not isinstance(message, str) or not message.strip():
        raise _bad("message", "Write a message to the person who posted this.")
    text = message.strip()
    if len(text) > MESSAGE_MAX:
        raise _bad("message", f"Keep the message to {MESSAGE_MAX} characters.")
    author = await session.get(Member, record.author_member_id) if record.author_member_id else None
    blocked = respond_blocked(viewer, record, author)
    if blocked == OWN_POST:
        raise ApiError(409, "This is your own post.", {"code": OWN_POST})
    if blocked == POST_CLOSED:
        raise ApiError(409, f"This post is no longer open (it is {'hidden' if record.hidden_at else record.status}).",
                       {"code": POST_CLOSED, "status": record.status})
    if blocked == AUTHOR_INACTIVE:
        raise ApiError(409, "The person who posted this is no longer an active member, so nobody can answer it.",
                       {"code": AUTHOR_INACTIVE})
    responder = _responder_row(viewer, record.ecosystem_id, preferred_row)
    if responder is None:  # active nowhere: always refused (CONSENT_PENDING names the pending ecosystem)
        pending = next((row for row in viewer.rows if row.current_status == "pending_consent"), None)
        await require_active_member(session, pending, pending.ecosystem_id if pending else record.ecosystem_id,
                                    "answer posts")
        raise ApiError(403, "Only an active member can answer posts.", {"code": MEMBERSHIP_REQUIRED})
    link = await session.scalar(select(ConversationLink).where(
        ConversationLink.entity_type == SHARE_NEED_LINK, ConversationLink.entity_id == record.id,
        ConversationLink.created_by.in_(list(viewer.member_ids)),
    ).order_by(ConversationLink.created_at).limit(1))
    if link is not None:
        sender = await session.scalar(select(ConversationParticipant.member_id).where(
            ConversationParticipant.conversation_id == link.conversation_id,
            ConversationParticipant.member_id.in_(list(viewer.member_ids)),
        ).limit(1))
        session.add(Message(id=uuid.uuid4(), conversation_id=link.conversation_id, sender_id=sender or link.created_by,
                            content=text))
        await session.flush()
        return link.conversation_id, False
    conversation = Conversation(id=uuid.uuid4(), ecosystem_id=record.ecosystem_id, type="dm",
                                title=f"Re: {record.title}"[:TITLE_MAX], created_by=responder.id)
    session.add(conversation)
    await session.flush()
    session.add_all([
        ConversationParticipant(id=uuid.uuid4(), conversation_id=conversation.id, member_id=responder.id, role="owner"),
        ConversationParticipant(id=uuid.uuid4(), conversation_id=conversation.id, member_id=author.id, role="member"),
        ConversationLink(id=uuid.uuid4(), conversation_id=conversation.id, entity_type=SHARE_NEED_LINK,
                         entity_id=record.id, created_by=responder.id),
        Message(id=uuid.uuid4(), conversation_id=conversation.id, sender_id=responder.id, content=text),
    ])
    await session.flush()
    return conversation.id, True


async def withdraw_on_exit(session, leaver: Member) -> int:
    """An exited member's open posts are withdrawn with the reason "author left" (owner default); returns how many."""
    result = await session.execute(update(SharesNeeds).where(
        SharesNeeds.author_member_id == leaver.id, SharesNeeds.status == OPEN,
    ).values(status="withdrawn", status_reason=AUTHOR_LEFT, status_changed_by_member_id=leaver.id,
             status_changed_at=_now(), fulfilled_by_member_id=None).execution_options(synchronize_session=False))
    return result.rowcount or 0


# ---------------------------------------------------------------------------
# Collaborations: read rule, propose, approve per side, end
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Sides:
    """The two domains a collaboration joins and their ecosystems (source first)."""

    source: Domain
    target: Domain

    @property
    def ecosystems(self) -> tuple:
        if self.source.ecosystem_id == self.target.ecosystem_id:
            return (self.source.ecosystem_id,)
        return (self.source.ecosystem_id, self.target.ecosystem_id)

    def domain_for(self, ecosystem_id) -> Domain:
        return self.source if self.source.ecosystem_id == ecosystem_id else self.target


async def load_sides(session, collaboration: Collaboration) -> Sides:
    domains = {d.id: d for d in (await session.execute(select(Domain).where(
        Domain.id.in_([collaboration.source_domain_id, collaboration.target_domain_id])))).scalars()}
    source, target = domains.get(collaboration.source_domain_id), domains.get(collaboration.target_domain_id)
    if source is None or target is None:
        raise ApiError(409, "Collaboration domain no longer exists")
    return Sides(source=source, target=target)


def can_read_collaboration(viewer: Viewer, collaboration: Collaboration, sides: Sides) -> bool:
    """Proposed ones only for members of either side (and their proposer); the rest for anyone signed in."""
    if viewer.user_id is None:
        return False
    if collaboration.status != "proposed":
        return True
    return (any(eco in viewer.active_ecosystems for eco in sides.ecosystems)
            or collaboration.proposed_by_member_id in viewer.member_ids)


def collaboration_visible_clause(viewer: Viewer):
    """can_read_collaboration as one SQL condition for the list."""
    if viewer.user_id is None:
        return false()
    clauses = [Collaboration.status != "proposed"]
    if viewer.active_ecosystems:
        side_domains = select(Domain.id).where(Domain.ecosystem_id.in_(list(viewer.active_ecosystems)))
        clauses += [Collaboration.source_domain_id.in_(side_domains), Collaboration.target_domain_id.in_(side_domains)]
    if viewer.rows:
        clauses.append(Collaboration.proposed_by_member_id.in_(list(viewer.member_ids)))
    return or_(*clauses)


async def load_collaboration(session, viewer: Viewer, collaboration_id: uuid.UUID, *,
                             for_update: bool = False) -> tuple[Collaboration, Sides]:
    """One collaboration the viewer may read (404 otherwise); FOR UPDATE locks the row before approvals."""
    stmt = select(Collaboration).where(Collaboration.id == collaboration_id)
    if for_update:
        stmt = stmt.with_for_update()
    record = (await session.execute(stmt)).scalar_one_or_none()
    if record is None:
        raise ApiError(404, COLLABORATION_NOT_FOUND)
    sides = await load_sides(session, record)
    if not can_read_collaboration(viewer, record, sides):
        raise ApiError(404, COLLABORATION_NOT_FOUND)
    return record, sides


async def _proposer_user_id(session, collaboration: Collaboration) -> uuid.UUID | None:
    if collaboration.proposed_by_member_id is None:
        return None
    return await session.scalar(select(Member.user_id).where(Member.id == collaboration.proposed_by_member_id))


def _may_approve(member, ecosystem_id, sides: Sides, proposer_user_id) -> bool:
    return can_approve_collaboration(member, ecosystem_id, source_ecosystem_id=sides.source.ecosystem_id,
                                     target_ecosystem_id=sides.target.ecosystem_id, proposer_user_id=proposer_user_id)


def _may_end(member, ecosystem_id, sides: Sides, collaboration: Collaboration) -> bool:
    return can_end_collaboration(member, ecosystem_id, source_ecosystem_id=sides.source.ecosystem_id,
                                 target_ecosystem_id=sides.target.ecosystem_id,
                                 proposer_member_id=collaboration.proposed_by_member_id, status=collaboration.status)


def _required_agreements(missing) -> dict:
    return {"required_agreements": [{"id": str(a.id), "title": a.title, "version": a.version} for a in missing]}


def _date_field(body: dict, field: str, today: _dt.date) -> _dt.date | None:
    raw = body.get(field)
    if raw in (None, ""):
        return None
    try:
        value = _dt.date.fromisoformat(str(raw))
    except ValueError:
        raise _bad(field, "Use a date like 2027-06-30.") from None
    if value < today:
        raise _bad(field, "Choose a review date that is not in the past.")
    return value


async def propose_collaboration(session, viewer: Viewer, body, *, today: _dt.date | None = None) -> Collaboration:
    """Any active member of the source ecosystem proposes; the source side counts as approved at once only when the
    proposer is a steward there (owner default) and the sides are different ecosystems."""
    today = today or _dates.aoe_today()  # "not in the past" by the one date rule (F9)
    if not isinstance(body, dict):
        raise ApiError(400, "JSON object required")
    source_id = _uuid_field(body, "source_domain_id", "Your domain")
    target_id = _uuid_field(body, "target_domain_id", "Domain to collaborate with")
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        raise _bad("title", "Give the collaboration a title.")
    if len(title.strip()) > TITLE_MAX:
        raise _bad("title", f"Keep the title to {TITLE_MAX} characters.")
    description = _optional_text(body, "description", TEXT_MAX, "Description")
    tier = body.get("engagement_tier") or "cooperate"
    if not isinstance(tier, str) or tier.strip().lower() not in COLLABORATION_TIERS:
        raise _bad("engagement_tier", "engagement_tier must be observe, cooperate, federate, or integrate",
                   allowed=list(COLLABORATION_TIERS))
    terms = body.get("terms")
    if terms is not None and not isinstance(terms, dict):
        raise _bad("terms", "Terms must be an object of named terms.")
    review_date = _date_field(body, "review_date", today)
    if source_id == target_id:
        raise ApiError(400, "Choose a different domain to collaborate with.",
                       {"code": SAME_DOMAIN, "field": "target_domain_id"})
    source = await session.get(Domain, source_id)
    if source is None:
        raise ApiError(404, "source_domain_id not found")
    proposer = await require_active_member(session, viewer.row_in(source.ecosystem_id), source.ecosystem_id,
                                           "propose a collaboration")
    target = await session.get(Domain, target_id)
    target_ecosystem = await session.get(Ecosystem, target.ecosystem_id) if target is not None else None
    if target is None or target_ecosystem is None or (
            target_ecosystem.visibility != "public" and viewer.row_in(target.ecosystem_id) is None):
        raise ApiError(404, "target_domain_id not found")
    require_active_domain(source, "source_domain_id", "collaborate")
    require_active_domain(target, "target_domain_id", "collaborate")
    missing = await missing_agreement_consents(session, proposer.id, source.ecosystem_id, "collaboration", source.id)
    if missing:
        raise ApiError(409, "Agreement consent is required before proposing a collaboration", _required_agreements(missing))
    linked = None
    if body.get("linked_share_need_id") not in (None, ""):
        linked = await load_visible(session, viewer, _uuid_field(body, "linked_share_need_id", "Post"))
        if linked.status != OPEN or linked.hidden_at is not None:
            raise ApiError(409, "That post is no longer open.", {"code": POST_CLOSED, "status": linked.status})
        if linked.domain_id not in (source.id, target.id):
            raise _bad("linked_share_need_id", "The post belongs to another domain than these two.")
    required = await required_agreements_for_scope(session, source.ecosystem_id, "collaboration", source.id)
    record = Collaboration(
        id=uuid.uuid4(), source_domain_id=source.id, target_domain_id=target.id, title=title.strip(),
        description=description, engagement_tier=tier.strip().lower(), terms=terms,
        required_agreement_ids=[str(a.id) for a in required] or None, status="proposed", review_date=review_date,
        linked_shares_needs=[str(linked.id)] if linked is not None else None, proposed_by_member_id=proposer.id,
    )
    session.add(record)
    await session.flush()
    sides = Sides(source=source, target=target)
    if _may_approve(proposer, source.ecosystem_id, sides, proposer.user_id):
        session.add(CollaborationApproval(id=uuid.uuid4(), collaboration_id=record.id, ecosystem_id=source.ecosystem_id,
                                          member_id=proposer.id, approved_at=_now()))
        await session.flush()
    await session.refresh(record)  # server-set columns (updated_at) loaded for the payload
    return record


async def _valid_approvals(session, collaboration: Collaboration, sides: Sides) -> dict:
    """ecosystem id -> approval, dropping approvals whose approver left the side or lost a required consent."""
    found = {}
    for approval in (await session.execute(select(CollaborationApproval).where(
            CollaborationApproval.collaboration_id == collaboration.id))).scalars().all():
        approver = await session.get(Member, approval.member_id)
        stale = approval.ecosystem_id not in sides.ecosystems or not is_active_member_in(approver, approval.ecosystem_id)
        if not stale:
            stale = bool(await missing_agreement_consents(session, approver.id, approval.ecosystem_id, "collaboration",
                                                          sides.domain_for(approval.ecosystem_id).id))
        if stale:
            await session.delete(approval)
        else:
            found[approval.ecosystem_id] = approval
    await session.flush()
    return found


async def approve_collaboration(session, viewer: Viewer, collaboration: Collaboration, sides: Sides,
                                ecosystem_id=None, *, today: _dt.date | None = None) -> Collaboration:
    """One side's approval by a steward there (load the row FOR UPDATE first); all sides approved -> active."""
    today = today or _dates.utc_today()  # started_date is a creation stamp
    if collaboration.status != "proposed":
        raise ApiError(409, "Only proposed collaborations can be approved", {"code": NOT_PROPOSED})
    approved = await _valid_approvals(session, collaboration, sides)
    proposer_user = await _proposer_user_id(session, collaboration)
    if ecosystem_id not in (None, ""):
        try:
            side = uuid.UUID(str(ecosystem_id))
        except ValueError:
            raise _bad("ecosystem_id", "Say which side you approve for.") from None
        if side not in sides.ecosystems:
            raise _bad("ecosystem_id", "That ecosystem is not a side of this collaboration.")
        if side in approved:
            raise ApiError(409, "That side has already approved.", {"code": ALREADY_APPROVED})
        if not _may_approve(viewer.row_in(side), side, sides, proposer_user):
            raise ApiError(403, "Only a steward of that ecosystem who did not propose it can approve for it.",
                           {"code": APPROVE_DENIED})
    else:
        eligible = [eco for eco in sides.ecosystems if _may_approve(viewer.row_in(eco), eco, sides, proposer_user)]
        open_sides = [eco for eco in eligible if eco not in approved]
        if not open_sides:
            if eligible:
                raise ApiError(409, "Your side has already approved.", {"code": ALREADY_APPROVED})
            raise ApiError(403, "Only a steward of one of its ecosystems who did not propose it can approve it.",
                           {"code": APPROVE_DENIED})
        if len(open_sides) > 1:
            raise ApiError(400, "You are a steward of both sides: say which one you approve for.",
                           {"code": SIDE_REQUIRED, "options": [str(eco) for eco in open_sides]})
        side = open_sides[0]
    approver = viewer.row_in(side)
    missing = await missing_agreement_consents(session, approver.id, side, "collaboration", sides.domain_for(side).id)
    if missing:
        raise ApiError(409, "Agreement consent is required before approving this collaboration",
                       _required_agreements(missing))
    approved[side] = CollaborationApproval(id=uuid.uuid4(), collaboration_id=collaboration.id, ecosystem_id=side,
                                           member_id=approver.id, approved_at=_now())
    session.add(approved[side])
    if all(eco in approved for eco in sides.ecosystems):
        collaboration.status = "active"
        collaboration.started_date = collaboration.started_date or today
        collaboration.review_date = collaboration.review_date or today + _dt.timedelta(days=REVIEW_AFTER_DAYS)
    await session.flush()
    await session.refresh(collaboration)
    return collaboration


async def end_collaboration(session, viewer: Viewer, collaboration: Collaboration, sides: Sides, outcome,
                            reason) -> Collaboration:
    """Complete or dissolve with a recorded reason: a steward of either side, or the proposer while proposed."""
    reason = _clean_reason(reason, required=True)
    actor = next((viewer.row_in(eco) for eco in sides.ecosystems
                  if _may_end(viewer.row_in(eco), eco, sides, collaboration)), None)
    if actor is None:
        raise ApiError(403, "Only a steward of either side can end this collaboration.", {"code": END_DENIED})
    allowed = END_OUTCOMES.get(collaboration.status, ())
    if outcome not in allowed:
        raise ApiError(409, f"A {collaboration.status} collaboration cannot end as {outcome}.",
                       {"code": END_NOT_ALLOWED, "allowed": list(allowed)})
    collaboration.status = outcome
    collaboration.ended_by_member_id, collaboration.end_reason, collaboration.ended_at = actor.id, reason, _now()
    await session.flush()
    await session.refresh(collaboration)
    return collaboration


def _review_side(viewer: Viewer, sides: Sides) -> Member | None:
    """The viewer's row on a side where they may record a review (a steward there), source side first."""
    return next((viewer.row_in(eco) for eco in sides.ecosystems
                 if can_review_collaboration(viewer.row_in(eco), eco, source_ecosystem_id=sides.source.ecosystem_id,
                                             target_ecosystem_id=sides.target.ecosystem_id)), None)


async def review_collaboration(session, viewer: Viewer, collaboration: Collaboration, sides: Sides, note,
                               next_review_date=None) -> Collaboration:
    """Record a review of an active collaboration (a steward of either side; load the row FOR UPDATE first): what it
    found, by whom and when, and the next review date (default a year out; a chosen one must be later than today)."""
    reviewer = _review_side(viewer, sides)
    if reviewer is None:
        raise ApiError(403, "Only a steward of either side can record a review of this collaboration.",
                       {"code": REVIEW_DENIED})
    if collaboration.status != "active":
        raise ApiError(409, f"Only an active collaboration is reviewed; this one is {collaboration.status}.",
                       {"code": NOT_ACTIVE, "status": collaboration.status})
    if note is not None and not isinstance(note, str):
        raise _bad("note", "The review note must be text.")
    text = (note or "").strip()
    if not text:
        raise ApiError(400, "Say what the review found; both ecosystems read it.",
                       {"code": REASON_REQUIRED, "field": "note"})
    if len(text) > REASON_MAX:
        raise _bad("note", f"Keep the review note to {REASON_MAX} characters.")
    if next_review_date in (None, ""):
        next_date = _dates.utc_today() + _dt.timedelta(days=REVIEW_AFTER_DAYS)
    else:
        try:
            next_date = _dt.date.fromisoformat(str(next_review_date))
        except ValueError:
            raise _bad("next_review_date", "Use a date like 2027-06-30.") from None
        if next_date <= _dates.aoe_today():
            raise _bad("next_review_date", "Choose a next review date after today.")
    collaboration.review_date = next_date
    collaboration.reviewed_by_member_id, collaboration.review_note, collaboration.reviewed_at = reviewer.id, text, _now()
    await session.flush()
    await session.refresh(collaboration)
    return collaboration


async def collaboration_payload(session, viewer: Viewer, collaboration: Collaboration, sides: Sides, *,
                                now: _dt.datetime | None = None) -> dict:
    """Detail with approvals, the awaited sides, the last review and the viewer's buttons."""
    from neos_agent.api.domains import domain_display_name  # api.domains imports this module

    names = dict((await session.execute(select(Ecosystem.id, Ecosystem.name).where(
        Ecosystem.id.in_(list(sides.ecosystems))))).all())
    approvals = (await session.execute(select(CollaborationApproval).where(
        CollaborationApproval.collaboration_id == collaboration.id).order_by(CollaborationApproval.approved_at))).scalars().all()
    member_ids = {a.member_id for a in approvals} | {collaboration.proposed_by_member_id, collaboration.ended_by_member_id,
                                                     collaboration.reviewed_by_member_id}
    member_ids.discard(None)
    people: dict = {}
    if member_ids:
        rows = await session.execute(select(Member.id, Member.display_name).where(Member.id.in_(member_ids)))
        people = dict(rows.all())
    approved = {a.ecosystem_id for a in approvals}
    proposed = collaboration.status == "proposed"
    proposer_user = await _proposer_user_id(session, collaboration) if proposed else None
    awaiting = [eco for eco in sides.ecosystems if eco not in approved] if proposed else []
    can_end = bool(END_OUTCOMES.get(collaboration.status)) and any(
        _may_end(viewer.row_in(eco), eco, sides, collaboration) for eco in sides.ecosystems)
    can_review = collaboration.status == "active" and _review_side(viewer, sides) is not None
    linked_ids = collaboration.linked_shares_needs or []
    if isinstance(linked_ids, dict):
        linked_ids = list(linked_ids.get("ids") or [])
    linked = []
    for raw in linked_ids:
        try:
            post = await session.get(SharesNeeds, uuid.UUID(str(raw)))
        except ValueError:
            post = None
        if post is not None and can_see_publication(viewer, post):
            linked.append({"id": str(post.id), "title": post.title, "type": post.type, "status": post.status})

    def side(eco) -> dict:
        return {"ecosystem_id": str(eco), "ecosystem_name": names.get(eco)}

    return {
        "id": str(collaboration.id), "title": collaboration.title, "description": collaboration.description,
        "status": collaboration.status, "engagement_tier": collaboration.engagement_tier,
        "terms": collaboration.terms, "required_agreement_ids": collaboration.required_agreement_ids or [],
        "source_domain_id": str(sides.source.id), "source_domain_name": domain_display_name(sides.source),
        "source_ecosystem_id": str(sides.source.ecosystem_id),
        "source_ecosystem_name": names.get(sides.source.ecosystem_id),
        "target_domain_id": str(sides.target.id), "target_domain_name": domain_display_name(sides.target),
        "target_ecosystem_id": str(sides.target.ecosystem_id),
        "target_ecosystem_name": names.get(sides.target.ecosystem_id),
        "started_date": _iso(collaboration.started_date), "review_date": _iso(collaboration.review_date),
        "review_due": collaboration.status == "active" and _dates.date_passed(collaboration.review_date, now),
        "reviewed_at": _iso(collaboration.reviewed_at), "review_note": collaboration.review_note,
        "reviewed_by_name": people.get(collaboration.reviewed_by_member_id),
        "caller_can_review": can_review,
        "created_at": _iso(collaboration.created_at),
        "proposed_by_member_id": str(collaboration.proposed_by_member_id) if collaboration.proposed_by_member_id else None,
        "proposed_by_name": people.get(collaboration.proposed_by_member_id),
        "approvals": [{"ecosystem_id": str(a.ecosystem_id), "ecosystem_name": names.get(a.ecosystem_id),
                       "approved_by": people.get(a.member_id), "approved_at": _iso(a.approved_at)} for a in approvals],
        "awaiting": [side(eco) for eco in awaiting],
        "caller_can_approve_for": [side(eco) for eco in awaiting
                                   if _may_approve(viewer.row_in(eco), eco, sides, proposer_user)],
        "caller_can_end": can_end,
        "end_outcomes": list(END_OUTCOMES.get(collaboration.status, ())) if can_end else [],
        "ended_by_name": people.get(collaboration.ended_by_member_id), "end_reason": collaboration.end_reason,
        "ended_at": _iso(collaboration.ended_at),
        "linked_publications": linked,
    }
