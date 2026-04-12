"""Seed course and quiz data for the OmniOne ecosystem.

Usage: python scripts/seed_courses.py
Requires: DATABASE_URL env var or agent/.env file
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add agent/src to path so we can import models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent" / "src"))


async def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / "agent" / ".env")

    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from neos_agent.db.models import Ecosystem, Domain
    from neos_agent.db.course_models import Course, Quiz

    db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///neos.db")
    engine = create_async_engine(db_url)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # Find OmniOne ecosystem
        result = await session.execute(select(Ecosystem).limit(1))
        ecosystem = result.scalar_one_or_none()
        if not ecosystem:
            print("No ecosystem found. Run the app first to create the default ecosystem.")
            return

        eco_id = ecosystem.id
        print(f"Seeding courses for ecosystem: {ecosystem.name} ({eco_id})")

        # Check if courses already exist
        existing = await session.scalar(select(Course).where(Course.ecosystem_id == eco_id).limit(1))
        if existing:
            print("Courses already exist. Skipping seed.")
            return

        # Create onboarding course
        onboarding_course = Course(
            id=uuid.uuid4(), ecosystem_id=eco_id,
            title="NEOS Governance Onboarding",
            description="Learn the fundamentals of NEOS governance: agreements, decisions, domains, and the ACT process.",
            is_onboarding_required=True, sort_order=1,
        )
        session.add(onboarding_course)
        await session.flush()

        # Create quizzes for onboarding
        quizzes = [
            Quiz(id=uuid.uuid4(), course_id=onboarding_course.id, title="Governance Basics",
                 description="Test your understanding of NEOS governance principles.",
                 mode="standard", passing_score=70, is_published=True,
                 survey_json={"pages": [{"elements": [
                     {"type": "radiogroup", "name": "q1", "title": "What does ACT stand for?",
                      "choices": ["Action-Consent-Test", "Advice-Consent-Test", "Agreement-Consent-Transfer"],
                      "correctAnswer": "Advice-Consent-Test"},
                     {"type": "radiogroup", "name": "q2", "title": "Can economic contribution buy governance authority in NEOS?",
                      "choices": ["Yes", "No", "Only for stewards"],
                      "correctAnswer": "No"},
                 ]}]}),
            Quiz(id=uuid.uuid4(), course_id=onboarding_course.id, title="Agreement Types",
                 description="Learn about the different types of agreements in NEOS.",
                 mode="standard", passing_score=70, is_published=True,
                 survey_json={"pages": [{"elements": [
                     {"type": "radiogroup", "name": "q1", "title": "What is the highest level agreement?",
                      "choices": ["Culture Code", "UAF", "Ecosystem Agreement"],
                      "correctAnswer": "UAF"},
                 ]}]}),
            Quiz(id=uuid.uuid4(), course_id=onboarding_course.id, title="Conflict Resolution",
                 description="Understand the NEOS approach to conflict and repair.",
                 mode="standard", passing_score=70, is_published=True,
                 survey_json={"pages": [{"elements": [
                     {"type": "radiogroup", "name": "q1", "title": "What is the primary goal of conflict resolution in NEOS?",
                      "choices": ["Punishment", "Repair", "Exclusion"],
                      "correctAnswer": "Repair"},
                 ]}]}),
        ]
        for q in quizzes:
            session.add(q)

        # Create advanced course
        advanced_course = Course(
            id=uuid.uuid4(), ecosystem_id=eco_id,
            title="Advanced Governance Skills",
            description="Deep dive into capture resistance, emergency protocols, and cross-unit coordination.",
            is_onboarding_required=False, sort_order=2,
        )
        session.add(advanced_course)

        await session.commit()
        print(f"Created {2} courses and {len(quizzes)} quizzes.")


if __name__ == "__main__":
    asyncio.run(main())
