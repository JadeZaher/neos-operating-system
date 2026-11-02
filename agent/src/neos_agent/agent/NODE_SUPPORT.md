# Agent node support

`node_admin_tools` exposes catalog, bounded record lookup, inspection and command tools only after a current server-side NodeAdmin check and an explicitly enabled support context containing the selected organization UUID and public reason category. Model arguments cannot supply or change caller identity, reason or organization. Parent-scoped lookup follows resource relationships and returns at most 25 rows, scanning at most 1000 candidates before asking for a narrower search.

`definitions_for_node_admin(factory, caller_user_id, support_context)` returns catalog, inspection and command definitions. `execute_node_admin_tool` takes the same context plus server-maintained `confirmed_keys` and optional `agent_session_id`. Every command requires a SHA-256 confirmation over the exact command/context, including inspected version; a model-supplied `confirmed` flag alone grants nothing. Execution rechecks role and target organization. Audit source is agent and correlation ID is the session UUID.

Support sessions belong to their actual User through `AgentSession.owner_user_id`, including operators without any organization membership. They remain private and cannot be shared publicly or with an ecosystem; frozen arguments, support context and inspected private bodies must not enter shared serializers. Public support actions are visible through the separate redacted audit trail.

The wrappers call the same service as REST and catch persistence failures without exposing SQL parameter values or private bodies. No support tool manufactures another member's consent, author identity or independent attestation. Evidence restoration is limited to the exact immutable private archive of original records.
