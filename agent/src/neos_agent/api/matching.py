"""Owner-controlled matching and consented participant discovery; see ORIENTATION_MATCHING.md."""
from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
import uuid
from urllib.parse import quote
from sanic import Blueprint, json
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError
from neos_agent.api.helpers import require_auth_user
from neos_agent.api.policy import can_administer_ecosystem
from neos_agent.db.models import Agreement, Ecosystem, EcosystemMatchingProfile, EthosUserAccess, MatchingAnswers, MatchingAssessment, MatchingConsent, Member, User
from neos_agent.services.matching import ALGORITHM_VERSION, CHOICES, fit_result, latest_profile, lock_matching_owner, profile_current, source_versions, utc_stamp, validate_configuration, visible_ecosystem

matching_api_bp = Blueprint("matching_api", url_prefix="/api/v1/matching")


def _body(request, allowed):
    body = request.json
    if not isinstance(body, dict) or set(body) - set(allowed):
        raise ApiError(400, "Only the documented matching fields may be supplied")
    return body


async def _owner(request):
    owner, error = require_auth_user(request)
    if error:
        raise ApiError(401, "Authentication required")
    return owner


async def _purge_matching(db, user_id, ecosystem_id=None):
    for model in (MatchingAssessment, MatchingAnswers):
        query = delete(model).where(model.user_id == user_id)
        if ecosystem_id:
            query = query.where(model.ecosystem_id == ecosystem_id)
        await db.execute(query)


def _consent_payload(row):
    return {key: bool(getattr(row, key, False)) for key in ("directory_visible", "contact_discovery", "matching_enabled")}


def _audited_publication(handler):
    @wraps(handler)
    async def guarded(request, *args, **kwargs):
        try:
            return await handler(request, *args, **kwargs)
        except (ApiError, IntegrityError) as error:
            owner = getattr(request.ctx, "user", None)
            body = request.json if isinstance(request.json, dict) else {}
            if owner is not None and "support_reason" in body:
                from neos_agent.services.node_admin import log_failure
                try:
                    await log_failure(request.app.ctx.db, owner.id, "publish_matching_profile", "ecosystem_matching_profiles", organization_id=kwargs.get("ecosystem_id"),
                                      reason="Organization support", outcome="denied" if isinstance(error, ApiError) and error.status == 403 else "failed", source="ui")
                except Exception:
                    raise ApiError(503, "The support audit is unavailable; no matching profile was published") from None
            if isinstance(error, IntegrityError):
                raise ApiError(409, "This matching-profile version was published concurrently; reload before continuing") from None
            raise
    return guarded


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/consent")
async def get_consent(request, ecosystem_id):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        await visible_ecosystem(db, ecosystem_id, owner.id)
        row = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == ecosystem_id))
        return json(_consent_payload(row))


@matching_api_bp.put("/ecosystems/<ecosystem_id:uuid>/consent")
async def update_consent(request, ecosystem_id):
    owner = await _owner(request)
    body = _body(request, ("directory_visible", "contact_discovery", "matching_enabled"))
    if not body or any(type(value) is not bool for value in body.values()):
        raise ApiError(400, "Consent choices must be explicit true or false values")
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        _, member = await visible_ecosystem(db, ecosystem_id, owner.id)
        if any(body.get(key) for key in ("directory_visible", "contact_discovery")) and (member is None or member.current_status != "active"):
            raise ApiError(403, "Active membership is required to appear in this ecosystem's participant discovery")
        row = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == ecosystem_id).with_for_update())
        if row is None:
            row = MatchingConsent(id=uuid.uuid4(), user_id=owner.id, ecosystem_id=ecosystem_id, directory_visible=False, contact_discovery=False, matching_enabled=False)
            db.add(row)
        for key, value in body.items():
            setattr(row, key, value)
        if body.get("matching_enabled") is False:
            await _purge_matching(db, owner.id, ecosystem_id)
        await db.commit()
        return json(_consent_payload(row))


def _tags(value):
    return [item.strip()[:100] for item in value[:30] if isinstance(item, str) and item.strip()] if isinstance(value, list) else []


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/participants")
async def participants(request, ecosystem_id):
    owner = await _owner(request)
    query = str(request.args.get("q", "")).strip().casefold()[:100]
    try:
        page = max(1, min(1000, int(request.args.get("page", "1"))))
    except ValueError:
        raise ApiError(400, "Page must be a whole number") from None
    async with request.app.ctx.db() as db:
        _, member = await visible_ecosystem(db, ecosystem_id, owner.id)
        if member is None or member.current_status != "active":
            raise ApiError(403, "Active membership is required to see protected participant discovery")
        access = await db.scalar(select(EthosUserAccess.id).where(EthosUserAccess.member_id == member.id, EthosUserAccess.ecosystem_id == ecosystem_id))
        own = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == ecosystem_id))
        if access is None or not own or not own.directory_visible or not own.contact_discovery:
            return json({"items": [], "total": 0, "state": "consent_required", "algorithm_version": "declared-overlap-v1", "next_action": {"label": "Choose separate participation, directory and contact permissions", "url": f"/ethos/{ecosystem_id}"}})
        rows = (await db.execute(select(User, Member.id).join(Member, Member.user_id == User.id).join(MatchingConsent, MatchingConsent.user_id == User.id).join(EthosUserAccess, EthosUserAccess.member_id == Member.id).where(
            Member.ecosystem_id == ecosystem_id, Member.current_status == "active", MatchingConsent.ecosystem_id == ecosystem_id,
            EthosUserAccess.ecosystem_id == ecosystem_id, MatchingConsent.directory_visible.is_(True), MatchingConsent.contact_discovery.is_(True),
            User.disabled_at.is_(None), User.id != owner.id).order_by(User.display_name, User.id).limit(1001))).unique().all()
        owner_skills = {tag.casefold() for tag in _tags(owner.skills)}
        owner_interests = {tag.casefold() for tag in _tags(owner.interests)}
        items = []
        for user, member_id in rows:
            skills, interests = _tags(user.skills), _tags(user.interests)
            if query and not any(query in text.casefold() for text in [user.display_name, user.headline or "", *skills, *interests]):
                continue
            items.append({"user_id": str(user.id), "member_id": str(member_id), "display_name": user.display_name, "headline": user.headline,
                          "skills": skills, "interests": interests, "profile_url": f"/users/{quote(user.username or str(user.id), safe='')}",
                          "shared_skills": [tag for tag in skills if tag.casefold() in owner_skills],
                          "shared_interests": [tag for tag in interests if tag.casefold() in owner_interests],
                          "contact_url": f"/messaging?member={member_id}"})
        return json({"items": items[(page - 1) * 20:page * 20], "total": len(items), "truncated": len(rows) > 1000,
                     "state": "ready" if items else "empty", "algorithm_version": "declared-overlap-v1",
                     "explanation": "An alphabetical directory of people who opted into discovery and contact here. Shared tags use only voluntarily published skills and interests; they are not a fit score or admission decision."})


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/matching-profile")
async def get_matching_profile(request, ecosystem_id):
    owner_id = getattr(getattr(request.ctx, "user", None), "id", None)
    async with request.app.ctx.db() as db:
        ecosystem, _ = await visible_ecosystem(db, ecosystem_id, owner_id)
        profile = await latest_profile(db, ecosystem_id)
        current, _ = await profile_current(db, ecosystem, profile)
        return json({"available": bool(current), "profile": {"id": str(profile.id), **profile.configuration, "source_versions": profile.source_versions, "published_at": utc_stamp(profile.created_at)} if profile else None,
                     "reason": None if current else "Fit estimate unavailable—governance profile incomplete or outdated"})


@matching_api_bp.post("/ecosystems/<ecosystem_id:uuid>/matching-profile")
@_audited_publication
async def publish_matching_profile(request, ecosystem_id):
    owner = await _owner(request)
    body = _body(request, ("governing_agreement_id", "support_reason"))
    try:
        agreement_id = uuid.UUID(str(body.get("governing_agreement_id", "")))
    except ValueError:
        raise ApiError(400, "Choose the ratified matching-policy agreement") from None
    async with request.app.ctx.db() as db:
        support_actor = None
        if "support_reason" in body:
            from neos_agent.services.node_admin import PUBLIC_REASONS, authorize
            if not isinstance(body["support_reason"], str) or body["support_reason"] not in PUBLIC_REASONS:
                raise ApiError(400, "Choose a public support reason category")
            support_actor = await authorize(db, owner.id)
            ecosystem = await db.get(Ecosystem, ecosystem_id)
            if ecosystem is None:
                raise ApiError(404, "Ecosystem not found")
        else:
            ecosystem, member = await visible_ecosystem(db, ecosystem_id, owner.id)
            if not can_administer_ecosystem(member, ecosystem_id):
                raise ApiError(403, "Only a steward can publish this profile; node support requires an explicit audited support reason")
        agreement = await db.get(Agreement, agreement_id)
        if agreement is None or agreement.ecosystem_id != ecosystem_id or agreement.status != "active":
            raise ApiError(409, "Publish only a matching policy already ratified in this ecosystem")
        configuration = validate_configuration((agreement.act_policy or {}).get("matching_profile"))
        if await db.scalar(select(EcosystemMatchingProfile.id).where(EcosystemMatchingProfile.ecosystem_id == ecosystem_id, EcosystemMatchingProfile.version == configuration["version"])):
            raise ApiError(409, "That published matching-profile version already exists; ratify a new version to change it")
        sources = await source_versions(db, ecosystem, configuration, agreement)
        row = EcosystemMatchingProfile(id=uuid.uuid4(), ecosystem_id=ecosystem_id, version=configuration["version"], governing_agreement_id=agreement.id,
                                       configuration=configuration, source_versions=sources, published_by_user_id=owner.id)
        db.add(row)
        event = None
        if support_actor is not None:
            from neos_agent.services.node_admin import audit_event
            event = audit_event(support_actor, "publish_matching_profile", "ecosystem_matching_profiles", row.id, organization_id=ecosystem_id,
                                reason=body["support_reason"], source="ui", fields=("governing_agreement_id", "version"), summary={"approved_policy_only": True})
            db.add(event)
        await db.commit()
        return json({"id": str(row.id), "version": row.version, "published": True, **({"audit_id": str(event.id), "audit_url": f"/node/audit/{event.id}"} if event else {})}, status=201)


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/profile")
async def owner_profile(request, ecosystem_id):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        await visible_ecosystem(db, ecosystem_id, owner.id)
        row = await db.scalar(select(MatchingAnswers).where(MatchingAnswers.user_id == owner.id, MatchingAnswers.ecosystem_id == ecosystem_id))
        return json({"profile_version": row.profile_version if row else None, "answers": row.answers if row else {}, "paused": bool(row.paused) if row else False})


@matching_api_bp.put("/ecosystems/<ecosystem_id:uuid>/profile")
async def save_owner_profile(request, ecosystem_id):
    owner = await _owner(request)
    body = _body(request, ("profile_version", "answers", "paused"))
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        ecosystem, _ = await visible_ecosystem(db, ecosystem_id, owner.id)
        consent = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == ecosystem_id))
        if not consent or not consent.matching_enabled:
            raise ApiError(403, "Choose matching-data consent before saving private answers")
        profile = await latest_profile(db, ecosystem_id)
        current, _ = await profile_current(db, ecosystem, profile)
        if not current or body.get("profile_version") != profile.version:
            raise ApiError(409, "Read the current published matching profile before answering its signals")
        answers = body.get("answers", {})
        signal_ids = {signal["id"] for signal in profile.configuration["signals"]}
        if not isinstance(answers, dict) or set(answers) - signal_ids or any(not isinstance(value, str) or value not in CHOICES for value in answers.values()) or type(body.get("paused", False)) is not bool:
            raise ApiError(400, "Use the published signals and the documented optional answer choices")
        row = await db.scalar(select(MatchingAnswers).where(MatchingAnswers.user_id == owner.id, MatchingAnswers.ecosystem_id == ecosystem_id).with_for_update())
        if row is None:
            row = MatchingAnswers(user_id=owner.id, ecosystem_id=ecosystem_id, profile_version=profile.version)
            db.add(row)
        row.answers, row.profile_version, row.paused = answers, profile.version, body.get("paused", False)
        await db.commit()
        return json({"profile_version": row.profile_version, "answers": row.answers, "paused": row.paused})


@matching_api_bp.delete("/ecosystems/<ecosystem_id:uuid>/profile")
async def delete_owner_profile(request, ecosystem_id):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        await _purge_matching(db, owner.id, ecosystem_id)
        consent = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == ecosystem_id))
        if consent:
            consent.matching_enabled = False
        await db.commit()
    return json({"deleted": True, "matching_enabled": False})


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/fit")
async def fit(request, ecosystem_id):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        ecosystem, _ = await visible_ecosystem(db, ecosystem_id, owner.id)
        return json(await fit_result(db, ecosystem, owner.id))


@matching_api_bp.post("/ecosystems/<ecosystem_id:uuid>/assessments")
async def create_assessment(request, ecosystem_id):
    owner = await _owner(request)
    _body(request, ())
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        ecosystem, _ = await visible_ecosystem(db, ecosystem_id, owner.id)
        result = await fit_result(db, ecosystem, owner.id)
        if result["status"] in {"unavailable", "paused", "consent_required", "outdated"}:
            raise ApiError(409, result.get("reason", "Matching is unavailable"))
        profile = await latest_profile(db, ecosystem_id)
        answers = await db.scalar(select(MatchingAnswers).where(MatchingAnswers.user_id == owner.id, MatchingAnswers.ecosystem_id == ecosystem_id))
        count = await db.scalar(select(func.count()).select_from(MatchingAssessment).where(MatchingAssessment.user_id == owner.id, MatchingAssessment.ecosystem_id == ecosystem_id))
        if count >= 100:
            raise ApiError(409, "You have 100 saved assessments for this ecosystem. Export or delete your matching data before saving more.")
        snapshot = {"algorithm_version": ALGORITHM_VERSION, "profile_version": profile.version, "configuration": profile.configuration,
                    "answers": answers.answers if answers else {}, "source_versions": profile.source_versions, "result": result, "calculated_at": utc_stamp(datetime.now(timezone.utc))}
        row = MatchingAssessment(user_id=owner.id, ecosystem_id=ecosystem_id, profile_id=profile.id, snapshot=snapshot, corrections=[])
        db.add(row)
        await db.commit()
        return json({"id": str(row.id), **snapshot, "stale": False}, status=201)


@matching_api_bp.get("/ecosystems/<ecosystem_id:uuid>/assessments")
async def assessments(request, ecosystem_id):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        ecosystem, _ = await visible_ecosystem(db, ecosystem_id, owner.id)
        current = await latest_profile(db, ecosystem_id)
        valid, _ = await profile_current(db, ecosystem, current)
        answers = await db.scalar(select(MatchingAnswers).where(MatchingAnswers.user_id == owner.id, MatchingAnswers.ecosystem_id == ecosystem_id))
        rows = (await db.scalars(select(MatchingAssessment).where(MatchingAssessment.user_id == owner.id, MatchingAssessment.ecosystem_id == ecosystem_id).order_by(MatchingAssessment.created_at.desc()).limit(50))).all()
        return json({"items": [{"id": str(row.id), "snapshot": row.snapshot, "corrections": row.corrections, "stale": not valid or row.profile_id != current.id or row.snapshot.get("answers", {}) != (answers.answers if answers else {})} for row in rows]})


@matching_api_bp.post("/assessments/<assessment_id:uuid>/corrections")
async def correction(request, assessment_id):
    owner = await _owner(request)
    body = _body(request, ("message",))
    if not isinstance(body.get("message"), str) or not 1 <= len(body["message"].strip()) <= 2000:
        raise ApiError(400, "Describe your correction in 1–2000 characters")
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        row = await db.scalar(select(MatchingAssessment).where(MatchingAssessment.id == assessment_id, MatchingAssessment.user_id == owner.id).with_for_update())
        if row is None:
            raise ApiError(404, "Assessment not found")
        consent = await db.scalar(select(MatchingConsent).where(MatchingConsent.user_id == owner.id, MatchingConsent.ecosystem_id == row.ecosystem_id))
        if not consent or not consent.matching_enabled:
            raise ApiError(403, "Matching consent is required to add private correction notes")
        if len(row.corrections or []) >= 20:
            raise ApiError(409, "This assessment already has 20 correction notes; export them or make a new assessment")
        row.corrections = list(row.corrections or []) + [{"message": body["message"].strip(), "created_at": utc_stamp(datetime.now(timezone.utc)), "status": "recorded_for_owner_review"}]
        await db.commit()
        profile = await db.get(EcosystemMatchingProfile, row.profile_id)
        next_action = {"label": "Follow the correction process in the ratified matching-policy agreement", "url": f"/agreements/{profile.governing_agreement_id}"}
    return json({"recorded": True, "message": "Your correction is saved privately. It does not change the source agreement or your original assessment.", "next_action": next_action}, status=201)


@matching_api_bp.get("/me/export")
async def export_data(request):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        consent = (await db.scalars(select(MatchingConsent).where(MatchingConsent.user_id == owner.id))).all()
        answers = (await db.scalars(select(MatchingAnswers).where(MatchingAnswers.user_id == owner.id))).all()
        rows = (await db.scalars(select(MatchingAssessment).where(MatchingAssessment.user_id == owner.id))).all()
        return json({"exported_at": utc_stamp(datetime.now(timezone.utc)), "consents": [{"ecosystem_id": str(row.ecosystem_id), **_consent_payload(row)} for row in consent],
                     "profiles": [{"ecosystem_id": str(row.ecosystem_id), "profile_version": row.profile_version, "answers": row.answers, "paused": row.paused} for row in answers],
                     "assessments": [{"id": str(row.id), "ecosystem_id": str(row.ecosystem_id), "snapshot": row.snapshot, "corrections": row.corrections} for row in rows]})


@matching_api_bp.delete("/me/profile")
async def erase_data(request):
    owner = await _owner(request)
    async with request.app.ctx.db() as db:
        await lock_matching_owner(db, owner.id)
        await _purge_matching(db, owner.id)
        await db.execute(delete(MatchingConsent).where(MatchingConsent.user_id == owner.id))
        await db.commit()
    return json({"deleted": True, "message": "Your matching answers, assessments, correction notes and discovery consents were deleted."})
