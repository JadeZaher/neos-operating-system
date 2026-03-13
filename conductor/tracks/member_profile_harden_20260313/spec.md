# Specification: Member Profile Flow -- Review & Harden

**Track ID:** `member_profile_harden_20260313`
**Type:** Bug (Review/Harden)
**Priority:** P0
**Created:** 2026-03-13

## Overview

Review and harden the member profile flow end-to-end. Fix known bugs (async lazy-loading 500 errors, template context safety), add defensive error handling, validate all CRUD paths and ownership guards, ensure skills/interests/ecosystem display correctly, and verify the signup-to-profile flow works without errors.

## Background

Recent work on the member profile introduced several features in rapid succession:

- `current_user` context injection in `_rendering.py`
- Header in `base.html` uses `current_user.display_name`, `current_user.profile`, `current_user.id`
- My Profile sidebar link referencing `current_user.id`
- `_is_own_profile()` helper and ownership guards on edit/update routes
- POST delegate route for HTML form compatibility
- `_parse_comma_list()` for skills/interests parsing
- `interests` JSON column on Member model + Alembic migration
- Skills/interests comma-separated inputs in form.html
- Conditional edit button, interests tags, ecosystem sidebar in detail.html
- `session.refresh(member, ["ecosystem", "onboarding"])` to eagerly load relationships

These changes were applied incrementally without comprehensive testing. The profile flow now has multiple potential failure points around async session scoping, detached ORM objects, and template attribute access patterns.

## Functional Requirements

### FR-1: Eliminate async lazy-load errors on profile detail page

**Description:** The member detail page (`GET /dashboard/members/<id>`) must not raise `MissingGreenlet` or `DetachedInstanceError` when rendering template attributes that traverse ORM relationships.

**Acceptance Criteria:**
- AC-1.1: Visiting any member's profile page returns 200, never 500.
- AC-1.2: The `member.ecosystem` relationship is usable in the template without error.
- AC-1.3: The `member.onboarding` relationship is usable in the template without error (both when an onboarding record exists and when it does not).
- AC-1.4: The `member.onboarding.completion_percentage`, `member.onboarding.facilitator`, `member.onboarding.consent_date`, and `member.onboarding.cooling_off_start` attributes are safely accessible.

**Priority:** P0

### FR-2: Ensure `current_user` survives session closure for column-only access

**Description:** The `current_user` object (loaded in auth middleware from `request.ctx.member`) is used across all templates via the `render()` function. Since the middleware's DB session closes before the route handler runs, any access to `current_user` attributes must only touch already-loaded columns, never trigger lazy-loaded relationships.

**Acceptance Criteria:**
- AC-2.1: `current_user.id`, `current_user.display_name`, `current_user.profile` are accessible in every template without error.
- AC-2.2: `base.html` renders the header (My Profile link, display name, profile badge, sign-out form) without error for authenticated users.
- AC-2.3: `base.html` renders correctly when `current_user` is `None` (unauthenticated or public routes).
- AC-2.4: Accessing `current_user.ecosystem` or `current_user.onboarding` (relationship attributes) from templates is either guarded or eagerly loaded.

**Priority:** P0

### FR-3: Ownership guards on edit and update routes

**Description:** Only the owner of a profile may edit it. Other authenticated users viewing someone else's profile must not see the edit button and must be redirected if they attempt to access the edit form or submit an update.

**Acceptance Criteria:**
- AC-3.1: `GET /dashboard/members/<id>/edit` redirects to the detail page when the logged-in user does not own the profile.
- AC-3.2: `PUT /dashboard/members/<id>` (and its POST delegate) redirects to the detail page when the logged-in user does not own the profile.
- AC-3.3: The "Edit Profile" button in `detail.html` only renders when `current_user.id == member.id`.
- AC-3.4: `_is_own_profile()` correctly handles the case when `request.ctx.member` is `None` (returns `False`).

**Priority:** P0

### FR-4: All CRUD paths return correct status codes and content

**Description:** Every member route must handle success and failure gracefully with appropriate HTTP status codes and user-facing messages.

**Acceptance Criteria:**
- AC-4.1: `GET /dashboard/members` returns 200 with member directory list.
- AC-4.2: `GET /dashboard/members/new` returns 200 with empty form.
- AC-4.3: `POST /dashboard/members` with valid data creates a member and redirects (302) to the detail page.
- AC-4.4: `POST /dashboard/members` with invalid ecosystem_id returns 403 with error message.
- AC-4.5: `GET /dashboard/members/<id>` returns 200 for an existing member.
- AC-4.6: `GET /dashboard/members/<nonexistent-id>` returns 404 with "Member not found" message.
- AC-4.7: `GET /dashboard/members/<id>/edit` returns 200 when user owns the profile.
- AC-4.8: `PUT /dashboard/members/<id>` (or POST delegate) with valid data updates the member and redirects (302).
- AC-4.9: `POST /dashboard/members/<id>/status` with valid `new_status` transitions the status and redirects.
- AC-4.10: `POST /dashboard/members/<id>/status` without `new_status` returns 400.
- AC-4.11: Database errors on any route return 500 with a user-friendly error message, not a stack trace.

**Priority:** P0

### FR-5: Skills and interests display correctly

**Description:** Skills offered, skills needed, and interests (all JSON list columns) must render as tag badges on the profile detail page and pre-populate as comma-separated values in the edit form.

**Acceptance Criteria:**
- AC-5.1: When `skills_offered` is a non-empty list, the detail page shows each skill as a tag badge.
- AC-5.2: When `skills_needed` is a non-empty list, the detail page shows each skill as a tag badge.
- AC-5.3: When `interests` is a non-empty list, the detail page shows each interest as a purple tag badge.
- AC-5.4: When any of skills_offered, skills_needed, or interests is `None` or empty, the corresponding section does not render (no empty card).
- AC-5.5: The edit form pre-populates skills_offered, skills_needed, and interests as comma-separated strings via `| join(', ')`.
- AC-5.6: Submitting the edit form with comma-separated values correctly parses them via `_parse_comma_list()` and stores as JSON lists.
- AC-5.7: Submitting the edit form with empty skills/interests fields clears the stored values (sets to `None`).

**Priority:** P1

### FR-6: Ecosystem displays correctly in profile sidebar

**Description:** The ecosystem card in the profile sidebar must show the ecosystem name, location, and status without triggering lazy-load errors.

**Acceptance Criteria:**
- AC-6.1: The ecosystem card renders with the ecosystem name, location (if present), and status.
- AC-6.2: The ecosystem card does not render if `ecosystem` is `None` or not passed to the template.
- AC-6.3: The ecosystem data is eagerly loaded in the `detail()` route handler within the active session.

**Priority:** P1

### FR-7: Signup-to-profile flow works end-to-end

**Description:** A new user who authenticates via DID challenge-response should be automatically created as a Member and immediately be able to view and edit their own profile.

**Acceptance Criteria:**
- AC-7.1: After successful DID verification, a new Member record is created with `current_status="active"`.
- AC-7.2: The new member is redirected to the dashboard (or can navigate to their profile).
- AC-7.3: The new member can view their own profile page without error.
- AC-7.4: The new member sees the "Edit Profile" button on their own profile.
- AC-7.5: The new member can edit their profile (display_name, profile, skills, interests) and save successfully.

**Priority:** P1

## Non-Functional Requirements

### NFR-1: No unhandled exceptions in template rendering

All template attribute accesses on ORM objects must be safe against `DetachedInstanceError` and `MissingGreenlet`. Every relationship access must be either eagerly loaded or wrapped in `is defined` / null guards.

### NFR-2: Defensive error handling on all routes

Every route handler must wrap database operations in try/except blocks (already present, but must be verified as sufficient). Error responses must use the appropriate template with a user-friendly `error` message.

### NFR-3: Test coverage for member views

All CRUD paths must have corresponding test cases. Tests must use the existing test infrastructure (in-memory SQLite, ASGI test client) and authenticate by setting `request.ctx.member` appropriately.

### NFR-4: No regression in existing views

Changes to `_rendering.py`, `base.html`, or the auth middleware must not break any existing dashboard view (agreements, domains, proposals, decisions).

## User Stories

### US-1: View own profile
**As** an authenticated NEOS member
**I want to** visit my profile page
**So that** I can see my information, skills, interests, and ecosystem membership.

**Scenarios:**
- **Given** I am logged in and click "My Profile" in the sidebar, **When** the page loads, **Then** I see my display name, member ID, profile type, skills, interests, and ecosystem card without errors.

### US-2: Edit own profile
**As** an authenticated NEOS member
**I want to** edit my profile details
**So that** I can update my skills, interests, and other information.

**Scenarios:**
- **Given** I am on my own profile page, **When** I click "Edit Profile", **Then** I see the edit form with my current data pre-populated.
- **Given** I am on the edit form, **When** I change my skills to "facilitation, design" and save, **Then** my profile shows the updated skills as tag badges.
- **Given** I am on the edit form, **When** I clear the interests field and save, **Then** my profile no longer shows the interests section.

### US-3: View another member's profile
**As** an authenticated NEOS member
**I want to** view another member's profile
**So that** I can see their skills and interests for collaboration.

**Scenarios:**
- **Given** I am logged in, **When** I visit another member's profile, **Then** I see their information but do NOT see an "Edit Profile" button.
- **Given** I am logged in, **When** I manually navigate to `/dashboard/members/<other-id>/edit`, **Then** I am redirected to their detail page.

### US-4: New member signup flow
**As** a new user
**I want to** authenticate with my DID and access my profile
**So that** I can set up my presence in the ecosystem.

**Scenarios:**
- **Given** I complete DID authentication for the first time, **When** I navigate to my profile, **Then** I see my auto-generated display name and can edit my profile.

## Technical Considerations

### Async session scoping (critical)

The auth middleware (`main.py` lines 236-257) loads `request.ctx.member` inside an `async with app.ctx.db() as db:` block. Once that block exits, the DB session closes. The member ORM object becomes detached. Column values that were loaded during the query remain accessible (they are cached in the instance dict). Relationship attributes (e.g., `member.ecosystem`, `member.onboarding`) are NOT loaded and will raise `MissingGreenlet` if accessed.

**Implication for `current_user`:** In `_rendering.py`, `current_user` is set to `request.ctx.member`. Templates must only access column attributes on `current_user`, never relationships. The `base.html` template currently accesses `current_user.id`, `current_user.display_name`, and `current_user.profile` -- all columns, so this is safe. But any future template that accesses `current_user.ecosystem` would fail.

**Implication for `detail()` route:** The detail route opens its own session and calls `session.refresh(member, ["ecosystem", "onboarding"])`. The member object used in the template is from this session, NOT the middleware session. This is correct. However, the template also accesses `current_user` (from middleware), which is a different object. The `current_user.id == member.id` comparison on line 22 of detail.html compares two UUID objects and should work since UUIDs are value-compared.

### Template safety patterns

- `{% if X is defined and X %}` -- guards against both undefined and None
- `{% if X.attr %}` -- only safe when X is guaranteed non-None
- Relationship traversal like `member.onboarding.facilitator` requires that both `member.onboarding` is loaded (not lazy) and is not None

### Middleware session produces `expire_on_commit=True` (default)

The middleware's session factory may use the default `expire_on_commit=True`. After `session.commit()` or session close, all attributes on the loaded objects become expired. However, since `expire_on_commit` only takes effect on commit (not session close), and the middleware session may use `expire_on_commit=False` (needs verification). The `_setup_db` in tests uses `expire_on_commit=False`. The production session factory must match.

## Out of Scope

- Profile picture upload
- AZPO membership display (no data source yet)
- Role assignments display (no join table yet)
- Participation history timeline (no data source yet)
- Advanced profile search/filtering
- Member deletion
- Password/credential management (handled by DID auth layer)

## Open Questions

1. **Q:** Should the middleware eagerly load specific columns on `current_user` to make it explicit which attributes are safe? Or is the current pattern (relying on SQLAlchemy's detached instance column caching) sufficient?
   **Current answer:** The current pattern works but is fragile. A comment in `_rendering.py` documenting which `current_user` attributes are safe for template access would help prevent future regressions.

2. **Q:** Should `_is_own_profile()` use `str(current_user.id) == str(member_id)` for safety against UUID type mismatches (e.g., SQLite storing CHAR(32) vs PostgreSQL storing native UUID)?
   **Current answer:** The GUID type normalizes all values to `uuid.UUID` in `process_result_value`, so direct comparison should be safe. A test should verify this.

3. **Q:** The `status_transition` route does not have an ownership guard. Should only the profile owner (or admins) be able to change their own status?
   **Current answer:** For now, status transitions are a governance action (not self-service), so no ownership guard is needed. This should be revisited when role-based access control is implemented.
