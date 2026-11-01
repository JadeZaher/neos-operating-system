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
