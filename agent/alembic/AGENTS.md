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
