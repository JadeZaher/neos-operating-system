"""
Exit records (Layer X — Exit & Portability).

Two exit scenarios:
  1. EX-002: In progress — Rani Maheswari (cooling-off exit).
     Data export requested but not yet completed.
     Commitments being unwound.
  2. EX-001: Completed — [Former member, identity anonymized per portable record].
     Full exit completed with data export delivered.
     Re-entry flagged as eligible.
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# ── Exit Record IDs ────────────────────────────────────────────────

EXIT_COMPLETED   = uuid.UUID("dba7b810-9dad-11d1-80b4-00c04fd430a1")
EXIT_IN_PROGRESS = uuid.UUID("dba7b810-9dad-11d1-80b4-00c04fd430a2")


EXIT_RECORDS: list[dict] = [
    # 1. Completed exit — [Former member]
    {
        "id": EXIT_COMPLETED,
        "ecosystem_id": ECOSYSTEM_ID,
        "member_id": None,  # set in run.py — former member UUID
        "exit_type": "standard",
        "status": "completed",
        "declared_date": date(2024, 12, 1),
        "target_completion_date": date(2025, 1, 1),
        "coordinator_id": None,  # set in run.py — Ketut Arsana
        "commitment_inventory": {
            "roles": [
                "TH assembly participant",
            ],
            "agreements_consented": [
                "UAF v1.0",
                "TH Culture Code v1.0",
            ],
            "economic_commitments": [],  # No resource pool commitments
            "pending_proposals": [],
            "conflict_involvement": [
                "CC-003 (Seed library breach) — witnessed, not party",
            ],
        },
        "unwinding_status": {
            "roles_resolved": True,
            "agreements_sunset": True,
            "economic_settled": True,
            "proposals_withdrawn_or_transferred": True,
            "conflicts_resolved": True,
            "notes": "All commitments unwound within 30-day handoff.  No blockers.",
        },
        "data_export_requested": True,
        "data_export_completed": date(2024, 12, 28),
        "departure_notice": (
            "[Member] is departing OmniOne to pursue a graduate degree in "
            "ecological design at Wageningen University.  They expressed "
            "gratitude for the community and indicated potential re-entry "
            "after completing their studies in 2027."
        ),
        "re_entry_eligible": True,
        "completed_date": date(2025, 1, 1),
        "notes": (
            "Exit was smooth and positive.  No conflict.  Portable record "
            "exported in NEOS Portable Record Format v1.0.  [Member] requested "
            "full governance participation history for academic use.  Ketut "
            "noted that this was the first test of the portable record format "
            "and it performed well — export took under 10 minutes."
        ),
    },

    # 2. Exit in progress — Rani Maheswari (cooling-off period)
    {
        "id": EXIT_IN_PROGRESS,
        "ecosystem_id": ECOSYSTEM_ID,
        "member_id": None,  # set in run.py — Rani's Member ID
        "exit_type": "standard",
        "status": "cooling_off",
        "declared_date": date(2025, 6, 5),
        "target_completion_date": date(2025, 7, 5),
        "coordinator_id": None,  # set in run.py — Ketut Arsana
        "commitment_inventory": {
            "roles": [],
            "agreements_consented": [
                "UAF v1.0 (section consent only — cooling off period)",
            ],
            "economic_commitments": [],
            "pending_proposals": [],
            "conflict_involvement": [],
        },
        "unwinding_status": {
            "roles_resolved": True,  # No roles to unwind
            "agreements_sunset": False,  # UAF section consent still active
            "economic_settled": True,  # No economic commitments
            "proposals_withdrawn_or_transferred": True,
            "conflicts_resolved": True,
            "notes": (
                "Rani is still within her cooling-off period (started 2025-05-15, "
                "ends 2025-06-15).  She has decided to exit rather than continue "
                "onboarding.  Since she never consented to the full UAF, the "
                "commitment unwinding is minimal."
            ),
        },
        "data_export_requested": True,
        "data_export_completed": None,  # Not yet completed
        "departure_notice": (
            "Rani has decided that OmniOne's governance depth exceeds what she "
            "needs at this stage of her life.  She expressed appreciation for "
            "the onboarding process and said she may return when she has more "
            "time to engage.  No negative experience.  'It is not the right "
            "ecosystem for me right now, but I am glad it exists.'"
        ),
        "re_entry_eligible": True,
        "completed_date": None,
        "notes": (
            "This is a cooling-off exit — Rani never left the onboarding "
            "process.  Ketut notes that this is a healthy exit: the onboarding "
            "system gave Rani enough information to decide OmniOne is not her "
            "fit, and the cooling-off period empowered her to leave cleanly.  "
            "Data export is pending — Rani requested her limited participation "
            "record for her own records.  Expected completion: 2025-06-20."
        ),
    },
]
