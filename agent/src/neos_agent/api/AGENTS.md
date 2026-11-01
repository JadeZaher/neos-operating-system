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
consent alone. The advisor name always comes from the caller's member row, never from
the request body.

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
| `record_consent_position` | `can_participate` | participant; `objection` stored as `object`; the gate cascades as in REST |
| `update_proposal_status` | `transition_proposal` (manage rule, table, gate) | actor |
| `create_agreement_draft` | `is_active_member_in` (REST: authorized ids) | proposer text defaults to the caller |
| `update_agreement_status` | `agreements.transition_agreement` (ceremony steward, table, `evidence`, gate) | conductor; the version never changes |
| `create_decision_record` | `can_record_decision` (steward; no REST route, decisions are minted by ACT) | recorder |
| `declare_emergency` | `can_declare_emergency` (any active member, owner decision) | declarer |
| `create_exit_record` | `is_active_member_in`; only one's own exit (`EXIT_SELF_ONLY`) | the leaving member |
| `create_conflict_case`, `triage_conflict`, `create_repair_agreement`, `create_safeguard_audit` | `is_active_member_in` the record's ecosystem (as REST) | reporter / auditor |
| `create_domain_draft` | `is_steward_in` (REST `require_ecosystem_role` mod) | `created_by` |
| `create_ecosystem` | signed in (as REST) | founder joins as an active `co_creator` and stewards a core domain |

Proposal tools accept the page's UUID as well as the `PROP-` key.

`update_agreement_status` used to keep its own table (`consent -> active`),
skip the gates and evidence, and bump the version on advice, consent and
active. The bump silently voided every member's consent, which is bound to
`agreement.version`; it now calls the REST/MCP engine, so a ceremony records
its `AgreementCeremony`, snapshots an `AgreementVersion`, and activation mints
the commitment artifact. Deliberately unchanged here, for the governance wave
(`uxqa/governance/review-core.md`): REST consent positions are not
de-duplicated; an objection cannot be lifted; one passed test report ratifies. REST `POST /emergency/declare` still has no
membership check (`emergency.py`, another lane); `can_declare_emergency` is
the predicate to adopt there, and the co-signer joins it.

## ACT parity

One script of ACT moves runs through REST, MCP and chat in
`tests/test_uxqa_p1_mcp_parity.py`; every surface must refuse and allow the
same moves and leave the same status.

| Move | REST | MCP | Chat |
|---|---|---|---|
| open draft -> advice | `POST /proposals/:id/status` | `transition_proposal` | `update_proposal_status` |
| forward move with unmet gate | 409 + `gates` | `ValueError` with gates | refusal text |
| advice | `POST /advice` (author refused) | `record_proposal_advice` | `record_advice` |
| consent position | `POST /consent` (caller, body name ignored) | `submit_proposal_consent` | `record_consent_position` |
| test report | `POST /test` | `submit_test_report` | none yet |
| withdraw | manage rule | manage rule | manage rule |
| agreement ceremony | `POST /agreements/:id/status` | `transition_agreement` | `update_agreement_status` (with `evidence`) |
| agreement round / evidence | `POST /agreements/:id/ceremonies` | `record_agreement_ceremony` | none yet |

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

