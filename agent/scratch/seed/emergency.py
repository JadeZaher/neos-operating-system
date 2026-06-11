"""
Two emergency states (Layer VIII — Circuit Breaker):

  1. EM-002: Open — Severe drought affecting East SHUR water supply.
     Active Crisis state with auto-revert timer in the future.
     Pre-authorized roles activated.
  2. EM-001: Closed — Mount Agung volcanic alert (2025).
     Historically resolved emergency with full Recovery → Closed cycle.
     Post-review completed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

NOW = datetime.now(timezone.utc)

# ── Emergency State IDs ────────────────────────────────────────────

EM_AGUNG    = uuid.UUID("bba7b810-9dad-11d1-80b4-00c04fd430a1")
EM_DROUGHT  = uuid.UUID("bba7b810-9dad-11d1-80b4-00c04fd430a2")


EMERGENCY_STATES: list[dict] = [
    # 1. Historical — Mount Agung volcanic alert (fully resolved)
    {
        "id": EM_AGUNG,
        "ecosystem_id": ECOSYSTEM_ID,
        "state": "closed",
        "declared_at": datetime(2025, 3, 8, 14, 0, 0, tzinfo=timezone.utc),
        "declared_by": "Dewa Putra",
        "criteria_met": {
            "criterion_id": "EC-003",
            "criterion_name": "Volcanic Activity within 50km of SHUR Facilities",
            "threshold": "PVMBG alert Level 3 (Siaga/Watch) or higher",
            "actual_condition": (
                "PVMBG raised Mount Agung alert to Level 3 on 2025-03-08.  "
                "East SHUR is 42km from crater — within 50km threshold.  "
                "West SHUR is 78km — outside threshold but evacuation "
                "preparation was extended to all facilities."
            ),
        },
        "auto_revert_at": datetime(2025, 3, 22, 14, 0, 0, tzinfo=timezone.utc),
        "recovery_entered_at": datetime(2025, 3, 20, 9, 0, 0, tzinfo=timezone.utc),
        "closed_at": datetime(2025, 3, 22, 14, 0, 0, tzinfo=timezone.utc),
        "pre_authorized_roles": {
            "emergency_coordinator": {
                "person": "Dewa Putra",
                "scope": "Evacuation logistics and communication only",
                "max_duration_hours": 336,  # 14 days
            },
        },
        "actions_log": {
            "2025-03-08T14:00": "Crisis state declared by Dewa Putra.",
            "2025-03-08T16:00": "OSC consent confirmed (compressed 2-hour timeline).",
            "2025-03-08T18:00": "Evacuation advisory issued.  East SHUR prepared for possible evacuation.",
            "2025-03-09T08:00": "Emergency supplies positioned at East SHUR (water, masks, first aid).",
            "2025-03-12T10:00": "PVMBG reports decreased seismic activity.  Alert remains at Level 3.",
            "2025-03-18T06:00": "PVMBG downgrades alert to Level 2 (Waspada/Caution).",
            "2025-03-20T09:00": "Recovery state entered.  Dewa begins post-emergency documentation.",
            "2025-03-22T14:00": "Auto-revert timer expires.  State closed.  Normal governance resumed.",
        },
        "post_review_status": "completed",
        "notes": (
            "Post-emergency review completed 2025-04-05 by Melati Kusuma.  "
            "Key findings: (a) pre-authorized criteria worked as intended — "
            "Dewa verified facts, did not exercise discretion; (b) compressed "
            "OSC consent timeline was feasible but stressed communication "
            "channels; (c) evacuation communication relied on radio repeaters "
            "that were unreliable in ash-fall zone — satellite-messaging backup "
            "recommended; (d) auto-reversion worked exactly as designed — "
            "the emergency ended on the timer, not on anyone's judgment call.  "
            "Overall rating: successful first activation of emergency protocol."
        ),
    },

    # 2. Currently Open — Severe drought, auto-revert in future
    {
        "id": EM_DROUGHT,
        "ecosystem_id": ECOSYSTEM_ID,
        "state": "open",
        "declared_at": datetime(2025, 7, 1, 8, 0, 0, tzinfo=timezone.utc),
        "declared_by": "Dewa Putra",
        "criteria_met": {
            "criterion_id": "EC-005",
            "criterion_name": "Severe Water Shortage at Any SHUR Facility",
            "threshold": (
                "Water tank level below 20% for 7 consecutive days OR "
                "nearby subak reports critical drought conditions"
            ),
            "actual_condition": (
                "East SHUR water tank level recorded at 18% on 2025-06-24 and "
                "dropped to 12% by 2025-06-30 (7 consecutive days below 20%).  "
                "The local subak also reported the lowest dry-season flow in "
                "12 years.  The monsoon is not expected until October."
            ),
        },
        "auto_revert_at": datetime(2025, 7, 31, 8, 0, 0, tzinfo=timezone.utc),
        "recovery_entered_at": None,
        "closed_at": None,
        "pre_authorized_roles": {
            "emergency_coordinator": {
                "person": "Dewa Putra",
                "scope": "Water rationing, emergency supply procurement, and coordination with subak",
                "max_duration_hours": 720,  # 30 days
            },
            "resource_pool_access": {
                "person": "Lani Wijaya",
                "scope": "Expedited emergency water procurement up to 5M IDR without full ACT",
                "max_duration_hours": 720,
            },
        },
        "actions_log": {
            "2025-07-01T08:00": "Crisis state declared by Dewa Putra — water tank at 12% for 7 days.",
            "2025-07-01T10:00": "OSC confirmed consent.  Auto-revert set for 2025-07-31.",
            "2025-07-01T14:00": "Water rationing protocol activated: non-drinking usage reduced to 50%.",
            "2025-07-02T09:00": "Lani authorized 3M IDR for emergency water truck delivery from Denpasar.",
            "2025-07-03T16:00": "First water delivery received.  Tank level restored to 35%.",
            "2025-07-05T08:00": "Dewa coordinating with subak for priority access to remaining spring flow.",
        },
        "post_review_status": None,  # Not yet — emergency is active
        "notes": (
            "This is the second emergency activation in OmniOne's history.  "
            "Unlike the Mount Agung event (rapid onset/rapid resolution), "
            "drought is a slow-onset crisis.  The 30-day maximum duration "
            "(criterion EC-005) may need extension if the monsoon is delayed — "
            "extension requires emergency ACT consent per crisis-coordination "
            "skill.  Melati has flagged this for post-review analysis: do "
            "slow-onset emergencies need different duration parameters?"
        ),
    },
]
