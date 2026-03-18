# Specification: Agent Foundation -- Scaffolding, Skill Loader & Database

**Track ID:** agent_foundation_20260305
**Type:** feature
**Priority:** P0
**Created:** 2026-03-05
**Depends on:** All 10 skill layer tracks (complete), global_packaging_20260302 (complete)

---

## 1. Overview

The NEOS governance skill stack (54 skills across 10 layers in `neos-core/`) is complete. This track builds the foundation of a full webservice that wraps these skills into an agent-powered governance platform. The deliverables are: a Sanic application factory, a skill loader that parses SKILL.md files into structured dataclasses, a dependency graph engine, an in-memory skill registry, PostgreSQL database models matching all NEOS YAML templates, database session management, configuration from environment variables, and two API endpoints (health check and skill index).

This is infrastructure-only. No AI agent logic, no conversation handling, no business logic beyond loading skills and exposing them. Those come in subsequent tracks.

## 2. Background

### 2.1 Why a Webservice

The skill stack exists as markdown documents designed for AI agent consumption. To make NEOS operational for OmniOne, we need:

- A persistent service that loads and indexes all skills at startup
- A database that stores governance artifacts (agreements, proposals, decisions, members)
- API endpoints for frontends and AI agents to interact with
- Multi-tenant support so multiple ecosystems can run on the same service

### 2.2 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web framework | Sanic + sanic-ext | 25.x |
| ORM | SQLAlchemy (async) | 2.0+ |
| DB driver | asyncpg | latest |
| Migrations | Alembic | latest |
| Configuration | pydantic-settings | latest |
| Python | CPython | 3.12+ |
| Testing | pytest + pytest-asyncio + httpx + aiosqlite | latest |

Note: The agent application uses Python 3.12+, not 3.14 like the skill validation scripts. This is intentional -- 3.12 has broader library compatibility for async web frameworks.

### 2.3 Monorepo Layout

```
NewEarth/
  neos-core/                     # Existing 54-skill stack (read-only for the agent)
  agent/                         # NEW -- the governance webservice
    pyproject.toml
    Dockerfile
    alembic.ini
    alembic/versions/
    src/neos_agent/
      __init__.py
      main.py                    # Sanic app factory + lifespan
      config.py                  # pydantic-settings (env vars)
      skills/
        __init__.py
        loader.py                # Parse SKILL.md -> SkillMeta/SkillContent dataclasses
        graph.py                 # Dependency graph from depends_on
        registry.py              # In-memory skill index, loaded at startup
      db/
        __init__.py
        models.py                # SQLAlchemy async ORM models
        session.py               # AsyncSession factory, app.ctx.db
      api/
        __init__.py
        health.py                # GET /api/v1/health
        skills.py                # GET /api/v1/skills (JSON index)
    tests/
      __init__.py
      conftest.py
      test_loader.py
      test_graph.py
      test_registry.py
      test_health.py
  .env.example
```

---

## 3. Functional Requirements

### FR-1: Skill Loader (`skills/loader.py`)

**Description:** Parse SKILL.md files from `neos-core/` into structured Python dataclasses suitable for in-memory indexing, system prompt injection, and API serialization.

**Detailed Design:**

Two dataclasses:

```python
@dataclass(frozen=True)
class SkillMeta:
    name: str                    # e.g., "agreement-creation"
    description: str             # Full trigger-oriented description
    layer: int                   # 1-10
    version: str                 # semver, e.g., "0.1.0"
    depends_on: list[str]        # List of skill names
    file_path: str               # Absolute path to SKILL.md

@dataclass(frozen=True)
class SkillContent:
    sections: dict[str, str]     # {"A": "text...", "B": "text...", ...}
    raw_text: str                # Full file content for system prompt injection
```
```python
@dataclass(frozen=True)
class ParsedSkill:
    meta: SkillMeta
    content: SkillContent
```

Functions:

- `parse_frontmatter(content: str) -> tuple[dict[str, Any], list[str]]` -- Extract YAML frontmatter between `---` delimiters. Returns (parsed_dict, errors). Reuse the regex/parsing logic from `scripts/validate_skill.py` lines 77-123.
- `parse_sections(content: str) -> dict[str, str]` -- Extract all 12 sections (A through L) into a dict keyed by letter. Reuse section detection from `scripts/validate_skill.py` lines 176-208 (the `find_sections` function and `_SECTION_STOP_RE` pattern).
- `parse_skill_file(file_path: Path) -> ParsedSkill` -- Read a SKILL.md file, parse frontmatter and sections, return a ParsedSkill. Raises `SkillParseError` on failure.
- `discover_skill_files(root: Path) -> list[Path]` -- Walk `neos-core/` to find all SKILL.md files. Returns sorted list of absolute paths.

**Acceptance Criteria:**

- [ ] AC-1.1: `parse_frontmatter` correctly extracts name, description, layer (as int), version, and depends_on (as list) from valid YAML frontmatter
- [ ] AC-1.2: `parse_frontmatter` returns a descriptive error when frontmatter is missing or malformed (no `---` delimiters, missing required fields)
- [ ] AC-1.3: `parse_sections` extracts all 12 sections (A-L) by letter key, with content text stripped of the header line
- [ ] AC-1.4: `parse_sections` returns `None` for any section not found (does not raise)
- [ ] AC-1.5: `parse_skill_file` returns a `ParsedSkill` with both `meta` and `content` populated for a valid SKILL.md
- [ ] AC-1.6: `parse_skill_file` raises `SkillParseError` with a clear message including the file path when the file is missing, unreadable, or has invalid frontmatter
- [ ] AC-1.7: `discover_skill_files` finds all 54 SKILL.md files in `neos-core/` and returns them as sorted absolute paths
- [ ] AC-1.8: `raw_text` in `SkillContent` contains the complete file content (for system prompt injection)
- [ ] AC-1.9: Frontmatter parsing handles quoted and unquoted values, empty lists (`[]`), and inline lists (`[a, b, c]`)

---

### FR-2: Dependency Graph (`skills/graph.py`)

**Description:** Build and query a directed acyclic graph (DAG) from the `depends_on` fields of all loaded skills. Support topological sorting, cycle detection, and dependency queries.

**Detailed Design:**

```python
class SkillGraph:
    def __init__(self) -> None: ...

    def add_skill(self, name: str, depends_on: list[str]) -> None: ...
    def build_from_skills(self, skills: list[SkillMeta]) -> None: ...

    def topological_order(self) -> list[str]: ...
    def detect_cycles(self) -> list[list[str]]: ...

    def dependencies_of(self, name: str) -> set[str]: ...       # transitive
    def direct_dependencies_of(self, name: str) -> list[str]: ...
    def dependents_of(self, name: str) -> set[str]: ...          # reverse transitive
    def direct_dependents_of(self, name: str) -> list[str]: ...

    def has_skill(self, name: str) -> bool: ...
    @property
    def skill_names(self) -> list[str]: ...
```

**Acceptance Criteria:**

- [ ] AC-2.1: `build_from_skills` populates the graph from a list of `SkillMeta` objects
- [ ] AC-2.2: `topological_order` returns a valid topological ordering where every skill appears after all its dependencies
- [ ] AC-2.3: `detect_cycles` returns an empty list for the actual NEOS skill set (no cycles exist)
- [ ] AC-2.4: `detect_cycles` returns a list of cycle paths when cycles are artificially introduced
- [ ] AC-2.5: `dependencies_of("agreement-creation")` returns `{"domain-mapping"}` (its only transitive dependency)
- [ ] AC-2.6: `dependents_of("domain-mapping")` returns all skills that transitively depend on domain-mapping
- [ ] AC-2.7: `direct_dependencies_of` returns only immediate dependencies (not transitive)
- [ ] AC-2.8: `direct_dependents_of` returns only immediate dependents (not transitive)
- [ ] AC-2.9: Querying a non-existent skill name raises `KeyError` with a descriptive message
- [ ] AC-2.10: The graph handles skills with empty `depends_on` lists (root nodes)

---

### FR-3: Skill Registry (`skills/registry.py`)

**Description:** In-memory index of all parsed skills, loaded at startup. Provides fast lookup by name, by layer, and full listing. Exposes metadata for health checks.

**Detailed Design:**

```python
class SkillRegistry:
    def __init__(self) -> None: ...

    async def load_all(self, neos_core_path: Path) -> None: ...

    def get(self, name: str) -> ParsedSkill: ...
    def get_meta(self, name: str) -> SkillMeta: ...
    def list_by_layer(self, layer: int) -> list[SkillMeta]: ...
    def all_skills(self) -> list[SkillMeta]: ...
    def all_names(self) -> list[str]: ...

    @property
    def count(self) -> int: ...
    @property
    def graph(self) -> SkillGraph: ...
    @property
    def is_loaded(self) -> bool: ...
```

**Acceptance Criteria:**

- [ ] AC-3.1: `load_all` discovers and parses all 54 skills from `neos-core/`, populating the internal index and building the dependency graph
- [ ] AC-3.2: `load_all` logs warnings for any skills that fail to parse but does not abort (partial loading is acceptable)
- [ ] AC-3.3: `get("agreement-creation")` returns the full `ParsedSkill` for that skill
- [ ] AC-3.4: `get` raises `KeyError` for unknown skill names
- [ ] AC-3.5: `list_by_layer(1)` returns exactly the 5 Layer I skills (agreement-creation, agreement-amendment, agreement-review, agreement-registry, universal-agreement-field)
- [ ] AC-3.6: `all_skills()` returns all 54 `SkillMeta` objects
- [ ] AC-3.7: `count` returns 54 after successful loading
- [ ] AC-3.8: `graph` returns the populated `SkillGraph` instance
- [ ] AC-3.9: `is_loaded` returns `False` before `load_all` and `True` after
- [ ] AC-3.10: Registry is safe for read access from multiple Sanic workers (frozen dataclasses, no mutation after load)

---

### FR-4: Database Models (`db/models.py`)

**Description:** SQLAlchemy 2.0 async ORM models mapping 1:1 to the NEOS YAML templates. All models are multi-tenant via `ecosystem_id` foreign key, use UUID primary keys, and have `created_at`/`updated_at` timestamps.

**Model Inventory (27 tables):**

#### Core (7 tables)

| Table | Source Template | Key Fields |
|-------|----------------|------------|
| `ecosystems` | (new) | id, name, description, uaf_agreement_id, status |
| `members` | lifecycle-record-template.yaml | id, ecosystem_id, member_id, display_name, current_status, profile |
| `member_onboarding` | lifecycle-record-template.yaml (onboarding_record) | id, member_id, facilitator, uaf_version_consented, consent_date, cooling_off_start, cooling_off_end |
| `member_status_transitions` | lifecycle-record-template.yaml (status_transitions) | id, member_id, from_status, to_status, date, trigger, notes |
| `domains` | domain-contract-template.yaml | id, ecosystem_id, domain_id, version, status, purpose, current_steward, all 11 elements as columns or JSONB |
| `domain_elements` | domain-contract-template.yaml (elements detail) | id, domain_id, element_name, element_value (JSONB) |
| `domain_metrics` | domain-contract-template.yaml (metrics) | id, domain_id, metric, target, measurement_method |

#### Agreements (4 tables)

| Table | Source Template | Key Fields |
|-------|----------------|------------|
| `agreements` | agreement-template.yaml | id, ecosystem_id, agreement_id, type, title, version, status, proposer, domain, text, hierarchy_level, parent_agreement_id, review_date, sunset_date |
| `agreement_ratification_records` | agreement-template.yaml (ratification_record) | id, agreement_id, participant, role, position, date |
| `amendment_records` | amendment-record-template.yaml | id, ecosystem_id, amendment_id, parent_agreement_id, amendment_type, proposed_by, changes (JSONB), rationale, status, new_agreement_version |
| `review_records` | review-record-template.yaml | id, ecosystem_id, review_id, agreement_id, review_type, trigger, review_body (JSONB), evaluation (JSONB), outcome, next_review_date |

#### ACT Process (10 tables)

| Table | Source Template | Key Fields |
|-------|----------------|------------|
| `proposals` | proposal-template.yaml | id, ecosystem_id, proposal_id, type, decision_type, title, version, status, proposer, affected_domain, urgency, proposed_change, rationale |
| `advice_logs` | advice-log-template.yaml | id, proposal_id, advice_window_start, advice_window_end, urgency, summary, proposer_modifications |
| `advice_entries` | advice-log-template.yaml (entries) | id, advice_log_id, advisor, role, ethos, date, advice_text, proposer_response, integration_status, rationale |
| `advice_non_respondents` | advice-log-template.yaml (non_respondents) | id, advice_log_id, name, notified_date, follow_up_sent |
| `consent_records` | consent-record-template.yaml | id, proposal_id, consent_mode, weighting_model, facilitator, date, quorum_required, quorum_met, outcome, escalation_level, final_proposal_version |
| `consent_participants` | consent-record-template.yaml (participants) | id, consent_record_id, name, role, ethos, position, reason, round |
| `consent_integration_rounds` | consent-record-template.yaml (integration_rounds) | id, consent_record_id, round_number, modifications_made, outcome |
| `consent_objections_addressed` | consent-record-template.yaml (objections_addressed) | id, integration_round_id, objector, objection, resolution |
| `test_reports` | test-report-template.yaml | id, proposal_id, test_start_date, test_end_date, midpoint_checkin_date, revert_procedure, observations, outcome |
| `test_success_criteria` | test-report-template.yaml (success_criteria) | id, test_report_id, criterion, met, evidence |

#### Memory (4 tables)

| Table | Source Template | Key Fields |
|-------|----------------|------------|
| `decision_records` | decision-record-template.yaml | id, ecosystem_id, record_id, date, holding, ratio_decidendi, obiter_dicta, source_skill, source_layer, artifact_type, artifact_reference, domain, precedent_level, status |
| `decision_dissent_records` | decision-record-template.yaml (dissent_record) | id, decision_record_id, objector, objection, resolution, notes |
| `decision_participants` | decision-record-template.yaml (participants) | id, decision_record_id, name, role, position |
| `decision_semantic_tags` | decision-record-template.yaml (semantic_tags) | id, decision_record_id, topic (JSONB array), affected_parties (JSONB array), ecosystem_scope, urgency_at_time, related_precedents (JSONB array) |

#### Sessions (1 table)

| Table | Source | Key Fields |
|-------|--------|------------|
| `agent_sessions` | (new) | id, ecosystem_id, member_id, skill_name, started_at, ended_at, status, context (JSONB) |

**Shared Column Patterns:**

All tables include:
- `id: Mapped[uuid.UUID]` -- primary key, server-default `gen_random_uuid()`
- `created_at: Mapped[datetime]` -- server-default `now()`
- `updated_at: Mapped[datetime]` -- server-default `now()`, onupdate `now()`

All tables except `ecosystems` include:
- `ecosystem_id: Mapped[uuid.UUID]` -- foreign key to `ecosystems.id`, indexed

**Acceptance Criteria:**

- [ ] AC-4.1: All 27 models are defined with correct table names, columns, and types
- [ ] AC-4.2: All models use UUID primary keys with server-side default generation
- [ ] AC-4.3: All models have `created_at` and `updated_at` timestamp columns with server defaults
- [ ] AC-4.4: All non-ecosystem models have an `ecosystem_id` foreign key to `ecosystems.id`
- [ ] AC-4.5: Foreign key relationships are defined with appropriate `back_populates` where useful (parent-child relationships)
- [ ] AC-4.6: JSONB columns are used for complex nested data (changes, evaluation, semantic tags, context)
- [ ] AC-4.7: Enum columns use string-based enums (not integer enums) for readability
- [ ] AC-4.8: Index is defined on `ecosystem_id` for all multi-tenant tables
- [ ] AC-4.9: Models can be imported and used to create tables via `metadata.create_all` against an in-memory SQLite database (for testing)
- [ ] AC-4.10: A shared `Base` declarative base is defined for all models

---

### FR-5: DB Session Factory (`db/session.py`)

**Description:** Async engine and session factory for PostgreSQL, integrated with Sanic lifecycle hooks.

**Detailed Design:**

```python
async def create_engine(database_url: str) -> AsyncEngine: ...
def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]: ...

async def setup_db(app: Sanic, loop) -> None:
    """before_server_start listener: create engine, store session factory on app.ctx.db"""
    ...

async def teardown_db(app: Sanic, loop) -> None:
    """after_server_stop listener: dispose engine"""
    ...
```

**Acceptance Criteria:**

- [ ] AC-5.1: `create_engine` creates an `AsyncEngine` from a `DATABASE_URL` string
- [ ] AC-5.2: `create_session_factory` returns an `async_sessionmaker` with `expire_on_commit=False`
- [ ] AC-5.3: `setup_db` stores the session factory on `app.ctx.db` so route handlers can access it
- [ ] AC-5.4: `teardown_db` calls `engine.dispose()` to clean up connections
- [ ] AC-5.5: The session factory works with both `postgresql+asyncpg://` (production) and `sqlite+aiosqlite://` (testing) URLs
- [ ] AC-5.6: The module does not import Sanic at module level (to allow testing without a running app)

---

### FR-6: Configuration (`config.py`)

**Description:** Centralized configuration using `pydantic-settings` to load from environment variables and `.env` files.

**Detailed Design:**

```python
class Settings(BaseSettings):
    DATABASE_URL: str                                    # Required
    ANTHROPIC_API_KEY: str                               # Required
    NEOS_CORE_PATH: str = "../neos-core"                 # Relative to agent/
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"            # Default model
    LOG_LEVEL: str = "info"                              # Logging level
    CORS_ORIGINS: str = "*"                              # CORS allowed origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
```

**Acceptance Criteria:**

- [ ] AC-6.1: `Settings()` raises a validation error when `DATABASE_URL` is not set
- [ ] AC-6.2: `Settings()` raises a validation error when `ANTHROPIC_API_KEY` is not set
- [ ] AC-6.3: `NEOS_CORE_PATH` defaults to `"../neos-core"` when not set
- [ ] AC-6.4: `CLAUDE_MODEL` defaults to `"claude-sonnet-4-20250514"` when not set
- [ ] AC-6.5: `LOG_LEVEL` defaults to `"info"` when not set
- [ ] AC-6.6: `CORS_ORIGINS` defaults to `"*"` when not set
- [ ] AC-6.7: Settings can be loaded from a `.env` file
- [ ] AC-6.8: Environment variables override `.env` file values

---

### FR-7: Sanic App Factory (`main.py`)

**Description:** Create a Sanic application with lifecycle hooks that load the skill registry and initialize the database on startup.

**Detailed Design:**

```python
def create_app(settings: Settings | None = None) -> Sanic:
    """
    Factory function that:
    1. Creates Sanic app instance
    2. Registers before_server_start listener to load skill registry
    3. Registers before_server_start listener to create DB engine
    4. Registers after_server_stop listener to dispose DB engine
    5. Registers API blueprints (health, skills)
    6. Returns configured app
    """
    ...
```

**Acceptance Criteria:**

- [ ] AC-7.1: `create_app()` returns a Sanic app instance
- [ ] AC-7.2: On startup, the skill registry is loaded and stored on `app.ctx.skills`
- [ ] AC-7.3: On startup, the DB engine is created and session factory stored on `app.ctx.db`
- [ ] AC-7.4: On shutdown, the DB engine is disposed
- [ ] AC-7.5: The app registers the health and skills API blueprints
- [ ] AC-7.6: The app can be created with custom `Settings` for testing
- [ ] AC-7.7: If skill loading fails, the app logs the error but still starts (degraded mode)

---

### FR-8: Health Endpoint (`api/health.py`)

**Description:** A health check endpoint that reports service status, skill loading status, and database connectivity.

**Endpoint:** `GET /api/v1/health`

**Response (200 OK):**

```json
{
  "status": "healthy",
  "skills_loaded": 54,
  "skills_available": true,
  "database": "connected",
  "version": "0.1.0"
}
```

**Acceptance Criteria:**

- [ ] AC-8.1: Returns 200 with JSON body containing `status`, `skills_loaded`, `skills_available`, `database`, and `version`
- [ ] AC-8.2: `skills_loaded` reflects the actual count from the skill registry
- [ ] AC-8.3: `skills_available` is `true` when the registry has loaded, `false` otherwise
- [ ] AC-8.4: `database` is `"connected"` when a test query succeeds, `"disconnected"` when it fails
- [ ] AC-8.5: Returns 200 even when database is disconnected (degraded mode, not a 500)

---

### FR-9: Skill Index Endpoint (`api/skills.py`)

**Description:** An API endpoint that returns the full skill index with metadata, filterable by layer.

**Endpoint:** `GET /api/v1/skills`

**Query Parameters:**
- `layer` (optional, int): Filter by layer number (1-10)

**Response (200 OK):**

```json
{
  "count": 54,
  "skills": [
    {
      "name": "agreement-creation",
      "description": "Create a new binding agreement...",
      "layer": 1,
      "version": "0.1.0",
      "depends_on": ["domain-mapping"]
    },
    ...
  ]
}
```

**Acceptance Criteria:**

- [ ] AC-9.1: Returns all 54 skills when no `layer` parameter is provided
- [ ] AC-9.2: Returns only skills for the specified layer when `layer` parameter is provided
- [ ] AC-9.3: Returns 400 when `layer` parameter is not a valid integer or is outside 1-10
- [ ] AC-9.4: Each skill object contains `name`, `description`, `layer`, `version`, and `depends_on`
- [ ] AC-9.5: Response includes a `count` field matching the length of the `skills` array

---

### FR-10: Seed Data Script

**Description:** A standalone Python script that seeds an initial OmniOne ecosystem into the database for development and demo purposes.

**Location:** `agent/scripts/seed_omnione.py`

**Seed Data:**

1. **Ecosystem**: OmniOne (name: "OmniOne", description: "First NEOS ecosystem, stewarded by Green Earth Vision")
2. **UAF Agreement**: Initial Universal Agreement Field (type: "uaf", hierarchy_level: "universal", status: "active")
3. **Sample Domains**:
   - SHUR Kitchen (dom-shur-kitchen-001)
   - SHUR Garden (dom-shur-garden-001)
4. **Sample Members**:
   - OSC Steward (profile: co_creator, status: active)
   - AE Builder (profile: builder, status: active)
   - TH Member (profile: townhall, status: active)

**Acceptance Criteria:**

- [ ] AC-10.1: Script can be run standalone with `python -m agent.scripts.seed_omnione`
- [ ] AC-10.2: Script creates all seed records in a single transaction
- [ ] AC-10.3: Script is idempotent (running twice does not create duplicates)
- [ ] AC-10.4: Script reads DATABASE_URL from environment or .env file
- [ ] AC-10.5: Script prints a summary of created records

---

### FR-11: Project Scaffolding

**Description:** All project configuration files needed to install, build, and run the agent service.

**Files:**

1. **`agent/pyproject.toml`** -- Project metadata and dependencies
2. **`agent/Dockerfile`** -- Multi-stage build for Python 3.12-slim
3. **`.env.example`** -- All environment variables with example values
4. **`agent/alembic.ini`** -- Alembic configuration pointing to async PostgreSQL

**Acceptance Criteria:**

- [ ] AC-11.1: `pyproject.toml` lists all runtime dependencies: sanic, sanic-ext, sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, anthropic
- [ ] AC-11.2: `pyproject.toml` lists all dev dependencies: pytest, pytest-asyncio, httpx, aiosqlite
- [ ] AC-11.3: `pyproject.toml` defines the package as `neos_agent` with source in `src/`
- [ ] AC-11.4: Dockerfile produces a working image that runs the Sanic server
- [ ] AC-11.5: `.env.example` documents all environment variables with placeholder values
- [ ] AC-11.6: `alembic.ini` is configured for async PostgreSQL with the migrations directory at `agent/alembic/versions/`

---

## 4. Non-Functional Requirements

### NFR-1: Type Safety

All Python code uses type hints. All function signatures include parameter types and return types. `mypy --strict` compatibility is a goal (not a gate for this track, but code should be written toward it).

### NFR-2: Documentation

All modules have module-level docstrings. All public functions and classes have docstrings. Dataclass fields have inline comments where the field name alone is not self-documenting.

### NFR-3: Test-Driven Development

Tests are written before implementation for all non-trivial modules (loader, graph, registry, health endpoint). Tests use `pytest` with `pytest-asyncio` for async code.

### NFR-4: Test Database Strategy

Tests use `aiosqlite` with in-memory SQLite databases. No PostgreSQL required for running tests. The `conftest.py` provides fixtures for:
- In-memory database engine and session
- Temporary skill directory with sample SKILL.md files
- Sanic test client

### NFR-5: No Unnecessary Dependencies

The agent service depends only on the libraries listed in the tech stack. No additional frameworks, ORMs, or utilities beyond what is specified.

### NFR-6: Multi-Worker Safety

The skill registry is loaded once at startup using frozen dataclasses. After loading, all access is read-only. This is safe for Sanic's multi-worker mode where each worker loads its own registry.

### NFR-7: Error Handling

- Skill loading errors are logged as warnings; the registry loads all parseable skills
- Database connection failures result in degraded mode (health endpoint reports disconnected)
- Configuration errors fail fast at startup with clear error messages
- API endpoints return structured JSON error responses, never raw tracebacks

---

## 5. User Stories

### US-1: Developer Sets Up the Agent Service

**As** a developer working on the NEOS agent,
**I want** to clone the repo, run `pip install -e ".[dev]"`, set environment variables, and start the server,
**So that** I can begin developing agent features against a running service with all skills loaded.

**Given** the developer has Python 3.12+ and PostgreSQL installed,
**When** they run `pip install -e ".[dev]"` in the `agent/` directory and set `DATABASE_URL` and `ANTHROPIC_API_KEY`,
**Then** `python -m neos_agent.main` starts a Sanic server on port 8000 with 54 skills loaded.

### US-2: Developer Runs Tests Without PostgreSQL

**As** a developer,
**I want** to run `pytest` without a PostgreSQL instance,
**So that** I can validate code changes quickly in any environment.

**Given** the developer has installed dev dependencies,
**When** they run `pytest` from the `agent/` directory,
**Then** all tests pass using in-memory SQLite, with no external service dependencies.

### US-3: Frontend Checks Service Health

**As** a frontend application,
**I want** to call `GET /api/v1/health` to check if the agent service is running,
**So that** I can display connection status to the user.

**Given** the agent service is running,
**When** the frontend calls `GET /api/v1/health`,
**Then** it receives a JSON response with skills_loaded count and database status.

### US-4: Frontend Displays Skill Catalog

**As** a frontend application,
**I want** to call `GET /api/v1/skills` to get the full skill catalog,
**So that** I can display available governance skills to ecosystem administrators.

**Given** the agent service has loaded all 54 skills,
**When** the frontend calls `GET /api/v1/skills?layer=1`,
**Then** it receives the 5 Layer I skills with their metadata.

### US-5: Agent Reads Skill Content for System Prompt

**As** the AI agent module (future track),
**I want** to retrieve the full raw text of a skill from the registry,
**So that** I can inject it into the system prompt for context-aware governance assistance.

**Given** the skill registry is loaded,
**When** the agent module calls `registry.get("agreement-creation")`,
**Then** it receives a `ParsedSkill` with `content.raw_text` containing the full SKILL.md content.

---

## 6. Technical Considerations

### 6.1 Frontmatter Parsing Reuse

The `scripts/validate_skill.py` file contains battle-tested parsing logic for SKILL.md files. The skill loader should reuse the same patterns and logic, adapted from standalone functions to the loader module. Key pieces:

- `parse_frontmatter()` (lines 77-123): YAML frontmatter extraction between `---` delimiters
- `find_sections()` (lines 176-208): Section detection using regex patterns
- `_SECTION_STOP_RE` (lines 70-72): Regex for section boundary detection
- `REQUIRED_SECTIONS` (lines 41-54): The 12 required section definitions

### 6.2 SQLAlchemy Async Patterns

Use SQLAlchemy 2.0 style with `Mapped[]` type annotations:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Ecosystem(Base):
    __tablename__ = "ecosystems"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    ...
```

For testing with SQLite, the `gen_random_uuid()` server default will not work. The test fixtures should handle UUID generation in Python instead.

### 6.3 JSONB vs Normalized Tables

Some YAML template fields are deeply nested (e.g., `domain.elements`, `consent_record.integration_rounds.objections_addressed`). The approach is:

- **Normalize** when the data will be queried independently (e.g., `consent_participants` as a separate table from `consent_records`)
- **JSONB** when the data is always read/written as a unit and has variable structure (e.g., `review_records.evaluation`, `domains.elements` for list-type elements)

### 6.4 Multi-Tenant Isolation

Every query that touches tenant data must filter by `ecosystem_id`. This is enforced at the model level by requiring `ecosystem_id` on all non-ecosystem tables. Future tracks will add middleware to extract ecosystem context from the request.

### 6.5 Alembic Async Configuration

Alembic requires special configuration for async engines. The `env.py` must use `run_async()` and `connectable` patterns from SQLAlchemy async documentation.

---

## 7. Out of Scope

The following are explicitly not part of this track:

- AI agent conversation logic (future track)
- WebSocket connections (future track)
- Authentication and authorization middleware (future track)
- Rate limiting (future track)
- Deployment configuration (Kubernetes, docker-compose) beyond Dockerfile
- Frontend/UI (separate project)
- Data migration from existing OmniOne records
- Full CRUD API endpoints for governance artifacts (future track)
- Anthropic API integration (future track -- the API key is configured but not used)

---

## 8. Open Questions

1. **RESOLVED: Schema evolution strategy** -- Use Alembic migrations. Initial migration creates all 27 tables. Future schema changes are tracked as Alembic versions.
2. **RESOLVED: Test isolation** -- Use aiosqlite with in-memory databases. Each test gets a fresh database via fixtures.
3. **FUTURE: Skill hot-reloading** -- Should the registry support reloading skills without restarting the server? Deferred to a future track.
4. **FUTURE: Multi-region deployment** -- How will the database handle multiple geographic regions (Bali, Costa Rica, etc.)? Deferred.
