# Implementation Plan: Chat & Direct Messaging System

**Track ID:** chat_messaging_20260313
**Created:** 2026-03-13

---

## Overview

This plan is divided into 6 phases, progressing from data model foundations through WebSocket infrastructure, REST/htmx views, real-time features, governance integration, and finally end-to-end validation. Each phase builds on the previous one and ends with a verification checkpoint.

**Estimated total effort:** 12-16 hours across 6 phases.

---

## Phase 1: Data Models & Migration

**Goal:** Define the messaging data models in SQLAlchemy, create the Alembic migration, and validate with unit tests.

**Tasks:**

- [x] Task 1.1: Write model tests for Conversation, ConversationParticipant, Message, ConversationLink [053186a]
  - TDD: Create `agent/tests/test_messaging_models.py`
  - Test Conversation creation with ecosystem_id, type, title, created_by
  - Test ConversationParticipant creation with unique constraint (conversation_id, member_id)
  - Test Message creation with conversation FK, sender FK, content, message_type, soft delete
  - Test ConversationLink creation with entity_type and entity_id
  - Test DM uniqueness constraint (only one DM per member pair per ecosystem)
  - Test cascade: deleting a conversation cascades to participants, messages, links
  - All tests RED initially

- [x] Task 1.2: Implement messaging models in models.py [053186a]
  - Add 4 new models after the Auth section (line ~762) in `agent/src/neos_agent/db/models.py`
  - `Conversation(TimestampMixin, Base)` -- id, ecosystem_id (FK), type, title, created_by (FK)
  - `ConversationParticipant(TimestampMixin, Base)` -- id, conversation_id (FK), member_id (FK), role, joined_at, last_read_at, muted; UniqueConstraint(conversation_id, member_id)
  - `Message(TimestampMixin, Base)` -- id, conversation_id (FK), sender_id (FK), content, message_type, metadata (JSON), edited_at, deleted_at; Index(conversation_id, created_at)
  - `ConversationLink(TimestampMixin, Base)` -- id, conversation_id (FK), entity_type, entity_id, created_by (FK), created_at; Index(entity_type, entity_id)
  - Add relationships: Conversation.participants, Conversation.messages, Conversation.links
  - Update module docstring with new table count
  - Run tests from Task 1.1 -- all GREEN

- [x] Task 1.3: Create Alembic migration
  - Generate migration: `alembic revision --autogenerate -m "add messaging models"`
  - Verify migration creates tables: conversations, conversation_participants, messages, conversation_links
  - Verify indexes and unique constraints are present
  - Test migration up/down cycle

- [x] Task 1.4: Add messaging seed data to conftest.py
  - Update `agent/tests/conftest.py` to import new models
  - Create a `seeded_messaging_db` fixture that extends `seeded_db` with:
    - 1 DM conversation between Lani and Kai
    - 1 group conversation ("Kitchen Planning") with all 3 members
    - 5 sample messages in the DM
    - 3 sample messages in the group
    - 1 governance link (group linked to proposal PROP-2026-001)
  - This fixture will be reused by all subsequent test files

- [x] Verification: Run full test suite, confirm all model tests pass, migration applies cleanly [checkpoint marker]

---

## Phase 2: Connection Manager & WebSocket Infrastructure

**Goal:** Build the in-memory WebSocket connection manager and the authenticated WebSocket endpoint.

**Tasks:**

- [x] Task 2.1: Write tests for ConnectionManager
  - TDD: Create `agent/tests/test_connection_manager.py`
  - 14 tests covering register, unregister, send_to_member, broadcast, online count

- [x] Task 2.2: Implement ConnectionManager
  - Created `agent/src/neos_agent/messaging/connections.py` with singleton instance
  - All 14 tests GREEN

- [x] Task 2.3: Write tests for WebSocket endpoint authentication
  - Tests in `agent/tests/test_messaging_ws.py` covering handler auth validation

- [x] Task 2.4: Implement WebSocket endpoint
  - Created `agent/src/neos_agent/messaging/routes.py` with messaging_bp
  - Registered blueprint in main.py
  - WebSocket auth via session cookie, ping/pong keepalive, JSON frame dispatch

- [x] Task 2.5: Implement WebSocket message handlers
  - Created `agent/src/neos_agent/messaging/handlers.py`
  - handle_message: persist + broadcast, rate limiting, max length validation
  - handle_typing: broadcast typing indicator (no persist)
  - handle_read_receipt: update last_read_at + broadcast
  - 6 handler tests all GREEN

- [x] Verification: 38 tests pass (18 model + 14 connection manager + 6 handlers) [checkpoint marker]

---

## Phase 3: REST API & Conversation Management

**Goal:** Build the htmx-compatible REST endpoints for conversation CRUD, message pagination, and member picker.

**Tasks:**

- [x] Task 3.1-3.6: REST API implementation and tests
  - 15 endpoints: messaging page, conversation CRUD, message CRUD, participant management, governance links, member picker, unread count
  - DM uniqueness enforcement, ecosystem scoping, owner succession on leave
  - 15 tests covering all CRUD paths, pagination, unread counts, governance links
  - All tests GREEN

- [x] Verification: 53 total tests pass (18 model + 14 CM + 6 handler + 15 views) [checkpoint marker]

---

## Phase 4: Templates & UI

**Goal:** Build the Jinja2 + Tailwind templates for the messaging interface, integrate with base.html navigation.

**Tasks:**

- [x] Task 4.1: Create messaging template directory and layout
  - Created `messaging/index.html` -- extends base.html, two-panel layout with WebSocket JS

- [x] Task 4.2: Create conversation list partial
  - Created `messaging/conversation_list.html` -- htmx partial with avatars, unread badges, last message preview

- [x] Task 4.3: Create conversation detail partial
  - Created `messaging/conversation_detail.html` -- header, messages, governance link banners, typing indicator, input area

- [x] Task 4.4: Create message list partial (for pagination)
  - Created `messaging/message_list.html` -- supports system, deleted, governance_link, and regular messages

- [x] Task 4.5: Create member picker partial
  - Created `messaging/member_picker.html` -- member list with avatars, profile types, status badges

- [x] Task 4.6: Update base.html with Messages nav link and unread badge
  - Added "Communication" section with Messages link and htmx-polled unread badge (every 30s)

- [x] Task 4.7: Add "Message" button to member profile detail page
  - Added "Message" button to member detail page, links to `/messaging?dm={member_id}`

- [x] Task 4.8: WebSocket client JavaScript
  - Included in index.html: connect/reconnect, send, typing, read receipts, message append, auto-scroll

- [ ] Verification: Full UI works in browser -- create DM, send messages, see real-time delivery, conversation list updates, unread badges show correctly [checkpoint marker]

---

## Phase 5: Governance Integration

**Goal:** Connect conversations to governance entities (proposals, agreements, domains, conflicts) with bidirectional navigation.

**Tasks:**

- [x] Task 5.1: Write tests for governance link creation and display
  - Added TestGetEntityDiscussions (4 tests) and TestEcosystemBoundary (1 test) to test_messaging_views.py

- [x] Task 5.2: Implement governance entity sharing
  - Governance link messages render as styled cards in conversation_detail.html and message_list.html
  - REST endpoint POST /messaging/conversations/{id}/link handles creation with duplicate prevention
  - governance_link message metadata stores entity_type, entity_id, entity_title

- [x] Task 5.3: Add "Discuss" button to governance entity detail pages
  - Added "Discuss" button to proposals, agreements, domains, and conflicts detail templates
  - Buttons use htmx POST to /messaging/conversations with link_entity_type and link_entity_id

- [x] Task 5.4: Add "Discussions" section to governance entity detail pages
  - Created `messaging/queries.py` with `get_entity_discussions()` helper (avoids circular import)
  - Updated proposals, agreements, domains, and conflicts views to pass `discussions` context
  - Each entity detail page shows linked conversations with participant counts

- [x] Task 5.5: Write integration tests for governance flow
  - Tests for get_entity_discussions: returns linked discussions, empty for no links, duplicate prevention
  - Tests for governance_link message metadata
  - Test ecosystem boundary enforcement
  - 58 total tests pass (18 model + 14 CM + 6 handler + 20 views)

- [ ] Verification: Navigate from proposal to discussion and back, share entities in conversations, see Discussions sections on entity pages [checkpoint marker]

---

## Phase 6: Search, Polish & End-to-End Validation

**Goal:** Add message search, polish the UI, handle edge cases, and run full end-to-end validation.

**Tasks:**

- [x] Task 6.1: Implement message search
  - Added GET /messaging/search?q=... endpoint with ILIKE search across member's conversations
  - Created `messaging/search_results.html` template with click-to-navigate results
  - Updated index.html search input to toggle between search results and conversation list

- [x] Task 6.2: Handle edge cases and error states
  - Rate limiting (10/sec) and max message length (10,000 chars) in handlers.py (Phase 2)
  - XSS prevention via Jinja2 autoescape and escapeHtml() in JS (Phase 4)
  - Tests: empty conversation list, empty message list, long content, search exclusion

- [x] Task 6.3: Exited member handling
  - REST returns 403 for exited member message send (routes.py Phase 3)
  - WebSocket handler checks exited status (handlers.py Phase 2)
  - Template shows read-only notice and hides input
  - Tests: exited member status check, can still read conversations

- [x] Task 6.4: Unread badge polling/refresh
  - GET /messaging/unread-count endpoint (routes.py Phase 3)
  - htmx polling every 30s on base.html sidebar badge (Phase 4)

- [x] Task 6.5: Performance optimization
  - Verified indexes: ix_messages_conversation_created, ix_conversation_participants_member_id, ix_conversation_links_entity

- [x] Task 6.6: End-to-end validation
  - 65 total tests pass (18 model + 14 CM + 6 handler + 27 views)

- [ ] Verification: All tests pass, messaging feature complete [checkpoint marker]

---

## File Summary

### New Files

| File | Description |
|------|-------------|
| `agent/src/neos_agent/messaging/__init__.py` | Messaging package init |
| `agent/src/neos_agent/messaging/connections.py` | WebSocket ConnectionManager singleton |
| `agent/src/neos_agent/messaging/routes.py` | Blueprint with REST + WebSocket endpoints |
| `agent/src/neos_agent/messaging/handlers.py` | WebSocket message type handlers |
| `agent/src/neos_agent/templates/messaging/index.html` | Main messaging page |
| `agent/src/neos_agent/templates/messaging/conversation_list.html` | Conversation list partial |
| `agent/src/neos_agent/templates/messaging/conversation_detail.html` | Conversation detail partial |
| `agent/src/neos_agent/templates/messaging/message_list.html` | Paginated message partial |
| `agent/src/neos_agent/templates/messaging/member_picker.html` | Member selection partial |
| `agent/tests/test_messaging_models.py` | Model unit tests |
| `agent/tests/test_connection_manager.py` | ConnectionManager unit tests |
| `agent/tests/test_messaging_ws.py` | WebSocket endpoint tests |
| `agent/tests/test_messaging_views.py` | REST endpoint tests |
| `agent/alembic/versions/xxxx_add_messaging_models.py` | Database migration |

### Modified Files

| File | Changes |
|------|---------|
| `agent/src/neos_agent/db/models.py` | Add 4 new models (~80 lines) |
| `agent/src/neos_agent/main.py` | Register messaging blueprint |
| `agent/src/neos_agent/templates/base.html` | Add Messages nav link with unread badge |
| `agent/src/neos_agent/auth/middleware.py` | Add /messaging to public prefix check if WS needs it |
| `agent/tests/conftest.py` | Add messaging seed fixture |
| `agent/src/neos_agent/templates/dashboard/members/detail.html` | Add "Message" button |
| `agent/src/neos_agent/templates/dashboard/proposals/detail.html` | Add "Discuss" button + Discussions section |
| `agent/src/neos_agent/templates/dashboard/agreements/detail.html` | Add "Discuss" button + Discussions section |
| `agent/src/neos_agent/templates/dashboard/domains/detail.html` | Add "Discuss" button + Discussions section |
| `agent/src/neos_agent/templates/dashboard/conflicts/detail.html` | Add "Discuss" button + Discussions section |

---

## Dependency Graph

```
Phase 1 (Models) ──> Phase 2 (WebSocket) ──> Phase 3 (REST API)
                                                    |
                                                    v
                     Phase 4 (Templates) <──────────┘
                           |
                           v
                     Phase 5 (Governance Integration)
                           |
                           v
                     Phase 6 (Search, Polish, E2E)
```
