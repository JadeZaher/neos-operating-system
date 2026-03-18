# Implementation Plan: Unified Ecosystem Scope Management

**Track ID:** ecosystem_scope_20260318
**Status:** complete

---

## Phase 1: EcosystemScope dataclass + shared utilities
**Status:** complete

### Task 1.1: Create EcosystemScope dataclass in _rendering.py
- [x] Define `EcosystemScope` dataclass with `selected`, `selected_ids`, `active`, `active_id`, `is_multi`, `require_ids()`
- [x] Add type hints and docstrings
- **File:** `agent/src/neos_agent/views/_rendering.py`

### Task 1.2: Move escape_like() to _rendering.py
- [x] Move `_escape_like()` from `ecosystems.py` to `_rendering.py` as `escape_like()`
- [x] Update `ecosystems.py` to import from `_rendering.py`
- **Files:** `_rendering.py`, `ecosystems.py`

### Task 1.3: Fix get_scoped_entity() fail-safe behavior
- [x] When `eco_ids` is empty and entity has `ecosystem_attr`, return `None` (deny access) instead of allowing
- [x] Add docstring clarifying fail-safe behavior
- **File:** `_rendering.py`

### Task 1.4: Replace datetime.utcnow() with datetime.now(timezone.utc)
- [x] Fix in `main.py` auth middleware (2 occurrences)
- [x] Fix in `chat.py` (1 occurrence)
- [x] Fix in `dashboard.py` (1 occurrence)
- [x] Fix in any other files using `utcnow()`
- **Files:** `main.py`, `chat.py`, `dashboard.py`

---

## Phase 2: Middleware + render() refactor
**Status:** complete

### Task 2.1: Update auth_middleware to populate EcosystemScope
- [x] Build `EcosystemScope` object from validated cookie data
- [x] Set `request.ctx.ecosystem_scope` alongside existing attrs (backward compat initially)
- [x] Ensure both public and authenticated paths set the scope
- **File:** `main.py`

### Task 2.2: Update render() to inject EcosystemScope
- [x] Inject `ecosystem_scope` into template context
- [x] Set `selected_ecosystems` = `scope.selected` (never overridable by views)
- [x] Remove the `context.setdefault("ecosystems", ecosystems)` backward-compat line
- [x] Audit that no template relies on the removed default
- **File:** `_rendering.py`

### Task 2.3: Update get_selected_ecosystem_ids() to use EcosystemScope
- [x] Read from `request.ctx.ecosystem_scope` first, fall back to old attrs
- [x] Deprecate direct `request.ctx.selected_ecosystem_ids` access in views over time
- **File:** `_rendering.py`

---

## Phase 3: View hardening (all 12 entity views)
**Status:** complete

### Task 3.1: Standardize _apply_filters with escape_like across all views
- [x] `agreements.py` — import and apply `escape_like()` in all ILIKE patterns
- [x] `members.py` — import and apply `escape_like()`
- [x] `domains.py` — import and apply `escape_like()`
- [x] `proposals.py` — import and apply `escape_like()`
- [x] `decisions.py` — import and apply `escape_like()`
- [x] `conflicts.py` — import and apply `escape_like()`
- [x] `exit.py` — import and apply `escape_like()`
- **Files:** 7 view files

### Task 3.2: Add _apply_filters to safeguards and emergency views
- [x] `safeguards.py` — extract inline ecosystem filtering into `_apply_filters(stmt, request, eco_ids)`
- [x] `emergency.py` — extract inline ecosystem filtering into `_apply_filters(stmt, request, eco_ids)`
- **Files:** `safeguards.py`, `emergency.py`

### Task 3.3: Add authorization scoping to ecosystem CRUD routes
- [x] `edit_form` — verify user is a member of the ecosystem (or has admin role)
- [x] `update_ecosystem` — same check
- [x] `update_ecosystem_post` — delegates to update, inherits check
- [x] Add comment to `create_ecosystem` noting role-check is deferred to RBAC track
- **File:** `ecosystems.py`

### Task 3.4: Fix onboarding routes to use get_scoped_entity
- [x] `ceremony` — replace manual scope check with `get_scoped_entity()` on parent Member
- [x] `record_consent` — same
- [x] `finalize_onboarding` — same
- [x] Ensure empty `eco_ids` case is handled (deny, not bypass)
- **File:** `onboarding.py`

### Task 3.5: Standardize error codes
- [x] All `validate_ecosystem_id()` failures return 403 consistently
- [x] Check: agreements, members, domains, proposals, conflicts, exit, safeguards, emergency
- **Files:** all entity view files

---

## Phase 4: Template + form fixes
**Status:** complete

### Task 4.1: Create shared ecosystem picker partial
- [x] Create `templates/partials/ecosystem_picker.html`
- [x] When `selected_ecosystems|length > 1`: render `<select name="ecosystem_id">` dropdown
- [x] When `selected_ecosystems|length == 1`: render `<input type="hidden">` with the ID
- [x] When `selected_ecosystems` is empty: render warning message with link to /ecosystems
- **File:** `templates/partials/ecosystem_picker.html` (new)

### Task 4.2: Update all creation form templates to use the picker
- [x] `agreements/form.html` — replace hidden input with `{% include "partials/ecosystem_picker.html" %}`
- [x] `members/form.html` — same
- [x] `domains/form.html` — same
- [x] `proposals/form.html` — same
- [x] `conflicts/form.html` — same
- [x] `exit/form.html` — same
- **Files:** 6 form templates

### Task 4.3: Add ecosystem_id to emergency and safeguards POST forms
- [x] `emergency/dashboard.html` — add hidden ecosystem_id field (or picker) to declare-emergency form
- [x] `safeguards/dashboard.html` — add hidden ecosystem_id field to request-audit form
- **Files:** 2 dashboard templates

### Task 4.4: Verify base.html uses selected_ecosystems everywhere
- [x] Confirm header badges use `selected_ecosystems`
- [x] Confirm breadcrumb uses `selected_ecosystems`
- [x] Confirm no remaining references to bare `ecosystems` for selection display
- **File:** `templates/base.html`

---

## Phase 5: Chat agent scope propagation
**Status:** complete

### Task 5.1: Update chat session to support multi-ecosystem context
- [x] Add `ecosystem_ids` JSON field to AgentSession model (or a related table)
- [x] Populate with all `selected_ecosystem_ids` on session creation
- [x] Create Alembic migration for the schema change
- **Files:** `db/models.py`, `alembic/versions/`, `chat.py`

### Task 5.2: Update system prompt ecosystem context
- [x] Build system prompt section listing all selected ecosystem names
- [x] Clarify whether the user is in a single or multi-ecosystem context
- [x] Pass ecosystem context to tool call functions
- **File:** `chat.py`

### Task 5.3: Ensure tool calls use full ecosystem scope
- [x] `execute_tool()` passes all selected ecosystem IDs to tool functions
- [x] Tool functions that create entities prompt for ecosystem selection when multi-select
- **File:** `chat.py`

---

## Verification Checklist
- [x] Header badges show ONLY selected ecosystems on /ecosystems page (not full directory)
- [x] Breadcrumb shows "1 Ecosystem name" or "N Ecosystems" matching actual selection
- [x] Creating an agreement with 1 ecosystem selected pre-populates ecosystem_id
- [x] Creating an agreement with 2+ ecosystems selected shows picker dropdown
- [x] ILIKE search with "%" character does not match all records
- [x] Editing another user's ecosystem returns 403
- [x] Accessing entity detail with no ecosystems selected returns 403 (not all data)
- [x] Emergency declare and safeguard audit POST actions succeed with ecosystem_id
- [x] Chat agent system prompt lists correct selected ecosystem names
- [x] All `datetime.utcnow()` calls replaced
