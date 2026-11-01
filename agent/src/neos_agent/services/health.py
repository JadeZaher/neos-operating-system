"""Governance health snapshot: computed indicator values and "needs attention" counts, read-only.

The monitor's role in framework Layer VII: values are computed here, statuses are rated by a human
auditor (api/safeguards.py). Rationale and indicator caveats: services/AGENTS.md "Maintenance and health (G-Maint)".
"""

from __future__ import annotations

import datetime as _dt
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import func, or_, select

from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Agreement,
    AgreementCeremony,
    AgreementMemberConsent,
    Collaboration,
    ConflictCase,
    ConsentParticipant,
    ConsentRecord,
    DecisionRecord,
    Domain,
    Ecosystem,
    EmergencyState,
    ExitRecord,
    GovernanceHealthAudit,
    Member,
    MemberStatusTransition,
    Proposal,
    ReviewRecord,
    TestReport,
)
from neos_agent.api.policy import PROFILE_ADMINS
from neos_agent.services import dates

DEFAULT_PERIOD_DAYS = 90  # framework: the previous quarter
AUDIT_INTERVAL_DAYS = 90  # framework E.10: the next audit a quarter after publication
POST_EMERGENCY_AUDIT_DAYS = 30  # framework C: within 30 days of an emergency's conclusion
LEADERSHIP_ROLES = ("mod", "admin", "owner")
REVIEW_CYCLE_DAYS = 90  # GHI-05 counts leadership tenure in quarterly cycles
MIN_DECIDED_PER_GROUP = 3  # GHI-02 is "n/a" below this many decided proposals in either group
STALL_DAYS = 30
NEWCOMER_WAIT_DAYS = 14
UNTRIAGED_DAYS = 7
EXIT_WINDOW_DAYS = 30
RATINGS = ("healthy", "warning", "critical")
AUDIT_PUBLISHED = "completed"


def _higher(healthy: float, warning: float) -> Callable[[float], str]:
    return lambda value: "healthy" if value >= healthy else "warning" if value >= warning else "critical"


@dataclass(frozen=True)
class Indicator:
    """One framework indicator (neos-core layer-07 governance-health-audit/assets/indicator-definitions.yaml)."""

    indicator_id: str
    name: str
    unit: str | None
    computable: bool
    higher_is_better: bool
    thresholds: dict
    band: Callable[[float], str]


INDICATORS = (
    Indicator("GHI-01", "Proposal authorship diversity", "%", True, True,
              {"healthy": ">= 60%", "warning": "40-59%", "critical": "< 40%"}, _higher(60, 40)),
    Indicator("GHI-02", "Approval rate by author role", "ratio", True, True,
              {"healthy": ">= 0.80", "warning": "0.50-0.79", "critical": "< 0.50"}, _higher(0.80, 0.50)),
    Indicator("GHI-03", "Resource concentration", "%", False, False,
              {"healthy": "< 30%", "warning": "30-49%", "critical": ">= 50%"},
              lambda value: "healthy" if value < 30 else "warning" if value < 50 else "critical"),
    Indicator("GHI-04", "Participation trend", "%", True, True,
              {"healthy": ">= -5%", "warning": "-5% to -20%", "critical": "< -20%"}, _higher(-5, -20)),
    Indicator("GHI-05", "Leadership tenure", "cycles", True, False,
              {"healthy": "<= 2 cycles", "warning": "3 cycles", "critical": ">= 4 cycles"},
              lambda value: "healthy" if value <= 2 else "warning" if value <= 3 else "critical"),
    Indicator("GHI-06", "Objection integration rate", "%", True, True,
              {"healthy": ">= 70%", "warning": "40-69%", "critical": "< 40%"}, _higher(70, 40)),
    Indicator("GHI-07", "Review compliance rate", "%", True, True,
              {"healthy": ">= 85%", "warning": "60-84%", "critical": "< 60%"}, _higher(85, 60)),
    Indicator("GHI-08", "Cross-unit engagement", "per quarter", True, True,
              {"healthy": ">= 4 per quarter", "warning": "2-3 per quarter", "critical": "<= 1 per quarter"},
              _higher(4, 2)),
)
INDICATOR_BY_ID = {indicator.indicator_id: indicator for indicator in INDICATORS}


@dataclass(frozen=True)
class Window:
    """The audit period: calendar days `start`..`end` inclusive, as naive-UTC instants [t0, t1)."""

    start: _dt.date
    end: _dt.date
    now: _dt.datetime

    @property
    def t0(self) -> _dt.datetime:
        return _dt.datetime.combine(self.start, _dt.time.min)

    @property
    def t1(self) -> _dt.datetime:
        return _dt.datetime.combine(self.end + _dt.timedelta(days=1), _dt.time.min)

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def prior(self) -> "Window":
        """The period of the same length just before this one."""
        return Window(self.start - _dt.timedelta(days=self.days), self.start - _dt.timedelta(days=1), self.now)


def default_period(now: _dt.datetime | None = None) -> tuple[_dt.date, _dt.date]:
    """The 90 days ending today (services/dates.aoe_today)."""
    end = dates.aoe_today(now)
    return end - _dt.timedelta(days=DEFAULT_PERIOD_DAYS - 1), end


def period_bounds(start: _dt.date | None, end: _dt.date | None,
                  now: _dt.datetime | None = None) -> tuple[_dt.date, _dt.date]:
    """FX-Maint (F11): the one period rule for the snapshot and publish: one bound given, the other is 90 days from it."""
    if start is None and end is None:
        return default_period(now)
    if end is None:
        end = start + _dt.timedelta(days=DEFAULT_PERIOD_DAYS - 1)
    if start is None:
        start = end - _dt.timedelta(days=DEFAULT_PERIOD_DAYS - 1)
    return start, end


def _in(column, window: Window):
    return (column >= window.t0) & (column < window.t1)


def _plural(count: int, one: str, many: str | None = None) -> str:
    return f"{count} {one if count == 1 else (many or one + 's')}"


# ---------------------------------------------------------------------------
# Indicators: each returns (measured_value, basis, detail)
# ---------------------------------------------------------------------------


async def _authorship_diversity(session, ecosystem_id, window: Window):
    rows = (await session.execute(select(Proposal.proposer_member_id, Proposal.proposer).where(
        Proposal.ecosystem_id == ecosystem_id, _in(Proposal.created_at, window),
    ))).all()
    if not rows:
        return None, "No proposals were written in the period.", None
    authors = {str(member_id) if member_id else (name or "").strip().lower() for member_id, name in rows} - {""}
    return (round(len(authors) * 100 / len(rows)),
            f"{_plural(len(authors), 'distinct author')} wrote {_plural(len(rows), 'proposal')} in the period.", None)


async def _approval_by_role(session, ecosystem_id, window: Window):
    rows = (await session.execute(select(Proposal.status, Member.role).join(
        Member, Member.id == Proposal.proposer_member_id,
    ).where(
        Proposal.ecosystem_id == ecosystem_id, Proposal.status.in_(("ratified", "withdrawn")),
        _in(Proposal.created_at, window),
    ))).all()
    groups = {True: [0, 0], False: [0, 0]}  # leadership? -> [ratified, decided]
    for status, role in rows:
        group = groups[role in LEADERSHIP_ROLES]
        group[1] += 1
        group[0] += status == "ratified"
    (lead_ok, lead_n), (other_ok, other_n) = groups[True], groups[False]
    basis = (f"Leadership (stewards) wrote {_plural(lead_n, 'decided proposal')}, {lead_ok} ratified; other members "
             f"{other_n}, {other_ok} ratified. Uses each author's role today; proposals without an author link are left out.")
    if lead_n < MIN_DECIDED_PER_GROUP or other_n < MIN_DECIDED_PER_GROUP:
        return None, f"Not enough data: each group needs {MIN_DECIDED_PER_GROUP} decided proposals. " + basis, None
    if lead_ok == 0:
        return None, "Leadership had no proposal ratified, so there is no ratio. " + basis, None
    return round((other_ok / other_n) / (lead_ok / lead_n), 2), basis, None


async def _participants(session, ecosystem_id, window: Window) -> set:
    """Members who advised, recorded a position, filed a test report or consented to an agreement (member-linked rows)."""
    statements = (
        select(AdviceEntry.member_id).join(AdviceLog, AdviceLog.id == AdviceEntry.advice_log_id)
        .join(Proposal, Proposal.id == AdviceLog.proposal_id)
        .where(Proposal.ecosystem_id == ecosystem_id, _in(AdviceEntry.created_at, window)),
        select(ConsentParticipant.member_id).join(ConsentRecord, ConsentRecord.id == ConsentParticipant.consent_record_id)
        .join(Proposal, Proposal.id == ConsentRecord.proposal_id)
        .where(Proposal.ecosystem_id == ecosystem_id, _in(ConsentParticipant.updated_at, window)),
        select(TestReport.reporter_member_id).join(Proposal, Proposal.id == TestReport.proposal_id)
        .where(Proposal.ecosystem_id == ecosystem_id, _in(TestReport.created_at, window)),
        select(AgreementMemberConsent.member_id).join(Agreement, Agreement.id == AgreementMemberConsent.agreement_id)
        .where(Agreement.ecosystem_id == ecosystem_id, _in(AgreementMemberConsent.attested_at, window)),
    )
    found: set = set()
    for statement in statements:
        found |= {value for value in (await session.execute(statement)).scalars() if value is not None}
    return found


async def _participation_trend(session, ecosystem_id, window: Window):
    current = len(await _participants(session, ecosystem_id, window))
    prior = len(await _participants(session, ecosystem_id, window.prior()))
    active = await _active_count(session, ecosystem_id)
    basis = (f"{_plural(current, 'member')} took part (advice, consent positions, test reports, agreement consent) "
             f"against {prior} in the {window.days} days before; {active} active members now. "
             "Rows without a member link are left out.")
    if prior == 0:
        return None, "No participation was recorded in the prior period, so there is no trend yet. " + basis, None
    return round((current - prior) * 100 / prior, 1), basis, None


async def _leadership_tenure(session, ecosystem_id, window: Window):
    leaders = (await session.execute(select(Member).where(
        Member.ecosystem_id == ecosystem_id, Member.current_status == "active", Member.role.in_(LEADERSHIP_ROLES),
    ))).scalars().all()
    if not leaders:
        return None, "Nobody holds a steward role.", None
    leadership = {f"role:{role}" for role in LEADERSHIP_ROLES}
    entered: dict = {}
    for grant in (await session.execute(select(MemberStatusTransition).where(
        MemberStatusTransition.member_id.in_([leader.id for leader in leaders]),
        MemberStatusTransition.trigger == "role_grant",
    ))).scalars():
        if grant.to_status in leadership and grant.from_status not in leadership and grant.date <= window.end:
            entered[grant.member_id] = max(grant.date, entered.get(grant.member_id, grant.date))
    tenure = []
    for leader in leaders:
        since = entered.get(leader.id) or (leader.created_at.date() if leader.created_at else window.end)
        tenure.append(((window.end - since).days // REVIEW_CYCLE_DAYS, leader.display_name, since))
    cycles, name, since = max(tenure, key=lambda row: row[0])
    return (cycles, "Ecosystem roles only (domain stewardship has no history yet). Role grants are recorded since "
            "2026-10-31, so earlier holders count from when they joined, which can overstate tenure.",
            f"{name}, a steward since {since.isoformat()}")


async def _objection_integration(session, ecosystem_id, window: Window):
    rows = (await session.execute(select(ConsentParticipant, ConsentRecord.proposal_id).join(
        ConsentRecord, ConsentRecord.id == ConsentParticipant.consent_record_id,
    ).join(Proposal, Proposal.id == ConsentRecord.proposal_id).where(
        Proposal.ecosystem_id == ecosystem_id, _in(ConsentParticipant.created_at, window),
    ))).all()
    objections = []
    for participant, proposal_id in rows:
        position = (participant.position or "").strip().lower()
        if position in ("object", "objection") or (position == "withdrawn" and (participant.reason or "").strip()):
            objections.append((participant, proposal_id))
    if not objections:
        return None, "No objection was raised in the period.", None
    from neos_agent.services.act_gates import revision_round  # the engine reads its own send-back summary

    sendbacks: dict = {}
    for log in (await session.execute(select(AdviceLog).where(
        AdviceLog.proposal_id.in_({proposal_id for _, proposal_id in objections}),
        AdviceLog.proposer_modifications.is_not(None),
    ))).scalars():
        revision = revision_round(log)
        if revision and revision.get("source") == "consent" and log.created_at is not None:
            sendbacks.setdefault(log.proposal_id, []).append(log.created_at)
    integrated = sum(
        any(sent > participant.created_at for sent in sendbacks.get(proposal_id, []))
        for participant, proposal_id in objections if participant.created_at is not None
    )
    return (round(integrated * 100 / len(objections)),
            f"{integrated} of {_plural(len(objections), 'objection')} led to a revision (sent back from consent). "
            "Changing an objection to consent overwrites the row, so lifted objections count only when a reason was kept.",
            None)


async def _review_compliance(session, ecosystem_id, window: Window):
    due = timely = 0
    for record in (await session.execute(select(ReviewRecord).where(ReviewRecord.ecosystem_id == ecosystem_id))).scalars():
        evaluation = record.evaluation if isinstance(record.evaluation, dict) else {}
        try:
            due_date = _dt.date.fromisoformat(evaluation.get("due_date") or "")
        except ValueError:
            continue
        if window.start <= due_date <= window.end:
            due += 1
            timely += bool(evaluation.get("on_time"))
    for agreement in (await session.execute(select(Agreement).where(
        Agreement.ecosystem_id == ecosystem_id, Agreement.status.in_(("active", "under_review")),
        Agreement.review_date >= window.start, Agreement.review_date <= window.end,
    ))).scalars():
        if agreement.status == "active":
            due += dates.date_passed(agreement.review_date, window.now)  # missed; not yet due counts nothing
            continue
        started = await session.scalar(select(func.max(AgreementCeremony.completed_at)).where(
            AgreementCeremony.agreement_id == agreement.id, AgreementCeremony.stage == "under_review",
        ))
        due += 1
        timely += started is not None and started.date() <= agreement.review_date
    if not due:
        return None, "No agreement review fell due in the period.", None
    return (round(timely * 100 / due),
            f"{timely} of {_plural(due, 'review')} due in the period finished (or, still open, started) by the "
            "review date.", None)


async def _cross_unit(session, ecosystem_id, window: Window):
    domain_ids = select(Domain.id).where(Domain.ecosystem_id == ecosystem_id)
    collaborations = await session.scalar(select(func.count(Collaboration.id)).where(
        or_(Collaboration.source_domain_id.in_(domain_ids), Collaboration.target_domain_id.in_(domain_ids)),
        _in(Collaboration.created_at, window),
    )) or 0
    shared = 0
    for model in (Proposal, Agreement):
        for owner, shared_ids in (await session.execute(select(model.ecosystem_id, model.shared_ecosystem_ids).where(
            model.shared_ecosystem_ids.is_not(None), _in(model.created_at, window),
        ))).all():
            listed = {str(item) for item in shared_ids or []} if isinstance(shared_ids, list) else set()
            shared += bool(listed) and (owner == ecosystem_id or str(ecosystem_id) in listed)
    count = collaborations + shared
    return (round(count * DEFAULT_PERIOD_DAYS / window.days, 1),
            f"{_plural(collaborations, 'collaboration')} between domains and {_plural(shared, 'shared proposal or agreement', 'shared proposals or agreements')} "
            f"in {window.days} days, counted per 90-day quarter.", None)


_COMPUTERS = {
    "GHI-01": _authorship_diversity, "GHI-02": _approval_by_role, "GHI-04": _participation_trend,
    "GHI-05": _leadership_tenure, "GHI-06": _objection_integration, "GHI-07": _review_compliance,
    "GHI-08": _cross_unit,
}


async def _active_count(session, ecosystem_id) -> int:
    return await session.scalar(select(func.count(Member.id)).where(
        Member.ecosystem_id == ecosystem_id, Member.current_status == "active",
    )) or 0


# ---------------------------------------------------------------------------
# Needs attention: counts with links, never a status
# ---------------------------------------------------------------------------


async def _attention(session, ecosystem_id, window: Window) -> list[dict]:
    now, today = window.now, dates.aoe_today(window.now)
    stall_before = now - _dt.timedelta(days=STALL_DAYS)
    items = []

    overdue_reviews = [a for a in (await session.execute(select(Agreement).where(
        Agreement.ecosystem_id == ecosystem_id, Agreement.status.in_(("active", "under_review")),
    ))).scalars() if dates.date_passed(a.review_date, now)]
    items.append({"key": "reviews_overdue", "label": "Agreement reviews overdue", "count": len(overdue_reviews),
                  "detail": None, "link": "/agreements"})

    stalled = {"advice past its deadline": 0, "advice with no deadline and no advice for 30 days": 0,
               "consent past its deadline": 0, "test with no report for 30 days": 0}
    for proposal in (await session.execute(select(Proposal).where(
        Proposal.ecosystem_id == ecosystem_id, Proposal.status.in_(("advice", "consent", "test")),
    ))).scalars():
        if proposal.status == "advice" and proposal.advice_deadline is not None:
            stalled["advice past its deadline"] += proposal.advice_deadline < today
        elif proposal.status == "advice":
            last = await session.scalar(select(func.max(AdviceEntry.created_at)).join(
                AdviceLog, AdviceLog.id == AdviceEntry.advice_log_id).where(AdviceLog.proposal_id == proposal.id))
            stalled["advice with no deadline and no advice for 30 days"] += (last or proposal.updated_at or now) < stall_before
        elif proposal.status == "consent":
            stalled["consent past its deadline"] += proposal.consent_deadline is not None and proposal.consent_deadline < today
        else:
            last = await session.scalar(select(func.max(TestReport.created_at)).where(TestReport.proposal_id == proposal.id))
            stalled["test with no report for 30 days"] += (last or proposal.updated_at or now) < stall_before
    total = sum(stalled.values())
    items.append({"key": "stalled_proposals", "label": "Stalled proposals", "count": total,
                  "detail": "; ".join(f"{reason}: {count}" for reason, count in stalled.items() if count) or None,
                  "link": "/proposals"})

    waiting = await session.scalar(select(func.count(Member.id)).where(
        Member.ecosystem_id == ecosystem_id, Member.current_status == "pending_consent",
        Member.created_at < now - _dt.timedelta(days=NEWCOMER_WAIT_DAYS),
    )) or 0
    items.append({"key": "waiting_newcomers", "label": "Newcomers waiting more than 14 days", "count": waiting,
                  "detail": None, "link": "/members"})

    cases = (await session.execute(select(ConflictCase.status, ConflictCase.created_at).where(
        ConflictCase.ecosystem_id == ecosystem_id, ConflictCase.status.notin_(("resolved", "closed")),
    ))).all()
    untriaged = sum(status == "reported" and created is not None and created < now - _dt.timedelta(days=UNTRIAGED_DAYS)
                    for status, created in cases)
    oldest = max(((now - created).days for _, created in cases if created is not None), default=None)
    items.append({"key": "open_conflicts", "label": "Open conflict cases", "count": len(cases),
                  "detail": (f"{untriaged} untriaged for more than 7 days; the oldest is {_plural(oldest, 'day')} old"
                             if cases and oldest is not None else None), "link": "/conflicts"})

    from neos_agent.api import emergency as emergency_api  # describe() owns the Recovery dates

    emergencies = (await session.execute(select(EmergencyState).where(
        EmergencyState.ecosystem_id == ecosystem_id,
        or_(_in(EmergencyState.declared_at, window), EmergencyState.state.in_(("open", "half_open"))),
    ))).scalars().all()
    overdue_recovery = sum(e.state == "half_open" and emergency_api.describe(e, now)["review_overdue"] for e in emergencies)
    items.append({"key": "emergencies", "label": "Emergencies in the period or still open", "count": len(emergencies),
                  "detail": f"{overdue_recovery} with the Recovery review overdue" if overdue_recovery else None,
                  "link": "/emergency"})

    exits = await session.scalar(select(func.count(ExitRecord.id)).where(
        ExitRecord.ecosystem_id == ecosystem_id, ExitRecord.status == "completed",
        ExitRecord.completed_date >= today - _dt.timedelta(days=EXIT_WINDOW_DAYS - 1),
    )) or 0
    base = await _active_count(session, ecosystem_id) + exits
    items.append({"key": "exits", "label": "Members who left in the last 30 days", "count": exits,
                  "detail": (f"{round(exits * 100 / base)}% of members; the framework calls for an audit at 20%"
                             if exits and base else None), "link": "/exit"})

    held = (await session.execute(select(Domain.steward_id, func.count(Domain.id)).where(
        Domain.ecosystem_id == ecosystem_id, Domain.steward_id.is_not(None),
    ).group_by(Domain.steward_id))).all()
    domains = await session.scalar(select(func.count(Domain.id)).where(Domain.ecosystem_id == ecosystem_id)) or 0
    stewards = await session.scalar(select(func.count(Member.id)).where(
        Member.ecosystem_id == ecosystem_id, Member.current_status == "active", Member.role.in_(LEADERSHIP_ROLES),
    )) or 0
    active = await _active_count(session, ecosystem_id)
    top_id, top_count = max(held, key=lambda row: row[1], default=(None, 0))
    top_name = await session.scalar(select(Member.display_name).where(Member.id == top_id)) if top_id else None
    parts = []
    if top_name and domains:
        parts.append(f"{top_name} stewards {top_count} of {_plural(domains, 'domain')} ({round(top_count * 100 / domains)}%)")
    if active:
        parts.append(f"{stewards} of {active} active members hold a steward role ({round(stewards * 100 / active)}%)")
    items.append({"key": "authority_concentration", "label": "Domains held by the busiest steward", "count": top_count,
                  "detail": "; ".join(parts) or None, "link": "/domains"})
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _indicator_row(indicator: Indicator, value, basis: str, detail: str | None) -> dict:
    return {
        "indicator_id": indicator.indicator_id,
        "name": indicator.name,
        "measured_value": value,
        "unit": indicator.unit,
        "computable": indicator.computable,
        "basis": basis,
        "band": indicator.band(value) if value is not None else None,
        "thresholds": indicator.thresholds,
        "higher_is_better": indicator.higher_is_better,
        "detail": detail,
    }


async def health_snapshot(session, ecosystem_id: uuid.UUID, *, start: _dt.date | None = None,
                          end: _dt.date | None = None, now: _dt.datetime | None = None) -> dict:
    """Every framework indicator's value for the period (default: the 90 days ending today) and "needs attention".

    Read-only: it never writes. `band` is the framework threshold, for reference; the auditor rates the status.
    """
    now = dates.naive_utc(now or dates.utc_now())
    window = Window(*period_bounds(start, end, now), now)
    indicators = []
    for indicator in INDICATORS:
        if not indicator.computable:
            indicators.append(_indicator_row(indicator, None, "Not computable yet: there are no resource records.", None))
            continue
        value, basis, detail = await _COMPUTERS[indicator.indicator_id](session, ecosystem_id, window)
        indicators.append(_indicator_row(indicator, value, basis, detail))
    name = await session.scalar(select(Ecosystem.name).where(Ecosystem.id == ecosystem_id))
    return {
        "ecosystem_id": str(ecosystem_id),
        "ecosystem": name,
        "period": {"start": window.start.isoformat(), "end": window.end.isoformat()},
        "generated_at": now.replace(microsecond=0).isoformat() + "Z",
        "indicators": indicators,
        "attention": await _attention(session, ecosystem_id, window),
    }


def _trend(indicator: Indicator | None, value, prior) -> str | None:
    if value is None or indicator is None:
        return None
    if not isinstance(prior, (int, float)):
        return "baseline"
    if abs(value - prior) < 1e-9:
        return "stable"
    return "improving" if (value > prior) == indicator.higher_is_better else "degrading"


def frozen_indicators(snapshot: dict, rated: list[dict] | None, prior: list[dict] | None) -> tuple[list[dict], list[str]]:
    """The published rows (computed value, unit, basis, band, prior value, trend, the auditor's status and notes)
    and the ids still needing a rating: every computable indicator that has data in the period."""
    ratings = {row.get("indicator_id"): row for row in rated or [] if isinstance(row, dict)}
    priors = {row.get("indicator_id"): row.get("measured_value") for row in prior or [] if isinstance(row, dict)}
    rows, missing = [], []
    for computed in snapshot["indicators"]:
        indicator_id = computed["indicator_id"]
        rating = ratings.get(indicator_id, {})
        status = rating.get("status") if rating.get("status") in RATINGS else None
        if computed["computable"] and computed["measured_value"] is not None and status is None:
            missing.append(indicator_id)
        prior_value = priors.get(indicator_id)
        rows.append({
            "indicator_id": indicator_id,
            "indicator_name": computed["name"],
            "measured_value": computed["measured_value"],
            "unit": computed["unit"],
            "computable": computed["computable"],
            "basis": computed["basis"],
            "band": computed["band"],
            "status": status,
            "notes": rating.get("notes"),
            "prior_value": prior_value if isinstance(prior_value, (int, float)) else None,
            "trend": _trend(INDICATOR_BY_ID.get(indicator_id), computed["measured_value"], prior_value),
        })
    return rows, missing


async def latest_published_audit(session, ecosystem_id) -> GovernanceHealthAudit | None:
    """The newest published audit of the ecosystem (drafts never count)."""
    return (await session.execute(select(GovernanceHealthAudit).where(
        GovernanceHealthAudit.ecosystem_id == ecosystem_id, GovernanceHealthAudit.status == AUDIT_PUBLISHED,
    ).order_by(GovernanceHealthAudit.audit_date.desc().nulls_last(), GovernanceHealthAudit.updated_at.desc(),
               GovernanceHealthAudit.created_at.desc()).limit(1)
    )).scalar_one_or_none()


async def audit_due_date(session, ecosystem_id, latest: GovernanceHealthAudit | None = None) -> _dt.date | None:
    """When the next audit is due (framework C, E.10): the earliest of a quarter after the latest published audit,
    30 days after an emergency that closed since then, or, never audited, a quarter after the ecosystem began."""
    if latest is not None:
        since = latest.audit_date or (latest.created_at.date() if latest.created_at else None)
        candidates = [latest.next_audit_due or (since + _dt.timedelta(days=AUDIT_INTERVAL_DAYS) if since else None)]
    else:
        created = await session.scalar(select(Ecosystem.created_at).where(Ecosystem.id == ecosystem_id))
        since = created.date() if created else None
        candidates = [since + _dt.timedelta(days=AUDIT_INTERVAL_DAYS) if since else None]
    closed = select(EmergencyState.closed_at).where(
        EmergencyState.ecosystem_id == ecosystem_id, EmergencyState.closed_at.is_not(None),
        EmergencyState.state == "closed",
    )
    for closed_at in (await session.execute(closed)).scalars():
        if since is None or closed_at.date() >= since:
            candidates.append(closed_at.date() + _dt.timedelta(days=POST_EMERGENCY_AUDIT_DAYS))
    return min((day for day in candidates if day is not None), default=None)


async def has_independent_member(session, ecosystem_id) -> bool:
    """An active member who is not a steward exists there (who may audit): policy.can_administer_ecosystem's steward,
    so neither mod+ nor a co_creator/builder row (a founder) counts as independent (FX-Maint, A5/F8)."""
    return bool(await session.scalar(select(func.count(Member.id)).where(
        Member.ecosystem_id == ecosystem_id, Member.current_status == "active", Member.role.notin_(LEADERSHIP_ROLES),
        or_(Member.profile.is_(None), Member.profile.notin_(PROFILE_ADMINS)),
    )))


# ---------------------------------------------------------------------------
# FX-Maint: drafts that stop holding the reminder (F6), and the records stewards write on an audit (F6, F7)
# ---------------------------------------------------------------------------

AUDIT_DRAFT = "draft"
AUDIT_ABANDONED = "abandoned"
STALE_DRAFT_DAYS = 30  # a draft untouched this long no longer silences audit_due (services/AGENTS.md "FX-Maint")
AUDIT_RESPONSE_SKILL = "audit-response"  # DecisionRecord.source_skill of a steward's response to a published audit
AUDIT_ABANDON_SKILL = "audit-abandonment"  # ... of an abandoned draft


def _member_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


async def audit_drafts(session, ecosystem_id, now: _dt.datetime | None = None) -> tuple[list, list]:
    """(live, stale) drafts of the ecosystem: live = touched in the last STALE_DRAFT_DAYS by an auditor still active there."""
    now = dates.naive_utc(now or dates.utc_now())
    drafts = (await session.execute(select(GovernanceHealthAudit).where(
        GovernanceHealthAudit.ecosystem_id == ecosystem_id, GovernanceHealthAudit.status == AUDIT_DRAFT,
    ).order_by(GovernanceHealthAudit.created_at))).scalars().all()
    if not drafts:
        return [], []
    auditors = {parsed for draft in drafts for parsed in map(_member_uuid, draft.auditor_ids or []) if parsed}
    active = set((await session.execute(select(Member.id).where(
        Member.id.in_(auditors), Member.ecosystem_id == ecosystem_id, Member.current_status == "active",
    ))).scalars()) if auditors else set()
    live, stale = [], []
    for draft in drafts:
        touched = draft.updated_at or draft.created_at
        fresh = touched is not None and dates.naive_utc(touched) >= now - _dt.timedelta(days=STALE_DRAFT_DAYS)
        held = any(_member_uuid(member_id) in active for member_id in draft.auditor_ids or [])
        (live if fresh and held else stale).append(draft)
    return live, stale


async def audit_record(session, audit_id, skill: str) -> DecisionRecord | None:
    """The latest DecisionRecord a steward wrote on this audit (`skill`: a response, or an abandoned draft)."""
    return (await session.execute(select(DecisionRecord).where(
        DecisionRecord.artifact_type == "audit", DecisionRecord.artifact_reference == str(audit_id),
        DecisionRecord.source_skill == skill,
    ).order_by(DecisionRecord.created_at.desc()).limit(1))).scalar_one_or_none()
