# Specification: Global Packaging & Cross-Layer Integration

## Track ID
`global_packaging_20260302`

## Overview

This track produces the global deliverables that wrap the entire NEOS governance skill stack into a distributable, verifiable, documented package. While every other track builds individual layers, this track builds the connective tissue: the top-level README that orients users, the NEOS Principles document that codifies the 10 non-negotiable structural principles, the Stress Test Protocol document that defines the 7 scenarios applied to every skill, the utility scripts for packaging and cross-skill stress test reporting, the cross-layer dependency verification, and the full skill index.

This track depends on all 10 skill layers being complete. It is the final track in the NEOS build sequence.

## Background

### Why Packaging Matters

NEOS is designed to be adopted by ecosystem architects who fork and configure it. A raw repository of 50+ SKILL.md files across 10 layers is unusable without: clear orientation (README), stated principles (so adopters know what is non-negotiable vs. configurable), verification tools (so adopters can validate their modifications), and distribution format (a self-contained zip that works offline).

### The Three Audiences

1. **AI Agents** reading individual skills need: clear YAML frontmatter, consistent section structure, cross-references by skill name. These needs are met by the skill format itself.
2. **Ecosystem Architects** configuring NEOS need: a top-level orientation, the principles document (to know what they cannot change), and the stress test protocol (to validate their configuration).
3. **Curious Observers** evaluating NEOS need: a readable README that explains what NEOS is, what it is not, and how to navigate the skill stack.

### Stress Testing as Quality Gate

The 7 stress-test scenarios are not just documentation -- they are the primary quality gate for the entire skill stack. Every skill must survive all 7 scenarios with a coherent structural response. The stress test report script aggregates these responses across all skills to identify systemic weaknesses: if 8 of 50 skills have weak responses to the Capital Influx scenario, that is a stack-level vulnerability.

---

## Functional Requirements

### FR-1: Top-Level README (`README.md`)

**Description:** Create a comprehensive README.md at the repository root that orients all three audiences: AI agents, ecosystem architects, and curious observers. The README is the front door to the entire NEOS skill stack.

**Acceptance Criteria:**
- AC-1.1: The README includes: project title and one-paragraph summary, what NEOS is and what it is not (the "middleware" framing), the first ecosystem (OmniOne) with brief context, the 10 skill layers listed with one-sentence descriptions, repository structure with directory guide, how to use the skill stack (for AI agents: load a skill, follow sections A-L; for architects: fork, configure, validate), how to validate skills (`scripts/validate_skill.py`), how to run the stress test report (`scripts/stress_test_report.py`), how to package for distribution (`scripts/package_zip.py`), licensing and attribution, and a link to the NEOS Principles and Stress Test Protocol documents.
- AC-1.2: The README is under 200 lines. It is a navigation document, not a treatise.
- AC-1.3: The README uses the correct terminology from product-guidelines.md (ETHOS, Current-See, Steward, ACT, etc.).
- AC-1.4: The README does not contain philosophical arguments -- it points to the Principles document for that. It is functional and navigational.

**Priority:** P0

### FR-2: NEOS Principles Document (`NEOS_PRINCIPLES.md`)

**Description:** Codify the 10 non-negotiable structural principles in a standalone document that ecosystem architects reference when determining what is configurable vs. what is architecturally fixed.

**Acceptance Criteria:**
- AC-2.1: Each of the 10 principles is stated with: the principle name, a one-sentence definition, the structural mechanism that enforces it (not just the aspiration but how the skill stack actually implements it), the specific skills that most directly implement this principle, and what would constitute a violation.
- AC-2.2: The document distinguishes between the 10 principles (non-negotiable architecture) and the OmniOne-specific configurations (customizable for other ecosystems).
- AC-2.3: The document is under 150 lines -- dense, precise, and referenceable.
- AC-2.4: Each principle includes a "this principle is violated when..." clause that gives ecosystem architects a concrete test.

**Priority:** P0

### FR-3: Stress Test Protocol Document (`STRESS_TEST_PROTOCOL.md`)

**Description:** Define the 7 stress-test scenarios as a reusable evaluation protocol that any skill author or ecosystem architect can apply. This document is the authoritative definition of each scenario, including the setup conditions, the specific pressures applied, and the evaluation criteria for a passing response.

**Acceptance Criteria:**
- AC-3.1: Each of the 7 scenarios includes: scenario name, setup conditions (the specific situation being tested), pressures applied (what forces are acting on the governance system), evaluation criteria (what constitutes a passing response -- structural integrity maintained, no hidden authority created, no capture enabled, exit remains possible), and example of a strong vs. weak response.
- AC-3.2: The document includes methodology notes: how to apply a scenario to a skill (read the skill's process, then narrate what happens when the scenario conditions are present), how to evaluate the response (does the skill's structure hold, degrade gracefully, or fail?), and how to document the result (full narrative, not bullet points).
- AC-3.3: The document is under 200 lines.
- AC-3.4: The 7 scenarios are:
  1. Capital Influx (large funding source gains influence)
  2. Emergency Crisis (acute crisis requiring rapid governance response)
  3. Leadership Charisma Capture (personality dominates governance)
  4. High Conflict / Polarization (factions blocking each other)
  5. Large-Scale Replication (ecosystem grows 100x)
  6. External Legal Pressure (government demands structural changes)
  7. Sudden Exit of 30% (mass departure)

**Priority:** P0

### FR-4: Packaging Script (`scripts/package_zip.py`)

**Description:** Create a Python script that packages the entire NEOS skill stack into a distributable zip file. The zip contains all SKILL.md files, asset templates, the README, Principles, and Stress Test Protocol, but excludes development artifacts (conductor/, .git/, scripts/test_*, etc.).

**Acceptance Criteria:**
- AC-4.1: The script accepts CLI arguments: `python package_zip.py [--output <path>] [--include-scripts]`. Default output is `neos-core-vX.Y.Z.zip` in the repository root. The `--include-scripts` flag includes `scripts/validate_skill.py` in the zip.
- AC-4.2: The zip contains: `README.md`, `NEOS_PRINCIPLES.md`, `STRESS_TEST_PROTOCOL.md`, all `neos-core/` contents (SKILL.md files, assets/, references/), and optionally `scripts/validate_skill.py`.
- AC-4.3: The zip excludes: `conductor/`, `.git/`, `__pycache__/`, `scripts/test_*`, `scripts/fixtures/`, `reference-docs/` (source documents not needed for distribution).
- AC-4.4: The script runs validation before packaging: calls `validate_skill.py` on all SKILL.md files and aborts if any fail. Packaging is only possible when all skills pass validation.
- AC-4.5: The script prints a manifest of included files and the total size.
- AC-4.6: Uses only Python stdlib (no external dependencies).
- AC-4.7: TDD: test file written before implementation.

**Priority:** P1

### FR-5: Stress Test Report Script (`scripts/stress_test_report.py`)

**Description:** Create a Python script that scans all SKILL.md files, extracts stress-test results for each of the 7 scenarios, and produces an aggregated cross-skill stress test summary. This summary identifies systemic strengths and weaknesses across the skill stack.

**Acceptance Criteria:**
- AC-5.1: The script accepts CLI arguments: `python stress_test_report.py [--path <neos-core-dir>] [--format text|markdown]`. Default path is `neos-core/`. Default format is markdown.
- AC-5.2: The script scans each SKILL.md for stress-test sections, extracting scenario name and response text.
- AC-5.3: The output includes: a matrix (skills x scenarios) showing presence/absence of each stress test, a per-scenario summary (how many skills address this scenario, any skills missing it), a strength/weakness analysis (identifies scenarios where multiple skills have notably strong or notably weak responses -- based on response length and structural keyword presence as heuristic), and a full skill index (all skills listed with layer, name, description from frontmatter).
- AC-5.4: The skill index portion serves as the comprehensive index of all NEOS skills.
- AC-5.5: Uses only Python stdlib.
- AC-5.6: TDD: test file written before implementation.

**Priority:** P1

### FR-6: Cross-Layer Dependency Verification

**Description:** Verify that all cross-layer references in all SKILL.md files are accurate: every skill referenced by name actually exists, every layer referenced by number actually exists, and no circular authority dependencies exist.

**Acceptance Criteria:**
- AC-6.1: A verification pass scans all SKILL.md files and extracts `depends_on` from YAML frontmatter.
- AC-6.2: Every skill name in `depends_on` must correspond to an actual SKILL.md in the repository.
- AC-6.3: Every skill name mentioned in the body text of a SKILL.md (e.g., "see the agreement-creation skill") should correspond to an actual skill.
- AC-6.4: The verification produces a dependency graph showing which skills reference which others.
- AC-6.5: This verification can be added to `validate_skill.py` as a `--cross-reference` mode or implemented as a separate script.

**Priority:** P1

---

## Non-Functional Requirements

### NFR-1: Self-Contained Distribution

The packaged zip must be fully usable without any external resources. A user receiving the zip should be able to read the README, navigate to any skill, understand the principles, and apply the stress tests without needing internet access or additional tooling.

### NFR-2: No External Dependencies

All Python scripts use only stdlib. The distribution has zero runtime dependencies.

### NFR-3: Portability

All documents use relative paths within the repository. The zip works on any operating system. No hardcoded absolute paths.

### NFR-4: Consistent Voice

The README, Principles, and Stress Test Protocol follow the same voice and tone guidelines as the SKILL.md files (inspirational and structural, per product-guidelines.md). Terminology is consistent throughout.

### NFR-5: Maintainability

The packaging and reporting scripts should be straightforward enough that a single developer can maintain and extend them. No complex abstractions -- these are utility scripts.

---

## User Stories

### US-1: Ecosystem Architect Evaluates NEOS
**As** an ecosystem architect considering NEOS for my community,
**I want** a clear README that tells me what NEOS is, how it works, and how to get started,
**So that** I can evaluate whether NEOS fits my needs within 15 minutes of opening the repository.

**Given** the architect opens the README,
**When** they read it,
**Then** they understand what NEOS is, what it is not, how the 10 layers work together, and where to go next.

### US-2: Ecosystem Architect Configures NEOS
**As** an ecosystem architect customizing NEOS for my community,
**I want** to know which principles are non-negotiable and which elements are configurable,
**So that** I can modify the skill stack without accidentally undermining its structural integrity.

**Given** the architect has forked the repository,
**When** they read NEOS_PRINCIPLES.md,
**Then** they understand the 10 principles, the enforcement mechanisms, and the violation tests -- and can confidently modify OmniOne-specific configurations.

### US-3: Skill Author Writes a Stress Test
**As** a skill author completing a new SKILL.md,
**I want** a clear protocol for how to apply each stress-test scenario,
**So that** my stress-test responses are thorough and consistent with other skills.

**Given** the author has written sections A-L and the OmniOne walkthrough,
**When** they read STRESS_TEST_PROTOCOL.md,
**Then** they understand the setup conditions, pressures, and evaluation criteria for each scenario and can write full narrative responses.

### US-4: AI Agent Navigates the Skill Stack
**As** an AI agent loaded with the NEOS skill stack,
**I want** a skill index that lists all skills with their layer, name, and description,
**So that** I can quickly identify which skill to load for a given governance task.

**Given** the AI agent needs to find the right skill for a participant's question,
**When** it reads the stress test report's skill index section,
**Then** it can identify the relevant skill by description and navigate to it.

### US-5: Distributor Packages NEOS for Delivery
**As** a project maintainer preparing a NEOS release,
**I want** a one-command packaging script that validates and zips the distribution,
**So that** I can confidently distribute a verified, self-contained package.

**Given** all skills pass validation,
**When** the maintainer runs `package_zip.py`,
**Then** a zip file is produced containing all distribution files, excluding development artifacts, with a printed manifest.

### US-6: Quality Reviewer Assesses Stack-Level Vulnerabilities
**As** a governance reviewer evaluating the NEOS stack's robustness,
**I want** an aggregated stress-test report showing how all skills respond to each scenario,
**So that** I can identify systemic weaknesses that individual skill reviews might miss.

**Given** all skills have stress-test sections,
**When** the reviewer runs `stress_test_report.py`,
**Then** a cross-skill matrix is produced showing coverage, and the analysis highlights scenarios where multiple skills have weak responses.

---

## Technical Considerations

### File Structure

```
NewEarth/
  README.md                       # FR-1
  NEOS_PRINCIPLES.md              # FR-2
  STRESS_TEST_PROTOCOL.md         # FR-3
  neos-core/                      # All skill layers (built by other tracks)
  scripts/
    validate_skill.py             # Already exists (from foundation track)
    test_validate_skill.py        # Already exists
    package_zip.py                # FR-4
    test_package_zip.py           # Tests for FR-4
    stress_test_report.py         # FR-5
    test_stress_test_report.py    # Tests for FR-5
    fixtures/                     # Test fixtures (already exists)
  conductor/                      # Excluded from distribution
  reference-docs/                 # Excluded from distribution
```

### Version Numbering

The packaged zip uses the version from a `VERSION` file at the repository root (e.g., `0.1.0` for the initial complete build). The `package_zip.py` script reads this file to name the zip.

### Script Testing Strategy

Both new scripts (`package_zip.py` and `stress_test_report.py`) follow TDD:
1. Write test file with expected behavior
2. Run tests -- all fail (Red)
3. Implement script
4. Run tests -- all pass (Green)
5. Refactor for clarity

Test fixtures use a minimal set of SKILL.md files in `scripts/fixtures/` (may already exist from foundation track validation script tests).

### Cross-Reference Verification Approach

Cross-layer dependency verification can be implemented as:
- A `--cross-reference` flag on `validate_skill.py` that scans all skills and checks that every `depends_on` entry and every in-text skill reference corresponds to an actual SKILL.md
- Produces a dependency graph in text format (DOT-like or simple list)
- Reports orphan references (references to skills that do not exist) and unreferenced skills (skills that no other skill depends on -- which may be fine for anchor skills but worth flagging)

---

## Out of Scope

- **Automated deployment** -- The package is a zip file. Hosting, CDN distribution, and download infrastructure are out of scope.
- **Interactive documentation** -- No web-based viewer, searchable interface, or rendered HTML. The distribution is markdown files.
- **Continuous integration** -- No CI/CD pipeline. Validation and packaging are run manually.
- **Changelog or release notes** -- The initial build does not need a changelog. Future tracks may add one.
- **Translation or localization** -- All documents are in English. Multi-language support is deferred.

---

## Open Questions

1. **Version numbering scheme**: Should the initial complete build be `0.1.0` (pre-release) or `1.0.0` (first release)? Recommendation: `0.1.0` because the skill stack has not been tested with real governance yet. `1.0.0` is reserved for post-pilot validation.

2. **Skill index format**: Should the skill index be a separate file (`SKILL_INDEX.md`) or embedded in the stress test report output? Recommendation: the stress test report generates it as part of its output, and it is also included in the README as a summary table.

3. **License**: What license should the NEOS skill stack be distributed under? This is a governance specification, not software. Creative Commons (CC BY-SA 4.0) may be more appropriate than MIT/Apache. Deferred to project leadership decision.

4. **Reference document inclusion**: Should the `reference-docs/` directory (source documents like the OmniOne field agreement) be included in the distribution zip? Recommendation: no -- they are source material, not part of the skill stack itself. Skills reference them but do not require them.
