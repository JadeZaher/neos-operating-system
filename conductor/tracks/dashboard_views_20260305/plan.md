# Implementation Plan: Datastar Dashboard & Views

**Track ID:** dashboard_views_20260305
**Depends On:** agent_foundation_20260305
**Total Phases:** 5
**Total Tasks:** 24
**Estimated Duration:** 3-4 days

---

## Overview

This plan builds the NEOS governance dashboard in five phases, starting with the foundational base layout and progressing through each entity type. Each phase ends with a verification checkpoint. The approach is outside-in: build the shell first, then fill in each entity's views.

All file paths are relative to `agent/src/neos_agent/` unless otherwise noted.

**Phase order:**
1. Base Layout and Navigation (foundation for all views)
2. Agreement and Domain Views (core governance entities)
3. Member and Role Views (participant management)
4. Proposal ACT Lifecycle Views (most complex interaction)
5. Decision Records and Search (reference and precedent system)

---

## Phase 1: Base Layout and Navigation

**Goal:** Establish the template directory structure, base layout with Datastar integration, navigation, theming, and the dashboard home page. After this phase, the app has a navigable shell with a working dashboard home.

### Tasks:

- [ ] **Task 1.1: Create template directory structure and partials**

  Create the full directory tree under `templates/` with all subdirectories. Write the three partial templates that are used across all pages.

  **TDD Cycle:**
  - **Red:** Write a test that asserts the Sanic app can locate and render `base.html`, `partials/pagination.html`, `partials/notification.html`, and `partials/loading.html` without error. The test should verify that each partial contains its expected root element ID.
  - **Green:** Create directory structure:
    ```
    templates/
      base.html
      dashboard/
        index.html
        agreements/
        domains/
        members/
        proposals/
        decisions/
      partials/
        pagination.html
        notification.html
        loading.html
    ```
    Write `partials/pagination.html` with: prev/next buttons, page number display, `data-signals` for `currentPage` and `totalPages`, `data-on:click` triggers for `@get` with page parameter.
    Write `partials/notification.html` with: toast container (fixed top-right), `data-show` bound to notifications signal, auto-dismiss logic via `data-on:load` with timeout.
    Write `partials/loading.html` with: spinner element, `data-show="$isFetching"` to display during active SSE requests.
  - **Refactor:** Ensure partials use consistent `id` attributes for SSE targeting.

  **Files:**
  - `templates/partials/pagination.html`
  - `templates/partials/notification.html`
  - `templates/partials/loading.html`

---

- [ ] **Task 1.2: Write base.html with Datastar, navigation, and CSS custom properties**

  Create the root layout template that all pages extend. This is the most critical template -- every other page inherits from it.

  **TDD Cycle:**
  - **Red:** Write a test that renders `base.html` with a child template and asserts: (1) the HTML contains the Datastar script tag, (2) CSS custom properties `--neos-primary` through `--neos-shadow` are defined, (3) navigation contains links to all six sections, (4) the `{% block content %}` region is present, (5) partials for notification and loading are included.
  - **Green:** Write `base.html` with:
    - HTML5 doctype, charset, viewport meta
    - `<title>{% block title %}NEOS Dashboard{% endblock %}</title>`
    - `<style>` block with `:root { --neos-primary: #2563eb; --neos-secondary: #7c3aed; ... }` (full property set from FR-1)
    - Datastar script tag: `<script type="module" src="https://cdn.jsdelivr.net/npm/@starfederation/datastar@1"></script>`
    - `<body>` with `data-signals` block for global signals (activePage, currentEcosystem, notifications)
    - `<aside>` navigation sidebar with `<nav>` landmark, links to /dashboard, /dashboard/agreements, /dashboard/domains, /dashboard/members, /dashboard/proposals, /dashboard/decisions
    - Active page highlighting: `data-class-active="activePage === 'agreements'"` on each nav link
    - Ecosystem selector `<select>` in header with `data-bind="currentEcosystem"`
    - `{% include "partials/notification.html" %}`
    - `{% include "partials/loading.html" %}`
    - `<main>{% block content %}{% endblock %}</main>`
    - `{% block signals %}{% endblock %}` for page-specific signal initialization
    - `{% block styles %}{% endblock %}` for page-specific CSS
    - `{% block scripts %}{% endblock %}` for page-specific JS
    - Responsive sidebar: CSS media query at 768px to collapse sidebar to hamburger
    - ARIA landmarks on all structural elements
  - **Refactor:** Extract CSS custom properties into a clear, documented block. Verify keyboard navigation order.

  **Files:**
  - `templates/base.html`

---

- [ ] **Task 1.3: Write views/dashboard.py with main dashboard route**

  Create the dashboard blueprint with the home route that serves summary data and activity feed.

  **TDD Cycle:**
  - **Red:** Write a test that: (1) requests GET `/dashboard` and asserts HTTP 200, (2) asserts the response contains summary card elements (ids: `agreement-count`, `proposal-count`, `decision-count`, `member-count`), (3) asserts the response contains an activity feed element (id: `activity-feed`).
  - **Green:** Write `views/dashboard.py`:
    ```python
    from sanic import Blueprint
    from datastar_py.sanic import datastar_response, read_signals
    from datastar_py import ServerSentEventGenerator as SSE

    dashboard_bp = Blueprint("dashboard", url_prefix="/dashboard")

    @dashboard_bp.route("/")
    async def dashboard_home(request):
        # Query summary counts from database
        # Query last 10 governance actions for activity feed
        # Render dashboard/index.html with context
        return await render("dashboard/index.html", ...)

    @dashboard_bp.route("/summary")
    @datastar_response
    async def dashboard_summary(request):
        # SSE endpoint for summary card updates
        # Query counts, render partial, yield patch
        yield SSE.patch_elements(html)

    @dashboard_bp.route("/activity")
    @datastar_response
    async def activity_feed(request):
        # SSE endpoint for activity feed updates
        yield SSE.patch_elements(html)
    ```
    Write `views/__init__.py` to collect and export all blueprints.
  - **Refactor:** Ensure query functions are async and use the session pattern from agent_foundation.

  **Files:**
  - `views/__init__.py`
  - `views/dashboard.py`

---

- [ ] **Task 1.4: Write templates/dashboard/index.html with summary cards and activity feed**

  Create the dashboard home page template with summary cards, activity feed, and quick action buttons.

  **TDD Cycle:**
  - **Red:** Write a test that renders `dashboard/index.html` with mock context data (counts, activity list) and asserts: (1) summary cards display correct counts, (2) activity feed shows items with timestamps, (3) quick action buttons link to /dashboard/agreements/new, /dashboard/proposals/new, /dashboard/decisions/search.
  - **Green:** Write `dashboard/index.html`:
    - Extends `base.html`, sets `{% block title %}Dashboard - NEOS{% endblock %}`
    - Sets `{% block signals %}data-signals='{"activePage": "dashboard"}'{% endblock %}`
    - Summary cards section: grid of cards, each with `data-on:load="@get('/dashboard/summary')"` for SSE refresh
    - Each card: icon, label, count value, link to list view
    - Activity feed section with id `activity-feed`: list of recent actions, each with description, actor, relative timestamp, entity link
    - `data-on:load="@get('/dashboard/activity')"` on activity feed for auto-refresh
    - Quick action buttons: "New Agreement" (link), "New Proposal" (link), "Search Precedents" (link)
    - Responsive grid: 3 columns on desktop, 2 on tablet, 1 on mobile
  - **Refactor:** Ensure all cards work as plain links without JavaScript. Ensure timestamps are human-readable.

  **Files:**
  - `templates/dashboard/index.html`

---

- [ ] **Verification: Phase 1** [checkpoint marker]

  1. Start the Sanic app and navigate to `/dashboard`.
  2. Verify the base layout renders with navigation sidebar, ecosystem selector, and loading indicator.
  3. Verify navigation links highlight the active page.
  4. Verify summary cards display (with placeholder data if database is empty).
  5. Verify the page renders correctly with JavaScript disabled (static HTML).
  6. Verify responsive layout: resize browser below 768px and confirm sidebar collapses.
  7. Verify keyboard navigation through the sidebar and summary cards.

---

## Phase 2: Agreement and Domain Views

**Goal:** Build full CRUD views for agreements and domains. After this phase, users can browse, create, edit, and inspect agreements and domains through the dashboard.

### Tasks:

- [ ] **Task 2.1: Write views/agreements.py -- list, detail, create, update routes**

  Create the agreements blueprint with all routes and SSE endpoints for filtering.

  **TDD Cycle:**
  - **Red:** Write tests that:
    - GET `/dashboard/agreements` returns 200 with agreement list HTML.
    - GET `/dashboard/agreements` with Datastar signals `{"filterType": "access", "filterStatus": "active"}` returns filtered results via SSE.
    - GET `/dashboard/agreements/new` returns 200 with form HTML.
    - POST `/dashboard/agreements` with valid data creates an agreement and returns redirect/success.
    - GET `/dashboard/agreements/{id}` returns 200 with agreement detail HTML.
    - GET `/dashboard/agreements/{id}/edit` returns 200 with pre-populated form.
    - PUT `/dashboard/agreements/{id}` updates the agreement.
    - GET `/dashboard/agreements/{id}/history` returns version history HTML.
  - **Green:** Write `views/agreements.py` with:
    - `agreements_bp = Blueprint("agreements", url_prefix="/dashboard/agreements")`
    - `agreement_list` -- renders list with initial data; SSE variant reads signals and patches.
    - `agreement_detail` -- queries agreement by ID with related data (ratification, amendments).
    - `agreement_create_form` -- renders empty form.
    - `agreement_create` -- validates and persists new agreement.
    - `agreement_edit_form` -- renders form with existing data.
    - `agreement_update` -- validates and updates existing agreement.
    - `agreement_history` -- queries version history for agreement.
    - `agreement_filter` -- `@datastar_response` SSE endpoint for filtering.
  - **Refactor:** Extract common query patterns. Ensure all routes handle not-found gracefully.

  **Files:**
  - `views/agreements.py`

---

- [ ] **Task 2.2: Write agreement templates (list, detail, form, history)**

  Create all four agreement templates with Datastar interactivity.

  **TDD Cycle:**
  - **Red:** Write template rendering tests with mock data asserting: (1) list.html renders a table/cards with agreement data, (2) detail.html shows all agreement fields including status badge and ratification history, (3) form.html has all required form fields with correct input types, (4) history.html shows version timeline.
  - **Green:**
    - `agreements/list.html`: extends base, filter bar with `data-bind` selects (type, status, domain), `data-on:change="@get('/dashboard/agreements/filter')"`, search input with `data-on:input.debounce_300ms`, table/card list with id for SSE patching, pagination include.
    - `agreements/detail.html`: extends base, agreement title, type badge, status badge (color-coded), domain link, full text (rendered), affected parties list, ratification record (table of positions with timestamps), amendment history (linked list), review schedule with countdown, action buttons for status transitions.
    - `agreements/form.html`: extends base, conditional title ("New Agreement" vs "Edit Agreement" via `is_edit`), type selector, title input, textarea for text, affected parties multi-select, domain dropdown, hierarchy level display, review date input, rationale textarea, submit button with `data-on:click.prevent="@post('/dashboard/agreements')"` and standard form action fallback.
    - `agreements/history.html`: extends base, vertical timeline of versions, each with version number, date, change summary, diff display (old/new side by side).
  - **Refactor:** Ensure form has both Datastar submit and standard POST fallback. Status badges include text labels (not just color).

  **Files:**
  - `templates/dashboard/agreements/list.html`
  - `templates/dashboard/agreements/detail.html`
  - `templates/dashboard/agreements/form.html`
  - `templates/dashboard/agreements/history.html`

---

- [ ] **Task 2.3: Write views/domains.py -- list, detail, create routes**

  Create the domains blueprint with routes for the S3 11-element domain contract views.

  **TDD Cycle:**
  - **Red:** Write tests that:
    - GET `/dashboard/domains` returns 200 with domain list.
    - GET `/dashboard/domains/{id}` returns 200 with all 11 elements displayed.
    - GET `/dashboard/domains/new` returns 200 with the guided form.
    - POST `/dashboard/domains` creates a domain.
    - GET `/dashboard/domains/{id}/edit` returns pre-populated form.
  - **Green:** Write `views/domains.py` with:
    - `domains_bp = Blueprint("domains", url_prefix="/dashboard/domains")`
    - `domain_list` -- queries active domains with steward and health data.
    - `domain_detail` -- queries domain with all 11 elements, assignment history, adjacent domains.
    - `domain_create_form` -- renders guided form.
    - `domain_create` -- validates all 11 elements and persists.
    - `domain_edit_form` -- renders form with existing data.
    - `domain_update` -- validates and updates.
    - `domain_filter` -- SSE filter endpoint.
  - **Refactor:** Ensure constraints validation warns on vague constraint text.

  **Files:**
  - `views/domains.py`

---

- [ ] **Task 2.4: Write domain templates (list, detail, form)**

  Create domain templates with the 11-element structured display.

  **TDD Cycle:**
  - **Red:** Write template rendering tests asserting: (1) list.html shows domain cards with steward and status, (2) detail.html renders all 11 labeled elements with constraints visually prominent, (3) form.html has 11 input sections with help text.
  - **Green:**
    - `domains/list.html`: extends base, card grid with domain name (purpose), steward name, delegating body, status badge, health indicator (green/yellow/red based on last review), filter bar for status and delegating body.
    - `domains/detail.html`: extends base, domain header (name, version, status badge), 11-element layout in a structured grid/accordion. Constraints section has visual emphasis (border, background color). Current steward with assignment date. Assignment history table. Amendment history. Adjacent domains as clickable links. Dependency list (domains this one depends on, domains depending on this one).
    - `domains/form.html`: extends base, guided form with 11 numbered sections. Each section has: element name as heading, help text explaining what to write (drawn from domain-mapping skill), input field (textarea for most, specific inputs for metrics/schedule). Constraints section has a warning callout: "Constraints must be specific -- describe what the domain CANNOT do." Submit with validation.
  - **Refactor:** Ensure the 11-element layout is scannable (not a wall of text). Use collapsible sections for long content.

  **Files:**
  - `templates/dashboard/domains/list.html`
  - `templates/dashboard/domains/detail.html`
  - `templates/dashboard/domains/form.html`

---

- [ ] **Task 2.5: Add SSE filtering for agreements (type, status, domain filters)**

  Wire up the Datastar SSE filtering flow end-to-end for agreements, ensuring filters update the list without page reload.

  **TDD Cycle:**
  - **Red:** Write an integration test that: (1) creates 3 agreements with different types, (2) sends a GET to the filter endpoint with signal `filterType=access`, (3) asserts the SSE response contains only the matching agreement, (4) asserts the response is a valid SSE event with `event: datastar-patch-elements`.
  - **Green:** In `views/agreements.py`, implement the filter endpoint:
    ```python
    @agreements_bp.route("/filter")
    @datastar_response
    async def agreement_filter(request):
        signals = await read_signals(request)
        query = build_agreement_query(
            type=signals.get("filterType"),
            status=signals.get("filterStatus"),
            domain=signals.get("filterDomain"),
            search=signals.get("searchText"),
            page=signals.get("currentPage", 1),
        )
        agreements = await query.all()
        html = await render("agreements/_list_body.html", agreements=agreements)
        yield SSE.patch_elements(html)
    ```
    Create `agreements/_list_body.html` as the patchable inner content of the list (without the filter bar).
  - **Refactor:** Extract `build_agreement_query` as a reusable query builder. Ensure empty results show a "No agreements found" message.

  **Files:**
  - `views/agreements.py` (update)
  - `templates/dashboard/agreements/_list_body.html`

---

- [ ] **Task 2.6: Add agreement version history view**

  Implement the version history display for agreements, showing amendments over time.

  **TDD Cycle:**
  - **Red:** Write a test that: (1) creates an agreement, (2) creates 2 amendment records for it, (3) requests `/dashboard/agreements/{id}/history`, (4) asserts the response shows both amendments in chronological order with version numbers.
  - **Green:** In `views/agreements.py`, implement:
    ```python
    @agreements_bp.route("/<agreement_id>/history")
    async def agreement_history(request, agreement_id):
        agreement = await get_agreement(agreement_id)
        versions = await get_agreement_versions(agreement_id)
        return await render("agreements/history.html",
            agreement=agreement, versions=versions)
    ```
    The template renders a vertical timeline with each version showing: version number, date, amendment type (minor/structural), change summary, and a simple old/new text comparison.
  - **Refactor:** Ensure the timeline reads chronologically (oldest first) with the current version highlighted.

  **Files:**
  - `views/agreements.py` (update)
  - `templates/dashboard/agreements/history.html` (update if needed)

---

- [ ] **Verification: Phase 2** [checkpoint marker]

  1. Navigate to `/dashboard/agreements` -- verify list displays, filters work via SSE.
  2. Create a new agreement via `/dashboard/agreements/new` -- verify form validation and successful creation.
  3. View agreement detail -- verify all fields display correctly including status badge and ratification record.
  4. Navigate to `/dashboard/domains` -- verify domain list with steward and status.
  5. View domain detail -- verify all 11 elements are displayed with constraints prominently shown.
  6. Create a domain via the guided form -- verify all 11 elements are captured.
  7. Test agreement filtering with multiple filter combinations.
  8. Verify all views render correctly without JavaScript.

---

## Phase 3: Member and Role Views

**Goal:** Build member directory, detail views with onboarding tracker, and role assignment display. After this phase, users can manage ecosystem participants through the dashboard.

### Tasks:

- [ ] **Task 3.1: Write views/members.py -- directory, detail, onboarding routes**

  Create the members blueprint with routes for directory browsing, member details, and status management.

  **TDD Cycle:**
  - **Red:** Write tests that:
    - GET `/dashboard/members` returns 200 with member directory.
    - GET `/dashboard/members` with signal `filterStatus=active` returns only active members.
    - GET `/dashboard/members/{id}` returns 200 with member detail including role assignments.
    - POST `/dashboard/members/{id}/transition` with `newStatus=inactive` updates member status.
    - GET `/dashboard/members/new` returns 200 with create form.
  - **Green:** Write `views/members.py` with:
    - `members_bp = Blueprint("members", url_prefix="/dashboard/members")`
    - `member_directory` -- queries members with filters for status, profile, AZPO.
    - `member_detail` -- queries member with roles, AZPO memberships, participation history.
    - `member_create_form` and `member_create` -- form and create handler.
    - `member_edit_form` and `member_update` -- edit form and update handler.
    - `member_transition` -- POST endpoint for status transitions with validation of valid transitions.
    - `member_filter` -- SSE filter endpoint.
  - **Refactor:** Validate status transitions against the allowed state machine (prospective->onboarding->active->inactive->reactivating->active, active->exiting->exited).

  **Files:**
  - `views/members.py`

---

- [ ] **Task 3.2: Write member templates (list, detail, form)**

  Create member directory and detail templates with onboarding stepper.

  **TDD Cycle:**
  - **Red:** Write template rendering tests asserting: (1) list.html renders member cards with name, profile badge, status, AZPO, (2) detail.html shows member info, roles, onboarding stepper, (3) form.html has fields for name, profile type, AZPO, facilitator.
  - **Green:**
    - `members/list.html`: extends base, search bar with `data-bind="searchText"` and `data-on:input.debounce_300ms`, filter bar (status, profile type, AZPO), member cards/table with name, profile type badge, lifecycle status badge, primary AZPO, role count, join date.
    - `members/detail.html`: extends base, member header (name, profile badge, status badge), onboarding stepper component, current roles section (list of role cards linking to domain detail), AZPO memberships list, participation summary (total actions, last active date), status transition buttons (contextual based on current status), edit link.
    - `members/form.html`: extends base, name input, profile type selector (Co-creator, Builder, Collaborator, TownHall), AZPO assignment dropdown, onboarding facilitator dropdown (filtered to AE members), submit.
  - **Refactor:** Ensure profile type labels use NEOS terminology. Status transition buttons show only valid transitions.

  **Files:**
  - `templates/dashboard/members/list.html`
  - `templates/dashboard/members/detail.html`
  - `templates/dashboard/members/form.html`

---

- [ ] **Task 3.3: Add role assignment display and management**

  Wire up role assignment data in the member detail view, showing which domains the member stewards and linking to those domains.

  **TDD Cycle:**
  - **Red:** Write a test that: (1) creates a member with 2 role assignments to different domains, (2) requests the member detail page, (3) asserts both roles are displayed with domain name, role title, assignment date, and a link to the domain detail view.
  - **Green:** Update `member_detail` in `views/members.py` to query role assignments joined with domain data. Update `members/detail.html` to include a "Current Roles" section with a card for each role: domain name (linked to `/dashboard/domains/{id}`), role title, authority scope summary, assignment date, and next review date.
  - **Refactor:** Handle members with no role assignments (show "No roles assigned" message). Sort roles by domain name.

  **Files:**
  - `views/members.py` (update)
  - `templates/dashboard/members/detail.html` (update)

---

- [ ] **Task 3.4: Add onboarding status tracker component**

  Build the visual stepper component showing onboarding progress through the four stages.

  **TDD Cycle:**
  - **Red:** Write a test that renders the onboarding stepper partial with a member in "onboarding" status at the "discovery" stage and asserts: (1) "orientation" shows as completed with a date, (2) "discovery" shows as current/in-progress, (3) "integration" and "active" show as pending/future.
  - **Green:** Create `templates/partials/onboarding_stepper.html`:
    - Horizontal stepper with 4 steps: Orientation, Discovery, Integration, Active.
    - Each step shows: step name, status icon (checkmark for complete, dot for current, circle for future), completion date (if complete).
    - Current step is visually highlighted (accent color, larger).
    - Steps are connected by a progress line that fills to the current step.
    - CSS handles responsive layout (horizontal on desktop, vertical on narrow screens).
  - **Refactor:** Make the stepper component generic enough to reuse (accept steps as a template variable). Ensure color is not the only indicator (icons + text labels).

  **Files:**
  - `templates/partials/onboarding_stepper.html`
  - `templates/dashboard/members/detail.html` (update to include stepper)

---

- [ ] **Verification: Phase 3** [checkpoint marker]

  1. Navigate to `/dashboard/members` -- verify directory displays with search and filters.
  2. View a member detail -- verify profile info, roles, AZPO memberships display correctly.
  3. Verify onboarding stepper shows correct progress for members in different lifecycle stages.
  4. Verify role assignments link to the correct domain detail pages.
  5. Test status transitions (e.g., active -> inactive) and verify the update is reflected.
  6. Create a new member via the form and verify it appears in the directory.
  7. Verify all views render without JavaScript.

---

## Phase 4: Proposal ACT Lifecycle Views

**Goal:** Build the most complex view set: proposal CRUD plus the three ACT phase sub-views (advice, consent, test) with phase transition controls and the progress indicator. After this phase, users can create proposals and interact with the full ACT decision lifecycle.

### Tasks:

- [ ] **Task 4.1: Write views/proposals.py -- list, detail, create routes**

  Create the proposals blueprint with the main routes. ACT phase sub-views are added in subsequent tasks.

  **TDD Cycle:**
  - **Red:** Write tests that:
    - GET `/dashboard/proposals` returns 200 with proposal list.
    - GET `/dashboard/proposals` with filter signals returns filtered results via SSE.
    - GET `/dashboard/proposals/new` returns 200 with create form.
    - POST `/dashboard/proposals` creates a proposal with status "draft."
    - GET `/dashboard/proposals/{id}` returns 200 with proposal detail including ACT progress indicator.
  - **Green:** Write `views/proposals.py` with:
    - `proposals_bp = Blueprint("proposals", url_prefix="/dashboard/proposals")`
    - `proposal_list` -- queries proposals with filters for phase, type, decision type, domain, urgency.
    - `proposal_detail` -- queries proposal with all related data (advice entries, consent rounds, test data).
    - `proposal_create_form` -- renders create form.
    - `proposal_create` -- validates and persists with status "draft."
    - `proposal_filter` -- SSE filter endpoint.
    - `proposal_transition` -- POST endpoint for phase transitions with precondition validation.
  - **Refactor:** Ensure phase transitions validate preconditions (e.g., consent requires quorum, test requires consent completion).

  **Files:**
  - `views/proposals.py`

---

- [ ] **Task 4.2: Write proposal templates (list, detail, form)**

  Create the main proposal templates including the tabbed detail view shell.

  **TDD Cycle:**
  - **Red:** Write template rendering tests asserting: (1) list.html renders proposals with phase badges and urgency indicators, (2) detail.html shows proposal metadata and has tabs for Advice/Consent/Test, (3) form.html has all required fields including urgency radio buttons and co-sponsor multi-select.
  - **Green:**
    - `proposals/list.html`: extends base, filter bar (phase, type, decision type, domain, urgency), proposal cards/table with title, type badge, phase badge (color-coded by phase), decision type indicator, proposer, domain, urgency badge, last updated.
    - `proposals/detail.html`: extends base, proposal header (title, type badge, phase badge, urgency), proposer and co-sponsors, full proposed change text, rationale, affected domain, impacted parties. ACT progress indicator component (see Task 4.6). Tabbed interface with three tabs: Advice, Consent, Test. Each tab loads its content from a sub-template. Tab switching uses Datastar signals (`activeTab`) and `data-show`. Phase transition action buttons (contextual based on current phase).
    - `proposals/form.html`: extends base, type selector, decision type radio (preference/solution with descriptions), title, proposed change textarea, rationale textarea, affected domain dropdown, impacted parties multi-select, urgency radio (normal/elevated/emergency with timeline descriptions), desired timeline date input, co-sponsors multi-select, submit.
  - **Refactor:** Ensure tab content is loaded on initial render (not only via SSE) for no-JS support.

  **Files:**
  - `templates/dashboard/proposals/list.html`
  - `templates/dashboard/proposals/detail.html`
  - `templates/dashboard/proposals/form.html`

---

- [ ] **Task 4.3: Write advice tab template and SSE endpoint**

  Build the advice phase sub-view with advice entry listing, submission form, and integration tracking.

  **TDD Cycle:**
  - **Red:** Write tests that: (1) GET `/dashboard/proposals/{id}/advice` returns advice entries HTML, (2) POST `/dashboard/proposals/{id}/advice` creates a new advice entry and returns updated advice list via SSE, (3) the advice template shows advisor name, advice text, date, integration status for each entry, (4) the advice window status (open/closed, days remaining) is displayed.
  - **Green:**
    - Add to `views/proposals.py`:
      - `proposal_advice` -- SSE endpoint returning advice tab content.
      - `proposal_advice_submit` -- POST endpoint to create advice entry.
    - Write `proposals/advice.html`:
      - Advice window status bar: open/closed indicator, days remaining (countdown), total advice count.
      - Advice entry list: each entry shows advisor name and role, advice text, submission date, integration status badge (pending, integrated, acknowledged, declined).
      - Integration summary: counts of integrated/acknowledged/declined entries.
      - "Add Advice" form (shown only when advice window is open): textarea, submit button with `data-on:click.prevent="@post('/dashboard/proposals/{id}/advice')"`.
      - SSE patching targets the advice list region by id.
  - **Refactor:** Ensure advice entries are sorted by date (newest first). Disable the add form when the advice window is closed.

  **Files:**
  - `views/proposals.py` (update)
  - `templates/dashboard/proposals/advice.html`

---

- [ ] **Task 4.4: Write consent tab template and SSE endpoint**

  Build the consent phase sub-view with round-by-round position display, quorum tracking, and position recording.

  **TDD Cycle:**
  - **Red:** Write tests that: (1) GET `/dashboard/proposals/{id}/consent` returns consent rounds HTML, (2) POST `/dashboard/proposals/{id}/consent/position` records a position and returns updated round via SSE, (3) the quorum indicator shows required vs. actual participation, (4) objections are displayed with their text and integration status.
  - **Green:**
    - Add to `views/proposals.py`:
      - `proposal_consent` -- SSE endpoint returning consent tab content.
      - `proposal_consent_position` -- POST endpoint to record a consent position.
    - Write `proposals/consent.html`:
      - Round-by-round accordion/tabs: each round shows round number, date, participant positions.
      - Position display: each participant's position as a color-coded badge (green=consent, yellow=stand-aside, red=objection) with their name and rationale text (for stand-aside and objection).
      - Quorum indicator: progress bar showing current participation count / required quorum, numeric display, and status (quorum met / not yet met).
      - Objection details section (when objections exist): objection text, objector identity, integration status (pending, integrated, dismissed with reason).
      - Integration round panel: for each objection, how it was addressed (proposal modified, objector satisfied, escalated).
      - "Record Position" form (for active round): radio buttons for consent/stand-aside/objection, rationale textarea (required for stand-aside and objection, hidden for consent), submit button.
  - **Refactor:** Ensure the current/active round is visually distinguished from past rounds. Previous rounds are collapsed by default.

  **Files:**
  - `views/proposals.py` (update)
  - `templates/dashboard/proposals/consent.html`

---

- [ ] **Task 4.5: Write test tab template and SSE endpoint**

  Build the test phase sub-view with criteria checklist, midpoint check-in, and outcome recording.

  **TDD Cycle:**
  - **Red:** Write tests that: (1) GET `/dashboard/proposals/{id}/test` returns test phase HTML, (2) POST `/dashboard/proposals/{id}/test/criterion/{criterion_id}` updates a criterion status, (3) the template shows test period dates and success criteria with checkable statuses, (4) the outcome form allows selecting adopt/extend/modify/revert.
  - **Green:**
    - Add to `views/proposals.py`:
      - `proposal_test` -- SSE endpoint returning test tab content.
      - `proposal_test_criterion` -- POST endpoint to update a criterion's status.
      - `proposal_test_outcome` -- POST endpoint to record test outcome.
    - Write `proposals/test.html`:
      - Test period header: start date, end date, midpoint check-in date, days remaining countdown.
      - Success criteria checklist: each criterion shows description, status selector (not started, in progress, met, not met), evidence notes textarea. Status updates via SSE on change.
      - Midpoint check-in section: summary textarea, adjustments made list, check-in date.
      - Outcome section (shown at test end or when explicitly triggered): radio buttons for adopt/extend/modify/revert, rationale textarea, submit button.
      - Overall test progress: visual indicator of criteria met vs. total criteria.
  - **Refactor:** Ensure criteria statuses are persisted individually (not all-or-nothing). Outcome section is only enabled when the test period has elapsed or all criteria have final statuses.

  **Files:**
  - `views/proposals.py` (update)
  - `templates/dashboard/proposals/test.html`

---

- [ ] **Task 4.6: Write ACT progress indicator component**

  Build the reusable horizontal progress indicator showing proposal phase progression.

  **TDD Cycle:**
  - **Red:** Write a test that renders the ACT progress indicator partial with a proposal in the "consent" phase and asserts: (1) Draft and Synergy Check and Advice show as completed (checkmark), (2) Consent shows as current (highlighted), (3) Test and Adopted show as future (grayed out), (4) the component has correct ARIA attributes for screen readers.
  - **Green:** Create `templates/partials/act_progress.html`:
    - Horizontal bar with 6 steps: Draft, Synergy Check, Advice, Consent, Test, Adopted.
    - Each step is a circle/node connected by lines.
    - Completed steps: filled circle with checkmark icon, solid connecting line.
    - Current step: larger circle with accent color, pulsing animation (subtle).
    - Future steps: empty circle, dashed connecting line.
    - Below each step: step label text.
    - Special states: Rejected/Withdrawn/Reverted shown as a branch off the timeline at the point where it occurred.
    - ARIA: `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label="Proposal progress: currently in consent phase"`.
    - Responsive: labels stack below on narrow screens, abbreviate on very narrow.
  - **Refactor:** Parameterize so the component accepts `current_phase` and `phase_history` as template variables. Ensure the component works without CSS animations (for reduced-motion preference).

  **Files:**
  - `templates/partials/act_progress.html`
  - `templates/dashboard/proposals/detail.html` (update to include component)

---

- [ ] **Verification: Phase 4** [checkpoint marker]

  1. Navigate to `/dashboard/proposals` -- verify list displays with phase badges and filters work.
  2. Create a proposal via the form -- verify all fields save correctly and proposal appears with "draft" status.
  3. View proposal detail -- verify ACT progress indicator shows correct state.
  4. Test each ACT phase tab:
     a. Advice tab: add advice entry, verify it appears in the list with pending integration status.
     b. Consent tab: record a position, verify quorum indicator updates, verify objection display.
     c. Test tab: update criterion status, verify checklist reflects changes, record an outcome.
  5. Test phase transitions via action buttons and verify the progress indicator updates.
  6. Verify the full flow works without JavaScript (standard form submissions, full page reloads).
  7. Verify responsive layout for all proposal views.

---

## Phase 5: Decision Records and Search

**Goal:** Build the decision record browser, detail view, precedent search, and finalize all shared partials. After this phase, the complete dashboard is operational.

### Tasks:

- [ ] **Task 5.1: Write views/decisions.py -- list, detail, search routes**

  Create the decisions blueprint with browse, detail, and search routes.

  **TDD Cycle:**
  - **Red:** Write tests that:
    - GET `/dashboard/decisions` returns 200 with decision record list.
    - GET `/dashboard/decisions` with filter signals returns filtered results via SSE.
    - GET `/dashboard/decisions/{id}` returns 200 with full decision record detail.
    - GET `/dashboard/decisions/search` returns 200 with search form.
    - GET `/dashboard/decisions/search` with search signals returns ranked results via SSE.
  - **Green:** Write `views/decisions.py` with:
    - `decisions_bp = Blueprint("decisions", url_prefix="/dashboard/decisions")`
    - `decision_list` -- queries decision records with filters for skill, layer, precedent level, domain, status, date range.
    - `decision_detail` -- queries record with related records (citing, cited-by, same-domain, superseding).
    - `decision_search_page` -- renders search form.
    - `decision_search` -- SSE endpoint: reads search signals (query text, tag filters, precedent level), queries with text matching and tag filtering, ranks results (constitutional > governance > routine), yields ranked results.
    - `decision_filter` -- SSE filter endpoint for the browser view.
  - **Refactor:** Implement search ranking as a simple scoring function (exact match > partial match, higher precedent level = higher score).

  **Files:**
  - `views/decisions.py`

---

- [ ] **Task 5.2: Write decision templates (list, detail, search)**

  Create the decision record templates with structured display of holdings, reasoning, and dissent.

  **TDD Cycle:**
  - **Red:** Write template rendering tests asserting: (1) list.html shows record cards with ID, holding excerpt, precedent badge, (2) detail.html shows full record with all sections (holding, ratio decidendi, obiter dicta, dissent, participants, tags), (3) search.html has search input, tag filters, and results area.
  - **Green:**
    - `decisions/list.html`: extends base, filter bar (source skill dropdown, layer dropdown 1-10, precedent level, domain, status, date range), record cards/table with record ID, holding (truncated to 200 chars), source skill/layer badge, precedent level badge (color-coded: blue=routine, purple=governance, gold=constitutional), domain, status badge, date.
    - `decisions/detail.html`: extends base, record header (ID, precedent level badge, status badge, date), sections:
      - **Holding** -- the decision statement, prominently displayed.
      - **Ratio Decidendi** -- the binding reasoning, in a distinct visual block.
      - **Obiter Dicta** -- contextual observations, visually de-emphasized.
      - **Dissent Record** -- objections with objector identity, objection text, resolution status.
      - **Deliberation Summary** -- reference to source discussion.
      - **Participants** -- table of names, roles, positions.
      - **Source Artifact** -- link to the originating entity (agreement, proposal, etc.).
      - **Semantic Tags** -- clickable tag pills that link to search with that tag pre-filled.
      - **Related Records** -- records citing this one, records this cites, same-domain records, superseding/overruling records.
    - `decisions/search.html`: extends base, search input with `data-bind="searchQuery"` and `data-on:input.debounce_300ms="@get('/dashboard/decisions/search')"`, tag filter chips (clickable to toggle), precedent level filter, results area with id for SSE patching, result cards showing record ID, holding (with search term highlighted), precedent badge, domain, date, relevance score.
  - **Refactor:** Ensure semantic tags use consistent styling across list and detail views. Highlighted search terms use `<mark>` for accessibility.

  **Files:**
  - `templates/dashboard/decisions/list.html`
  - `templates/dashboard/decisions/detail.html`
  - `templates/dashboard/decisions/search.html`

---

- [ ] **Task 5.3: Implement precedent search with tag-based filtering**

  Wire up the search functionality with text matching and tag-based filtering, returning ranked results.

  **TDD Cycle:**
  - **Red:** Write integration tests that: (1) create 5 decision records with different tags and precedent levels, (2) search with text query matching 3 of them, (3) assert results are returned in rank order (constitutional first), (4) search with a tag filter returns only records with that tag, (5) combined text + tag search returns the intersection.
  - **Green:** In `views/decisions.py`, implement the search logic:
    - Text search: ILIKE query across holding and ratio_decidendi fields.
    - Tag filter: filter by semantic_tags JSONB/array containment.
    - Ranking function: score = text_relevance_score + precedent_weight (constitutional=30, governance=20, routine=10).
    - Return results sorted by score descending.
    - Render results via SSE, patching the results region.
    - Include result count in the patched HTML.
  - **Refactor:** Add "No results found" message for empty search results. Ensure search is case-insensitive.

  **Files:**
  - `views/decisions.py` (update)

---

- [ ] **Task 5.4: Finalize partials and cross-cutting template concerns**

  Review and complete all partial templates. Ensure pagination, notifications, and loading work consistently across all views. Add any missing ARIA attributes and responsive fixes.

  **TDD Cycle:**
  - **Red:** Write tests that: (1) pagination partial renders correct page numbers and prev/next states for a given total/page/pageSize, (2) notification partial displays and auto-dismisses, (3) loading indicator shows during SSE fetch simulation, (4) all views pass an HTML validator (well-formed HTML5), (5) all interactive elements have ARIA labels.
  - **Green:**
    - Review and finalize `partials/pagination.html`: ensure it handles edge cases (page 1 disables prev, last page disables next, single page hides pagination).
    - Review `partials/notification.html`: ensure auto-dismiss works, multiple notifications stack, dismiss button works.
    - Review `partials/loading.html`: ensure it appears during SSE fetches on all pages.
    - Audit all templates for:
      - Missing ARIA labels on buttons, links, form fields.
      - Missing `<label>` elements for form inputs.
      - Color-only information (add text labels to all badges).
      - Keyboard navigation gaps.
      - Consistent use of `{% include %}` for partials.
    - Add `prefers-reduced-motion` media query to disable animations.
  - **Refactor:** Create a template checklist in comments at the top of `base.html` documenting the block structure and conventions.

  **Files:**
  - `templates/partials/pagination.html` (update)
  - `templates/partials/notification.html` (update)
  - `templates/partials/loading.html` (update)
  - `templates/base.html` (update if needed)

---

- [ ] **Verification: Phase 5** [checkpoint marker]

  1. Navigate to `/dashboard/decisions` -- verify browser displays with all filters functional.
  2. View a decision record detail -- verify all sections render (holding, ratio decidendi, obiter dicta, dissent, participants, tags, related records).
  3. Use precedent search -- verify text search returns highlighted results ranked by relevance and precedent level.
  4. Verify tag-based filtering works (click a tag, see filtered results).
  5. Test pagination across all list views -- verify prev/next, page numbers, edge cases.
  6. Test toast notifications -- trigger a create/update action and verify toast appears and auto-dismisses.
  7. Test loading indicator -- verify spinner appears during SSE requests.
  8. Full accessibility pass: tab through all views, verify focus indicators, verify ARIA labels, verify screen reader announces page structure.
  9. Responsive pass: test all views at 320px, 768px, and 1920px widths.
  10. No-JavaScript pass: disable JavaScript and verify all views render with full content, forms submit via POST, navigation works via links.

---

## Summary

| Phase | Tasks | Focus |
|-------|-------|-------|
| 1 | 4 + verification | Base layout, navigation, dashboard home |
| 2 | 6 + verification | Agreement CRUD, domain views, SSE filtering |
| 3 | 4 + verification | Member directory, onboarding tracker, roles |
| 4 | 6 + verification | Proposal CRUD, ACT lifecycle tabs, progress indicator |
| 5 | 4 + verification | Decision records, precedent search, partials finalization |
| **Total** | **24 tasks** | **5 verification checkpoints** |

**Key files produced:**
- `views/__init__.py`, `views/dashboard.py`, `views/agreements.py`, `views/domains.py`, `views/members.py`, `views/proposals.py`, `views/decisions.py` (7 Python modules)
- `templates/base.html` (root layout)
- `templates/dashboard/index.html` (home)
- `templates/dashboard/agreements/{list,detail,form,history,_list_body}.html` (5 templates)
- `templates/dashboard/domains/{list,detail,form}.html` (3 templates)
- `templates/dashboard/members/{list,detail,form}.html` (3 templates)
- `templates/dashboard/proposals/{list,detail,form,advice,consent,test}.html` (6 templates)
- `templates/dashboard/decisions/{list,detail,search}.html` (3 templates)
- `templates/partials/{pagination,notification,loading,onboarding_stepper,act_progress}.html` (5 partials)
- **Total: 7 view modules + 26 templates**
