"""Always-public user profiles and authenticated owner updates."""

from __future__ import annotations

from collections import OrderedDict
import uuid

from pydantic import ValidationError
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.schemas.profiles import ProfileProject, ProfileUpdateRequest
from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import (
    CircleMembership,
    Domain,
    Ecosystem,
    Member,
    SharesNeeds,
    User,
)


profiles_api_bp = Blueprint("profiles_api", url_prefix="/api/v1/profiles")

def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _public_string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _public_social_links(value) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): url
        for key, url in value.items()
        if isinstance(key, str) and isinstance(url, str)
    }


def _public_projects(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    projects: list[dict] = []
    for item in value:
        try:
            projects.append(ProfileProject.model_validate(item).model_dump(mode="json"))
        except ValidationError:
            continue
    return projects


async def _resolve_profile_user(session, identifier: str) -> User | None:
    try:
        identifier_uuid = uuid.UUID(identifier)
    except ValueError:
        identifier_uuid = None

    if identifier_uuid:
        user = await session.get(User, identifier_uuid)
        if user:
            return user
        member_user_id = await session.scalar(
            select(Member.user_id).where(Member.id == identifier_uuid)
        )
        if member_user_id:
            return await session.get(User, member_user_id)

    return await session.scalar(
        select(User).where(func.lower(User.username) == identifier.casefold())
    )


async def _build_profile_response(
    session,
    user: User,
    viewer_user_id: uuid.UUID | None,
) -> dict:
    member_rows = (
        await session.execute(
            select(Member, Ecosystem)
            .join(Ecosystem, Member.ecosystem_id == Ecosystem.id)
            .where(
                Member.user_id == user.id,
                Member.current_status == "active",
            )
            .order_by(Ecosystem.name.asc(), Member.created_at.asc())
            .limit(100)
        )
    ).all()
    member_ids = [member.id for member, _ in member_rows]

    ecosystems = [
        {
            "id": str(ecosystem.id),
            "name": ecosystem.name,
            "description": ecosystem.description,
            "logo_url": ecosystem.logo_url,
            "location": ecosystem.location,
            "website": ecosystem.website,
            "membership": {
                "id": str(member.id),
                "member_id": member.member_id,
                "status": member.current_status,
                "profile": member.profile,
                "skills_offered": member.skills_offered,
                "skills_needed": member.skills_needed,
                "interests": member.interests,
                "created_at": _iso(member.created_at),
            },
        }
        for member, ecosystem in member_rows
    ]

    domains: list[dict] = []
    if member_ids:
        circle_rows = (
            await session.execute(
                select(CircleMembership, Domain, Ecosystem)
                .join(Domain, CircleMembership.domain_id == Domain.id)
                .join(Ecosystem, Domain.ecosystem_id == Ecosystem.id)
                .where(
                    CircleMembership.member_id.in_(member_ids),
                    CircleMembership.status == "active",
                )
                .order_by(Ecosystem.name.asc(), Domain.domain_id.asc())
                .limit(200)
            )
        ).all()
        domains = [
            {
                "id": str(domain.id),
                "domain_id": domain.domain_id,
                "purpose": domain.purpose,
                "status": domain.status,
                "role": (
                    "steward"
                    if domain.steward_id == membership.member_id
                    else "member"
                ),
                "joined_date": _iso(membership.joined_date),
                "ecosystem": {
                    "id": str(ecosystem.id),
                    "name": ecosystem.name,
                },
                "member_id": str(membership.member_id),
            }
            for membership, domain, ecosystem in circle_rows
        ]

    quiz_results: list[dict] = []
    publications: list[dict] = []
    if member_ids:
        result_rows = (
            await session.execute(
                select(QuizResult, Quiz, Course)
                .join(Quiz, QuizResult.quiz_id == Quiz.id)
                .outerjoin(Course, Quiz.course_id == Course.id)
                .where(
                    QuizResult.member_id.in_(member_ids),
                    QuizResult.completed_at.is_not(None),
                    Quiz.is_published.is_(True),
                    Quiz.visibility == "public",
                )
                .order_by(QuizResult.completed_at.desc())
                .limit(200)
            )
        ).all()

        quiz_domain_ids = {
            quiz.domain_id or (course.domain_id if course else None)
            for _, quiz, course in result_rows
            if quiz.domain_id or (course and course.domain_id)
        }
        quiz_ecosystem_ids = {
            quiz.ecosystem_id or (course.ecosystem_id if course else None)
            for _, quiz, course in result_rows
            if quiz.ecosystem_id or (course and course.ecosystem_id)
        }
        domain_map: dict[uuid.UUID, Domain] = {}
        if quiz_domain_ids:
            domain_rows = await session.scalars(
                select(Domain).where(Domain.id.in_(quiz_domain_ids))
            )
            domain_map = {domain.id: domain for domain in domain_rows}
            quiz_ecosystem_ids.update(domain.ecosystem_id for domain in domain_map.values())

        ecosystem_map: dict[uuid.UUID, Ecosystem] = {}
        if quiz_ecosystem_ids:
            ecosystem_rows = await session.scalars(
                select(Ecosystem).where(Ecosystem.id.in_(quiz_ecosystem_ids))
            )
            ecosystem_map = {
                ecosystem.id: ecosystem for ecosystem in ecosystem_rows
            }

        grouped: OrderedDict[uuid.UUID, dict] = OrderedDict()
        for result, quiz, course in result_rows:
            effective_domain_id = quiz.domain_id or (
                course.domain_id if course else None
            )
            domain = domain_map.get(effective_domain_id)
            effective_ecosystem_id = (
                quiz.ecosystem_id
                or (domain.ecosystem_id if domain else None)
                or (course.ecosystem_id if course else None)
            )
            ecosystem = ecosystem_map.get(
                effective_ecosystem_id
            )
            group = grouped.setdefault(
                quiz.id,
                {
                    "quiz": {
                        "id": str(quiz.id),
                        "title": quiz.title,
                        "description": quiz.description,
                        "mode": quiz.mode,
                    },
                    "domain": (
                        {
                            "id": str(domain.id),
                            "domain_id": domain.domain_id,
                            "purpose": domain.purpose,
                        }
                        if domain
                        else None
                    ),
                    "ecosystem": (
                        {"id": str(ecosystem.id), "name": ecosystem.name}
                        if ecosystem
                        else None
                    ),
                    "results": [],
                },
            )
            group["results"].append(
                {
                    "id": str(result.id),
                    "score": result.score,
                    "is_passed": result.is_passed,
                    "time_spent": result.time_spent,
                    "result_metadata": {},
                    "completed_at": _iso(result.completed_at),
                }
            )
        quiz_results = list(grouped.values())

        publication_rows = (
            await session.execute(
                select(SharesNeeds, Domain, Ecosystem)
                .join(Domain, SharesNeeds.domain_id == Domain.id)
                .join(Ecosystem, SharesNeeds.ecosystem_id == Ecosystem.id)
                .where(
                    SharesNeeds.author_member_id.in_(member_ids),
                    SharesNeeds.visibility == "public",
                    SharesNeeds.status == "active",
                )
                .order_by(SharesNeeds.created_at.desc())
                .limit(200)
            )
        ).all()
        publications = [
            {
                "id": str(record.id),
                "author_member_id": str(record.author_member_id),
                "ecosystem_id": str(ecosystem.id),
                "ecosystem_name": ecosystem.name,
                "domain_id": str(domain.id),
                "domain_name": domain.domain_id,
                "type": record.type,
                "title": record.title,
                "description": record.description,
                "category": record.category,
                "capacity": record.capacity,
                "tags": record.tags if isinstance(record.tags, list) else [],
                "visibility": record.visibility,
                "status": record.status,
                "domain": {
                    "id": str(domain.id),
                    "domain_id": domain.domain_id,
                    "purpose": domain.purpose,
                },
                "ecosystem": {
                    "id": str(ecosystem.id),
                    "name": ecosystem.name,
                },
                "created_at": _iso(record.created_at),
                "updated_at": _iso(record.updated_at),
            }
            for record, domain, ecosystem in publication_rows
        ]

    return {
        "profile": {
            "id": str(user.id),
            "username": user.username,
            "display_name": user.display_name,
            "profile_picture": user.profile_picture,
            "headline": user.headline,
            "bio": user.bio,
            "location": user.location,
            "website": user.website,
            "social_links": _public_social_links(user.social_links),
            "skills": _public_string_list(user.skills),
            "interests": _public_string_list(user.interests),
            "projects": _public_projects(user.projects),
            "created_at": _iso(user.created_at),
        },
        "ecosystems": ecosystems,
        "domains": domains,
        "quiz_results": quiz_results,
        "badges": [],
        "tags": [],
        "publications": publications,
        "is_owner": viewer_user_id == user.id,
    }


def _authenticated_user_id(request: Request) -> uuid.UUID | None:
    user = getattr(request.ctx, "user", None)
    return user.id if user else None


@profiles_api_bp.get("/me")
async def get_own_profile(request: Request):
    """Return the authenticated user's public profile."""
    user_id = _authenticated_user_id(request)
    if not user_id:
        return json({"error": "Authentication required"}, status=401)
    async with request.app.ctx.db() as session:
        user = await session.get(User, user_id)
        if not user:
            return json({"error": "Profile not found"}, status=404)
        response = await _build_profile_response(session, user, user_id)
    return json(response)


@profiles_api_bp.put("/me")
async def update_own_profile(request: Request):
    """Update public fields owned by the authenticated user."""
    user_id = _authenticated_user_id(request)
    if not user_id:
        return json({"error": "Authentication required"}, status=401)
    if not isinstance(request.json, dict):
        return json({"error": "JSON object required"}, status=400)

    try:
        payload = ProfileUpdateRequest.model_validate(request.json)
    except ValidationError as exc:
        return json(
            {"error": "Invalid profile data", "details": exc.errors(include_context=False)},
            status=400,
        )
    update_data = payload.model_dump(exclude_unset=True, mode="json")
    if not update_data:
        return json({"error": "No profile fields supplied"}, status=400)
    if update_data.get("username") is None and "username" in update_data:
        return json({"error": "username cannot be empty"}, status=400)
    if update_data.get("display_name") is None and "display_name" in update_data:
        return json({"error": "display_name cannot be empty"}, status=400)

    async with request.app.ctx.db() as session:
        user = await session.get(User, user_id)
        if not user:
            return json({"error": "Profile not found"}, status=404)

        username = update_data.get("username")
        if username is not None:
            duplicate = await session.scalar(
                select(User.id).where(
                    func.lower(User.username) == username.casefold(),
                    User.id != user.id,
                )
            )
            if duplicate:
                return json({"error": "Username already in use"}, status=409)

        for field, value in update_data.items():
            setattr(user, field, value)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return json({"error": "Username already in use"}, status=409)
        await session.refresh(user)
        response = await _build_profile_response(session, user, user.id)

    return json(response)


@profiles_api_bp.get("/<identifier:str>")
async def get_public_profile(request: Request, identifier: str):
    """Return a profile by username, user UUID, or member UUID."""
    async with request.app.ctx.db() as session:
        user = await _resolve_profile_user(session, identifier.strip())
        if not user:
            return json({"error": "Profile not found"}, status=404)
        response = await _build_profile_response(
            session,
            user,
            _authenticated_user_id(request),
        )
    return json(response)
