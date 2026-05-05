"""Run all seed scripts in the correct order for a fully immersive QA environment.

Usage:
    python -m agent.scripts.seed_all              # seed all (idempotent)
    python -m agent.scripts.seed_all --purge       # purge everything then reseed

Execution order:
  1. seed_omnione   — ecosystems, members, domains, agreements, proposals (advice),
                      conflicts, decisions, emergency, exit, audits, collaborations
  2. seed_act_lifecycle — proposals in consent, test, ratified, withdrawn stages
  3. seed_quizzes   — courses, quizzes, results, progress, tags, badges, tiles
  4. seed_orientation — journey maps, ethos user access records
  5. seed_messaging — conversations, messages, links, push subscriptions
  6. seed_conflicts_emergency — additional conflicts, emergencies, exit records

Total seed data:
  4 ecosystems | 12 domains | 11+ members
  20+ agreements | 20 proposals (all ACT stages) | 12+ conflicts
  8 courses | 16 quizzes | 16 quiz results
  8 journey maps | 11 ethos access records
  8 conversations | 56+ messages | 8 push subscriptions
  4+ emergency states | 4+ exit records | 4 compliance summaries
"""

from __future__ import annotations

import asyncio
import sys


async def run_all(purge: bool = False) -> None:
    from neos_agent.config import get_settings

    database_url = get_settings().DATABASE_URL

    # --- 1. Core data (ecosystems, members, domains, agreements, etc.) ---
    from scripts.seed_omnione import purge as purge_omnione, seed as seed_omnione

    if purge:
        print("\n" + "=" * 60)
        print("PURGING ALL DATA")
        print("=" * 60)
        # Purge in reverse order: supplemental scripts first, then core
        from scripts.seed_conflicts_emergency import purge as purge_ce
        from scripts.seed_messaging import purge as purge_msg
        from scripts.seed_orientation import purge as purge_orientation
        from scripts.seed_quizzes import purge as purge_quiz
        from scripts.seed_act_lifecycle import purge as purge_act

        await purge_ce(database_url)
        await purge_msg(database_url)
        await purge_orientation(database_url)
        await purge_quiz(database_url)
        await purge_act(database_url)
        await purge_omnione(database_url)

    print("\n" + "=" * 60)
    print("STEP 1/6: Core data (ecosystems, members, domains, agreements)")
    print("=" * 60)
    await seed_omnione(database_url)

    # --- 2. Full ACT lifecycle proposals ---
    from scripts.seed_act_lifecycle import seed as seed_act

    print("\n" + "=" * 60)
    print("STEP 2/6: ACT lifecycle proposals (consent, test, ratified, withdrawn)")
    print("=" * 60)
    await seed_act(database_url)

    # --- 3. Courses, quizzes, results ---
    from scripts.seed_quizzes import seed as seed_quizzes

    print("\n" + "=" * 60)
    print("STEP 3/6: Courses, quizzes, results, badges, tiles")
    print("=" * 60)
    await seed_quizzes(database_url)

    # --- 4. Orientation (journey maps, ethos access) ---
    from scripts.seed_orientation import seed as seed_orientation

    print("\n" + "=" * 60)
    print("STEP 4/6: Orientation (journey maps, ethos user access)")
    print("=" * 60)
    await seed_orientation(database_url)

    # --- 5. Messaging ---
    from scripts.seed_messaging import seed as seed_messaging

    print("\n" + "=" * 60)
    print("STEP 5/6: Messaging (conversations, messages, push subscriptions)")
    print("=" * 60)
    await seed_messaging(database_url)

    # --- 6. Additional conflicts, emergencies, exits ---
    from scripts.seed_conflicts_emergency import seed as seed_ce

    print("\n" + "=" * 60)
    print("STEP 6/6: Additional conflicts, emergencies, exit records")
    print("=" * 60)
    await seed_ce(database_url)

    print("\n" + "=" * 60)
    print("ALL SEED DATA COMPLETE")
    print("=" * 60)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed the full NEOS QA environment (all scripts)"
    )
    parser.add_argument(
        "--purge", action="store_true",
        help="Delete all data before seeding"
    )
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        get_settings()
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    asyncio.run(run_all(purge=args.purge))


if __name__ == "__main__":
    main()
