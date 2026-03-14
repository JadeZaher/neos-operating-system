# NEOS Tracks

## Implementation Order

Tracks are ordered by layer number for sequential implementation. Each track's dependencies are satisfied by tracks above it.

```
1. Layers I + III (Foundation)     <- no dependencies
2. Layer II (Authority & Role)     <- depends on #1
3. Layer IV (Economic Coord)       <- depends on #1, #2
4. Layer V (Inter-Unit Coord)      <- depends on #1, #2, #3
5. Layer VI (Conflict & Repair)    <- depends on #1, #2
6. Layer VII (Safeguard & Capture) <- depends on #1
7. Layer VIII (Emergency Handling)  <- depends on #1, #6
8. Layer IX (Memory & Trace)       <- depends on #1
9. Layer X (Exit & Portability)    <- depends on #1, #6, #7
10. Global Packaging               <- depends on all
11. Agent Foundation               <- depends on #10 (scaffolding, skill loader, DB)
12. Dashboard & Views              <- depends on #11 (Datastar UI, CRUD views)
13. Agent Core                     <- depends on #11 (Claude Agent SDK, chat, tools)
14. Sync & Deploy                  <- depends on #11, #12, #13 (GunDB, IPFS, Railway)
15. Member Profile Harden          <- depends on #12 (bug fix track)
16. Chat & Messaging               <- depends on #11, #12, #13 (member-to-member messaging)
```

---

## Active Tracks

### 11. [ ] agent_foundation_20260305 -- Agent Foundation: Scaffolding, Skill Loader & Database
**Priority:** P0
**Type:** feature
**Status:** Planned
**Created:** 2026-03-05
**Depends on:** All 10 skill layer tracks (complete)

Build the foundation of the NEOS governance webservice: Sanic app factory, skill loader that parses SKILL.md files into structured dataclasses, dependency graph engine, in-memory skill registry, PostgreSQL database models (26 tables mapping to NEOS YAML templates), session management, configuration, and two API endpoints (health check and skill index).

**Components:**
- [ ] Project scaffolding (pyproject.toml, Dockerfile, config)
- [ ] Skill loader (parse SKILL.md frontmatter + sections)
- [ ] Dependency graph (DAG, topological sort, cycle detection)
- [ ] Skill registry (in-memory index, loaded at startup)
- [ ] Database models (26 SQLAlchemy async ORM models)
- [ ] DB session factory (async engine, Sanic lifecycle hooks)
- [ ] Alembic migrations config
- [ ] OmniOne seed data script
- [ ] Health endpoint (GET /api/v1/health)
- [ ] Skill index endpoint (GET /api/v1/skills)

**Phases:**
- [ ] Phase 1: Scaffolding (directory structure, pyproject.toml, Dockerfile, config)
- [ ] Phase 2: Skill Loader & Registry (loader, graph, registry with TDD)
- [ ] Phase 3: Database Models & Migrations (models, session, Alembic, seed data)
- [ ] Phase 4: Sanic App Factory & API (app factory, health, skills endpoints)

**Tech Stack:** Sanic 25.x, SQLAlchemy 2.0 async, asyncpg, Alembic, pydantic-settings, Python 3.12+

**Spec:** `conductor/tracks/agent_foundation_20260305/spec.md`
**Plan:** `conductor/tracks/agent_foundation_20260305/plan.md`

---

### 16. [x] chat_messaging_20260313 -- Chat & Direct Messaging System
**Priority:** P1
**Type:** feature
**Status:** Planned
**Created:** 2026-03-13
**Depends on:** agent_foundation_20260305 (complete), dashboard_views_20260305 (pending), agent_core_20260305 (pending)

Real-time member-to-member messaging with DM (1:1), group conversations (multi-party), and governance process integration. Uses Sanic native WebSocket for real-time delivery alongside existing SSE-based AI chat. Conversations can be linked to proposals, agreements, domains, and conflicts. Ecosystem-scoped with read receipts, unread counts, and member search.

**Deliverables:**
- [ ] 4 new database models (Conversation, ConversationParticipant, Message, ConversationLink)
- [ ] WebSocket ConnectionManager for real-time message delivery
- [ ] Authenticated WebSocket endpoint with JSON frame protocol
- [ ] REST/htmx endpoints for conversation CRUD, message pagination, member picker
- [ ] Messaging UI (two-panel layout, conversation list, message view, member picker)
- [ ] Governance entity integration (Discuss buttons, linked conversations, entity sharing)
- [ ] Sidebar navigation with unread message badge
- [ ] Message search across conversation history

**Phases:**
- [ ] Phase 1: Data Models & Migration (4 models, Alembic migration, seed fixtures)
- [ ] Phase 2: Connection Manager & WebSocket Infrastructure (ConnectionManager, WS auth, handlers)
- [ ] Phase 3: REST API & Conversation Management (conversation CRUD, messages, participants, links)
- [ ] Phase 4: Templates & UI (messaging page, conversation list/detail, member picker, base.html nav)
- [ ] Phase 5: Governance Integration (Discuss buttons on entity pages, ConversationLink, Discussions sections)
- [ ] Phase 6: Search, Polish & E2E Validation (message search, edge cases, exited member handling, performance)

**Tech Stack:** Sanic WebSocket, SQLAlchemy 2.0 async, Jinja2, htmx 2.x, Tailwind CSS 4.x (CDN)

**Spec:** `conductor/tracks/chat_messaging_20260313/spec.md`
**Plan:** `conductor/tracks/chat_messaging_20260313/plan.md`

---

## Completed Tracks

### 1. [x] foundation_20260301 -- Layers I + III: Agreement Layer + ACT Decision Engine
**Priority:** P0
**Layers:** I (Agreement), III (ACT Decision Engine)
**Status:** Complete
**Created:** 2026-03-01

Build the two foundational NEOS skill layers that everything else depends on. 11 governance skills across 2 layers, plus a global validation script and layer integration.

**Skills (11):**
- [x] agreement-creation (Layer I) -- P0 anchor
- [x] agreement-amendment (Layer I)
- [x] agreement-review (Layer I)
- [x] agreement-registry (Layer I)
- [x] universal-agreement-field (Layer I) -- P0 anchor
- [x] act-advice-phase (Layer III)
- [x] act-consent-phase (Layer III)
- [x] act-test-phase (Layer III)
- [x] proposal-creation (Layer III) -- P0 anchor
- [x] proposal-resolution (Layer III)
- [x] consensus-check (Layer III)

**Phases:**
- [x] Phase 1: Tooling and Scaffolding (validate_skill.py, directory structure, template)
- [x] Phase 2: Anchor Skills (agreement-creation, proposal-creation)
- [x] Phase 3: UAF + ACT Core Phases (universal-agreement-field, act-advice, act-consent, act-test)
- [x] Phase 4: Amendment, Consensus, Review (agreement-amendment, consensus-check, agreement-review)
- [x] Phase 5: Registry and Resolution (agreement-registry, proposal-resolution)
- [x] Phase 6: Layer Integration and Finalization (READMEs, cross-review, quality gates)

**Spec:** `conductor/tracks/foundation_20260301/spec.md`
**Plan:** `conductor/tracks/foundation_20260301/plan.md`

---

### 2. [x] authority_role_20260302 -- Layer II: Authority & Role
**Priority:** P0
**Layers:** II (Authority & Role)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301

Build 7 governance skills for domain definition (S3 11-element contract), role assignment, boundary negotiation, role transfer, domain review, role sunset, and member lifecycle. Includes a foundation integration phase that updates all 11 Layer I and III skills with formal authority references, resolving the structural weakness identified in the foundation review. Primary framework: Sociocracy 3.0 domain model. Secondary: Holacracy, Laloux Teal.

**Skills (7):**
- [x] domain-mapping (Layer II) -- P0 anchor
- [x] member-lifecycle (Layer II) -- P0
- [x] role-assignment (Layer II) -- P0
- [x] authority-boundary-negotiation (Layer II) -- P0
- [x] role-transfer (Layer II)
- [x] domain-review (Layer II)
- [x] role-sunset (Layer II)

**Phases:**
- [x] Phase 1: Scaffolding and Anchor Skill (domain-mapping)
- [x] Phase 2: Member Lifecycle and Role Assignment (member-lifecycle, role-assignment)
- [x] Phase 3: Boundary Negotiation and Role Transfer (authority-boundary-negotiation, role-transfer)
- [x] Phase 4: Domain Review and Role Sunset (domain-review, role-sunset)
- [x] Phase 5: Layer Integration and README (foundation updates, cross-review)
- [x] Phase 6: Quality Gate

**Spec:** `conductor/tracks/authority_role_20260302/spec.md`
**Plan:** `conductor/tracks/authority_role_20260302/plan.md`

---

### 3. [x] economic_coord_20260302 -- Layer IV: Economic Coordination
**Priority:** P1
**Layers:** IV (Economic Coordination)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301, authority_role_20260302

Build 5 governance skills for resource requests, funding pool stewardship, participatory allocation, commons monitoring, and access economy transition. Grounded in Ostrom's 8 commons governance principles with OmniOne Current-See and H.A.R.T. system as inline examples.

**Skills (5):**
- [x] resource-request (Layer IV) -- P0 anchor
- [x] funding-pool-stewardship (Layer IV) -- P0
- [x] participatory-allocation (Layer IV)
- [x] commons-monitoring (Layer IV)
- [x] access-economy-transition (Layer IV)

**Phases:**
- [x] Phase 1: Scaffolding and Anchor Skills (resource-request, funding-pool-stewardship)
- [x] Phase 2: Participatory Allocation
- [x] Phase 3: Commons Monitoring
- [x] Phase 4: Access Economy Transition and Layer Integration

**Spec:** `conductor/tracks/economic_coord_20260302/spec.md`
**Plan:** `conductor/tracks/economic_coord_20260302/plan.md`

---

### 4. [x] inter_unit_20260302 -- Layer V: Inter-Unit Coordination
**Priority:** P1
**Layers:** V (Inter-Unit Coordination)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301, authority_role_20260302, economic_coord_20260302

Build 5 governance skills for cross-AZPO requests, shared resource stewardship, federation agreements, inter-unit liaison roles, and polycentric conflict navigation. Grounded in Ostrom's polycentric governance, millet system structural pattern (minus the Sultan), and Holochain agent-centric architecture.

**Skills (5):**
- [x] cross-azpo-request (Layer V) -- P0 anchor
- [x] shared-resource-stewardship (Layer V) -- P0
- [x] federation-agreement (Layer V)
- [x] inter-unit-liaison (Layer V)
- [x] polycentric-conflict-navigation (Layer V)

**Phases:**
- [x] Phase 1: Scaffolding and Anchor Skill (cross-azpo-request)
- [x] Phase 2: Shared Resources and Federation (shared-resource-stewardship, federation-agreement)
- [x] Phase 3: Liaison Roles and Conflict Navigation (inter-unit-liaison, polycentric-conflict-navigation)
- [x] Phase 4: Layer Integration and Finalization

**Spec:** `conductor/tracks/inter_unit_20260302/spec.md`
**Plan:** `conductor/tracks/inter_unit_20260302/plan.md`

---

### 5. [x] conflict_repair_20260302 -- Layer VI: Conflict and Repair
**Priority:** P1
**Layers:** VI (Conflict and Repair)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301, authority_role_20260302

Build 6 governance skills for harm circles, NVC dialogue, repair agreements, escalation triage, coaching interventions, and community impact assessment. Grounded in Transformative Justice, Restorative Justice, NVC, and Ostrom's accessible conflict resolution principle. OmniOne's Solutionary Culture as inline example.

**Skills (6):**
- [x] harm-circle (Layer VI) -- P0 anchor
- [x] nvc-dialogue (Layer VI) -- P0
- [x] escalation-triage (Layer VI) -- P0
- [x] repair-agreement (Layer VI)
- [x] coaching-intervention (Layer VI)
- [x] community-impact-assessment (Layer VI)

**Phases:**
- [x] Phase 1: Scaffolding and Core Processes (harm-circle, nvc-dialogue)
- [x] Phase 2: Escalation Triage
- [x] Phase 3: Repair Agreements and Coaching (repair-agreement, coaching-intervention)
- [x] Phase 4: Community Impact Assessment
- [x] Phase 5: Layer Integration and Finalization

**Spec:** `conductor/tracks/conflict_repair_20260302/spec.md`
**Plan:** `conductor/tracks/conflict_repair_20260302/plan.md`

---

### 6. [x] safeguard_capture_20260302 -- Layer VII: Safeguard & Capture Detection
**Priority:** P0
**Layers:** VII (Safeguard & Capture Detection)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301

Build 5 governance skills for continuous governance health monitoring and structural capture resistance. Draws on Michels' Iron Law of Oligarchy, V-Dem Democracy Indicators, and research on capital, charisma, emergency, and ossification capture types. Skills observe, measure, and trigger safeguards when governance health degrades.

**Skills (5):**
- [x] governance-health-audit (Layer VII) -- P0 anchor
- [x] capture-pattern-recognition (Layer VII) -- P0
- [x] safeguard-trigger-design (Layer VII)
- [x] independent-monitoring (Layer VII)
- [x] structural-diversity-maintenance (Layer VII)

**Phases:**
- [x] Phase 1: Scaffolding and Anchor Skill (governance-health-audit)
- [x] Phase 2: Pattern Recognition and Trigger Design (capture-pattern-recognition, safeguard-trigger-design)
- [x] Phase 3: Monitoring and Diversity (independent-monitoring, structural-diversity-maintenance)
- [x] Phase 4: Layer Integration and Finalization

**Spec:** `conductor/tracks/safeguard_capture_20260302/spec.md`
**Plan:** `conductor/tracks/safeguard_capture_20260302/plan.md`

---

### 7. [x] emergency_handling_20260302 -- Layer VIII: Emergency Handling
**Priority:** P0
**Layers:** VIII (Emergency Handling)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301, safeguard_capture_20260302

Build 5 governance skills implementing Agamben-resistant emergency governance with circuit breaker states (Closed/Normal, Open/Crisis, Half-Open/Recovery) and mandatory auto-reversion. Every mechanism makes permanence structurally impossible. Follows the emergency lifecycle chronologically.

**Skills (5):**
- [x] emergency-criteria-design (Layer VIII) -- P0 anchor
- [x] pre-authorization-protocol (Layer VIII) -- P0
- [x] crisis-coordination (Layer VIII)
- [x] emergency-reversion (Layer VIII)
- [x] post-emergency-review (Layer VIII)

**Phases:**
- [x] Phase 1: Scaffolding and Entry Criteria (emergency-criteria-design, pre-authorization-protocol)
- [x] Phase 2: Crisis Operations (crisis-coordination)
- [x] Phase 3: Reversion and Review (emergency-reversion, post-emergency-review)
- [x] Phase 4: Layer Integration and Finalization

**Spec:** `conductor/tracks/emergency_handling_20260302/spec.md`
**Plan:** `conductor/tracks/emergency_handling_20260302/plan.md`

---

### 8. [x] memory_trace_20260302 -- Layer IX: Memory & Traceability
**Priority:** P0
**Layers:** IX (Memory & Traceability)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301

Build 5 governance skills for decision recording, precedent search, semantic tagging, agreement versioning, and precedent challenge. Defines a generic decision-record wrapper that accommodates any governance artifact from any layer. Primary framework: legal precedent system (stare decisis). Secondary: DAO governance memory, Git-style versioning.

**Skills (5):**
- [x] decision-record (Layer IX) -- P0 anchor
- [x] semantic-tagging (Layer IX)
- [x] precedent-search (Layer IX) -- P0
- [x] agreement-versioning (Layer IX)
- [x] precedent-challenge (Layer IX)

**Phases:**
- [x] Phase 1: Scaffolding and Anchor Skill (decision-record)
- [x] Phase 2: Semantic Tagging and Precedent Search (semantic-tagging, precedent-search)
- [x] Phase 3: Agreement Versioning and Precedent Challenge (agreement-versioning, precedent-challenge)
- [x] Phase 4: Layer Integration and README (retroactive tagging plan, foundation notes, cross-review)
- [x] Phase 5: Quality Gate

**Spec:** `conductor/tracks/memory_trace_20260302/spec.md`
**Plan:** `conductor/tracks/memory_trace_20260302/plan.md`

---

### 9. [x] exit_portability_20260302 -- Layer X: Exit & Portability
**Priority:** P0
**Layers:** X (Exit & Portability)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** foundation_20260301, safeguard_capture_20260302, emergency_handling_20260302

Build 5 governance skills ensuring exit is a structural right with graceful degradation and data portability. The capstone functional layer referencing all earlier layers. Draws on Hirschman's Exit/Voice/Loyalty, GDPR Article 20 data portability, cooperative dissolution precedents, and graceful degradation engineering.

**Skills (5):**
- [x] voluntary-exit (Layer X) -- P0 anchor
- [x] commitment-unwinding (Layer X)
- [x] portable-record (Layer X) -- P0
- [x] azpo-dissolution (Layer X)
- [x] re-entry-integration (Layer X)

**Phases:**
- [x] Phase 1: Scaffolding and Individual Exit (voluntary-exit, commitment-unwinding)
- [x] Phase 2: Data Portability (portable-record)
- [x] Phase 3: Collective Exit and Re-Entry (azpo-dissolution, re-entry-integration)
- [x] Phase 4: Layer Integration and Finalization

**Spec:** `conductor/tracks/exit_portability_20260302/spec.md`
**Plan:** `conductor/tracks/exit_portability_20260302/plan.md`

---

### 10. [x] global_packaging_20260302 -- Global Packaging & Cross-Layer Integration
**Priority:** P0
**Layers:** (cross-cutting)
**Status:** Complete
**Created:** 2026-03-02
**Depends on:** All 9 skill layer tracks

Produce global deliverables wrapping the NEOS skill stack into a distributable, verifiable package: README.md, NEOS_PRINCIPLES.md, STRESS_TEST_PROTOCOL.md, package_zip.py, stress_test_report.py, cross-layer dependency verification, and full skill index.

**Deliverables (6):**
- [x] README.md
- [x] NEOS_PRINCIPLES.md
- [x] STRESS_TEST_PROTOCOL.md
- [x] scripts/package_zip.py
- [x] scripts/stress_test_report.py
- [x] VERSION + full skill index

**Phases:**
- [x] Phase 1: Reference Documents (NEOS_PRINCIPLES.md, STRESS_TEST_PROTOCOL.md)
- [x] Phase 2: Utility Scripts (package_zip.py, stress_test_report.py)
- [x] Phase 3: README and Skill Index
- [x] Phase 4: Cross-Layer Verification
- [x] Phase 5: Final Quality Gate and Release Packaging

**Spec:** `conductor/tracks/global_packaging_20260302/spec.md`
**Plan:** `conductor/tracks/global_packaging_20260302/plan.md`

---

### 11. [x] agent_foundation_20260305 -- Agent Scaffolding, Skill Loader & Database
**Priority:** P0
**Status:** Complete
**Created:** 2026-03-05
**Depends on:** global_packaging_20260302

Build the foundation of the NEOS Governance Agent webservice: Sanic app factory, skill loader (parsing SKILL.md into dataclasses), dependency graph, PostgreSQL models (26 tables from YAML templates), Alembic migrations, and configuration.

**Deliverables:**
- [x] Sanic app factory with health endpoint and skill index API
- [x] Skill loader (SKILL.md → SkillMeta + SkillContent dataclasses)
- [x] Skill dependency graph (DAG, topological sort)
- [x] Skill registry (in-memory index, loaded at startup)
- [x] SQLAlchemy async ORM models (26 tables)
- [x] Alembic setup + initial migration
- [x] DB session factory with Sanic lifecycle hooks
- [x] OmniOne seed data script
- [x] pyproject.toml, Dockerfile, .env.example

**Phases:**
- [x] Phase 1: Scaffolding (directory structure, pyproject.toml, Dockerfile, config)
- [x] Phase 2: Skill Loader & Registry (loader.py, graph.py, registry.py + tests)
- [x] Phase 3: Database Models & Migrations (models.py, session.py, Alembic, seed data)
- [x] Phase 4: Sanic App Factory & API (main.py, health endpoint, skill index API)

**Spec:** `conductor/tracks/agent_foundation_20260305/spec.md`
**Plan:** `conductor/tracks/agent_foundation_20260305/plan.md`

---

### 12. [ ] dashboard_views_20260305 -- Datastar Dashboard & Views
**Priority:** P0
**Status:** Pending
**Created:** 2026-03-05
**Depends on:** agent_foundation_20260305

Build the Datastar-powered dashboard UI: base layout with Jinja2 templates, agreement/domain/member/proposal/decision views with SSE-driven interactivity, and all CRUD forms.

**Deliverables:**
- [ ] Base HTML layout with Datastar script tag and navigation
- [ ] Agreement views (list, create, edit, version history)
- [ ] Domain views (list, 11-element detail, metrics)
- [ ] Member views (directory, role assignments, status)
- [ ] Proposal views (list, create, ACT lifecycle tracker)
- [ ] Decision record views (browser, semantic tag filter, precedent search)

**Phases:**
- [ ] Phase 1: Base Layout & Navigation (base.html, Datastar signals, nav)
- [ ] Phase 2: Agreement & Domain Views (list, forms, SSE filtering)
- [ ] Phase 3: Member & Role Views (directory, assignments)
- [ ] Phase 4: Proposal ACT Lifecycle Views (advice, consent rounds, test phase tracker)
- [ ] Phase 5: Decision Records & Search (browser, tags, precedent search)

**Spec:** `conductor/tracks/dashboard_views_20260305/spec.md`
**Plan:** `conductor/tracks/dashboard_views_20260305/plan.md`

---

### 13. [ ] agent_core_20260305 -- Claude Agent SDK Integration & Chat
**Priority:** P0
**Status:** Pending
**Created:** 2026-03-05
**Depends on:** agent_foundation_20260305

Build the Claude Agent SDK integration: 14 governance @tool definitions, system prompt assembly, multi-turn conversation management via ClaudeSDKClient, Datastar SSE chat panel, and skill transition routing.

**Deliverables:**
- [ ] 14 governance tools via @tool decorator + create_sdk_mcp_server()
- [ ] 3-layer system prompt assembly (foundation + active skill + dependencies)
- [ ] Chat SSE handler (Datastar streaming of agent responses)
- [ ] Multi-turn session management via ClaudeSDKClient
- [ ] Skill transition router (process → next skill detection)

**Phases:**
- [ ] Phase 1: Governance Tools (14 @tool definitions, MCP server)
- [ ] Phase 2: System Prompt Assembly (3-layer dynamic construction)
- [ ] Phase 3: Chat Panel & SSE Streaming (Datastar chat view, streaming agent responses)
- [ ] Phase 4: Session Management & Skill Routing (ClaudeSDKClient, transitions)

**Spec:** `conductor/tracks/agent_core_20260305/spec.md`
**Plan:** `conductor/tracks/agent_core_20260305/plan.md`

---

### 14. [ ] sync_deploy_20260305 -- dApp Sync, Micro-Frontends & Railway Deploy
**Priority:** P1
**Status:** Pending
**Created:** 2026-03-05
**Depends on:** agent_foundation_20260305, dashboard_views_20260305, agent_core_20260305

Build the decentralized sync layer (GunDB relay + IPFS pinning), embeddable micro-frontend components, and Railway multi-service deployment.

**Deliverables:**
- [ ] GunDB relay (Node.js, separate service)
- [ ] Gun bridge (Sanic → GunDB WebSocket publisher)
- [ ] IPFS pinning (Pinata API, store CIDs in Postgres + GunDB)
- [ ] Embeddable micro-frontend components (agreement-card, proposal-status, domain-summary)
- [ ] Embed snippet system (drop-in script + div for hub pages)
- [ ] Railway multi-service config (Sanic + PostgreSQL + GunDB relay)
- [ ] End-to-end test (full governance flow)
- [ ] Documentation

**Phases:**
- [ ] Phase 1: GunDB Relay & Bridge (Node.js relay, Python bridge, P2P sync)
- [ ] Phase 2: IPFS Pinning (Pinata API integration, CID storage)
- [ ] Phase 3: Micro-Frontend Components (embeddable Datastar fragments, embed system)
- [ ] Phase 4: Railway Deployment (multi-service config, health checks, seed data)
- [ ] Phase 5: E2E Testing & Documentation

**Spec:** `conductor/tracks/sync_deploy_20260305/spec.md`
**Plan:** `conductor/tracks/sync_deploy_20260305/plan.md`

---

### 15. [x] member_profile_harden_20260313 -- Member Profile Flow: Review & Harden
**Priority:** P0
**Type:** Bug (Review/Harden)
**Status:** Complete
**Created:** 2026-03-13
**Depends on:** dashboard_views_20260305

Review and harden the member profile flow end-to-end. Fix async lazy-load 500 errors, template context safety issues, variable name mismatches, and add defensive error handling. Validate all CRUD paths (view own profile, view others, edit own, blocked from editing others), ensure skills/interests/ecosystem display correctly, and verify the signup-to-profile flow.

**Known Bugs:**
- 500 error on profile detail from `MissingGreenlet` (async lazy-load of `member.onboarding`)
- `transitions`/`status_transitions` variable name mismatch (status history never renders)
- `member=None` crash risk in detail.html when member not found
- Zero test coverage for member CRUD paths

**Phases:**
- [ ] Phase 1: Audit & Test Infrastructure (test fixtures, ~20 tests for all CRUD paths)
- [ ] Phase 2: Fix Async/Session Bugs (lazy-load fix, session scoping, `current_user` safety)
- [ ] Phase 3: Harden Templates & Guards (attribute access audit, error guards, name mismatch fix)
- [ ] Phase 4: End-to-End Validation (signup flow, skills round-trip, regression check)

**Spec:** `conductor/tracks/member_profile_harden_20260313/spec.md`
**Plan:** `conductor/tracks/member_profile_harden_20260313/plan.md`
