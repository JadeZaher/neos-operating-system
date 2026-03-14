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

- [ ] Task 5.1: Write tests for governance link creation and display
  - TDD: Add to `agent/tests/test_messaging_views.py`
  - Test POST /messaging/conversations/{id}/link creates ConversationLink
  - Test GET /messaging/conversations/{id} displays governance link banner
  - Test sharing a governance entity into a conversation creates a governance_link message
  - Test ConversationLink prevents duplicate links (same entity + same conversation)

- [ ] Task 5.2: Implement governance entity sharing
  - In handlers: when a `governance_link` message is received, validate entity exists and is accessible
  - Create a `governance_link` message with metadata: `{"entity_type": "...", "entity_id": "...", "entity_title": "..."}`
  - Render governance link messages as styled cards in the conversation view (entity type icon, title, link to entity page)
  - Run tests -- GREEN

- [ ] Task 5.3: Add "Discuss" button to governance entity detail pages
  - Update templates (check each for existence first):
    - `agent/src/neos_agent/templates/dashboard/proposals/detail.html` -- add "Discuss" button
    - `agent/src/neos_agent/templates/dashboard/agreements/detail.html` -- add "Discuss" button
    - `agent/src/neos_agent/templates/dashboard/domains/detail.html` -- add "Discuss" button
    - `agent/src/neos_agent/templates/dashboard/conflicts/detail.html` -- add "Discuss" button
  - "Discuss" button sends POST to `/messaging/conversations` with `{type: "group", title: "<Entity> Discussion", link_entity_type: "...", link_entity_id: "..."}`
  - If a linked conversation already exists, redirect to it

- [ ] Task 5.4: Add "Discussions" section to governance entity detail pages
  - On each entity detail page, add a "Discussions" section showing linked conversations
  - Query ConversationLink by entity_type + entity_id
  - Show each linked conversation: title, participant count, last activity, unread count
  - Each links to `/messaging?conversation={id}`

- [ ] Task 5.5: Write integration tests for governance flow
  - Test creating a discussion from a proposal page, sending messages, verifying the link
  - Test that the proposal detail page shows the discussion in the "Discussions" section
  - Test sharing an agreement into an existing group conversation
  - Test ecosystem boundary: cannot link entity from different ecosystem

- [ ] Verification: Navigate from proposal to discussion and back, share entities in conversations, see Discussions sections on entity pages [checkpoint marker]

---

## Phase 6: Search, Polish & End-to-End Validation

**Goal:** Add message search, polish the UI, handle edge cases, and run full end-to-end validation.

**Tasks:**

- [ ] Task 6.1: Implement message search
  - Write tests for GET /messaging/search?q=... returning matching messages
  - Implement full-text search across messages the member participates in
  - Use SQL ILIKE for initial implementation (PostgreSQL full-text search deferred)
  - Return search results as htmx partial with conversation context
  - Clicking a result navigates to that message in its conversation

- [ ] Task 6.2: Handle edge cases and error states
  - Write tests for:
    - Member with no conversations sees empty state with "Start a conversation" CTA
    - Conversation with 0 messages shows empty state
    - WebSocket reconnection after network interruption
    - Rapid message sending (rate limiting: max 10/sec per member)
    - Very long messages (truncate at 10,000 characters)
    - XSS prevention: message content is HTML-escaped on render
  - Implement rate limiting in WebSocket handler
  - Implement max message length validation
  - Ensure all user content is escaped via Jinja2 autoescape

- [ ] Task 6.3: Exited member handling
  - Write tests for:
    - Exited member can view conversation list and message history
    - Exited member cannot send messages (REST returns 403, WebSocket rejects)
    - Exited member cannot create new conversations
    - Exited member sees "You have exited this ecosystem" notice
  - Implement status check in message send path
  - Implement read-only UI state for exited members

- [ ] Task 6.4: Unread badge polling/refresh
  - Implement unread count endpoint: GET /messaging/unread-count returns `{"count": N}`
  - Add htmx polling on base.html sidebar badge: `hx-get="/messaging/unread-count" hx-trigger="every 30s"` to update badge
  - WebSocket also pushes unread count updates for instant badge refresh when chat is open
  - Write test for unread count endpoint

- [ ] Task 6.5: Performance optimization
  - Add database indexes review:
    - Verify Index on messages(conversation_id, created_at) exists
    - Verify Index on conversation_participants(member_id) for quick conversation lookup
    - Verify Index on conversation_links(entity_type, entity_id) for governance page queries
  - Test conversation list query performance with 100 conversations
  - Test message pagination performance with 1000 messages
  - Add `select_from` hints and eager loading where needed

- [ ] Task 6.6: End-to-end validation
  - Manual test script:
    1. Log in as Lani (co_creator) -- verify Messages link in sidebar
    2. Click "Messages" -- verify empty state with "Start a conversation"
    3. Navigate to Kai's profile -- click "Message" -- verify DM created
    4. Send 3 messages in the DM -- verify real-time delivery (open second browser as Kai)
    5. Create group conversation with Lani, Kai, Manu -- title "Kitchen Planning"
    6. Send messages in group -- verify all 3 members receive them
    7. Navigate to proposal PROP-2026-001 -- click "Discuss" -- verify conversation created and linked
    8. Share an agreement into the Kitchen Planning group -- verify governance_link card renders
    9. Verify unread badges update when Manu sends a message while Lani is on a different page
    10. Verify ecosystem boundary: switch to a different ecosystem, verify only members from that ecosystem appear in member picker
    11. Edit a message -- verify "edited" indicator appears
    12. Delete a message -- verify "This message was deleted" appears
  - Document any issues found and fix

- [ ] Verification: Full end-to-end flow works, all tests pass, no console errors, messaging is functional for all member types [checkpoint marker]

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
