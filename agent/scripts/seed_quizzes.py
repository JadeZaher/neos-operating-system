"""Seed demo courses and quizzes into the database."""

import asyncio
import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def seed():
    from neos_agent.config import get_settings

    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # Get ecosystem and a member
        eco = await db.execute(text("SELECT id FROM ecosystems LIMIT 1"))
        eco_id = eco.scalar()
        mem = await db.execute(text("SELECT id FROM members WHERE display_name = 'Manu' LIMIT 1"))
        mem_id = mem.scalar()

        if not eco_id or not mem_id:
            print("Missing ecosystem or member")
            return

        # Check if quizzes already exist
        existing = await db.execute(text("SELECT count(*) FROM quizzes"))
        if existing.scalar() > 0:
            print("Quizzes already seeded")
            return

        # --- Course 1: Governance Fundamentals ---
        course_id = uuid.uuid4()
        await db.execute(
            text(
                "INSERT INTO courses (id, ecosystem_id, title, description, created_by, sort_order) "
                "VALUES (:id, :eco, :title, :desc, :by, 1)"
            ),
            {
                "id": str(course_id),
                "eco": str(eco_id),
                "title": "Governance Fundamentals",
                "desc": "Learn the basics of sociocratic governance, consent-based decision making, and ecosystem stewardship.",
                "by": str(mem_id),
            },
        )

        # --- Course 2: Collaboration Styles ---
        course2_id = uuid.uuid4()
        await db.execute(
            text(
                "INSERT INTO courses (id, ecosystem_id, title, description, created_by, sort_order) "
                "VALUES (:id, :eco, :title, :desc, :by, 2)"
            ),
            {
                "id": str(course2_id),
                "eco": str(eco_id),
                "title": "Collaboration Styles",
                "desc": "Discover your collaboration style and how you work best with others in a governance ecosystem.",
                "by": str(mem_id),
            },
        )

        # --- Quiz 1: Governance Knowledge Check ---
        q1_id = uuid.uuid4()
        survey1 = {
            "pages": [
                {
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
                            "title": "Which layer of NEOS covers conflict resolution?",
                            "choices": ["Layer I", "Layer IV", "Layer VI", "Layer VIII"],
                            "correctAnswer": "Layer VI",
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
                }
            ]
        }
        await db.execute(
            text(
                "INSERT INTO quizzes (id, course_id, title, description, mode, survey_json, passing_score, is_published, created_by, visibility) "
                "VALUES (:id, :cid, :title, :desc, 'standard', :sj, 60, true, :by, 'public')"
            ),
            {
                "id": str(q1_id),
                "cid": str(course_id),
                "title": "Governance Knowledge Check",
                "desc": "Test your understanding of NEOS governance principles.",
                "sj": json.dumps(survey1),
                "by": str(mem_id),
            },
        )

        # --- Quiz 2: Collaboration Style Assessment ---
        q2_id = uuid.uuid4()
        survey2 = {
            "pages": [
                {
                    "name": "page1",
                    "elements": [
                        {
                            "type": "rating",
                            "name": "collab_listening",
                            "title": "I prefer to listen and gather all perspectives before sharing my own view.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                        {
                            "type": "rating",
                            "name": "collab_action",
                            "title": "I tend to move quickly from discussion to action.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                        {
                            "type": "rating",
                            "name": "collab_harmony",
                            "title": "Maintaining group harmony is more important than being right.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                        {
                            "type": "rating",
                            "name": "collab_structure",
                            "title": "I work best with clear roles and documented processes.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                        {
                            "type": "rating",
                            "name": "collab_innovation",
                            "title": "I enjoy experimenting with new approaches even when the current way works fine.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                        {
                            "type": "rating",
                            "name": "collab_empathy",
                            "title": "I naturally consider how decisions affect others emotionally.",
                            "rateMin": 1,
                            "rateMax": 5,
                            "minRateDescription": "Strongly Disagree",
                            "maxRateDescription": "Strongly Agree",
                        },
                    ],
                }
            ]
        }
        await db.execute(
            text(
                "INSERT INTO quizzes (id, course_id, title, description, mode, survey_json, is_published, created_by, visibility, allow_retakes) "
                "VALUES (:id, :cid, :title, :desc, 'assessment', :sj, true, :by, 'public', true)"
            ),
            {
                "id": str(q2_id),
                "cid": str(course2_id),
                "title": "Collaboration Style Assessment",
                "desc": "Discover your natural collaboration style. No right or wrong answers.",
                "sj": json.dumps(survey2),
                "by": str(mem_id),
            },
        )

        # --- Quiz 3: Onboarding Readiness Check (standalone, no course) ---
        q3_id = uuid.uuid4()
        survey3 = {
            "pages": [
                {
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
                }
            ]
        }
        await db.execute(
            text(
                "INSERT INTO quizzes (id, title, description, mode, survey_json, is_published, created_by, visibility, allow_retakes) "
                "VALUES (:id, :title, :desc, 'standard', :sj, true, :by, 'public', false)"
            ),
            {
                "id": str(q3_id),
                "title": "Onboarding Readiness Check",
                "desc": "Quick self-check before completing your onboarding ceremony.",
                "sj": json.dumps(survey3),
                "by": str(mem_id),
            },
        )

        await db.commit()
        print(f"Seeded 2 courses, 3 quizzes")
        print(f"  Course 1: {course_id} - Governance Fundamentals")
        print(f"  Course 2: {course2_id} - Collaboration Styles")
        print(f"  Quiz 1: {q1_id} - Governance Knowledge Check")
        print(f"  Quiz 2: {q2_id} - Collaboration Style Assessment")
        print(f"  Quiz 3: {q3_id} - Onboarding Readiness Check")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
