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
minutes old (`AgentSession.context["pending_confirmations"]`), and only when
the member's current message is an explicit affirmative response. The UI's
"Yes, go ahead", plain "yes", and concise "Yes, withdraw it" / "Yes, co-sign
it" forms qualify; a verb-qualified yes must match that tool and action
("Yes, send it" cannot authorize withdrawing a proposal). Uncertain or
unrelated wording supplies no keys. A
decline ("No, cancel", "do not ...", "never mind") clears the pending keys
and cannot re-arm them in that turn, even if the model tries again. Keys asked in
the current request only count from the next one, so the model can never
confirm on the member's behalf, neither straight away nor in the same turn
that asked. Each stored key also binds the canonical tool name and a SHA-256
digest and frozen JSON payload of every action argument except `confirmed`
(at most 64 KiB of UTF-8 JSON, allowing a legal 10,000-character message). A single matching affirmative executes that exact payload
under the session row lock, with the same handler, current scope and current
authority. It does not ask a model to regenerate a target or reason. The
handler checks its newly resolved confirmation key, so a reused title or
changed party resolution cannot redirect approval. Consumption and ordinary
member writes share the transaction. Support consumes approval durably
before invoking its separately transacted audited service, so a later
session-save failure cannot replay a committed support command; a failed
attempt needs a fresh request. Support also reauthorizes inside that service.
The receipt reports the actual outcome and record link.
Changed message text, target, reason or outcome requires a new question.
Legacy entries without a valid payload are re-asked. A generic affirmative
authorizes only one pending action, never a set. If several are pending,
re-asking one replaces the pending set so the next affirmative is unambiguous.
A frozen confirmation is consumed once, including when fresh checks refuse
the action. A replay with no pending action returns a deterministic message
and cannot arm another model-selected action.
Consumption increments a monotonic `confirmation_epoch` under the session
lock. Every session save locks again and compares its request's snapshot
epoch with the live one. A stale unrelated response cannot restore inherited
pending actions; only new questions explicitly asked by that response can
be saved after an epoch change. The epoch itself is never overwritten by a
stale snapshot.
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

The assistant is the signed-in member's personal governance operator: it
executes a clear permitted request through tools, asks for missing details
or a required confirmation, and reports the result. It never chooses the
member's position or makes a decision for the group. Recording the member's
explicit consent or approval is different from inventing that choice.

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

## Domain lookup

`_find_domain` resolves a scoped UUID, then an exact business key, exact
name, legacy display label, partial name, and finally purpose/key text.
Name matches take precedence over incidental mentions in another group's
purpose. Every tier must identify exactly one domain; multiple matches
return `AMBIGUOUS_DOMAIN` with scoped names, ecosystems and record links.
The assistant asks which group the member meant and uses its UUID next.
This is shared by reads, joining, posting and parent-domain choices, so an
ambiguous query never joins or publishes to whichever row happens to be
oldest. Regression coverage: `tests/test_operator_domain_resolution.py`.

The prompt requires a fresh lookup before describing a record's current
state, gates, steward or available actions; the question or page label is
not evidence of live governance state.

## Router

Each request first calls `skill_decision.select_skill` with the new prompt,
bounded recent context, page type and skill metadata. `active_skill` is only
a prior-context hint; an explicit `requested_skill` is a validated manual
selection. Typed decisions can choose a skill or direct platform/framework
context. Failure falls back to general guidance and clears the prior skill.
Routing changes context, never caller authority or confirmation rules.
Transport and selection policy: `ai/AGENTS.md` and `DECISIONS.md`.

`router.py` only routes moves the lifecycle tables have; the old
`consent -> active` agreement pattern was dead (every agreement passes
through test). `tests/test_router.py` checks every agreement pattern against
`AGREEMENT_LIFECYCLE`.

`match_transition` returns the matched pattern, so a terminal destination
of `None` clears the active skill instead of looking like no match. The
older `detect_transition` method retains its destination-only contract for
internal callers. Chat emits `skill_route` on selection and each transition,
including the null skill, and saves the resulting skill in the session.

## Runtime guidance and bounded lookup

Prompt assembly places current application policy after skill/dependency
prose. The ACT guide is generated from `PROPOSAL_LIFECYCLE`; stale skill
descriptions cannot establish automatic advice closure or override tool
gates. Direct platform/framework modes explain the relevant facts without
loading a process skill. A fresh record lookup is required for live claims;
current state does not establish who changed it or why.

The canonical `act-advice-phase` skill and its advice-log asset also describe
explicit closure, continued advice while overdue, and a deadline as a
reminder. The consent skill's entry condition names the same authorized
transition. A final prompt override alone did not prevent the model from
repeating the former hard-cutoff instruction in pass 04; keep source and
runtime policy aligned. Real-registry prompt coverage checks both layers.

Platform help uses a bounded navigation map verified against
`client/src/App.tsx`, `components/AppSidebar.tsx`, `pages/me/MePage.tsx` and
`pages/Profile.tsx` in `charting-the-course`. Profile editing is sidebar
`Me` (`/me`) -> `Profile` -> `Display name` -> `Save profile`; no preliminary
edit control exists. Answers link to known routes and acknowledge unknown
controls rather than inventing a generic avatar-menu path. Update this map
when the client changes; it describes navigation, not access grants.

The final policy prioritizes short, plain answers, explicit ecosystem choice
before other creation details, all exit facts (voluntary/no penalty,
wind-down, steward confirmation and portable records), and no invented
dates, schedules or commitments in drafts. Creating a proposal returns its
actual change and rationale so the draft can be reviewed. A clear request
to create and open a draft remains possible through the existing tools.

Chat withholds model narration accompanying tool calls from the visible
answer and saved text history. Those calls can claim a state before the
lookup establishes it. Only the resulting final prose is presented; tool
status remains visible through its own events.

Failed/empty lookups are tracked by exact tool/argument signature per turn.
A repeated unresolved call, or an additional lookup after three unresolved
attempts, ends the search with scope/access clarification. Reads that find
a record remain repeatable, and the guard never reveals whether a hidden record
exists or grants a write. Real SSE regression coverage lives in
`tests/test_operator_routing.py`.

## Session record context and support mode

`known_records` retains at most 20 typed record references (kind, UUID, label,
local link) from successful scoped tool outputs or the scoped domain
ambiguity result. It excludes nested member content and client history.
Each reference is re-read with current caller scope before reuse; this is
navigation context, never cached permission. Follow-up choices keep their
domain kind instead of being mistaken for ecosystem names.

Proposal read/explain tools include lifecycle-derived automatic-transition
facts and explicitly state that transition history was not returned. A met
advice gate or current Consent state establishes neither an actor nor a
cause. The runtime instruction names this distinction; live QA must still
check the final answer rather than treating prompt text as proof.

Explicit support mode requires freshly verified NodeAdmin assignment and
`{enabled: true, organization_id, reason}` on each request. Its normalized
organization/reason binds the conversation; changing mode starts a new one.
Only `node_support_*` tools are exposed there, with every command using the
same frozen confirmation contract. Each call rechecks the role and audits
the actual actor with source `agent` and the chat session UUID. Core member
tools remain separate and cannot impersonate another member. Support
transcripts are owner-only: privacy changes cannot share them, and the
shared endpoint refuses them even if an old share token exists.
Support session ownership uses the actual User (`owner_user_id`) without
requiring or creating a Member. Memberless NodeAdmins can use explicit
support and their own session history; member mode still requires a real
membership. Core member-session history retains its existing ecosystem
scope. The chat's guard and every support tool check the current assignment,
and support auditing always attributes the actual User.

## Personal operator workflows

`operator_tools.py` adds ordinary member capabilities to the same registry,
caller-aware/scoped dispatch and frozen confirmation allowlist. These tools
never borrow NodeAdmin authority. Shared request-free functions in messaging,
exchange, safeguards, exit and conflicts perform the REST validation and
mutation; no tool constructs an HTTP request or calls a route handler.

| Family | Reads | Acts and confirmation |
|---|---|---|
| Messaging | `list_conversations`, `get_conversation`, `search_messages`, `find_message_members` | `create_conversation` (optional first message), `send_message`; both frozen and confirmed |
| Collaboration | `find_collaboration_domains`, `find_collaborations`, `get_collaboration` | `propose_collaboration`; confirmed, actual proposer, only the canonical eligible source-side approval |
| Health audit | `get_health_audit`, existing computed health | `update_health_audit` saves only the auditor's supplied draft fields; `publish_health_audit` and `abandon_health_audit` require confirmation |
| Exit | existing `get_exit_status`, `export_portable_record` | `update_exit_status` is confirmed; only the leaver cancels, a different actual steward starts/completes handoff |
| Conflict/repair | existing `get_conflict_case` | `update_conflict_case`, `update_repair_agreement`; confirmed, same visibility, actor, field and move validation as REST |

Messaging recipients come from active memberships in the caller's active
ecosystems. Namesakes remain separate choices. The creator/sender always
comes from current participation, never an argument. Conversation reads
mark only served messages read; cached navigation refresh checks access
without advancing the read watermark. The confirmation key binds recipient
membership/User identities and current names, so an edited recipient or
participant list requires a new question. Broadcasts are queued in the
session and delivered only after commit; a refusal cannot emit a message.

Audit publication prepares a read-only plan using the actual period,
computed values, previous values/trends, and the auditor's own ratings.
Its confirmation key hashes that plan plus findings/scope/recommendations;
changed content, computed evidence, or lost independence invalidates old
approval. Publication never invents the member's ratings. Abandonment uses
the same recorded reason and decision record as REST.

Exit is voluntary and penalty-free. Handoff dates are maximum practical
wind-down periods, not a permission or minimum waiting gate. The export
tool returns the actual own-only authenticated download URL and says it has
not downloaded anything; it does not transmit the private export body to
the model or mark completion. Opening the actual export endpoint performs
the existing owner check and records the download.

Conflict moves require the same summary and non-party facilitator/steward
rules. A reporter retains their limited text-correction/withdrawal rights.
Repair fulfillment requires the facilitator's explicit report that both
parties confirmed; a generic chat Yes approves only the already frozen
payload, never invents that fact. Undeclared repair status spellings cannot
bypass the fulfilled check. Tools flush; the dispatcher commits their
ordinary writes atomically with one-use approval consumption.

Proposal reads carry short `plain_help` derived from current stage, caller
standing and consent/consensus mode. It is a wording aid for brief answers,
not a new lifecycle rule. The prompt gives short advice, concern/objection
and voluntary-exit wording; actual model P1/P2/P3 scores remain live QA work.
Coverage: `tests/test_personal_operator_workflows.py`; the separate guarded
real-model probe and fixture plan are in `uxqa/agent-evals/operator-capability-*`.


## Explicit reasons are already input

A clear own-position request plus an identified proposal and a concrete stated reason is enough to call `record_consent_position`; the engine checks current participation/stage. An unfair shift burden is a stated reason, without requiring the member to restate it in formal governance language. Missing reasons/targets still require clarification, and a question or vague concern does not become an automatic consent/objection. No semantic authorization parser was added. Real-model follow-through must still be verified; mocked SSE tests establish execution, scope and no-extra-confirmation behavior only.


Proposal status tools also supply `status_explanation`, derived from the lifecycle's manual Advice exit, fresh caller standing and ready moves. It distinguishes a read with no transition history from a claim that no history is stored. Consent help identifies the caller's actual position and available options, with return-to-Advice note requirements and proposal withdrawal kept distinct from withdrawing an own position. Explaining an unexpected transition does not execute one. R4 live follow-through remains a real-model verification requirement.


## Live plain language and factual drafting follow-through

The full live retry showed that long sentences and formal vocabulary persisted despite the previous 80-word suggestion. The final policy now models short everyday wording for consent, advice and standing aside, with roughly 40 to 60 words for a simple question and sentences of 5 to 10 words. It avoids repeated titles, machine labels and closing check-in questions. These are general answer patterns, not task-ID branches; live grade thresholds remain unchanged and must still be verified.

The proposal tool no longer demands 2-to-6 sentences of change and rationale from a brief user request. It asks for the supplied change/reason and omits guessed staffing, benefits and optional control fields. Chat's separate source guard can refuse unsupported wording before a write and allow an exact correction immediately. Explicit requested ideas remain draft material for review. The history limit is stated positively: the read looked only at current state and did not inspect change history. The suggested bounded wording is that this read cannot establish who moved the record or why; it is not a claim about what history is stored.

## Phase-qualified skill use

The selected proposal skill now distinguishes the current app draft adapter from formal readiness and later ratification guidance. Draft minimums are the title, stated change and server-scoped actor/ecosystem; an absent reason gets the transparent placeholder and an unchosen domain is omitted. The existing framework readiness fields and process remain intact. A requested create-and-open flow uses the real returned draft ID and existing lifecycle checks; it does not certify readiness or invent facts. Dependency checklists apply only to the requested work, so the domain-mapping dependency cannot turn an ordinary proposal draft into domain creation.

A personal operator completes each explicit read as well as a requested write. Finding collaboration target groups and finding existing collaborations are distinct reads. A write's authorization preflight or returned updated record does not excuse silently omitting a requested search/read. Refusals still give the caller an available next action grounded in fresh tool facts; chat's bounded canonical summary completes omitted current proposal facts without executing them.

Conflict update tool arguments derive their changes schema from the shared `ConflictUpdateRequest`, so the model sees actual field names rather than an unconstrained object. A requested resolution prepares both `status=resolved` and `resolution_summary`; editing the summary alone leaves the stage unchanged. Verb-qualified confirmation remains bound to the actual frozen status, with no inferred field addition. Personal operator anonymous refusals use the existing `CALLER_REQUIRED` constant, keeping the common caller boundary and error contract consistent.

`create_conversation` advertises a required explicit initial-message choice in its model-facing schema. A create-and-send request includes the member's exact text in the first frozen payload; a deliberately empty string means conversation only. Chat refuses a missing choice before preparing confirmation, allowing correction within the same tool loop rather than asking the member again. This adapter does not change ordinary REST/direct-call compatibility or permit a later Yes to add a message to a conversation-only review.
