"""Seed ecosystem-level and domain-level courses & quizzes into the database.

Usage:
    python -m agent.scripts.seed_quizzes            # seed (idempotent)
    python -m agent.scripts.seed_quizzes --purge     # drop quiz data then reseed

Creates:
  8 courses (2 per ecosystem: 1 ecosystem-wide, 1 domain-scoped)
  16 quizzes (2 per course: mix of standard, assessment, and onboarding)
    - All quizzes have ecosystem_id set for ecosystem-level filtering
    - Domain-level quizzes also have domain_id set
    - One entry quiz per ecosystem (Onboarding Readiness, is_entry_quiz=True)
  33 quiz results (16 existing + 8 collab + 4 onboarding + 4 failed + 1 retake)
  4 quiz progress records (leads in-progress on onboarding readiness)
  8 user tags (2 per ecosystem lead)
  4 user badges (1 per ecosystem lead)
  4 profile tiles (1 per ecosystem lead)
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.course_models import (
    Course,
    Quiz,
    QuizResult,
    QuizProgress,
    UserTag,
    UserBadge,
    ProfileTile,
)


# ---------------------------------------------------------------------------
# Deterministic UUID helper — must match seed_omnione
# ---------------------------------------------------------------------------
def _uid(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"neos.seed.{name}")


# ---------------------------------------------------------------------------
# Ecosystem / Domain / Member IDs (must match seed_omnione)
# ---------------------------------------------------------------------------
eco_omni_id = _uid("eco.omnione")
eco_eb_id = _uid("eco.escherbridge")
eco_ps_id = _uid("eco.plansystems")
eco_oa_id = _uid("eco.oasis")

dom_omni_gov_id = _uid("dom.omni.gov")
dom_eb_art_id = _uid("dom.eb.art")
dom_ps_design_id = _uid("dom.ps.design")
dom_oa_protocol_id = _uid("dom.oa.protocol")

m_josh_id = _uid("mbr.omni.josh")
m_ahmed_eb_id = _uid("mbr.eb.ahmed")
m_rachel_id = _uid("mbr.ps.rachel")
m_max_id = _uid("mbr.oa.max")

m_nathan_id = _uid("mbr.omni.nathan")
m_kenny_id = _uid("mbr.eb.kenny")
m_brandon_id = _uid("mbr.ps.brandon")
m_david_id = _uid("mbr.oa.david")


# ---------------------------------------------------------------------------
# Purge quiz-related tables
# ---------------------------------------------------------------------------
PURGE_ORDER = [
    "profile_tiles",
    "user_badges",
    "user_tags",
    "quiz_progress",
    "quiz_results",
    "quizzes",
    "courses",
]


async def purge(database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        for table in PURGE_ORDER:
            try:
                await conn.execute(text(f'DELETE FROM "{table}"'))
            except Exception:
                pass
    print(f"Purged quiz data from {len(PURGE_ORDER)} tables.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# Survey definitions
# ---------------------------------------------------------------------------

def _governance_knowledge_survey() -> dict:
    return {
        "pages": [{
            "name": "page1",
            "elements": [
                {
                    "type": "radiogroup",
                    "name": "q1",
                    "title": "What is consent-based decision making?",
                    "choices": [
                        "Everyone must agree enthusiastically",
                        "No one has a principled objection",
                        "Majority vote wins",
                        "The leader decides",
                    ],
                    "correctAnswer": "No one has a principled objection",
                },
                {
                    "type": "radiogroup",
                    "name": "q2",
                    "title": "What is the role of a domain steward?",
                    "choices": [
                        "To make all decisions unilaterally",
                        "To facilitate governance within their domain",
                        "To enforce rules strictly",
                        "To report to management",
                    ],
                    "correctAnswer": "To facilitate governance within their domain",
                },
                {
                    "type": "radiogroup",
                    "name": "q3",
                    "title": "Which phase of the ACT process comes first?",
                    "choices": ["Consent", "Test", "Advice", "Ratification"],
                    "correctAnswer": "Advice",
                },
                {
                    "type": "radiogroup",
                    "name": "q4",
                    "title": "What triggers an emergency circuit breaker?",
                    "choices": [
                        "A member complaint",
                        "Existential risk to the ecosystem",
                        "Budget overrun",
                        "Low attendance at meetings",
                    ],
                    "correctAnswer": "Existential risk to the ecosystem",
                },
                {
                    "type": "radiogroup",
                    "name": "q5",
                    "title": "What is the purpose of a cooling-off period in onboarding?",
                    "choices": [
                        "To delay membership",
                        "To allow reflection before full commitment",
                        "To test technical skills",
                        "To reduce workload",
                    ],
                    "correctAnswer": "To allow reflection before full commitment",
                },
            ],
        }],
    }


def _collaboration_style_survey() -> dict:
    return {
        "pages": [{
            "name": "page1",
            "elements": [
                {
                    "type": "rating",
                    "name": "collab_listening",
                    "title": "I prefer to listen and gather all perspectives before sharing my own view.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
                {
                    "type": "rating",
                    "name": "collab_action",
                    "title": "I tend to move quickly from discussion to action.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
                {
                    "type": "rating",
                    "name": "collab_harmony",
                    "title": "Maintaining group harmony is more important than being right.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
                {
                    "type": "rating",
                    "name": "collab_structure",
                    "title": "I work best with clear roles and documented processes.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
                {
                    "type": "rating",
                    "name": "collab_innovation",
                    "title": "I enjoy experimenting with new approaches even when the current way works fine.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
                {
                    "type": "rating",
                    "name": "collab_empathy",
                    "title": "I naturally consider how decisions affect others emotionally.",
                    "rateMin": 1, "rateMax": 5,
                    "minRateDescription": "Strongly Disagree",
                    "maxRateDescription": "Strongly Agree",
                },
            ],
        }],
    }


def _onboarding_readiness_survey() -> dict:
    return {
        "pages": [{
            "name": "page1",
            "elements": [
                {
                    "type": "boolean",
                    "name": "read_agreements",
                    "title": "I have read and understand the ecosystem agreements.",
                },
                {
                    "type": "boolean",
                    "name": "understand_consent",
                    "title": "I understand how consent-based decision making works.",
                },
                {
                    "type": "boolean",
                    "name": "know_steward",
                    "title": "I know who my domain steward is.",
                },
                {
                    "type": "comment",
                    "name": "expectations",
                    "title": "What are your expectations for participating in this ecosystem?",
                },
                {
                    "type": "radiogroup",
                    "name": "commitment",
                    "title": "How much time can you commit weekly to governance activities?",
                    "choices": ["1-2 hours", "3-5 hours", "5-10 hours", "10+ hours"],
                },
            ],
        }],
    }


def _domain_knowledge_survey(domain_name: str, questions: list[dict]) -> dict:
    return {
        "pages": [{
            "name": "page1",
            "elements": questions,
        }],
    }


# ---------------------------------------------------------------------------
# Per-ecosystem domain quiz questions
# ---------------------------------------------------------------------------

DOMAIN_QUESTIONS = {
    "omni_gov": [
        {
            "type": "radiogroup",
            "name": "q1",
            "title": "What governance model does OmniOne use for decision-making?",
            "choices": ["Majority vote", "ACT (Advice-Consent-Test)", "Executive authority", "Random selection"],
            "correctAnswer": "ACT (Advice-Consent-Test)",
        },
        {
            "type": "radiogroup",
            "name": "q2",
            "title": "How many levels does the GAIA conflict escalation model have?",
            "choices": ["3", "4", "6", "10"],
            "correctAnswer": "6",
        },
        {
            "type": "radiogroup",
            "name": "q3",
            "title": "What is the governance structure based on in OmniOne?",
            "choices": ["Hierarchy", "S3-structured domains", "Flat consensus", "Elected representatives"],
            "correctAnswer": "S3-structured domains",
        },
    ],
    "eb_art": [
        {
            "type": "radiogroup",
            "name": "q1",
            "title": "How often do domain stewards rotate at Escherbridge?",
            "choices": ["Monthly", "Quarterly", "Annually", "Never"],
            "correctAnswer": "Quarterly",
        },
        {
            "type": "radiogroup",
            "name": "q2",
            "title": "What is Escherbridge's emphasis in resource allocation?",
            "choices": ["Profit maximization", "Transparent resource allocation", "Cost cutting", "External funding only"],
            "correctAnswer": "Transparent resource allocation",
        },
        {
            "type": "radiogroup",
            "name": "q3",
            "title": "What licensing model does Escherbridge use for creative works?",
            "choices": ["All rights reserved", "Open creative commons", "Proprietary", "No license"],
            "correctAnswer": "Open creative commons",
        },
    ],
    "ps_design": [
        {
            "type": "radiogroup",
            "name": "q1",
            "title": "What planning framework does Plan Systems blend with NEOS ACT?",
            "choices": ["Agile/Scrum", "Systems thinking", "Waterfall", "PRINCE2"],
            "correctAnswer": "Systems thinking",
        },
        {
            "type": "radiogroup",
            "name": "q2",
            "title": "Who holds review authority on Plan Systems strategic planning?",
            "choices": ["All members equally", "Advisory council", "Executive director", "External board"],
            "correctAnswer": "Advisory council",
        },
        {
            "type": "radiogroup",
            "name": "q3",
            "title": "What is the PLAN-Unity SDK primarily used for?",
            "choices": ["Financial accounting", "Spatial collaboration", "Email marketing", "HR management"],
            "correctAnswer": "Spatial collaboration",
        },
    ],
    "oa_protocol": [
        {
            "type": "radiogroup",
            "name": "q1",
            "title": "What decision-making adaptation does Oasis use?",
            "choices": ["Synchronous voting only", "Asynchronous ACT process", "Executive decisions", "AI-driven decisions"],
            "correctAnswer": "Asynchronous ACT process",
        },
        {
            "type": "radiogroup",
            "name": "q2",
            "title": "What is Oasis's core infrastructure focus?",
            "choices": ["Social media", "Cross-chain interoperability", "Cloud hosting", "Content delivery"],
            "correctAnswer": "Cross-chain interoperability",
        },
        {
            "type": "radiogroup",
            "name": "q3",
            "title": "What identity model does Oasis use?",
            "choices": ["Username/password", "Holonic identity-first", "OAuth only", "Anonymous"],
            "correctAnswer": "Holonic identity-first",
        },
    ],
}


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

async def seed(database_url: str) -> None:
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        from neos_agent.db.course_models import Course
        Course.metadata.create_all  # ensure tables exist via Base
        from neos_agent.db.models import Base
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Idempotency check
        existing = await session.execute(text("SELECT count(*) FROM courses"))
        if existing.scalar() > 0:
            print("Courses/quizzes already seeded. Skipping. Use --purge to reseed.")
            await engine.dispose()
            return

        # Ecosystem specs: (eco_id, domain_id, member_id, eco_short, domain_short, eco_name, domain_name)
        eco_specs = [
            (eco_omni_id, dom_omni_gov_id, m_josh_id, "omni", "omni_gov",
             "OmniOne", "Governance Circle"),
            (eco_eb_id, dom_eb_art_id, m_ahmed_eb_id, "eb", "eb_art",
             "Escherbridge", "Creative Arts Studio"),
            (eco_ps_id, dom_ps_design_id, m_rachel_id, "ps", "ps_design",
             "Plan Systems", "Systems Design Lab"),
            (eco_oa_id, dom_oa_protocol_id, m_max_id, "oa", "oa_protocol",
             "Oasis", "Protocol Engineering"),
        ]

        course_count = 0
        quiz_count = 0

        for (eco_id, domain_id, member_id, eco_short, domain_short,
             eco_name, domain_name) in eco_specs:

            # --- Ecosystem-level course ---
            eco_course_id = _uid(f"course.eco.{eco_short}")
            session.add(Course(
                id=eco_course_id,
                ecosystem_id=eco_id,
                domain_id=None,
                title=f"{eco_name} — Governance Fundamentals",
                description=f"Core governance concepts and onboarding knowledge for {eco_name} members.",
                created_by=member_id,
                sort_order=1,
            ))
            course_count += 1

            # Quiz 1: Governance knowledge (ecosystem-level)
            session.add(Quiz(
                id=_uid(f"quiz.eco.{eco_short}.gov"),
                course_id=eco_course_id,
                ecosystem_id=eco_id,
                title=f"{eco_name} Governance Knowledge Check",
                description=f"Test your understanding of governance principles within {eco_name}.",
                mode="standard",
                survey_json=_governance_knowledge_survey(),
                passing_score=60,
                is_published=True,
                created_by=member_id,
                visibility="public",
            ))
            quiz_count += 1

            # Quiz 2: Onboarding readiness (ecosystem-level, entry quiz)
            session.add(Quiz(
                id=_uid(f"quiz.eco.{eco_short}.onboard"),
                course_id=eco_course_id,
                ecosystem_id=eco_id,
                title=f"{eco_name} Onboarding Readiness",
                description=f"Self-check before completing your {eco_name} onboarding ceremony.",
                mode="standard",
                survey_json=_onboarding_readiness_survey(),
                is_published=True,
                created_by=member_id,
                visibility="public",
                allow_retakes=False,
                is_entry_quiz=True,
            ))
            quiz_count += 1

            # --- Domain-level course ---
            dom_course_id = _uid(f"course.dom.{domain_short}")
            session.add(Course(
                id=dom_course_id,
                ecosystem_id=eco_id,
                domain_id=domain_id,
                title=f"{eco_name} — {domain_name} Orientation",
                description=f"Domain-specific learning for the {domain_name} domain within {eco_name}.",
                created_by=member_id,
                sort_order=2,
            ))
            course_count += 1

            # Quiz 3: Domain knowledge (domain-level)
            session.add(Quiz(
                id=_uid(f"quiz.dom.{domain_short}.know"),
                course_id=dom_course_id,
                ecosystem_id=eco_id,
                domain_id=domain_id,
                title=f"{domain_name} Domain Knowledge",
                description=f"Assess your understanding of {domain_name} practices and protocols.",
                mode="standard",
                survey_json=_domain_knowledge_survey(domain_name, DOMAIN_QUESTIONS[domain_short]),
                passing_score=66,
                is_published=True,
                created_by=member_id,
                visibility="public",
            ))
            quiz_count += 1

            # Quiz 4: Collaboration style (domain-level, assessment)
            session.add(Quiz(
                id=_uid(f"quiz.dom.{domain_short}.collab"),
                course_id=dom_course_id,
                ecosystem_id=eco_id,
                domain_id=domain_id,
                title=f"{domain_name} Collaboration Style",
                description=f"Discover your collaboration style within {domain_name}. No right or wrong answers.",
                mode="assessment",
                survey_json=_collaboration_style_survey(),
                is_published=True,
                created_by=member_id,
                visibility="public",
                allow_retakes=True,
            ))
            quiz_count += 1

        # Flush so quiz IDs are available for FK references
        await session.flush()

        # ---------------------------------------------------------------
        # Quiz Results (33 total)
        # ---------------------------------------------------------------
        result_count = 0

        # (eco_short, domain_short, lead_id, lead_short, second_id, second_short)
        result_specs = [
            ("omni", "omni_gov", m_josh_id, "josh", m_nathan_id, "nathan"),
            ("eb", "eb_art", m_ahmed_eb_id, "ahmed", m_kenny_id, "kenny"),
            ("ps", "ps_design", m_rachel_id, "rachel", m_brandon_id, "brandon"),
            ("oa", "oa_protocol", m_max_id, "max", m_david_id, "david"),
        ]

        collab_answers_lead = {
            "collab_listening": 4,
            "collab_action": 3,
            "collab_harmony": 5,
            "collab_structure": 4,
            "collab_innovation": 3,
            "collab_empathy": 5,
        }
        collab_answers_second = {
            "collab_listening": 3,
            "collab_action": 5,
            "collab_harmony": 2,
            "collab_structure": 5,
            "collab_innovation": 4,
            "collab_empathy": 3,
        }
        onboarding_answers_complete = {
            "read_agreements": True,
            "understand_consent": True,
            "know_steward": True,
            "expectations": "I want to contribute to collective governance and bring my skills to the community.",
            "commitment": "3-5 hours",
        }
        gov_answers_failed = {
            "q1": "Everyone must agree enthusiastically",  # wrong
            "q2": "To make all decisions unilaterally",    # wrong
            "q3": "Consent",                               # wrong
            "q4": "Existential risk to the ecosystem",
            "q5": "To delay membership",                   # wrong
        }

        gov_answers_perfect = {
            "q1": "No one has a principled objection",
            "q2": "To facilitate governance within their domain",
            "q3": "Advice",
            "q4": "Existential risk to the ecosystem",
            "q5": "To allow reflection before full commitment",
        }
        gov_answers_good = {
            "q1": "No one has a principled objection",
            "q2": "To facilitate governance within their domain",
            "q3": "Advice",
            "q4": "Existential risk to the ecosystem",
            "q5": "To delay membership",  # wrong
        }
        domain_answers_perfect = {
            "q1": "correct",
            "q2": "correct",
            "q3": "correct",
        }
        domain_answers_partial = {
            "q1": "correct",
            "q2": "correct",
            "q3": "wrong",  # 2/3 = 66%
        }

        for eco_short, domain_short, lead_id, lead_short, second_id, second_short in result_specs:
            eco_gov_quiz_id = _uid(f"quiz.eco.{eco_short}.gov")
            domain_know_quiz_id = _uid(f"quiz.dom.{domain_short}.know")

            # Lead — eco governance (100%, passed)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{lead_short}.gov"),
                quiz_id=eco_gov_quiz_id,
                member_id=lead_id,
                survey_results=gov_answers_perfect,
                score=100.0,
                is_passed=True,
                time_spent=180000,
                completed_at=datetime.utcnow() - timedelta(days=7),
            ))
            result_count += 1

            # Second member — eco governance (80%, passed)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{second_short}.gov"),
                quiz_id=eco_gov_quiz_id,
                member_id=second_id,
                survey_results=gov_answers_good,
                score=80.0,
                is_passed=True,
                time_spent=240000,
                completed_at=datetime.utcnow() - timedelta(days=6),
            ))
            result_count += 1

            # Lead — domain knowledge (100%, passed)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{lead_short}.domain"),
                quiz_id=domain_know_quiz_id,
                member_id=lead_id,
                survey_results=domain_answers_perfect,
                score=100.0,
                is_passed=True,
                time_spent=150000,
                completed_at=datetime.utcnow() - timedelta(days=5),
            ))
            result_count += 1

            # Second member — domain knowledge (66%, passed at threshold)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{second_short}.domain"),
                quiz_id=domain_know_quiz_id,
                member_id=second_id,
                survey_results=domain_answers_partial,
                score=66.0,
                is_passed=True,
                time_spent=200000,
                completed_at=datetime.utcnow() - timedelta(days=4),
            ))
            result_count += 1

            # Lead — collaboration style (assessment, no score/pass)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{lead_short}.collab"),
                quiz_id=_uid(f"quiz.dom.{domain_short}.collab"),
                member_id=lead_id,
                survey_results=collab_answers_lead,
                score=None,
                is_passed=None,
                time_spent=120000,
                completed_at=datetime.utcnow() - timedelta(days=5),
            ))
            result_count += 1

            # Second member — collaboration style (assessment, no score/pass)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{second_short}.collab"),
                quiz_id=_uid(f"quiz.dom.{domain_short}.collab"),
                member_id=second_id,
                survey_results=collab_answers_second,
                score=None,
                is_passed=None,
                time_spent=130000,
                completed_at=datetime.utcnow() - timedelta(days=4),
            ))
            result_count += 1

            # Second member — onboarding readiness (completed)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{second_short}.onboard"),
                quiz_id=_uid(f"quiz.eco.{eco_short}.onboard"),
                member_id=second_id,
                survey_results=onboarding_answers_complete,
                score=None,
                is_passed=True,
                time_spent=180000,
                completed_at=datetime.utcnow() - timedelta(days=6),
            ))
            result_count += 1

            # Second member — failed governance attempt (before passing)
            session.add(QuizResult(
                id=_uid(f"qr.{eco_short}.{second_short}.gov.fail1"),
                quiz_id=_uid(f"quiz.eco.{eco_short}.gov"),
                member_id=second_id,
                survey_results=gov_answers_failed,
                score=20.0,
                is_passed=False,
                time_spent=210000,
                completed_at=datetime.utcnow() - timedelta(days=10),
            ))
            result_count += 1

        # Kenny (Escherbridge second) — domain knowledge retake (100%, improved)
        session.add(QuizResult(
            id=_uid("qr.eb.kenny.domain.retake1"),
            quiz_id=_uid("quiz.dom.eb_art.know"),
            member_id=m_kenny_id,
            survey_results=domain_answers_perfect,
            score=100.0,
            is_passed=True,
            time_spent=140000,
            completed_at=datetime.utcnow() - timedelta(days=2),
        ))
        result_count += 1

        # ---------------------------------------------------------------
        # Quiz Progress (4 — leads in-progress on onboarding readiness)
        # ---------------------------------------------------------------
        progress_count = 0

        progress_specs = [
            ("omni", m_josh_id),
            ("eb", m_ahmed_eb_id),
            ("ps", m_rachel_id),
            ("oa", m_max_id),
        ]

        for eco_short, lead_id in progress_specs:
            session.add(QuizProgress(
                id=_uid(f"qp.{eco_short}.onboard"),
                quiz_id=_uid(f"quiz.eco.{eco_short}.onboard"),
                member_id=lead_id,
                current_question_index=2,
                answers={"read_agreements": True, "understand_consent": True},
                started_at=datetime.utcnow() - timedelta(hours=2),
            ))
            progress_count += 1

        # Flush so quiz_result IDs are available for user_tags FK
        await session.flush()

        # ---------------------------------------------------------------
        # User Tags (8 — 2 per ecosystem lead, derived from quiz results)
        # ---------------------------------------------------------------
        tag_count = 0

        tag_specs = [
            ("omni", "josh", m_josh_id),
            ("eb", "ahmed", m_ahmed_eb_id),
            ("ps", "rachel", m_rachel_id),
            ("oa", "max", m_max_id),
        ]

        for eco_short, lead_short, lead_id in tag_specs:
            # Tag from governance quiz — expert
            session.add(UserTag(
                id=_uid(f"tag.{eco_short}.{lead_short}.gov_knowledge"),
                member_id=lead_id,
                quiz_result_id=_uid(f"qr.{eco_short}.{lead_short}.gov"),
                tag_key="governance_knowledge",
                tag_value="expert",
                tag_category="governance",
                data_type="string",
                numeric_value=None,
            ))
            tag_count += 1

            # Tag from domain quiz — collaboration style
            session.add(UserTag(
                id=_uid(f"tag.{eco_short}.{lead_short}.collab_style"),
                member_id=lead_id,
                quiz_result_id=_uid(f"qr.{eco_short}.{lead_short}.domain"),
                tag_key="collaboration_style",
                tag_value="harmonizer",
                tag_category="personality",
                data_type="string",
                numeric_value=None,
            ))
            tag_count += 1

        # ---------------------------------------------------------------
        # User Badges (4 — 1 per ecosystem lead)
        # ---------------------------------------------------------------
        badge_count = 0

        for eco_short, lead_short, lead_id in tag_specs:
            session.add(UserBadge(
                id=_uid(f"badge.{eco_short}.{lead_short}.gov_champion"),
                member_id=lead_id,
                badge_key="governance_champion",
                badge_name="Governance Champion",
                badge_description="Scored 100% on governance fundamentals",
                badge_category="governance",
                badge_icon="\U0001f3c6",
                strength=1.0,
                source_tag_keys=["governance_knowledge"],
                earned_at=datetime.utcnow() - timedelta(days=7),
            ))
            badge_count += 1

        # ---------------------------------------------------------------
        # Profile Tiles (4 — 1 per ecosystem lead)
        # ---------------------------------------------------------------
        tile_count = 0

        for eco_short, lead_short, lead_id in tag_specs:
            session.add(ProfileTile(
                id=_uid(f"tile.{eco_short}.{lead_short}.badge"),
                member_id=lead_id,
                type="badge",
                data={
                    "badge_key": "governance_champion",
                    "badge_name": "Governance Champion",
                    "icon": "\U0001f3c6",
                },
                layout_index=0,
                is_visible=True,
            ))
            tile_count += 1

        await session.commit()

    await engine.dispose()

    print()
    print(f"=== Quiz Seed Data ===")
    print(f"Courses:        {course_count} ({course_count // 2} ecosystem-level, {course_count // 2} domain-level)")
    print(f"Quizzes:        {quiz_count} ({quiz_count // 2} ecosystem-level, {quiz_count // 2} domain-level)")
    print(f"Quiz Results:   {result_count}")
    print(f"Quiz Progress:  {progress_count}")
    print(f"User Tags:      {tag_count}")
    print(f"User Badges:    {badge_count}")
    print(f"Profile Tiles:  {tile_count}")
    print(f"Ecosystems covered: OmniOne, Escherbridge, Plan Systems, Oasis")
    print(f"=== Done ===")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed ecosystem & domain quizzes")
    parser.add_argument("--purge", action="store_true", help="Delete quiz data before seeding")
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging quiz data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
