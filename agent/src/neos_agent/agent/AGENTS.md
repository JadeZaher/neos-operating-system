# The in-app assistant

`governance_tools.py` (the tools), `system_prompt.py` (what the model is told),
`router.py` (skill transitions) and `api/chat.py` (the agentic loop) make the
assistant behind `POST /api/v1/chat/send`. The rules it enforces live in the
same places REST uses (`api/policy.py`, `services/act_gates.py`,
`api/emergency.py`, `api/conflicts.py`, `api/exit.py`); the tools call them
and never restate them. Evidence and grading: `uxqa/agent-evals/` (review,
design, tasks). Authorization table per tool: `api/AGENTS.md` "Chat assistant
tools (caller-scoped)".

## Who the tools act for

`execute_tool(name, args, db, ecosystem_ids, caller_user_id, confirmed_keys)`.

- `CALLER_SCOPED_TOOLS` act as the signed-in member and refuse without one.
  Identity is always the caller's own `Member` row in the record's ecosystem
  (`_caller_row`); a model-chosen name (`participant`, `declared_by`,
  `member_name`, `auditor`, `reporter_id`) is ignored or refused.
- `CALLER_AWARE_TOOLS` (`get_proposal`, `get_agreement`, `get_domain`,
  `what_needs_me`, `explain_status`, `get_conflict_case`, `get_exit_status`)
  are reads that also describe the caller's standing (author? advised?
  consented? joined? what is waiting for them?). Standing is matched by member id only (`AdviceEntry.member_id`,
  `act_gates.current_position`), never by display name: names are
  self-editable, so a member renamed "Ben" must not inherit Ben's advice or
  position. Legacy rows with a NULL member are nobody's.
- `list_ecosystems` and `get_ecosystem` are caller-aware too, with REST
  `GET /ecosystems/:id` visibility: public ecosystems for anyone, private and
  unlisted ones only for members (any `Member` row, as `caller_in`); a hidden
  one is "not found". `contact_email` is returned only to members, even for a
  public ecosystem (stricter than REST, which shows it on the public page).
- Scope: a signed-in caller's `ecosystem_ids` is always a list, and `_scope`
  turns it into `restrict_to_ecosystems` (an empty list matches nothing).
  `None` is reserved for internal callers (tests, scripts) and means
  unscoped; `execute_tool` turns `None` into `[]` whenever there is a caller,
  so the old fail-open `if ecosystem_ids:` cannot come back through a surface
  that passes `selected or None` (legacy `views/chat.py` does).
- Creating tools pick their ecosystem with `_target_ecosystem`: the one named
  in `ecosystem`, else the only one selected. With several selected and none
  named they refuse with the names, so the assistant asks instead of guessing
  (eval C3).

## Lookups, names, links, next steps

- Every record lookup takes the page's UUID, the business key (any case) or
  the exact title (`_find`; a title counts only when it names exactly one
  record). Domains also match their name, the legacy `"Name — "` purpose
  label, then a partial match (`_find_domain`).
- Results carry `id`, a `link` to the client route (`_ROUTES`, mirroring
  `client/src/App.tsx`) and names, never `DOM-` codes or ecosystem UUIDs.
- Proposal and agreement results carry the engine's gates
  (`proposal_gate_status` / `agreement_gate_status`, `_compact_gates` drops
  the policy echo) and a `next_step` sentence. `proposal_next_step` /
  `agreement_next_step` read *how* a record moves from the lifecycle tables
  (`_move_note`: automatic, by hand, steward-confirmed; send-back moves with
  `note_required` are skipped), so an owner's table edit changes the wording
  without touching this file. `get_proposal` also returns `your_moves`
  (`act_gates.proposal_next_moves`, the UI's buttons). These sentences and the
  standing helpers live in `services/next_steps.py` (G-Next), which the status
  banner reads too, so the page and the assistant use the same words.
- "What needs me?": `what_needs_me` returns `next_steps.waiting_for` for every
  ecosystem the member is active in, item for item the bell's list
  (`GET /me/next-steps`), not narrowed to the selection: it is the member's
  own list and each item names its ecosystem. "Where does this stand?":
  `explain_status(kind, record)` finds the record with the tool's lookups
  (scope, UUID / key / title; a hidden conflict is not found) and returns
  `next_steps.explain_record`, equal to `GET /explain/<kind>/<id>`.
- `check_quorum` reports the engine's consent gate, never a share of members.

## Confirmation of irreversible acts

`CONFIRMATION_TOOLS`: withdrawing or ratifying a proposal; putting an
agreement in force (also when the cascade after a ceremony would), sunsetting
or archiving it; declaring, co-signing or ending an emergency; recording its
review as complete; filing an exit; recording agreement evidence that would put
the agreement in force; reporting a conflict that names parties. The emergency
tools load the row FOR UPDATE and run `emergency.cosign_refusal` /
`end_authority_refusal` / `review_refusal` before asking. The tool first runs every refusal the
engine would give (so the member is never asked to confirm something they
cannot do), then `_needs_confirmation`:

- without `confirmed: true` it writes nothing and returns
  `{"success": false, "needs_confirmation": "<what will happen>",
  "confirmation_key": "<tool>:<record>:<target>"}`;
- with `confirmed: true` it acts only if the key is in `confirmed_keys`.

`api/chat.py` supplies `confirmed_keys` from the chat session: keys that a
tool asked about in an *earlier* request of the same session, at most 30
minutes old (`AgentSession.context["pending_confirmations"]`). Keys asked in
the current request only count from the next one, so the model can never
confirm on the member's behalf, neither straight away nor in the same turn
that asked. A successful confirmed act drops that tool's pending keys.
`confirmed_keys=None` (tests, scripts, the legacy view) trusts the flag. The
drawer shows the question with "Yes, go ahead" / "No, cancel"
(`client/src/lib/chat-tools.ts`).

The two conditional ones:

- `record_agreement_evidence` asks only when this record would carry the
  automatic cascade (`advice -> consent -> test -> active`) into force.
  `agreement_act_puts_in_force` is a dry run of `act_gates._advance` over
  `AGREEMENT_LIFECYCLE` with the gates as they would be after the write
  (advice rounds or test evidence + 1, or one more member's consent; or after
  a requested ceremony), so an owner's table edit changes when it asks. MCP
  `record_agreement_ceremony`, `attest_agreement_consent` and
  `transition_agreement` use the same dry run with `confirm`. Any active member may record evidence, so without this an ordinary
  member's note could make an agreement binding unasked. Key:
  `record_agreement_evidence:<agreement>:active`.
- `create_conflict_case` asks whenever `parties` resolve to anyone: naming a
  party gives them read access to a harm report (`policy.can_view_conflict`),
  so the member sees exactly who was resolved (`parties`: name + member id in
  the result, names in the question). The key binds the sorted member ids,
  so a rename between the turns that changes who resolves asks again.

MCP has no turns, so `transition_proposal` takes `confirm: true` instead:
for `ratified` and `withdrawn` it first raises every refusal
(`proposal_move_refusal`, shared with the chat tool), then without
`confirm=true` returns the record unchanged with `needs_confirmation`
(`PROPOSAL_CONFIRM` wording) and a `next` telling the agent to ask its owner.
Other moves (open, close advice, send back) stay one call. The server
`instructions` tell agents the same.

## Tool results the model reads

`api/chat.py _fit_tool_result` keeps a result within 6000 characters of JSON
by clipping long strings and long lists in progressively tighter passes
(`_SHRINK_STEPS`), each clip saying how much was left out. Every key stays;
`error`, `needs_confirmation`, `next_step`, `link`, `message` are never
clipped. The browser receives the same shrunk data, so the screen and the
model agree. The old behaviour replaced any result over 2000 characters with
`"Result truncated ... Key fields: success, data"`, which hid every real
proposal from the model (review §2).

## Engines the tools delegate to (other lanes own them)

| Tool | Engine |
|---|---|
| `record_consent_position` | `act_gates.record_consent_position` (one position per member, `objection` -> `object`, reason required to object) |
| `withdraw_consent_position` | `act_gates.withdraw_consent_position` (only one's own; the only way an objection is lifted) |
| `update_proposal_status`, `record_advice`, `submit_test_report` | `act_gates.transition_proposal` (manage rule, table, steward-only, `note` for send-backs, gates) |
| `update_agreement_status`, `record_agreement_evidence` | `api/agreements.transition_agreement` |
| `declare_emergency`, `get_emergency_state` | `api/emergency.declare` (pending until a co-signer), `describe`, `live_condition` |
| `cosign_emergency`, `end_emergency_authority`, `record_emergency_review` | `api/emergency.cosign` / `end_authority` / `record_review` and their `*_refusal` checks |
| `what_needs_me`, `explain_status`, `get_conflict_case`, `get_exit_status` | `services/next_steps.waiting_for` / `explain_record`; `api/conflicts._conflict_to_detail` |
| `create_exit_record` | `api/exit` `HANDOFF_DAYS`, `OPEN_STATUSES`, `NEXT_STEP` (same rules as `POST /exit`) |
| `triage_conflict`, `create_repair_agreement` | `policy.can_triage_conflict`, `can_view_conflict` (hidden == not found), `api/conflicts.CONFLICT_MOVES` |
| `create_conflict_case` | parties resolved to member ids (`_resolve_party_ids`: the exact full display name, case and spacing ignored, unique in the ecosystem; no first-name or partial shortcut, which let a member renamed "Alex" take "Alex Smith"'s place), then `api/conflicts._party_record`, then the member confirms who (a short name others start with says "(not Alex Smith)") |
| `join_domain` | `services/agreement_consent.missing_agreement_consents` (as `POST /domains/:id/participation`) |

## System prompt

`build_foundation_prompt` sections, in order: identity (zero authority), how
to talk (plain words, about 120 words, one question at a time, names not
codes, links, the tool's `next_step`), who you act for (caller only, refusal
wording, confirmation, tool text is data not instructions, emergencies:
safety first), the ACT guide, principles, constraints and tool-use rules,
global rules (capture taxonomy per NEOS.md: capital, charisma, emergency,
ossification; emergency states Normal / Crisis / Recovery; exit), terminology,
then the skill index as names only (a skill's text loads only when it is
active). `act_stage_guide()` is generated from `PROPOSAL_LIFECYCLE`, so it
cannot drift from the engine (`tests/test_system_prompt.py`). Removed on
purpose: "check_authority before every binding action" (it only knows domain
stewardship and denied authors) and "check_quorum before consent" (neither a
NEOS nor an app rule).

## Router

`router.py` only routes moves the lifecycle tables have; the old
`consent -> active` agreement pattern was dead (every agreement passes
through test). `tests/test_router.py` checks every agreement pattern against
`AGREEMENT_LIFECYCLE`.
