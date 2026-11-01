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
payload. Which moves exist, their gates and which are automatic live in the
lifecycle tables; see `services/AGENTS.md` "ACT lifecycle".

## Proposal authorship and manage rule

`proposals.proposer_member_id` records the member who authored a proposal: the
caller's own `Member` row in the proposal's ecosystem, set on REST, MCP and
chat-assistant create. The free-text `proposer` is display text only. It defaults to the
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
  shares and needs. REST `POST /status`, MCP `transition_proposal` and the
  chat tool `update_proposal_status` all call
  `act_gates.transition_proposal(..., to=...)`, which applies the manage rule,
  the table and the gate (MCP forward moves used to skip the manage rule).

Advice integrity: blank advice is rejected with 400, because a blank entry would
still count toward the advice gate. The author cannot advise their own proposal
(409 `SELF_ADVICE_DENIED`, REST, MCP and chat), so they cannot advance it to
consent alone. Advice is taken only in the advice stage (409 `ADVICE_CLOSED`).
The advisor name always comes from the caller's member row, never from
the request body; the row also records `member_id`.

The migration `n6a1d4f8b2c5` backfilled the link only where the proposer text
matched exactly one member's display name in the same ecosystem. Always
resolve the caller per ecosystem (`guards.caller_in`; `caller_member` where
there is no request); `request.ctx.member` is only a default row (see
"Handler contracts").

## Domain naming and participation flags

`domains.name` is the human name. `domain_id` (`DOM-XXXXXXXX`) is a generated
business key and must only appear as secondary text. Serializers emit
`display_name` = `name`, else the purpose's leading `"Name — "` segment (1-120
characters), else `domain_id` (`domain_display_name`). The fallback keeps
legacy rows and fresh `create_all` databases readable without the backfill.
Profile payloads (`profiles.py`: domain participation, quiz scopes,
publications) carry the same `display_name`, and `domain_name` is that label.

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

## Chat assistant tools (caller-scoped)

The in-app assistant (`api/chat.py`, legacy `views/chat.py`) runs
`agent/governance_tools.execute_tool` with `caller_user_id` = the signed-in
user. Every state-changing tool is in `CALLER_SCOPED_TOOLS`: it acts as that
member, returns `CALLER_REQUIRED` without one, resolves the caller's row in
the record's ecosystem (`_caller_row`, the request-free `caller_in`) and asks
the same `policy` predicate as REST. A model-chosen argument never stands in
for identity: `participant`, `declared_by`, `recorder`, `auditor`,
`reporter_id`, `created_by` and `member_name` are ignored or refused.

| Tool | Rule (policy) | Identity from the caller |
|---|---|---|
| `create_proposal` | a member row in the scoped ecosystem | author (`proposer_member_id`); `proposer` is display text |
| `record_advice` | not the author (`is_proposal_author`) | advisor |
| `record_consent_position` | `can_participate`, then `act_gates.record_consent_position` (one position per member, as REST) | participant |
| `update_proposal_status` | `transition_proposal` (manage rule, table, steward-only, `note` for send-backs, gate); withdraw and ratify need confirmation | actor |
| `create_agreement_draft` | `is_active_member_in` (REST: authorized ids) | proposer text defaults to the caller |
| `update_agreement_status` | `agreements.transition_agreement` (ceremony steward, table, `evidence`, gate); needs confirmation for active, sunset and archived, and when the automatic cascade after the ceremony would put it in force | conductor; the version never changes |
| `create_decision_record` | `can_record_decision` (steward; no REST route, decisions are minted by ACT) | recorder |
| `declare_emergency` | `emergency.declare` (`can_declare_emergency`; pending until a co-signer); needs confirmation | declarer |
| `cosign_emergency` | `emergency.cosign` on a row loaded FOR UPDATE (`cosign_refusal` first); needs confirmation | co-signer |
| `end_emergency_authority` | `emergency.end_authority` on a row loaded FOR UPDATE (`end_authority_refusal` first); needs confirmation | whoever ends it |
| `record_emergency_review` | `emergency.record_review` on a row loaded FOR UPDATE (`review_refusal` first); needs confirmation when the outcome is `complete` (final) | reviewer |
| `create_exit_record` | `is_active_member_in`; only one's own exit (`EXIT_SELF_ONLY`); one open exit; needs confirmation | the leaving member |
| `create_conflict_case` | `is_active_member_in` (as REST); parties resolved to member ids; needs confirmation when it names parties (they can then read the report) | reporter |
| `create_safeguard_audit` | `is_active_member_in` (as REST); the audit is a human-owned draft | auditor (`auditor_ids`) |
| `triage_conflict`, `create_repair_agreement` | `can_triage_conflict` (a hidden case is not found); `CONFLICT_MOVES` | triager |
| `join_domain` | active member; `missing_agreement_consents` (as `POST /domains/:id/participation`) | participant |
| `submit_test_report` | `can_participate`, test stage; declared case names only | reporter (`reporter_member_id`) |
| `withdraw_consent_position` | `act_gates.withdraw_consent_position` | the position's owner |
| `record_agreement_evidence` | `is_active_member_in`, matching stage (as `POST /agreements/:id/ceremonies`); needs confirmation when it would put the agreement in force | `completed_by_member_id` |
| `create_domain_draft` | `is_steward_in` (REST `require_ecosystem_role` mod) | `created_by` |
| `create_ecosystem` | signed in (as REST) | founder joins as an active `co_creator` and stewards a core domain |

Caller-aware reads (they need no write rule, only the caller's identity):
`what_needs_me` (`next_steps.waiting_for`, every ecosystem the caller is active
in, equal to `GET /me/next-steps`), `explain_status` (`next_steps.explain_record`
after the tool's own lookup, equal to `GET /explain/<kind>/<id>`),
`get_conflict_case` (`can_view_conflict`: a hidden case is "not found"; the REST
detail payload plus the banner's words) and `get_exit_status` (an exit in
scope or the caller's own; without an id, the caller's own exits).

Every lookup takes the page's UUID, the business key or the exact title, and
results carry names, links, the engine's gates and a next step. Irreversible
acts need the member's yes in a later chat turn. Details: `agent/AGENTS.md`.

`update_agreement_status` used to keep its own table (`consent -> active`),
skip the gates and evidence, and bump the version on advice, consent and
active. The bump silently voided every member's consent, which is bound to
`agreement.version`; it now calls the REST/MCP engine, so a ceremony records
its `AgreementCeremony`, snapshots an `AgreementVersion`, and activation mints
the commitment artifact. Since G-ACT (see "ACT integrity (G-ACT)"), REST and
MCP keep one consent position per member, an objection's author can lift it,
and ratification needs a steward; chat `record_consent_position` calls the
same `act_gates.record_consent_position` (G-Agent).

## ACT parity

One script of ACT moves runs through REST, MCP and chat in
`tests/test_uxqa_p1_mcp_parity.py`; every surface must refuse and allow the
same moves and leave the same status.

| Move | REST | MCP | Chat |
|---|---|---|---|
| open draft -> advice | `POST /proposals/:id/status` | `transition_proposal` | `update_proposal_status` |
| forward move with unmet gate | 409 + `gates` | `ValueError` with gates | refusal text |
| advice | `POST /advice` (author refused) | `record_proposal_advice` | `record_advice` |
| consent position | `POST /consent` (caller, body name ignored, one per member) | `submit_proposal_consent` (same engine call) | `record_consent_position` (same engine call) |
| close advice | `POST /status consent` (manage rule) | `transition_proposal` | `update_proposal_status` |
| test report | `POST /test` (test stage, reporter recorded) | `submit_test_report` | `submit_test_report` |
| ratify | `POST /status ratified` (steward only) | `transition_proposal` | `update_proposal_status` |
| send back | `POST /status advice` + `note` | needs `note` (hand-off) | `update_proposal_status` + `note` |
| withdraw | manage rule, non-terminal only | manage rule | manage rule |
| agreement ceremony | `POST /agreements/:id/status` | `transition_agreement` | `update_agreement_status` (with `evidence`) |
| agreement round / evidence | `POST /agreements/:id/ceremonies` | `record_agreement_ceremony` | `record_agreement_evidence` |

The agreement script also refuses short evidence, an unmet advice gate and a
skipped stage on every surface, and checks that no surface changes the
version. An agreement move the table lacks is a 400 carrying `allowed`, as
for proposals, so MCP and chat can name the valid next stages.

## Sign-up placement and the consent gate

Password register, DID verify and OAuth callback share `auth.py` helpers. A
returning user keeps their oldest membership (`existing_membership`); a new
one is placed by `signup_ecosystem`: the requested `ecosystem_id`, else
`SIGNUP_DEFAULT_ECOSYSTEM_SLUG` (an id or the slug of a name), else the oldest
ecosystem ordered by `created_at`, `founded_date` (nulls last), `id`. Seeds
insert every ecosystem in one transaction, so `created_at` ties and
`founded_date` decides; never rely on the id tie-break. Set
`SIGNUP_DEFAULT_ECOSYSTEM_SLUG=omnione` in every deployment (Railway agent
service, the uxqa stack `uxqa/adapter/stack.sh`, local `.env`).

`create_signup_member` applies the ecosystem-membership agreement gate exactly
like `POST /ecosystems/:id/join`: `pending_consent` until each required
agreement is attested. Register/verify responses add `status`
(`consent_required` | `joined`) and `required_agreements`; OAuth redirects a
gated newcomer to the client route `/welcome/consent` (`CONSENT_GATE_PATH`);
`GET /auth/me` returns `pending_consents` (ecosystem + missing agreements per
pending membership) so the client can show the gate after any sign-in path.

## Join-first self-service writes

Orientation progress (`POST /orientation/ethos/:id/progress`) and ethos
participation consent (`POST /ethos/:id/access/consent`) are stored per
member row, so they need the caller's row in that ecosystem (any status: a
pending-consent row is enough). A member of A opening public ecosystem B has
none. `guards.caller_in_or_join_required` answers 404 (`"Ecosystem not
found"` / `"Ethos not found"`) only when the ecosystem does not exist, and
otherwise 409 `{"error": "Join this ecosystem to …", "code":
"JOIN_REQUIRED"}`. Beginning an orientation or consenting is an intent to
join, so the client joins first (`POST /ecosystems/:id/join`, which creates
the row as active or pending consent) and then retries; see
`client/src/AGENTS.md` "Orientation journeys". The reads (`GET .../progress`,
`GET .../access/me`) still answer empty for a non-member.

## Chat sessions

A session belongs to the member row of its own ecosystem
(`_save_session` uses `caller_in` for the session's ecosystem). Reads match
the caller's rows in scope: the selection for the list, every authorized
ecosystem for one session. A caller with no authorized ecosystem (only
pending or exited rows) would match nothing, so `_member_ids_in` falls back
to all of the caller's own rows, any status. It is always filtered by the
caller's `user_id`, so the fallback widens the caller's own history only,
never anyone else's.

## Handler contracts

Shared building blocks for JSON handlers (craft plan BE1/BE2, wave 0). Each
one replaces copies that had drifted into a class of bug. Wave-1 lanes migrate
handlers onto them; new handlers use them from the start. The probe blueprint
in `tests/test_api_contracts.py` is the executable version of the examples.

| Contract | Signature | Removes |
|---|---|---|
| `guards.authenticated` | `@authenticated` above `async def handler(request, ...)` | `member, err = require_auth(request)` boilerplate |
| `guards.caller_in` | `await caller_in(session, request, ecosystem_id) -> Member \| None` | per-ecosystem decisions made on the session's default row |
| `guards.reachable_ecosystem_ids` | `await reachable_ecosystem_ids(session, request, include_pending=True) -> list[UUID]` | the inline active+pending membership query in `get_agreement` |
| `guards.caller_in_or_join_required` | `await caller_in_or_join_required(session, request, ecosystem_id, *, not_found=..., join_message=...) -> Member` | a 404 that told a non-member the ecosystem does not exist; see "Join-first self-service writes" |
| `policy` | `is_steward(member)`, `is_steward_in(member, ecosystem_id)`, `can_manage_proposal(member, proposal)`, `can_edit_domain(member, domain)`, `can_conduct_agreement_ceremony(member, agreement)`, `can_assign_role(caller, target, new_role)`; also `ROLE_RANK`, `role_rank`, `has_role_at_least`, `is_proposal_author`, `is_domain_steward`, `is_profile_admin` | rules restated in REST, MCP and chat |
| `errors.ApiError` | `raise ApiError(status, message, extra=None)` -> `{"error": message, **extra}` | hand-built error JSON |
| `errors.get_scoped_or_404` | `await get_scoped_or_404(session, request, Model, entity_id, *, options=(), label="Proposal", ecosystem_ids=None, include_shared=True)` | fail-open detail scoping; 403s that confirm a row exists |
| `helpers.parse_pagination` | `parse_pagination(request, default=25, cap=100) -> Page` (`page`, `per_page`, `offset`) | `?page=abc` -> 500 |
| `auth.ecosystem_scope` | `restrict_to_ecosystems(stmt, Model, ecosystem_ids, *, include_shared=True)`; `EcosystemScope.filter(stmt, Model)` | fail-open `if eco_ids:` filters |

Why each one is shaped the way it is:

- `@authenticated` is authentication only: exactly `require_auth`'s 401
  (`{"error": "Authentication required"}`), else the handler runs and reads
  `request.ctx.member`. It keeps the handler's `__name__`, which Sanic uses as
  the route name, so two guarded handlers never collide.
- `request.ctx.member` is a deterministic default, not "the caller in X".
  `main._load_ecosystems` first drops every cookie id the user is not ACTIVE
  in (stale, foreign, pending consent); when none is left, or there is no
  cookie, the scope is the default ecosystem: the oldest ACTIVE membership by
  `created_at`, then `id` (seeds share one `created_at`; the id breaks the
  tie). An empty scope therefore means the user has no active membership at
  all, never "the cookie named the wrong ecosystem". `guards.default_member`
  then gets that FILTERED scope and returns the oldest active row inside it,
  else the oldest membership at all (a newcomer whose only row is pending
  consent). So whenever the scope is non-empty, `ctx.member.ecosystem_id` is
  in it, and with one ecosystem in scope both name the same one. Use it for
  identity (`user_id`, name). For any decision about a resource, use
  `caller_in(session, request, resource.ecosystem_id)`.
- `policy` predicates are pure, so REST, MCP and chat tools call the same
  function. Resource predicates return False for a member row from another
  ecosystem, so passing `request.ctx.member` by mistake fails closed instead of
  letting a steward of one ecosystem act in another. `is_steward` has no
  resource, so it checks no ecosystem: give it a `caller_in` row, or use
  `is_steward_in(member, ecosystem_id)`, which fails closed the same way.
  Unknown roles rank below `user` (the stricter of the old copies; the role
  CHECK constraint makes it unreachable for stored rows).
- `ApiError` is rendered once by `register_api_errors(app)` in `main.py`.
  Never raise Sanic `NotFound`: the catch-all in `main.py` rewrites its message
  to "Not found" and redirects non-API paths to the dashboard.
- `get_scoped_or_404` scopes to every authorized ecosystem (owned or shared,
  the `apply_ecosystem_filter` match), not the UI selection, so a deep link
  into another of the user's ecosystems still opens. A row outside scope and a
  missing row return the same 404 body. Both knobs are explicit keywords:
  `ecosystem_ids=` replaces the authorized set (the consent-gate exemption in
  rule 5), `include_shared=False` drops the shared-with match (only for an
  entity whose list matches owners only).
- `parse_pagination` rejects non-integers (400) and clamps integers
  (`page >= 1`, `1 <= per_page <= cap`) as the inline copies did, so valid
  clients see no change. A page whose offset would overflow SQL BIGINT is also
  a 400.
- `restrict_to_ecosystems` turns an empty id list into `WHERE false`. The old
  `if eco_ids:` guard dropped the filter instead, so `?ecosystem_ids=` naming
  only foreign ecosystems (intersected to `[]`), or a newcomer whose only
  membership awaits consent, listed every ecosystem's rows.
  `EcosystemScope.filter` is the same rule over a scope's `selected_ids`.

Before:

```python
@proposals_api_bp.post("/<proposal_id:uuid>/status")
async def change_status(request, proposal_id):
    member, err = require_auth(request)
    if err:
        return err
    async with request.app.ctx.db() as session:
        stmt = select(Proposal).where(Proposal.id == proposal_id)
        eco_ids = get_authorized_ecosystem_ids(request)
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Proposal, eco_ids)
        proposal = (await session.execute(stmt)).scalar_one_or_none()
        if proposal is None:
            return json({"error": "Proposal not found"}, status=404)
        caller = await _caller_member(session, member.user_id, proposal.ecosystem_id)
        if not can_manage_proposal(caller, proposal):
            return json({"error": MANAGE_DENIED}, status=403)
```

After:

```python
@proposals_api_bp.post("/<proposal_id:uuid>/status")
@authenticated
async def change_status(request, proposal_id):
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        if not can_manage_proposal(caller, proposal):
            raise ApiError(403, MANAGE_DENIED)
```

Lists: `page = parse_pagination(request)`, then
`stmt = restrict_to_ecosystems(stmt, Model, get_ecosystem_ids(request))` and
`.offset(page.offset).limit(page.per_page)`.

Migration rules for wave-1 lanes:

1. Route decorator outermost, `@authenticated` directly above `async def`.
   Read `request.ctx.member` where the handler used `member`. Keep
   `require_admin` calls as they are.
2. Every authorization decision: `caller_in(...)` for the resource's
   ecosystem, then a `policy` predicate. Delete local `_caller_member`,
   `_member_in_ecosystem` and inline `select(Member).where(user_id,
   ecosystem_id)` copies. Code with no request resolves the same row itself:
   `mcp_server._row` and `governance_tools._caller_row`.
3. `ROLE_RANK.get(m.role, 0) >= ROLE_RANK["mod"]` -> `is_steward(m)` when `m`
   is a `caller_in` row, else `is_steward_in(m, ecosystem_id)`; the
   `members.py` role matrix -> `can_assign_role`; active plus
   `role in {"admin", "owner"}` -> `can_conduct_agreement_ceremony`. Local
   `can_manage_proposal` / `_can_edit_domain` copies -> `policy`. Import
   `ROLE_RANK` from `policy` (`helpers` re-exports it for old imports).
4. `if eco_ids: stmt = apply_ecosystem_filter(stmt, M, eco_ids)` ->
   `stmt = restrict_to_ecosystems(stmt, M, eco_ids)`, keeping the same id
   source (`get_ecosystem_ids` for lists, `get_authorized_ecosystem_ids` for
   details). A caller with no ecosystems now gets an empty result.
5. Single-row loads by primary key -> `get_scoped_or_404` with the existing
   label, so the 404 body is unchanged. A detail load matches its list's
   visibility: a row the list can show must open, a row it never shows must
   404. Every list of a shareable entity (agreements, conflicts, decisions,
   domains, exits, members, proposals) matches owned-or-shared rows
   (`apply_ecosystem_filter`), so the default `include_shared=True` is right;
   pass `include_shared=False` only for an entity whose list matches owners
   only. On a model without `shared_ecosystem_ids` the flag changes nothing. Writes on a shared row
   still authorize with `caller_in` for the row's own ecosystem, so a shared
   row opens but a foreign steward cannot change it. Entities whose detail
   differs from the list today (migrating them with the defaults fixes both):
   - Agreements: the list is owned-or-shared, but detail, update, status,
     ceremonies, history and rollback filter `Agreement.ecosystem_id` only, so
     a shared agreement is listed and then 404s; consent (POST and DELETE)
     loads with no scope at all.
   - Exit records: detail and status scope to the cookie selection
     (`get_ecosystem_ids`, and drop the filter when it is empty) instead of
     every authorized ecosystem, so a row listed through `?ecosystem_ids=`
     404s on open, and an empty selection opens any ecosystem's record.

   Exemption: agreement detail, history and consent (POST and DELETE) use the
   active+pending scope,
   `ecosystem_ids=await reachable_ecosystem_ids(session, request, include_pending=True)`.
   A newcomer behind the consent gate is not authorized anywhere yet, but must
   read and consent to the agreements the gate lists (client
   `ConsentGatePage`); consenting is what activates them. This also covers a
   member active in one ecosystem and pending in another, whom the old
   `get_agreement` fallback (pending ids only when nothing is authorized)
   refused. Consent on a foreign agreement changes from 403 ("Only an
   ecosystem member may…") to 404. Every other agreement route keeps the
   default active-only scope.
6. Expected failures -> `raise ApiError(status, message, extra)` with the same
   body as before; success responses stay `json(...)`.
7. `int(request.args.get(...))` pairs -> `parse_pagination(request,
   default=<current default>, cap=<current cap>)`. Changing a default (the
   proposals list uses 20, the rest 25) is a visible change; make it on purpose.
8. Test apps that mount blueprints on a bare `Sanic(...)` must call
   `register_api_errors(app)`, or an `ApiError` surfaces as a 500.

Drift found while unifying, deliberately not changed in wave 0:

- "Steward" has two rules: proposals and domains accept any `mod+` row;
  agreement ceremonies require an active `admin+` row. Kept, under separate
  names: `is_steward` / `can_manage_proposal` versus
  `can_conduct_agreement_ceremony` (REST, MCP and chat all call the latter).
  `caller_can_conduct` means "may participate" (`can_participate`) on
  proposals but "may conduct ceremonies" on agreements.
- `ecosystems.py` ~333 lets "a steward of any domain, or the sole member"
  update ecosystem settings: a third rule, outside `policy`.
- The chat tool `check_domain_authority` (`governance_tools.py` ~556) accepts
  a display-name match on `current_steward`; `can_edit_domain` uses
  `steward_id` only.
- `helpers.require_admin` reads `profile` from `request.ctx.member`, the
  default row; `profile` is stored per member row. The default is now the
  oldest active row (or the oldest in the selection), so a creator whose
  `co_creator` row is in a newer ecosystem is refused unless that ecosystem
  is the only one selected. An admin check about a resource must read the
  profile of `caller_in(session, request, resource.ecosystem_id)`
  (`is_profile_admin`).
- Per-member rows keyed on `ctx.member.id` follow the default row, so they
  change with the selection. Fixed in wave 1 for orientation progress, ethos
  access and chat sessions (they key on `caller_in` for the route's
  ecosystem); migration `o7c3e9a5d2f8` moved the existing progress and access
  rows (rule: `alembic/AGENTS.md` "Data revisions"). The same pattern
  (`grep "member_id == member.id"`) still runs through notifications,
  messaging and onboarding.
- `chat.py` shared-chat "ecosystem" privacy: fixed in wave 1. It reads the
  caller's row in the session's ecosystem and requires it to be active
  (`is_active_member_in`), so an exited or suspended member is refused.
- `auth.existing_membership` (the `/auth/me` `member`) is NOT the same rule
  as `guards.default_member`: it orders by `created_at, id` across every
  status, with no active-first key and no selection, so for a user whose
  oldest membership is pending or exited `/auth/me` reports that row while
  `ctx.member` is the oldest active one. Wave 2: build it on `default_member`.
- `/auth/me` `ecosystems` carry no membership status (`status` is the
  ecosystem's own), so the client can tell pending memberships
  (`pending_consents`) but not exited or suspended ones from active. Client
  `lib/consent-gate.ts` uses the one status it has (`member.current_status`).
  Wave 2: add the membership status per ecosystem so the client applies the
  server's active-only rule exactly.


## Conflict care and audits (G-Care)

Owner defaults, each one constant in `policy.py` under "# G-Care":
`CONFLICT_TRIAGE_MIN_ROLE` ("mod": who triages), `CONFLICT_PARTIES_CAN_VIEW`
(True: named parties read the case). Audits default to a human auditor.

- **Reporter.** `POST /conflicts` records the caller (`caller_in`, active member of the ecosystem, else 403); a body `reporter_id` is ignored.
- **Who reads a case** (`policy.can_view_conflict`): reporter, facilitator, members named in `parties` (by member id only, `is_conflict_party`; labels never authorize), and triage stewards. Everyone else gets 404, in the list too (filtered in Python after the ecosystem scope; case volume is small).
- **Who triages or moves a case** (`can_triage_conflict`): an active steward of the ecosystem or the case facilitator, never a named party. The reporter may correct title/description/domain or withdraw (status closed). Any other change is 403.
- **Lifecycle** (`CONFLICT_MOVES` in `conflicts.py`): reported -> triaged -> in_progress -> resolved -> closed (resolved can reopen to in_progress). A move the table lacks is 409 with `allowed`. A status outside the table (a stray older writer) reads as stage "Needs a steward to review", never "Closed", and `allowed_moves` lets triage put it at any stage (`UNKNOWN_STATUS_MOVES`); the assistant should use `allowed_moves` too. Resolving needs a summary (400) and stamps `resolved_date`. A facilitator must be an active member who is not a party.
- **Stage text.** `conflict_stage` gives `stage`, `next_step` and `decided_by`; the UI shows these instead of a promised response time. Detail adds `caller_can_triage` and `allowed_next`.
- **Repair.** Triage authority records repair. Check-ins default to +30/60/90 days; `next_checkin_date` and `next_checkin_overdue` are computed. `status: fulfilled` needs `confirmed_by_parties: true` (400 otherwise) and the server sets `completed_date`.
- **Audits.** `POST /safeguards/audits` starts a draft with the caller as auditor (`auditor_ids` holds their member id; no AI placeholder text). Only that auditor edits (`PUT /audits/:id`) or publishes (`POST /audits/:id/publish`, 403 for others, 409 once published). Publishing needs at least one rated indicator and sets the score as the mean of `INDICATOR_STATUS_POINTS`; status becomes `completed`. `GET /safeguards` reads its score from published audits only. An assistant may draft but not publish. AI analysis is optional and never a state a draft waits in.
- Compliance summaries name an open case by id only, never its title.
- Revision `r6c1e8a4f2d7` schedules check-ins for old unscheduled repairs (from the migration date when the 30-day one is already past), maps the legacy statuses `open` -> `reported` and `in_mediation`/`escalated` -> `in_progress`, clears the old placeholder text on draft audits, and adds the reporter index. It adds no columns (alembic/AGENTS.md "r6c1e8a4f2d7").

## Emergency and exit (G-Safety)

Owner decision (2026-10-31): any ACTIVE member of the ecosystem may declare an
emergency, but it opens only when a second active member co-signs. The
transition functions in `emergency.py` (`declare`, `cosign`, `withdraw`,
`end_authority`, `record_review`, `complete_recovery_for`, `begin_recovery`,
`expire_if_stale`) are the one implementation: REST calls them, the cron
calls `begin_recovery`/`expire_if_stale`, and the assistant calls `declare`,
`cosign`, `end_authority` and `record_review` (G-Next). Each raises `ApiError`;
none commits. `cosign_refusal`, `end_authority_refusal` and `review_refusal`
return the same refusal without acting, so the assistant refuses before it asks
for a confirmation; `caller_flags` is the page's button set. Rules live in
`policy.py` under `# G-Safety`.

| State | Move | Who (policy) |
|---|---|---|
| (none) -> `pending` | `POST /declare {ecosystem_id, reason, auto_revert_days}` | `can_declare_emergency`: active member; declarer = caller |
| `pending` -> `open` | `POST /:id/cosign` | `can_cosign_emergency`: another active member; the timer starts here |
| `pending` -> `withdrawn` | `POST /:id/withdraw`; cron after `COSIGN_WINDOW_HOURS` (48) | declarer or steward |
| `open` -> `half_open` | `POST /:id/resolve`; cron when `auto_revert_at` passes | declarer, co-signer or steward (`can_end_emergency`) |
| `half_open` (review) | `POST /:id/review {outcome: scheduled\|complete, summary}` writes `post_review_status` | `can_review_emergency`: active, and not the declarer, co-signer or whoever ended it |
| `half_open` -> `closed` | `POST /:id/complete-recovery` (409 + `next_step` until the review is complete) | `can_complete_recovery`: active steward |

Bounds are module constants, sent to the client as `GET /emergency` `limits`:
`DEFAULT_AUTHORITY_DAYS` 7, `MAX_AUTHORITY_DAYS` 30 (the skill's default
maximum; 400 above it), `REVIEW_SCHEDULE_DAYS` 14, `RECOVERY_WINDOW_DAYS` 30.

Why it is shaped this way:

- One live emergency per ecosystem (`ACTIVE_STATES` = pending, open,
  half_open), enforced by the database: the partial unique index
  `uq_emergency_states_one_live`. `declare` locks the live rows it can see,
  but two first declarations see none, so the index decides: the loser's
  insert (in a savepoint, so an assistant turn keeps its other work) fails and
  becomes 409 `JUST_DECLARED`. `cosign` also refuses (409 with `emergency_id`)
  while another emergency is live, for a database without the index. A pending declaration past its co-sign window is dead at once
  (`live_condition`, `describe` reports `withdrawn`), before the cron flips the
  row, so a stale declaration never blocks a new one; `declare` flips it.
- `auto_revert_at` only ever means "authority ends". Recovery dates derive from
  `half_open_entered_at` (`review_schedule_by` +14 d, `review_due_at` +30 d), so
  the page never shows a ratification deadline under the authority label.
- Recovery does not auto-close (owner default). Past `review_due_at` the
  payload says `review_overdue` and the next step starts "Review overdue."; the
  client shows it to stewards. The cron never touches `half_open` rows.
- The review excludes emergency actors (post-emergency-review step 1);
  `policy.emergency_actor_ids` reads the declarer, co-signer and the
  `actor_member_id` of the `half_open_transition` log entry.
- Detail and the banner feed carry `phase` (pending, open, recovery, closed,
  withdrawn), the dates above, a plain `next_step` and caller flags
  (`caller_can_cosign`, `_withdraw`, `_end`, `_review`, `_complete_recovery`,
  `caller_is_steward`). `GET /emergency` lists the live emergency per SELECTED
  ecosystem (`active`, `current` = the first) and `caller_can_declare_in`;
  `GET /emergency/active` lists live ones across EVERY authorized ecosystem,
  for the all-member banner.
- The legacy `/dashboard/emergency/declare` and `/:id/resolve` views answer
  410 and change nothing: they skipped the co-signer and jumped open -> closed
  (every legacy write is retired the same way: "Legacy dashboard (views/)").
- Revision `q2a7c5e9d1b3` widens the state CHECK, adds the live index after
  retiring duplicate live rows (alembic/AGENTS.md "q2a7c5e9d1b3"), and adds
  `declared_by_member_id`, `co_signer_member_id`, `co_signed_by`,
  `co_signed_at`, `authority_days` (batch rebuild on SQLite).

Exit (`exit.py`): only the leaver files (`member_id` is the caller; another
id is 403 `EXIT_SELF_ONLY`; one open exit at a time, 409 with `exit_id`) and
only the leaver cancels. A steward who is not the leaver starts the handoff
(`declared` -> `unwinding`, and becomes `coordinator_id`) and confirms the
departure (`completed`), which sets the member `exited` with a
`MemberStatusTransition`, so they drop out of the agreement-consent
participating set. A move loads the exit row `FOR UPDATE`, so two stewards
confirming at once run one after the other: the second re-reads `completed`
and gets 409, and only one `MemberStatusTransition` is written. `EXIT_MOVES` is the table; free-text statuses are 400, so
the old client "export" that wrote `export_requested` into the status cannot.
The handoff ends by `target_completion_date` (30 days, 7 urgent; the skill's
maximum). Payloads carry `member_name`, `reason` (`departure_notice`),
`next_step`, `caller_is_leaver` and `allowed_next`. The leaver can still open
their own record after leaving (no scope there any more).

`GET /exit/:id/portable-record` (leaver only: 403 in scope, else 404) returns
the person's own record across all memberships: memberships, proposals
authored, advice given, consent positions, test reports filed, agreements
consented. It sets `data_export_requested`/`data_export_completed` and never
the status. Rows are matched on their member-id columns only
(`consent_participants.member_id`, `advice_entries.member_id`,
`test_reports.reporter_member_id`). Rows without an id are never matched by
display name: names are editable, so after a rename a name match would hand
the leaver a namesake's rows. Unlinked rows under the member's current name
are left out and counted in `omitted`. Legacy consent rows whose name was
unique when `p8d4f1b6e3a9` ran were linked by that revision (a frozen match a
later rename cannot move); legacy advice rows were not, so they stay omitted
until a revision backfills `advice_entries.member_id` the same way.

## ACT integrity (G-ACT)

Owner decisions live since 2026-10-31; the table and engine rules are in
`services/AGENTS.md` "ACT lifecycle" and "One gate vocabulary". What the API
adds on top:

| Route | Rule |
|---|---|
| `POST /proposals/:id/consent` | the caller's row in the proposal's ecosystem only (403 otherwise; no shared-ecosystem fallback); one position per member, owned by `member_id`, a second call replaces it; `member_name` is gone from the schema (ignored if sent) |
| `DELETE /proposals/:id/consent` | withdraw the caller's own position (`withdrawn`); the only way an objection is lifted, so only its author lifts it |
| `POST /proposals/:id/advice` | 409 outside advice; records `member_id` |
| `POST /proposals/:id/test` | 409 outside test; records `reporter_member_id` (detail adds `reporter_name`) |
| `PUT /proposals/:id` | author or steward; outside draft/advice any changed value is 409 `PROPOSAL_LOCKED` (see "The text members decide on") |
| `POST /proposals/:id/status` | `{status, note}`; `note` required to send back (consent/test -> advice); `ratified` needs a steward who is not the author (`policy.can_confirm_ratification`; the author-steward, or on a legacy proposal the steward its proposer text names, gets 403 `code: NEEDS_ANOTHER_STEWARD`); no withdrawal once ratified or withdrawn |
| `POST /proposals/:id/register-agreement` | `agreements.register_ratified_proposal`; `policy.can_register_agreement` (active mod+ of the ecosystem); proposal row locked; 409 unless ratified, unregistered and with captured `ratified_text` |
| `PUT /members/:id` | self only; a `profile` that confers administration (co_creator, builder) is 403 `PROFILE_GRANT_ONLY` unless already held (`policy.can_choose_own_profile`); `POST /members` likewise |
| `PUT /members/:id/role` | `policy.can_assign_role` (owner decision) and a recorded `MemberStatusTransition` |
| `PUT /members/:id/profile-grant` | `policy.can_grant_profile`: whoever may make the member an admin, never on yourself; recorded like a role grant |
| `POST /onboarding/:member_id/ceremony` | `policy.can_record_onboarding_consent`: the member or a steward of their ecosystem, else 403 |

Proposal detail adds `allowed_next` (the caller's manual moves with `ready`),
`caller_position` (`{position, reason}` in the latest consent record),
`caller_can_register`, and briefs (`id`, `agreement_id`, `title`, `status`,
`version`) for `governing_agreement`, `amends_agreement` and
`registered_agreement`. Sub-records are serialized oldest first, so the last
consent record is the one the gate reads. A governing or amended agreement
must be in force (`active`, `under_review`); `decision_type` is `consent` or
`consensus`.

### The text members decide on

From consent on, members are deciding on the proposal as written, so `PUT
/proposals/:id` (author and steward alike) refuses any changed value outside
draft and advice with 409 `PROPOSAL_LOCKED`; the edit form resends every field,
so an unchanged resend (trimmed text, empty == unset) is not a change. The
only way to change the text after advice is "Send back for revision", which
reopens advice (new minor version, fresh advice and consent rounds). Entering
`ratified` copies the trimmed `proposed_change` into `proposals.ratified_text`
(`act_gates._enter_proposal_stage`, so REST, MCP and chat all capture it), and
registration reads only that column: a later write to `proposed_change` by a
route that skips this lock (legacy views, direct SQL) never reaches the
registry. Rows ratified before the column existed were backfilled by
`p8d4f1b6e3a9` (alembic/AGENTS.md). A proposal ratified with no captured text
(for instance by the legacy dashboard, which sets the status directly) cannot
be registered (409).

Legacy proposals (`proposer_member_id` NULL) are steward-managed and their
`proposer` is free text, so `can_confirm_ratification` also refuses the steward
whose display name equals that text (`policy.is_legacy_proposer_named`, trimmed,
case-insensitive). The name is only ever an extra refusal: a matching name never
grants management or anything else (display names are self-editable).

### Ratified is not registered

Ratification mints the decision record; it does not touch the registry. A
steward's "Register as agreement" does: with `amends_agreement_id` it snapshots
the agreement, replaces its text with the proposal's `ratified_text`, bumps
the version (members' consent is bound to the version, so they re-attest) and
writes an `AmendmentRecord` (`amendment_type` "proposal", `status`
"ratified"); without one it creates an `active` agreement from the proposal
(type mapped from the proposal type, the effective ACT policy copied, no
participation scopes). Either way an `AgreementCeremony` (outcome
"registered") names the proposal and `proposals.registered_agreement_id`
links them. The proposal row (and an amended agreement) is read `FOR UPDATE`
before the "already registered" check, so two stewards pressing Register at
once produce one agreement and a 409. Agreement detail adds `caller_can_propose_change` for in-force
agreements; the page opens a proposal pre-filled to amend it.

`PUT /agreements/:id` bumps the version only when `title` or `text` changes
(`VERSIONED_FIELDS`): a review-date edit used to void every attestation.
`agreements.record_member_consent` is the one consent write (row, alignment
ledger, pending-membership activation); REST and MCP `attest_agreement_consent`
both call it, so MCP consent now credits the ledger and refuses outside the
consent-open stages.

### Role grants (owner decision)

`can_assign_role(caller, target, role, *, ecosystem_has_owner, founder_id)`:
only roles below your own rank, only to members below it, only an owner makes
an owner, anyone may step down. The bootstrap (`policy.can_bootstrap_roles`)
belongs to the ecosystem's founder alone, and only while the ecosystem has no
owner: the founder of a new ecosystem is a `user` with the co_creator profile,
so this is how the first owner appears. Founding is recorded as the first
member row (`ecosystems.create_ecosystem` and the chat tool insert it in the
founding transaction); `members._bootstrap_context` reads the oldest row
(`created_at`, then `id`). Before 2026-10-31 any co_creator/builder could
bootstrap, and members chose their own profile, so anyone could make
themselves owner of an ownerless ecosystem.

Profiles that confer administration (`policy.PROFILE_ADMINS`: co_creator,
builder; also honoured by `helpers.require_admin`) are therefore never
self-chosen: `PUT /members/:id` and `POST /members` refuse them unless the row
already holds that profile. `PUT /members/:id/profile-grant` sets any
`MEMBER_PROFILES` value on another member for whoever could make them an admin
(`can_grant_profile` = `can_assign_role(..., "admin")`, so owners, or the
founder before there is one; admins cannot, as they cannot mint admins).

Every role or profile change writes the smallest existing record, a
`MemberStatusTransition` with `trigger` "role_grant" / "profile_grant",
`from_status`/`to_status` "role:<tier>" / "profile:<value>" and the granter's
member id in `actor_member_id` (steward status moves record it too).
`GET /members/:id/profile` returns both kinds as `role_history` (`kind`,
`granted_by` = the granter's CURRENT display name, read from the id: an
editable name stored as text would let anyone rewrite who granted what), with
`caller_assignable_roles` and `caller_grantable_profiles` for the pickers. A
no-op grant writes nothing.

## Legacy dashboard (views/)

The server-rendered `/dashboard/*` and `/ecosystems` pages share the app's
session cookie, so any write they still performed bypassed every rule above
(`/phase` set any status including ratified, consent was recorded under a
form-supplied name, any exit or conflict status could be written). The app is
where governance changes now:

- Every legacy write route (POST/PUT on proposals incl. advice, consent and
  phase; agreements; conflicts; exit; members incl. status and onboarding;
  onboarding ceremony; domains; ecosystems; safeguards audits; emergency)
  answers 410 through `views/_rendering.retired_write`, changes nothing, and
  links the matching app page (`FRONTEND_URL` + path). The inventory is the
  `RETIRED` table in `tests/test_legacy_dashboard.py`; a test fails when a
  legacy blueprint registers a write route that is not in it. The chat
  housekeeping routes (`/chat/conversations` rename and archive) stay.
- Legacy reads of conflict cases apply `policy.can_view_conflict` exactly like
  `GET /api/v1/conflicts`: a non-reader gets 404 on the detail page and never
  sees the case in the list or the htmx filter fragment.
- The legacy chat (`views/chat.py`) runs tools through `run_legacy_tool`,
  which passes `confirmed_keys=frozenset()`: it does not track which act the
  member confirmed in an earlier turn, so the model's `confirmed: true` is
  never trusted and the irreversible acts (`CONFIRMATION_TOOLS`) cannot happen
  there; the tool result tells the model to send the member to the app's
  assistant.

## Next steps (G-Next)

One source for "what is waiting for me" and "what happens next here":
`services/next_steps.py` (rules and rationale: `services/AGENTS.md` "Next
steps"). Blueprint `api/next_steps.py`, no prefix:

| Route | Shape |
|---|---|
| `GET /api/v1/me/next-steps` | `{items: [{uid, kind, id, key, title, ecosystem_id, ecosystem, action, what, why, due, overdue, link}], count}`; every ecosystem the caller is active in; overdue first, then by `due` |
| `GET /api/v1/explain/<kind>/<id>` | `{kind, id, key, title, ecosystem, status, state, next_step, decided_by, due, due_label, overdue, your_moves: [{move, label, ready, blocked}], waiting_on_you: [items], link}` for `kind` in proposal, agreement, conflict, emergency, exit (anything else 400 with `allowed`) |

`/explain` loads the record with its detail page's own rule, so it 404s exactly
where the page does: proposals and emergencies `get_scoped_or_404`; agreements
the consent-gate scope (rule 5 exemption); conflicts
`conflicts.load_visible_case` (`can_view_conflict`, same body as a missing
case); exits `exit.load_visible_exit` (in scope, or the leaver's own after
they left). `your_moves` is the engine's list for the caller
(`proposal_next_moves`, ceremony targets, `CONFLICT_MOVES`, the emergency
`caller_flags`, `exit.allowed_next`); `tests/test_g_next.py` checks that each
listed move is accepted by the REST route and an unlisted one is refused.

MCP parity: `record_agreement_ceremony`, `attest_agreement_consent` and
`transition_agreement` take `confirm`; an act that would put an agreement in
force (directly, or through the automatic cascade:
`governance_tools.agreement_act_puts_in_force`, a dry run of the lifecycle with
the gates as they would be after the write), or a sunset or archive ceremony,
returns `needs_confirmation` and writes nothing until `confirm=true`. Refusals
come first. `record_agreement_ceremony` now refuses evidence for a stage the
agreement is not in, as REST and the chat tool do (out-of-stage test evidence
could carry a later consent straight into force).
