# Specification: Claude Agent SDK Integration & Chat

**Track ID:** agent_core_20260305
**Track Type:** Feature
**Created:** 2026-03-05
**Depends on:** agent_foundation_20260305 (Sanic app, SQLAlchemy models, skill registry)
**Priority:** P0

---

## Overview

Build the Claude Agent SDK integration layer that transforms the 54-skill NEOS governance stack into an interactive AI governance agent. This track delivers: 14 governance tool definitions registered as an MCP server, a dynamic 3-layer system prompt assembly pipeline, multi-turn conversation management with session persistence, Datastar SSE chat streaming, and a skill transition router that detects when one governance process triggers another.

The agent is a process facilitator with zero governance authority. It helps participants navigate agreements, proposals, consent rounds, resource requests, and conflict resolution by loading the relevant SKILL.md at the right time, presenting the correct process steps, and recording outcomes through structured tool calls. The agent never makes governance decisions -- it structures and records them.

---

## Background

The NEOS governance skill stack (54 skills across 10 layers in `neos-core/`) is complete and validated. Each skill follows a standardized 12-section structure (A through L) with YAML frontmatter, step-by-step processes, authority boundary checks, capture resistance checks, and failure containment logic.

The `agent_foundation_20260305` track provides:
- Sanic web application with Datastar SSE integration
- SQLAlchemy models for: agreements, proposals, members, roles, domains, decision_records, agent_sessions
- Skill registry that indexes all 54 SKILL.md files with metadata (name, description, layer, depends_on)
- Base route structure and static asset serving

This track builds on that foundation to create the conversational AI layer.

---

## Functional Requirements

### FR-1: Governance Tools (14 MCP Tools)

Define 14 tools using the `@tool` decorator from `claude-agent-sdk`, registered as an MCP server via `create_sdk_mcp_server()`. Each tool interacts with SQLAlchemy models from agent_foundation and returns structured text that Claude can interpret and present to users.

**Tool naming convention:** lowercase snake_case, prefixed by category when useful for clarity.

#### Registry Query Tools

**FR-1.1: `search_agreements`**
- Description: "Search agreements by type, domain, status, affected party, or date range"
- Parameters:
  - `type` (str, optional): agreement type -- space, access, organizational, ecosystem, uaf, stewardship, culture_code, personal_commitment
  - `domain` (str, optional): domain name or partial match
  - `status` (str, optional): draft, advice, consent, test, active, under_review, sunset
  - `affected_party` (str, optional): member name or ID
  - `date_range` (str, optional): ISO date range "YYYY-MM-DD/YYYY-MM-DD"
- Returns: list of matching agreements with ID, title, type, status, domain, created_date
- Acceptance criteria:
  - Supports any combination of filters (logical AND)
  - Returns max 20 results, ordered by relevance (status=active first, then recency)
  - Empty result set returns a helpful message ("No agreements found matching...")
  - Partial domain matches work (searching "kitchen" finds "SHUR Bali kitchen")

**FR-1.2: `get_agreement`**
- Description: "Get full details of an agreement by its ID"
- Parameters:
  - `agreement_id` (str, required): unique agreement identifier
- Returns: complete agreement record -- ID, type, title, full text, version, status, proposer, affected_parties, domain, created_date, ratification_date, review_date, hierarchy_position, ratification_record
- Acceptance criteria:
  - Returns all fields from the agreement model
  - Returns clear error if agreement_id does not exist
  - Includes the ratification record with individual positions when available

#### Agreement Lifecycle Tools

**FR-1.3: `create_agreement_draft`**
- Description: "Create a new agreement draft with type, title, proposer, domain, text, and affected parties"
- Parameters:
  - `type` (str, required): agreement type (one of the 7 types from FR-1.1)
  - `title` (str, required): agreement title
  - `proposer` (str, required): proposer name or member ID
  - `domain` (str, required): domain scope
  - `text` (str, required): the agreement text body
  - `affected_parties` (list[str], required): names or IDs of all affected parties
  - `review_date` (str, optional): ISO date for scheduled review (defaults per type: space=1yr, access=6mo, organizational=2yr, uaf=1yr, culture_code=1yr)
  - `rationale` (str, optional): why this agreement is needed
- Returns: new agreement record with generated ID and status="draft"
- Acceptance criteria:
  - Generates agreement ID in format AGR-{DOMAIN_PREFIX}-{YEAR}-{SEQ}
  - Sets status to "draft" and version to "0.1"
  - Validates that proposer exists as an active member
  - Validates that all affected_parties exist as active members
  - Stores the rationale in the agreement metadata
  - Creates a corresponding decision_record entry

**FR-1.4: `update_agreement_status`**
- Description: "Transition an agreement's status through its lifecycle"
- Parameters:
  - `agreement_id` (str, required): the agreement to update
  - `new_status` (str, required): target status
  - `reason` (str, optional): explanation for the transition
  - `metadata` (dict, optional): additional context (e.g., consent_record_id for consent->test transition)
- Returns: updated agreement with old_status, new_status, transition timestamp
- Acceptance criteria:
  - Enforces valid transitions only: draft->advice, advice->consent, consent->test, consent->active (when test skipped by consent), test->active, active->under_review, under_review->sunset, under_review->active (re-ratified)
  - Rejects invalid transitions with clear error message
  - Records the transition in decision_records
  - Increments version on content-modifying transitions

#### Authority Check Tools

**FR-1.5: `check_authority`**
- Description: "Verify whether a member has authority for a specific action within a domain"
- Parameters:
  - `member` (str, required): member name or ID
  - `action` (str, required): the action being checked (e.g., "propose_agreement", "facilitate_consent", "allocate_resources")
  - `domain` (str, required): the domain within which the action would occur
- Returns: authorized (bool), reason (str), role_source (str -- the role assignment granting or denying authority), domain_contract (str -- relevant domain contract reference)
- Acceptance criteria:
  - Checks the member's active role assignments against the domain contract
  - Returns false with explanation when no matching role exists
  - Distinguishes between "no role in this domain" and "role exists but action not in scope"
  - Facilitator authority is process-only -- cannot approve/reject content

**FR-1.6: `get_member_roles`**
- Description: "Get all active role assignments for a member"
- Parameters:
  - `member` (str, required): member name or ID
- Returns: list of role assignments -- role_name, domain, scope, assigned_date, review_date, status
- Acceptance criteria:
  - Returns only active (non-sunset) roles
  - Includes the domain scope for each role
  - Returns empty list with helpful message if member has no active roles

#### ACT Process Tools

**FR-1.7: `create_proposal`**
- Description: "Create a new ACT proposal with type, title, rationale, and proposed change"
- Parameters:
  - `type` (str, required): proposal type -- new_agreement, amendment, resource_allocation, role_change, structural_change
  - `title` (str, required): proposal title
  - `proposer` (str, required): proposer name or ID
  - `rationale` (str, required): why this proposal is needed
  - `proposed_change` (str, required): what the proposal would change
  - `affected_domains` (list[str], optional): domains impacted
  - `urgency` (str, optional): normal (default), elevated, emergency
  - `consent_mode` (str, optional): consent (default) or consensus
- Returns: proposal record with generated ID, status="created"
- Acceptance criteria:
  - Generates proposal ID in format PROP-{YEAR}-{SEQ}
  - Sets consent_mode based on scope when not explicitly provided (OSC/UAF = consensus, else consent)
  - Creates a decision_record entry
  - Validates proposer exists and is active

**FR-1.8: `record_advice`**
- Description: "Record an advice entry during the ACT advice phase"
- Parameters:
  - `proposal_id` (str, required): the proposal being advised on
  - `advisor` (str, required): the person giving advice
  - `advice_text` (str, required): the advice content
  - `integration_response` (str, optional): proposer's response to this advice (accept, partially_integrate, note_without_change)
- Returns: advice entry record with timestamp
- Acceptance criteria:
  - Validates proposal exists and is in advice phase
  - Validates advisor is in the affected parties or has standing to advise
  - Timestamps the entry
  - Records the proposer's integration response when provided

**FR-1.9: `record_consent_position`**
- Description: "Record a participant's position in a consent round"
- Parameters:
  - `proposal_id` (str, required): the proposal in consent phase
  - `participant` (str, required): the person stating their position
  - `position` (str, required): consent, stand_aside, or objection
  - `reason` (str, required when position is stand_aside or objection): stated reason
  - `round_number` (int, optional): consent round number (defaults to current round)
- Returns: consent position record with timestamp
- Acceptance criteria:
  - Validates proposal exists and is in consent phase
  - Validates participant is in the deciding body
  - Rejects stand_aside in consensus mode (consensus requires active agreement from all)
  - Requires reason for stand_aside and objection positions
  - Records against the correct round number
  - Does not allow overwriting a position in the same round (new round required for changes)

**FR-1.10: `check_quorum`**
- Description: "Check whether quorum is met for a consent or consensus round"
- Parameters:
  - `proposal_id` (str, required): the proposal to check
  - `present_members` (list[str], optional): members present (if not provided, uses recorded positions for current round)
- Returns: quorum_met (bool), required_threshold (str), present_count (int), required_count (int), total_deciding_body (int), consent_mode (str)
- Acceptance criteria:
  - Consent mode: 2/3 of deciding body must be present
  - Consensus mode: ALL members must be present
  - Emergency consent: 50% minimum
  - Returns detailed breakdown for transparency

#### Decision Record and Lookup Tools

**FR-1.11: `create_decision_record`**
- Description: "Create a universal decision record wrapping any governance artifact"
- Parameters:
  - `skill` (str, required): the NEOS skill that produced this decision (e.g., "agreement-creation", "act-consent-phase")
  - `artifact_type` (str, required): type of artifact (agreement, proposal, consent_record, advice_log, role_assignment, domain_contract)
  - `artifact_id` (str, required): ID of the artifact being recorded
  - `summary` (str, required): human-readable summary of what was decided
  - `domain` (str, required): domain context
  - `participants` (list[str], required): who was involved
  - `tags` (list[str], optional): semantic tags for searchability
- Returns: decision record with generated ID and timestamp
- Acceptance criteria:
  - Generates decision record ID in format DR-{YEAR}-{SEQ}
  - Links to the source artifact by ID
  - Stores tags for precedent search
  - Automatically tags with layer and skill name

**FR-1.12: `search_precedents`**
- Description: "Search decision records for precedent by skill, domain, tags, or text"
- Parameters:
  - `skill` (str, optional): filter by originating skill
  - `domain` (str, optional): filter by domain
  - `tags` (list[str], optional): filter by semantic tags (OR matching)
  - `text` (str, optional): full-text search across summary and artifact content
  - `limit` (int, optional): max results (default 10)
- Returns: list of matching decision records with ID, skill, domain, summary, date, tags
- Acceptance criteria:
  - Supports any combination of filters
  - Text search is case-insensitive
  - Results ordered by relevance (tag match count, then recency)
  - Returns empty set with helpful message when no matches

**FR-1.13: `get_domain`**
- Description: "Get the full domain contract for a named domain"
- Parameters:
  - `domain` (str, required): domain name
- Returns: complete domain contract with all 11 Sociocracy 3.0 elements -- primary_driver, key_responsibilities, main_deliverables, customers, external_constraints, key_challenges, key_resources, delegator_responsibilities, competencies_needed, key_metrics, evaluation_schedule
- Acceptance criteria:
  - Returns all 11 elements of the domain contract
  - Returns clear error if domain does not exist
  - Includes current steward(s) and their role assignments

**FR-1.14: `get_active_members`**
- Description: "Get active ecosystem members, optionally filtered"
- Parameters:
  - `ethos` (str, optional): filter by ETHOS name
  - `profile` (str, optional): filter by profile type (co-creator, builder, collaborator, townhall)
  - `status` (str, optional): filter by membership status (active, onboarding, wind_down)
- Returns: list of members with name, profile, ETHOS(s), joined_date, status
- Acceptance criteria:
  - Returns only active members by default (status=active)
  - Supports combining filters
  - Returns count alongside the list

#### MCP Server Registration

All 14 tools are registered into a single MCP server:

```python
gov_server = create_sdk_mcp_server(
    name="neos-governance",
    version="0.1.0",
    tools=[
        search_agreements, get_agreement,
        create_agreement_draft, update_agreement_status,
        check_authority, get_member_roles,
        create_proposal, record_advice,
        record_consent_position, check_quorum,
        create_decision_record, search_precedents,
        get_domain, get_active_members,
    ]
)
```

Tool names are prefixed with `mcp__neos-gov__` when referenced in the agent's `allowed_tools` configuration.

---

### FR-2: System Prompt Assembly

Dynamic 3-layer system prompt assembled per session in `agent/src/neos_agent/agent/system_prompt.py`.

#### FR-2.1: Layer 1 -- Foundation Prompt (~2,000 tokens, always present)

Content:
- **Agent identity**: "You are the NEOS Governance Agent for {ecosystem_name}."
- **Role definition**: Process facilitator, NOT decision-maker. Zero authority over governance outcomes. The agent structures, records, and explains -- it never approves, rejects, or overrides.
- **NEOS Principles**: All 10 principles from `NEOS_PRINCIPLES.md`, condensed to name + one-sentence summary each.
- **Behavioral constraints**:
  - Never bypass the ACT process, even if asked to
  - Never make a governance decision on behalf of a participant
  - Always state when a participant needs to take an action (the agent cannot take it for them)
  - Flag capture resistance concerns when detected in user requests
  - Use NEOS terminology consistently (ETHOS, not "department"; Steward, not "manager"; Current-See, not "token")
- **Terminology table**: Key terms from product-guidelines.md
- **Skill index**: All 54 skill names with one-line descriptions, organized by layer. This allows the agent to identify which skill is relevant to a user's request.
- **Capabilities summary**: What the agent can do (search agreements, help draft proposals, walk through ACT phases, check authority, search precedents) and what it cannot do (approve agreements, cast votes, override objections, expand authority).

Acceptance criteria:
- Foundation prompt is deterministic given an ecosystem_name
- Token count stays under 2,500 tokens
- Includes all 10 NEOS principles
- Includes all 54 skill names

#### FR-2.2: Layer 2 -- Active Skill Prompt (~4,000 tokens, loaded on demand)

Content:
- The complete SKILL.md content of the currently active skill (sections A through L)
- The relevant YAML template from the skill's `assets/` directory (if one exists)
- Instruction to follow the step-by-step process in Section E
- Instruction to check authority boundaries per Section G before executing steps
- Instruction to monitor for capture risks per Section H

Acceptance criteria:
- Loaded only when a participant starts or continues a governance process
- Replaced when the skill router detects a transition
- If skill content exceeds 4,000 tokens, truncate stress-test results (section after "Stress-Test Results") first -- they are valuable but not needed for process execution
- Null/empty when no active skill (general conversation mode)

#### FR-2.3: Layer 3 -- Dependency Prompt (~2,000 tokens, loaded with active skill)

Content:
- For each skill listed in the active skill's `depends_on` frontmatter field:
  - Skill name
  - Description (from frontmatter)
  - Condensed Section E (key process steps only, not full narrative)
  - Section G summary (who has authority for what)

Acceptance criteria:
- Only populated when Layer 2 is populated
- Each dependency summary is max 400 tokens
- If total exceeds 2,000 tokens, prioritize direct dependencies over transitive ones
- Dependencies are resolved from the skill registry (agent_foundation)

#### FR-2.4: Assembly Function

```python
async def assemble_system_prompt(
    ecosystem_name: str,
    active_skill: str | None = None,
    skill_registry: SkillRegistry = None,
) -> str:
```

Acceptance criteria:
- Returns a single string combining all applicable layers
- Total output stays under 10,000 tokens to leave room for conversation context
- Layers are separated by clear markers (e.g., `---`) for readability in debugging
- Logs the token count estimate on each assembly

---

### FR-3: Chat SSE Handler

Sanic route handler in `agent/src/neos_agent/views/chat.py` that connects user messages to the Claude Agent SDK and streams responses via Datastar SSE.

#### FR-3.1: Message Endpoint

- Route: `POST /chat/message`
- Request body: `{ "message": str, "session_id": str }`
- Behavior:
  1. Look up or create an agent session by session_id
  2. Load the session's current system prompt (assembled per FR-2)
  3. Create or resume a `ClaudeSDKClient` with the session's configuration
  4. Send the user's message via `client.query()`
  5. Stream the response as Datastar SSE events

#### FR-3.2: SSE Streaming Format

Each chunk from the agent is forwarded as a Datastar SSE event:

- **Text deltas**: `patch_elements` targeting `#chat-messages` with appended message HTML fragment
- **Tool calls**: `patch_elements` with a tool-call indicator fragment showing the tool name and arguments (collapsed by default, expandable)
- **Tool results**: `patch_elements` with tool result summary appended to the tool-call indicator
- **Skill transitions**: `patch_signals` updating `active_skill` and `active_step` signals, plus a `patch_elements` with a visual transition indicator in the chat
- **Completion**: `patch_signals` updating `loading` to false

Acceptance criteria:
- First SSE event emitted within 200ms of receiving the user message (network time excluded; this is time from receiving the request to sending the first SSE event, which includes the initial "typing" indicator)
- Tool calls are shown inline in the chat with a visual distinction from regular messages
- Tool errors are caught and displayed gracefully (not raw stack traces)
- The SSE connection closes cleanly after the response completes

#### FR-3.3: Session History

- Route: `GET /chat/history?session_id={id}`
- Returns the full message history for a session as HTML fragments suitable for Datastar rendering
- Used on page load to restore chat state after a page refresh

Acceptance criteria:
- Returns all messages in chronological order
- Includes both user messages and agent responses
- Includes tool call/result summaries
- Returns empty state with welcome message for new sessions

---

### FR-4: Chat Panel Template

HTML templates for the chat interface, rendered server-side with Datastar signals for reactivity.

#### FR-4.1: Chat Panel (`templates/chat/panel.html`)

Structure:
- **Header**: ecosystem name + "Governance Agent" label
- **Active skill indicator**: shows current active skill name and step (or "General" when no skill active), bound to `active_skill` signal
- **ACT progress indicator**: shows current ACT phase (Advice/Consent/Test) when in a proposal flow, bound to `active_step` signal
- **Message history area**: scrollable container with ID `chat-messages`, auto-scrolls to bottom on new messages
- **Input area**: text input + send button, disabled while `loading` is true
- **Datastar signals**: `active_skill` (str), `active_step` (str), `session_id` (str), `loading` (bool), `message` (str, bound to input)

Acceptance criteria:
- Panel occupies the right side of the application layout (or full width on mobile)
- Message input submits on Enter key (Shift+Enter for newline)
- Send button shows loading state while waiting for response
- Auto-scrolls to newest message on each SSE update
- Session ID is generated client-side on first load and persisted in localStorage

#### FR-4.2: Message Fragment (`templates/chat/message.html`)

Structure:
- **User message**: styled distinctly (right-aligned or colored background), shows message text and timestamp
- **Agent message**: styled distinctly (left-aligned), shows message text, timestamp, and optional tool call indicators
- **Tool call indicator**: collapsible element showing tool name, arguments summary, and result. Defaults to collapsed. Shows a small icon (wrench or gear via CSS, no emoji) to indicate tool usage.
- **Skill transition indicator**: a visual divider/banner showing "Transitioning to: {skill_name}" when the router detects a skill change
- **System message**: for errors, welcome messages, session restored indicators

Acceptance criteria:
- Each message has a unique ID for SSE targeting
- Messages are semantic HTML (not just divs -- use appropriate elements)
- Tool call details are expandable/collapsible without JavaScript beyond Datastar
- Timestamps show relative time ("2 min ago") with full timestamp on hover

---

### FR-5: Skill Router

Detects when the current governance process triggers a transition to another skill, implemented in `agent/src/neos_agent/agent/router.py`.

#### FR-5.1: Transition Pattern Registry

A declarative mapping of skill transitions based on process completion states:

| Source Skill | Trigger Condition | Destination Skill |
|---|---|---|
| agreement-creation (Step 4) | Draft complete, ACT routing determined | act-advice-phase |
| act-advice-phase (Step complete) | Advice period ends, proposer proceeds | act-consent-phase |
| act-consent-phase (consent achieved) | All positions recorded, consent achieved | act-test-phase OR None (adopted directly) |
| act-consent-phase (objections unresolved) | Max rounds exhausted | proposal-resolution |
| act-test-phase (test complete) | Test period ends, test adopted | agreement-registry |
| agreement-review (amendment needed) | Review identifies need for change | agreement-amendment |
| agreement-amendment (draft complete) | Amendment drafted, needs ACT | act-advice-phase |
| resource-request (approval needed) | Request requires ACT process | act-advice-phase |
| harm-circle (repair needed) | Harm acknowledged, repair agreed | repair-agreement |
| escalation-triage (coaching needed) | Escalated to GAIA Level 4 | coaching-intervention |
| voluntary-exit (obligations found) | Exit initiated, commitments to unwind | commitment-unwinding |
| commitment-unwinding (complete) | All obligations resolved | portable-record |
| emergency-criteria-design (crisis declared) | Emergency declared | crisis-coordination |
| crisis-coordination (crisis resolved) | Emergency ends | emergency-reversion |
| emergency-reversion (complete) | Authority reverted | post-emergency-review |

Acceptance criteria:
- Transition patterns are data-driven (a dict or similar structure), not hardcoded if/else chains
- Each transition includes the source skill, a trigger description, and the destination skill name
- The router returns None when no transition applies (conversation continues in current skill)
- New transitions can be added by extending the pattern registry without modifying router logic

#### FR-5.2: Transition Detection

```python
class SkillRouter:
    def detect_transition(
        self,
        current_skill: str,
        tool_calls: list[dict],
        agent_response: str,
    ) -> str | None:
```

The router analyzes:
1. **Tool call patterns**: e.g., if `create_agreement_draft` was just called successfully, and the current skill is agreement-creation, the next step is act-advice-phase
2. **Status transitions**: e.g., if `update_agreement_status` moved a proposal from "consent" to "test", transition to act-test-phase
3. **Agent response content**: secondary signal -- look for phrases that indicate process completion ("The advice phase is complete", "Consent has been achieved")

Acceptance criteria:
- Primary detection is tool-call-based (deterministic), not pure text analysis
- Returns the destination skill name or None
- Does not trigger transitions on failed tool calls
- Logs transition detections for debugging

#### FR-5.3: Transition Announcement

When a transition is detected:
1. Update the session's active_skill
2. Reassemble the system prompt with the new skill's content (Layer 2 + Layer 3)
3. Emit a Datastar `patch_signals` event with updated active_skill and active_step
4. Insert a visual transition indicator in the chat stream

Acceptance criteria:
- The transition is announced to the user in the chat before the agent continues
- The system prompt is updated before the next agent turn
- The previous skill's context is removed from the system prompt (replaced, not accumulated)

---

## Non-Functional Requirements

### NFR-1: Streaming Latency

- Time from receiving POST /chat/message to emitting the first SSE event (typing indicator) must be under 200ms
- This is application-side latency only; Claude API latency is outside our control
- The typing indicator appears immediately; actual content follows when Claude responds

### NFR-2: Session Persistence

- Agent sessions are persisted to the `agent_sessions` database table (provided by agent_foundation)
- Session record stores: session_id, ecosystem_id, active_skill, message_history (JSON), created_at, updated_at
- Sessions survive page refreshes -- history is restored from DB on reconnect
- Sessions expire after 24 hours of inactivity (configurable)
- Message history is pruned to the most recent 50 messages to manage context window size

### NFR-3: Error Handling

- Tool execution errors are caught at the MCP server level and returned as structured error responses
- The agent sees the error and can explain it to the user (e.g., "I could not find that agreement. Would you like to search by a different term?")
- Network errors during SSE streaming send a final error event before closing the connection
- Database errors during tool execution are logged and return a generic "internal error" to the agent (no raw SQL or stack traces)

### NFR-4: Prompt Token Budget

- Foundation prompt (Layer 1): max 2,500 tokens
- Active skill prompt (Layer 2): max 4,500 tokens
- Dependency prompt (Layer 3): max 2,000 tokens
- Total system prompt: max 10,000 tokens
- This leaves approximately 190,000 tokens for conversation context on Claude models with 200K context windows
- Token count is estimated using a 4-characters-per-token heuristic (conservative)

### NFR-5: Audit Trail

- Every tool call is logged to the decision_records table with:
  - The tool name
  - The input parameters
  - The output (success or error)
  - The session_id
  - Timestamp
- This creates a complete audit trail of all governance actions taken through the agent

### NFR-6: Principle Compliance

- The agent's system prompt explicitly prohibits NEOS principle violations
- Tools enforce structural constraints (valid status transitions, authority checks, quorum rules)
- The agent cannot be instructed to bypass governance process -- the tools themselves enforce the process, and the system prompt reinforces this

---

## User Stories

### US-1: Create an Agreement Through the Agent

**As** a TH member,
**I want** to create a new space agreement through the governance agent,
**So that** I follow the correct NEOS process without needing to memorize it.

**Given** I am chatting with the governance agent,
**When** I say "I need to create a kitchen space agreement for SHUR Bali,"
**Then** the agent:
1. Loads the agreement-creation skill
2. Walks me through the required inputs (type, domain, affected parties, text, review date)
3. Uses `create_agreement_draft` to create the draft
4. Explains the next step (synergy check, then ACT routing)
5. Transitions to act-advice-phase when the draft is complete
6. Guides me through each subsequent phase

### US-2: Record Consent Positions

**As** a facilitator,
**I want** to record each participant's position during a consent round,
**So that** every position is formally documented with timestamps.

**Given** a proposal is in consent phase,
**When** I tell the agent "Amara consents, Kaia stands aside because she is not affected, Preethi objects because the cleanup timeline is too short,"
**Then** the agent:
1. Uses `record_consent_position` for each participant
2. Validates each position (requires reason for stand-aside and objection)
3. Shows a summary of all positions recorded
4. Checks quorum via `check_quorum`
5. If objections exist, explains the integration round process

### US-3: Search for Precedent

**As** an OSC member,
**I want** to find how similar situations were handled before,
**So that** I can make a more informed governance decision.

**Given** I am considering a resource allocation dispute,
**When** I ask "Have we handled resource disputes between ETHOS before?,"
**Then** the agent:
1. Uses `search_precedents` with relevant tags
2. Returns matching decision records with summaries
3. Explains the context of each precedent
4. Notes whether the precedent is still current or has been challenged

### US-4: Check Authority Before Acting

**As** an AE member,
**I want** to verify I have authority to propose changes to a shared resource,
**So that** I do not overstep my domain.

**Given** I am unsure about my authority scope,
**When** I ask "Can I propose changes to the workshop schedule?,"
**Then** the agent:
1. Uses `check_authority` with my name, the action, and the domain
2. Returns whether I have authority and why
3. If I lack authority, explains who does and how to proceed
4. Suggests the correct process (e.g., "You can propose through your circle, which would then go through cross-circle ACT")

### US-5: Resume a Session After Page Refresh

**As** a participant mid-process,
**I want** my chat history and active skill to persist across page refreshes,
**So that** I do not lose my progress.

**Given** I am in the middle of recording advice for a proposal,
**When** I refresh the page,
**Then** the agent:
1. Restores my session from the database
2. Shows my full message history
3. Resumes with the correct active skill (act-advice-phase)
4. Continues from where I left off

---

## Technical Considerations

### Claude Agent SDK Usage

- Use `ClaudeSDKClient` for multi-turn sessions (not stateless `query()`) to maintain conversation context
- Register all tools via a single MCP server named "neos-governance"
- Set `max_turns=20` to prevent runaway tool loops
- Use `allowed_tools` to list all 14 tools explicitly (no wildcards)

### Datastar SSE Integration

- Datastar expects SSE events in specific formats: `patch_elements` for DOM updates, `patch_signals` for reactive signal updates
- Chat messages are streamed as HTML fragments targeting the `#chat-messages` container
- The agent's response is accumulated into a message fragment and patched into the DOM as tokens arrive

### Skill Registry Dependency

- The skill registry (from agent_foundation) provides:
  - `get_skill(name)` -- returns skill metadata and file path
  - `get_skill_content(name)` -- returns the full SKILL.md content
  - `list_skills()` -- returns all 54 skills with metadata
  - `get_skill_assets(name)` -- returns YAML templates from assets/

### Database Models (from agent_foundation)

This track depends on but does not define these models:
- `Agreement` -- agreements table
- `Proposal` -- proposals table
- `Member` -- members table
- `Role` -- roles / role_assignments table
- `Domain` -- domains table
- `DecisionRecord` -- decision_records table
- `AgentSession` -- agent_sessions table

---

## Out of Scope

- **Authentication/authorization**: user identity is assumed to be provided by the application layer (future track)
- **File uploads**: agreement documents are text-only in this track
- **Multi-ecosystem support**: this track targets a single ecosystem (OmniOne); multi-tenancy is deferred
- **Agent memory beyond sessions**: long-term agent memory or learning is not in scope
- **Voice/audio interface**: text chat only
- **Mobile-specific UI**: responsive CSS but no dedicated mobile components
- **Rate limiting**: deferred to infrastructure track
- **Automated governance actions**: the agent facilitates but never autonomously initiates governance processes

---

## Open Questions

1. **Session concurrency**: Should multiple browser tabs share a session, or does each tab get its own? Current assumption: same session_id from localStorage means shared session, but SSE connections are per-tab.

2. **Prompt caching**: Claude supports prompt caching for repeated system prompts. Should we enable this for the foundation prompt (Layer 1) since it rarely changes? Likely yes, but depends on SDK support.

3. **Tool call confirmation**: Should certain tools (e.g., `create_agreement_draft`, `update_agreement_status`) require user confirmation before executing? The agent could present a summary and ask "Shall I proceed?" This adds friction but prevents accidental actions.

4. **Offline skill loading**: Should the system prompt include the full SKILL.md content (current design) or provide it as a tool the agent calls on demand? Including it ensures the agent has full context but uses more tokens; on-demand loading saves tokens but adds latency.

5. **Consent round real-time**: In a live consent round with multiple participants, should the agent support concurrent position recording from different users? Current assumption: single-user chat, facilitator records positions on behalf of participants. Multi-user real-time is a future track.
