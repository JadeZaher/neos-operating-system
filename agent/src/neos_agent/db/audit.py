"""Print a read-only aggregate database audit as JSON."""

from __future__ import annotations

import asyncio
import json
import os

from sqlalchemy import func, select, text

from neos_agent.db.models import (
    Agreement,
    DecisionRecord,
    Domain,
    Ecosystem,
    Member,
    Proposal,
    User,
)
from neos_agent.db.session import create_db_engine


COUNT_MODELS = {
    "ecosystems": Ecosystem,
    "users": User,
    "members": Member,
    "domains": Domain,
    "agreements": Agreement,
    "proposals": Proposal,
    "decisions": DecisionRecord,
}

ECOSYSTEM_MODELS = {
    "members": Member,
    "domains": Domain,
    "agreements": Agreement,
    "proposals": Proposal,
    "decisions": DecisionRecord,
}


async def collect_audit() -> dict:
    engine = await create_db_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as connection:
            version_rows = await connection.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num")
            )
            versions = [row.version_num for row in version_rows]

            totals = {}
            for name, model in COUNT_MODELS.items():
                totals[name] = await connection.scalar(
                    select(func.count()).select_from(model)
                )

            ecosystem_ids = (
                await connection.execute(select(Ecosystem.id).order_by(Ecosystem.id))
            ).scalars()
            per_ecosystem = {
                str(ecosystem_id): {
                    "ecosystems": 1,
                    "users": 0,
                    "members": 0,
                    "domains": 0,
                    "agreements": 0,
                    "proposals": 0,
                    "decisions": 0,
                }
                for ecosystem_id in ecosystem_ids
            }

            user_rows = await connection.execute(
                select(
                    Member.ecosystem_id,
                    func.count(func.distinct(Member.user_id)),
                ).group_by(Member.ecosystem_id)
            )
            for ecosystem_id, count in user_rows:
                per_ecosystem[str(ecosystem_id)]["users"] = count

            for name, model in ECOSYSTEM_MODELS.items():
                count_rows = await connection.execute(
                    select(model.ecosystem_id, func.count()).group_by(
                        model.ecosystem_id
                    )
                )
                for ecosystem_id, count in count_rows:
                    per_ecosystem[str(ecosystem_id)][name] = count

            return {
                "alembic_versions": versions,
                "totals": totals,
                "per_ecosystem": per_ecosystem,
            }
    finally:
        await engine.dispose()


def main() -> None:
    payload = json.dumps(asyncio.run(collect_audit()), sort_keys=True)
    print(f"DATABASE_AUDIT {payload}")


if __name__ == "__main__":
    main()
