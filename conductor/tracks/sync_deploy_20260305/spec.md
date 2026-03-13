# Specification: dApp Sync, Micro-Frontends & Railway Deploy

**Track ID:** sync_deploy_20260305
**Track Type:** feature
**Created:** 2026-03-05
**Priority:** P0
**Depends On:** agent_foundation_20260305, dashboard_views_20260305, agent_core_20260305

---

## Overview

This is the final track in the NEOS webservice platform build. It adds three capabilities that transform the single-server Sanic application into a decentralized, embeddable, production-deployed governance platform:

1. **GunDB P2P Data Sync** -- A CRDT-based peer-to-peer broadcast layer so that multiple synergy hubs can run their own relays and share governance data without a central server.
2. **IPFS Immutable Pinning** -- Content-addressed storage for governance artifacts that must never change (signed agreements, decision records, consent outcomes).
3. **Datastar Micro-Frontend Components** -- Self-contained, embeddable UI fragments that any hub can drop into their own website to display live governance data.
4. **Railway Multi-Service Deployment** -- Production deployment configuration for the Sanic app, PostgreSQL database, and GunDB relay as separate services on Railway.

The design philosophy follows NEOS principles: no single point of failure (P2P sync), no hidden authority (immutable records on IPFS), voluntary participation (hubs run their own relays), and local failure containment (GunDB/IPFS failures never break core governance operations).

## Background

The NEOS governance skill stack (54 skills across 10 layers) is complete in `neos-core/`. Three preceding agent tracks build the webservice foundation:

- **agent_foundation_20260305** -- Sanic server, PostgreSQL models (SQLAlchemy + Alembic), Datastar SSE integration, project scaffolding, API routing.
- **dashboard_views_20260305** -- Datastar HTML templates, dashboard views, governance workflow UIs (agreement forms, ACT progress, domain management).
- **agent_core_20260305** -- Claude agent integration, chat interface, skill-layer-aware governance assistant, tool definitions.

This track sits on top of all three. It does not modify their core functionality but extends the platform with sync, immutability, embeddability, and deployment.

## Functional Requirements

### FR-1: GunDB Relay Service

**Description:** A minimal Node.js server that acts as a GunDB relay node, enabling peer-to-peer data synchronization between NEOS hubs.

**Implementation:**
- `gun-relay/server.js` -- HTTP server (~20 lines) with Gun attached
- `gun-relay/package.json` -- Minimal dependencies (gun, express or http)
- `gun-relay/Dockerfile` -- node:20-slim base image
- The relay accepts WebSocket connections from browsers and other GunDB relays
- Relays auto-discover and sync with each other in a mesh topology
- Each synergy hub runs their own relay; no master node exists

**Acceptance Criteria:**
- AC-1.1: The relay starts on a configurable port (default 8765)
- AC-1.2: A GunDB client (browser or Node.js) can connect and write/read data
- AC-1.3: Two relays pointed at each other sync data bidirectionally within 5 seconds
- AC-1.4: The relay runs in a Docker container with node:20-slim base
- AC-1.5: The relay server.js is 30 lines of code or fewer
- AC-1.6: The relay exposes a health check endpoint at GET /health

### FR-2: Gun Bridge (Python Async Module)

**Description:** A Python async module that publishes governance records to the GunDB relay via WebSocket after every Postgres write. This bridges the ACID source-of-truth (PostgreSQL) with the CRDT broadcast layer (GunDB).

**Implementation:**
- `agent/src/neos_agent/sync/gun_bridge.py`
- Uses `websockets` library (async WebSocket client) or raw `asyncio` sockets
- Maintains a persistent WebSocket connection to the local GunDB relay with auto-reconnect
- Publishes to structured GunDB namespaces after Postgres writes

**Namespace Structure:**
```
neos.{ecosystem_id}.public.agreements     -- Public agreement metadata
neos.{ecosystem_id}.public.decisions      -- Public decision records
neos.{ecosystem_id}.public.proposals      -- Public proposal status/progress
neos.{ecosystem_id}.private.{encrypted}   -- Hub-private records (SEA encrypted)
neos.network.shared                       -- Cross-hub shared governance data
```

**SEA Encryption:**
- Hub-private records are encrypted with GunDB SEA (Security, Encryption, Authorization) before publishing
- SEA keypairs are generated per-hub and stored in environment configuration
- Public records are published in plaintext for transparency

**Graceful Degradation:**
- If the GunDB relay is unreachable, log a warning but do not fail the primary Postgres write
- Queue failed publishes for retry with exponential backoff (max 5 retries, max 60s delay)
- Connection manager handles reconnection transparently

**Acceptance Criteria:**
- AC-2.1: After an agreement is created in Postgres, its metadata appears in the GunDB relay within 2 seconds
- AC-2.2: After a proposal status changes, the updated status is published to GunDB
- AC-2.3: After a decision record is created, its holding and ratio appear in GunDB
- AC-2.4: If the GunDB relay is down, the primary Postgres operation still succeeds
- AC-2.5: If the GunDB relay comes back up, queued records are published
- AC-2.6: Private records are encrypted with SEA before publishing
- AC-2.7: The bridge maintains a persistent WebSocket with auto-reconnect (reconnect within 10s)

### FR-3: IPFS Pinning Service

**Description:** An async module that pins immutable governance documents to IPFS via the Pinata managed pinning API. This creates content-addressed, tamper-evident records of governance artifacts.

**Implementation:**
- `agent/src/neos_agent/sync/ipfs_pin.py`
- Uses `httpx` or `aiohttp` for async HTTP requests to Pinata API
- Pinning is fire-and-forget (async, does not block the primary operation)
- IPFS CID is stored back in the Postgres record and published to GunDB

**What Gets Pinned:**
| Artifact | Content Pinned | Trigger |
|----------|---------------|---------|
| Signed Agreement | Full agreement text + signatures + metadata | Agreement enters ACTIVE status |
| Decision Record | Holding + ratio + participant positions | Decision record is created |
| Consent Record | All consent positions + outcome + objections | Consent phase completes |
| Agreement Amendment | Amendment diff + rationale + approval record | Amendment is ratified |

**Configuration:**
- `PINATA_API_KEY` and `PINATA_SECRET_KEY` environment variables
- If either is not set, IPFS pinning is silently skipped (optional dependency)
- Pinata API endpoint: `https://api.pinata.cloud/pinning/pinJSONToIPFS`

**Storage:**
- New `ipfs_cid` column (nullable VARCHAR) on relevant Postgres models
- CID is also published alongside the record in GunDB
- CID format: `Qm...` (CIDv0) or `bafy...` (CIDv1)

**Acceptance Criteria:**
- AC-3.1: When an agreement is activated, its full text is pinned to IPFS via Pinata
- AC-3.2: The returned IPFS CID is stored in the Postgres `ipfs_cid` column
- AC-3.3: The CID is published to GunDB alongside the agreement record
- AC-3.4: If Pinata credentials are not configured, pinning is skipped without error
- AC-3.5: If Pinata API is unreachable, the primary operation still succeeds (log warning)
- AC-3.6: Pinned content includes a JSON envelope with: content, content_type, ecosystem_id, timestamp, neos_version
- AC-3.7: Each pin includes Pinata metadata with name and keyvalues for searchability

### FR-4: Embeddable Micro-Frontend Components

**Description:** Three self-contained Datastar components that external hub pages can embed to display live governance data. Each component is a server-rendered HTML fragment with Datastar data-attributes, CSS custom properties for theming, and independent SSE connections for live updates.

**Implementation:**
- `agent/src/neos_agent/views/components.py` -- Sanic route handlers
- `agent/src/neos_agent/templates/components/` -- Jinja2/Datastar templates

**Component 1: Agreement Card**
- Endpoint: `GET /components/agreement-card/{agreement_id}`
- Displays: title, type badge (governance/operational/inter-unit), status indicator, domain, next review date, creation date
- Self-updates via SSE: `data-on:load="@get('/components/agreement-card/{id}')"` with configurable polling interval (default 30s)
- Click-to-expand: shows full agreement text, signatories, version history
- Responsive: works at 300px minimum width

**Component 2: Proposal Status**
- Endpoint: `GET /components/proposal-status/{proposal_id}`
- Displays: ACT progress bar (three phases: Advice, Consent, Test), current phase highlighted, time remaining in current phase, proposer name
- Live updates via SSE stream: phase transitions update in real-time
- Visual states: pending (grey), active (blue), complete (green), blocked (red)

**Component 3: Domain Summary**
- Endpoint: `GET /components/domain-summary/{domain_id}`
- Displays: domain name, primary steward, health score (from governance-health-audit), active agreements count, open proposals count, member count
- Updates via SSE with 60-second interval

**Cross-Cutting Component Requirements:**
- Each component returns complete HTML with inline `<style>` and `data-*` attributes
- No dependencies on host page CSS or JS (except Datastar itself)
- CSS custom properties for theming:
  ```css
  --neos-primary: #2563eb;
  --neos-surface: #ffffff;
  --neos-text: #1e293b;
  --neos-border: #e2e8f0;
  --neos-success: #16a34a;
  --neos-warning: #ca8a04;
  --neos-danger: #dc2626;
  --neos-radius: 8px;
  --neos-font: system-ui, sans-serif;
  ```
- Host pages override these vars to match their design system
- CORS headers on all component endpoints (configurable allowed origins)
- Each component opens its own SSE connection for live data

**Acceptance Criteria:**
- AC-4.1: Agreement card renders with correct data when fetched by ID
- AC-4.2: Proposal status shows correct ACT phase and updates when phase changes
- AC-4.3: Domain summary displays accurate counts and health score
- AC-4.4: All components work when embedded in a foreign origin page (CORS)
- AC-4.5: Components use CSS custom properties that can be overridden by host page
- AC-4.6: Each component loads in under 2 seconds on a simulated 3G connection (< 50KB total)
- AC-4.7: Components degrade gracefully if SSE connection drops (show last known data, retry)

### FR-5: Embed System

**Description:** A JavaScript loader that enables one-line embedding of NEOS components in any web page.

**Implementation:**
- `agent/src/neos_agent/static/embed/loader.js` -- The embed loader script
- `agent/src/neos_agent/templates/components/embed-loader.html` -- Documentation/demo page

**Embed Pattern:**
```html
<script src="https://neos-hub.example.com/embed/loader.js"></script>
<neos-agreement data-agreement-id="AGR-001"></neos-agreement>
<neos-proposal data-proposal-id="PRP-001"></neos-proposal>
<neos-domain data-domain-id="DOM-001"></neos-domain>
```

**Loader Behavior:**
1. Check if Datastar is already loaded on the page; if not, inject the Datastar script tag
2. Register three custom elements: `<neos-agreement>`, `<neos-proposal>`, `<neos-domain>`
3. Each custom element, on `connectedCallback`, fetches the corresponding component from the NEOS server URL (determined from the loader script's `src` attribute)
4. Shadow DOM encapsulation: each component renders inside a shadow root for CSS isolation
5. The loader script is < 5KB minified

**Configuration:**
- Server URL is automatically derived from the script tag's `src` attribute
- Optional `data-theme` attribute on the script tag to load a preset theme
- Optional `data-poll-interval` attribute to override the default SSE polling interval

**Acceptance Criteria:**
- AC-5.1: A plain HTML page with only the script tag and custom elements renders NEOS components
- AC-5.2: Datastar is automatically injected if not already present
- AC-5.3: Custom elements fetch from the correct NEOS server URL
- AC-5.4: Components are isolated in Shadow DOM (host page CSS does not leak in)
- AC-5.5: The loader script is under 5KB
- AC-5.6: An embed demo page at `/embed/demo` shows all three components working

### FR-6: Railway Deployment Configuration

**Description:** Multi-service Railway deployment configuration that provisions the Sanic app, PostgreSQL database, and GunDB relay with minimal manual setup.

**Implementation:**
- `railway.toml` -- Top-level Railway configuration
- Updated `agent/Dockerfile` -- Production-ready with health check
- `gun-relay/Dockerfile` -- GunDB relay container
- Environment variable documentation

**Railway Services:**
| Service | Type | Base Image | Internal Port |
|---------|------|------------|---------------|
| sanic-app | Dockerfile | python:3.13-slim | 8000 |
| gun-relay | Dockerfile | node:20-slim | 8765 |
| postgres | Railway Plugin | (managed) | 5432 |

**Environment Variables:**
| Variable | Source | Required |
|----------|--------|----------|
| DATABASE_URL | Railway auto-inject (Postgres plugin) | Yes |
| ANTHROPIC_API_KEY | Manual (sealed) | Yes |
| GUN_RELAY_URL | Internal networking (`gun-relay.railway.internal:8765`) | Yes (auto) |
| PINATA_API_KEY | Manual | No |
| PINATA_SECRET_KEY | Manual | No |
| NEOS_ECOSYSTEM_ID | Manual (default: "omnione") | No |
| CORS_ALLOWED_ORIGINS | Manual (comma-separated) | No |
| SANIC_ENV | Set to "production" | Yes (auto) |

**Health Check:**
- Sanic: `GET /api/v1/health` returns `{"status": "ok", "version": "...", "services": {"postgres": "ok", "gun_relay": "ok|degraded", "ipfs": "ok|disabled"}}`
- GunDB relay: `GET /health` returns `{"status": "ok"}`
- Railway health check timeout: 30 seconds, interval: 60 seconds

**Cost Optimization:**
- Hobby plan: ~$5-10/month
- Auto-sleep after 30 minutes of inactivity (configurable)
- GunDB relay is lightweight (~30MB memory)

**Acceptance Criteria:**
- AC-6.1: `railway.toml` defines build and deploy settings for both services
- AC-6.2: Sanic Dockerfile builds and runs with `CMD` pointing to the Sanic entry point
- AC-6.3: GunDB relay Dockerfile builds and starts the relay server
- AC-6.4: Health check endpoint returns status of all sub-services
- AC-6.5: Application starts correctly with only DATABASE_URL and ANTHROPIC_API_KEY set
- AC-6.6: The application works with auto-provisioned Railway PostgreSQL (no manual DB setup)

### FR-7: End-to-End Governance Flow Test

**Description:** An automated test that exercises the complete governance lifecycle through the webservice, verifying that sync and pinning integrations fire correctly.

**Test Flow:**
1. Create an ecosystem (POST /api/v1/ecosystems)
2. Add a member (POST /api/v1/ecosystems/{id}/members)
3. Create an agreement (POST /api/v1/agreements)
4. Run ACT decision flow:
   a. Create proposal (POST /api/v1/proposals)
   b. Advice phase: submit advice (POST /api/v1/proposals/{id}/advice)
   c. Consent phase: submit consent (POST /api/v1/proposals/{id}/consent)
   d. Test phase: submit test results (POST /api/v1/proposals/{id}/test)
5. Register the agreement (POST /api/v1/agreements/{id}/register)
6. Create a decision record (POST /api/v1/decisions)

**Verification Points:**
- Each Postgres write is confirmed via GET query
- Mock GunDB relay receives published records at correct namespaces
- Mock Pinata API receives pin requests with correct content
- IPFS CID is stored in Postgres after pinning
- Chat interface can narrate the same flow (optional, integration test)

**Acceptance Criteria:**
- AC-7.1: The test runs end-to-end without manual intervention
- AC-7.2: All REST API endpoints return expected status codes and bodies
- AC-7.3: The mock GunDB relay receives at least 4 published records (agreement, proposal status x3, decision)
- AC-7.4: The mock Pinata API receives at least 2 pin requests (agreement, decision record)
- AC-7.5: IPFS CIDs are stored in Postgres records
- AC-7.6: The test completes in under 30 seconds

### FR-8: Documentation

**Description:** Comprehensive documentation covering setup, architecture, deployment, and embedding.

**Documents:**

1. **agent/README.md** -- Project overview
   - Architecture diagram (ASCII): Sanic + Postgres + GunDB + IPFS + Datastar
   - Local development setup (Python venv, Node.js for relay, Docker Compose)
   - API endpoint summary
   - Environment variable reference
   - Project structure overview

2. **agent/docs/deployment.md** -- Railway deployment guide
   - Step-by-step Railway setup (fork, connect repo, add Postgres plugin)
   - Environment variable configuration
   - Custom domain setup
   - Monitoring and logs
   - Cost breakdown

3. **agent/docs/embedding.md** -- Component embedding guide
   - Quick start (copy-paste snippet)
   - Available components and their attributes
   - Theming with CSS custom properties
   - CORS configuration
   - Troubleshooting

4. **agent/docs/dapp-sync.md** -- Decentralized sync guide
   - Architecture: Postgres (truth) + GunDB (broadcast) + IPFS (immutable)
   - Running your own GunDB relay
   - Joining the mesh network
   - Data namespaces and encryption
   - IPFS pinning configuration

**Acceptance Criteria:**
- AC-8.1: README includes working local dev setup instructions
- AC-8.2: Deployment guide covers Railway setup from zero to running
- AC-8.3: Embedding guide includes copy-paste-ready code snippets
- AC-8.4: dApp sync guide explains the three-tier architecture (Postgres/GunDB/IPFS)
- AC-8.5: All env vars are documented with descriptions and defaults

---

## Non-Functional Requirements

### NFR-1: Fault Isolation
GunDB bridge failures and IPFS pinning failures must never cause a 500 error or prevent a governance operation from completing. These are best-effort broadcast/archive layers. The Postgres write is the only operation that must succeed.

### NFR-2: Performance
- Micro-frontend components must be under 50KB each (HTML + inline CSS + data attributes)
- Components must render in under 2 seconds on a simulated 3G connection
- GunDB publishing must not add more than 200ms latency to any API response (fire-and-forget async)
- IPFS pinning must be fully async (zero added latency to the API response)

### NFR-3: Security
- SEA encryption for all hub-private records before GunDB publishing
- CORS headers with configurable allowed origins (no wildcard `*` in production)
- No secrets in client-side code (embed loader only contains the server URL)
- Pinata API keys are server-side only, never exposed to clients
- ANTHROPIC_API_KEY stored as sealed variable in Railway

### NFR-4: Portability
- No Railway-specific code in the application itself (Railway config is external: railway.toml, Dockerfiles, env vars)
- The application must run equally well with `docker compose up` locally
- GunDB relay is a standard Gun server; any Gun-compatible relay can join the mesh

### NFR-5: Observability
- Health check endpoint reports status of all sub-services (Postgres, GunDB, IPFS/Pinata)
- Structured logging for sync events: `gun.publish`, `gun.connect`, `gun.reconnect`, `ipfs.pin`, `ipfs.fail`
- Log levels: INFO for successful operations, WARNING for degraded operations, ERROR for failures

### NFR-6: Cost Efficiency
- Railway Hobby plan target: $5-10/month
- GunDB relay memory footprint: < 50MB
- Auto-sleep for cost optimization during low-traffic periods

---

## User Stories

### US-1: Hub Operator Runs a Relay
**As** a synergy hub operator,
**I want** to run my own GunDB relay node,
**So that** my hub's governance data stays synchronized with the network without depending on a central server.

**Given** a hub operator has Docker installed
**When** they run `docker run neos-gun-relay`
**Then** the relay starts and accepts connections
**And** data written by connected clients syncs to other relays in the mesh

### US-2: Governance Architect Pins an Agreement
**As** a governance architect,
**I want** signed agreements to be automatically pinned to IPFS,
**So that** there is a tamper-evident, permanent record that no one can alter.

**Given** an agreement has been signed by all required parties
**When** the agreement transitions to ACTIVE status
**Then** the full agreement text and metadata are pinned to IPFS via Pinata
**And** the IPFS CID is stored in the database record

### US-3: Hub Embeds Governance Widget
**As** a hub website maintainer,
**I want** to embed a live agreement card on my hub's public page,
**So that** visitors can see our active governance agreements without navigating to the NEOS platform.

**Given** a hub page includes the NEOS embed script tag
**When** a `<neos-agreement>` custom element is placed on the page
**Then** the agreement card renders with live data from the NEOS server
**And** the card updates automatically when the agreement changes

### US-4: Developer Deploys to Production
**As** a developer,
**I want** to deploy the entire NEOS platform to Railway with minimal configuration,
**So that** I can have a production instance running in under 15 minutes.

**Given** the developer has a Railway account and the repo connected
**When** they configure the required environment variables (ANTHROPIC_API_KEY)
**Then** Railway auto-provisions PostgreSQL, builds both services, and the platform is live
**And** the health check confirms all services are operational

### US-5: Agent Publishes Decision to Network
**As** a NEOS governance agent,
**I want** every decision record to be broadcast to the P2P network,
**So that** all connected hubs see governance activity in near-real-time.

**Given** an ACT decision process completes (consent phase passes)
**When** a decision record is created in PostgreSQL
**Then** the record metadata is published to `neos.{ecosystem}.public.decisions` in GunDB
**And** the full decision content is pinned to IPFS
**And** both the GunDB entry and Postgres record contain the IPFS CID

---

## Technical Considerations

### Three-Tier Data Architecture
```
PostgreSQL (Source of Truth)
    |
    |--- write-through ---> GunDB (P2P Broadcast/Sync)
    |                           |
    |                           +--- other relays (mesh)
    |
    +--- async pin ---------> IPFS/Pinata (Immutable Archive)
                                  |
                                  +--- CID stored back in Postgres + GunDB
```

- PostgreSQL is always the authoritative source. No governance operation reads from GunDB.
- GunDB is a broadcast/sync layer for near-real-time distribution across hubs.
- IPFS is a write-once archive for artifacts that must be tamper-evident.

### GunDB Integration Pattern
- The Gun bridge is called as a post-commit hook, not a pre-commit hook
- If GunDB is down, the operation succeeds and the publish is queued
- The bridge uses `asyncio.create_task()` to fire-and-forget publishes
- Connection pooling: one persistent WebSocket per Sanic worker

### IPFS Integration Pattern
- Pinning uses Pinata's JSON API (no IPFS node needed)
- Content is JSON-serialized with a standard envelope format
- CID is written back to Postgres in a separate async update
- If CID write-back fails, the pin still exists (orphaned pins are acceptable)

### Micro-Frontend Isolation
- Shadow DOM provides CSS isolation from host pages
- Each component manages its own SSE connection lifecycle
- Components are stateless on the server (no session required)
- CORS is configured per-deployment, not hardcoded

### Railway Networking
- Sanic and GunDB relay communicate via Railway internal networking
- GunDB relay URL: `http://gun-relay.railway.internal:8765`
- PostgreSQL URL: auto-injected by Railway as `DATABASE_URL`
- External traffic goes to Sanic only; GunDB relay is internal-only by default

---

## Out of Scope

- **Mobile native apps** -- Components are web-only (responsive, but not native)
- **GunDB as primary database** -- GunDB is broadcast-only; Postgres remains the source of truth
- **IPFS node hosting** -- We use Pinata managed pinning, not a self-hosted IPFS node
- **Multi-region deployment** -- Single Railway region; multi-region is a future concern
- **Custom domain SSL** -- Railway provides SSL automatically; custom domain setup is documented but not automated
- **Real-time collaborative editing** -- Components are read-only displays, not collaborative editors
- **Payment/billing integration** -- Railway billing is handled through the Railway dashboard
- **WebRTC direct P2P** -- We use GunDB relay-mediated sync, not direct browser-to-browser
- **Offline-first PWA** -- Components require server connectivity; offline support is future work

---

## Open Questions

1. **GunDB relay authentication** -- Should relays require authentication to join the mesh, or is the mesh open? Initial implementation: open mesh with namespace-based access control. Private data is encrypted with SEA, so even an unauthorized relay cannot read it.

2. **IPFS content retention** -- Pinata free tier has storage limits. Should we implement content rotation (unpin old records after N months)? Initial implementation: pin everything, monitor usage.

3. **Component SSE connection limits** -- If a page embeds many components, each opens its own SSE connection. Should we implement connection multiplexing? Initial implementation: one SSE per component (simple). Optimize if connection limits become an issue.

4. **GunDB namespace governance** -- Who controls the namespace schema? Can hubs extend the namespace with their own data? Initial implementation: NEOS-defined namespaces only. Hub-specific namespaces are a future extension.

5. **Cross-hub identity** -- GunDB SEA keypairs are per-hub. How do we verify that a record from Hub A is authentic when viewed from Hub B? Initial implementation: trust the relay mesh. Cross-hub identity verification is a future track.
