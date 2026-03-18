# NEOS -- New Earth Operating System

A modular governance skill stack for non-sovereign coordination. NEOS defines how authority, agreements, decisions, economics, and coordination function across autonomous units -- without centralized coercive authority. It is civilizational middleware: the protocol layer between individual autonomy and collective coordination.

## What NEOS Is

NEOS provides 54 discrete governance skills organized into 10 layers. Each skill follows a standardized structure (sections A through L) that an AI agent can load and execute or a human architect can read and implement. Skills are independently functional, reference each other by name, and produce traceable output artifacts.

## What NEOS Is Not

NEOS is not a nation-state, a DAO, a democracy, a token-governed system, a belief system, or a political ideology. It does not assign votes, sell governance tokens, or grant authority based on capital contribution. It is an operating system layer -- structural middleware between values and daily operations.

## First Ecosystem: OmniOne

The first ecosystem instantiating NEOS is **OmniOne**, stewarded by **Green Earth Vision (GEV)**, a 501(c)(3) non-profit based in Bali. OmniOne serves as the inline example throughout the skill stack. Its organizational structure includes Town Hall (TH), Agents of the Ecosystem (AE), the OMNI Steward Council (OSC), and ETHOS (Autonomous Zones of Purposeful Operation). Another ecosystem can fork NEOS and replace OmniOne-specific configuration blocks with its own.

## The 10 Skill Layers

| Layer | Name | Skills | Description |
|-------|------|--------|-------------|
| I | Agreement | 5 | Agreement lifecycle from creation through amendment, review, registry, and the Universal Agreement Field |
| II | Authority & Role | 7 | Domain mapping, role assignment, role transfer, role sunset, authority boundary negotiation, domain review, member lifecycle |
| III | ACT Decision Engine | 6 | Advice -> Consent -> Test decision protocol: proposal creation, three ACT phases, consensus check, resolution |
| IV | Economic Coordination | 5 | Resource requests, funding pool stewardship, participatory allocation, commons monitoring, access economy transition |
| V | Inter-Unit Coordination | 5 | Cross-ETHOS requests, shared resource stewardship, federation agreements, inter-unit liaison, polycentric conflict navigation |
| VI | Conflict & Repair | 6 | Harm circles, NVC dialogue, escalation triage, repair agreements, coaching intervention, community impact assessment |
| VII | Safeguard & Capture | 5 | Governance health audit, capture pattern recognition, safeguard trigger design, independent monitoring, structural diversity maintenance |
| VIII | Emergency Handling | 5 | Emergency criteria design, pre-authorization protocol, crisis coordination, emergency reversion, post-emergency review |
| IX | Memory & Trace | 5 | Decision records, semantic tagging, precedent search, agreement versioning, precedent challenge |
| X | Exit & Portability | 5 | Voluntary exit, commitment unwinding, portable records, ETHOS dissolution, re-entry integration |

## Repository Structure

```
NewEarth/
  neos-core/
    SKILL_TEMPLATE.md              # Canonical template for all skills (sections A-L)
    README.md                      # This file
    NEOS_PRINCIPLES.md             # 10 non-negotiable structural principles
    STRESS_TEST_PROTOCOL.md        # 7 stress-test scenario definitions
    VERSION                        # Current version
    layer-01-agreement/            # Layer I: Agreement lifecycle
      agreement-creation/
        SKILL.md
        assets/
      agreement-amendment/
      agreement-review/
      agreement-registry/
      universal-agreement-field/
    layer-02-authority/            # Layer II: Authority & Role
      domain-mapping/
      role-assignment/
      role-transfer/
      role-sunset/
      authority-boundary-negotiation/
      domain-review/
      member-lifecycle/
    layer-03-act-engine/           # Layer III: ACT Decision Engine
      proposal-creation/
      act-advice-phase/
      act-consent-phase/
      act-test-phase/
      consensus-check/
      proposal-resolution/
    layer-04-economic/             # Layer IV: Economic Coordination
    layer-05-inter-unit/           # Layer V: Inter-Unit Coordination
    layer-06-conflict/             # Layer VI: Conflict & Repair
    layer-07-safeguard/            # Layer VII: Safeguard & Capture
    layer-08-emergency/            # Layer VIII: Emergency Handling
    layer-09-memory/               # Layer IX: Memory & Trace
    layer-10-exit/                 # Layer X: Exit & Portability
  scripts/
    validate_skill.py              # Validates skill structure and completeness
    test_validate_skill.py         # Tests for the validator
    md_to_pdf.py                   # Markdown to PDF export
  conductor/                       # Development orchestration (internal)
```

Each skill directory follows the same structure:

```
skill-name/
  SKILL.md          # Full skill document (YAML frontmatter + sections A-L)
  assets/           # Templates, schemas, examples (YAML)
  references/       # Supporting documents loaded as needed
  scripts/          # Executable code for deterministic tasks
```

## How to Use

### For AI Agents

1. Identify the governance function needed (e.g., "a participant wants to propose a new agreement").
2. Load the relevant `SKILL.md` file (e.g., `layer-01-agreement/agreement-creation/SKILL.md`).
3. Read the YAML frontmatter for the skill description and dependencies.
4. Follow sections A through L in order: understand the structural problem (A), confirm domain scope (B), verify trigger conditions (C), gather required inputs (D), execute the step-by-step process (E), produce the output artifact (F).
5. Use sections G through L for governance checks: authority boundary (G), capture resistance (H), failure containment (I), expiry conditions (J), exit compatibility (K), cross-unit impact (L).

### For Ecosystem Architects

1. **Fork** this repository as your starting point.
2. **Read** `NEOS_PRINCIPLES.md` to understand the 10 non-negotiable structural principles.
3. **Review** the OmniOne walkthroughs in each skill to see how the protocol works in practice.
4. **Configure** by replacing OmniOne-specific example blocks with your ecosystem's roles, structures, and defaults.
5. **Validate** your configuration using the validation scripts below.
6. **Test** against the 7 stress-test scenarios defined in `STRESS_TEST_PROTOCOL.md`.

## Validation and Scripts

### Validate Skill Structure

Checks that all skills follow the canonical template, have required YAML frontmatter, include all 12 sections (A-L), contain an OmniOne walkthrough, and have complete stress-test results.

```bash
python scripts/validate_skill.py neos-core/ --verbose
```

### Generate Stress-Test Report

Runs the stress-test evaluation across all skills and produces a summary report.

```bash
python scripts/stress_test_report.py
```

### Package for Distribution

Creates a Claude-ready zip archive of the entire skill stack.

```bash
python scripts/package_zip.py
```

## Terminology

| Term | Meaning |
|------|---------|
| ETHOS | Emergent Thriving Holonic Organizational Structure -- a self-organizing unit |
| Current-See | Influence currency (equal allocation, not purchasable) |
| Steward | Person who holds responsibility, not ownership |
| ACT | Advice -> Consent -> Test decision protocol |
| Agreement Field | The set of active agreements governing a space or interaction |
| Circle | A self-organizing group with a defined domain |
| Ecosystem | The federated whole (e.g., OmniOne) |
| Domain | Boundary within which a Circle makes decisions |

## Key Documents

- [NEOS_PRINCIPLES.md](NEOS_PRINCIPLES.md) -- 10 non-negotiable structural principles that every skill enforces
- [STRESS_TEST_PROTOCOL.md](STRESS_TEST_PROTOCOL.md) -- 7 stress-test scenarios applied to every skill
- [SKILL_TEMPLATE.md](SKILL_TEMPLATE.md) -- Canonical template defining sections A through L

## Version

See [VERSION](VERSION) for the current release. This skill stack follows semantic versioning.
