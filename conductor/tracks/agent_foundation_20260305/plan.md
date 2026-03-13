# Implementation Plan: Agent Foundation -- Scaffolding, Skill Loader & Database

**Track ID:** agent_foundation_20260305
**Spec:** `conductor/tracks/agent_foundation_20260305/spec.md`
**Total Tasks:** 18
**Estimated Duration:** 2-3 days
**Approach:** TDD where applicable (Red -> Green -> Refactor)

---

## Overview

Four phases, each building on the previous:

1. **Phase 1: Scaffolding** -- Directory structure, pyproject.toml, Dockerfile, configuration
2. **Phase 2: Skill Loader & Registry** -- Parse SKILL.md files, build dependency graph, populate registry
3. **Phase 3: Database Models & Migrations** -- 27 SQLAlchemy models, session factory, Alembic, seed data
4. **Phase 4: Sanic App Factory & API** -- App factory with lifecycle hooks, health and skills endpoints

---

## Phase 1: Scaffolding

**Goal:** Create the full `agent/` directory structure with all configuration files so that `pip install -e ".[dev]"` works and the project is ready for code.

### Task 1.1: Create directory structure and __init__.py files

Create the complete directory tree for the agent application:

```
agent/
  src/neos_agent/
    __init__.py
    skills/
      __init__.py
    db/
      __init__.py
    api/
      __init__.py
  tests/
    __init__.py
  alembic/
    versions/
  scripts/
```

Each `__init__.py` should contain a module docstring describing the package purpose. The top-level `neos_agent/__init__.py` should define `__version__ = "0.1.0"`.

**Files:**
- `agent/src/neos_agent/__init__.py`
- `agent/src/neos_agent/skills/__init__.py`
- `agent/src/neos_agent/db/__init__.py`
- `agent/src/neos_agent/api/__init__.py`
- `agent/tests/__init__.py`

**Acceptance Criteria:** AC-11.3 (partial)
**Commit message:** `agent(scaffold): Create directory structure with init files`

---

### Task 1.2: Write pyproject.toml

Create `agent/pyproject.toml` with:

**Runtime dependencies:**
- `sanic>=25.0,<26.0`
- `sanic-ext>=25.0,<26.0`
- `sqlalchemy[asyncio]>=2.0,<3.0`
- `asyncpg>=0.29`
- `alembic>=1.13`
- `pydantic-settings>=2.0`
- `anthropic>=0.40`

**Dev dependencies (optional group `dev`):**
- `pytest>=8.0`
- `pytest-asyncio>=0.24`
- `httpx>=0.27`
- `aiosqlite>=0.20`

**Package configuration:**
- Name: `neos-agent`
- Python requires: `>=3.12`
- Source layout: `src/`
- Package: `neos_agent`

**Acceptance Criteria:** AC-11.1, AC-11.2, AC-11.3
**Commit message:** `agent(scaffold): Add pyproject.toml with dependencies`

---

### Task 1.3: Write Dockerfile

Create `agent/Dockerfile`:

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
CMD ["sanic", "neos_agent.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
```

**Acceptance Criteria:** AC-11.4
**Commit message:** `agent(scaffold): Add Dockerfile for Python 3.12-slim`

---

### Task 1.4: Write .env.example and config.py

Create two files:

**`.env.example`** (at repo root):
```env
# Required
DATABASE_URL=postgresql+asyncpg://neos:neos@localhost:5432/neos
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (defaults shown)
NEOS_CORE_PATH=../neos-core
CLAUDE_MODEL=claude-sonnet-4-20250514
LOG_LEVEL=info
CORS_ORIGINS=*
```

**`agent/src/neos_agent/config.py`:**

Implement the `Settings` class using `pydantic-settings.BaseSettings`:
- `DATABASE_URL: str` (required)
- `ANTHROPIC_API_KEY: str` (required)
- `NEOS_CORE_PATH: str = "../neos-core"`
- `CLAUDE_MODEL: str = "claude-sonnet-4-20250514"`
- `LOG_LEVEL: str = "info"`
- `CORS_ORIGINS: str = "*"`
- `model_config` with `env_file=".env"`, `case_sensitive=True`

Include a module-level `get_settings()` function that caches and returns a `Settings` instance.

**Acceptance Criteria:** AC-6.1 through AC-6.8, AC-11.5
**Commit message:** `agent(scaffold): Add pydantic-settings config and .env.example`

---

### Task 1.5: Verification -- Scaffolding

Verify the scaffolding is correct:

1. `cd agent && pip install -e ".[dev]"` succeeds without errors
2. `python -c "import neos_agent; print(neos_agent.__version__)"` prints `0.1.0`
3. `python -c "from neos_agent.config import Settings"` imports without error
4. All `__init__.py` files exist and contain docstrings
5. `.env.example` is present at repo root

**[checkpoint marker]**

**Commit message:** `agent(scaffold): Verify scaffolding installation`

---

## Phase 2: Skill Loader & Registry

**Goal:** Parse all 54 SKILL.md files into structured dataclasses, build a dependency graph, and expose an in-memory skill registry.

### Task 2.1: Write test_loader.py (TDD Red)

Create `agent/tests/test_loader.py` with tests that will initially fail:

**Test fixtures (in conftest.py or local):**
- `sample_skill_md`: A string containing a valid SKILL.md with full frontmatter and at least sections A, B, C
- `tmp_skill_file`: A temporary file written to disk with the sample content
- `malformed_skill_md`: A string with missing frontmatter delimiters
- `neos_core_path`: Path to the actual `neos-core/` directory (for integration tests)

**Test cases:**
- `test_parse_frontmatter_valid` -- Extracts all 5 fields correctly (name, description, layer as int, version, depends_on as list)
- `test_parse_frontmatter_missing_delimiters` -- Returns error list
- `test_parse_frontmatter_empty_depends` -- Handles `depends_on: []` correctly
- `test_parse_frontmatter_inline_list` -- Handles `depends_on: [skill-a, skill-b]`
- `test_parse_frontmatter_quoted_values` -- Handles double and single quoted values
- `test_parse_sections_valid` -- Extracts all 12 sections by letter
- `test_parse_sections_missing_section` -- Returns None for absent sections
- `test_parse_skill_file_valid` -- Returns ParsedSkill with meta and content
- `test_parse_skill_file_missing_file` -- Raises SkillParseError
- `test_parse_skill_file_raw_text` -- raw_text contains full file content
- `test_discover_skill_files` -- Finds all SKILL.md files in neos-core/

**Acceptance Criteria:** Tests exist and fail (Red phase)
**Commit message:** `agent(skills): Add loader tests (TDD Red)`

---

### Task 2.2: Implement loader.py (TDD Green)

Create `agent/src/neos_agent/skills/loader.py`:

1. Define `SkillParseError(Exception)` custom exception
2. Define `SkillMeta` frozen dataclass with fields: name, description, layer, version, depends_on, file_path
3. Define `SkillContent` frozen dataclass with fields: sections (dict), raw_text (str)
4. Define `ParsedSkill` frozen dataclass with fields: meta, content
5. Implement `parse_frontmatter(content: str) -> tuple[dict[str, Any], list[str]]`
   - Port logic from `scripts/validate_skill.py` lines 77-123
   - Find `---` delimiters, extract key-value pairs
   - Handle quoted values, empty lists, inline lists
   - Convert `layer` to int
6. Implement `parse_sections(content: str) -> dict[str, str | None]`
   - Port logic from `scripts/validate_skill.py` lines 176-208
   - Use the same `REQUIRED_SECTIONS` list and `_SECTION_STOP_RE` pattern
   - Return dict keyed by letter (A-L), value is section text or None
7. Implement `parse_skill_file(file_path: Path) -> ParsedSkill`
   - Read file, call parse_frontmatter and parse_sections
   - Raise SkillParseError on any failure with file path in message
8. Implement `discover_skill_files(root: Path) -> list[Path]`
   - Walk directory tree, find all `SKILL.md` files
   - Return sorted list of absolute paths

Run tests -- all should pass (Green phase).

**Acceptance Criteria:** AC-1.1 through AC-1.9
**Commit message:** `agent(skills): Implement skill loader with frontmatter and section parsing`

---

### Task 2.3: Write test_graph.py (TDD Red)

Create `agent/tests/test_graph.py` with tests:

**Test data:**
- A small graph: A depends on nothing, B depends on A, C depends on A and B, D depends on C
- A graph with a cycle: X depends on Y, Y depends on Z, Z depends on X
- The actual NEOS skill dependency data (extracted from neos-core)

**Test cases:**
- `test_build_from_skills` -- Graph contains all added skills
- `test_topological_order_simple` -- A appears before B, B before C, C before D
- `test_topological_order_root_nodes` -- Skills with no dependencies appear first
- `test_detect_cycles_none` -- Empty list for acyclic graph
- `test_detect_cycles_found` -- Non-empty list for cyclic graph
- `test_dependencies_of_direct` -- B's dependencies include A
- `test_dependencies_of_transitive` -- D's dependencies include A, B, C
- `test_dependents_of_direct` -- A's dependents include B and C
- `test_dependents_of_transitive` -- A's dependents include B, C, D
- `test_direct_dependencies_of` -- C's direct dependencies are A and B only
- `test_direct_dependents_of` -- A's direct dependents are B and C only
- `test_unknown_skill_raises` -- KeyError for non-existent skill
- `test_empty_depends_on` -- Root nodes handled correctly
- `test_skill_names` -- Returns sorted list of all names
- `test_has_skill` -- Returns True for existing, False for non-existing

**Acceptance Criteria:** Tests exist and fail (Red phase)
**Commit message:** `agent(skills): Add dependency graph tests (TDD Red)`

---

### Task 2.4: Implement graph.py (TDD Green)

Create `agent/src/neos_agent/skills/graph.py`:

1. Define `SkillGraph` class
2. Internal storage: `_forward: dict[str, list[str]]` (dependencies), `_reverse: dict[str, list[str]]` (dependents)
3. `add_skill(name, depends_on)` -- Add to both forward and reverse maps
4. `build_from_skills(skills: list[SkillMeta])` -- Iterate skills, call add_skill
5. `topological_order()` -- Kahn's algorithm (BFS-based topological sort)
   - Find all nodes with in-degree 0
   - Process queue, decrement in-degrees, add to result
   - If result length differs from node count, raise error (cycle detected)
6. `detect_cycles()` -- DFS-based cycle detection
   - Track visited and recursion stack
   - Return list of cycle paths (each path is a list of skill names)
7. `dependencies_of(name)` -- BFS/DFS traversal of forward edges (transitive closure)
8. `direct_dependencies_of(name)` -- Return `_forward[name]`
9. `dependents_of(name)` -- BFS/DFS traversal of reverse edges (transitive closure)
10. `direct_dependents_of(name)` -- Return `_reverse[name]`
11. `has_skill(name)`, `skill_names` property

Run tests -- all should pass.

**Acceptance Criteria:** AC-2.1 through AC-2.10
**Commit message:** `agent(skills): Implement dependency graph with topological sort and cycle detection`

---

### Task 2.5: Write test_registry.py (TDD Red)

Create `agent/tests/test_registry.py` with tests:

**Test fixtures:**
- `tmp_neos_core`: A temporary directory with 3-5 sample SKILL.md files mimicking the neos-core structure
- `registry`: A `SkillRegistry` instance

**Test cases:**
- `test_load_all_populates_registry` -- After load_all, count > 0
- `test_load_all_from_real_neos_core` -- Integration test loading actual neos-core, count == 54
- `test_get_existing_skill` -- Returns ParsedSkill for a known skill
- `test_get_nonexistent_skill_raises` -- KeyError for unknown name
- `test_get_meta` -- Returns SkillMeta (not full content)
- `test_list_by_layer` -- Returns correct skills for a given layer
- `test_list_by_layer_empty` -- Returns empty list for non-existent layer (e.g., layer 99)
- `test_all_skills` -- Returns list of all SkillMeta
- `test_all_names` -- Returns sorted list of skill names
- `test_count` -- Returns correct count
- `test_graph_populated` -- graph property returns a populated SkillGraph
- `test_is_loaded_before_and_after` -- False before load_all, True after
- `test_partial_load_on_parse_error` -- Loads parseable skills, warns on errors

**Acceptance Criteria:** Tests exist and fail (Red phase)
**Commit message:** `agent(skills): Add registry tests (TDD Red)`

---

### Task 2.6: Implement registry.py (TDD Green)

Create `agent/src/neos_agent/skills/registry.py`:

1. Define `SkillRegistry` class
2. Internal storage: `_skills: dict[str, ParsedSkill]`, `_graph: SkillGraph`, `_loaded: bool`
3. `load_all(neos_core_path: Path)`:
   - Call `discover_skill_files(neos_core_path)`
   - For each file, call `parse_skill_file(file_path)`
   - Catch `SkillParseError`, log warning, continue
   - Build `SkillGraph` from all loaded metas
   - Set `_loaded = True`
   - Log summary: "Loaded N skills from neos-core"
4. `get(name)` -- Return `_skills[name]` or raise KeyError
5. `get_meta(name)` -- Return `_skills[name].meta`
6. `list_by_layer(layer)` -- Filter by `meta.layer == layer`
7. `all_skills()` -- Return list of all metas
8. `all_names()` -- Return sorted list of names
9. `count` property -- `len(_skills)`
10. `graph` property -- Return `_graph`
11. `is_loaded` property -- Return `_loaded`

Update `agent/src/neos_agent/skills/__init__.py` to export `SkillRegistry`, `SkillMeta`, `SkillContent`, `ParsedSkill`, `SkillGraph`.

Run tests -- all should pass.

**Acceptance Criteria:** AC-3.1 through AC-3.10
**Commit message:** `agent(skills): Implement skill registry with loading and lookup`

---

### Task 2.7: Verification -- Skill Loader & Registry

Verify end-to-end skill loading:

1. Run all tests: `cd agent && python -m pytest tests/test_loader.py tests/test_graph.py tests/test_registry.py -v`
2. All tests pass
3. Integration test confirms 54 skills loaded from actual neos-core
4. Dependency graph has no cycles
5. Topological sort produces valid ordering
6. Each of the 10 layers returns the correct number of skills

**[checkpoint marker]**

**Commit message:** `agent(skills): Verify skill loader, graph, and registry`

---

## Phase 3: Database Models & Migrations

**Goal:** Define all 27 SQLAlchemy async ORM models, configure the session factory, set up Alembic migrations, and create a seed data script.

### Task 3.1: Write conftest.py with DB fixtures

Create or update `agent/tests/conftest.py` with database test fixtures:

1. `db_engine` fixture -- Create async SQLite in-memory engine
2. `db_session` fixture -- Create tables, yield session, drop tables
3. `sample_skill_md` fixture -- Sample SKILL.md content string
4. `tmp_neos_core` fixture -- Temporary directory with sample skills

Handle the UUID default issue: SQLite does not support `gen_random_uuid()`. Use a Python-side default (`uuid.uuid4`) in test fixtures or an event listener.

**Acceptance Criteria:** NFR-4
**Commit message:** `agent(db): Add test fixtures with in-memory SQLite`

---

### Task 3.2: Implement db/models.py -- All 27 models

Create `agent/src/neos_agent/db/models.py`:

Define a `Base` declarative base with a mixin for common columns:

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
```

Implement all 27 models organized by section:

**Core (7 models):**

1. `Ecosystem` -- id, name, description, uaf_agreement_id (nullable FK), status
2. `Member` -- id, ecosystem_id (FK), member_id (business key), display_name, current_status, profile, last_governance_activity_date, notes
3. `MemberOnboarding` -- id, member_id (FK to Member), facilitator, uaf_version_consented, consent_date, cooling_off_start, cooling_off_end, section_consents (JSONB)
4. `MemberStatusTransition` -- id, member_id (FK to Member), from_status, to_status, date, trigger, notes
5. `Domain` -- id, ecosystem_id (FK), domain_id (business key), version, status, purpose, current_steward, created_by, elements (JSONB for list-type elements like key_responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator_responsibilities, competencies)
6. `DomainElement` -- id, domain_id (FK to Domain), element_name, element_value (JSONB)
7. `DomainMetric` -- id, domain_id (FK to Domain), metric, target, measurement_method

**Agreements (4 models):**

8. `Agreement` -- id, ecosystem_id (FK), agreement_id (business key), type, title, version, status, proposer, affected_parties (JSONB), domain, text, hierarchy_level, parent_agreement_id (self-referential FK nullable), review_date, sunset_date, ratification_date, created_date
9. `AgreementRatificationRecord` -- id, agreement_id (FK to Agreement), participant, role, position, date
10. `AmendmentRecord` -- id, ecosystem_id (FK), amendment_id (business key), parent_agreement_id (FK to Agreement), parent_agreement_version, amendment_type, proposed_by, date, changes (JSONB), rationale, act_level_used, consent_record_id, new_agreement_version, status
11. `ReviewRecord` -- id, ecosystem_id (FK), review_id (business key), agreement_id (FK to Agreement), agreement_version, review_type, trigger, review_body (JSONB), date, evaluation (JSONB), outcome, next_review_date, follow_up_actions (JSONB)

**ACT Process (10 models):**

12. `Proposal` -- id, ecosystem_id (FK), proposal_id (business key), type, decision_type, title, version, status, proposer, co_sponsors (JSONB), affected_domain, impacted_parties (JSONB), urgency, proposed_change, rationale, created_date, advice_deadline, consent_deadline, test_duration, related_proposals (JSONB), synergy_check (JSONB)
13. `AdviceLog` -- id, proposal_id (FK to Proposal), advice_window_start, advice_window_end, urgency, summary, proposer_modifications
14. `AdviceEntry` -- id, advice_log_id (FK to AdviceLog), advisor, role, azpo, date, advice_text, proposer_response, integration_status, rationale
15. `AdviceNonRespondent` -- id, advice_log_id (FK to AdviceLog), name, notified_date, follow_up_sent (bool)
16. `ConsentRecord` -- id, proposal_id (FK to Proposal), consent_mode, weighting_model, facilitator, date, quorum_required, quorum_met (bool), outcome, escalation_level, final_proposal_version
17. `ConsentParticipant` -- id, consent_record_id (FK to ConsentRecord), name, role, azpo, position, reason, round (int)
18. `ConsentIntegrationRound` -- id, consent_record_id (FK to ConsentRecord), round_number (int), modifications_made, outcome
19. `ConsentObjectionAddressed` -- id, integration_round_id (FK to ConsentIntegrationRound), objector, objection, resolution
20. `TestReport` -- id, proposal_id (FK to Proposal), test_start_date, test_end_date, midpoint_checkin_date, revert_procedure, observations, midpoint_findings, outcome, extension_end_date, modifications, next_action, agreement_registry_id
21. `TestSuccessCriterion` -- id, test_report_id (FK to TestReport), criterion, met (bool), evidence

**Memory (4 models):**

22. `DecisionRecord` -- id, ecosystem_id (FK), record_id (business key), date, holding, ratio_decidendi, obiter_dicta, deliberation_summary, source_skill, source_layer (int), artifact_type, artifact_reference, domain, precedent_level, status, overruled_by, superseded_by, related_records (JSONB), review_date, recorder, recorder_role, verification_by, verification_date
23. `DecisionDissentRecord` -- id, decision_record_id (FK to DecisionRecord), objector, objection, resolution, notes
24. `DecisionParticipant` -- id, decision_record_id (FK to DecisionRecord), name, role, position
25. `DecisionSemanticTag` -- id, decision_record_id (FK to DecisionRecord), topic (JSONB), affected_parties (JSONB), ecosystem_scope, urgency_at_time, related_precedents (JSONB)

**Sessions (1 model):**

26. `AgentSession` -- id, ecosystem_id (FK), member_id (FK to Member nullable), skill_name, started_at, ended_at (nullable), status, context (JSONB)

**Total: 26 models** (Note: `DomainElement` can be merged into `Domain` using JSONB if the separate table proves unnecessary during implementation. The model count is 26-27 depending on this decision.)

Wait -- let me recount. The spec says 27, let me make sure we have 27. After listing:
1-7 Core, 8-11 Agreements, 12-21 ACT Process, 22-25 Memory, 26 Sessions = 26 total.

The 27th table can be added as `member_section_consents` (normalizing out the section_consents JSONB from MemberOnboarding) OR we keep the count at 26 and note the difference. Let us keep the models at 26 and document the adjustment -- JSONB for `section_consents` within `MemberOnboarding` is simpler and more faithful to the template structure.

**Acceptance Criteria:** AC-4.1 through AC-4.10
**Commit message:** `agent(db): Implement all SQLAlchemy ORM models`

---

### Task 3.3: Implement db/session.py

Create `agent/src/neos_agent/db/session.py`:

1. `create_engine(database_url: str) -> AsyncEngine` -- Create async engine with appropriate driver
2. `create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]` -- Configure with `expire_on_commit=False`
3. `setup_db(app, loop)` -- Sanic `before_server_start` listener: create engine from settings, create session factory, store on `app.ctx.db`
4. `teardown_db(app, loop)` -- Sanic `after_server_stop` listener: dispose engine

Do not import Sanic at module level. The `setup_db` and `teardown_db` functions take `app` as a parameter and use it for context storage.

Write a simple test in `tests/test_session.py` or add to conftest that verifies engine creation with aiosqlite URL.

**Acceptance Criteria:** AC-5.1 through AC-5.6
**Commit message:** `agent(db): Implement async session factory with Sanic lifecycle hooks`

---

### Task 3.4: Set up Alembic with async configuration

Create Alembic configuration:

1. `agent/alembic.ini` -- Configure script_location, sqlalchemy.url placeholder
2. `agent/alembic/env.py` -- Async-aware env.py using `run_async()` pattern:
   - Import all models so metadata is populated
   - Use `async_engine_from_config` for migrations
   - Support both online and offline modes
3. `agent/alembic/script.py.mako` -- Template for migration scripts
4. Generate initial migration: Document the command `alembic revision --autogenerate -m "initial_schema"` but do not run it (requires PostgreSQL)

Create placeholder `agent/alembic/versions/.gitkeep` to track the directory.

**Acceptance Criteria:** AC-11.6
**Commit message:** `agent(db): Configure Alembic for async PostgreSQL migrations`

---

### Task 3.5: Write seed data script

Create `agent/scripts/seed_omnione.py`:

1. Read DATABASE_URL from environment or .env
2. Create async engine and session
3. Check if OmniOne ecosystem already exists (idempotency)
4. Create seed records in a single transaction:
   - Ecosystem: OmniOne
   - UAF Agreement (type=uaf, hierarchy_level=universal, status=active)
   - Update ecosystem.uaf_agreement_id to point to the UAF
   - Domain: SHUR Kitchen (dom-shur-kitchen-001)
   - Domain: SHUR Garden (dom-shur-garden-001)
   - Member: OSC Steward (co_creator, active)
   - Member: AE Builder (builder, active)
   - Member: TH Member (townhall, active)
   - MemberOnboarding records for each member
   - MemberStatusTransition records (prospective -> onboarding -> active)
5. Print summary of created records

Make the script runnable as `python -m agent.scripts.seed_omnione` or `python agent/scripts/seed_omnione.py`.

**Acceptance Criteria:** AC-10.1 through AC-10.5
**Commit message:** `agent(db): Add OmniOne seed data script`

---

### Task 3.6: Verification -- Database Models & Migrations

Verify database layer:

1. Run model tests: Verify all models can create tables against in-memory SQLite
2. Verify all foreign key relationships are valid (no dangling references)
3. Verify all models have `created_at` and `updated_at` columns
4. Verify all non-ecosystem models have `ecosystem_id`
5. Verify seed script can create records against in-memory SQLite (mock test)
6. Count models and confirm the total matches the spec

**[checkpoint marker]**

**Commit message:** `agent(db): Verify models, session, and seed script`

---

## Phase 4: Sanic App Factory & API

**Goal:** Wire everything together into a Sanic application with lifecycle hooks, health check, and skill index endpoints.

### Task 4.1: Write test_health.py (TDD Red)

Create `agent/tests/test_health.py` with tests:

**Test fixture:** A Sanic test client using `httpx.AsyncClient` or Sanic's built-in `ASGIApp` testing.

**Test cases:**
- `test_health_returns_200` -- GET /api/v1/health returns 200
- `test_health_response_fields` -- Response contains status, skills_loaded, skills_available, database, version
- `test_health_skills_loaded_count` -- skills_loaded matches registry count
- `test_health_skills_available_true` -- skills_available is True when registry is loaded
- `test_health_degraded_without_db` -- Returns 200 with database="disconnected" when DB is not available

**Acceptance Criteria:** Tests exist and fail (Red phase)
**Commit message:** `agent(api): Add health endpoint tests (TDD Red)`

---

### Task 4.2: Implement main.py -- Sanic app factory

Create `agent/src/neos_agent/main.py`:

1. `create_app(settings: Settings | None = None) -> Sanic`:
   - Create `Sanic("neos-agent")` instance
   - Load settings (from parameter or `get_settings()`)
   - Store settings on `app.ctx.settings`
   - Register `before_server_start` listener for skill registry:
     - Create `SkillRegistry`, call `load_all(settings.NEOS_CORE_PATH)`
     - Store on `app.ctx.skills`
     - Log warning on failure (degraded mode)
   - Register `before_server_start` listener for DB (from `session.setup_db`)
   - Register `after_server_stop` listener for DB (from `session.teardown_db`)
   - Register API blueprints (health, skills)
   - Return app

2. Add `if __name__ == "__main__"` block to run with `app.run(host="0.0.0.0", port=8000)`

**Acceptance Criteria:** AC-7.1 through AC-7.7
**Commit message:** `agent(app): Implement Sanic app factory with lifecycle hooks`

---

### Task 4.3: Implement api/health.py -- Health check endpoint

Create `agent/src/neos_agent/api/health.py`:

1. Define a Sanic `Blueprint("health", url_prefix="/api/v1")`
2. `GET /health` handler:
   - Read `app.ctx.skills.count` and `app.ctx.skills.is_loaded`
   - Attempt a DB test query (e.g., `SELECT 1`):
     - If success: `database = "connected"`
     - If exception: `database = "disconnected"`
   - Return JSON:
     ```json
     {
       "status": "healthy",
       "skills_loaded": <count>,
       "skills_available": <bool>,
       "database": "<connected|disconnected>",
       "version": "0.1.0"
     }
     ```
   - Always return 200 (even in degraded mode)

Run health tests -- should pass.

**Acceptance Criteria:** AC-8.1 through AC-8.5
**Commit message:** `agent(api): Implement health check endpoint`

---

### Task 4.4: Implement api/skills.py -- Skill index endpoint

Create `agent/src/neos_agent/api/skills.py`:

1. Define a Sanic `Blueprint("skills", url_prefix="/api/v1")`
2. `GET /skills` handler:
   - Read optional `layer` query parameter
   - If `layer` provided:
     - Validate it is an integer between 1-10
     - Return 400 with error message if invalid
     - Filter skills by layer
   - If no `layer`:
     - Return all skills
   - Response JSON:
     ```json
     {
       "count": <int>,
       "skills": [
         {
           "name": "...",
           "description": "...",
           "layer": <int>,
           "version": "...",
           "depends_on": [...]
         }
       ]
     }
     ```

Write `agent/tests/test_skills_api.py` with tests:
- `test_skills_returns_all` -- Returns all skills with count
- `test_skills_filter_by_layer` -- Returns only matching layer
- `test_skills_invalid_layer` -- Returns 400 for invalid layer
- `test_skills_response_format` -- Each skill has required fields

Run all tests.

**Acceptance Criteria:** AC-9.1 through AC-9.5
**Commit message:** `agent(api): Implement skill index endpoint with layer filtering`

---

### Task 4.5: Verification -- Full Integration

Verify the complete application:

1. Run full test suite: `cd agent && python -m pytest tests/ -v`
2. All tests pass
3. Start the app (with mock DB or real PostgreSQL if available):
   - `DATABASE_URL=sqlite+aiosqlite:// ANTHROPIC_API_KEY=test python -m neos_agent.main`
   - Confirm startup logs show 54 skills loaded
4. Test endpoints manually:
   - `curl http://localhost:8000/api/v1/health` returns expected JSON
   - `curl http://localhost:8000/api/v1/skills` returns 54 skills
   - `curl http://localhost:8000/api/v1/skills?layer=3` returns Layer III skills
5. Verify Dockerfile builds: `docker build -t neos-agent agent/` (if Docker is available)

**[checkpoint marker]**

**Commit message:** `agent(foundation): Complete agent foundation -- scaffolding, skills, DB, API`

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|-----------------|
| Phase 1: Scaffolding | 5 | Directory structure, pyproject.toml, Dockerfile, config.py, .env.example |
| Phase 2: Skill Loader & Registry | 7 | loader.py, graph.py, registry.py with full test coverage |
| Phase 3: Database Models & Migrations | 6 | 26-27 SQLAlchemy models, session factory, Alembic config, seed script |
| Phase 4: Sanic App Factory & API | 5 | main.py, health.py, skills.py with test coverage |
| **Total** | **23** | |

### Commit Log Template

```
agent(scaffold): Create directory structure with init files
agent(scaffold): Add pyproject.toml with dependencies
agent(scaffold): Add Dockerfile for Python 3.12-slim
agent(scaffold): Add pydantic-settings config and .env.example
agent(scaffold): Verify scaffolding installation
agent(skills): Add loader tests (TDD Red)
agent(skills): Implement skill loader with frontmatter and section parsing
agent(skills): Add dependency graph tests (TDD Red)
agent(skills): Implement dependency graph with topological sort and cycle detection
agent(skills): Add registry tests (TDD Red)
agent(skills): Implement skill registry with loading and lookup
agent(skills): Verify skill loader, graph, and registry
agent(db): Add test fixtures with in-memory SQLite
agent(db): Implement all SQLAlchemy ORM models
agent(db): Implement async session factory with Sanic lifecycle hooks
agent(db): Configure Alembic for async PostgreSQL migrations
agent(db): Add OmniOne seed data script
agent(db): Verify models, session, and seed script
agent(api): Add health endpoint tests (TDD Red)
agent(app): Implement Sanic app factory with lifecycle hooks
agent(api): Implement health check endpoint
agent(api): Implement skill index endpoint with layer filtering
agent(foundation): Complete agent foundation -- scaffolding, skills, DB, API
```

### Dependencies Between Phases

```
Phase 1 (Scaffolding)
  |
  v
Phase 2 (Skill Loader & Registry) ----+
  |                                    |
  v                                    v
Phase 3 (Database Models)        Phase 4 (Sanic App Factory)
  |                                    ^
  +------------------------------------+
```

Phase 2 and Phase 3 can be worked on in parallel after Phase 1. Phase 4 requires both Phase 2 and Phase 3 to be complete.
