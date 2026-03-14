# Specification: Chat & Direct Messaging System

**Track ID:** chat_messaging_20260313
**Type:** Feature
**Priority:** P1
**Created:** 2026-03-13
**Depends on:** agent_foundation_20260305 (complete), dashboard_views_20260305 (pending), agent_core_20260305 (pending)

---

## 1. Overview

Build a real-time member-to-member messaging system for the NEOS governance platform. This system enables direct messages (1:1), group conversations (multi-party), and governance-linked conversations that connect discussions to proposals, agreements, domains, conflicts, and other governance artifacts. The messaging system complements the existing AI governance assistant (human-to-AI via SSE) by adding human-to-human communication channels that operate within ecosystem boundaries.

---

## 2. Background

### Current State

- The NEOS agent has an AI chat system (`/chat/message`) that streams Claude responses via SSE. This is strictly human-to-AI and stores sessions in `agent_sessions`.
- No member-to-member messaging infrastructure exists anywhere in the codebase.
- Real-time transport is SSE-only (server-to-client push). No WebSocket code exists.
- The platform uses Sanic 25.x which has native WebSocket support via `@bp.websocket()`.
- Deployment is Railway, single replica -- meaning WebSocket connections terminate at the same process.
- Members belong to ecosystems and can be active in multiple ecosystems simultaneously (via the ecosystem selector cookie and DID-based cross-ecosystem membership).
- Members have DID:key Ed25519 identities with HMAC session cookie authentication.

### Why This Matters

NEOS governance processes (ACT decision protocol, conflict resolution, domain coordination) require structured dialogue between members. Currently, all governance communication happens outside the platform. Bringing messaging in-platform enables:

1. **Traceable governance discussions** -- conversations linked to proposals, agreements, and conflicts become part of the governance memory layer.
2. **Ecosystem-scoped coordination** -- members can only message others within shared ecosystems, enforcing governance boundaries.
3. **Process integration** -- the consent round, advice phase, and harm circle processes can reference conversation threads as evidence and context.

### Architectural Decision: WebSocket

**Decision:** Use Sanic native WebSocket (`@bp.websocket`) for real-time message delivery.

**Rationale:**
- SSE is server-to-client only; messaging requires bidirectional communication.
- Sanic has first-class WebSocket support (`@bp.websocket("/path")`).
- Single-replica Railway deployment means no need for a pub/sub layer (Redis, etc.) in the initial implementation.
- WebSocket connections provide lower latency than HTTP polling for chat UX.
- The existing SSE AI chat and WebSocket member chat coexist without conflict (different URL paths, different protocols).

**Future Scaling Note:** When NEOS moves to multi-replica deployment, a pub/sub broker (Redis Pub/Sub or similar) will be needed to fan out WebSocket messages across replicas. This is out of scope for the initial implementation but the data model and message routing layer are designed to accommodate it.

---

## 3. Functional Requirements

### FR-1: Conversation Model

**Description:** A unified conversation model supports both 1:1 DMs and group conversations with consistent APIs and UI.

**Acceptance Criteria:**
- AC-1.1: A `Conversation` model exists with fields: id (UUID), ecosystem_id (FK), type (enum: "dm" | "group"), title (nullable, for group only), created_by (FK to members), created_at, updated_at.
- AC-1.2: A `ConversationParticipant` model links members to conversations with fields: id, conversation_id (FK), member_id (FK), role (enum: "owner" | "admin" | "member"), joined_at, last_read_at, muted (boolean).
- AC-1.3: DM conversations enforce exactly 2 participants and are unique per pair (no duplicate DM threads between the same two members within the same ecosystem).
- AC-1.4: Group conversations support 2-100 participants with a required title.
- AC-1.5: All conversations are scoped to a single ecosystem_id.

**Priority:** P0

### FR-2: Message Model

**Description:** Messages are the atomic unit of communication within conversations.

**Acceptance Criteria:**
- AC-2.1: A `Message` model exists with fields: id (UUID), conversation_id (FK), sender_id (FK to members), content (Text), message_type (enum: "text" | "system" | "governance_link"), metadata (JSON, nullable), created_at, edited_at (nullable), deleted_at (nullable, soft delete).
- AC-2.2: Messages support soft deletion -- deleted messages show "This message was deleted" to other participants.
- AC-2.3: Messages support editing with an `edited_at` timestamp that is visible in the UI.
- AC-2.4: System messages (member joined, member left, conversation created) use message_type "system" and are auto-generated.
- AC-2.5: Governance link messages embed a reference to a governance entity (proposal, agreement, domain, conflict) via the metadata JSON field with structure `{"entity_type": "proposal", "entity_id": "<uuid>", "entity_title": "..."}`.

**Priority:** P0

### FR-3: Real-Time Message Delivery

**Description:** Messages are delivered in real-time to all online conversation participants via WebSocket.

**Acceptance Criteria:**
- AC-3.1: A WebSocket endpoint (`/messaging/ws`) accepts authenticated connections using the existing session cookie.
- AC-3.2: On connection, the server authenticates the member and registers the WebSocket in an in-memory connection registry keyed by member_id.
- AC-3.3: When a message is sent (via WebSocket or REST), all online participants of that conversation receive the message in real-time.
- AC-3.4: Messages sent while a participant is offline are persisted to the database and delivered when they next load the conversation.
- AC-3.5: WebSocket connections send periodic ping/pong frames (every 30 seconds) to detect stale connections.
- AC-3.6: The WebSocket protocol uses JSON frames with a `type` field: `{"type": "message", "data": {...}}`, `{"type": "typing", "data": {"conversation_id": "...", "member_id": "..."}}`, `{"type": "read_receipt", "data": {...}}`.

**Priority:** P0

### FR-4: Conversation Management

**Description:** Members can create, list, and manage conversations.

**Acceptance Criteria:**
- AC-4.1: Members can start a DM by selecting another member from the member directory (a "Message" button on member profiles and member list).
- AC-4.2: If a DM already exists between two members in the same ecosystem, opening a DM navigates to the existing conversation instead of creating a duplicate.
- AC-4.3: Members can create group conversations by selecting multiple participants and providing a title.
- AC-4.4: Group conversation owners/admins can add or remove participants.
- AC-4.5: Any participant can leave a group conversation. If the owner leaves, the oldest admin becomes owner; if no admins, the oldest member becomes owner.
- AC-4.6: The conversation list shows all conversations the member participates in, sorted by most recent message, with unread counts.

**Priority:** P0

### FR-5: Read Receipts and Unread Counts

**Description:** Members can see which messages have been read and how many unread messages exist.

**Acceptance Criteria:**
- AC-5.1: Each participant has a `last_read_at` timestamp on their `ConversationParticipant` record.
- AC-5.2: When a member views a conversation, `last_read_at` is updated to the current time.
- AC-5.3: Unread count for each conversation is computed as the count of messages with `created_at > last_read_at` for that participant.
- AC-5.4: A total unread count badge appears in the sidebar navigation next to a "Messages" link.
- AC-5.5: Read receipts are broadcast via WebSocket to other participants (showing "read" status).

**Priority:** P1

### FR-6: Governance Process Integration

**Description:** Conversations can be linked to governance entities, and governance processes can reference conversations.

**Acceptance Criteria:**
- AC-6.1: A `ConversationLink` model exists with fields: id, conversation_id (FK), entity_type (enum: "proposal" | "agreement" | "domain" | "conflict" | "decision"), entity_id (UUID), created_by (FK to members), created_at.
- AC-6.2: From any governance entity detail page (proposal, agreement, domain, conflict), a "Discuss" button creates or navigates to a linked conversation.
- AC-6.3: Linked governance entities are displayed as a header/banner in the conversation view.
- AC-6.4: Members can share a governance entity into an existing conversation as a governance_link message type.
- AC-6.5: Governance entity detail pages show a "Discussions" section listing linked conversations with participant count and last activity.

**Priority:** P1

### FR-7: Messaging UI

**Description:** A dedicated messaging interface accessible from the sidebar navigation.

**Acceptance Criteria:**
- AC-7.1: A "/messaging" page shows a two-panel layout: conversation list on the left, active conversation on the right.
- AC-7.2: On mobile, the conversation list and active conversation are separate views (navigable via back button).
- AC-7.3: The message input area supports multi-line text with Shift+Enter for newlines and Enter to send.
- AC-7.4: Messages display the sender's display_name, profile picture (or initial avatar), and timestamp.
- AC-7.5: The conversation view supports infinite scroll (load older messages on scroll-up).
- AC-7.6: A typing indicator shows when another participant is typing.
- AC-7.7: The messaging page uses the standard base.html layout with sidebar navigation.

**Priority:** P0

### FR-8: Ecosystem Boundary Enforcement

**Description:** Messaging respects ecosystem boundaries -- members can only message others in shared ecosystems.

**Acceptance Criteria:**
- AC-8.1: The member picker (for creating DMs/groups) only shows members from the currently selected ecosystem(s).
- AC-8.2: A conversation's ecosystem_id must match one of the sender's selected ecosystems.
- AC-8.3: A member cannot be added to a conversation in an ecosystem they do not belong to.
- AC-8.4: If a member is removed from an ecosystem (status changes to "exited"), they retain read access to historical messages but cannot send new messages.

**Priority:** P0

### FR-9: Message Search

**Description:** Members can search across their message history.

**Acceptance Criteria:**
- AC-9.1: A search bar at the top of the conversation list supports full-text search across message content.
- AC-9.2: Search results show the matching message with conversation context (conversation title/participant names, timestamp).
- AC-9.3: Clicking a search result navigates to that message in its conversation.
- AC-9.4: Search is scoped to conversations the member participates in (no access to conversations they are not part of).

**Priority:** P2

---

## 4. Non-Functional Requirements

### NFR-1: Performance

- Messages must be delivered to online participants within 500ms of being sent.
- The conversation list must load within 1 second with up to 100 conversations.
- Message history pagination must load 50 messages per page within 500ms.
- WebSocket connections must handle up to 200 concurrent connections per single Sanic worker (Railway single-replica deployment).

### NFR-2: Security

- WebSocket connections must be authenticated using the existing HMAC session cookie mechanism.
- Message content is stored as plaintext in PostgreSQL (no end-to-end encryption in v1, as all data is already server-side).
- All database queries for messages and conversations must be scoped by ecosystem_id to prevent cross-ecosystem data leakage.
- Soft-deleted messages must not expose original content via any API.
- Rate limiting: maximum 10 messages per second per member to prevent spam.

### NFR-3: Data Integrity

- Messages are persisted to the database before being broadcast via WebSocket (write-then-notify pattern).
- Conversation participant modifications (add/remove) are transactional.
- The unique DM constraint (one DM per member pair per ecosystem) is enforced at the database level.

### NFR-4: Compatibility

- The messaging system must work alongside the existing AI chat panel without interference.
- WebSocket transport must coexist with SSE transport used by the AI chat.
- All messaging views use Tailwind CSS 4.x exclusively (no custom CSS) per tech stack rules.
- Templates use Jinja2 with htmx for partial updates where appropriate.

---

## 5. User Stories

### US-1: Domain Member Direct Message

**As** a domain steward, **I want** to send a direct message to another domain member, **so that** I can coordinate governance activities privately.

**Given** I am an active member of the "SHUR Kitchen" domain
**When** I click "Message" on another domain member's profile
**Then** a DM conversation opens (or the existing one if it already exists) and I can type and send messages in real-time.

### US-2: Ecosystem Member Group Chat

**As** an ecosystem member, **I want** to create a group conversation with multiple members, **so that** I can coordinate across domains within the ecosystem.

**Given** I am an active member of the OmniOne ecosystem
**When** I click "New Group" in the messaging view and select 3 other members
**Then** a group conversation is created with all 4 members, and everyone receives messages in real-time.

### US-3: Governance-Linked Discussion

**As** a proposal author, **I want** to create a discussion thread linked to my proposal, **so that** advice phase feedback is captured alongside the proposal.

**Given** I have created proposal PROP-2026-001 ("Add evening kitchen hours")
**When** I click "Discuss" on the proposal detail page
**Then** a conversation is created (or navigated to) that shows the proposal title as a banner, and all advice can be discussed in context.

### US-4: Unread Message Notification

**As** a member, **I want** to see how many unread messages I have, **so that** I know when someone has messaged me.

**Given** I have 3 unread messages across 2 conversations
**When** I view the sidebar navigation
**Then** I see a badge showing "3" next to the "Messages" navigation link.

### US-5: Cross-Ecosystem Boundary

**As** a member of both OmniOne and a partner ecosystem, **I want** messaging to respect ecosystem boundaries, **so that** I only communicate with members in the context of shared ecosystems.

**Given** I am active in OmniOne and EcoPartner ecosystems
**When** I start a new DM from the OmniOne ecosystem context
**Then** I can only select members who are also active in OmniOne, not members exclusively in EcoPartner.

### US-6: Exited Member History Access

**As** a member who has exited an ecosystem, **I want** to retain read access to my message history, **so that** I can reference past governance discussions.

**Given** my status in OmniOne is "exited"
**When** I view the messaging page filtered to OmniOne
**Then** I can read all my past conversations but the message input is disabled with a notice "You have exited this ecosystem."

---

## 6. Technical Considerations

### 6.1 Data Model Design

```
conversations
  id: UUID (PK)
  ecosystem_id: UUID (FK -> ecosystems)
  type: VARCHAR(20) -- "dm" | "group"
  title: VARCHAR(255) -- nullable, required for groups
  created_by: UUID (FK -> members)
  created_at: DATETIME
  updated_at: DATETIME

conversation_participants
  id: UUID (PK)
  conversation_id: UUID (FK -> conversations)
  member_id: UUID (FK -> members)
  role: VARCHAR(20) -- "owner" | "admin" | "member"
  joined_at: DATETIME
  last_read_at: DATETIME (nullable)
  muted: BOOLEAN (default false)
  UNIQUE(conversation_id, member_id)

messages
  id: UUID (PK)
  conversation_id: UUID (FK -> conversations)
  sender_id: UUID (FK -> members)
  content: TEXT
  message_type: VARCHAR(20) -- "text" | "system" | "governance_link"
  metadata: JSON (nullable)
  created_at: DATETIME
  edited_at: DATETIME (nullable)
  deleted_at: DATETIME (nullable)
  INDEX(conversation_id, created_at)

conversation_links
  id: UUID (PK)
  conversation_id: UUID (FK -> conversations)
  entity_type: VARCHAR(50) -- "proposal" | "agreement" | "domain" | "conflict" | "decision"
  entity_id: UUID
  created_by: UUID (FK -> members)
  created_at: DATETIME
  INDEX(entity_type, entity_id)
```

### 6.2 WebSocket Architecture

```
Client                         Server (Sanic)
  |                               |
  |--- WS connect /messaging/ws ->|
  |<-- auth check (session cookie) |
  |                               |-- register in ConnectionManager
  |                               |
  |--- {"type":"message",...} ---->|
  |                               |-- validate & persist to DB
  |                               |-- broadcast to participants via ConnectionManager
  |<-- {"type":"message",...} -----|
  |                               |
  |--- {"type":"typing",...} ----->|
  |                               |-- broadcast typing indicator (no persist)
  |<-- {"type":"typing",...} ------|
  |                               |
  |--- {"type":"read_receipt",...}->|
  |                               |-- update last_read_at in DB
  |                               |-- broadcast read receipt
  |<-- {"type":"read_receipt",...}-|
```

**ConnectionManager** is an in-memory singleton that maps `member_id -> set[WebSocket]` (a member can have multiple tabs open). It provides:
- `register(member_id, ws)` -- add connection
- `unregister(member_id, ws)` -- remove connection
- `send_to_member(member_id, payload)` -- send to all connections for a member
- `broadcast_to_conversation(conversation_id, payload, exclude_sender)` -- look up participants, send to each online member

### 6.3 REST API Endpoints (htmx-compatible)

| Method | Path | Description |
|--------|------|-------------|
| GET | /messaging | Messaging page (full HTML) |
| GET | /messaging/conversations | Conversation list (htmx partial) |
| POST | /messaging/conversations | Create conversation |
| GET | /messaging/conversations/{id} | Conversation detail + messages (htmx partial) |
| GET | /messaging/conversations/{id}/messages | Paginated messages (htmx partial, scroll-up) |
| POST | /messaging/conversations/{id}/messages | Send message (REST fallback) |
| PUT | /messaging/conversations/{id}/messages/{msg_id} | Edit message |
| DELETE | /messaging/conversations/{id}/messages/{msg_id} | Soft-delete message |
| POST | /messaging/conversations/{id}/participants | Add participant (group only) |
| DELETE | /messaging/conversations/{id}/participants/{member_id} | Remove/leave |
| POST | /messaging/conversations/{id}/read | Mark conversation as read |
| POST | /messaging/conversations/{id}/link | Link governance entity |
| GET | /messaging/search | Search messages (htmx partial) |
| GET | /messaging/members | Member picker (htmx partial, filtered by ecosystem) |
| WS | /messaging/ws | WebSocket for real-time messaging |

### 6.4 Integration Points

- **Sidebar Navigation:** Add "Messages" link with unread badge to base.html sidebar (between "Lifecycle" and the user profile section).
- **Member Profile:** Add "Message" button on member detail page.
- **Governance Entity Pages:** Add "Discuss" button and "Discussions" section on proposal, agreement, domain, and conflict detail pages.
- **Auth Middleware:** WebSocket connections must validate the session cookie on initial handshake.

---

## 7. Out of Scope

- **End-to-end encryption:** Messages are stored as plaintext. E2EE would require significant client-side crypto infrastructure.
- **File/media attachments:** Text-only messages in v1.
- **Message reactions/emoji:** Not in initial release.
- **Push notifications:** No external push notification service (email, mobile push) in v1. Only in-app WebSocket notifications.
- **Voice/video calls:** Text messaging only.
- **Multi-replica WebSocket fan-out:** No Redis Pub/Sub or similar. Single-replica only in v1.
- **Message threading/replies:** Flat conversation model in v1, no nested threads.
- **Bot/AI participants in group chats:** The AI assistant remains in its separate chat panel; it does not participate in member conversations.
- **Conversation archiving/export:** No data export for conversation history in v1.

---

## 8. Open Questions

1. **Message retention policy:** Should messages have a maximum retention period, or are they kept indefinitely? (Recommended: indefinite, with future data export via Layer X exit portability.)

2. **Typing indicator throttle:** How aggressively should typing indicators be throttled? (Recommended: broadcast at most once every 3 seconds per member per conversation.)

3. **Governance link permissions:** Should any conversation participant be able to link a governance entity, or only the entity's proposer/steward? (Recommended: any participant, since the link is informational.)

4. **Group conversation size limit:** Is 100 participants a reasonable upper bound? (Recommended: yes, larger coordination should use ecosystem-wide mechanisms.)

5. **DM blocking:** Should members be able to block other members from DMing them? (Recommended: defer to v2, rely on conflict resolution processes for now.)
