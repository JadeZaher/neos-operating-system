# NEOS Agent

Governance webservice for the **New Earth Operating System** (NEOS). Provides a real-time dashboard, AI-powered governance chat, and a REST API — all backed by the 54-skill NEOS governance stack.

Built with Sanic, SQLAlchemy, Datastar, Tailwind CSS, and the Claude API.

## Architecture

```
agent/
  src/neos_agent/
    main.py              # Sanic app factory
    config.py            # pydantic-settings (env vars)
    db/
      models.py          # 26 SQLAlchemy ORM models
      session.py         # Async engine + session factory
    skills/
      registry.py        # In-memory SKILL.md index
      graph.py           # Dependency graph (topological sort)
    agent/
      governance_tools.py  # 14 MCP-style governance tools
      system_prompt.py     # 3-layer dynamic prompt assembly
      router.py            # Skill transition router (15 patterns)
    api/
      health.py          # GET /api/v1/health
      skills.py          # GET /api/v1/skills
    views/
      dashboard.py       # Home + SSE data fragments
      agreements.py      # CRUD + status transitions + history
      domains.py         # CRUD + elements/metrics
      members.py         # CRUD + onboarding + status transitions
      proposals.py       # CRUD + ACT phase tabs (Advice/Consent/Test)
      decisions.py       # Browse + search + detail
      chat.py            # SSE streaming chat with Claude
      _rendering.py      # Jinja2 async render + Datastar SSE helpers
    templates/           # 29 Jinja2 templates (Tailwind CSS)
  alembic/               # Database migrations
  tests/                 # 167 tests
  Dockerfile             # Multi-stage production image
```

## Requirements

- Python 3.12+
- PostgreSQL 14+ (production) or SQLite (development/testing)
- A valid [Anthropic API key](https://console.anthropic.com/)
- The `neos-core/` skill directory (sibling to `agent/`)

## Quick Start

### 1. Environment Variables

You can configure the app using either a `.env` file or inline environment variables.

**Option A — `.env` file (recommended):**

```bash
cp .env.example .env
# Edit .env with your values
```

**Option B — Inline environment variables:**

```bash
# Linux / macOS
export DATABASE_URL="postgresql+asyncpg://neos:neos@localhost:5432/neos"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Windows (PowerShell)
$env:DATABASE_URL = "postgresql+asyncpg://neos:neos@localhost:5432/neos"
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Windows (CMD)
set DATABASE_URL=postgresql+asyncpg://neos:neos@localhost:5432/neos
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | Async connection string. PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/dbname`. SQLite: `sqlite+aiosqlite:///neos.db` |
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key (`sk-ant-...`) |
| `NEOS_CORE_PATH` | No | `../neos-core` | Path to the NEOS skill modules directory |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-20250514` | Claude model ID for governance chat |
| `LOG_LEVEL` | No | `info` | Logging level (`debug`, `info`, `warning`, `error`) |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins (comma-separated or `*`) |

The app loads variables in this order (first found wins):
1. System environment variables
2. `.env` file in the `agent/` directory

### 2. Install

```bash
cd agent
pip install -e .
```

For development (includes pytest, sanic-testing, aiosqlite):

```bash
pip install -e ".[dev]"
```

### 3. Database Setup

If you're using a `.env` file, the commands below will pick up `DATABASE_URL` automatically. Otherwise, set it inline first (see Step 1).

**Option A — SQLite (local dev, no install needed):**

Set `DATABASE_URL` in your `.env` file or environment:

```
DATABASE_URL=sqlite+aiosqlite:///neos.db
```

Then seed:

```bash
python -m scripts.seed_omnione
```

The seed script auto-creates tables when using SQLite — no migration step needed.

**Option B — Railway PostgreSQL (hosted):**

1. Create a PostgreSQL database on [Railway](https://railway.app) and copy the connection string.
2. Set `DATABASE_URL` in your `.env` file using the **async driver prefix** (`postgresql+asyncpg://`):

```
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@HOST:PORT/railway
```

> Railway provides URLs starting with `postgresql://`. You **must** change the scheme to `postgresql+asyncpg://` for the async driver.

3. Run migrations and seed:

```bash
python -m alembic upgrade head
python -m scripts.seed_omnione
```

**Option C — Local PostgreSQL:**

Requires PostgreSQL 14+ installed and running.

```bash
# Create the database
createdb neos

# Run migrations
python -m alembic upgrade head

# Seed with OmniOne sample data
python -m scripts.seed_omnione
```

The seed script is idempotent (safe to run multiple times) and creates:
- 1 Ecosystem (OmniOne)
- 1 UAF Agreement
- 2 Domains (SHUR Kitchen, SHUR Garden)
- 3 Members (Manu/OSC, Lani/AE, Kai/TH)
- Onboarding records and status transitions

### 4. Run

Make sure `DATABASE_URL` and `ANTHROPIC_API_KEY` are set (via `.env` or environment).

```bash
# Development (auto-reload) — run from the agent/ directory
cd agent
../.venv/Scripts/python -m neos_agent.main --dev

# Custom host/port
../.venv/Scripts/python -m neos_agent.main --dev --host 127.0.0.1 --port 3000

# Production
../.venv/Scripts/python -m neos_agent.main --workers 4
```

> **Note:** The `sanic` CLI does not work on Windows (missing `grp` module). Use `python -m neos_agent.main` instead.
>
> **First-time setup:** If you get `ModuleNotFoundError: No module named 'neos_agent'`, run `../.venv/Scripts/pip install -e .` from the `agent/` directory.

The dashboard is at [http://localhost:8000/dashboard](http://localhost:8000/dashboard).

### 5. Docker

```bash
docker build -t neos-agent .
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://host:5432/neos" \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  neos-agent
```

## Dashboard

The dashboard is a server-rendered Datastar application. Pages update in real-time via SSE without full page reloads.

| Route | Description |
|---|---|
| `/dashboard` | Home — summary cards, activity feed |
| `/dashboard/agreements` | Agreement registry with filters and CRUD |
| `/dashboard/agreements/new` | Create a new agreement |
| `/dashboard/agreements/<id>` | Agreement detail + amendment history |
| `/dashboard/domains` | Domain directory with elements and metrics |
| `/dashboard/members` | Member directory with onboarding stepper |
| `/dashboard/proposals` | Proposal list with ACT phase filtering |
| `/dashboard/proposals/new` | Create a new proposal |
| `/dashboard/proposals/<id>` | Proposal detail with Advice/Consent/Test tabs |
| `/dashboard/decisions` | Decision record archive (Layer IX memory) |

## API

### Health Check

```
GET /api/v1/health
```

Returns service status, skill count, and database connectivity.

```json
{
  "status": "healthy",
  "skills_loaded": 54,
  "skills_available": true,
  "database": "connected",
  "version": "0.1.0"
}
```

### Skill Catalog

```
GET /api/v1/skills
GET /api/v1/skills?layer=3
```

Returns all loaded NEOS governance skills with metadata, filterable by layer (1-10).

### Chat (SSE)

```
POST /chat/send
```

Streams governance-aware AI responses via Server-Sent Events. The agent uses:

- **System prompt**: Foundation context + active skill content + dependency graph
- **14 governance tools**: `search_agreements`, `create_proposal`, `record_consent_position`, `check_quorum`, `create_decision_record`, etc.
- **Skill router**: Detects when the conversation should transition between governance skills (e.g., from agreement creation to consent round)

## Governance Tools

The agent exposes 14 tools to Claude, enabling it to query and modify governance state during conversations:

| Tool | Description |
|---|---|
| `search_agreements` | Search agreements by status, type, or keyword |
| `get_agreement` | Fetch a specific agreement by ID |
| `create_agreement_draft` | Create a new agreement in draft status |
| `update_agreement_status` | Transition agreement status |
| `check_authority` | Verify a member's authority for an action |
| `create_proposal` | Submit a new governance proposal |
| `record_advice` | Record an advice entry on a proposal |
| `record_consent_position` | Record consent, objection, or stand-aside |
| `check_quorum` | Check if quorum requirements are met |
| `create_decision_record` | Create a Layer IX decision record |
| `search_precedents` | Search decision records by domain or keyword |
| `get_domain` | Fetch domain details with elements/metrics |
| `get_active_members` | List active members, optionally by profile |
| `lookup_skill` | Look up a governance skill from the registry |

## Testing

```bash
# Run all 167 tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_views.py -v       # Dashboard views
python -m pytest tests/test_chat.py -v         # Chat handler
python -m pytest tests/test_governance_tools.py -v  # Governance tools
python -m pytest tests/test_router.py -v       # Skill router
python -m pytest tests/test_system_prompt.py -v  # Prompt assembly
```

Tests use an in-memory SQLite database with seeded OmniOne data. No external services required.

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | [Sanic](https://sanic.dev) 25.x (async Python) |
| Database ORM | [SQLAlchemy](https://sqlalchemy.org) 2.0 (async) |
| Database | PostgreSQL 14+ / SQLite (dev) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org) |
| AI | [Anthropic Claude](https://anthropic.com) SDK 0.40+ |
| Frontend reactivity | [Datastar](https://data-star.dev) 1.x (11KB, SSE-first) |
| CSS | [Tailwind CSS](https://tailwindcss.com) 4.x (CDN) |
| Templates | [Jinja2](https://jinja.palletsprojects.com) (async rendering) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |

## Project Context

This agent is part of the **NEOS** (New Earth Operating System) project — a modular, non-sovereign governance architecture. The first ecosystem is **OmniOne**, a community in Bali stewarded by Green Earth Vision (GEV, 501c3).

The `neos-core/` directory contains 54 governance skill modules across 10 layers, from foundational agreements (Layer I) through exit and portability (Layer X). This agent wraps those skills into a web-accessible service with AI-assisted governance facilitation.

For more on the NEOS protocol, see [neos-core/README.md](../neos-core/README.md).
