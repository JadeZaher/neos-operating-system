# API architecture

## OAuth return origins

The production backend serves more than one frontend origin. OAuth initiation therefore carries the initiating frontend through the provider round trip in signed `state`, instead of relying on one global redirect URL.

Only origins listed in `CORS_ORIGINS` or `FRONTEND_URL` may be encoded or accepted. The signed state must also match the short-lived, HttpOnly transaction cookie set for the initiating browser; callbacks consume that cookie and reject missing or mismatched state before token exchange.

Keep the provider callback itself on `OAUTH_REDIRECT_BASE`; changing the consumer origin must not require additional provider callback registrations or permit an open redirect.

## Agreement consent and participation gates

Agreement consent is a personal, version-bound attestation, never a free-text
ratification or an administrator grant. `agreements.py` records it in
`AgreementMemberConsent`, writes balancing `MemberAlignmentEvent` ledger rows,
and relies on the central evaluator in `services/agreement_consent.py` for all
participation gates. Reuse that evaluator for ecosystem membership, domain
membership, and collaboration actions; do not reimplement a local shortcut.

New agreements follow the mandatory ACT sequence `draft → advice → consent →
test → active`. Status changes are ceremony records, and activation requires
both complete required consent and test evidence. Agreement policy and consent
must only be changed through the agreement endpoints so history and gates stay
in sync.

## ACT gate engine and gate inheritance

`services/act_gates.py` owns the ACT gates for proposals AND agreements. Each
record's `act_policy` declares minimum advice rounds, consent
requirement/quorum, and test cases; the engine auto-advances status when the
conditions are met and mints the decision artifact at completion
(`artifact_type` "proposal" or "commitment" with member participants).
A proposal with NULL `act_policy` inherits gates from its
`governing_agreement_id` (same-ecosystem agreement, validated on
create/update); explicit-null in PUT clears the declaration or the link.
Detail payloads carry `gates` (with `policy_source`), effective `act_policy`,
stored `own_act_policy`, and a `governing_agreement` brief — never recompute
any of this in a view. Agreement advice rounds and test evidence are recorded
via `POST /agreements/:id/ceremonies` (`outcome` "round"/"evidence"); manual
forward transitions that skip unmet gates are rejected 409 with the gates
payload.

## Proposal authorship and manage rule

`proposals.proposer_member_id` records the member who authored a proposal: the
caller's own `Member` row in the proposal's ecosystem, set on REST and MCP
create. The free-text `proposer` is display text only. It defaults to the
author's display name, may name someone else when proposing on their behalf,
and is fixed after creation (`ProposalUpdateRequest` has no proposer field).

Participation and management are separate:

- **Participate** (`caller_can_conduct`): any member row in the ecosystem may
  give advice, record consent, or file test reports.
- **Manage** (`caller_can_manage`, `can_manage_proposal`): editing (PUT) and
  manual status moves (POST `/status`) need the author OR an ecosystem steward
  (`ROLE_RANK >= mod`). Otherwise the response is 403 with `MANAGE_DENIED`.
  A proposal with a NULL author link (legacy, or created by a path that does not
  set it) is steward-only, the same rule `discover.py` applies to legacy
  shares and needs. MCP `transition_proposal` applies the rule to withdrawing
  and to `draft -> advice`; its forward moves only run the gate engine.

Advice integrity: blank advice is rejected with 400, because a blank entry would
still count toward the advice gate. The author cannot advise their own proposal
(409 `SELF_ADVICE_DENIED`, REST and MCP), so they cannot advance it to consent
alone. The advisor name always comes from the caller's member row, never from
the request body.

The migration `n6a1d4f8b2c5` backfilled the link only where the proposer text
matched exactly one member's display name in the same ecosystem. Always
resolve the caller per ecosystem (`_caller_member`); `request.ctx.member` is
an arbitrary row.

## Domain naming and participation flags

`domains.name` is the human name. `domain_id` (`DOM-XXXXXXXX`) is a generated
business key and must only appear as secondary text. Serializers emit
`display_name` = `name`, else the purpose's leading `"Name — "` segment (1-120
characters), else `domain_id` (`domain_display_name`). The fallback keeps
legacy rows and fresh `create_all` databases readable without the backfill.

Caller flags are computed on the server so the UI survives reloads:

- list items: `caller_is_participant` (an active `CircleMembership` for any
  of the caller's member rows, one IN query per page) and `caller_is_steward`.
  The envelope adds `caller_can_create` (mod+ in a scoped ecosystem).
- detail: `caller_is_participant`, `caller_is_steward` (`steward_id` is the
  caller's member), `caller_can_edit` (domain steward or mod+), and
  `participants` (active roster) with `participant_count`.

Stewardship and participation are separate records. A steward who has not
joined is still offered Join, because domain-scoped publishing checks active
participation. Creating a domain requires `require_ecosystem_role(..., "mod")`.
Updating requires the domain's steward or mod+ (403 `EDIT_DENIED`). Moving
`require_admin` to per-ecosystem checks is deferred to the role-tiers phase of
`governance_matching_ux_enforcement_20260727`.
