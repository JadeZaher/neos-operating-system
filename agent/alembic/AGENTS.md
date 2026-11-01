# alembic - schema migrations

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
