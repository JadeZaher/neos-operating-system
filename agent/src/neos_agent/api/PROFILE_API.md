# Public profile API

Profiles are platform-user resources, not single-ecosystem member resources. The profile API resolves usernames, user UUIDs, and member UUIDs to one `User`, then aggregates all of that user's active member identities. Active circle memberships and completed public quiz results are joined back to their domain and ecosystem so one public response remains stable when a user belongs to multiple ecosystems.

The response is intentionally allowlisted. Never serialize DID, phone, password/auth fields, member notes/privacy, KYC data, raw quiz answers, assessment-derived tags or badges, or non-public publications. User-authored shares, needs, and solutions appear only when both `visibility == "public"` and `status == "active"`.

Profile writes are owner-only and limited to the public fields validated by `schemas/profiles.py`. Publication writes use `SharesNeeds.author_member_id`; non-admin mutation authorization follows that member identity back to its platform user. Rows created before author tracking remain admin-managed instead of guessing an owner.
