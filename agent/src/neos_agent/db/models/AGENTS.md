# Support authority and provenance

## Engagement records

`engagement.py` defines global-User-owned settings, scoped follows, source occurrences, inbox receipts, verified contact generations and durable delivery state. Occurrence/inbox/consumption uniqueness prevents repeated fanout. Push consumption is per device; email/SMS consumption is per channel. Push registrations bind an auth session with SET NULL on session deletion, preserving delivery history while making an expired registration ineligible. The additive `z6f0c4e8b2d5` revision follows `y5e9b3d7a1c4`; it grants no contact verification or external consent to existing users.

NodeAdmin assignments attach to global Users; user-editable profiles and earned badges never grant authority. NodeAdminAction is the public append-only event stream. NodeAdminSnapshot is a private append-only archive of original evidence and support correction snapshots. Both tables install SQLite/PostgreSQL immutability triggers on create_all as well as migration. Their actor/target snapshots do not cascade away when application records change.

User.disabled_at disables session, password, DID, OAuth and agent-token access and removes the operator from the public roster. AgentSession.owner_user_id supports actual-user ownership even without any Member; historical sessions are backfilled from their Member.user_id. Proposal.support_created_by_user_id and support_action_id identify an administrator creating for an organization without forging proposer membership.

Detailed service contracts and bootstrap behavior: ../services/NODE_SUPPORT.md (from the db directory, ../../services/NODE_SUPPORT.md from this models directory).
