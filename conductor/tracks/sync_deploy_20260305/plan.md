# Implementation Plan: dApp Sync, Micro-Frontends & Railway Deploy

**Track ID:** sync_deploy_20260305
**Phases:** 5
**Tasks:** 20
**Estimated Duration:** 2-3 days
**Depends On:** agent_foundation_20260305, dashboard_views_20260305, agent_core_20260305

---

## Overview

This plan builds the final layer of the NEOS webservice platform in five phases:

1. **Phase 1: GunDB Relay & Bridge** -- Stand up the P2P relay and the Python bridge that publishes governance records after Postgres writes.
2. **Phase 2: IPFS Pinning** -- Add immutable content pinning via Pinata with CID storage.
3. **Phase 3: Micro-Frontend Components** -- Build three embeddable Datastar components and the embed loader system.
4. **Phase 4: Railway Deployment** -- Configure multi-service Railway deployment with Dockerfiles and health checks.
5. **Phase 5: E2E Testing & Documentation** -- Validate the full governance flow and write all documentation.

Each phase ends with a verification checkpoint. Tasks follow TDD methodology where applicable (Red: write failing test, Green: implement to pass, Refactor: clean up).

---

## Phase 1: GunDB Relay & Bridge

**Goal:** Stand up a minimal GunDB relay service and build the Python async bridge that publishes governance records to GunDB after every Postgres write.

### Task 1: Create GunDB Relay Service

**Description:** Write the minimal Node.js GunDB relay server, package.json, and Dockerfile.

**Files:**
- `agent/gun-relay/server.js`
- `agent/gun-relay/package.json`
- `agent/gun-relay/Dockerfile`

**Steps:**
1. Create `package.json` with `gun` dependency and start script
2. Write `server.js`: HTTP server with Gun attached, health check at `/health`, configurable port via `PORT` env var (default 8765)
3. Write `Dockerfile`: node:20-slim, copy package files, npm ci --production, expose port, CMD node server.js
4. Verify: `docker build` succeeds, container starts, `/health` returns 200

**Acceptance Criteria:** AC-1.1, AC-1.2, AC-1.4, AC-1.5, AC-1.6

---

### Task 2: Write Gun Bridge Tests (TDD Red)

**Description:** Write test_gun_bridge.py with tests that define the expected behavior of the GunDB bridge module. All tests should fail initially (no implementation yet).

**File:** `agent/tests/test_gun_bridge.py`

**Test Cases:**
1. `test_publish_agreement_to_gun` -- After creating an agreement dict, the bridge publishes to `neos.{ecosystem}.public.agreements`
2. `test_publish_proposal_status` -- After a proposal phase changes, the bridge publishes to `neos.{ecosystem}.public.proposals`
3. `test_publish_decision_record` -- After a decision record is created, the bridge publishes to `neos.{ecosystem}.public.decisions`
4. `test_graceful_degradation` -- If WebSocket connection fails, the bridge logs a warning but does not raise
5. `test_auto_reconnect` -- If the connection drops, the bridge reconnects within 10 seconds
6. `test_retry_queue` -- Failed publishes are queued and retried when connection is restored
7. `test_sea_encryption` -- Private records are encrypted before publishing

**Approach:** Use `unittest.mock` to mock the WebSocket connection. Use `asyncio` test patterns (`pytest-asyncio` or `unittest.IsolatedAsyncioTestCase`).

**Acceptance Criteria:** AC-2.1 through AC-2.7 (test definitions)

---

### Task 3: Implement Gun Bridge Module (TDD Green)

**Description:** Implement the GunDB bridge module to pass all tests from Task 2.

**File:** `agent/src/neos_agent/sync/__init__.py`, `agent/src/neos_agent/sync/gun_bridge.py`

**Implementation:**
1. `GunBridge` class with:
   - `__init__(relay_url, ecosystem_id)` -- configuration
   - `async connect()` -- establish persistent WebSocket to relay
   - `async publish(namespace, key, data)` -- write data to GunDB namespace
   - `async publish_agreement(agreement)` -- format and publish agreement metadata
   - `async publish_proposal(proposal)` -- format and publish proposal status
   - `async publish_decision(decision)` -- format and publish decision record
   - `async _reconnect()` -- auto-reconnect with exponential backoff
   - `_encrypt_private(data, keypair)` -- SEA encryption for private records
2. Connection manager: persistent WebSocket with heartbeat
3. Retry queue: `asyncio.Queue` for failed publishes, drained on reconnect
4. Graceful degradation: all publish methods catch connection errors and log warnings

**Acceptance Criteria:** AC-2.1 through AC-2.7

---

### Task 4: Integrate Gun Bridge with Sanic Event Handlers

**Description:** Hook the GunDB bridge into the Sanic application lifecycle so that governance operations automatically publish to GunDB after Postgres writes.

**Files:**
- `agent/src/neos_agent/sync/hooks.py` (new: event handler registration)
- Updates to existing Sanic route handlers or middleware

**Implementation:**
1. Create `SyncHooks` class that registers post-write hooks for:
   - Agreement creation/update -> `bridge.publish_agreement()`
   - Proposal phase change -> `bridge.publish_proposal()`
   - Decision record creation -> `bridge.publish_decision()`
2. Initialize `GunBridge` in Sanic `app.before_server_start` listener
3. Use `asyncio.create_task()` for fire-and-forget publishing (non-blocking)
4. Configure via env vars: `GUN_RELAY_URL` (required for sync, optional overall)
5. If `GUN_RELAY_URL` is not set, sync hooks are not registered (standalone mode)

**Acceptance Criteria:** AC-2.1, AC-2.2, AC-2.3, AC-2.4

---

### Task 5: Verify P2P Sync Between Two Relays

**Description:** Integration test verifying that two GunDB relays discover each other and sync data bidirectionally.

**Steps:**
1. Start two GunDB relay containers (relay-a on port 8765, relay-b on port 8766)
2. Configure relay-a to peer with relay-b and vice versa
3. Write data to relay-a via WebSocket
4. Read data from relay-b and verify it matches
5. Write data to relay-b
6. Read from relay-a and verify bidirectional sync
7. Verify sync completes within 5 seconds

**Verification:** Manual steps with Docker Compose or scripted integration test. [checkpoint marker]

**Acceptance Criteria:** AC-1.3

---

## Phase 2: IPFS Pinning

**Goal:** Add IPFS immutable pinning for governance artifacts via the Pinata API, with CID storage in Postgres and GunDB.

### Task 6: Write IPFS Pinning Tests (TDD Red)

**Description:** Write test_ipfs_pin.py with tests defining expected Pinata API interaction, CID storage, and graceful degradation.

**File:** `agent/tests/test_ipfs_pin.py`

**Test Cases:**
1. `test_pin_agreement_to_ipfs` -- Pinning an agreement sends correct JSON to Pinata API and returns a CID
2. `test_pin_decision_record` -- Pinning a decision record includes holding, ratio, and positions
3. `test_pin_content_envelope` -- Pinned content is wrapped in standard JSON envelope (content, content_type, ecosystem_id, timestamp, neos_version)
4. `test_cid_stored_in_record` -- After pinning, the CID is written back to the record dict
5. `test_skip_when_unconfigured` -- If PINATA_API_KEY is not set, pinning is silently skipped
6. `test_graceful_failure` -- If Pinata API returns an error, log warning but do not raise
7. `test_pinata_metadata` -- Pin request includes Pinata metadata with name and keyvalues

**Approach:** Mock the HTTP client (httpx or aiohttp). Use `os.environ` patching for configuration tests.

**Acceptance Criteria:** AC-3.1 through AC-3.7 (test definitions)

---

### Task 7: Implement IPFS Pinning Module (TDD Green)

**Description:** Implement the IPFS pinning module to pass all tests from Task 6.

**File:** `agent/src/neos_agent/sync/ipfs_pin.py`

**Implementation:**
1. `IPFSPinner` class with:
   - `__init__(api_key, secret_key)` -- configuration (from env vars)
   - `@classmethod from_env()` -- factory that reads PINATA_API_KEY and PINATA_SECRET_KEY
   - `async pin_json(content, name, metadata)` -- pin JSON to IPFS via Pinata API
   - `async pin_agreement(agreement)` -- wrap agreement in envelope, pin, return CID
   - `async pin_decision(decision)` -- wrap decision record in envelope, pin, return CID
   - `async pin_consent(consent)` -- wrap consent record in envelope, pin, return CID
   - `is_configured` property -- returns True if API keys are set
2. Standard JSON envelope format:
   ```json
   {
     "content": { ... },
     "content_type": "agreement|decision|consent",
     "ecosystem_id": "omnione",
     "timestamp": "2026-03-05T12:00:00Z",
     "neos_version": "1.0.0"
   }
   ```
3. Pinata API interaction via httpx AsyncClient
4. Error handling: catch all httpx errors, log, return None for CID

**Acceptance Criteria:** AC-3.1 through AC-3.7

---

### Task 8: Add IPFS CID Column and Hook into Sync Pipeline

**Description:** Add the `ipfs_cid` column to relevant Postgres models via Alembic migration and integrate IPFS pinning into the sync hooks.

**Files:**
- New Alembic migration file
- Update `agent/src/neos_agent/sync/hooks.py` -- add IPFS pinning to post-write hooks
- Update relevant SQLAlchemy models to include `ipfs_cid = Column(String, nullable=True)`

**Implementation:**
1. Add `ipfs_cid` nullable VARCHAR column to: agreements, decisions, consent_records (via Alembic migration)
2. In sync hooks, after Postgres write:
   a. Fire-and-forget: `asyncio.create_task(pinner.pin_agreement(agreement))`
   b. On CID return, async update the Postgres record with the CID
   c. Publish CID to GunDB alongside the record
3. If `IPFSPinner.is_configured` is False, skip all pinning hooks

**Verification:** Create an agreement, verify `ipfs_cid` is populated after async pin completes. [checkpoint marker]

**Acceptance Criteria:** AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5

---

## Phase 3: Micro-Frontend Components

**Goal:** Build three embeddable Datastar components and the JavaScript embed loader system.

### Task 9: Write Component Endpoint Tests (TDD Red)

**Description:** Write test_components.py with tests for the three component endpoints and the embed system.

**File:** `agent/tests/test_components.py`

**Test Cases:**
1. `test_agreement_card_renders` -- GET /components/agreement-card/{id} returns HTML with agreement data
2. `test_agreement_card_contains_datastar_attrs` -- Response includes `data-on:load` and `data-store` attributes
3. `test_proposal_status_renders` -- GET /components/proposal-status/{id} returns HTML with ACT progress
4. `test_proposal_status_sse` -- SSE endpoint streams phase transition updates
5. `test_domain_summary_renders` -- GET /components/domain-summary/{id} returns HTML with domain data
6. `test_cors_headers` -- All component endpoints include Access-Control-Allow-Origin header
7. `test_component_size_under_50kb` -- Each component response is under 50KB
8. `test_css_custom_properties` -- Components use `--neos-*` CSS custom properties
9. `test_embed_loader_served` -- GET /embed/loader.js returns JavaScript
10. `test_embed_demo_page` -- GET /embed/demo returns an HTML page with all three components

**Approach:** Use Sanic test client for HTTP assertions. Parse HTML responses for expected elements.

**Acceptance Criteria:** AC-4.1 through AC-4.7, AC-5.1 through AC-5.6 (test definitions)

---

### Task 10: Implement Component Endpoints (TDD Green)

**Description:** Implement the Sanic route handlers for the three micro-frontend components.

**File:** `agent/src/neos_agent/views/components.py`

**Implementation:**
1. Sanic Blueprint `components_bp` with routes:
   - `GET /components/agreement-card/<agreement_id>`
   - `GET /components/proposal-status/<proposal_id>`
   - `GET /components/domain-summary/<domain_id>`
2. Each endpoint:
   a. Queries Postgres for the record
   b. Renders the corresponding Jinja2 template with Datastar attributes
   c. Returns HTML with CORS headers
3. CORS middleware for component routes:
   - `Access-Control-Allow-Origin`: from CORS_ALLOWED_ORIGINS env var (default: `*` in dev)
   - `Access-Control-Allow-Methods`: GET, OPTIONS
   - `Access-Control-Allow-Headers`: Content-Type
4. SSE endpoints for live updates:
   - `GET /components/agreement-card/<agreement_id>/stream`
   - `GET /components/proposal-status/<proposal_id>/stream`
   - `GET /components/domain-summary/<domain_id>/stream`
5. Register blueprint in Sanic app

**Acceptance Criteria:** AC-4.1, AC-4.2, AC-4.3, AC-4.4

---

### Task 11: Write Component Templates

**Description:** Create the Jinja2/Datastar HTML templates for each component with CSS custom properties and self-contained styling.

**Files:**
- `agent/src/neos_agent/templates/components/agreement-card.html`
- `agent/src/neos_agent/templates/components/proposal-status.html`
- `agent/src/neos_agent/templates/components/domain-summary.html`

**Implementation:**

**Agreement Card Template:**
- Title, type badge (governance/operational/inter-unit), status indicator (active/draft/sunset)
- Domain name, next review date, creation date
- `data-on:load="@get('/components/agreement-card/{{ id }}')"` with 30s interval for self-refresh
- Click-to-expand section with full text and signatories
- Inline `<style>` using `--neos-*` CSS custom properties
- Responsive: min-width 300px, flex layout

**Proposal Status Template:**
- Three-phase ACT progress bar: Advice -> Consent -> Test
- Current phase highlighted with accent color
- Time remaining (countdown or "awaiting input")
- Proposer name and proposal title
- `data-on:load` with SSE stream connection for live phase updates
- Visual states: pending (grey), active (blue), complete (green), blocked (red)

**Domain Summary Template:**
- Domain name and description
- Primary steward name and role
- Health score gauge (0-100, from governance-health-audit)
- Counts: active agreements, open proposals, members
- 60-second SSE refresh interval

**All Templates:**
- Complete, self-contained HTML fragments (no external CSS/JS dependencies beyond Datastar)
- Under 50KB per template
- CSS custom properties with sensible defaults:
  ```css
  :host {
    --neos-primary: var(--neos-primary, #2563eb);
    --neos-surface: var(--neos-surface, #ffffff);
    --neos-text: var(--neos-text, #1e293b);
    --neos-border: var(--neos-border, #e2e8f0);
    --neos-success: var(--neos-success, #16a34a);
    --neos-warning: var(--neos-warning, #ca8a04);
    --neos-danger: var(--neos-danger, #dc2626);
    --neos-radius: var(--neos-radius, 8px);
    --neos-font: var(--neos-font, system-ui, sans-serif);
  }
  ```

**Acceptance Criteria:** AC-4.5, AC-4.6, AC-4.7

---

### Task 12: Implement Embed Loader System

**Description:** Create the JavaScript embed loader and demo page that enables one-line embedding of NEOS components in any web page.

**Files:**
- `agent/src/neos_agent/static/embed/loader.js`
- `agent/src/neos_agent/templates/components/embed-loader.html` (demo page)
- Update `agent/src/neos_agent/views/components.py` to serve embed routes

**Implementation:**

**loader.js:**
1. Self-executing function that:
   a. Determines the NEOS server URL from the script tag's `src` attribute
   b. Checks if Datastar is loaded; if not, injects the Datastar `<script>` tag
   c. Defines three custom elements: `NeosAgreement`, `NeosProposal`, `NeosDomain`
   d. Each custom element:
      - Creates a Shadow DOM root in `connectedCallback`
      - Reads `data-agreement-id` / `data-proposal-id` / `data-domain-id` attribute
      - Fetches the component HTML from `{serverUrl}/components/{type}/{id}`
      - Inserts the response into the shadow root
      - Sets up SSE connection for live updates
   e. Registers elements as `<neos-agreement>`, `<neos-proposal>`, `<neos-domain>`
2. Target: under 5KB minified (no build step; hand-written, clean JS)

**Demo Page:**
- Route: `GET /embed/demo`
- Shows all three component types with sample data
- Includes the embed snippet users can copy
- Demonstrates theme override via CSS custom properties

**Verification:** Open demo page in browser, verify all three components render and update. [checkpoint marker]

**Acceptance Criteria:** AC-5.1 through AC-5.6

---

## Phase 4: Railway Deployment

**Goal:** Configure multi-service Railway deployment with production-ready Dockerfiles and health checks.

### Task 13: Write Railway Configuration

**Description:** Create the railway.toml configuration file for multi-service deployment.

**File:** `railway.toml`

**Implementation:**
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "agent/Dockerfile"

[deploy]
healthcheckPath = "/api/v1/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Notes:**
- Railway auto-detects services from the repo structure
- GunDB relay is configured as a separate service via Railway dashboard or `railway.json`
- PostgreSQL is added as a Railway plugin (auto-provisions, injects DATABASE_URL)
- Document the manual Railway setup steps in the deployment guide (Task 19)

**Acceptance Criteria:** AC-6.1

---

### Task 14: Update Sanic Dockerfile for Production

**Description:** Write or update the Sanic application Dockerfile with production settings, health check, and optimized layers.

**File:** `agent/Dockerfile`

**Implementation:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (layer caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python package
RUN pip install --no-cache-dir -e .

# Copy remaining files
COPY templates/ ./templates/
COPY static/ ./static/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Environment
ENV SANIC_ENV=production
ENV SANIC_HOST=0.0.0.0
ENV SANIC_PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["sanic", "neos_agent.app:create_app", "--host=0.0.0.0", "--port=8000", "--workers=2"]
```

**Acceptance Criteria:** AC-6.2, AC-6.4

---

### Task 15: Write GunDB Relay Dockerfile and Health Check

**Description:** Finalize the GunDB relay Dockerfile for Railway deployment with internal networking configuration.

**File:** `agent/gun-relay/Dockerfile` (created in Task 1, now updated for Railway)

**Implementation:**
1. Verify Dockerfile uses node:20-slim, installs gun, exposes configurable port
2. Add health check: `HEALTHCHECK CMD node -e "require('http').get('http://localhost:8765/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"`
3. Configure for Railway internal networking:
   - The relay listens on `0.0.0.0:8765`
   - Sanic connects to it via `http://gun-relay.railway.internal:8765`
   - External access is not needed (internal service only)
4. Document in deployment guide how to add as a second Railway service

**Acceptance Criteria:** AC-6.3

---

### Task 16: Implement Health Check Endpoint and Seed Data

**Description:** Write the comprehensive health check endpoint that reports status of all sub-services, and create seed data for initial deployment.

**Files:**
- Update health check in Sanic app (new or enhanced `/api/v1/health` handler)
- `agent/scripts/seed_data.py` -- optional seed script for demo deployment

**Implementation:**

**Health Check:**
```python
@app.get("/api/v1/health")
async def health(request):
    status = {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "postgres": await check_postgres(),    # "ok" or "error"
            "gun_relay": await check_gun_relay(),   # "ok", "degraded", or "error"
            "ipfs": check_ipfs_configured(),        # "ok", "disabled", or "error"
        }
    }
    # Return 200 if postgres is ok (core requirement)
    # Return 503 if postgres is down
    http_status = 200 if status["services"]["postgres"] == "ok" else 503
    return json(status, status=http_status)
```

**Seed Data Script:**
- Creates a demo ecosystem ("OmniOne Demo")
- Adds sample members with different profiles (Steward, Builder, TownHall)
- Creates one sample agreement and one sample proposal
- Useful for first-time Railway deployment verification

**Verification:** Deploy locally with Docker Compose, hit /api/v1/health, verify all services report status. Run seed script and verify data appears. [checkpoint marker]

**Acceptance Criteria:** AC-6.4, AC-6.5, AC-6.6

---

## Phase 5: E2E Testing & Documentation

**Goal:** Validate the complete governance lifecycle through the webservice and write comprehensive documentation.

### Task 17: Write End-to-End Governance Flow Test

**Description:** Automated test that exercises the full governance lifecycle: create ecosystem, add member, create agreement, run ACT flow, register, create decision record. Verifies sync and pinning integrations.

**File:** `agent/tests/test_e2e_governance.py`

**Test Flow:**
```python
async def test_full_governance_lifecycle():
    # 1. Create ecosystem
    eco = await client.post("/api/v1/ecosystems", json={...})
    assert eco.status == 201

    # 2. Add member
    member = await client.post(f"/api/v1/ecosystems/{eco_id}/members", json={...})
    assert member.status == 201

    # 3. Create agreement
    agreement = await client.post("/api/v1/agreements", json={...})
    assert agreement.status == 201

    # 4. ACT decision flow
    proposal = await client.post("/api/v1/proposals", json={...})
    assert proposal.status == 201

    # 4a. Advice phase
    advice = await client.post(f"/api/v1/proposals/{prop_id}/advice", json={...})
    assert advice.status == 200

    # 4b. Consent phase
    consent = await client.post(f"/api/v1/proposals/{prop_id}/consent", json={...})
    assert consent.status == 200

    # 4c. Test phase
    test = await client.post(f"/api/v1/proposals/{prop_id}/test", json={...})
    assert test.status == 200

    # 5. Register agreement
    register = await client.post(f"/api/v1/agreements/{agr_id}/register")
    assert register.status == 200

    # 6. Create decision record
    decision = await client.post("/api/v1/decisions", json={...})
    assert decision.status == 201

    # Verify GunDB received records
    assert mock_gun_relay.received_count >= 4  # agreement, 3x proposal status, decision

    # Verify IPFS pins
    assert mock_pinata.pin_count >= 2  # agreement, decision record

    # Verify CID stored in Postgres
    agr = await client.get(f"/api/v1/agreements/{agr_id}")
    assert agr.json["ipfs_cid"] is not None
```

**Mock Setup:**
- Mock GunDB relay: simple WebSocket server that records all received messages
- Mock Pinata API: HTTP server that records all pin requests and returns fake CIDs
- Both mocks run as fixtures in the test

**Acceptance Criteria:** AC-7.1 through AC-7.6

---

### Task 18: Write agent/README.md

**Description:** Write the main project README with architecture overview, local dev setup, and API reference.

**File:** `agent/README.md`

**Contents:**
1. **Project Overview** -- What NEOS Agent is, what it does
2. **Architecture Diagram** (ASCII art):
   ```
   Browser/Embed  <-->  Sanic (Python)  <-->  PostgreSQL
                           |      |
                           |      +---------->  GunDB Relay  <--->  Other Relays
                           |
                           +----------------->  Pinata/IPFS
   ```
3. **Quick Start** -- Clone, venv, pip install, docker compose up, open browser
4. **Local Development** -- Python 3.13+, Node.js 20+ (for relay), PostgreSQL 16+, Docker (optional)
5. **API Endpoints** -- Summary table of all routes with methods and descriptions
6. **Environment Variables** -- Full reference table with descriptions, required/optional, defaults
7. **Project Structure** -- Directory tree with descriptions
8. **Testing** -- How to run tests (pytest, e2e, integration)
9. **Deployment** -- Link to docs/deployment.md

**Acceptance Criteria:** AC-8.1

---

### Task 19: Write Deployment and Embedding Guides

**Description:** Write the Railway deployment guide and the component embedding guide.

**Files:**
- `agent/docs/deployment.md`
- `agent/docs/embedding.md`
- `agent/docs/dapp-sync.md`

**Deployment Guide Contents:**
1. Prerequisites (Railway account, GitHub repo)
2. Step-by-step Railway setup:
   a. Create new project from GitHub repo
   b. Add PostgreSQL plugin
   c. Add GunDB relay as separate service (point to gun-relay/ directory)
   d. Configure environment variables
   e. Deploy
3. Custom domain configuration
4. Monitoring and logs (Railway dashboard)
5. Cost breakdown (Hobby plan: ~$5-10/month)
6. Troubleshooting common issues

**Embedding Guide Contents:**
1. Quick start (3-line code snippet)
2. Available components: agreement-card, proposal-status, domain-summary
3. Component attributes reference
4. Theming: CSS custom property overrides with examples
5. CORS: how to configure allowed origins
6. Advanced: multiple components, custom polling intervals
7. Troubleshooting: CORS errors, loading issues

**dApp Sync Guide Contents:**
1. Three-tier architecture explanation (Postgres/GunDB/IPFS)
2. Running your own GunDB relay (Docker one-liner)
3. Peering with other relays (mesh topology)
4. GunDB namespace reference
5. SEA encryption for private data
6. IPFS pinning: what gets pinned, how to verify, Pinata setup
7. Data flow diagram

**Acceptance Criteria:** AC-8.2, AC-8.3, AC-8.4, AC-8.5

---

### Task 20: Final Quality Gate

**Description:** Run all tests, verify all services deploy correctly, and confirm components embed properly. This is the final verification for the entire NEOS webservice platform.

**Checklist:**
- [ ] All unit tests pass (`pytest agent/tests/`)
- [ ] E2E governance flow test passes
- [ ] GunDB relay starts and accepts connections
- [ ] P2P sync works between two relays
- [ ] IPFS pinning works with valid Pinata credentials (or is gracefully skipped without)
- [ ] All three micro-frontend components render correctly
- [ ] Embed loader loads Datastar and registers custom elements
- [ ] Components work cross-origin (CORS)
- [ ] Health check endpoint reports all service statuses
- [ ] Sanic Dockerfile builds and runs
- [ ] GunDB relay Dockerfile builds and runs
- [ ] railway.toml is valid
- [ ] README and all documentation files are complete
- [ ] No hardcoded secrets in any file
- [ ] All environment variables are documented

**Verification:** Full test suite, manual smoke test of each component, Docker Compose up with all services. [checkpoint marker]

**Acceptance Criteria:** All FR and NFR acceptance criteria verified.

---

## Dependency Map

```
Phase 1: GunDB Relay & Bridge
  Task 1  (relay service)         ──┐
  Task 2  (bridge tests)          ──┤
  Task 3  (bridge impl)  ← T2    ──┤
  Task 4  (hook integration) ← T3──┤
  Task 5  (P2P verify) ← T1      ──┘ [checkpoint]

Phase 2: IPFS Pinning          ← Phase 1 (hooks infrastructure)
  Task 6  (pin tests)            ──┐
  Task 7  (pin impl) ← T6       ──┤
  Task 8  (DB + hooks) ← T7     ──┘ [checkpoint]

Phase 3: Micro-Frontends       ← Phase 1 (for SSE patterns)
  Task 9  (component tests)      ──┐
  Task 10 (endpoints) ← T9      ──┤
  Task 11 (templates) ← T10     ──┤
  Task 12 (embed loader) ← T11  ──┘ [checkpoint]

Phase 4: Railway Deploy        ← Phases 1-3 (all services built)
  Task 13 (railway.toml)        ──┐
  Task 14 (Sanic Dockerfile)    ──┤
  Task 15 (Relay Dockerfile)    ──┤
  Task 16 (health + seed) ← T13-15──┘ [checkpoint]

Phase 5: E2E & Docs            ← All phases
  Task 17 (E2E test)            ──┐
  Task 18 (README)              ──┤
  Task 19 (guides)              ──┤
  Task 20 (quality gate) ← T17-19──┘ [checkpoint]
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| GunDB WebSocket protocol is not well-documented for Python clients | Medium | Use raw WebSocket with JSON messages; Gun protocol is simple PUT/GET over WS |
| Pinata API rate limits on free tier | Low | Pin only on status transitions (not every edit); implement backoff |
| Shadow DOM compatibility in older browsers | Low | Target modern browsers; provide graceful fallback (render without shadow DOM) |
| Railway internal networking changes | Low | Use standard Docker networking patterns; Railway's internal DNS is stable |
| SSE connection limits per browser (6 per domain) | Medium | Document limit; implement connection multiplexing if needed in future |
| pygundb library may not be maintained | Medium | Use raw WebSocket instead of pygundb; Gun protocol is simple enough for direct implementation |

---

## Post-Track Verification

After all 20 tasks are complete, the NEOS webservice platform should demonstrate:

1. **Governance operations** work end-to-end through both REST API and chat interface
2. **Data syncs** to GunDB relay in near-real-time after every governance write
3. **Immutable records** are pinned to IPFS for signed agreements and decision records
4. **Embeddable components** render in any web page with live updates
5. **Production deployment** is one-command on Railway with auto-provisioned infrastructure
6. **Fault isolation** ensures GunDB/IPFS failures never break core governance operations
