# NEOS Seed Data Fixture

Comprehensive, realistic seed data for the NEOS governance database.
Exercises all 10 layers end-to-end against the full 46+ table schema
in `neos_agent/db/models.py`.

## Quick Start

```bash
# Default: SQLite in current directory
cd neos-operating-system/agent
python -m scratch.seed.run

# Reset and re-seed (idempotent)
python -m scratch.seed.run --reset

# Target a specific database
python -m scratch.seed.run --database postgresql+asyncpg://user:pass@localhost:5432/neos_dev
```

All seed steps are **idempotent** — checks for existing records before
inserting.  Safe to run repeatedly.  Use `--reset` to clear and
re-seed from scratch.

## File Structure

```
scratch/seed/
├── personas.py       14 named members, consistent identities, roles, backstories
├── ecosystem.py      OmniOne ecosystem + 4 domains + elements + metrics
├── agreements.py     6 agreements at every hierarchy level + ratifications + amendments + reviews
├── proposals.py      7 proposals in all ACT states + advice + consent + test data
├── decisions.py      4 historical decisions with semantic tags + dissent records
├── conflict.py       4 conflict cases (tiers 1-4) + repair agreement
├── emergency.py      2 emergencies (1 open, 1 resolved) — circuit breaker pattern
├── safeguard.py      1 governance health audit with all 4 capture-risk categories
├── exit.py           2 exit records (1 in-progress, 1 completed)
├── economic.py       Shares/needs + collaborations + TODO for missing models
├── run.py            Idempotent entry point, async SQLAlchemy
└── README.md         This file
```

## Persona Map

| Persona | Role | ETHOS | Canon? |
|---------|------|-------|--------|
| **Manu Dewantara** | Ecosystem Architect, OSC steward | OSC | ✅ |
| **Lani Wijaya** | Resource Pool Steward | AE | ✅ |
| **Kai Nakamura** | Conflict Facilitator / Lead Triager | OSC | ✅ |
| **Nirmala Sari** | Agreement Steward | AE | |
| **Dewa Putra** | Emergency Coordinator | AE | |
| **Indra Gunawan** | Developer / NEOS agent builder | AE | |
| **Sari Dewi** | Proposal Steward / ACT Facilitator | TH | |
| **Gede Artha** | Bamboo Builder / Craftsman | TH + AE | |
| **Melati Kusuma** | Governance Health Auditor | OSC | |
| **Putu Ardana** | Culture Code Steward | TH | |
| **Ayu Pertiwi** | Inter-ETHOS Liaison | OSC | |
| **Budi Santoso** | Smallholder Farmer | TH | |
| **Rani Maheswari** | Graphic Designer (in onboarding) | — | |
| **Ketut Arsana** | Exit Coordinator / Data Portability | OSC | |

## Layer Coverage

| Layer | Seed Module | Tables Exercised |
|-------|-------------|------------------|
| I — Agreement | `agreements.py` | agreements, agreement_versions, ratification_records, amendment_records, review_records |
| II — Authority & Role | `ecosystem.py` + `personas.py` | ecosystems, users, members, member_onboarding, member_status_transitions, domains, domain_elements, domain_metrics, circle_memberships |
| III — ACT Engine | `proposals.py` | proposals, advice_logs, advice_entries, advice_non_respondents, consent_records, consent_participants, consent_integration_rounds, consent_objections_addressed, test_reports, test_success_criteria |
| IV — Economic | `economic.py` | shares_needs, collaborations (+ TODO for funding pools, resource requests, Current-Sees) |
| V — Inter-Unit | `ecosystem.py` + `proposals.py` | cross-ETHOS proposal (GAIA-stalled), inter-ETHOS collaboration, domain hierarchy |
| VI — Conflict | `conflict.py` | conflict_cases, repair_agreement_records |
| VII — Safeguard | `safeguard.py` | governance_health_audits |
| VIII — Emergency | `emergency.py` | emergency_states |
| IX — Memory | `decisions.py` | decision_records, decision_participants, decision_dissent_records, decision_semantic_tags |
| X — Exit | `exit.py` | exit_records |

## Database Tables

### Tables Seeded (31)
`ecosystems`, `users`, `members`, `member_onboarding`, `member_status_transitions`,
`domains`, `domain_elements`, `domain_metrics`, `circle_memberships`,
`agreements`, `agreement_versions`, `agreement_ratification_records`,
`amendment_records`, `review_records`,
`proposals`, `advice_logs`, `advice_entries`, `advice_non_respondents`,
`consent_records`, `consent_participants`, `consent_integration_rounds`,
`consent_objections_addressed`, `test_reports`, `test_success_criteria`,
`decision_records`, `decision_participants`, `decision_dissent_records`,
`decision_semantic_tags`, `conflict_cases`, `repair_agreement_records`,
`governance_health_audits`, `emergency_states`, `exit_records`,
`shares_needs`, `collaborations`

### Tables NOT Seeded (model gaps or intentionally out-of-scope)
| Table | Reason |
|-------|--------|
| `agent_sessions` | Runtime-only — not seed data |
| `auth_sessions`, `auth_challenges` | Runtime-only — authentication sessions |
| `conversations`, `conversation_participants`, `messages`, `conversation_links` | Runtime messaging — test with integration tests |
| `push_subscriptions` | Runtime-only — device-level |
| `journey_maps`, `ethos_user_access`, `user_journey_progress` | Runtime orientation — test with integration tests |
| `compliance_summaries` | AI-generated, regenerated on 30-day cycle — not seed data |
| `funding_pools` | ❌ Model missing — TODO in `economic.py` |
| `resource_requests` | ❌ Model missing — TODO in `economic.py` |
| `current_see_balances` | ❌ Model missing — TODO in `economic.py` |
| `pool_transactions` | ❌ Model missing — TODO in `economic.py` |
| `commons_indicators` | ❌ Model missing — TODO in `economic.py` |

## Tests This Seed Enables

### Top 3 First Integration Tests

1. **`test_full_proposal_lifecycle`**
   — Walk PROP-006 from advice through consent to test to ratified.
   — Assert each status transition, advice entries populated, consent
     participants recorded, test criteria evaluated.  Verifies ACT engine
     end-to-end against realistic data.

2. **`test_conflict_triage_routing`**
   — Query all 4 conflict cases, verify each is routed to the correct
     tier.  Assert that Tier 3 case has a repair agreement with all
     check-ins.  Verifies Layer VI triage logic and repair tracking.

3. **`test_emergency_circuit_breaker`**
   — Verify EM-002 (drought) is in `open` state with auto-revert in
     the future.  Verify EM-001 (Mount Agung) completed the full
     circuit breaker cycle (open → recovery → closed).  Assert
     pre-authorized roles scopes are respected.  Verifies Layer VIII
     emergency state machine.

### Additional Integration Tests

4. **`test_agreement_hierarchy_integrity`**
   — Walk the agreement tree: UAF → Master Plan → SHUR Access →
     Pool Steward.  Verify parent_agreement_id chains.  Assert
     hierarchy levels are correct.  Check amendment record links
     to the correct agreement version.

5. **`test_exit_data_portability`**
   — Query EX-001 (completed exit) and verify commitment unwinding
     status.  Assert data export completed date is before departure
     date.  Verify re-entry eligibility is set.

6. **`test_capture_risk_indicators`**
   — Query GHA-001 audit.  Assert all 4 capture categories are
     assessed.  Verify ossification indicators flag overdue
     agreement reviews.  Verify capital capture indicators flag
     single-source funding risk.

7. **`test_cross_ethos_coordination`**
   — Query the GAIA-stalled proposal (PROP-001).  Assert it has
     objections from both ETHOS.  Verify integration rounds
     progressed.  Assert escalation level is GAIA-3.

8. **`test_persona_consistency`**
   — Verify that all 14 personas have corresponding User + Member
     records.  Assert canonical personas (Lani, Kai, Manu) have
     the expected roles.  Verify domain stewards are in correct
     circle memberships.

9. **`test_decision_precedent_search`**
   — Query decisions by semantic tag.  Assert bamboo decision
     is tagged with "construction standards".  Assert emergency
     decision is tagged with "volcanic hazard" and "crisis
     coordination".  Verify dissent records link to correct
     decisions.

10. **`test_agreement_review_compliance`**
    — Query all agreements and assert review_date is not null
    for ratified agreements.  Verify SHUR Access has a review
    record.  Assert overdue agreements (Pool Steward, TH Culture,
    AE Culture) are flagged by the audit.

## Realism Notes

- **Dates are relative.**  Most dates use `date.today() - timedelta(...)`
  so the seed feels recent whenever you run it.  Historical decisions
  use absolute dates (2024-2025) for narrative consistency.

- **Personas have backstories.**  Every persona has a realistic backstory
  rooted in Balinese geography, economics, and culture.  Skills align
  with roles.  The farmer (Budi) is not a governance expert; the
  architect (Manu) is.  This creates realistic power dynamics.

- **Conflicts are subtle.**  The seed conflict at Tier 2 involves a
  well-meaning community member who doesn't understand why rules exist —
  not a villain.  The Tier 4 conflict is a structural values difference
  between ETHOS units.  Real governance conflicts are rarely dramatic.

- **The audit is honest.**  The governance health audit (GHA-001)
  reports a fair score (68/100) with real vulnerabilities: single-source
  funding, overdue reviews, role tenure drift.  It does not pretend
  everything is fine.

- **TODO comments are explicit.**  Where models are missing from
  `db/models.py`, the TODO comments in `economic.py` include the full
  schema shapes needed so the next developer can implement them.

## Cross-References

- NEOS skill stack: `neos-operating-system/neos-core/`
- Database models: `neos_agent/db/models.py`
- Async session: `neos_agent/db/session.py`
