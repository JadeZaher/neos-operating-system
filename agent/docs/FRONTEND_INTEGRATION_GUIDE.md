# Frontend Integration Guide

This guide describes how to integrate the generic agent framework with any frontend chat interface, including both bubble and dedicated page modes.

## Overview

The agent framework is frontend-agnostic. It provides a standard API contract for chat interfaces to use. The existing `ChatPanel.tsx` demonstrates a React-based implementation, but the same principles apply to Vue, Svelte, Angular, or vanilla JavaScript.

## Context Management Contract

### Frontend → Agent

Every message sent to the agent should include the following context:

```typescript
interface AgentContext {
  session_id?: string;
  user_id?: string;
  member_id?: string;
  ecosystem_ids?: string[];
  tenant_id?: string;
  page_context_summary?: string;
  current_page?: string;
  active_skill?: string;
  privacy?: 'private' | 'ecosystem' | 'public';
}
```

### Agent → Frontend

The agent returns a response with:

```typescript
interface AgentResponse {
  success: boolean;
  content: string;
  skill?: string;
  thinkingSteps?: ThinkingStep[];
  tools?: ToolCall[];
  artifacts?: Artifact[];
  usage?: TokenUsage;
  context?: {
    session_id: string;
    active_skill: string;
    workflow_state: any;
  };
}
```

## Bubble Chat Mode

The bubble chat is a compact, embeddable widget. Best practices:

- **Minimal context**: Only pass session and ecosystem scope
- **Quick actions**: Show suggested actions from the active skill
- **Tool status**: Show small tool call badges
- **Privacy**: Use compact privacy selector
- **Expand**: Link to dedicated page for complex workflows

### Example Implementation

```tsx
function ChatBubble() {
  const [open, setOpen] = useState(false);
  const { selectedIds, selected } = useEcosystem();
  const { user } = useAuth();

  const handleSend = (message: string) => {
    sendAgentMessage(message, {
      ecosystem_ids: selectedIds,
      member_id: user?.memberId,
      page_context_summary: document.title,
    });
  };

  return (
    <div className="fixed bottom-4 right-4">
      <button onClick={() => setOpen(!open)}>Chat</button>
      {open && <MiniChatPanel onSend={handleSend} />}
    </div>
  );
}
```

## Dedicated Page Mode

The dedicated page is the full-featured chat interface. It should support:

- **Session sidebar**: List, search, and delete conversations
- **Privacy controls**: Toggle between private, ecosystem, public
- **Tool call display**: Show tool names, status, and results
- **Thinking steps**: Show agent reasoning
- **Artifacts**: Link to generated pages or records
- **Context visualization**: Show active ecosystem and skill
- **Workflow progress**: Show multi-step workflow progress

### Existing Implementation

The existing `ChatPanel.tsx` supports both `embedded` and dedicated modes via the `embedded` prop. Use `embedded={true}` for side panels and `embedded={false}` for the dedicated page.

## Open Source Compatibility

To make the frontend generic and open-source friendly:

1. **No hardcoded backend URLs**: Use environment variables
2. **No hardcoded UI text**: Use configuration or i18n
3. **No hardcoded skill names**: Load from agent registry
4. **Pluggable components**: Allow custom message renderers
5. **Standard hooks**: Expose `useSSEChat` or `useAgentChat` as reusable hooks
6. **Theme support**: Use CSS variables or theme tokens

### Generic API Client

```typescript
// lib/agent-client.ts
export async function sendAgentMessage(message: string, context: AgentContext) {
  const response = await fetch(`${API_BASE}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, context }),
  });
  return response.json();
}
```

## Best Practices

1. **Always pass scope**: Ecosystem and member context are required for governance skills
2. **Preserve session**: Use session IDs to maintain conversation continuity
3. **Handle errors**: Show user-friendly error messages
4. **Show tool calls**: Make agent actions transparent
5. **Respect privacy**: Don't share private messages in ecosystem/public mode
6. **Cache sessions**: Use local storage or session storage for UX
7. **Stream responses**: Use SSE for real-time responses

## Context Management Matrix

```
Frontend                 →  Agent                     →  Pipeline
─────────────────────────────────────────────────────────────────
Chat Bubble              →  /agent/chat              →  validate
Session ID               →  session_context          →  resolve
Ecosystem                →  scope_context            →  create
Page Summary             →  page_context             →  audit
Message                  →  user_intent              →  workflow

Result                   ←  Agent Response           ←  Pipeline
─────────────────────────────────────────────────────────────────
Content                  ←  assistant text           ←  success/data
Skill Badge              ←  active_skill             ←  tool name
Tool Calls               ←  tools[]                  ←  operations
Artifacts                ←  artifacts[]              ←  created records
Thinking Steps           ←  thinkingSteps[]          ←  execution trace
```

## Testing

1. Test bubble mode on multiple pages
2. Test dedicated page with session switching
3. Test privacy modes
4. Test tool call display
5. Test context preservation across reloads
6. Test error handling
7. Test with different ecosystem scopes

## Security

1. Never expose API keys in frontend
2. Validate privacy server-side
3. Sanitize user input
4. Use authentication for agent endpoints
5. Audit all agent actions
