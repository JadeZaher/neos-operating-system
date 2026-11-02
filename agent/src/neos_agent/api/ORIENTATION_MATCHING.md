# Orientation chat and voluntary discovery

`orientation_chat.py` is a separate read-only OmniBot surface. Its model sees
only a server-loaded active journey and that owner's bounded conversation.
It receives no governance tools, quiz answer keys, other users' data, client
system messages or supplied identity. An active or pending member may use
their own ecosystem's journey; a global journey must already be assigned to
one of their member rows. Chat never advances the journey or grants entry.
The existing configured paid OpenRouter provider is used; disabled,
unsupported/free configuration and provider errors are honest unavailable
responses. A successful persisted model reply is the only completed turn.

POST `/orientation/chat` accepts exactly `journey_id`, `message` (1–2000
characters), optional `session_id`, and optional canonical `step_id`.
Sessions are owner-private in
`orientation_chat_sessions`, separate from governance chat history. Availability,
owner-only history and deletion are under the same prefix. Conversations
stop at 20 user turns. PostgreSQL row locking serializes writes to an
existing conversation. The hourly maintenance job deletes conversations
after 90 days without a new turn.

Required AI steps bind their private conversation to `step_<index>` and a
server hash of the journey source. A generic panel conversation, another
person's reply, another step's reply or a reply to an older journey cannot
complete that step. Completion and step-advance routes share one evidence
validator. Required surveys require a real configured-quiz result for the
caller's relevant member row, the current quiz fingerprint and server-owned
`completion_verified`; graded quizzes additionally require a genuine pass.
Non-graded readiness answers are not preferences to judge or convert into
a fake pass. Node administrators may explicitly choose an audited quiz
exemption; authorization is refreshed before locking progress and the event
does not fabricate a quiz result. Optional skips and declared branch routes
remain available. Genplan choices persist the owner's actual saved choice
using canonical server labels/output instead of returning a no-op receipt.
Switching journeys defaults to `in_progress` and clears prior completion;
validation uses the effective persisted status even when the request omits it.
Canonical genplan output is derived inside the same progress transaction,
so a failed derivation cannot leave a completed journey without its output.
The legacy acknowledgement endpoint reuses that idempotent derivation and
rejects contradictory client labels or choice keys.

Entrant journey DTOs and all model context recursively strip inline grading
keys. Authorized ecosystem stewards keep the full source for editing;
private ecosystem journeys are not exposed through the legacy list/detail
routes. Deactivating a journey preserves owner-private conversation history;
owners retain access to their own session detail and deletion even after
their membership changes. A journey referenced by progress or a private
conversation must be deactivated rather than physically deleted.

## Consent and participant discovery

The matching APIs implement the boundaries in the repository's
`GOVERNANCE-ECOSYSTEM-MATCHING-UX-GUIDE.md`. Participation access, directory
visibility, contact discovery and private matching processing are distinct.
All matching opt-ins default off. Protected people discovery requires an
active member row and `EthosUserAccess` in that same ecosystem; both the
viewer and each displayed person must opt into directory/contact discovery.
Disabled accounts and inactive memberships never appear. The endpoint reads
only public display name/headline/skills/interests, emits real profile and
member identifiers, and searches those volunteered fields. No private
organization's membership, phone, DID, quiz answer, hidden score, social
graph, popularity, wealth, protected characteristic or inferred personality
is used. Shared tags are literal case-insensitive overlap, disclosed as
`declared-overlap-v1`; the directory is alphabetical, not a ranking or fit
percentage. Directory and contact withdrawal take effect on the next read.

## Governed fit estimates

Matching profile publication is allowed only to that ecosystem's steward,
and copies the exact `act_policy.matching_profile` of an already active
agreement in that ecosystem. The publication endpoint accepts the governing
agreement UUID, not editable weights. A profile version cannot be overwritten.
This prevents an administrator from secretly changing weights for one person.

Explicit global node administrators can publish an already active, same-
ecosystem policy without inventing a membership: supply a public
`support_reason` category. This branch reauthorizes under the support lock,
permits the selected private organization lookup, and commits a redacted
public audit event atomically with the profile. It never accepts editable
weights or grants access to owner-private answers. Denied/failed support
publication attempts are recorded through the independent audit boundary.

The structured agreement-policy editor submits `ActPolicySchema.matching_profile`;
normal ACT-policy normalization preserves validated matching metadata without
using it as a lifecycle gate. A new draft follows the existing advice, consent
and test workflow before publication. Legacy malformed matching metadata is
ignored by ACT normalization and rejected by matching publication, so a broken
optional fit profile cannot block ordinary governance. Ecosystem settings expose
`uaf_agreement_id` only for an active, same-ecosystem agreement of type `uaf`.
Create the ecosystem first, then ratify and link its UAF; a newly generated
ecosystem cannot reference another ecosystem's existing UAF. Node support has
an audited reference control with the same source checks and a typed policy
editor; neither can publish unratified matching weights.

The governed configuration contains:

```json
{
  "version": "1.0",
  "algorithm_version": "affinity-v1",
  "weights": {"agreements": 0.35, "domains": 0.30, "purpose": 0.20, "practical": 0.15},
  "signals": [{
    "id": "example",
    "dimension": "agreements",
    "label": "Can you support this published commitment?",
    "weight": 1,
    "classification": "non_negotiable",
    "source": {"kind": "agreement", "id": "<UUID>", "version": "1.0", "section": "Commitments, section 1"}
  }]
}
```

The example illustrates one signal; a valid profile has 4–80 signals covering
all four dimensions. Every signal cites a same-ecosystem active agreement or
documented active domain and an exact version/section. The ecosystem's
ratified UAF and at least one documented domain must be cited. Domain
contracts need purpose plus the domain-mapping template's eleven structured
elements (responsibilities, customers, deliverables, dependencies, constraints,
challenges, resources, delegator responsibilities, competencies, metrics and
evaluation schedule) before making fit claims. Only agreement provisions
may be classified as non-negotiable. Missing/incomplete sources yield an
unavailable result and a real dossier link, never a fabricated percentage.

Owners choose matching-data consent and save optional answers as `supports`,
`discuss`, `incompatible`, or `unknown`. The published dimension weights sum
to one. Within each dimension, answered signal importance determines the
score and answered/published importance determines coverage. The headline
uses the guide's coverage-weighted formula and is suppressed below 60%
coverage. Unknown is excluded rather than scored zero. Explicit incompatibility
with an approved non-negotiable remains a separate routing cue, regardless
of the arithmetic. A result never grants membership, a role, contact access
or approval; learning needs can be left unknown without penalty.

`POST /matching/ecosystems/:id/assessments` stores an immutable configuration,
source-version/fingerprint, answer and result snapshot. Reads recompute stale
state against current ratified sources and profile publication. Editing a
source, changing its version, or publishing a new profile does not overwrite
past assessments. Corrections append private owner notes; they do not amend
the source agreement or original snapshot. Owners can export, pause, revoke,
or delete their data. Matching-consent withdrawal erases their answers and
assessment/correction records immediately; directory consent is independent.
Every matching-data writer and eraser first locks the actual owner `User`
row, then reads current consent. This includes consent creation/withdrawal,
answers, assessment creation, corrections, scoped/global deletion and
retention. A missing consent row is never a substitute for this persistent
lock. Retention rechecks age after acquiring the owner lock; expired consent
also erases that scope's private records. These paths never acquire the
NodeAdmin support lock or fabricate membership. PostgreSQL race regressions
use isolated schemas and `pg_blocking_pids`, rather than SQLite lock claims.
The hourly job expires matching data and unrenewed discovery consent after
365 days. Deletion here is immediate in the primary database; deployment
backup rotation is an infrastructure retention policy, not a promise of this
API. Matching never changes membership or charges an exit penalty.

These personal-data tables and governed publications are classified INTERNAL
in the generic support catalog. Dedicated APIs enforce ownership and governed
publication; generic CRUD cannot silently rewrite assessments, read private
answers or republish weights. Migration `y5e9b3d7a1c4` follows the coordinated
join-gate migration `x4d8a2c6f0b3`.

## Public audit time

`services.node_admin.public_json_value` serializes public audit timestamps
with an explicit UTC `Z`. Naive database timestamps mean UTC, not the
browser's local zone. The existing `json_value` is unchanged because private
evidence archives use its round-trip datetime encoding for restoration.
