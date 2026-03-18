# Specification: Unified Ecosystem Scope Management

**Track ID:** ecosystem_scope_20260318
**Track Type:** Bug Fix + Refactor
**Created:** 2026-03-18
**Depends On:** dashboard_views_20260305, agent_foundation_20260305
**Priority:** P0

---

## Overview

Centralize and harden the ecosystem selection state management so that every view, form, template, and AI agent interaction consistently scopes data to the user's selected ecosystem(s). Today, the pipeline (cookie -> middleware -> request.ctx -> template -> forms) has variable naming collisions, inconsistent scoping, security gaps, and no single-ecosystem resolution for entity creation.

## Background

The ecosystem selection system uses a browser cookie (`neos_selected_ecosystems`) containing a JSON array of UUIDs. The auth middleware in `main.py` reads this cookie, validates membership, and sets `request.ctx.selected_ecosystem_ids` and `request.ctx.ecosystems`. The `render()` function in `_rendering.py` injects these into template context. Individual views call `get_selected_ecosystem_ids(request)` to filter queries.

### Current Problems (from code review)

**Critical:**
1. **ILIKE wildcard injection** — 7 of 9 entity views do raw `f"%{search}%"` without escaping SQL LIKE wildcards. Only `ecosystems.py` defines `_escape_like()`.
2. **Ecosystem CRUD has no authorization scoping (IDOR)** — `ecosystems.py` edit/update routes use `session.get()` directly without `get_scoped_entity()`. Any authenticated user can edit any ecosystem.

**High:**
3. **Variable naming collision** — `ecosystems` is used for both the selected ecosystems (from middleware) and the full directory listing (from ecosystems view), causing `base.html` to display all ecosystems instead of the selected ones. Partially patched with `selected_ecosystems` but `ecosystems` backward-compat default remains.
4. **Emergency/safeguards POST forms missing `ecosystem_id`** — POST handlers call `validate_ecosystem_id()` but templates have no form with the hidden field.
5. **`get_scoped_entity()` bypasses scope when `eco_ids` is empty** — Returns entity without checking ecosystem if the user has no selected ecosystems.
6. **Onboarding routes bypass `get_scoped_entity()`** — Manual scope check skips validation when `eco_ids` is empty.
7. **Chat agent session pins to single ecosystem** — Session model stores one `ecosystem_id` but tool calls span all selected ecosystems.

**Medium:**
8. **No `_apply_filters()` pattern in safeguards/emergency** — Inconsistent with all other entity views.
9. **`datetime.utcnow()` deprecated** — Used in auth middleware and chat, should be `datetime.now(timezone.utc)`.
10. **No ecosystem picker for multi-select creation** — Forms silently use `selected_ecosystems[0]` without user choice when multiple ecosystems are selected.
11. **Inconsistent error codes** — Some views return 403, others 400 for ecosystem validation failures.

## Goals

1. **Single source of truth**: One typed context object (`EcosystemScope`) on `request.ctx` that every layer reads from.
2. **Fail-safe scoping**: Queries raise/deny by default when no scope is active, rather than returning unfiltered data.
3. **No variable collisions**: Template context uses `scope.ecosystems` (or dedicated `selected_ecosystems`) for the selected set, never conflated with view-specific data.
4. **Consistent patterns**: All 12 entity views follow the same `_apply_filters()` pattern with shared `escape_like()`.
5. **Secure by default**: `get_scoped_entity()` denies access when `eco_ids` is empty. Ecosystem CRUD gets authorization checks.
6. **Multi-select creation UX**: When multiple ecosystems are selected, creation forms show a picker instead of silently choosing the first.
7. **AI agent awareness**: Chat agent receives full ecosystem context, session model supports multi-ecosystem scope.

## Non-Goals

- Changing the cookie-based storage mechanism (it works fine)
- Implementing full multi-tenant database isolation (row-level filtering is appropriate for this use case)
- Role-based access control beyond ecosystem membership (separate track)

## Technical Approach

### Phase 1: EcosystemScope dataclass + shared utilities

Create a typed `EcosystemScope` dataclass that replaces the loose `request.ctx.ecosystems` / `request.ctx.selected_ecosystem_ids` attributes:

```python
@dataclass
class EcosystemScope:
    selected: list[Ecosystem]       # ORM objects for selected ecosystems
    selected_ids: list[uuid.UUID]   # just the IDs
    active: Ecosystem | None        # single-select resolution (first, or None if multi)
    active_id: uuid.UUID | None     # convenience

    @property
    def is_multi(self) -> bool:
        return len(self.selected) > 1

    def require_ids(self) -> list[uuid.UUID]:
        """Return selected_ids or raise if empty (fail-safe)."""
        if not self.selected_ids:
            raise ValueError("No ecosystem scope active")
        return self.selected_ids
```

Move `escape_like()` to `_rendering.py`. Standardize all `_apply_filters()` functions.

### Phase 2: Middleware + render() refactor

Update `auth_middleware` in `main.py` to populate `request.ctx.ecosystem_scope` (the new typed object). Update `render()` to inject `ecosystem_scope` and `selected_ecosystems` into every template context. Remove the ambiguous `ecosystems` default.

### Phase 3: View hardening

- Fix `get_scoped_entity()` to deny when `eco_ids` is empty
- Add authorization to ecosystem CRUD routes
- Add `_apply_filters()` to safeguards and emergency views
- Fix onboarding routes to use `get_scoped_entity()`
- Standardize error codes to 403 for ecosystem validation failures
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`

### Phase 4: Template + form fixes

- Update all templates to use `selected_ecosystems` exclusively for selected set
- Add ecosystem picker `<select>` to creation forms when `selected_ecosystems|length > 1`
- Add `ecosystem_id` hidden fields to emergency and safeguards POST forms
- Add "select an ecosystem first" guard when `selected_ecosystems` is empty

### Phase 5: Chat agent scope propagation

- Update chat session model to support multi-ecosystem context
- Propagate full `EcosystemScope` to AI agent tool calls
- Update system prompt to reflect actual selected ecosystems

## Affected Files

### Python (views + middleware)
- `agent/src/neos_agent/views/_rendering.py` — EcosystemScope, escape_like, render(), get_scoped_entity()
- `agent/src/neos_agent/main.py` — auth_middleware refactor
- `agent/src/neos_agent/views/agreements.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/members.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/domains.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/proposals.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/decisions.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/conflicts.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/exit.py` — _apply_filters, escape_like
- `agent/src/neos_agent/views/safeguards.py` — add _apply_filters
- `agent/src/neos_agent/views/emergency.py` — add _apply_filters
- `agent/src/neos_agent/views/onboarding.py` — use get_scoped_entity
- `agent/src/neos_agent/views/ecosystems.py` — add authorization
- `agent/src/neos_agent/views/dashboard.py` — use EcosystemScope
- `agent/src/neos_agent/views/chat.py` — multi-ecosystem session

### Templates
- `templates/base.html` — use selected_ecosystems exclusively
- `templates/dashboard/agreements/form.html` — ecosystem picker
- `templates/dashboard/members/form.html` — ecosystem picker
- `templates/dashboard/domains/form.html` — ecosystem picker
- `templates/dashboard/proposals/form.html` — ecosystem picker
- `templates/dashboard/conflicts/form.html` — ecosystem picker
- `templates/dashboard/exit/form.html` — ecosystem picker
- `templates/dashboard/emergency/dashboard.html` — add ecosystem_id to POST forms
- `templates/dashboard/safeguards/dashboard.html` — add ecosystem_id to POST forms

### Shared partial (new)
- `templates/partials/ecosystem_picker.html` — reusable ecosystem selector for forms

## Testing Strategy

- Verify header badges show only selected ecosystems on all pages including /ecosystems directory
- Verify breadcrumb shows correct count/name on all pages
- Verify CRUD forms pre-populate correct ecosystem_id from selection
- Verify multi-ecosystem picker appears when 2+ ecosystems selected
- Verify ILIKE search cannot inject wildcards
- Verify ecosystem edit/update returns 403 for unauthorized users
- Verify `get_scoped_entity()` denies access when no ecosystem is selected
- Verify emergency and safeguards POST actions include ecosystem_id
- Verify chat agent context reflects all selected ecosystems
