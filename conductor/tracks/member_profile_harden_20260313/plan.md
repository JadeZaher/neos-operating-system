# Implementation Plan: Member Profile Flow -- Review & Harden

**Track ID:** `member_profile_harden_20260313`
**Type:** Bug (Review/Harden)
**Estimated effort:** 4-6 hours across 4 phases

## Overview

This plan is organized into 4 phases:

1. **Audit & Test Infrastructure** -- Set up member-specific test fixtures and write failing tests for all known bugs and CRUD paths.
2. **Fix Async/Session Bugs** -- Resolve lazy-load errors, session scoping issues, and detached object access.
3. **Harden Templates & Guards** -- Audit all template attribute accesses, add defensive guards, verify ownership logic.
4. **End-to-End Validation** -- Verify signup-to-profile flow, skills/interests round-trip, and regression check.

Each task follows TDD: write a failing test first, implement the fix, then verify.

---

## Phase 1: Audit & Test Infrastructure

**Goal:** Establish comprehensive test coverage for member views so that all subsequent bug fixes and hardening changes can be verified by tests.

### Tasks:

- [ ] **Task 1.1: Create `test_members.py` with authenticated test fixtures**

  Create `agent/tests/test_members.py`. Set up fixtures that:
  - Create an in-memory SQLite DB with `expire_on_commit=False`.
  - Seed an Ecosystem, two Members (owner and other), and a MemberOnboarding record for the owner.
  - Create a Sanic test app with the members blueprint registered.
  - Provide a helper to simulate authentication by setting `request.ctx.member`, `request.ctx.ecosystems`, and `request.ctx.selected_ecosystem_ids` via a request middleware on the test app.

  TDD: Write the fixture, then write a trivial test (`test_fixture_works`) that verifies the seed data is queryable. Run it to confirm the fixture produces a working test app.

- [ ] **Task 1.2: Write failing tests for member detail page (FR-1, FR-4)**

  Write tests in `test_members.py`:
  - `test_member_detail_own_profile_200` -- GET own profile returns 200 with display name, skills, interests, ecosystem.
  - `test_member_detail_other_profile_200` -- GET another member's profile returns 200 without "Edit Profile" button.
  - `test_member_detail_nonexistent_404` -- GET with a random UUID returns 404.
  - `test_member_detail_no_onboarding_200` -- GET profile for member with no MemberOnboarding record returns 200 (no crash on None onboarding).
  - `test_member_detail_with_onboarding_200` -- GET profile for member with onboarding record shows completion percentage.

  TDD: These tests will likely fail if the lazy-load bug still exists. That is expected -- they document the bugs.

- [ ] **Task 1.3: Write failing tests for edit/update ownership guards (FR-3)**

  Write tests:
  - `test_edit_form_own_profile_200` -- GET `/members/<own-id>/edit` returns 200 with pre-populated form.
  - `test_edit_form_other_profile_redirects` -- GET `/members/<other-id>/edit` returns 302 redirect to detail page.
  - `test_update_own_profile_redirects_to_detail` -- POST `/members/<own-id>` with valid data returns 302.
  - `test_update_other_profile_redirects` -- POST `/members/<other-id>` with data returns 302 redirect (no update).
  - `test_edit_form_unauthenticated_redirects` -- GET `/members/<id>/edit` with no `request.ctx.member` redirects.

  TDD: Write tests, run to see which pass and which fail. Document failures.

- [ ] **Task 1.4: Write tests for skills/interests round-trip (FR-5)**

  Write tests:
  - `test_update_skills_offered_stores_json_list` -- POST with `skills_offered=facilitation, design` stores `["facilitation", "design"]`.
  - `test_update_interests_stores_json_list` -- POST with `interests=permaculture, governance` stores `["permaculture", "governance"]`.
  - `test_update_clear_skills_sets_null` -- POST with empty `skills_offered` field stores `None`.
  - `test_detail_shows_skills_tags` -- GET detail page for member with skills shows the skill text in the response.
  - `test_detail_hides_empty_skills` -- GET detail page for member with no skills does not contain "Skills Offered" heading.

  TDD: Write tests first. These test the data round-trip through `_parse_comma_list()` and template rendering.

- [ ] **Task 1.5: Write tests for remaining CRUD paths (FR-4)**

  Write tests:
  - `test_member_directory_200` -- GET `/members` returns 200 with member names.
  - `test_member_create_form_200` -- GET `/members/new` returns 200.
  - `test_member_create_valid_redirects` -- POST `/members` with valid data redirects to detail.
  - `test_member_create_bad_ecosystem_403` -- POST `/members` with invalid ecosystem_id returns 403.
  - `test_status_transition_valid_redirects` -- POST `/members/<id>/status` with `new_status=inactive` redirects.
  - `test_status_transition_missing_status_400` -- POST `/members/<id>/status` without `new_status` returns 400.

  TDD: Write all tests, run suite. Some should pass with existing code; document any failures.

- [ ] **Verification: Run full test suite, document pass/fail matrix** [checkpoint marker]

  Run `pytest agent/tests/test_members.py -v`. Create a summary of which tests pass and which fail. The failing tests become the bug fix backlog for Phase 2 and 3.

---

## Phase 2: Fix Async/Session Bugs

**Goal:** Fix all 500 errors caused by async lazy-loading and detached object access.

### Tasks:

- [ ] **Task 2.1: Verify and fix `session.refresh()` in detail route (FR-1)**

  In `members.py` `detail()`, verify that `session.refresh(member, ["ecosystem", "onboarding"])` correctly eagerly loads both relationships. Confirm behavior when:
  - Member has an ecosystem (should always) -- `member.ecosystem` is populated.
  - Member has an onboarding record -- `member.onboarding` is populated.
  - Member has NO onboarding record -- `member.onboarding` is `None` (not a lazy proxy).

  If `session.refresh()` does not resolve `None` onboarding correctly (i.e., it still leaves a lazy proxy), switch to explicit query:
  ```python
  # After get_scoped_entity:
  await session.refresh(member, ["ecosystem", "onboarding"])
  ```
  Or use `selectinload` in the initial query. The key is that after the session block exits, `member.onboarding` must be either a loaded `MemberOnboarding` object or `None`, never a lazy proxy.

  TDD: `test_member_detail_no_onboarding_200` and `test_member_detail_with_onboarding_200` should now pass.

- [ ] **Task 2.2: Verify `current_user` column-only access pattern (FR-2)**

  Audit `base.html` and confirm every `current_user` access is a column attribute:
  - `current_user.id` -- column (safe)
  - `current_user.display_name` -- column (safe)
  - `current_user.profile` -- column (safe)

  Audit `detail.html` line 22: `current_user.id == member.id` -- both are column UUIDs (safe).

  Verify by checking that the middleware session uses `expire_on_commit=False` or that the session factory does. Check `main.py` line 197: `async with app.ctx.db() as db:` -- need to verify what `app.ctx.db` is (a `sessionmaker` or a context manager). If it uses default `expire_on_commit=True`, the member object's columns may be expired after commit, but since we never commit in the middleware session (we only read), the columns should remain accessible.

  Action: Add a code comment in `_rendering.py` at the `current_user` assignment line documenting that only column attributes are safe for template access. Example:
  ```python
  # current_user is a detached Member ORM instance from the auth middleware session.
  # Only column attributes (id, display_name, profile, etc.) are safe for template access.
  # Relationship attributes (ecosystem, onboarding) will raise MissingGreenlet.
  context["current_user"] = member
  ```

  TDD: All `base.html`-involving tests should pass without `MissingGreenlet` errors.

- [ ] **Task 2.3: Ensure edit form does not trigger lazy loads (FR-1)**

  In `members.py` `edit_form()`, the member object is loaded via `get_scoped_entity()` which calls `session.get()`. The form template accesses:
  - `member.display_name`, `member.member_id`, `member.profile`, `member.phone` -- all columns (safe within session).
  - `member.skills_offered`, `member.skills_needed`, `member.interests` -- all JSON columns (safe within session).
  - `member.ecosystem_id` -- column (safe).
  - `member.notes` -- column (safe).

  Since the template is rendered inside `await render(...)` which is called AFTER the `async with session:` block exits, the member object is detached. However, all accessed attributes are columns, so they should be cached.

  Verify: The `edit_form()` handler renders the template OUTSIDE the session block (line 251). This means `member` is detached. All column accesses should be safe IF `expire_on_commit=False` is set, or if no commit happened in the session. Since `get_scoped_entity` only reads (no commit), columns should be cached.

  If any test fails here, the fix is to either:
  (a) Render inside the session block, or
  (b) Ensure the session factory uses `expire_on_commit=False`.

  TDD: `test_edit_form_own_profile_200` should pass.

- [ ] **Verification: All Phase 1 tests related to 500 errors now pass** [checkpoint marker]

  Run `pytest agent/tests/test_members.py -v -k "detail or edit_form"`. All should pass.

---

## Phase 3: Harden Templates & Guards

**Goal:** Audit every template attribute access for safety, add defensive guards, and verify ownership logic edge cases.

### Tasks:

- [ ] **Task 3.1: Audit `detail.html` for unsafe attribute access**

  Review every line of `detail.html` and categorize each attribute access:

  **Line 2** (`member.display_name if member`): Safe -- guarded.
  **Line 13** (`member.display_name`): Unsafe if `member` is None. The route handler returns a different template context with `member=None` for 404, but the template block title still runs. Add guard: `{{ member.display_name if member else 'Not Found' }}` (already present on line 2).
  **Line 19-20** (`member.display_name`, `member.member_id`): These are inside `{% block content %}` which only renders when member is truthy because the route returns early on 404. But the error template also uses `detail.html` with `member=None`. Add a top-level guard:
  ```jinja2
  {% if member %}
    ... all content ...
  {% else %}
    <div class="...">{{ error | default('Member not found.') }}</div>
  {% endif %}
  ```

  **Lines 66-68** (`member.onboarding is defined and member.onboarding and member.onboarding.completion_percentage is defined`): This guard chain is correct. If `onboarding` is `None`, the chain short-circuits.
  **Lines 363-389** (`member.onboarding is defined and member.onboarding`): Same pattern, correct.

  Action: Wrap the entire `{% block content %}` body in `{% if member %}...{% else %}` to handle the `member=None` error case cleanly. Move the error display into the `{% else %}` block.

  TDD: `test_member_detail_nonexistent_404` should return 404 with "Member not found" text and no template errors.

- [ ] **Task 3.2: Audit `detail.html` for the `transitions` variable name mismatch**

  The route handler passes `transitions=transitions` to the template context. But the template on line 341 checks `{% if status_transitions is defined and status_transitions %}` and iterates `{% for t in status_transitions %}`. This is a variable name mismatch -- the route passes `transitions` but the template expects `status_transitions`.

  Fix: Either rename the variable in the route handler to `status_transitions=transitions`, or rename the template references to `transitions`. Prefer renaming in the route handler since the template name is more descriptive.

  TDD: Write a test `test_member_detail_with_transitions_shows_history` that creates a MemberStatusTransition record and verifies "Status History" appears in the response. This test would fail before the fix due to the name mismatch.

- [ ] **Task 3.3: Audit `form.html` for edge cases**

  Review `form.html`:
  - **Line 43** (`member.ecosystem_id`): When editing, this is a hidden field. When creating (`member=None`), it's empty. The create route requires `ecosystem_id` from the form. For edit, the ecosystem_id should be preserved. Verify the hidden field is populated correctly for both create and edit flows.
  - **Lines 118, 132, 147** (`member.skills_offered | join(', ')`): The `join` filter on a `None` value would fail. The guard `if member is defined and member and member.skills_offered` protects this. Verify this guard is sufficient.

  No code changes expected if guards are correct. Verify with tests.

  TDD: `test_edit_form_own_profile_200` should pass and show pre-populated skills.

- [ ] **Task 3.4: Verify `_is_own_profile()` edge cases**

  Test that `_is_own_profile()`:
  - Returns `True` when `request.ctx.member.id == member_id`.
  - Returns `False` when `request.ctx.member.id != member_id`.
  - Returns `False` when `request.ctx.member` is `None`.
  - Returns `False` when `request.ctx` has no `member` attribute.

  These are unit tests that do not need the full Sanic app. Add them to `test_members.py`.

  TDD: Write tests, implement any fixes needed. The current code (`getattr(request.ctx, "member", None)`) handles the missing attribute case. Verify the None case.

- [ ] **Task 3.5: Add `member=None` error guard to `detail.html`**

  Implement the wrap from Task 3.1. The entire content block should be gated:

  ```jinja2
  {% block content %}
  {% if error is defined and error %}
  <div class="...error alert...">{{ error }}</div>
  {% endif %}

  {% if member %}
    ... existing content ...
  {% else %}
    {% if not error %}
    <p class="text-neos-muted">Member not found.</p>
    {% endif %}
  {% endif %}
  {% endblock %}
  ```

  This prevents any `member.X` access when member is None.

  TDD: `test_member_detail_nonexistent_404` passes cleanly.

- [ ] **Verification: All tests pass, no template rendering errors** [checkpoint marker]

  Run `pytest agent/tests/test_members.py -v`. All tests green. Manually verify no Jinja2 `UndefinedError` or `TypeError` in test output.

---

## Phase 4: End-to-End Validation

**Goal:** Verify the complete signup-to-profile flow and ensure no regressions in other views.

### Tasks:

- [ ] **Task 4.1: Write signup-to-profile integration test (FR-7)**

  Write a test that simulates the full flow:
  1. POST `/auth/verify` with a new DID (mocking `verify_did_signature` to return True).
  2. Verify a Member record was created.
  3. GET `/dashboard/members/<new-member-id>` with the authenticated session.
  4. Verify 200 response with the auto-generated display name.
  5. GET `/dashboard/members/<new-member-id>/edit` -- verify 200 (own profile).
  6. POST `/dashboard/members/<new-member-id>` with updated display_name and skills.
  7. GET `/dashboard/members/<new-member-id>` -- verify updated values in response.

  This is a longer integration test. It may require setting up the full app factory or a sufficiently complete test app with auth routes.

  TDD: Write the test first. It exercises the full chain from auth through member CRUD.

- [ ] **Task 4.2: Write skills/interests complete round-trip test (FR-5)**

  Write a test that:
  1. Seeds a member with no skills/interests.
  2. GET detail page -- verify no "Skills Offered" section.
  3. POST update with `skills_offered=facilitation, design`, `interests=permaculture`.
  4. GET detail page -- verify "facilitation" and "design" appear as tags, "permaculture" appears.
  5. POST update with `skills_offered=` (empty), `interests=` (empty).
  6. GET detail page -- verify skills and interests sections are gone.

  TDD: Write test, verify it passes with the existing code. If `_parse_comma_list("")` returns `None` (it does, since `if not raw: return None`), the clear path should work.

- [ ] **Task 4.3: Regression test -- existing views still work**

  Verify that the existing `test_views.py` tests all still pass. These test agreements, domains, proposals, and decisions -- they exercise `base.html` and `_rendering.py`.

  Run: `pytest agent/tests/test_views.py -v`. All must pass.

  If any fail due to changes in `_rendering.py` or `base.html`, fix the regressions.

  TDD: Existing tests serve as the regression suite.

- [ ] **Task 4.4: Add documentation comment for async safety pattern**

  Add a docstring or comment block at the top of `members.py` explaining the async session scoping pattern:

  ```python
  # ASYNC SESSION SAFETY NOTES:
  # - request.ctx.member (current_user) is loaded in auth middleware and is DETACHED
  #   from its session. Only column attributes are safe to access.
  # - In route handlers, open a new session to load the target member. Eagerly load
  #   all relationships needed by the template using session.refresh() before exiting
  #   the session block.
  # - Templates must use `{% if X is defined and X %}` guards for optional relationships.
  ```

  No TDD needed -- this is a documentation task.

- [ ] **Verification: Full test suite passes, including regressions** [checkpoint marker]

  Run `pytest agent/tests/ -v`. All tests pass. Summarize:
  - Total tests in `test_members.py`: ~20
  - Total tests in `test_views.py`: unchanged, all pass
  - No 500 errors reproducible via test client
  - Skills/interests round-trip verified
  - Ownership guards verified
  - Error pages render cleanly for 404/500 cases
