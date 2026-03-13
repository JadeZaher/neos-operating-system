# NEOS Tech Stack

## Project Type

Governance specification + AI skill stack. Primarily markdown documents with supporting Python scripts.

## Primary Deliverable Format

- **Development**: Git repository
- **Distribution**: Zip export of skill modules with top-level README

## Languages

| Language | Purpose |
|----------|---------|
| Markdown | All skill definitions (SKILL.md), reference docs, templates, README |
| YAML | Frontmatter in SKILL.md files, configuration schemas |
| Python 3.14 | Validation scripts, schema checkers, automation tools |

## Skill File Format

```
skill-name/
├── SKILL.md          # YAML frontmatter + markdown instructions (< 500 lines)
├── scripts/          # Python scripts for deterministic tasks
├── references/       # Docs loaded into context as needed
└── assets/           # Templates, schemas, examples (markdown, YAML)
```

## Repository Structure

```
NewEarth/
├── README.md                     # Top-level overview and usage guide
├── NEOS_PRINCIPLES.md            # The 10 non-negotiable structural principles
├── STRESS_TEST_PROTOCOL.md       # The 7 stress-test scenarios
├── neos-core/                    # All skill layers
│   ├── layer-01-agreement/
│   │   ├── agreement-creation/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   ├── references/
│   │   │   └── assets/
│   │   ├── agreement-amendment/
│   │   └── ...
│   ├── layer-02-authority/
│   ├── layer-03-act-engine/
│   ├── layer-04-economic/
│   ├── layer-05-inter-unit/
│   ├── layer-06-conflict/
│   ├── layer-07-safeguard/
│   ├── layer-08-emergency/
│   ├── layer-09-memory/
│   └── layer-10-exit/
├── reference-docs/               # Source documents (docx, md)
├── scripts/                      # Global utility scripts
│   ├── validate_skill.py         # Validates SKILL.md structure
│   ├── stress_test_report.py     # Generates stress-test summary
│   └── package_zip.py            # Creates distribution zip
├── conductor/                    # Conductor project management
└── .gitignore
```

## Tooling

- **Python 3.14** — available at `c:/Python314/python`
- **Git** — version control
- **Claude Code** — AI-assisted development and skill authoring

## Schema Validation

Each SKILL.md must pass validation against the required 12-section structure (A through L). A Python validator script will enforce this.

## Agent Webservice (agent/)

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | >=3.12 | Runtime |
| Sanic | 25.x | Async web framework |
| SQLAlchemy | 2.0+ | Async ORM (asyncpg for PostgreSQL, aiosqlite for tests) |
| Alembic | 1.13+ | Database migrations |
| Anthropic SDK | 0.40+ | Claude API integration |
| pydantic-settings | 2.0+ | Configuration management |
| Datastar | 1.x | SSE-first hypermedia reactivity (11KB JS) |
| datastar-py | 0.8+ | Server-side SSE helpers |
| Tailwind CSS | 4.x (CDN) | Utility-first CSS framework (exclusively) |
| Jinja2 | via sanic-ext | Server-side templates |

### CSS Rule: Tailwind Only

**All dashboard styling MUST use Tailwind CSS utility classes exclusively.**
- No custom CSS files (no dashboard.css)
- No CSS custom properties (no --neos-*)
- Use Tailwind's built-in color palette, spacing, and responsive utilities
- Load via CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- Custom NEOS colors defined in Tailwind config block in base.html
- Responsive breakpoints use Tailwind's `sm:`, `md:`, `lg:` prefixes

## No External Dependencies (Skill Stack)

The skill stack itself (neos-core/) has zero runtime dependencies. Python scripts use only stdlib. The deliverable is self-contained markdown + YAML.
