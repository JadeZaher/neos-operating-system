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
latest revision round on, so a revision needs advice of its own. The test gate
likewise counts only reports filed at or after the send-back
(`reports_since_revision`: `created_at >= ` the revision round's `updated_at`,
compared in Python), so a report on an earlier version is history and never
meets the gate of the version being decided; the page's `caller_has_reported`
and the decision record's report count use the same cut. Both new rows
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
- The proposal decision record (`record_proposal_decision(..., confirmed_by)`)
  is the confirming steward's act: `recorder` is that steward and
  `recorder_role` "steward who confirmed ratification" (it credited the
  proposer before). Its summary is plain words (no Python `True`), and its
  counts are the gate's: advice rounds with advice since the latest revision
  (`_advice_rounds_since_revision`), non-withdrawn positions in the final
  consent record, test reports since the latest revision
  (`reports_since_revision`). The decisions API adds the agreement the
  proposal was registered as (`registered_agreement`), looked up live.
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
- Participation (`require_participant`): advice, positions and test reports
  need an ACTIVE row in the proposal's ecosystem (`policy.can_participate`;
  owner rule: a pending newcomer reads, never acts). A `pending_consent` row is
  refused 403 with `code` `CONSENT_PENDING` and `consent_pending_message(<the
  ecosystem's name>)` (`refuse_pending_member`), the same words in REST, MCP
  (the message is prefixed `CONSENT_PENDING:`) and the assistant (`code` in the
  result); any other non-active row is `INACTIVE_PARTICIPANT` (advice, test) or
  `PARTICIPATE_DENIED` (positions). Advice and test reports keep the
  shared-ecosystem path (`row_optional`): a caller with NO row in the
  proposal's ecosystem, reaching it because it is shared into one where they
  are active, still advises or reports as their session member. Before this,
  any row counted, so a pending member's consent could meet the quorum of a
  shared proposal. Creating a proposal refuses a pending author the same way.
- `record_consent_position(session, proposal, *, member, position, reason)`
  is the one write for a consent position (REST, MCP and chat call it):
  `require_participant` (403 `CONSENT_PENDING` or `PARTICIPATE_DENIED`), consent stage only (409
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

## Next steps (G-Next)

`next_steps.py` answers two questions from state on every call (no table, no
notification service): what is waiting for this member (`waiting_for`), and
where a record stands (`explain_record`, `explain`). REST (`api/next_steps.py`:
the dashboard queue, the header bell, the status banner) and the assistant
(`what_needs_me`, `explain_status`, and the `next_step` of `get_proposal` /
`get_agreement`) read the same functions, so the page and the assistant say
the same words. `proposal_next_step`, `agreement_next_step` and the standing
helpers moved here from `agent/governance_tools.py` for that reason.

Nothing is re-derived. Each item or explanation asks the engine that owns the
rule:

| Record | Items (who) | explain(): next step, who decides, moves |
|---|---|---|
| proposal | advice to give (members who did not write it and have not advised this round); a position to record (no live position in the latest consent record); `close_advice` (the author, as soon as the advice move is `ready`, deadline or not); `revise` (the author, while the send-back round has no advice AND the text is unchanged since the send-back); `answer_objection` (the author, one item per open objection: "<name> objected: “<reason>”", with send back for revision or wait for the withdrawal as the way out); `confirm_ratification` (`proposal_next_moves` ready and not blocked: a steward who did not write it); `register_agreement` (ratified, `registered_agreement_id` NULL, text captured: every `policy.can_register_agreement` steward until one registers it) | `proposal_next_step(prop, gates, you, facts)`; who decides: `_proposal_decider` (advice: the author, "a steward can act for them"; test: the confirmers by name; ratified and unregistered: any steward), else the table row (`_decider`); moves = `proposal_next_moves` (the detail's `allowed_next`) |
| agreement | consent to record in the consent stage, or to renew after the version changed (`reattest_agreement`); only when the agreement asks for consent | `agreement_next_step`; table row; ceremony moves for `can_conduct_agreement_ceremony`, plus `attest` |
| emergency | co-sign (`caller_flags`); the post-emergency review and closing Recovery go to stewards only (owner default: the review alarm is a steward's) | `emergency.describe()`; dates from the same module |
| conflict | triage (`can_triage_conflict`, a hidden case yields nothing); repair check-ins whose date has come (`conflicts.next_checkin`) | `conflicts.conflict_stage`; moves = `allowed_moves` for triage, `closed` for the reporter |
| exit | the steward's next `EXIT_MOVES` move on someone else's exit (withdrawing is the leaver's choice, never a task) | `exit.NEXT_STEP`; moves = `exit.allowed_next` |
| audit | the caller's own draft (`can_finish_audit`) | (no banner) |

Rules of the queue:

- Scope: every ecosystem where the user has an ACTIVE row (REST passes the
  authorized ids, which are the same set; the assistant passes None). It is
  the member's own list, so it is not narrowed to the header selection; each
  item names its ecosystem.
- Items only for an active caller row in the record's own ecosystem (a shared
  record never gives a foreign member a task: every act needs a row there).
- Order: overdue first, then `OWNER_ACTIONS` (close_advice, revise,
  answer_objection, confirm_ratification, register_agreement: acts only this
  caller's role can take, which hold the record up until taken), then the
  nearest `due` (undated last), then kind (emergency, conflict, proposal,
  agreement, exit, audit). Before, a close_advice without a deadline sank
  below every dated item and was sorted by title (item 18 of 22 in the bell). `due` is `YYYY-MM-DD` for date columns and
  ISO with `Z` for the naive-UTC timestamps (emergencies), so browsers never
  shift it. `overdue` uses one `Clock` per request: a date passes the next day,
  a timestamp at once.
- `uid` is unique per item (a case with two repairs due yields two items).
- Cost: a few queries per open record (gates, standing). Fine at study volume;
  the trigger to batch is a member with hundreds of open proposals. Batching
  the standing lookups was skipped on purpose: the caller's position goes
  through the engine's private `current_position` helpers (latest consent
  record, legacy duplicates), and re-implementing that in bulk would fork the
  rule. The client polls once (the bell, every 5 minutes) to keep the load down.
- `close_advice` (the proposer's prompt) appears as soon as the advice->consent
  move is `ready`, deadline set or not: advice never advances by itself, so it
  must not wait silently for a date. Before the deadline (or with none) the
  words are `ADVICE_READY_PROMPT` ("Close advice and move to consent: enough
  advice is in", naming the act); once it has passed, `ADVICE_DEADLINE_PROMPT`.
  Both are the page's `adviceClosePrompt` titles, word for word.
- `revise` clears once the author edits: the proposal's `updated_at` is later
  than the revision round's `updated_at` (its insert time; `created_at` is
  ordered artificially by `created_after_newest`, so it cannot be used). In
  PostgreSQL both are the send-back transaction's `now()`, so a send-back alone
  never counts as an edit.

### Banner words (`proposal_next_step`)

`proposal_standing` is the caller's standing (author, may manage, may take
part, advised this round, position, `can_confirm`, `can_register`);
`proposal_facts` is what the sentences name at this stage: the revision round
(`act_gates.revision_round`, read back from the summary `_open_revision`
writes: who sent it back, from where, the note), open objections
(`act_gates.open_objections`, classified as the gate does), the confirmers
(`act_gates.ratification_confirmers`: active stewards, never the author), and
the registered or amended agreement's title. The assistant's tools pass the
same facts, so chat and page say the same words.

- Advice: one statement per viewer under the current manage rule (the
  owner question on who may close advice is open): the author "you decide when
  to close advice", a non-author steward "you can also close it for them",
  anyone else "<author> decides". A revision round names who sent it back, the
  note and the version, and says earlier advice, positions and test reports are
  history (the gates count none of them).
- Consent: "N positions recorded, Q needed"; each open objection by name and
  reason; the author is told how to answer (send back, or wait for the
  withdrawal), the objector that they can withdraw. Only objecting needs a
  reason (standing aside does not).
- Test: once `gates.test.met`, "the test evidence is in", the confirmers by
  name and that it is in their list; it stops inviting another report.
- Ratified: unregistered, registering is the next step by any steward;
  registered, the agreement is named and nothing more is needed.
- Plain words: no "(s)" plurals (`act_gates.counted`), no "Nobody by hand"
  (automatic moves read "It moves on by itself once ...").
