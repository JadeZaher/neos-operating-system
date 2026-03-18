# Implementation Plan: Claude Agent SDK Integration & Chat

**Track ID:** agent_core_20260305
**Depends on:** agent_foundation_20260305
**Phases:** 4
**Tasks:** 16
**Estimated scope:** 2-3 days

---

## Overview

This plan builds the conversational AI layer on top of the Sanic/SQLAlchemy foundation. We proceed bottom-up: governance tools first (the agent's "hands"), then the system prompt (the agent's "knowledge"), then the chat interface (the agent's "voice"), and finally session management with skill routing (the agent's "memory and awareness").

Each phase ends with a verification checkpoint. All tasks follow TDD: write the test first, implement to pass, then refactor.

---

## Phase 1: Governance Tools (5 tasks)

**Goal:** Define all 14 governance tools as MCP-registered functions that interact with the SQLAlchemy models from agent_foundation. At the end of this phase, the MCP server can be instantiated with all tools and each tool can be called independently.

### Task 1.1: Test scaffold for governance tools

**TDD: Red**

Create `agent/tests/test_governance_agent.py` with test cases for all 14 tools.

Tests to write:
- `test_mcp_server_creation` -- verify `create_sdk_mcp_server` returns a server with 14 registered tools
- `test_search_agreements_by_status` -- search with status filter returns matching agreements
- `test_search_agreements_empty` -- search with no matches returns helpful message
- `test_get_agreement_exists` -- get by ID returns full agreement record
- `test_get_agreement_not_found` -- get by invalid ID returns error
- `test_create_agreement_draft` -- creates draft with generated ID, status="draft"
- `test_create_agreement_draft_invalid_proposer` -- rejects unknown proposer
- `test_update_agreement_status_valid` -- valid transition succeeds
- `test_update_agreement_status_invalid` -- invalid transition returns error with explanation
- `test_check_authority_authorized` -- member with matching role returns authorized=true
- `test_check_authority_unauthorized` -- member without role returns authorized=false with reason
- `test_create_proposal` -- creates proposal with generated ID
- `test_record_consent_position_objection_requires_reason` -- objection without reason is rejected
- `test_check_quorum_consent_mode` -- 2/3 threshold calculation
- `test_check_quorum_consensus_mode` -- all-present requirement
- `test_create_decision_record` -- creates record with auto-generated tags
- `test_search_precedents_by_tags` -- tag-based search returns matches

Use a test database fixture (SQLite in-memory) with seed data: 3 members, 2 agreements (1 active, 1 draft), 1 domain, 2 role assignments. Mock the SQLAlchemy session.

**File:** `agent/tests/test_governance_agent.py`

---

### Task 1.2: Implement registry and agreement lifecycle tools (tools 1-4)

**TDD: Green**

Implement in `agent/src/neos_agent/agent/governance_agent.py`:

```python
@tool("search_agreements", "Search agreements by type, domain, status, affected party, or date range", {
    "type": str, "domain": str, "status": str, "affected_party": str, "date_range": str
})
async def search_agreements(args: dict) -> dict: ...

@tool("get_agreement", "Get full details of an agreement by its ID", {
    "agreement_id": str
})
async def get_agreement(args: dict) -> dict: ...

@tool("create_agreement_draft", "Create a new agreement draft", {
    "type": str, "title": str, "proposer": str, "domain": str,
    "text": str, "affected_parties": list, "review_date": str, "rationale": str
})
async def create_agreement_draft(args: dict) -> dict: ...

@tool("update_agreement_status", "Transition an agreement's status through its lifecycle", {
    "agreement_id": str, "new_status": str, "reason": str, "metadata": dict
})
async def update_agreement_status(args: dict) -> dict: ...
```

Implementation details:
- Each tool function receives `args: dict` and returns `{"content": [{"type": "text", "text": json.dumps(result)}]}`
- Database access via an async SQLAlchemy session injected through a module-level factory or context variable
- `search_agreements` builds a dynamic query with optional filters, limits to 20, orders by status priority then recency
- `create_agreement_draft` generates ID as `AGR-{domain_prefix}-{year}-{seq}`, validates proposer and affected parties exist in members table
- `update_agreement_status` enforces valid transitions via a VALID_TRANSITIONS dict:
  ```python
  VALID_TRANSITIONS = {
      "draft": ["advice"],
      "advice": ["consent"],
      "consent": ["test", "active"],
      "test": ["active"],
      "active": ["under_review"],
      "under_review": ["sunset", "active"],
  }
  ```

Run tests from Task 1.1 for tools 1-4. All should pass.

**File:** `agent/src/neos_agent/agent/governance_agent.py`

---

### Task 1.3: Implement authority and ACT process tools (tools 5-10)

**TDD: Green**

Add to `agent/src/neos_agent/agent/governance_agent.py`:

```python
@tool("check_authority", ...) async def check_authority(args): ...
@tool("get_member_roles", ...) async def get_member_roles(args): ...
@tool("create_proposal", ...) async def create_proposal(args): ...
@tool("record_advice", ...) async def record_advice(args): ...
@tool("record_consent_position", ...) async def record_consent_position(args): ...
@tool("check_quorum", ...) async def check_quorum(args): ...
```

Implementation details:
- `check_authority`: joins member -> role_assignments -> domains, checks if the action falls within the role's scope for the given domain
- `get_member_roles`: simple query filtering by member and status=active
- `create_proposal`: generates `PROP-{year}-{seq}`, auto-sets consent_mode based on scope when not provided (OSC/UAF = consensus)
- `record_advice`: validates proposal status is "advice", validates advisor standing
- `record_consent_position`: validates proposal status is "consent", rejects stand_aside in consensus mode, requires reason for stand_aside/objection, prevents duplicate positions in same round
- `check_quorum`: calculates threshold based on consent_mode (2/3 for consent, 100% for consensus, 50% for emergency)

Run tests from Task 1.1 for tools 5-10.

**File:** `agent/src/neos_agent/agent/governance_agent.py`

---

### Task 1.4: Implement decision record and lookup tools (tools 11-14)

**TDD: Green**

Add to `agent/src/neos_agent/agent/governance_agent.py`:

```python
@tool("create_decision_record", ...) async def create_decision_record(args): ...
@tool("search_precedents", ...) async def search_precedents(args): ...
@tool("get_domain", ...) async def get_domain(args): ...
@tool("get_active_members", ...) async def get_active_members(args): ...
```

Implementation details:
- `create_decision_record`: generates `DR-{year}-{seq}`, auto-adds layer and skill name as tags
- `search_precedents`: supports multi-filter query, case-insensitive text search via SQL LIKE, orders by tag match count then recency
- `get_domain`: returns all 11 S3 domain contract elements, includes current steward(s)
- `get_active_members`: defaults to status=active, supports ETHOS and profile filters, returns count alongside list

Run tests from Task 1.1 for tools 11-14.

**File:** `agent/src/neos_agent/agent/governance_agent.py`

---

### Task 1.5: MCP server registration and integration verification

**TDD: Green + Refactor**

Create the MCP server factory function and verify all 14 tools are registered:

```python
def create_governance_server(db_session_factory) -> MCPServer:
    # Inject DB access into all tools
    # Register all 14 tools
    return create_sdk_mcp_server(
        name="neos-governance",
        version="0.1.0",
        tools=[search_agreements, get_agreement, ...]
    )
```

Also create `agent/src/neos_agent/agent/__init__.py` with clean exports.

Refactor pass:
- Extract common patterns (result formatting, error handling, ID generation) into helper functions
- Ensure consistent error response format across all tools
- Add docstrings to all tool functions

Verification:
- [ ] All 17 test cases pass
- [ ] MCP server instantiates with 14 tools
- [ ] Each tool returns the expected response format
- [ ] Invalid inputs return helpful error messages
- [ ] All tool calls create audit entries in decision_records

**Files:** `agent/src/neos_agent/agent/governance_agent.py`, `agent/src/neos_agent/agent/__init__.py`

[checkpoint marker]

---

## Phase 2: System Prompt Assembly (3 tasks)

**Goal:** Build the 3-layer dynamic prompt assembly pipeline. At the end of this phase, `assemble_system_prompt()` produces a well-structured system prompt that includes the agent's identity, active skill, and dependency context.

### Task 2.1: Test scaffold for system prompt

**TDD: Red**

Create `agent/tests/test_system_prompt.py` with test cases:

- `test_foundation_prompt_contains_identity` -- output contains "NEOS Governance Agent"
- `test_foundation_prompt_contains_all_principles` -- all 10 principle names appear
- `test_foundation_prompt_contains_skill_index` -- all 54 skill names appear
- `test_foundation_prompt_contains_terminology` -- key terms (ETHOS, Current-See, Steward, ACT) present
- `test_foundation_prompt_token_budget` -- estimated tokens under 2,500
- `test_skill_prompt_loads_content` -- active skill content appears when skill is set
- `test_skill_prompt_empty_when_no_skill` -- Layer 2 is empty when active_skill is None
- `test_skill_prompt_truncates_stress_tests` -- long skills are truncated at stress-test boundary
- `test_dependency_prompt_loads_depends_on` -- dependency summaries appear for active skill's depends_on
- `test_assembled_prompt_under_budget` -- total prompt under 10,000 tokens
- `test_assembled_prompt_layer_separation` -- layers are separated by markers

Use a mock SkillRegistry that returns canned skill metadata and content.

**File:** `agent/tests/test_system_prompt.py`

---

### Task 2.2: Implement system_prompt.py

**TDD: Green**

Create `agent/src/neos_agent/agent/system_prompt.py` with:

```python
FOUNDATION_TEMPLATE = """..."""  # Static template with {ecosystem_name} placeholder

PRINCIPLES_CONDENSED = [
    ("Consent Over Consensus", "Standard decisions pass when no one raises a reasoned objection..."),
    ...  # All 10
]

TERMINOLOGY = {
    "ETHOS": "Emergent Thriving Holonic Organizational Structure -- a self-organizing unit",
    ...
}

def build_foundation_prompt(ecosystem_name: str, skill_index: list[dict]) -> str:
    """Layer 1: identity, principles, terminology, skill index, constraints."""
    ...

async def build_skill_prompt(skill_name: str, registry: SkillRegistry) -> str:
    """Layer 2: full SKILL.md + assets for the active skill."""
    ...

async def build_dependency_prompt(skill_name: str, registry: SkillRegistry) -> str:
    """Layer 3: condensed depends_on skill summaries."""
    ...

async def assemble_system_prompt(
    ecosystem_name: str,
    active_skill: str | None = None,
    skill_registry: SkillRegistry = None,
) -> str:
    """Assemble the complete system prompt from all applicable layers."""
    ...
```

Implementation details:
- Foundation prompt is built from a template string with interpolation for ecosystem_name, principles, terminology, and skill index
- Skill prompt reads the full SKILL.md via the registry, truncates after "## Stress-Test Results" if the content exceeds ~4,000 tokens (estimated at 4 chars/token = 16,000 chars)
- Dependency prompt iterates the active skill's `depends_on` list, loads each dependency's frontmatter + Section E + Section G, condenses to ~400 tokens each
- Token estimation: `len(text) // 4` (conservative heuristic)
- `assemble_system_prompt` combines layers with `---` separators, logs the estimated token count

Run tests from Task 2.1.

**File:** `agent/src/neos_agent/agent/system_prompt.py`

---

### Task 2.3: Integration test -- prompt budget verification

**TDD: Green + Refactor**

Add integration tests to `agent/tests/test_system_prompt.py`:

- `test_real_skill_prompt_budget` -- using the actual agreement-creation SKILL.md content (read from disk), verify assembled prompt stays under 10,000 tokens
- `test_real_skill_with_dependencies` -- using agreement-creation (depends_on: domain-mapping), verify dependency prompt loads correctly
- `test_all_skills_fit_budget` -- iterate all 54 skills, verify each one individually fits within the Layer 2 budget (4,500 tokens)

Refactor pass:
- Optimize foundation prompt wording if over budget
- Tune truncation logic for SKILL.md content
- Ensure dependency summaries are genuinely useful (not just truncated at arbitrary point)

Verification:
- [ ] All test cases pass
- [ ] Foundation prompt contains all required elements under 2,500 tokens
- [ ] Every skill's Layer 2 prompt fits within 4,500 tokens
- [ ] Assembled prompt with any skill stays under 10,000 tokens
- [ ] Layer separation markers are present and clear

[checkpoint marker]

---

## Phase 3: Chat Panel & SSE Streaming (4 tasks)

**Goal:** Build the chat interface and SSE streaming pipeline. At the end of this phase, a user can send a message, the agent responds via streaming SSE, and the chat UI updates in real time.

### Task 3.1: Chat SSE handler

Create `agent/src/neos_agent/views/chat.py` with:

```python
from sanic import Blueprint, Request
from sanic.response import ResponseStream

chat_bp = Blueprint("chat", url_prefix="/chat")

@chat_bp.route("/message", methods=["POST"])
async def send_message(request: Request):
    """Accept user message, query the agent, stream response as Datastar SSE."""
    message = request.json.get("message")
    session_id = request.json.get("session_id")

    # 1. Look up or create session
    # 2. Build system prompt via assemble_system_prompt()
    # 3. Create ClaudeAgentOptions with system prompt + MCP server
    # 4. Create/resume ClaudeSDKClient
    # 5. Send user message
    # 6. Stream response as SSE

    async def stream_response(response):
        # Emit typing indicator immediately
        # Stream agent deltas as patch_elements
        # Stream tool calls as patch_elements with tool indicators
        # Update signals on skill transitions
        # Close with loading=false signal
        ...

    return ResponseStream(stream_response, content_type="text/event-stream")

@chat_bp.route("/history", methods=["GET"])
async def get_history(request: Request):
    """Return full message history for a session as HTML fragments."""
    session_id = request.args.get("session_id")
    # Load from agent_sessions table
    # Render as HTML fragments
    ...
```

Implementation details:
- SSE format follows Datastar conventions:
  ```
  event: datastar-patch-elements
  data: selector #chat-messages
  data: merge append
  data: fragment <div class="message agent">...</div>


  event: datastar-patch-signals
  data: signals {active_skill: "agreement-creation", loading: false}
  ```
- Text deltas are buffered into complete words before emitting (no mid-word breaks)
- Tool calls emit a collapsed indicator immediately, then append the result when available
- Errors are caught and emitted as system message fragments

**File:** `agent/src/neos_agent/views/chat.py`

---

### Task 3.2: Chat panel template

Create `agent/src/neos_agent/templates/chat/panel.html`:

```html
<div id="chat-panel"
     data-signals="{
       active_skill: '',
       active_step: '',
       session_id: '',
       loading: false,
       message: ''
     }">

  <!-- Header -->
  <div class="chat-header">
    <h2>{ecosystem_name} Governance Agent</h2>
    <div class="skill-indicator" data-text="$active_skill || 'General'"></div>
    <div class="step-indicator" data-show="$active_step" data-text="$active_step"></div>
  </div>

  <!-- Messages -->
  <div id="chat-messages" class="chat-messages">
    <!-- Messages appended here via SSE -->
  </div>

  <!-- Input -->
  <form class="chat-input"
        data-on-submit__prevent="$$post('/chat/message', {message: $message, session_id: $session_id})"
        data-attr-disabled="$loading">
    <textarea
      data-bind="message"
      placeholder="Ask about governance processes..."
      data-on-keydown="if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); this.form.requestSubmit(); }">
    </textarea>
    <button type="submit" data-attr-disabled="$loading || !$message.trim()">
      <span data-show="!$loading">Send</span>
      <span data-show="$loading">...</span>
    </button>
  </form>
</div>
```

Implementation details:
- Session ID initialization: `data-on-load` generates UUID and stores in localStorage if not present
- Auto-scroll: `data-on-load` on `#chat-messages` scrolls to bottom using MutationObserver or Datastar's built-in mechanisms
- History loading: `data-on-load` fires GET /chat/history to populate existing messages
- Mobile responsive: flexbox layout, full-width on screens < 768px

**File:** `agent/src/neos_agent/templates/chat/panel.html`

---

### Task 3.3: Message fragment template

Create `agent/src/neos_agent/templates/chat/message.html`:

```html
<!-- User message -->
<div class="message message-user" id="msg-{message_id}">
  <div class="message-content">{content}</div>
  <div class="message-meta">
    <time datetime="{iso_timestamp}" title="{full_timestamp}">{relative_time}</time>
  </div>
</div>

<!-- Agent message -->
<div class="message message-agent" id="msg-{message_id}">
  <div class="message-content">{content}</div>
  <div class="message-meta">
    <time datetime="{iso_timestamp}" title="{full_timestamp}">{relative_time}</time>
  </div>
</div>

<!-- Tool call indicator -->
<div class="message message-tool" id="tool-{call_id}">
  <details>
    <summary>
      <span class="tool-icon">[tool]</span>
      <span class="tool-name">{tool_name}</span>
      <span class="tool-status">{status}</span>
    </summary>
    <div class="tool-args"><pre>{args_json}</pre></div>
    <div class="tool-result"><pre>{result_summary}</pre></div>
  </details>
</div>

<!-- Skill transition indicator -->
<div class="message message-transition" id="transition-{id}">
  <div class="transition-banner">
    Transitioning to: <strong>{skill_name}</strong>
  </div>
</div>

<!-- System message -->
<div class="message message-system" id="sys-{id}">
  <div class="message-content">{content}</div>
</div>
```

Implementation details:
- Templates are rendered server-side with Jinja2 (Sanic-ext provides Jinja2 support) or simple string formatting
- Each message has a unique ID for SSE targeting
- Tool call uses HTML `<details>` element for native expand/collapse without extra JavaScript
- CSS classes control visual styling (no inline styles in template)

**File:** `agent/src/neos_agent/templates/chat/message.html`

---

### Task 3.4: Integration -- message round-trip verification

**TDD: Green**

Create `agent/tests/test_chat_integration.py`:

Tests:
- `test_send_message_returns_sse` -- POST /chat/message returns content-type text/event-stream
- `test_sse_contains_typing_indicator` -- first event is a typing indicator
- `test_sse_contains_agent_response` -- response includes patch_elements with message content
- `test_tool_call_appears_in_stream` -- when agent uses a tool, the tool indicator appears in SSE
- `test_history_empty_for_new_session` -- GET /chat/history returns welcome message for unknown session
- `test_history_returns_past_messages` -- GET /chat/history returns previously sent messages

Use Sanic's test client (`app.asgi_client` or `app.test_client`) to send requests. Mock the ClaudeSDKClient to return canned responses (no real API calls in tests).

Verification:
- [ ] Message round-trip works: user sends message, agent response streams back
- [ ] Tool calls are visible in the chat stream
- [ ] SSE events follow Datastar format
- [ ] Chat panel renders with all required elements
- [ ] History endpoint returns past messages

[checkpoint marker]

---

## Phase 4: Session Management & Skill Routing (4 tasks)

**Goal:** Implement session persistence and the skill transition router. At the end of this phase, the agent maintains state across page refreshes and automatically transitions between skills as governance processes flow through their natural lifecycle.

### Task 4.1: Test scaffold for skill router

**TDD: Red**

Create `agent/tests/test_router.py`:

Tests:
- `test_transition_agreement_creation_to_advice` -- after create_agreement_draft tool call in agreement-creation skill, router returns "act-advice-phase"
- `test_transition_advice_to_consent` -- after update_agreement_status(new_status="consent") in act-advice-phase, router returns "act-consent-phase"
- `test_transition_consent_to_test` -- after consent achieved, router returns "act-test-phase"
- `test_transition_consent_to_resolution` -- after max rounds exhausted, router returns "proposal-resolution"
- `test_no_transition_mid_process` -- during advice recording, router returns None
- `test_transition_on_failed_tool_call_ignored` -- failed tool call does not trigger transition
- `test_transition_exit_to_unwinding` -- voluntary-exit with obligations returns "commitment-unwinding"
- `test_transition_emergency_chain` -- emergency-criteria-design -> crisis-coordination -> emergency-reversion -> post-emergency-review
- `test_custom_transition_pattern_added` -- adding a new pattern to the registry works

**File:** `agent/tests/test_router.py`

---

### Task 4.2: Implement skill router

**TDD: Green**

Create `agent/src/neos_agent/agent/router.py`:

```python
from dataclasses import dataclass

@dataclass
class TransitionPattern:
    source_skill: str
    trigger_tool: str | None       # Tool call that triggers this transition
    trigger_status: str | None     # Status value that triggers (for update_ tools)
    trigger_condition: str         # Human-readable description
    destination_skill: str

TRANSITION_PATTERNS: list[TransitionPattern] = [
    TransitionPattern(
        source_skill="agreement-creation",
        trigger_tool="create_agreement_draft",
        trigger_status=None,
        trigger_condition="Agreement draft created, ready for ACT routing",
        destination_skill="act-advice-phase",
    ),
    TransitionPattern(
        source_skill="act-advice-phase",
        trigger_tool="update_agreement_status",
        trigger_status="consent",
        trigger_condition="Advice phase complete, entering consent",
        destination_skill="act-consent-phase",
    ),
    TransitionPattern(
        source_skill="act-consent-phase",
        trigger_tool="update_agreement_status",
        trigger_status="test",
        trigger_condition="Consent achieved, entering test phase",
        destination_skill="act-test-phase",
    ),
    TransitionPattern(
        source_skill="act-consent-phase",
        trigger_tool="update_agreement_status",
        trigger_status="active",
        trigger_condition="Consent achieved, adopted directly (test skipped)",
        destination_skill=None,  # Process complete
    ),
    # ... (all 15 patterns from spec FR-5.1)
]

class SkillRouter:
    def __init__(self, patterns: list[TransitionPattern] = None):
        self.patterns = patterns or TRANSITION_PATTERNS

    def detect_transition(
        self,
        current_skill: str,
        tool_calls: list[dict],
        agent_response: str,
    ) -> str | None:
        """Detect if a skill transition should occur based on tool calls and context."""
        for tc in tool_calls:
            if not tc.get("success", True):
                continue  # Skip failed tool calls
            for pattern in self.patterns:
                if pattern.source_skill != current_skill:
                    continue
                if pattern.trigger_tool and pattern.trigger_tool == tc.get("name"):
                    if pattern.trigger_status:
                        # Check if the status matches
                        args = tc.get("args", {})
                        if args.get("new_status") == pattern.trigger_status:
                            return pattern.destination_skill
                    else:
                        return pattern.destination_skill
        return None

    def add_pattern(self, pattern: TransitionPattern):
        """Add a custom transition pattern."""
        self.patterns.append(pattern)
```

Run tests from Task 4.1.

**File:** `agent/src/neos_agent/agent/router.py`

---

### Task 4.3: Implement session persistence

Add session management to the chat handler:

```python
# In views/chat.py or a new agent/session.py

async def get_or_create_session(session_id: str, db) -> AgentSession:
    """Load existing session or create new one."""
    session = await db.get(AgentSession, session_id)
    if not session:
        session = AgentSession(
            id=session_id,
            ecosystem_id="omnione",  # Default for now
            active_skill=None,
            message_history=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(session)
        await db.commit()
    return session

async def save_session(session: AgentSession, db):
    """Persist session state after each interaction."""
    session.updated_at = datetime.utcnow()
    # Prune to 50 most recent messages
    if len(session.message_history) > 50:
        session.message_history = session.message_history[-50:]
    await db.commit()

async def cleanup_expired_sessions(db, max_age_hours: int = 24):
    """Remove sessions older than max_age_hours of inactivity."""
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    await db.execute(
        delete(AgentSession).where(AgentSession.updated_at < cutoff)
    )
    await db.commit()
```

Update the chat message handler to:
1. Load session on each request
2. Append user message to history
3. Append agent response to history
4. Update active_skill when router detects a transition
5. Save session after each interaction

Tests (add to `agent/tests/test_chat_integration.py`):
- `test_session_persists_messages` -- send two messages, verify both appear in history
- `test_session_persists_active_skill` -- set active skill, reload session, verify it persists
- `test_session_prunes_old_messages` -- send 60 messages, verify only 50 retained
- `test_session_expires` -- create session, advance time 25 hours, verify cleanup removes it

**Files:** `agent/src/neos_agent/views/chat.py`

---

### Task 4.4: End-to-end test -- agreement creation through ACT flow

**TDD: Green + Refactor**

Create `agent/tests/test_e2e_agreement_flow.py`:

Simulate a complete agreement-creation -> act-advice-phase -> act-consent-phase flow:

1. User: "I want to create a kitchen space agreement for SHUR Bali"
2. Agent loads agreement-creation skill, asks for details
3. User provides: type=space, domain=SHUR Bali kitchen, affected_parties=[Amara, Kaia, Preethi], text="Kitchen quiet hours 10pm-7am..."
4. Agent calls `create_agreement_draft` -- verify tool call succeeds
5. Router detects transition to act-advice-phase -- verify active_skill updates
6. Transition indicator appears in chat
7. System prompt is reassembled with act-advice-phase SKILL.md
8. User: "Kaia advises changing quiet hours to 9:30pm"
9. Agent calls `record_advice` -- verify advice recorded
10. User: "Advice phase is complete, let's move to consent"
11. Agent calls `update_agreement_status(new_status="consent")`
12. Router detects transition to act-consent-phase
13. User: "Amara consents, Kaia stands aside, Preethi objects because cleanup time is too short"
14. Agent calls `record_consent_position` three times
15. Agent calls `check_quorum`
16. Verify all governance artifacts were created in the database

This test uses a mocked ClaudeSDKClient that returns scripted responses simulating the agent's behavior. It verifies the tool calls, session state, and router transitions without making real API calls.

Refactor pass:
- Clean up any code duplication across the codebase
- Ensure all modules have proper `__init__.py` exports
- Add type hints throughout
- Verify consistent logging patterns

Verification:
- [ ] Full agreement-creation to consent flow works end-to-end
- [ ] Skill transitions fire at the correct points
- [ ] Session state persists across simulated "page refreshes"
- [ ] All tool calls are logged in decision_records
- [ ] System prompt updates when active skill changes
- [ ] Chat history shows transition indicators
- [ ] Error cases are handled gracefully (invalid inputs, missing members, failed tools)

[checkpoint marker]

---

## File Summary

### New Files Created

| File | Phase | Purpose |
|------|-------|---------|
| `agent/src/neos_agent/agent/__init__.py` | 1 | Package exports |
| `agent/src/neos_agent/agent/governance_agent.py` | 1 | 14 tool definitions + MCP server factory |
| `agent/src/neos_agent/agent/system_prompt.py` | 2 | 3-layer prompt assembly |
| `agent/src/neos_agent/agent/router.py` | 4 | Skill transition detection |
| `agent/src/neos_agent/views/chat.py` | 3 | Chat SSE handler + session history |
| `agent/src/neos_agent/templates/chat/panel.html` | 3 | Chat panel template |
| `agent/src/neos_agent/templates/chat/message.html` | 3 | Message fragment templates |
| `agent/tests/test_governance_agent.py` | 1 | Tool tests |
| `agent/tests/test_system_prompt.py` | 2 | Prompt assembly tests |
| `agent/tests/test_chat_integration.py` | 3 | Chat round-trip tests |
| `agent/tests/test_router.py` | 4 | Router tests |
| `agent/tests/test_e2e_agreement_flow.py` | 4 | End-to-end flow test |

### Files Modified

| File | Phase | Change |
|------|-------|--------|
| (none from this track -- all new files) | | |

### Dependencies on agent_foundation_20260305

This track requires the following to exist before implementation begins:
- Sanic app instance with Datastar SSE support
- SQLAlchemy models: Agreement, Proposal, Member, Role, Domain, DecisionRecord, AgentSession
- SkillRegistry class with get_skill(), get_skill_content(), list_skills(), get_skill_assets()
- Database session factory for async SQLAlchemy operations
- Base route registration pattern for blueprints
