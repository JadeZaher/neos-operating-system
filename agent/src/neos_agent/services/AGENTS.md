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
of `Move(source, target, gate=None, automatic=False, steward_only=False)`.
They stay separate because agreements continue past activation (review,
sunset, archive) and have no withdraw; proposals end at ratified or withdrawn.

| Record | Move | Gate | Automatic | By hand |
|---|---|---|---|---|
| proposal | draft -> advice | - | no | manage rule |
| proposal | advice -> consent | advice | yes | manage rule |
| proposal | consent -> test | consent | yes | manage rule |
| proposal | test -> ratified | test | yes | manage rule |
| proposal | any -> withdrawn | - | no | manage rule |
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
`created` is a legacy alias of `draft` (old chat drafts). Withdrawing is
allowed from any status, as the REST rule always was.

Owner decisions recorded in the table comments, not live yet (each is a
one-line edit, proven by `tests/test_act_lifecycle.py::test_owner_decisions_are_table_edits`):

- Advice closes on the proposer's call: drop `automatic=True` on
  advice -> consent. The advice-deadline backstop needs a timer (later wave).
- A steward confirms ratification: test -> ratified becomes
  `steward_only=True` without `automatic`.

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

The engine never commits; callers own the transaction.
