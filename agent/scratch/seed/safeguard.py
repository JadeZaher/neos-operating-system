"""
Governance health audit (Layer VII — Safeguard & Capture Detection).

One comprehensive audit conducted by Melati Kusuma, covering all four
capture-risk categories with realistic indicators.

Capture-risk indicators assessed:
  - Capital capture: funder influence, resource pool concentration
  - Charisma capture: proposal pass-through rates per proposer, meeting dominance
  - Emergency capture: emergency state duration vs pre-authorization scope
  - Ossification capture: role tenure, departure rate, agreement staleness
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")


SAFEGUARD_AUDIT: dict = {
    "id": uuid.UUID("cba7b810-9dad-11d1-80b4-00c04fd430a1"),
    "ecosystem_id": ECOSYSTEM_ID,
    "audit_id": "GHA-001",
    "audit_date": date(2025, 12, 1),
    "auditor": "Melati Kusuma",
    "audit_scope": "Full ecosystem governance health audit — all ETHOS, all layers",
    "audit_period_start": date(2025, 6, 1),
    "audit_period_end": date(2025, 12, 1),
    "auditor_ids": {
        "lead": "Melati Kusuma",
        "peer_reviewers": ["Manu Dewantara", "Kai Nakamura"],
    },
    "overall_health": "fair",
    "overall_health_score": 68,  # out of 100

    # ── Capture-risk indicators ────────────────────────────────────
    "capture_risk_indicators": {
        "capital_capture": {
            "risk_level": "low",
            "score": 82,
            "indicators": {
                "funder_governance_participation": {
                    "observation": (
                        "GEV (Green Earth Vision) is the primary funder through "
                        "a 3-year grant.  GEV staff participate in governance "
                        "as individual members, not as institutional representatives.  "
                        "No GEV representative sits on OSC or holds ETHOS steward role.  "
                        "GEV's grant agreement explicitly waives governance authority."
                    ),
                    "risk": "low",
                },
                "resource_pool_concentration": {
                    "observation": (
                        "Resource pool is 80% funded by GEV grant + 20% from "
                        "community contributions and workshop fees.  Single-source "
                        "funding is a structural risk even if the funder behaves "
                        "well.  If GEV withdrew, the pool would collapse."
                    ),
                    "risk": "medium",
                    "recommendation": "Diversify funding sources to no more than 50% from any single source by 2027.",
                },
                "economic_power_governance_correlation": {
                    "observation": (
                        "No correlation detected between economic contribution "
                        "and governance participation frequency.  The highest "
                        "proposal output (Budi Santoso, 3 proposals) comes from "
                        "a smallholder farmer, not a resource contributor."
                    ),
                    "risk": "low",
                },
            },
        },
        "charisma_capture": {
            "risk_level": "medium",
            "score": 58,
            "indicators": {
                "proposal_pass_through_rate": {
                    "observation": (
                        "Manu Dewantara's proposals have a 100% consent rate (3/3).  "
                        "This is partly structural — Manu proposals are ecosystem-level "
                        "and well-designed — but it may also reflect deference.  "
                        "No proposal from Manu has received a reasoned objection."
                    ),
                    "risk": "medium",
                    "recommendation": (
                        "Ensure that at least one future Manu proposal is assigned "
                        "to a different facilitator.  Monitor for 'no objection "
                        "because Manu proposed it' pattern."
                    ),
                },
                "meeting_speaking_time_distribution": {
                    "observation": (
                        "OSC meetings show 40% of speaking time goes to the top "
                        "2 speakers (Manu and Lani).  TH assemblies are more "
                        "balanced (top 2 = 25%).  AE meetings are moderately "
                        "concentrated (top 2 = 35%)."
                    ),
                    "risk": "medium",
                    "recommendation": "OSC should implement round-robin speaking protocol.",
                },
                "proposal_fatigue_metric": {
                    "observation": (
                        "Proposal submission rate is healthy (4-5/quarter).  "
                        "No single proposer exceeds the 3-active-proposal limit.  "
                        "Advice phase participation averages 3.2 advisors/proposal.  "
                        "No fatigue detected."
                    ),
                    "risk": "low",
                },
            },
        },
        "emergency_capture": {
            "risk_level": "low",
            "score": 75,
            "indicators": {
                "emergency_activation_frequency": {
                    "observation": (
                        "Two emergencies activated in 18 months: Mount Agung "
                        "(Level 3 volcanic alert) and East SHUR drought (water "
                        "below 20% for 7 days).  Both met objective criteria.  "
                        "One emergency per 9 months is consistent with Bali's "
                        "natural hazard profile."
                    ),
                    "risk": "low",
                },
                "emergency_duration_vs_criteria": {
                    "observation": (
                        "Mount Agung: 14-day duration vs 30-day maximum.  "
                        "Closed on auto-revert timer, not later.  Current "
                        "drought emergency is tracking within its 30-day limit.  "
                        "No emergency has exceeded its pre-authorized duration."
                    ),
                    "risk": "low",
                },
                "emergency_scope_creep": {
                    "observation": (
                        "Mount Agung emergency: scope was 'evacuation logistics "
                        "and communication.'  No scope expansion occurred.  "
                        "Drought emergency: scope is 'water rationing and "
                        "procurement.'  Lani's resource access is capped at "
                        "5M IDR and she has spent 3M.  No creep detected."
                    ),
                    "risk": "low",
                },
                "post_emergency_review_compliance": {
                    "observation": (
                        "Mount Agung post-review completed within 14 days of "
                        "closure.  Findings documented and communicated.  "
                        "Drought post-review is pending (emergency active)."
                    ),
                    "risk": "low",
                },
            },
        },
        "ossification_capture": {
            "risk_level": "medium",
            "score": 55,
            "indicators": {
                "role_tenure": {
                    "observation": (
                        "Lani Wijaya: Resource Pool Steward for 18 months "
                        "(role mandates 12-month term with review).  Role "
                        "was reviewed at 12 months but stewardship continued "
                        "— no other qualified candidate stepped forward.  "
                        "Manu Dewantara: Ecosystem Architect — this role has "
                        "no defined term limit (intentional for continuity) "
                        "but also no mandatory review trigger."
                    ),
                    "risk": "medium",
                    "recommendation": (
                        "Set a mandatory rotation trigger for Resource Pool "
                        "Steward by June 2026.  Identify and mentor successor.  "
                        "Define a review trigger for Ecosystem Architect role."
                    ),
                },
                "departure_rate": {
                    "observation": (
                        "Zero completed exits in 18 months.  One exit in "
                        "progress (Rani — cooling off period).  Zero "
                        "departures is an ossification risk indicator, not "
                        "a health indicator.  Healthy ecosystems have some "
                        "turnover."
                    ),
                    "risk": "medium",
                    "recommendation": (
                        "No structural problem to fix, but monitor.  Zero "
                        "departures is statistically unusual and may mean "
                        "exit barriers exist that haven't been triggered yet."
                    ),
                },
                "agreement_staleness": {
                    "observation": (
                        "UAF: reviewed on schedule (12-month cycle).  "
                        "SHUR Access: reviewed and amended (v1.0 → v1.1).  "
                        "Resource Pool Steward commitment: review overdue "
                        "by 5 months (was due 2025-06-01).  TH Culture Code: "
                        "review overdue by 5 months.  AE Culture Code: review "
                        "overdue by 5 months.  Three agreements past due."
                    ),
                    "risk": "high",
                    "recommendation": (
                        "Urgent: schedule review for Pool Steward, TH Culture "
                        "Code, and AE Culture Code within 30 days."
                    ),
                },
            },
        },
    },

    # ── Indicator Scores (structured) ──────────────────────────────
    "indicator_scores": {
        "capital_capture_resistance": 82,
        "charisma_capture_resistance": 58,
        "emergency_capture_resistance": 75,
        "ossification_capture_resistance": 55,
        "overall_weighted": 68,
    },

    # ── Findings ───────────────────────────────────────────────────
    "findings": (
        "**Overall Health: Fair (68/100)**\n\n"
        "**Strengths.**\n"
        "- Emergency protocol is functioning correctly — two activations, "
        "both within criteria, both under duration limits, scope remained "
        "within pre-authorized boundaries.\n"
        "- Capital-governance firewall is intact.  GEV's grant agreement "
        "waives governance authority.  No correlation between economic "
        "contribution and governance participation.\n"
        "- Conflict triage system is operational and appropriately tiered.\n"
        "- Proposal rate limit (3 active per person) is respected.\n\n"
        "**Concerns.**\n"
        "- Resource pool has 80% single-source funding (GEV grant).  This "
        "is a structural vulnerability even if GEV is well-behaved.\n"
        "- Three agreements are 5 months past their scheduled review date.  "
        "This is a governance hygiene failure that could mask capture.\n"
        "- Role tenure for Resource Pool Steward (18 months vs 12-month "
        "mandate) is drifting toward ossification.\n"
        "- Manu's 100% proposal consent rate warrants structured monitoring.\n"
        "- Zero exits in 18 months may indicate undeclared exit barriers.\n\n"
        "**Emerging Risk.**\n"
        "- Slow-onset emergency (drought) is testing the 30-day duration "
        "limit.  If the monsoon is delayed, OmniOne will face its first "
        "emergency extension scenario — precedent-setting."
    ),

    # ── Recommendations ────────────────────────────────────────────
    "recommendations": {
        "critical": [
            "Schedule and complete overdue agreement reviews (Pool Steward, TH Culture Code, AE Culture Code) within 30 days",
            "Begin resource pool funding diversification planning with 50% single-source cap by 2027",
        ],
        "important": [
            "Identify and mentor Resource Pool Steward successor by June 2026",
            "Assign a different facilitator for at least one future Manu proposal to test charisma risk",
            "OSC to implement round-robin speaking protocol",
        ],
        "monitor": [
            "Drought emergency duration and potential extension scenario",
            "Exit barriers — survey participants on perceived ease of leaving",
            "Agreement review compliance rate (currently 57% — 4 of 7 reviewed on time)",
        ],
    },
    "structured_recommendations": {
        "critical": [
            {
                "action": "Schedule overdue agreement reviews",
                "owner": "Nirmala Sari (agreement steward)",
                "deadline": "2026-01-01",
                "affected_agreements": ["AG-STEW-001", "AG-ETHOS-TH-001", "AG-ETHOS-AE-001"],
            },
            {
                "action": "Begin funding diversification planning",
                "owner": "Lani Wijaya (resource steward)",
                "deadline": "2026-03-01",
                "target": "Reduce single-source funding to <50% by 2027",
            },
        ],
        "important": [
            {
                "action": "Identify Resource Pool Steward successor",
                "owner": "Lani Wijaya + OSC",
                "deadline": "2026-06-01",
            },
            {
                "action": "Test charisma-independence of Manu's proposals",
                "owner": "Sari Dewi (proposal steward)",
                "deadline": "2026-03-01",
            },
        ],
    },

    # ── Triggered Safeguards ───────────────────────────────────────
    "triggered_safeguards": {
        "auto_notify": [
            {
                "trigger": "agreement_review_overdue",
                "threshold": "agreement review date + 90 days",
                "triggered_by": ["AG-STEW-001", "AG-ETHOS-TH-001", "AG-ETHOS-AE-001"],
                "action": "Notification sent to Nirmala Sari (agreement steward) and both ETHOS stewards.",
            },
        ],
    },

    "trigger_type": "scheduled_semi_annual",
    "status": "published",
    "next_audit_date": date(2026, 6, 1),
    "next_audit_due": date(2026, 6, 1),
}
