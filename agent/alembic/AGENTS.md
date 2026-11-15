# alembic - schema migrations

## b8d3f1a6c4e2: ecosystem cross-link admins

Follows `z6f0c4e8b2d5`. Creates `ecosystem_admins` when the table is missing
(fresh `create_all` databases already have it). For each ecosystem, if an
active non-disabled member is an `owner`, else a `co_creator`, else a root
domain steward (else any active domain steward), the revision inserts that
member's `internal` and `external` links when those exact rows are absent.
It does not update members, drop columns, or replace an existing link. A
second upgrade inserts nothing. Downgrade drops only `ecosystem_admins`;
the `ecosystem_admin` transition rows stay. `tests/test_ecosystem_admins.py`
covers the backfill on SQLite and, when configured, disposable PostgreSQL.

## x4d8a2c6f0b3: configured join quizzes

Follows `w3c7f1a9d5e2`; the orientation/matching migration `y5e9b3d7a1c4` follows this revision.
Adds nullable `quizzes.team_id` with an index (and PostgreSQL foreign key) and nullable
`quiz_results.graded_fingerprint`, plus server-owned `quiz_results.completion_verified` defaulting false.
Existing memberships, attempts, and assignments remain unchanged; legacy results receive no verified-completion flag.
Historical attempts receive no fabricated grading provenance. Fresh metadata carries the same columns.
The migration is additive and tolerates columns already present after `create_all`; no production data
backfill or automatic loss of active memberships occurs. `test_join_quiz_gates.py` covers migration
preservation and repeat-upgrade behavior; run tests only in the coordinated end-of-batch sweep.

## Fresh databases

The revision history was written against databases that `main.init_db`
had already built with `Base.metadata.create_all`: early revisions alter
tables no revision creates (`005` -> `conflict_cases`, `006` ->
`members.username`, `002` -> `governance_health_audits`, `g8c5` ->
`shares_needs`, `h9d6` -> `collaborations`) and `009` declares a `CHAR(32)`
foreign key to the UUID `ecosystems.id`. Replaying it on an empty database
fails at the first of these.

So `env.py` treats one case specially: **`upgrade head` on a database with
no tables** builds the schema from the models (importing
`neos_agent.db.course_models` first, exactly like `init_db`) and stamps
head. The models are the source of truth for a fresh schema; the revisions
are the source of truth for moving an existing one. Every other command
(upgrades of non-empty databases, `upgrade <rev>`, downgrades, `current`,
`history`) takes the normal path.

A database built by `create_all` outside Alembic (no `alembic_version`,
tables present) is not empty: stamp it once (`alembic stamp head`) before
its first upgrade.

## Writing a revision

Chain on the single current head (`alembic heads`). Because live databases
may have been created by `create_all`, inspect before adding or altering
(`sa.inspect(bind).get_columns(...)`) so the revision is safe on both kinds.

## Parallel work: reserve revisions in a chain

When several lanes need schema changes at once, the coordinator creates
empty skeleton revisions first, chained one after another (A revises the
head, B revises A), and each lane fills in only its own `upgrade()`.
Two lanes each revising the current head would leave two heads, and
`upgrade head` (and the fresh-database check in `env.py`) needs exactly one.

## Data revisions

A revision that rewrites rows (not only DDL) still runs on both kinds of
database: check the table exists (`sa.inspect(bind).get_table_names()`),
keep the SQL portable (correlated subqueries, `lower`/`trim`) or do the
grouping in Python over `sa.table(...)` columns, and test it on SQLite and on
a disposable PostgreSQL (`NEOS_TEST_POSTGRES_URL`, see
`tests/test_uxqa_p1_migration.py`). Say in the docstring when the downgrade
cannot restore the data.

### o7c3e9a5d2f8: member-row re-keying

`user_journey_progress` and `ethos_user_access` rows written for the caller's
default member row move to the same user's member row in the row's own
ecosystem (the row `guards.caller_in` returns). No member row there: the row
is untouched. A target row that already holds rows forms a group with them
(every row of that user for that ecosystem); the group keeps one row, on the
target row, and the rest is deleted. Only groups with at least one mis-keyed
row are touched.

Which row is kept (highest first, compared in this order):

| Table | Rank |
|---|---|
| progress | status `complete` > `in_progress` > `opted_out` > anything else; more `completed_steps`; higher `current_step`; later `updated_at`; already on the target row; lowest id |
| access | `role_in_ethos` `steward` > `member` > `observer` > anything else; `access_level` on the same scale; already on the target row; earliest `granted_at` |

Why: the readers key on (target row, ecosystem) and take one row, so two rows
there would be read arbitrarily. A duplicate is the same person's record in
the same ecosystem, so the less advanced one carries nothing a reader would
show. Progress keeps the furthest journey (a later restart elsewhere must not
undo a completion); access keeps the strongest grant, and an admin's grant on
the right row beats an equal self-consent on the wrong one. A self-granted
row (`granted_by` = its old member id) is re-pointed to the new member id.
The same revision rewrites `consent_participants.position` `objection` (any
case, surrounding spaces) to `object`. The downgrade is a no-op.

### p8d4f1b6e3a9: ACT integrity columns (G-ACT)

Adds `consent_participants.member_id`, `advice_entries.member_id`,
`test_reports.reporter_member_id`, `member_status_transitions.actor_member_id`
(each `SET NULL` on member delete), `proposals.amends_agreement_id`,
`proposals.registered_agreement_id` and the text column
`proposals.ratified_text`. The
member columns let a member hold exactly one consent position (changing it
replaces the row) and name the reporter of each test report; the proposal
columns link a proposal to the in-force agreement it changes and to the
agreement a steward registered it as (`api/AGENTS.md` "Ratified is not
registered").

Each column is added only when the table lacks it (`create_all` databases
already have them). SQLite gets the bare column (it cannot add a constraint to
an existing table); PostgreSQL also gets the foreign key.

Backfill (both kinds of database): a `consent_participants` row with NULL
`member_id` gets the member whose display name matches its `name`
(case-insensitive, trimmed) only when exactly one member of the proposal's
ecosystem has that name. Ambiguous, unknown and blank names stay NULL. Why:
at runtime a position is owned ONLY by `member_id`
(`act_gates._members_rows`); display names are self-editable, so matching by
name would let a member rename themselves and change or withdraw someone
else's legacy position (lift their objection). An unowned row is read-only
history: it still counts in the consent gate exactly as stored, and nobody can
change or withdraw it. A member who owned two pre-dedupe rows in one record
(an objection, then a consent) gets both; their next change keeps the newest
row and marks the older ones `withdrawn`. `advice_entries.member_id` gets the
same unique-name rule on `advisor` (via `advice_logs.proposal_id`), because
the portable record and the assistant's standing now match advice by member
id only, so unlinked legacy advice would be left out of a member's record;
ambiguous or unmatched advice stays NULL, read-only history like an unowned
position. Both use `_backfill_members_sql`. `test_reports.reporter_member_id`
is not backfilled: nothing matches reports by name or owns them.
`actor_member_id` (who granted a role or profile, who moved
a status; `api/AGENTS.md` "Role grants") is not backfilled either: role-grant
records first appear in this same wave, and older status rows name nobody.

`ratified_text` is the text a steward confirmed at ratification; registering
an agreement copies it, never the live `proposed_change` (`api/AGENTS.md` "The
text members decide on"). Before this wave the author could edit a proposal at
any stage, so for proposals already `ratified` the backfill first recovers the
text from the decision record minted at ratification, whose `holding` is
`<title> — ratified after completing the ACT process. <proposed_change>`
(`act_gates.record_proposal_decision`): when the holding starts with the
proposal's current title plus that phrase, the rest is the ratified text.
Otherwise (no decision record, title edited since, an older holding format)
it falls back to the trimmed live `proposed_change`, the best evidence left.
Both statements are portable (`substr`, `length`, `||`, `nullif`) and only
fill NULLs, so a rerun and a create_all database are safe. Proposals in any
other status stay NULL. The downgrade drops the columns, backfilled values
included.
The `objection` -> `object` rewrite the governance plan mentions already ran
in `o7c3e9a5d2f8`.

### q2a7c5e9d1b3: emergency co-signing (G-Safety)

Widens the state CHECK to pending/withdrawn, adds the co-signer columns, then
adds `uq_emergency_states_one_live`: a partial unique index on
`emergency_states(ecosystem_id)` where `state IN ('pending', 'open',
'half_open')` (PostgreSQL and SQLite both take `*_where`; the model declares
it too, so `create_all` databases already have it and the step is skipped by
name). It is what stops two concurrent declarations: `declare()` can only lock
rows that exist, so two first declarations would otherwise both insert.

Before creating it, duplicate live rows are retired, because the old
dashboard never refused a second declaration. Per ecosystem one row stays
live, chosen by `KEEP_ORDER`: `open` (authority in effect) over `half_open`
(Recovery) over `pending`, then the latest `declared_at`, then `created_at`,
then id. The others become `closed` (or `withdrawn` if pending) with
`closed_at` set and an `actions_log` entry `superseded` naming the row that
stays live. Closing a duplicate skips its Recovery review; the kept row
carries the ecosystem's live state, and the log entry leaves a trail for a
steward to follow up. Idempotent: with the index in place the step is
skipped. The downgrade drops the index (and, as before, closes pending and
withdrawn rows).

### r6c1e8a4f2d7: conflict care

Schedules 30/60/90-day check-ins for active repairs without dates, clears the
"AI analysis pending" placeholder on draft audits, adds `ix_conflict_cases_reporter_id`.
Check-ins count from the repair's creation date, unless its 30-day check-in
would already be past: then from the migration date (+30/60/90), so years of
unscheduled repairs do not all show overdue on the first page load.
Legacy statuses become stages of `api/conflicts.CONFLICT_MOVES`
(`LEGACY_CONFLICT_STAGES`): `open` (the old dashboard's "new case", written
by anyone, never triaged) -> `reported`; `in_mediation` and `escalated` (the
demo seed and the old dashboard's "escalate to next tier", both mid-process)
-> `in_progress`. Any other unknown status is left for a steward: the API
shows it as "Needs a steward to review" and lets triage move it to any stage.
It also rewrites legacy free-text `conflict_cases.parties` (a list of names or a dict of
role -> name) into `{"member_ids": [...], "labels": [...]}`. A name becomes a member id only when
exactly one member of the case's ecosystem has that display name (compared case-insensitively,
trimmed); an ambiguous or unknown name stays in `labels`, which never authorizes access. Only
`member_ids` grants party access (display names are user-editable). Rows already holding
`member_ids` are left alone. The downgrade does not restore the old shape.


### u7d2f4b8a3c6: maintenance and health (G-Maint)

Adds `governance_health_audits.self_assessment` (boolean, server default false) when missing: an
audit a steward recorded of their own ecosystem because no member who is not a steward could
(`api/AGENTS.md` "Maintenance and health (G-Maint)"). Frozen indicator values and review findings
need no column: they live in the existing JSON (`indicator_scores`, `review_records.evaluation`).

Data, only NULLs filled (a rerun and a create_all database are safe), in Python over `sa.table`
columns:
- An agreement in force (`active`, `under_review`) with no review date gets the per-type interval
  (a frozen copy of `REVIEW_INTERVAL_MONTHS`) from its ratification date, else its creation. When
  that date is already past, the first review is due 30 days after the migration, so years of
  undated agreements do not all show overdue on the first page load (the r6c1e8a4f2d7 rule).
- An agreement in `sunset` with no sunset date gets 60 days (the framework's notice) after its
  latest sunset ceremony, else after its last update, else after the migration date; archiving is
  offered after it.

The four study agreements stuck under review need no special case: they can now be finished with
findings. The downgrade drops the column; the filled dates stay (they cannot be told apart from set
ones). `tests/test_g_health_migration.py` runs it on SQLite and on a disposable PostgreSQL.

### v1b4e7c9d2f5: platform home pin (G-Authority)

The platform home (whose co_creator/builder rows are platform admins) is an id, never a name: at
request time `PLATFORM_HOME_ECOSYSTEM_ID`, else the `app_settings` row `platform_home_ecosystem_id` =
`{"ecosystem_id": "<uuid>"}`, else nobody (`api/AGENTS.md` "Platform admin (G-Authority)"). This
revision writes that row once, resolving the home the way sign-up placement did: the
`SIGNUP_DEFAULT_ECOSYSTEM_SLUG` environment variable (an id or a name slug), else "omnione"; the oldest
match (`created_at`, `founded_date` nulls last, `id`; the ordering is done in Python, so it is the same
on both databases). Why at migration time: production runs `alembic upgrade head` on deploy while the
seeded OmniOne still carries its name, so the pin lands on the real one before a rename (or a later
ecosystem named "omnione") could matter. No match: no row (fail closed). A row already present is never
touched, so a re-run, or an operator's own pin, survives. Fresh `create_all` + stamp databases skip the
revision; the server pins the OmniOne it founds on an empty database (`main.init_db`), and any other
fresh environment sets `PLATFORM_HOME_ECOSYSTEM_ID`. The downgrade deletes the row whatever it holds.
`tests/test_platform_admin_migration.py` runs it on SQLite and on a disposable PostgreSQL.


### s3e8b1d7c4a2: exchange integrity (G-Exchange)

Adds `shares_needs.status_reason`, `status_changed_by_member_id`, `status_changed_at`, `fulfilled_by_member_id`,
`hidden_at`, `hidden_by_member_id`, `hidden_reason` and `collaborations.proposed_by_member_id`,
`ended_by_member_id`, `end_reason`, `ended_at`, plus the last recorded review `reviewed_by_member_id`, `review_note`,
`reviewed_at` (FX-Exchange amendment before any deploy) (member columns `SET NULL`; SQLite the bare column, PostgreSQL also
the foreign key; each only when missing). Why: who moved a post and why, whom a fulfilled post names, a
restorable hide, who proposed and who ended a collaboration (services/AGENTS.md "Exchange (G-Exchange)").

Data, on both kinds of database (typed `sa.table` statements, no dialect SQL):

| Rows | Becomes | Why |
|---|---|---|
| `category` blank | NULL | an empty category matched no filter |
| `category` in the vocabulary up to case and spaces | the vocabulary value | the filters compare exactly |
| `category` `skill` / `resource` | `skills` / `resources` | DomainDetail sent the singulars (D11) |
| `visibility` `private` | `domain` | `private` is retired; `domain` is its narrowest successor |
| active, no author | withdrawn, "No author on record (legacy post)" | nobody can answer it (there is no one to message) |
| active, author `exited` | withdrawn, "author left" | what `api/exit.py` now does at exit |
| active collaboration, no review date | `started_date` (else the created date) + 365 days; already past: the migration date + 30 days (`FIRST_REVIEW_GRACE_DAYS`, as u7d2f4b8a3c6 for agreements) | activation now sets one; the grace keeps every year-old collaboration from being due the day it deploys (wave-c A10) |

Other free-text categories are left as they are (the server refuses new ones). The downgrade drops the columns;
the data rewrites are not restored. `proposed_by_member_id` is not backfilled (nothing recorded the proposer).
Tested by `tests/test_exchange_migration.py` (SQLite, and PostgreSQL with downgrade and re-upgrade).

### w3c7f1a9d5e2: explicit node support

Follows v1b4e7c9d2f5. Adds global User assignments (`node_admins`), append-only public events (`node_admin_actions`) and append-only private repair archives (`node_admin_snapshots`). Both immutable tables install SQLite/PostgreSQL rejection triggers through model table creation and migration. Adds `users.disabled_at`, proposal support-user/action provenance, and `agent_sessions.owner_user_id`; existing sessions backfill their actual User through Member.user_id. Columns/tables are added only when absent for create_all compatibility.

The migration grants no assignments from historical profiles and never marks an empty node bootstrapped. The server's reviewed explicit `NODE_ADMIN_BOOTSTRAP_USER_IDS` input is the only first-assignment path, with enabled/usable identity checks, serialized all-or-nothing grants, public server-bootstrap events and a sealed completion marker. No production IDs belong in source. See `src/neos_agent/services/NODE_SUPPORT.md`. Tests are authored in `test_node_admin_migration.py` for SQLite and disposable PostgreSQL; the coordinator runs the integrated sweep after all fixes.
