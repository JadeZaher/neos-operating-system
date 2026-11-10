# Services

## Community engagement

`engagement_events.py` records source occurrences in the caller's transaction. `engagement.py` owns current source visibility, follows and personal inbox state. `engagement_delivery.py` owns contact generations, consent, immutable provider attempts and leased delivery; `engagement_providers.py` is the transport boundary. External sending defaults off. Neither a read receipt nor a notification changes governance obligations. Design, provider sources and the full lifecycle/precedence contract are in the root `conductor/tracks/community_engagement_20261102/` track. Messages from both ordinary chat and opportunity-response branches share message-ID occurrence identity; private message bodies never enter community events.

## Ordinary operator service boundaries

`member_messaging.py` is the request-free implementation used by the messaging
REST endpoints and ordinary operator tools. Reads check current participation;
lists/searches preserve the selection plus cross-ecosystem post-reply rule.
New conversations validate all recipients against active memberships in the
caller's active ecosystems, including cross-ecosystem contacts surfaced by the
existing member picker. The creator/sender is resolved from the actual User's
Member rows. A caller cannot add an unrelated private outsider or supply a
different sender. One exception: a signed-in account with an active or
pending row may open a direct conversation with an ecosystem's public owner
(the oldest active `role="owner"` whose user is not disabled; none is null).
Pending rows can message that owner and no one else. A private ecosystem
still requires a row there. Repeating it reuses the direct conversation.
Pending sends use the messaging websocket's one-second limit. Services flush
but do not commit. Message WebSocket events are queued on the SQLAlchemy
session and broadcast only after successful commit.

`exchange.prepare_collaboration` validates the normal source/target, consent,
linked-post, date and active-domain requirements without writing, allowing the
operator to ask a valid confirmation first. `propose_collaboration` reuses that
preparation. Domain discovery and target lookup share `collaboration_domain_clause`;
collaboration lists share `search_collaborations` and the existing visibility rule.

The REST modules expose request-free operations where they previously embedded
mutation: `safeguards.prepare_audit_publication` / `publish_audit_record` and
draft-edit/abandon validators; `exit.validate_exit_move` / `apply_exit_move`;
`conflicts.prepare_case_update` / `apply_case_update` and repair equivalents.
The operator calls those functions with real scoped records and caller rows.
It never invokes a route via a synthetic request or copies policy into tools.
Publication plans are fingerprinted before confirmation; a changed plan cannot
be published with an old approval. Repair writes accept active/fulfilled and
cannot evade the parties' attestation by using an alternate completion spelling.

Coverage: `tests/test_personal_operator_workflows.py` plus the existing messaging,
exchange, governance-care, maintenance, exit and actor-boundary suites. All new
source and tests are authored before the coordinator's integrated sweep.

## Configured entry quizzes

`join_gates.py` is the canonical prerequisite check for ecosystem enrollment, re-entry and activation,
domain/circle participation (including all domain ancestors), and team participation. A quiz is required only
when it is marked `is_entry_quiz` or belongs to a configured `is_onboarding_required` course of the applicable
scope. No quiz configured means no quiz requirement. Unpublished, unsupported or empty configured quizzes fail closed.
Knowledge quizzes with answer keys require a server-graded pass. Valid questionnaires without answer keys
require verified completion, without judging readiness declarations or personal preferences as right or wrong.
Schema determines this distinction; existing `mode="standard"` readiness surveys remain completion-based.
All applicable quizzes must have a server-verified result for the entrant's actual membership, with the
current content/scope/passing-threshold fingerprint, including course identity and its effective ecosystem/domain.
Legacy quiz rows with no direct ecosystem safely inherit their course's ecosystem and domain; inconsistent
course scopes fail closed. Moving a quiz or course invalidates the old pass for new admission. Legacy results without grading provenance remain history;
they do not grant new admission. Existing active memberships and subgroup participation are not demoted.

`member_lifecycle` uses `pending_consent` for the combined entry gate, so a newcomer can read and take the
published quiz before becoming active. Agreement attestation and quiz submission both call gate-aware
activation: completing either first never bypasses the other. Steward restores and ordinary team adds check
the entrant's requirements. Existing proposal-author rights are a separate established policy; enrollment
gates do not revoke authorship over historical artifacts.

An enabled, explicitly assigned NodeAdmin entrant bypasses quizzes only. Builder/co-creator profiles confer
no exemption. An administrator adding an ordinary entrant does not exempt that entrant. Bypassed admission
records a public `join_quiz_bypass` event and never fabricates a quiz attempt or agreement consent. Explicit
technical console corrections remain auditable support operations under the separate support policy.

The shared DTO contains `target_type`, `target_id`, `eligible`, `status`, `required_quizzes`,
`required_agreements`, and `quiz_bypass: {applied, reason}`. Each requirement carries `completion_mode`
(`graded` or `completion`). Quiz statuses are `required`, `passed`, `completed`, `unavailable`, or `bypassed`;
the bypass reason is `node_admin`. Links use `/quiz/take/:id` and
`/agreements/:id`. Blocked actions return 409 with `JOIN_QUIZ_REQUIRED`, `JOIN_QUIZ_UNAVAILABLE`, or
`CONSENT_REQUIRED` plus the complete `join_gates` DTO. New enrollment persists its pending membership and
returns the DTO; repeated pending enrollment does not create another row. Auth pending gates and the
steward newcomer queue expose the same DTO.

Candidate quiz content and result serialization remove answer keys. Submission accepts only answers and
time spent, resolves the actual caller, checks publication and ecosystem access, and verifies completion on the server.
`QuizResult.completion_verified` defaults false and can be set only by this verification path. Every configured
required field must have a valid typed answer from its allowed choices; legacy fields without `isRequired`
are required. Explicit boolean false is an answer. Unknown fields, unsupported formats, malformed choices,
empty submissions and blank required text cannot complete a questionnaire. Nongraded results keep `is_passed`
null; knowledge results additionally require a passing score for admission. `quiz_attempt_complete` is that
check for one stored attempt; the first-month queue uses it too (admission still matches the current fingerprint).
No client completion/pass flag is accepted.
`target_ecosystem_id` is optional submission scope context for a shared global quiz. The server resolves the
actual caller's active/pending row there; a local quiz rejects a mismatched target. It never accepts a member
identity override. Orientation passes its current ecosystem, so a shared quiz result binds the journey's actual
membership instead of an unrelated default row. Result ownership remains strict. `GET /quizzes/:id?candidate=1`
forces candidate redaction even for authors/stewards; the take/orientation cache key is separate from editing.
Quiz editing by stewards retains answer keys; global privileged editing uses the audited admin boundary.

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
proposer_until_deadline=False, note_required=False)` plus `terminal` statuses. They stay separate because
agreements continue past activation (review, sunset, archive) and have no
withdraw; proposals end at ratified or withdrawn.

| Record | Move | Gate | Automatic | By hand |
|---|---|---|---|---|
| proposal | draft -> advice | - | no | manage rule |
| proposal | advice -> consent | advice | **no** (owner decision) | the proposer; another steward only after the advice deadline (`policy.can_close_advice`) |
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
| agreement | under_review -> active | - (FX-Maint: the review's findings are the evidence) | no | ceremony steward + findings |
| agreement | sunset -> archived | sunset_ended (FX-Maint: the sunset date has passed) | no | ceremony steward |

"Manage rule" is `policy.can_manage_proposal` (author or mod+ steward);
"ceremony steward" is `policy.can_conduct_agreement_ceremony` (active admin
or owner). The two steward meanings stay under those two names on purpose.
`created` is a legacy alias of `draft` (old chat drafts). `ratified` and
`withdrawn` are terminal: a decided or withdrawn proposal cannot be withdrawn
(it could before, from any status).

Owner decisions, live since 2026-10-31 and 2026-11-01 (`tests/test_act_lifecycle.py::
test_owner_decisions_are_live_in_the_table` goes red if one is flipped back):

- **Advice closes on the proposer's call.** advice -> consent has no
  `automatic`; the advice deadline is a backstop, not a timer: once it passes,
  `gates.advice.deadline_passed` is true and the proposer's page asks "Advice
  deadline passed: move to consent?". Nothing moves by itself.
- **Only the proposer closes advice before its deadline** (2026-11-01). The
  move carries `proposer_until_deadline`, which the engine checks through ONE
  predicate, `policy.can_close_advice(member, proposal, today)`:

  | Caller | No deadline | Before the deadline | After it (deadline < today) |
  |---|---|---|---|
  | the proposer | yes | yes | yes |
  | a steward who did not write it | no | no | yes ("absent proposer") |
  | a steward, legacy proposal (no `proposer_member_id`) | yes | yes | yes |
  | anyone else | no (manage rule) | no | no |

  A refused steward gets 403 `code` `ADVICE_CLOSE_PROPOSER_ONLY`
  (`advice_close_refusal`: "The proposer closes advice. You can close it after
  the advice deadline (<date>) if they haven't.", or "...has no advice
  deadline, so only they can close it.") plus `advice_deadline`; MCP prefixes
  the code, chat returns it as `code`. `allowed_next` still lists the move for
  that steward with `blocked: "proposer_closes_advice"`, so the page says who
  decides. Legacy proposals have no author who could act, so their stewards
  keep closing advice as before (they also keep the proposer's queue items).
  REST, MCP and chat inherit it through `transition_proposal`; the assistant's
  pre-confirmation check and the engine share `move_authority_refusal`. A
  deadline passes the day after it (`advice_deadline_passed`), as
  `gates.advice.deadline_passed` and the queue's `Clock` count it.
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
stay as history. The revision round starts with NO advice deadline
(`_open_revision` clears it, and the round's `advice_window_end` is null): the old
one is for the old version and may have passed, which would let a steward close
the round at once; until the proposer sets a new one only the proposer may close
advice. The advice gate counts rounds that carry advice from the
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
`note_required`, `steward_only` and `blocked` (`needs_another_steward` for the
author of a test proposal, `proposer_closes_advice` for a steward before the
advice deadline), so the page draws buttons from the table instead of a client
copy.

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

**The author's own position counts** (owner decision 2026-11-01, no code
change): the consent gate counts every live position in the latest record,
the author's included, and the queue asks the author to record one like any
member. With the default quorum of 1 the author can complete consent alone
(the page warns before that press, `consentCompletesRound`); a proposal or its
governing agreement raises `consent_quorum` when that is not wanted.
`tests/test_act_lifecycle.py::test_the_authors_own_consent_counts_toward_the_quorum`
goes red if the gate ever excludes the author.

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
| proposal | advice to give (members who did not write it and have not advised this round); a position to record (no live position in the latest consent record); `close_advice` (the author, as soon as the advice move is `ready`, deadline or not; a steward who did not write it only once the deadline has passed, the move is ready and not blocked: the absent proposer); `revise` (the author, while the send-back round has no advice AND the text is unchanged since the send-back); `answer_objection` (the author, one item per open objection: "<name> objected: “<reason>”", with send back for revision or wait for the withdrawal as the way out); `confirm_ratification` (`proposal_next_moves` ready and not blocked: a steward who did not write it); `register_agreement` (ratified, `registered_agreement_id` NULL, text captured: every `policy.can_register_agreement` steward until one registers it) | `proposal_next_step(prop, gates, you, facts)`; who decides: `_proposal_decider` (advice: the author, plus when a steward may close it for them: after the deadline, or never without one; test: the confirmers by name; ratified and unregistered: any steward), else the table row (`_decider`); moves = `proposal_next_moves` (the detail's `allowed_next`) |
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
- Order (`_queue_order`): overdue first, then `FIRST_TIER`, then the
  nearest `due` (undated last), then kind (`_KIND_ORDER`: emergency, conflict,
  proposal/newcomer, agreement, exit, audit, collaboration, share_need), then
  `_STEP_ORDER`, then the title. `FIRST_TIER` = `OWNER_ACTIONS` (close_advice,
  revise, answer_objection, confirm_ratification, register_agreement,
  finish_review: acts only this caller's role can take, which hold the record
  up until taken) + `UNBLOCKING_ACTIONS` (read_response, approve_collaboration,
  respond_to_audit: acts another person is waiting on; uxqa pass 03). Before,
  a close_advice without a deadline sank below every dated item and was sorted
  by title (item 18 of 22 in the bell); pass 03 found the same for an answer
  to your post (item 25 of 26): every undated act sank under dated advice and
  consent items, so the person who answered waited on a list nobody reached.
  `_STEP_ORDER` puts a step before the one that builds on it when kind and
  date tie (`start_orientation` before `take_entry_quiz`; the title used to
  put "Take ..." first). `due` is `YYYY-MM-DD` for date columns and
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
  Both are the page's `adviceClosePrompt` titles, word for word. A steward's
  item (deadline passed, proposer silent) reads
  `ADVICE_DEADLINE_STEWARD_PROMPT` ("Advice deadline passed: close advice for
  the proposer?"), the page's title for a non-proposer; every eligible steward
  sees it until one of them, or the proposer, closes advice.
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

- Advice: one statement per viewer (owner decision 2026-11-01): the author
  "you decide when to close advice", a non-author steward when they may close
  it (`_steward_advice_close`: after the deadline "<date>", once it passed, or
  "only <author> can" without one), anyone else "<author> decides". A revision round names who sent it back, the
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


## Maintenance and health (G-Maint)

### One date rule (`dates.py`)

"Has this date passed?" has one answer, computed by the server only; the client words the server's
`overdue` flag and never computes it (client `lib/next-steps.ts` `dueStatus`).

| Value | Passes when | Code |
|---|---|---|
| date-only (review, sunset, advice and consent deadlines, next audit, handoff, check-ins) | the day has ended everywhere on Earth: `due < aoe_today(now)`, where `aoe_today = (utc_now - 12h).date()` | `date_passed(due, now)` |
| timestamp (naive UTC column) | at that instant, compared in UTC (aware values are converted) | `date_passed(moment, now)` |

Why "anywhere on Earth" (owner default 2026-11-01): nobody is told "overdue", and no steward may
close advice for an absent proposer, while it is still the due date for someone. One constant,
`DAY_ENDS_EVERYWHERE_AFTER`, reverts it to UTC midnight. `aoe_today` is "today" for every due-date
decision (the queue `Clock`, `can_close_advice` in `proposal_standing`, the proposal detail's
`allowed_next`, review and sunset dates); creation stamps use `utc_today()`.

`next_steps.Clock.at(now)` takes ONE reading: `today = aoe_today(now)` (it used to read the server's
local `date.today()` and ignore `now`, the wave-B LOW), and `Clock.past` is `date_passed`. Every
queue source reads dates through `scope.clock`, so the switch reaches the other lanes' items.
FX-Maint closed the hand-off: `act_gates` decides the advice deadline with the rule too
(`transition_proposal`'s `move_authority_refusal`, `proposal_gate_status.deadline_passed`,
`proposal_next_moves`' default `today`), as do the chat pre-confirmation refusal and the conflict case
page's check-in flag (`api/conflicts.next_checkin`); conflict creation stamps use `utc_today()`. REST,
the queue and the banner now agree to the instant (`tests/test_g_health.py`, 11:59 vs 12:00 UTC rows).

**The database session runs in UTC.** `db/session.create_db_engine` passes asyncpg
`server_settings={"timezone": "UTC"}` (the MCP engine too). `TimestampMixin` stamps
`server_default=now()` into naive columns, and PostgreSQL writes that in the session TimeZone; the
study database runs America/Denver, so `created_at` was 6-7 hours behind the Python-UTC columns of
the same row (`attested_at`). Pinning the session makes both naive UTC, which the app-wide `Z` on API
datetimes (craft wave 2) needs first. SQLite has no session zone (no-op). Rows written before the pin
keep their local stamps; check `SHOW timezone` on production before shipping the `Z` fix.
`tests/test_g_health_migration.py` proves the pin on a database whose default is America/Denver.

### Health snapshot (`health.py`)

The framework separates observation (computed data, the independent monitor's role) from analysis
(a human auditor rates each indicator) (`neos-core/layer-07-safeguard`). `health_snapshot(session,
ecosystem_id, start=, end=, now=)` is the observation half: read-only, every framework indicator for
the period (default the 90 days ending `aoe_today`), each with `measured_value`, `unit`, `basis`
(how it was computed, with its caveat), `band` (the framework threshold, for reference only) and
`computable`; plus "needs attention" counts with links. It never rates a status: a computed health
score was rejected (review §8), statuses stay human.

| Indicator | Computed from | Caveat |
|---|---|---|
| GHI-01 authorship diversity | distinct `proposer_member_id` (else lower-cased `proposer`) / proposals created in the period | - |
| GHI-02 approval by author role | ratified / (ratified + withdrawn) per group, leadership = mod+ today | today's role; unlinked authors left out; "n/a" below 3 decided per group |
| GHI-03 resource concentration | - | not computable yet (no resource records) |
| GHI-04 participation trend | distinct members with advice, a consent position, a test report or an agreement consent, this period vs the one before | member-linked rows only; same denominator, so it is the change in participants |
| GHI-05 leadership tenure | per current mod+: latest `role_grant` INTO leadership from a non-leadership tier, else `members.created_at`; cycles of 90 days | ecosystem roles only; grants recorded since 2026-10-31, so older holders are overstated |
| GHI-06 objection integration | objection rows (plus withdrawn rows that kept a reason) followed by a send-back from consent | changing an objection overwrites its row |
| GHI-07 review compliance | review records whose `evaluation.due_date` is in the period (`on_time`), plus agreements in force whose date passed unreviewed (late) or whose review started by its date (on time) | - |
| GHI-08 cross-unit engagement | collaborations touching the ecosystem's domains plus shared proposals and agreements, per 90 days | - |

Needs attention: reviews overdue, stalled proposals (advice past its deadline; advice with no
deadline and no advice for 30 days; consent past its deadline; test with no report for 30 days),
newcomers waiting more than 14 days, open conflicts (untriaged more than 7 days, oldest age),
emergencies in the period or open (Recovery review overdue), exits in the last 30 days (the
framework's 20% audit trigger) and authority concentration. Owner default: these are counts with
links, never queue items. Cost: a handful of queries per indicator, a query per open proposal for
the stall check; fine at study volume (the trigger to batch is hundreds of open proposals).

One period rule (FX-Maint F11): `period_bounds(start, end)` is what the snapshot endpoint, `health_snapshot`
and publish all use: no bound, the 90 days ending `aoe_today`; one bound, 90 days from it. Publish froze
"start to today" while the form previewed "start to start + 89", with different values and ratings asked for.

`audit_due_date` (framework C, E.10): the earliest of the latest published audit's
`next_audit_due` (else its date + 90), 30 days after an emergency closed since then, or, never
audited, 90 days after the ecosystem began. `frozen_indicators` builds the published rows (value,
unit, basis, band, prior value, trend, the auditor's status and notes) and lists the computable
indicators that have data but no rating.

### Queue items (registry sources in `next_steps.py`, section "G-Maint")

| Item | Who | When |
|---|---|---|
| `start_review` | `can_conduct_agreement_ceremony` (active admin/owner), never mods (they could not act) | in force (`active`) from 14 days before `review_date` (`REVIEW_NOTICE_DAYS`); overdue after it |
| `finish_review` (in `OWNER_ACTIONS`) | same | `under_review` |
| `archive_agreement` | same | `sunset` and `sunset_date` has passed; `overdue` is false (it became possible, nothing is late) |
| `audit_due` | stewards (mod+) | from 14 days before `audit_due_date`, unless a draft audit exists there; it links to `/safeguards` and says who records it (a non-steward, or a self-assessment when nobody else is active) |
| `respond_to_audit` (in `UNBLOCKING_ACTIONS`) | stewards | the latest published audit rates an indicator `critical` (`RESPOND_TO_RATINGS`, owner default: warnings show on the page only); a newer audit clears it |

The agreement banner names the review date ("Its next review is due ..." / "was due ...; an admin
or owner starts it"), and overdue never takes an agreement out of force (framework agreement-review
I-J). A sunset's end is the banner's due date ("Sunset ends"), never "overdue". The `audit` banner
(`EXPLAIN_KINDS`, `_EXPLAINERS["audit"]`) says draft or published, the critical indicators, who
responds and when the next audit is due. Deferred: a proposal citing the audit (`responds_to_audit`
in `related_proposals`) as a second way to clear `respond_to_audit`; it needs the proposal form.

### FX-Maint (wave-c fix wave)

These rows supersede the table above where they differ (`uxqa/governance/wave-c-review-*.md`).

| Item | Change | Why |
|---|---|---|
| `audit_due`, `respond_to_audit` audience | `policy.can_administer_ecosystem` (active, mod+ or a co_creator/builder row there), the same steward as `can_record_audit`; `health.has_independent_member` excludes those rows too (NULL profile counts as plain) | A5/F8: a founder (role `user`, profile `co_creator`) was an "independent" auditor of their own ecosystem and never heard the audit was due |
| `audit_due` held by a draft | only a **live** draft holds it: touched in the last `STALE_DRAFT_DAYS` (30) by an auditor still active there (`health.audit_drafts`); otherwise the item appears and names the stale draft ("ask them to finish it, or abandon it") | F6: one forgotten draft, or one whose auditor left, silenced the reminder for good. 30 days is the smallest rule: a quarter's audit takes days, not a month, and the 14-day notice plus 30 days still lands before the next quarter |
| `respond_to_audit` clears | when the stewards record a response on that audit (`DecisionRecord`, `source_skill` `audit-response`), or a newer audit is published | F7: a same-day answer left the item in every steward's queue for about 90 days. The response may name a proposal; it is stored in `related_records`, never `source_proposal_id`, because `act_gates.record_proposal_decision` treats any record carrying that id as the proposal's own decision |
| `archive_agreement` | `due: null` (the `why` names the end) | F13: a past due with `overdue: false` printed "Due 30 Jul" in November |
| audit item and banner titles | "Governance health of <ecosystem>"; the scope is detail | F14: the bell read "full: Respond to ..." |
| agreement banner `your_moves` | the archive move is `ready: false` with a `blocked` sentence until the sunset has ended; `attest` carries `kind: "consent"` (the consent act, not a status move); `due_label` "Sunset ended" once passed | F5, F2 |
| audit banner `your_moves` | `publish` (its auditor), `abandon` (auditor or steward) on a draft; `respond` (a steward, no response yet) on a published audit; state "Abandoned" with the recorded reason | F6, F7 |

The lifecycle table changed with it (`act_gates.AGREEMENT_LIFECYCLE`): `under_review -> active` asks no
gate (a review ends on its findings; `api/agreements.ends_review` no longer special-cases it), and
`sunset -> archived` asks `sunset_ended`, a gate `agreement_gate_status` computes from `sunset_date`
through `dates.date_passed` (a legacy sunset with no date never blocks: nobody could set one). Abandoned
audits keep their row with status `abandoned` (`health.AUDIT_ABANDONED`); nothing counts or publishes them.

## Member lifecycle (G-Onboard)

`member_lifecycle.py` is the one place a membership row is created or moved, so sign-up, join,
return, `POST /members`, the assistant's `join_ecosystem` / `move_member` and the agreement
consent call sites cannot drift. Owner decisions and the API shapes: api/AGENTS.md "Onboarding
(G-Onboard)". Nothing commits; callers own the transaction.

`place_member(session, *, user_id, ecosystem, display_name, member_key, trigger, public_only)`:

| The user's row there | Outcome | Transition |
|---|---|---|
| none, public ecosystem (or `public_only=False`: the operator's sign-up default) | new row, `pending_consent` when a membership agreement is missing, else `active` (`Placement.created`) | `prospective -> ...`, trigger `signup` / `joined` |
| none, private | 404 "Ecosystem not found" | - |
| `active` | 409 `ALREADY_MEMBER` | - |
| `pending_consent`, agreements missing | 409 `CONSENT_REQUIRED` + `required_agreements` | - |
| `pending_consent`, nothing missing (stuck) | `active` | `gate_cleared` |
| `exited`, latest `ExitRecord.re_entry_eligible` (no record: eligible) | same row, standing cleared (`clear_standing`), back to `pending_consent`, or `active` with no gate | `re_entry` |
| `exited`, not eligible | 403 `RE_ENTRY_CLOSED` | - |
| anything else (`suspended`, `inactive`, ...) | 409 `MEMBERSHIP_PAUSED` (a steward restores it) | - |

Why: the gate is evaluated after the row exists so consent is bound to that membership; the
existing row is read `FOR UPDATE` so two returns or heals serialize; a first insert cannot be
locked, so it runs in a savepoint and a lost race (`uq_member_ecosystem_user`) is a 409 that rolls
back only that insert. A returning member keeps their row and history (framework re-entry E:
same identity, re-consent to the current agreements). No coordinator, timer or decline state (review §7).
FX-Onboard superseded "old consents to an unchanged agreement version still count": see below.

`record_transition(session, member, to, *, trigger, actor, notes)` sets the status (and
`onboarding_status` for pending/active) and adds the one row; an unchanged status writes nothing.
`move_refusal` / `move_member` / `caller_member_moves` apply `policy.MEMBER_MOVES` and
`can_move_member` with the same refusal, so the page's buttons, the route and the assistant's
pre-confirmation check agree.

### Queue items (registry sources in `next_steps.py`, section "G-Onboard")

Kind `newcomer` (queue order 2), record = the member row; each item carries its own `link`:

| Action | Who | Until |
|---|---|---|
| `consent_to_join` (one per missing membership agreement) | the pending member themselves | they consent |
| `finish_joining` | a pending member with nothing left to consent to | they press "Check my membership" (join heals) |
| `confirm_membership` | active stewards of that ecosystem (`can_manage_onboarding`, founders included; FX-Onboard) | a steward confirms (`MEMBER_MOVES`) or the newcomer heals; its words offer both: ask them to press Check my membership on their consent page, or confirm them on their member page (pass 03: it used to say "a steward confirms them" while the page said nobody needs approval) |
| `start_orientation` | an active member in their first 30 days, the ecosystem has an active journey | a `complete` progress row |
| `take_entry_quiz` | the same, the ecosystem has a published entry quiz | `quiz_attempt_complete` on that row: a verified pass when the quiz has answer keys, or a verified completion with `is_passed` null when it does not; listed after `start_orientation` (`_STEP_ORDER`), and while the journey is unfinished its `why` says to take it after the journey |

Waiting newcomers whose consent is still missing are NOT steward items (owner decision: consent
activates them; G-Maint's health snapshot counts them). The 30-day window compares the row's
`created_at` with `scope.clock.now` (a timestamp, not a date-only due date). The pending member's
items honour `scope.wanted`. The earlier REST gap (a newcomer active nowhere got no joining items) is
closed: `api/next_steps.py` passes `reachable_ecosystem_ids(include_pending=True)` and `waiting_for` runs the
sources when there is no active row (coordinator); `test_onboarding_flows.py`
`test_a_newcomer_active_nowhere_gets_their_joining_steps_over_rest` keeps it (F16).

### FX-Onboard: leaving and returning (wave-c fix wave, 2026-11-01)

`end_membership(session, member, *, actor, notes)` is the confirmed exit (`api/exit.py` `_mark_exited`):
`exited` through `record_transition` (trigger `exit_completed`, the confirming steward as actor), then
`clear_standing`. `clear_standing(session, member, *, actor, reason)`: role -> `user` and a co_creator/builder
profile -> none, each a `grant_record` row (`role_grant` / `profile_grant`, "role:<tier>" / "profile:<value>",
the same rows `api/members.py` writes for grants, so the role history and the health tenure read them), and
every live `AgreementMemberConsent` of the row withdrawn (`withdrawn_at`, `withdrawal_reason`, `revision + 1`,
alignment credit reversed by a negative `MemberAlignmentEvent`, as a member's own withdrawal does). The return
branch of `place_member` calls `clear_standing` too, for rows that left before exits cleared them; on a row
already cleared it writes nothing.

Why withdraw rather than have placement ignore consents older than the latest exit: the withdrawal is one
recorded fact at one place, with its date and reason, and every reader agrees without knowing about exits
(the consent gate, `missing_agreement_consents`, `/auth/me` gates, the queue, steward moves, agreement consent
counts, the portable record, which already prints `withdrawn_at`). An "ignore older than" rule would leave
rows that look current on the agreement page while every gate treats them as absent, and each reader would
need the exit date. Re-consenting to the same version reuses the row (`revision` counts the history;
`MemberAlignmentEvent` keeps the ledger).

`re_entry_eligible` has no writer: the column defaults to true and nothing sets it false, so every leaver
may return, which is the honest default (owner default: a leaver returns unless a recorded decision says
otherwise). `RE_ENTRY_CLOSED` is reserved for that decision; a steward route to record it (with a reason) is
not built. Until it is, a return is safe because standing is cleared: the leaver comes back as a pending
member and consents again.

`policy.can_move_member`: confirming a pending newcomer is any steward there (`can_manage_onboarding`,
founders included; it confers nothing and only applies when nothing is left to consent to), suspending and
restoring stay "an active mod+ who outranks them". So the stuck item reaches founders and they can act on it.


## Exchange (G-Exchange)

`exchange.py` is the one implementation of shares, needs and collaborations. REST (`api/discover.py`, the
shares-needs lists of `api/domains.py`, `api/ecosystems.py` and the owner's `own_publications` in
`api/profiles.py`), the queue (`next_steps.py` "# G-Exchange"), the chat tools and MCP all call it. Nothing in it
commits; every write flushes and refreshes its record so any caller can serialize it.

Owner decisions (2026-11-01, `uxqa/governance/wave-c.md`), each with an actor x action row in
`tests/test_exchange_authority.py` that goes red if flipped:

- **Moderation is per ecosystem.** A moderator is `policy.is_exchange_steward(caller_in(post.ecosystem_id), ...)`:
  an ACTIVE row there that is mod+ or holds an admin profile ON THAT ROW. Never `request.ctx.member.profile`,
  never platform-wide: founding an ecosystem makes you its steward there only (the D1 exploit was every founder
  moderating every ecosystem). The same predicate decides "the ecosystem's stewards" in the visibility rule and
  collaboration approval, so there is one meaning of steward in the exchange.
- **Moderators hide, authors delete.** `hide_publication` sets `hidden_at`, `hidden_by_member_id` and a required
  `hidden_reason`; `restore_publication` clears `hidden_at` only, so the last hide's actor and reason stay on the
  row as its trail. Hiding is orthogonal to status: the author's state (open, fulfilled, withdrawn) survives a
  hide and a restore. Hard delete is the author's alone and only while nobody has answered (`HAS_RESPONSES`):
  an answered post is part of someone's conversation history.
- **Nobody moves a post.** `update_publication` refuses a different `ecosystem_id`/`domain_id` (400
  `CANNOT_MOVE`); resending the same values (edit forms resend every field) is fine.
- **Collaborations need a steward of each side.** `policy.can_approve_collaboration`: a steward of that side's
  ecosystem; the proposer counts only for the source side of a cross-ecosystem collaboration (compared by
  `user_id`, so a person who stewards both sides still cannot activate alone), and a same-ecosystem collaboration
  needs a steward who did not propose it. Proposing records `proposed_by_member_id`; when the proposer is a
  steward of the source side (and the sides differ) that side's approval is written at once (owner default).

### One visibility rule

`policy.can_see_publication(viewer, record)` and `exchange.visible_clause(viewer)` say the same thing (the clause
is the predicate in SQL for every list; `load_visible` applies the predicate to one row, 404 otherwise):

| Post | Who sees it |
|---|---|
| any | its author (any of the user's rows) and the stewards of its ecosystem |
| hidden | nobody else |
| `public` | anyone signed in (signed-out visitors see nothing: 401, owner default) |
| `ecosystem` | ACTIVE members of its ecosystem |
| `domain` | the domain's active participants (or its steward) through an active row, plus the stewards above |

`Viewer` (`load_viewer(session, user_id)`) holds the user's rows of every status and the sets the rule reads:
active ecosystems, steward ecosystems, domains. `private` is the retired spelling of `domain` (read as `domain`;
s3e8b1d7c4a2 rewrote the rows; writes accept it as an alias). Discover never lists hidden posts; the domain and
ecosystem lists show them flagged to the author and stewards; the moderation list (`/shares-needs/admin`) is
`steward_ecosystems` only (empty, not 403, for someone who moderates nothing).

### Status table and the 90-day check-in

`PUBLICATION_MOVES` is the author's table: active -> fulfilled | withdrawn | active ("Keep it open"),
fulfilled -> active, withdrawn -> active. Anything else is 409 `MOVE_NOT_ALLOWED` with `allowed`. Every move
records `status_reason` (the note), `status_changed_by_member_id`, `status_changed_at`; `fulfilled` may name
one responder (`fulfilled_by_member_id`, 400 `NOT_A_RESPONDER` otherwise); reopening re-runs the publishing gate
(active membership, domain participation and consent when the domain asks for them). Posts never expire (owner
default): `open_since` is `status_changed_at` while active (a reopen or "Keep it open" restarts it), else
`created_at`; the card's `age_days` and the queue's "Still open?" (`STALE_AFTER_DAYS` = 90, on or after the 90th
day by `QueueScope.clock.today`, G-Maint's date rule) count from it. An exited member's open posts are withdrawn
with reason "author left" (`withdraw_on_exit`, one call in `api/exit._mark_exited`, same transaction).

### Respond

`respond(session, viewer, post, message)` refuses in `respond_blocked` order: `OWN_POST`, `POST_CLOSED` (status
not active, or hidden), `AUTHOR_INACTIVE` (no author row or not active), then `CONSENT_PENDING` /
`MEMBERSHIP_REQUIRED` for a caller active nowhere. It finds the caller's earlier conversation about the post (a
`ConversationLink(entity_type="share_need", entity_id=post.id)` whose `created_by` is one of the user's rows) and
appends the message, else opens a `dm` in the post's ecosystem with two participants: the responder's row (their
active row in the post's ecosystem, else the session's row when active, else their oldest active row) and the
author's row (`author_member_id`, which is the author's row in the post's ecosystem), plus the link and the
message. Unread counting (`api/messaging.py`) excludes only the reader's own rows, so the author sees 1 unread.
Load the post FOR UPDATE first: two answers by one person at once then make one conversation. Messaging lists
answer conversations through ANY active row of the user, whatever the header selection (FX-Exchange F1,
api/AGENTS.md "Messaging scope (FX-Exchange)"), so the poster's bell item, unread badge, list and detail agree; other
conversations still follow the selection. Who answered is derived from the links (`responders`, `response_count`),
so there is no responses table.

### Collaborations

`load_collaboration(..., for_update=True)` locks the collaboration row before an approval or an end, so two
first approvals from one side serialize (the second gets 409 `ALREADY_APPROVED`; before, both inserted and one hit
the unique constraint as a 500) and two sides approving at once end `active`. Approvals whose approver left the
side or lost a required collaboration consent are dropped when the next approval is counted. Activation sets
`started_date` (a creation stamp: `dates.utc_today`) and, when none was proposed, `review_date` = start +
`REVIEW_AFTER_DAYS` (365). Every "is it past?" decision reads the one date rule (FX-Exchange F9): a proposed
`review_date` must not be before `dates.aoe_today()`, and the detail's `review_due` is `dates.date_passed(review_date)`,
the same instant the queue's `clock.past` turns the review item on. `END_OUTCOMES`:
proposed -> dissolved; active -> completed | dissolved; `end_collaboration` needs a reason and records
`ended_by_member_id`, `end_reason`, `ended_at` (a steward of either side; the proposer while proposed).
Proposed collaborations are read by members of either side only (and their proposer); propose refuses a target
in a private ecosystem the caller is outside of (404), the same domain on both sides (`SAME_DOMAIN`) and a linked
post that is closed or invisible (`linked_share_need_id` -> `linked_shares_needs`).

### Archived domains (uxqa pass 03)

`require_active_domain(domain, field, doing)`: a domain whose `status` is not `active` (`archived` in practice)
refuses 409 `DOMAIN_NOT_ACTIVE` (`field`, `status`) for a new post (`publishing_gate`, `doing="post"`), reopening
a post (`"reopen"`) and either side of a new collaboration (`propose_collaboration`, `"collaborate"`), in words
fitted to the act. Editing an open post that is already there (`"edit"`) still passes: the post exists, and its
author may still correct it, withdraw it or mark it fulfilled. Before, the server never looked at the status, and
the post and collaboration forms listed the 12 archived OmniOne domains of neos_uxqa; the client now asks for
`status=active` too, but the rule lives here so the assistant and MCP refuse the same way. The propose check runs
after the target's visibility check, so an invisible target is still a 404, never a status leak.

### Queue items (`next_steps.py` "# G-Exchange", registered with `@item_source`)

| Kind / action | Who | Link |
|---|---|---|
| `share_need` / `read_response` | the author, one per answer conversation with unread messages from others | `/messaging?conversation=<id>` |
| `share_need` / `still_open` | the author, open post 90+ days since `open_since` | `/discover?tab=shares-needs&post=<id>` |
| `collaboration` / `approve_collaboration` | each steward who may approve a side not yet approved (one item per side) | `/discover/collaborations/<id>` |
| `collaboration` / `review_collaboration` | stewards of either side once `review_date` has passed (one item each): "Review or end"; clears when a review moves `review_date` on or the collaboration ends | same |

`read_response` and `approve_collaboration` are `UNBLOCKING_ACTIONS` (someone waits on them), so they rank right
after overdue items, with `OWNER_ACTIONS` ("Next steps" > "Rules of the queue").

Cost: one unread count per answer conversation of the caller's posts; fine at study volume, batch it when a
member has hundreds of answered posts.

### Fix wave (FX-Exchange, wave-c.md "Fix wave")

- **Recording a review (F3).** `review_collaboration(session, viewer, collaboration, sides, note, next_review_date)`
  (load the row FOR UPDATE first): `policy.can_review_collaboration` (a steward of either side, the same steward rule
  as moderation; else 403 `REVIEW_DENIED`), an ACTIVE collaboration only (409 `NOT_ACTIVE`), a required note (400
  `REASON_REQUIRED`, `field: note`), and a next review date that is later than `dates.aoe_today()` (400, `field:
  next_review_date`), default `dates.utc_today()` + 365. It writes `review_date`, `reviewed_by_member_id`,
  `review_note`, `reviewed_at` (the last review, columns added by s3e8b1d7c4a2); the payload adds `caller_can_review`,
  `reviewed_by_name`, `review_note`, `reviewed_at`. Why not an "acknowledge" flag: a review is a governance act both
  sides read, and moving the date is what makes the queue item honest (it reappears at the next review date).
- **Chat lock (A13).** `update_share_need_status` reloads the post with `load_visible(..., for_update=True)` before
  any write, as REST `_write_post` does, so two hides at once cannot both pass `ALREADY_HIDDEN`.
- **Restore records no note (F10).** `restore_publication` takes no reason; the client no longer offers a note field.


## Typed quiz proof and orientation routing

`same_answer_value` treats integers and floats as JSON numbers, with strings and booleans kept distinct. Both choice validation and grading use this boundary. The versioned quiz fingerprint invalidates older grading proofs without demoting existing active participation. Candidate sources and result-owner responses strip answer keys.

Journey route validation belongs in `orientation_content` so member authoring, node support and completion agree on the same declared forward-only graph. A terminal destination is the step count; a missing optional route continues sequentially. Required evidence is checked only on the selected path, and a required choice cannot manufacture a path by omitting or inventing its selection.

## Dev-drive cycle 2: completion, erasure and attempt boundaries

Orientation validation computes the effective saved status before checking proofs; changing journeys starts fresh unless the caller explicitly completes with valid current evidence. Canonical genplan output is derived from saved choices in that same transaction, and the legacy acknowledgement shares the idempotent helper.

Private matching writes and erasure serialize first on the actual User row, then recheck current consent. This persistent lock covers absent-consent creation, answer/assessment/correction writes, scoped/global withdrawal, and retention cleanup; no matching-data path acquires support locks afterward. Retention enumerates candidates without locks, processes one owner per transaction, then rechecks expiration. See api/ORIENTATION_MATCHING.md for privacy semantics and PostgreSQL concurrency evidence.

No-retakes means one server-verified attempt for the current quiz fingerprint, including a genuine failed attempt. Historical or unverified results remain available without blocking the first attempt for revised content. Invalid submissions never create a verified attempt. Exact owner-result responses supply current-version eligibility so the UI can distinguish a current retake from a first attempt on revised content.

## Notification support privacy
The engagement tables are explicitly internal to the generic NodeAdmin resource catalog. They carry personal follows, contact destinations, verification proofs, push capabilities and delivery manifests. Generic support repair must not forge channel consent, verification or delivery receipts, or copy these values into public audit payloads. Existing account/session revocation remains available for support; dedicated owner-scoped notification APIs enforce enrollment and withdrawal.
