"""Consent-scoped discovery and evidence-weighted fit; see api/ORIENTATION_MATCHING.md."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import uuid
from sqlalchemy import delete, select
from neos_agent.api.errors import ApiError
from neos_agent.db.models import Agreement, Domain, Ecosystem, EcosystemMatchingProfile, MatchingAnswers, MatchingAssessment, MatchingConsent, Member, OrientationChatSession, User

ALGORITHM_VERSION = "affinity-v1"
DIMENSIONS = ("agreements", "domains", "purpose", "practical")
CHOICES = {"supports": 1.0, "discuss": 0.5, "incompatible": 0.0, "unknown": None}
CLASSIFICATIONS = {"non_negotiable", "discussion_required", "informational"}
DOMAIN_CONTRACT_FIELDS = ("key_responsibilities", "customers", "deliverables", "dependencies", "constraints", "challenges", "resources", "delegator_responsibilities", "competencies", "metrics", "evaluation_schedule")


def utc_stamp(value):
    if value is None:
        return None
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def lock_matching_owner(db, user_id):
    """Serialize private matching writes and erasure on the persistent owner row."""
    if await db.scalar(select(User.id).where(User.id == user_id).with_for_update()) is None:
        raise ApiError(401, "Matching-data owner is unavailable")


async def cleanup_private_discovery(factory, now=None):
    """Expire purpose-limited discovery records; see api/ORIENTATION_MATCHING.md."""
    now = now or datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc).replace(tzinfo=None) if now.tzinfo else now
    cutoff = now - timedelta(days=365)
    async with factory() as db:
        owners = set()
        for model in (MatchingAnswers, MatchingAssessment, MatchingConsent):
            owners.update((await db.scalars(select(model.user_id).where(model.updated_at < cutoff))).all())
    for owner_id in sorted(owners, key=str):
        async with factory() as db:
            await lock_matching_owner(db, owner_id)
            expired_scopes = (await db.scalars(select(MatchingConsent.ecosystem_id).where(MatchingConsent.user_id == owner_id, MatchingConsent.updated_at < cutoff))).all()
            for model in (MatchingAnswers, MatchingAssessment):
                await db.execute(delete(model).where(model.user_id == owner_id, model.updated_at < cutoff))
                if expired_scopes:
                    await db.execute(delete(model).where(model.user_id == owner_id, model.ecosystem_id.in_(expired_scopes)))
            await db.execute(delete(MatchingConsent).where(MatchingConsent.user_id == owner_id, MatchingConsent.updated_at < cutoff))
            await db.commit()
    async with factory() as db:
        await db.execute(delete(OrientationChatSession).where(OrientationChatSession.updated_at < now - timedelta(days=90)))
        await db.commit()


async def visible_ecosystem(db, ecosystem_id, owner_id):
    eco = await db.get(Ecosystem, ecosystem_id)
    row = await db.scalar(select(Member).where(Member.user_id == owner_id, Member.ecosystem_id == ecosystem_id)) if owner_id else None
    if eco is None or (eco.visibility != "public" and (row is None or row.current_status not in ("active", "pending_consent"))):
        raise ApiError(404, "Ecosystem not found")
    return eco, row


async def validate_uaf_reference(db, ecosystem_id, agreement_id):
    """A UAF pointer names an existing active UAF in the same ecosystem."""
    if agreement_id is None:
        return
    agreement = await db.get(Agreement, agreement_id)
    if agreement is None or agreement.ecosystem_id != ecosystem_id or agreement.status != "active" or agreement.type != "uaf":
        raise ApiError(400, "Choose an active UAF agreement from this ecosystem; create and ratify it before linking it")


async def latest_profile(db, ecosystem_id):
    return await db.scalar(select(EcosystemMatchingProfile).where(EcosystemMatchingProfile.ecosystem_id == ecosystem_id).order_by(EcosystemMatchingProfile.created_at.desc(), EcosystemMatchingProfile.id.desc()).limit(1))


def _positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 < value <= 1000


def validate_configuration(configuration):
    if not isinstance(configuration, dict) or set(configuration) != {"version", "algorithm_version", "weights", "signals"}:
        raise ApiError(400, "The approved matching profile needs version, algorithm_version, weights and signals")
    if configuration["algorithm_version"] != ALGORITHM_VERSION or not isinstance(configuration["version"], str) or not 1 <= len(configuration["version"]) <= 80:
        raise ApiError(400, "Use a named profile version and the published affinity-v1 algorithm")
    weights = configuration["weights"]
    if not isinstance(weights, dict) or set(weights) != set(DIMENSIONS) or not all(_positive(weight) for weight in weights.values()) or not math.isclose(sum(weights.values()), 1.0, abs_tol=0.000001):
        raise ApiError(400, "Publish all four positive dimension weights, adding up to 1")
    signals = configuration["signals"]
    if not isinstance(signals, list) or not 4 <= len(signals) <= 80:
        raise ApiError(400, "Publish between 4 and 80 voluntary matching signals")
    ids = set()
    for signal in signals:
        if not isinstance(signal, dict) or set(signal) != {"id", "dimension", "label", "weight", "classification", "source"}:
            raise ApiError(400, "Each signal needs id, dimension, label, weight, classification and a versioned source")
        if not isinstance(signal["id"], str) or not 1 <= len(signal["id"]) <= 80 or signal["id"] in ids or not isinstance(signal["dimension"], str) or signal["dimension"] not in DIMENSIONS or not _positive(signal["weight"]) or not isinstance(signal["classification"], str) or signal["classification"] not in CLASSIFICATIONS:
            raise ApiError(400, "Signal identifiers, dimensions, weights or classifications are invalid")
        if not isinstance(signal["label"], str) or not 1 <= len(signal["label"]) <= 500:
            raise ApiError(400, "Each signal needs a plain-language question of at most 500 characters")
        source = signal["source"]
        if not isinstance(source, dict) or set(source) != {"kind", "id", "version", "section"} or not isinstance(source["kind"], str) or source["kind"] not in {"agreement", "domain"} or not isinstance(source["section"], str) or not 1 <= len(source["section"]) <= 200:
            raise ApiError(400, "Every signal needs a source agreement/domain id, version and section")
        try:
            uuid.UUID(str(source["id"]))
        except (TypeError, ValueError):
            raise ApiError(400, "A matching source id is invalid") from None
        if signal["classification"] == "non_negotiable" and source["kind"] != "agreement":
            raise ApiError(400, "Only a ratified agreement provision may be classified as a non-negotiable")
        ids.add(signal["id"])
    if {signal["dimension"] for signal in signals} != set(DIMENSIONS):
        raise ApiError(400, "The published profile must cover all four dimensions")
    return configuration


async def source_versions(db, ecosystem, configuration, governing=None):
    await validate_uaf_reference(db, ecosystem.id, ecosystem.uaf_agreement_id)
    snapshots = []
    seen = {}
    for signal in configuration["signals"]:
        source = signal["source"]
        key = (source["kind"], str(source["id"]))
        if key in seen:
            if seen[key] != source["version"]:
                raise ApiError(409, "One source cannot name two different versions", {"code": "MATCHING_SOURCE_STALE"})
            continue
        seen[key] = source["version"]
        model = Agreement if source["kind"] == "agreement" else Domain
        record = await db.get(model, uuid.UUID(str(source["id"])))
        if record is None or record.ecosystem_id != ecosystem.id or record.status != "active" or record.version != source["version"]:
            raise ApiError(409, "A source is missing, outside this ecosystem, unratified, or on a different version", {"code": "MATCHING_SOURCE_STALE"})
        if isinstance(record, Domain):
            missing = [field for field in DOMAIN_CONTRACT_FIELDS if not isinstance(record.elements, dict) or record.elements.get(field) is None or record.elements.get(field) == ""]
            if not record.purpose or missing:
                raise ApiError(409, "A source domain's governed contract is incomplete; document its required elements before using it for fit", {"code": "MATCHING_PROFILE_INCOMPLETE", "missing_fields": missing, "domain_url": f"/domains/{record.id}"})
        fingerprint = hashlib.sha256(json.dumps({"version": record.version, "status": record.status, "text": record.text if isinstance(record, Agreement) else record.purpose,
                                                "elements": record.elements if isinstance(record, Domain) else record.act_policy}, sort_keys=True, default=str).encode()).hexdigest()
        snapshots.append({"kind": source["kind"], "id": str(record.id), "version": record.version, "status": record.status,
                          "review_date": str(record.review_date) if isinstance(record, Agreement) and record.review_date else None,
                          "fingerprint": fingerprint,
                          "url": f"/{'agreements' if isinstance(record, Agreement) else 'domains'}/{record.id}"})
    if not ecosystem.uaf_agreement_id or ("agreement", str(ecosystem.uaf_agreement_id)) not in seen or not any(kind == "domain" for kind, _ in seen):
        raise ApiError(409, "The profile must cite the ecosystem's ratified UAF and at least one documented domain", {"code": "MATCHING_PROFILE_INCOMPLETE"})
    if governing is not None and ("agreement", str(governing.id)) not in seen:
        fingerprint = hashlib.sha256(json.dumps({"version": governing.version, "status": governing.status, "text": governing.text, "elements": governing.act_policy}, sort_keys=True, default=str).encode()).hexdigest()
        snapshots.append({"kind": "agreement", "id": str(governing.id), "version": governing.version, "status": governing.status,
                          "review_date": str(governing.review_date) if governing.review_date else None, "fingerprint": fingerprint,
                          "url": f"/agreements/{governing.id}"})
    return snapshots


async def profile_current(db, ecosystem, profile):
    if profile is None:
        return False, []
    try:
        governed = await db.get(Agreement, profile.governing_agreement_id)
        current = await source_versions(db, ecosystem, profile.configuration, governed)
        approved = (governed.act_policy or {}).get("matching_profile") if governed and governed.status == "active" else None
        return current == profile.source_versions and approved == profile.configuration, current
    except ApiError:
        return False, []


def calculate(configuration, answers):
    dimensions = []
    reasons = []
    tensions = []
    missing = []
    non_negotiable_conflict = False
    numerator = denominator = coverage = 0.0
    for dimension in DIMENSIONS:
        signals = [signal for signal in configuration["signals"] if signal["dimension"] == dimension]
        total = sum(signal["weight"] for signal in signals)
        answered_weight = weighted_value = 0.0
        for signal in signals:
            choice = answers.get(signal["id"], "unknown")
            value = CHOICES.get(choice)
            evidence = {"signal_id": signal["id"], "label": signal["label"], "choice": choice, "source": signal["source"]}
            if choice == "incompatible" and signal["classification"] == "informational":
                tensions.append(evidence)
                value = None
            if value is None:
                missing.append(evidence)
                continue
            answered_weight += signal["weight"]
            weighted_value += signal["weight"] * value
            if choice == "supports":
                reasons.append(evidence)
            else:
                tensions.append(evidence)
            if choice == "incompatible" and signal["classification"] == "non_negotiable":
                non_negotiable_conflict = True
        dimension_coverage = answered_weight / total
        score = 100 * weighted_value / answered_weight if answered_weight else None
        weight = configuration["weights"][dimension]
        coverage += weight * dimension_coverage
        if score is not None:
            numerator += weight * dimension_coverage * score
            denominator += weight * dimension_coverage
        dimensions.append({"dimension": dimension, "weight": weight, "coverage": round(dimension_coverage, 6), "fit_estimate": round(score, 2) if score is not None else None})
    fit = round(numerator / denominator, 2) if denominator and coverage >= 0.6 else None
    status = "not_currently_recommended" if non_negotiable_conflict else "more_to_learn" if coverage < 0.6 else "discuss_before_deciding" if tensions else "promising_to_explore"
    return {"status": status, "fit_estimate": fit, "coverage": round(coverage, 6), "dimensions": dimensions,
            "why": reasons[:3], "tensions": tensions, "missing": missing, "algorithm_version": ALGORITHM_VERSION,
            "profile_version": configuration["version"], "weights": configuration["weights"],
            "limitations": "Decision support only. This does not grant membership, admission, a role, or contact access."}


async def fit_result(db, ecosystem, owner_id):
    profile = await latest_profile(db, ecosystem.id)
    current, sources = await profile_current(db, ecosystem, profile)
    consent = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner_id, MatchingConsent.ecosystem_id == ecosystem.id))
    answers = await db.scalar(select(MatchingAnswers).where(MatchingAnswers.user_id == owner_id, MatchingAnswers.ecosystem_id == ecosystem.id))
    base = {"status": "unavailable", "fit_estimate": None, "coverage": 0, "algorithm_version": ALGORITHM_VERSION, "profile_version": profile.version if profile else None,
            "dimensions": [], "why": [], "tensions": [], "missing": [], "source_versions": sources,
            "next_action": {"label": "Read the ecosystem dossier", "url": f"/ecosystems/{ecosystem.id}"}}
    if not current:
        return {**base, "reason": "Fit estimate unavailable—governance profile incomplete or outdated", "stale": profile is not None}
    if not consent or not consent.matching_enabled:
        return {**base, "status": "consent_required", "reason": "Choose whether to use your voluntary answers for this ecosystem's fit check", "stale": False}
    if answers and answers.paused:
        return {**base, "status": "paused", "reason": "Your matching profile is paused", "stale": False}
    if answers and answers.profile_version != profile.version:
        return {**base, "status": "outdated", "reason": "The published profile changed. Review its sources and answer the current signals.", "stale": True}
    return {**calculate(profile.configuration, answers.answers if answers else {}), "source_versions": sources, "stale": False, "next_action": base["next_action"]}
