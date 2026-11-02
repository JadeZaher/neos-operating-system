# Support authority and provenance

NodeAdmin assignments attach to global Users; user-editable profiles and earned badges never grant authority. NodeAdminAction is the public append-only event stream. NodeAdminSnapshot is a private append-only archive of original evidence and support correction snapshots. Both tables install SQLite/PostgreSQL immutability triggers on create_all as well as migration. Their actor/target snapshots do not cascade away when application records change.

User.disabled_at disables session, password, DID, OAuth and agent-token access and removes the operator from the public roster. AgentSession.owner_user_id supports actual-user ownership even without any Member; historical sessions are backfilled from their Member.user_id. Proposal.support_created_by_user_id and support_action_id identify an administrator creating for an organization without forging proposer membership.

Detailed service contracts and bootstrap behavior: ../services/NODE_SUPPORT.md (from the db directory, ../../services/NODE_SUPPORT.md from this models directory).
