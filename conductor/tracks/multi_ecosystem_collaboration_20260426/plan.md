# Multi-Ecosystem Collaboration Track — Implementation Plan

**Track ID:** multi_ecosystem_collaboration_20260426
**Phases:** 6

---

## Phase 0: Critical Fixes & Foundation [COMPLETE]

Security and correctness fixes that must land before collaboration features.

- [x] 0.1 Fix ecosystem scoping bypass — centralize to `api/helpers.py`, delete 14 duplicate `_get_ecosystem_ids()`
- [x] 0.2 Fix `Member.did` unique constraint → composite `(ecosystem_id, did)`
- [x] 0.3 Fix async Anthropic client in `ai_assist.py`
- [x] 0.4 Unify agreement state machine (API → full ACT lifecycle)
- [x] 0.5 Replace all `datetime.utcnow()` → `datetime.now(timezone.utc)` (18 sites)
- [x] 0.6 Harden `SESSION_SECRET` (fail in prod, auto-gen in dev)
- [x] 0.7 Add `toggleEcosystem` + `selectMultiple` to `EcosystemContext`
- [x] 0.8 Fix quorum calculation (`math.ceil` instead of `int`)
- [x] 0.9 Add steward authorization to ecosystem updates
- [x] 0.10 Add new data models: `CircleMembership`, `SharesNeeds`, `Collaboration`, `ComplianceSummary`
- [x] 0.11 Add `version_fingerprint` to Agreement and Domain
- [x] 0.12 Enrich seed data to 3 ecosystems × 5 members × 3-4 domains

**Acceptance:** All security fixes verified, seed script runs clean, 3-ecosystem test data available.

---

## Phase 1: AI Provider Independence

Switch from Anthropic SDK to LiteLLM/OpenRouter for multi-model support.

- [ ] 1.1 Add `litellm` to dependencies, remove direct `anthropic` dependency from API layer
- [ ] 1.2 Create `neos_agent/ai/provider.py` — async wrapper around `litellm.acompletion()`
  - Config: `AI_PROVIDER` (openrouter, anthropic, local), `AI_MODEL`, `AI_API_KEY`
  - Fallback: if no API key, AI features disabled gracefully
- [ ] 1.3 Update `ai_assist.py` to use provider abstraction
- [ ] 1.4 Update `chat.py` SSE handler to use provider abstraction
- [ ] 1.5 Update `system_prompt.py` to add "No Sultan" behavioral constraint:
  - Never concentrate decision authority in AI recommendations
  - Always present multiple options, never prescribe single outcomes
  - Flag when a process is approaching authority concentration
- [ ] 1.6 Update `config.py` with new AI settings (provider, model, API key, base URL)
- [ ] 1.7 Ensure all governance templates include human-readable instructions (no AI dependency)

**Acceptance:** AI chat works with OpenRouter. Setting `AI_PROVIDER=""` disables AI without breaking governance workflows.

---

## Phase 2: Remove Jinja2/Datastar, React-Only Frontend

- [ ] 2.1 Audit all Sanic routes that serve HTML — list every `render()` / `jinja2_render()` call
- [ ] 2.2 Remove Jinja2 template rendering from Sanic (keep JSON API only)
- [ ] 2.3 Remove `templates/` directory and Jinja2 dependencies
- [ ] 2.4 Remove Datastar-related static files and CDN references
- [ ] 2.5 Update Sanic app factory — remove static file serving, template engine init
- [ ] 2.6 Verify all React pages still work against JSON API endpoints
- [ ] 2.7 Update Dockerfile to remove template-related build steps

**Acceptance:** `pip install` no longer includes jinja2. All UI served by React app. No HTML routes in Sanic.

---

## Phase 3: Discover Hub & Collaboration UI

Build the React frontend for cross-ecosystem discovery and collaboration.

- [ ] 3.1 Create `DiscoverHub` page with tabs: Ecosystems, Shares & Needs, Collaborations
- [ ] 3.2 Build `SharesNeedsList` component — filterable grid with type/category/ecosystem filters
- [ ] 3.3 Build `SharesNeedsForm` — create/edit share or need (domain-scoped)
- [ ] 3.4 Build `CollaborationsList` component — shows active collaborations with engagement tier badges
- [ ] 3.5 Build `CollaborationForm` — propose new collaboration between domains
- [ ] 3.6 Build `CollaborationDetail` page — shows terms, linked shares/needs, status, timeline
- [ ] 3.7 Add circle membership display to Domain detail page
- [ ] 3.8 Add multi-ecosystem toggle to sidebar (use new `toggleEcosystem`)
- [ ] 3.9 Update API client types for new endpoints

**Acceptance:** Users can browse shares/needs across ecosystems, propose collaborations, and view collaboration details.

---

## Phase 4: Compliance & Version Tracking

- [ ] 4.1 Create `POST /api/v1/compliance/generate` — triggers AI compliance summary generation
  - Reads all agreements, domains, proposals, conflicts for the ecosystem
  - Generates structured compliance report via LiteLLM
  - Stores in `compliance_summaries` table
- [ ] 4.2 Create `GET /api/v1/compliance/latest` — returns most recent summary
- [ ] 4.3 Create `GET /api/v1/compliance/history` — paginated compliance history
- [ ] 4.4 Build `ComplianceDashboard` React page
- [ ] 4.5 Add version fingerprint generation on agreement/domain create and update
  - SHA-256 of (title + text + version + status + updated_at)
- [ ] 4.6 Add version fingerprint to API responses and detail pages

**Acceptance:** Compliance summaries generate on demand, display in dashboard, and auto-regenerate on 30-day cycle.

---

## Phase 5: PWA Notifications & Cron Jobs

- [ ] 5.1 Add service worker to React app for PWA support
- [ ] 5.2 Implement push subscription endpoint: `POST /api/v1/notifications/subscribe`
- [ ] 5.3 Store push subscriptions in new `push_subscriptions` table
- [ ] 5.4 Create notification service: `neos_agent/services/notifications.py`
  - Web Push API (VAPID keys)
  - Notification types: agreement_review_due, consent_round_open, proposal_deadline, conflict_update
- [ ] 5.5 Add cron runner to Sanic lifecycle (or APScheduler)
  - 30-day: compliance summary regeneration
  - Daily: check agreement review dates, consent round deadlines, emergency auto-reversion
  - Push notifications for upcoming deadlines (7-day, 1-day warnings)
- [ ] 5.6 Add expired session/challenge cleanup to cron
- [ ] 5.7 Build notification preferences UI in React

**Acceptance:** PWA installable, push notifications fire for governance deadlines, compliance auto-regenerates monthly.

---

## Phase 6: Integration Testing & Seed Validation

- [ ] 6.1 Run full seed script, verify all 3 ecosystems + collaborations load
- [ ] 6.2 Test multi-ecosystem login flow (same DID, multiple ecosystems)
- [ ] 6.3 Test cross-ecosystem discovery (ecosystem A sees ecosystem B's shares)
- [ ] 6.4 Test collaboration proposal flow end-to-end
- [ ] 6.5 Test compliance summary generation
- [ ] 6.6 Test PWA notification subscription and delivery
- [ ] 6.7 Verify empty state handling (new ecosystem with zero data)
- [ ] 6.8 Verify "No Sultan" AI constraints in chat
- [ ] 6.9 Performance check: ensure N+1 queries are resolved

**Acceptance:** All flows work for 3-ecosystem scenario. Empty states display correctly. No security regressions.

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| LiteLLM compatibility issues | Keep anthropic SDK as fallback provider option |
| Jinja2 removal breaks undiscovered routes | Audit all routes before removal, test all React pages |
| PWA push requires HTTPS | Use self-signed certs in dev, Railway provides HTTPS in prod |
| Cron jobs don't survive container restarts | Use Railway cron or embed scheduler in Sanic lifecycle |
| Seed script breaks with model changes | Run seed as part of CI/test suite |
