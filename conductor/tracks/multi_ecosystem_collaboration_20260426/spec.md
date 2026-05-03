# Multi-Ecosystem Collaboration Track — Specification

**Track ID:** multi_ecosystem_collaboration_20260426
**Priority:** P0
**Type:** Feature
**Created:** 2026-04-26
**Depends on:** agent_foundation_20260305 (complete), ecosystem_scope_20260318 (partially complete)

---

## Problem Statement

NEOS's 54-skill governance stack is designed for multi-community coordination, but the software currently supports only single-ecosystem operation. The critical review identified:

1. **No Circle/ETHOS data model** — governance processes reference circles as organizational units but have no way to model membership in them
2. **Layer IV (Economic) and Layer V (Inter-Unit) are completely unimplemented** in code
3. **No cross-ecosystem discovery** — ecosystems cannot discover what other ecosystems share or need
4. **No collaboration tracking** — no mechanism to propose, track, or manage cross-domain partnerships
5. **No compliance monitoring** — no automated compliance summaries or version tracking
6. **Proprietary AI lock-in** — hard dependency on Anthropic API contradicts sovereignty principles
7. **No notification infrastructure** — time-bound governance processes fail silently
8. **Dual frontend stack** — Jinja2/Datastar and React running simultaneously

## Goals

- Enable N=3 ecosystem operation with cross-ecosystem discovery and collaboration
- Implement circle membership so domains function as organizational units
- Add shares/needs entities for resource matching across ecosystems
- Add collaboration tracking with graduated engagement tiers
- Add compliance summaries (AI-generated, 30-day cycle)
- Switch to OpenRouter/LiteLLM for AI provider independence
- Remove Jinja2/Datastar, commit to React-only frontend
- Add PWA notification support with cron-based push
- Add "No Sultan" routing to the AI agent
- Add version fingerprints to agreements, domains, and collaborations

## Non-Goals (deferred)

- Full Layer IV economic model implementation (deferred to economic track)
- Cross-instance federation protocol (requires external API design)
- Multi-ecosystem identity linking (intentionally excluded — 3rd space design)
- N>2 party conflict resolution protocol
- Cultural translation layer

---

## Architecture Decisions

### AI Provider Independence
Switch from direct `anthropic` SDK to `litellm` with OpenRouter as default provider. All AI calls go through a single abstraction. Every governance process must work without AI — templates include human-readable instructions.

### Circle = Domain
Circles, ETHOS, and domains are similar enough to merge into `Domain`. `CircleMembership` links members to domains with roles (steward, delegate, member). This keeps the model flat and lean.

### Shares & Needs for Discovery
Domain-level declarations of what resources/skills are shared or needed. These power the cross-ecosystem discovery page and enable collaboration matching.

### Collaborations as Domain Relationships
Collaborations link two domains (potentially cross-ecosystem) with graduated engagement tiers (observe → cooperate → federate → integrate). This implements the Layer V inter-unit coordination model at the data level.

### Conflict Resolution Model
Conflict → Solution Proposal → If fails, break into smaller parts → Pass what can be agreed on → Maintain velocity with incremental proposals → Continue engagement until resolved → Update agreements to prevent recurrence.

### Frontend: React Only
Remove all Jinja2/Datastar templates and routes. The React app in `charting-the-course/client/` is the single frontend.

### PWA Notifications
Embed service worker in the React client for push notifications. Cron jobs on the backend push notifications for governance deadlines.

---

## Data Model Changes

### New Tables (4)
1. **circle_memberships** — Links members to domains with roles
2. **shares_needs** — Domain-level resource/skill declarations
3. **collaborations** — Cross-domain partnership agreements
4. **compliance_summaries** — AI-generated ecosystem compliance reports

### Modified Tables
- **agreements** — Add `version_fingerprint` (String 64)
- **domains** — Add `version_fingerprint` (String 64)
- **members** — `did` unique constraint changed to composite `(ecosystem_id, did)` ✓ (done in Phase 0)

---

## Security Fixes (Phase 0 — Complete)

- [x] CRITICAL-1: Ecosystem scoping bypass — all 14 blueprints re-parsed raw cookie
- [x] CRITICAL-2: Member.did unique=True blocked multi-ecosystem membership
- [x] CRITICAL-3: Synchronous Anthropic client blocked Sanic event loop
- [x] HIGH-1: datetime.utcnow() deprecated across 18 call sites
- [x] HIGH-2: Default SESSION_SECRET "change-me-in-production"
- [x] HIGH-7: Incompatible agreement state machines (API vs governance tools)
- [x] HIGH-8: EcosystemContext only supports single selection
- [x] HIGH-10: Quorum math.ceil fix
