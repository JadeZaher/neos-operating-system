# Specification: Datastar Dashboard & Views

**Track ID:** dashboard_views_20260305
**Track Type:** Feature
**Created:** 2026-03-05
**Depends On:** agent_foundation_20260305 (Sanic app factory, SQLAlchemy models, skill registry, configuration)
**Priority:** P0

---

## Overview

Build the complete Datastar-powered dashboard UI for the NEOS governance platform. This track produces all Jinja2 templates, Sanic view modules, and SSE-driven interactive components that allow ecosystem participants to create, read, update, and manage governance entities: agreements, domains, members, proposals (with full ACT lifecycle), and decision records.

The dashboard is the primary interface through which OmniOne members interact with the governance skill stack daily. It must faithfully represent the structural concepts defined in the 54 NEOS skills across 10 layers while remaining responsive, accessible, and functional without JavaScript (Datastar enhances but does not replace server-rendered HTML).

## Background

The NEOS governance skill stack (neos-core/, 10 layers, 54 skills) defines governance protocols in markdown. The agent_foundation track (agent_foundation_20260305) translates these into a Sanic web application with SQLAlchemy models (27 tables), a skill registry, and configuration management. This track builds the presentation layer on top of that foundation.

**Technology choices:**

- **Datastar 1.x** (11KB JS) provides SSE-first hypermedia reactivity via `data-*` HTML attributes. The server streams `event: datastar-patch-elements` and `event: datastar-patch-signals` events. The client applies DOM morphing (preserving state) and signal updates atomically.
- **datastar-py** (official Python SDK) provides `@datastar_response` decorator, `ServerSentEventGenerator` (SSE), and `read_signals()` for Sanic integration.
- **Jinja2** via sanic-ext handles server-side template rendering with block inheritance.
- **CSS custom properties** (`--neos-*`) enable per-ecosystem theming.

The Sanic + Datastar pattern is:
```python
from datastar_py.sanic import datastar_response, read_signals
from datastar_py import ServerSentEventGenerator as SSE

@app.route("/dashboard/agreements")
@datastar_response
async def agreement_list(request):
    signals = await read_signals(request)
    agreements = await db.query_agreements(type=signals.get("filterType"))
    html = await render("agreements/list.html", agreements=agreements)
    yield SSE.patch_elements(html)
```

The client uses declarative attributes:
```html
<div data-signals='{"filterType": "all"}'>
  <select data-bind="filterType" data-on:change="@get('/dashboard/agreements')">
    <option value="all">All</option>
  </select>
  <div id="agreement-list" data-on:load="@get('/dashboard/agreements')">
    <!-- SSE patches this region -->
  </div>
</div>
```

---

## Functional Requirements

### FR-1: Base Layout and Navigation

**Description:** Create the HTML5 base layout template that all dashboard pages extend. The layout includes the Datastar script, navigation sidebar, ecosystem selector, toast notification system, and loading indicator.

**Acceptance Criteria:**
- AC-1.1: `base.html` is a valid HTML5 document with `<meta charset="utf-8">`, viewport meta tag, and Datastar 1.x script tag (CDN with self-hosted fallback).
- AC-1.2: Navigation sidebar contains links to: Dashboard (home), Agreements, Domains, Members, Proposals, Decisions.
- AC-1.3: The currently active page is visually highlighted using a Datastar signal (`activePage`) that is set by each page template via `{% block signals %}`.
- AC-1.4: An ecosystem selector dropdown is present in the header for multi-tenant support. Changing the ecosystem updates a `currentEcosystem` signal and triggers a page refresh via `@get`.
- AC-1.5: NEOS brand colors are defined in a Tailwind config block in base.html (`tailwind.config.theme.extend.colors.neos`). All styling uses Tailwind utility classes exclusively — no custom CSS files or CSS custom properties.
- AC-1.6: A toast notification region exists (fixed position, top-right) driven by a `notifications` signal array. Each notification has type (success, warning, error, info), message, and auto-dismiss after 5 seconds.
- AC-1.7: A loading indicator (CSS spinner or progress bar) is displayed during active SSE requests, controlled by Datastar's built-in `$isFetching` signal.
- AC-1.8: The page renders with full content and navigation when JavaScript is disabled. Datastar enhances the experience but the server-rendered HTML is complete and usable.
- AC-1.9: All interactive elements have ARIA labels. Navigation uses `<nav>` landmark. Main content area uses `<main>` landmark. Sidebar is keyboard-navigable with Tab/Shift+Tab.

**Priority:** P0

---

### FR-2: Agreement Views

**Description:** Full CRUD views for governance agreements (UAF, ecosystem, access, stewardship, ETHOS, culture code, personal commitment). Agreements follow a 7-level hierarchy where no lower-level agreement may contradict a higher-level one.

**Acceptance Criteria:**
- AC-2.1: List view at `/dashboard/agreements` displays agreements in a table/card layout with columns: title, type, status, domain, review date, last modified.
- AC-2.2: List view supports SSE-driven filtering by type (space, access, organizational, uaf, stewardship, culture_code, personal_commitment), status (active, under_review, sunset, archived, draft), and domain. Filters use Datastar signals and `@get` to fetch updated results without full page reload.
- AC-2.3: List view supports text search across agreement titles and text content, debounced at 300ms via Datastar signal binding.
- AC-2.4: Create form at `/dashboard/agreements/new` includes: type selector (dropdown), title (text input), text editor (textarea with markdown preview), affected parties (multi-select with search), domain selector (dropdown populated from domain registry), hierarchy level (auto-determined from type but overridable), proposed review date (date picker), and rationale (textarea).
- AC-2.5: Form validation occurs both client-side (Datastar signals for required fields) and server-side (returning validation errors via SSE.patch_elements on the error regions).
- AC-2.6: Detail view at `/dashboard/agreements/{id}` displays: full agreement text (rendered markdown), status badge (color-coded), type badge, domain link, affected parties list, ratification history (consent positions with timestamps), amendment history (linked to amendment records), review schedule (next review date with countdown), hierarchy position, and version number.
- AC-2.7: Edit view at `/dashboard/agreements/{id}/edit` pre-populates the create form with existing data and submits via `@put`.
- AC-2.8: Version history view at `/dashboard/agreements/{id}/history` shows a timeline of amendments with: version number, date, amendment type (minor/structural), summary of changes, and a diff view showing what changed between versions.
- AC-2.9: Agreement status transitions (active -> under_review, under_review -> active, active -> sunset, sunset -> archived) are available as action buttons on the detail view, with confirmation dialog.

**Priority:** P0

---

### FR-3: Domain Views

**Description:** Views for S3-style governance domains using the 11-element domain contract model. Domains define where authority exists, who holds it, and what it cannot do.

**Acceptance Criteria:**
- AC-3.1: List view at `/dashboard/domains` shows active domains in a card layout with: domain name (purpose summary), current steward, delegating body, status (active, provisional, contested, archived), health indicator (from last domain-review), and creation date.
- AC-3.2: List view supports filtering by status and delegating body.
- AC-3.3: Detail view at `/dashboard/domains/{id}` displays all 11 S3 domain contract elements in a structured layout:
  1. Purpose
  2. Key Responsibilities
  3. Customers
  4. Deliverables
  5. Dependencies (linked to dependent domains)
  6. Constraints (visually prominent -- these define what the domain CANNOT do)
  7. Challenges
  8. Resources
  9. Delegator Responsibilities
  10. Competencies
  11. Metrics + Evaluation Schedule (with next evaluation date)
- AC-3.4: Detail view also shows: current steward and assignment history, domain version and amendment history, adjacent domains (linked), and subordinate domains (if any).
- AC-3.5: Create/edit form at `/dashboard/domains/new` and `/dashboard/domains/{id}/edit` provides a guided 11-element form with help text for each element drawn from the domain-mapping skill description. Constraints field has special emphasis with a warning if left vague.
- AC-3.6: Domain dependency visualization shows which domains depend on this one and which this domain depends on, as a simple linked list (not a full graph -- that is a future track).

**Priority:** P0

---

### FR-4: Member Views

**Description:** Views for ecosystem participant management following the member-lifecycle skill. Members transition through states: prospective -> onboarding -> active -> inactive -> reactivating -> active (loop), or active -> exiting -> exited.

**Acceptance Criteria:**
- AC-4.1: Directory view at `/dashboard/members` shows a searchable, filterable list of members with: name, profile type (Co-creator, Builder, Collaborator, TownHall), lifecycle status, primary ETHOS, role count, and join date.
- AC-4.2: Directory supports filtering by lifecycle status (prospective, onboarding, active, inactive, reactivating, exiting, exited), profile type, and ETHOS.
- AC-4.3: Directory supports text search across member names.
- AC-4.4: Detail view at `/dashboard/members/{id}` shows: member information (name, profile type, contact), current lifecycle status with transition timestamp, all current role assignments (linked to domain detail views), ETHOS memberships, participation history summary (governance actions count, last active date), and onboarding status tracker.
- AC-4.5: Onboarding status tracker is a visual stepper showing the member's progress through: orientation (UAF reading), discovery (ecosystem exploration), integration (first governance participation), active (full participant). Each step shows completion date or current status.
- AC-4.6: Status transition buttons are available on the detail view for valid transitions (e.g., onboarding -> active, active -> inactive) with confirmation and rationale input.
- AC-4.7: Create/edit form at `/dashboard/members/new` and `/dashboard/members/{id}/edit` includes: name, profile type selector, ETHOS assignment, and onboarding facilitator assignment.

**Priority:** P0

---

### FR-5: Proposal and ACT Lifecycle Views

**Description:** Full lifecycle views for proposals following the ACT (Advice -> Consent -> Test) decision protocol. This is the most complex view set, as proposals transition through multiple phases with distinct sub-views for each phase.

**Acceptance Criteria:**
- AC-5.1: List view at `/dashboard/proposals` shows proposals with: title, type (ecoplan, genplan, amendment, resource_request, policy_change), decision type (preference/solution), current phase (draft, synergy_check, advice, consent, test, adopted, reverted, withdrawn, archived), proposer, domain, urgency level (normal, elevated, emergency), and last updated date.
- AC-5.2: List supports SSE-driven filtering by phase, type, decision type, domain, and urgency level.
- AC-5.3: Create form at `/dashboard/proposals/new` includes: type selector, decision type selector, title, proposed change text (textarea with markdown), rationale, affected domain (dropdown), impacted parties (multi-select), urgency level (radio buttons with descriptions), desired timeline (date), and co-sponsors (multi-select, optional).
- AC-5.4: Detail view at `/dashboard/proposals/{id}` shows the proposal metadata, full text, and a tabbed interface for the three ACT phases: Advice, Consent, and Test.
- AC-5.5: **ACT Progress Indicator** -- a horizontal visual timeline at the top of the detail view showing all phases (Draft -> Synergy Check -> Advice -> Consent -> Test -> Adopted) with the current phase highlighted, completed phases marked with a check, and future phases grayed out. The indicator updates via SSE when the phase changes.
- AC-5.6: **Advice Tab** (`/dashboard/proposals/{id}/advice`) displays:
  - List of all advice entries with: advisor name, role, advice text, date submitted, and integration status (pending, integrated, acknowledged, declined with reason).
  - "Add Advice" form: textarea for advice text, submit button.
  - Advice window status: open/closed, days remaining, total advice count.
  - Integration summary: how many entries were integrated vs. acknowledged vs. declined.
- AC-5.7: **Consent Tab** (`/dashboard/proposals/{id}/consent`) displays:
  - Round-by-round view (consent may take multiple rounds if objections require integration).
  - For each round: round number, date, participant positions (consent / stand-aside / objection) displayed as color-coded badges.
  - Quorum indicator: required quorum vs. current participation count, with visual progress bar.
  - For objections: objection text, objector identity, integration status.
  - "Record Position" form (for the current round): radio buttons for consent / stand-aside / objection, text field for rationale (required for stand-aside and objection).
  - Integration round panel (when objections exist): shows how each objection was addressed.
- AC-5.8: **Test Tab** (`/dashboard/proposals/{id}/test`) displays:
  - Test period dates (start, end, midpoint check-in date).
  - Success criteria as a checklist with: criterion description, status (not started, in progress, met, not met), evidence notes.
  - Midpoint check-in section: summary, any adjustments made.
  - Outcome selector: adopt (make permanent), extend (more testing time), modify (adjust and re-test), revert (undo the change).
  - Outcome rationale textarea.
- AC-5.9: Phase transition buttons are available for authorized users: "Open Advice Round," "Close Advice / Open Consent," "Record Consent Outcome," "Begin Test Period," "Record Test Outcome." Each transition validates preconditions (e.g., consent requires quorum met).
- AC-5.10: Proposal status changes trigger a toast notification to the current user.

**Priority:** P0

---

### FR-6: Decision Record Views

**Description:** Views for governance decision records following the decision-record skill from Layer IX. Decision records wrap any governance artifact with holding, ratio decidendi, and precedent classification.

**Acceptance Criteria:**
- AC-6.1: Browser view at `/dashboard/decisions` shows decision records with: record ID (DR-[ECOSYSTEM]-[YEAR]-[SEQUENCE]), holding (truncated), source skill/layer, precedent level (routine, governance, constitutional), domain, status (active, superseded, overruled), and date.
- AC-6.2: Browser supports filtering by: source skill, layer (I through X), precedent level, domain, status, and date range.
- AC-6.3: Detail view at `/dashboard/decisions/{id}` displays: full holding text, ratio decidendi (the binding reasoning), obiter dicta (contextual observations), dissent record (objections and their resolution), deliberation summary, participant list with positions, source artifact link, domain, precedent classification badge, semantic tags (clickable to search for related records), lifecycle status, and authorship metadata.
- AC-6.4: Related records section shows: records that cite this record, records this record cites, records in the same domain, and records that supersede or overrule this record.
- AC-6.5: Search view at `/dashboard/decisions/search` provides: text search across holdings and ratio decidendi, tag-based filtering (domain tags, topic keywords, layer tags), and result ranking by relevance and precedent level (constitutional > governance > routine).
- AC-6.6: Search results display as cards with: record ID, holding (highlighted matching text), precedent level badge, domain, date, and relevance score.

**Priority:** P1

---

### FR-7: Dashboard Home

**Description:** The main dashboard landing page providing an at-a-glance overview of ecosystem governance health and quick access to common actions.

**Acceptance Criteria:**
- AC-7.1: Dashboard home at `/dashboard` displays summary cards showing: total active agreements (count), active proposals by phase (bar or segmented count), pending consent rounds (count with "needs your input" indicator), recent decisions (count in last 30 days), active members (count), and domains (count).
- AC-7.2: Each summary card is a link to the relevant list view.
- AC-7.3: Recent activity feed shows the last 10 governance actions (agreement created, proposal phase changed, consent recorded, decision registered, member status changed) with: action description, actor, timestamp, and link to the relevant entity.
- AC-7.4: Activity feed auto-updates via SSE polling (every 30 seconds) or on-demand refresh button.
- AC-7.5: Quick action buttons are prominently displayed: "New Agreement," "New Proposal," "Search Precedents." Each navigates to the relevant create/search view.
- AC-7.6: Summary cards update via SSE when the dashboard loads (not hardcoded into the page template).

**Priority:** P0

---

## Non-Functional Requirements

### NFR-1: Progressive Enhancement

**Description:** All pages must render with full content and be usable when JavaScript is disabled. Datastar enhances the experience (SSE-driven updates, filtering without page reload, toast notifications) but the server-rendered HTML is complete. Forms submit via standard HTTP POST when JavaScript is unavailable. Navigation works via standard `<a>` links.

**Acceptance Criteria:**
- NFR-1.1: Every list view renders the initial data set in the HTML response (not as a blank container waiting for SSE).
- NFR-1.2: Every form has a standard `action` and `method` attribute so it submits without JavaScript.
- NFR-1.3: Filtering without JavaScript falls back to query parameters on page reload.

---

### NFR-2: Responsive Layout

**Description:** The dashboard must be usable on mobile devices (minimum 320px width) through large desktop displays (1920px+).

**Acceptance Criteria:**
- NFR-2.1: Navigation sidebar collapses to a hamburger menu on screens narrower than 768px.
- NFR-2.2: Card layouts reflow from multi-column to single-column on narrow screens.
- NFR-2.3: Tables horizontally scroll on narrow screens rather than breaking layout.
- NFR-2.4: Touch targets are at least 44x44px on mobile.

---

### NFR-3: Accessibility

**Description:** The dashboard meets WCAG 2.1 AA standards.

**Acceptance Criteria:**
- NFR-3.1: All interactive elements have ARIA labels or visible text labels.
- NFR-3.2: Color is not the sole means of conveying information (status badges include text, not just color).
- NFR-3.3: Focus indicators are visible on all interactive elements.
- NFR-3.4: Keyboard navigation works for all interactive flows (tab order, enter to activate, escape to close modals).
- NFR-3.5: Page structure uses semantic HTML landmarks: `<nav>`, `<main>`, `<aside>`, `<header>`, `<footer>`, `<section>`, `<article>`.

---

### NFR-4: Database Access Pattern

**Description:** All database access goes through the SQLAlchemy models and session management provided by the agent_foundation track. Views never construct raw SQL.

**Acceptance Criteria:**
- NFR-4.1: Every view function obtains a database session through the app's dependency injection or middleware.
- NFR-4.2: Queries use SQLAlchemy ORM methods (query, filter, join) or the repository pattern if established by agent_foundation.
- NFR-4.3: Write operations (create, update) go through model constructors and session.commit() with proper error handling.

---

### NFR-5: Template Architecture

**Description:** Templates use Jinja2 block inheritance for maintainability and consistency.

**Acceptance Criteria:**
- NFR-5.1: All page templates extend `base.html` using `{% extends "base.html" %}`.
- NFR-5.2: `base.html` defines blocks: `title`, `signals`, `styles`, `content`, `scripts`.
- NFR-5.3: Partial templates (pagination, notification, loading) are included via `{% include "partials/..." %}`.
- NFR-5.4: Template variables use consistent naming conventions (snake_case, plural for lists, singular for detail objects).
- NFR-5.5: No business logic in templates -- templates receive pre-computed values from view functions.

---

### NFR-6: Performance

**Description:** Dashboard pages load and respond quickly under normal usage.

**Acceptance Criteria:**
- NFR-6.1: Initial page load (server-rendered HTML) completes in under 500ms for list views with up to 100 items.
- NFR-6.2: SSE filter updates complete in under 300ms.
- NFR-6.3: List views use pagination (default 25 items per page) to bound query size.
- NFR-6.4: Datastar script loads from CDN with a local fallback to avoid blocking on CDN failures.

---

## User Stories

### US-1: Agreement Management

**As** an ecosystem steward,
**I want** to browse, search, and filter agreements by type and status,
**So that** I can quickly find the agreements relevant to my domain.

**Given** I am on the agreements list page,
**When** I select "access" from the type filter and "active" from the status filter,
**Then** the list updates via SSE (without full page reload) to show only active access agreements.

---

### US-2: Agreement Creation

**As** a circle member with proposal authority,
**I want** to create a new agreement through a structured form,
**So that** the agreement enters the governance process with all required metadata.

**Given** I am on the "New Agreement" form,
**When** I fill in type, title, text, affected parties, domain, and review date, then submit,
**Then** the agreement is created with status "draft" and I am redirected to the detail view with a success notification.

---

### US-3: Domain Inspection

**As** a governance participant,
**I want** to view the full 11-element domain contract for any domain,
**So that** I can understand exactly what authority that domain holds and what it cannot do.

**Given** I am on the domain detail page,
**When** the page loads,
**Then** I see all 11 elements clearly labeled with the constraints section visually prominent.

---

### US-4: ACT Lifecycle Tracking

**As** a proposal author,
**I want** to see my proposal's current ACT phase and interact with each phase's sub-view,
**So that** I can track progress and respond to advice and consent feedback.

**Given** I am viewing a proposal in the "advice" phase,
**When** I click the "Advice" tab,
**Then** I see all submitted advice entries, their integration status, and a form to view or respond to each entry.

---

### US-5: Consent Round Participation

**As** an affected party in a consent round,
**I want** to record my position (consent, stand-aside, or objection) with my rationale,
**So that** my voice is formally documented in the governance record.

**Given** I am on the consent tab of a proposal in active consent round,
**When** I select "objection," type my rationale, and submit,
**Then** my objection is recorded, the quorum indicator updates, and the round status reflects the new objection.

---

### US-6: Precedent Search

**As** a governance facilitator,
**I want** to search decision records by topic tags and text,
**So that** I can find relevant precedents before a new decision is made.

**Given** I am on the decision search page,
**When** I enter "resource allocation" in the search field and select "governance" precedent level,
**Then** I see ranked results showing decision records about resource allocation at the governance level, with matching text highlighted.

---

### US-7: Dashboard Overview

**As** an ecosystem member,
**I want** to see an at-a-glance summary of governance activity on the dashboard home,
**So that** I know what requires my attention without navigating to each section.

**Given** I am on the dashboard home page,
**When** the page loads,
**Then** I see summary cards with counts, a recent activity feed, and quick action buttons.

---

### US-8: Member Onboarding Tracking

**As** an onboarding facilitator,
**I want** to see each new member's progress through the onboarding stages,
**So that** I can provide timely support and know when they are ready for full participation.

**Given** I am viewing a member in "onboarding" status,
**When** the detail page loads,
**Then** I see a visual stepper showing which onboarding stages are complete and which are pending.

---

## Technical Considerations

### Datastar Integration Patterns

1. **Initial Load:** Each page template renders full HTML server-side. Datastar signals are initialized in the template via `data-signals`. SSE endpoints provide dynamic updates.

2. **Filtering Pattern:** Filter controls use `data-bind` to bind to signals. On change, `data-on:change="@get('/endpoint')"` triggers an SSE request. The server reads signals via `read_signals(request)`, queries the database with filter parameters, renders a partial template, and yields `SSE.patch_elements(html)`.

3. **Form Submission Pattern:** Forms use `data-on:submit.prevent="@post('/endpoint')"` for Datastar-enhanced submission. The server validates, persists, and yields either `SSE.patch_elements(success_html)` or `SSE.patch_elements(error_html)` targeting the form's error regions. The form also has a standard `action`/`method` for no-JS fallback.

4. **Toast Notification Pattern:** After successful operations, the server yields `SSE.patch_signals({"notifications": [{"type": "success", "message": "..."}]})`. The base template's notification region reacts to signal changes.

5. **Multi-Element Updates:** A single SSE response can yield multiple `SSE.patch_elements()` calls to update several page regions atomically (e.g., update the list AND the summary count after a create operation).

### View Module Structure

Each view module (`views/agreements.py`, etc.) registers a Sanic Blueprint with its routes. The main `views/__init__.py` collects all blueprints and registers them with the app. This keeps route definitions modular and testable.

### Template Naming Convention

- `templates/base.html` -- root layout
- `templates/dashboard/{entity}/list.html` -- list/browser views
- `templates/dashboard/{entity}/detail.html` -- detail views
- `templates/dashboard/{entity}/form.html` -- create/edit forms (distinguished by context variable `is_edit`)
- `templates/partials/{component}.html` -- reusable partial templates

### NEOS Terminology in UI

The UI must use NEOS terminology consistently (per product-guidelines.md):
- "Domain" not "jurisdiction"
- "Steward" not "owner" or "manager"
- "Circle" not "committee"
- "Ecosystem" not "organization"
- "ACT" not "voting" or "approval process"
- "Current-See" not "token" or "vote"
- "Agreement Field" not "contract" or "rules"
- "ETHOS" not "department" or "team"

### CSS Architecture: Tailwind Only

**All styling uses Tailwind CSS utility classes exclusively. No custom CSS files.**

- Tailwind 4.x loaded via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Custom NEOS colors defined in Tailwind config block in base.html:
  ```html
  <script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          neos: {
            primary: '#2D5A27',
            secondary: '#1a3a17',
            accent: '#7CB342',
            bg: '#f5f5f0',
            surface: '#ffffff',
            success: '#4CAF50',
            warning: '#FF9800',
            danger: '#f44336',
          }
        }
      }
    }
  }
  </script>
  ```
- Responsive layouts use Tailwind's `sm:`, `md:`, `lg:` prefixes
- Dark mode via Tailwind's `dark:` prefix (future)
- No `<style>` blocks, no `dashboard.css`, no CSS custom properties
- All spacing, typography, colors, borders use Tailwind utility classes directly in HTML

---

## Out of Scope

- **Authentication and authorization** -- handled by a separate auth track; views assume a logged-in user context is available.
- **Real-time multi-user collaboration** -- SSE provides server-to-client updates but not WebSocket-style multi-user sync.
- **Full graph visualization** of domain dependencies -- deferred to a future track; this track provides simple linked lists.
- **Email or push notifications** -- toast notifications are in-browser only.
- **File upload** (for agreement attachments, member photos) -- deferred.
- **Internationalization (i18n)** -- English only for initial release.
- **Audit logging UI** -- the foundation track logs actions but this track does not build an audit log viewer.
- **Governance health dashboard** (Layer VII metrics visualization) -- deferred to a future analytics track.
- **Mobile native app** -- responsive web only.

---

## Open Questions

1. **Markdown rendering:** Should agreement and proposal text be rendered as markdown in detail views? If so, should we use a server-side markdown library (e.g., markdown-it via subprocess or a Python markdown library) or client-side rendering? Recommendation: server-side via Python `markdown` library for progressive enhancement compatibility.

2. **Pagination strategy:** Cursor-based or offset-based pagination? Offset-based is simpler for Datastar SSE patching. Recommendation: offset-based with configurable page size (default 25).

3. **Ecosystem selector behavior:** When the user switches ecosystems, should the dashboard reload entirely or attempt to stay on the same entity type view? Recommendation: reload to dashboard home to avoid cross-ecosystem entity confusion.

4. **Test phase criteria tracking:** Should success criteria be editable after the test phase begins, or locked at test start? The skill says criteria are defined at proposal creation but the test tab allows "modify." Recommendation: criteria are defined at test start and can only be amended through a recorded modification (not silent edit).

5. **Diff rendering for agreement version history:** How sophisticated should the diff view be? Full word-level diff or simple side-by-side? Recommendation: start with a simple "old text / new text" side-by-side display; word-level diff is a future enhancement.
