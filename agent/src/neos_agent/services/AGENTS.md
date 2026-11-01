# Services

## ACT lifecycle

`act_gates.py` is the one place that says which ACT status moves exist, which
gate each one needs, who may make it by hand, and which ones the engine takes
by itself. REST (`api/proposals.py`, `api/agreements.py`), the MCP server and
the chat assistant tools all call it, so the three surfaces cannot drift
(executable parity table: `tests/test_uxqa_p1_mcp_parity.py`, documented in
`api/AGENTS.md` "ACT parity").

### Tables

`PROPOSAL_LIFECYCLE` and `AGREEMENT_LIFECYCLE` are `Lifecycle` values: a tuple
of `Move(source, target, gate=None, automatic=False, steward_only=False,
note_required=False)` plus `terminal` statuses. They stay separate because
agreements continue past activation (review, sunset, archive) and have no
withdraw; proposals end at ratified or withdrawn.

| Record | Move | Gate | Automatic | By hand |
|---|---|---|---|---|
| proposal | draft -> advice | - | no | manage rule |
| proposal | advice -> consent | advice | **no** (owner decision) | manage rule: the proposer closes advice |
| proposal | consent -> test | consent | yes | manage rule |
| proposal | consent -> advice | - | no | manage rule + note (send back for revision) |
| proposal | test -> advice | - | no | manage rule + note (send back for revision) |
| proposal | test -> ratified | test | **no** (owner decision) | a steward who did not write it (`policy.can_confirm_ratification`) |
| proposal | non-terminal -> withdrawn | - | no | manage rule |
| agreement | draft -> advice | - | no | ceremony steward + evidence |
| agreement | advice -> consent | advice | yes | ceremony steward + evidence |
| agreement | consent -> test | consent | yes | ceremony steward + evidence |
| agreement | test -> active | test | yes | ceremony steward + evidence |
| agreement | active -> under_review | - | no | ceremony steward |
| agreement | under_review -> sunset | - | no | ceremony steward |
| agreement | under_review -> active | test | no | ceremony steward + evidence |
| agreement | sunset -> archived | - | no | ceremony steward |

"Manage rule" is `policy.can_manage_proposal` (author or mod+ steward);
"ceremony steward" is `policy.can_conduct_agreement_ceremony` (active admin
or owner). The two steward meanings stay under those two names on purpose.
`created` is a legacy alias of `draft` (old chat drafts). `ratified` and
`withdrawn` are terminal: a decided or withdrawn proposal cannot be withdrawn
(it could before, from any status).

Owner decisions, live since 2026-10-31 (`tests/test_act_lifecycle.py::
test_owner_decisions_are_live_in_the_table` goes red if either is flipped back):

- **Advice closes on the proposer's call.** advice -> consent has no
  `automatic`; the advice deadline is a backstop, not a timer: once it passes,
  `gates.advice.deadline_passed` is true and the proposer's page asks "Advice
  deadline passed: move to consent?". Nothing moves by itself.
- **A steward confirms ratification.** test -> ratified is `steward_only`; test
  reports are evidence (each names its reporter), never self-certifying, and
  the confirming steward is never the author: a non-steward proposer gets 403
  `STEWARD_MOVE_DENIED`, a steward who wrote it 403 with `code`
  `NEEDS_ANOTHER_STEWARD` (`NEEDS_ANOTHER_STEWARD` tells a lone steward to give
  someone the moderator role first). `allowed_next` still lists the move for the
  author with `blocked: "needs_another_steward"`, so the page says "Another
  steward needs to confirm this" instead of offering a button. A legacy proposal
  with no author link has no author to exclude.

Send back for revision (consent or test -> advice) needs a note
(`NOTE_REQUIRED`, 400). Entering advice that way bumps the proposal's minor
version and opens a fresh advice round (the note is its
`proposer_modifications`) and a fresh consent record, so earlier positions
stay as history. The advice gate counts rounds that carry advice from the
latest revision round on, so a revision needs advice of its own. Both new rows
are stamped strictly after the proposal's newest row (`created_after_newest`):
"latest" is ordered by `created_at`, which SQLite stores to the second.

The detail payload's `allowed_next` (`proposal_next_moves`) lists the manual
moves this caller may make now with `ready` (gate met), `gate`,
`note_required` and `steward_only`, so the page draws buttons from the table
instead of a client copy.

### Engine

- `transition_proposal(session, proposal, *, to=None, caller) -> ActOutcome`.
  With `to`: manage rule (403), table (400 with `allowed`), `steward_only`
  (403), gate (409 with `gates`), then the move. Always: every automatic move
  whose gate is met, re-evaluating the gates after each. `caller` is the
  member row resolved from the authenticated identity (REST `caller_in`, MCP
  token owner, chat `caller_user_id`), never a request or model field.
- Agreements: `advance_agreement` (the cascade) and `apply_agreement_move`
  (one validated manual move). `api/agreements.transition_agreement` wraps
  them with the ceremony rule, evidence and version snapshots, because
  snapshots and fingerprints belong to the agreements API. REST, MCP and the
  chat tool `update_agreement_status` all call it.
- Entering a stage is the only place side effects happen: ratified mints the
  proposal decision record; every agreement stage records its ceremony and
  active mints the commitment record. So a manual ratification or activation
  mints its artifact too (it did not before for proposals).
- Refusals raise `TransitionRefused`, an `ApiError`: REST renders it as is,
  MCP turns it into a `ValueError`, chat into `{"success": false}`.
- `ActOutcome` carries `status`, `gates`, `moved` (the requested move),
  `auto_transitions` and `decision_record_id`; `attach(payload)` adds them to
  a response so no handler builds the shape by hand. `auto_transitions`
  never includes the requested move.
- `on_transition(listener)` is the single hook point: `listener(session,
  Transition)` runs after every applied move, manual or automatic, inside the
  caller's transaction. Nothing registers yet (notifications are a later
  feature).
- `consent_position` maps the assistant's `objection` to the engine's
  `object` at every boundary, and `proposal_gate_status` classifies stored
  positions through it too, so any legacy spelling (`Objection`, padded)
  blocks. Migration `o7c3e9a5d2f8` rewrote the stored `objection` rows to
  `object`. A proposal that already advanced past consent over such a row is
  not reopened.
- `record_consent_position(session, proposal, *, member, position, reason)`
  is the one write for a consent position (REST, MCP and chat call it):
  `can_participate` (403 `PARTICIPATE_DENIED`), consent stage only (409
  `CONSENT_CLOSED`), vocabulary `consent | stand_aside | object` (400), an
  objection needs a reason, consensus refuses a stand-aside. It keeps one row
  per member in the latest record, owned ONLY by `member_id` (never by display
  name, which members can edit), and replaces it on change. A legacy row with
  NULL `member_id` is read-only history that still counts in the gate; see
  `alembic/AGENTS.md` "p8d4f1b6e3a9" for the backfill.
  `withdraw_consent_position` marks the caller's own row `withdrawn`, which is
  how an objection's author lifts it; nobody else can. Both then cascade and
  keep `ConsentRecord.quorum_met` in step with the gate.

### One gate vocabulary

| Record | `consent_quorum` declared | undeclared |
|---|---|---|
| proposal | that many positions (from the proposal or inherited from its governing agreement) | 1 position (`DEFAULT_PROPOSAL_QUORUM`, owner default) |
| agreement | that many member attestations | every participating member |

`gates.consent.quorum_source` says which (`proposal`, `agreement`, `default`;
agreements: `agreement` or `all_members`) and the UI explains it from there.
Decision modes are `consent` and `consensus` (`consent_mode`); consensus also
holds the gate on a (legacy) stand-aside. A governing or amended agreement must
be in force (`active` or `under_review`); the old `advice` and `autocratic`
decision types decided nothing and are refused.

The engine never commits; callers own the transaction.
