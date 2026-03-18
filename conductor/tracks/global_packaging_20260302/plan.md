# Implementation Plan: Global Packaging & Cross-Layer Integration

## Overview

This plan produces the global deliverables that wrap the NEOS governance skill stack into a distributable package, organized into 5 phases. The build order starts with the reference documents (Principles, Stress Test Protocol), moves to the utility scripts (packaging, reporting), then to the README (which references everything else), and concludes with full cross-layer verification and final quality gate.

**Total deliverables:** 3 documents + 2 scripts + cross-layer verification + full skill index
**Total phases:** 5
**Estimated scope:** 15-22 hours of focused implementation

### Build Order Rationale

The Principles and Stress Test Protocol documents are written first because the README references them and the scripts depend on stress test section structure. Scripts are built next using TDD. The README is written after everything else exists so it can accurately describe the full package. Cross-layer verification is the final gate because it requires all 10 layers and all global documents to be complete.

### Commit Strategy

- Document commits: `neos(global): Add <document-name>`
- Script commits: `neos(scripts): Add <script-name>`
- Integration commit: `neos(global): Complete packaging and cross-layer verification`

---

## Phase 1: Reference Documents

**Goal:** Write the NEOS Principles document and the Stress Test Protocol document. These are the two authoritative reference documents that all other deliverables depend on.

### Tasks

- [ ] **Task 1.1: Draft NEOS_PRINCIPLES.md**
  Write the 10 structural principles document:
  1. **No Sovereign Authority** -- No permanent centralized override exists. Enforcement: all authority is scoped, reviewed, and revocable through ACT process. Skills: authority-role-definition, emergency-reversion, governance-health-audit. Violation: any person or body that can override any decision without process.
  2. **Scoped Authority** -- Authority exists only within defined domains, must expire or be reviewable. Enforcement: every authority assignment has a domain boundary, a review date, and a removal process. Skills: authority-role-definition, act-consent-phase. Violation: authority exercised outside its defined domain without ACT process.
  3. **Voluntary Participation** -- Exit is always structurally possible. Enforcement: voluntary-exit skill ensures departure cannot be prevented. Skills: voluntary-exit, commitment-unwinding, portable-record. Violation: any mechanism that makes exit practically impossible through financial, social, or structural barriers.
  4. **Capital Does Not Equal Power** -- Economic contribution does not grant governance authority. Enforcement: governance-health-audit monitors resource concentration; safeguard triggers activate on capital capture indicators. Skills: governance-health-audit, capture-pattern-recognition, safeguard-trigger-design. Violation: a funding source gaining veto power or systematic approval bias.
  5. **Solutionary Decision-Making (ACT)** -- Advice, Consent, Test. Enforcement: all governance decisions route through the ACT engine. Skills: act-advice-phase, act-consent-phase, act-test-phase, proposal-creation. Violation: decisions made outside ACT process except within pre-authorized emergency scope.
  6. **Local Failure Containment** -- Autonomous units; failure does not cascade. Enforcement: ETHOS boundaries, inter-unit coordination protocols. Skills: inter-unit skills, ethos-dissolution. Violation: one ETHOS's failure causing governance collapse in another ETHOS.
  7. **Explicit Agreements** -- Written, scannable, traceable, revisable. Enforcement: agreement registry, version control, review dates. Skills: agreement-creation, agreement-registry, agreement-review. Violation: binding commitments that exist only as informal understandings.
  8. **Capture Resistance** -- Resists capital, charismatic, emergency, and informal capture. Enforcement: Layer VII monitoring, safeguard triggers, independent monitoring. Skills: all Layer VII skills, post-emergency-review. Violation: sustained capture pattern with no triggered safeguard.
  9. **Pluralism** -- Multiple value systems coexist via agreement, not belief. Enforcement: consent (not consensus) as default decision mode, UAF defines process not ideology. Skills: universal-agreement-field, act-consent-phase. Violation: governance decisions based on ideological alignment rather than reasoned objection process.
  10. **Emergency Contraction** -- Temporary expansion auto-expires. Enforcement: circuit breaker with auto-reversion timer, mandatory recovery state. Skills: all Layer VIII skills. Violation: emergency authority persisting beyond exit criteria or auto-reversion timer.

  For each principle: name, definition (1 sentence), enforcement mechanism (how the skill stack implements it), primary skills (which skills most directly enforce it), violation test ("this principle is violated when...").
  **Acceptance:** All 10 principles documented. Under 150 lines. Each principle has enforcement mechanism and violation test.

- [ ] **Task 1.2: Draft STRESS_TEST_PROTOCOL.md**
  Write the 7 stress-test scenarios as a reusable evaluation protocol:
  1. **Capital Influx Scenario**
     - Setup: A single funding source offers resources equal to 200% of current budget, contingent on governance accommodations (favorable agreement terms, board representation, veto power).
     - Pressures: Financial dependency, self-censorship near funder, systematic approval bias for funder-aligned proposals.
     - Evaluation criteria: (a) The skill's process does not shortcut or bypass because of funding, (b) capture indicators are flagged, (c) no hidden authority is created, (d) the funding can be accepted without governance compromise.
     - Strong response: The skill's structure routes the funding through normal processes, safeguard triggers fire on concentration, and the funder receives no governance authority.
     - Weak response: The skill defers to "leadership judgment" or "case-by-case assessment" without structural guardrails.

  2. **Emergency Crisis Scenario**
     - Setup: A sudden, severe crisis (natural disaster, infrastructure failure, funding collapse) requiring governance action within 24-48 hours.
     - Pressures: Time compression, authority concentration, bypass of consultation, precedent for future shortcuts.
     - Evaluation criteria: (a) The skill can operate under compressed timelines, (b) authority expansion is bounded and pre-authorized, (c) auto-reversion is structurally guaranteed, (d) a post-emergency review is mandated.
     - Strong/weak response examples.

  3. **Leadership Charisma Capture Scenario**
     - Setup: A charismatic, well-intentioned leader's proposals consistently pass without modification, objections are withdrawn under social pressure, and new member onboarding depends on personal relationship with the leader.
     - Pressures: Social dynamics, psychological safety, information asymmetry, identity attachment.
     - Evaluation criteria: (a) The skill's structure protects objectors, (b) proposals are evaluated on merit not authorship, (c) onboarding is process-based not relationship-based, (d) capture indicators are detectable.
     - Strong/weak response examples.

  4. **High Conflict / Polarization Scenario**
     - Setup: Two factions with mutually exclusive positions are blocking each other's proposals. Participation splits into non-overlapping groups. Decision-making is gridlocked.
     - Pressures: Emotional escalation, zero-sum framing, withdrawal from governance, exit threats.
     - Evaluation criteria: (a) The skill's escalation path leads to resolution, (b) "third solution" finding is structurally supported, (c) participation does not collapse, (d) the conflict can be addressed without governance shutdown.
     - Strong/weak response examples.

  5. **Large-Scale Replication Scenario**
     - Setup: The ecosystem grows from 50 to 5,000 participants across 40 ETHOS in 5 countries.
     - Pressures: Coordination overhead, cultural diversity, timezone distribution, communication bottlenecks, governance fatigue.
     - Evaluation criteria: (a) The skill's process remains feasible at scale, (b) authority does not concentrate due to coordination pressure, (c) local autonomy is preserved, (d) cross-ETHOS processes work across timezone and language.
     - Strong/weak response examples.

  6. **External Legal Pressure Scenario**
     - Setup: A government jurisdiction demands that the ecosystem modify its governance to comply with local law (e.g., mandatory registered officers, data disclosure, organizational structure requirements).
     - Pressures: Legal consequences for non-compliance, sovereignty vs. legality tension, different jurisdictions making conflicting demands.
     - Evaluation criteria: (a) The skill handles the tension between NEOS principles and legal requirements, (b) compliance in one jurisdiction does not force global structural changes, (c) legal interface is contained, (d) no hidden authority is created through legal proxies.
     - Strong/weak response examples.

  7. **Sudden Exit of 30% of Participants Scenario**
     - Setup: 30% of participants depart within a 2-week period (organizational disagreement, external opportunity, community conflict).
     - Pressures: Loss of institutional knowledge, quorum failures, role vacancies, morale collapse, agreement review triggers.
     - Evaluation criteria: (a) Governance continues functioning for remaining participants, (b) departure process is orderly, (c) commitments are handled through graceful degradation, (d) governance health audit triggers and identifies systemic impacts.
     - Strong/weak response examples.

  Include methodology notes: how to apply a scenario (narrate the skill's process under scenario conditions), how to evaluate (does the structure hold, degrade gracefully, or fail?), how to document (full narrative paragraph, not bullet points).
  **Acceptance:** All 7 scenarios documented with setup, pressures, evaluation criteria, and response examples. Under 200 lines. Methodology notes included.

- [ ] **Verification 1: Review both documents against product.md and product-guidelines.md. Principles must match the 10 from product.md. Stress scenarios must match the 7 from product.md. Terminology must be consistent. Voice must follow product-guidelines.md.** [checkpoint marker]

---

## Phase 2: Packaging Script

**Goal:** Build the `package_zip.py` script using TDD. After this phase, the skill stack can be validated and packaged into a distributable zip.

### Tasks

- [ ] **Task 2.1: Write test_package_zip.py (TDD Red)**
  Write the test file defining expected behavior:
  - Test: script creates a zip file at the specified output path
  - Test: zip contains README.md, NEOS_PRINCIPLES.md, STRESS_TEST_PROTOCOL.md
  - Test: zip contains all neos-core/ SKILL.md files and assets
  - Test: zip excludes conductor/, .git/, __pycache__/, scripts/test_*, scripts/fixtures/
  - Test: zip includes scripts/validate_skill.py when --include-scripts flag is used
  - Test: zip excludes scripts/validate_skill.py when --include-scripts flag is not used
  - Test: script runs validation before packaging and aborts on failure (mock validation)
  - Test: script prints a manifest of included files
  - Test: script reads version from VERSION file for zip naming
  - Test: script exits with code 0 on success, 1 on validation failure
  Create test fixtures as needed (minimal directory structure with test SKILL.md files).
  **Acceptance:** Test file runs, all tests fail (Red).

- [ ] **Task 2.2: Implement package_zip.py (TDD Green)**
  Write the packaging script using only Python stdlib:
  - Parse CLI arguments: `--output <path>`, `--include-scripts`
  - Read VERSION file for zip naming (default: `neos-core-v{version}.zip`)
  - Run `validate_skill.py` on all SKILL.md files (subprocess call)
  - If validation fails: print error, exit 1
  - If validation passes: build file list (include/exclude rules), create zip, print manifest with file count and total size, exit 0
  Include/exclude rules:
  - Include: README.md, NEOS_PRINCIPLES.md, STRESS_TEST_PROTOCOL.md, VERSION, neos-core/**/*
  - Exclude: conductor/**, .git/**, __pycache__/**, scripts/test_*, scripts/fixtures/**, reference-docs/**
  - Conditional: scripts/validate_skill.py (only with --include-scripts)
  **Acceptance:** All tests from Task 2.1 pass (Green).

- [ ] **Task 2.3: Refactor package_zip.py (TDD Refactor)**
  Review for:
  - Clean function decomposition (file collection, validation, zip creation, manifest printing)
  - Helpful error messages
  - Consistent output format
  - Add a `--dry-run` flag that prints the manifest without creating the zip
  **Acceptance:** All tests still pass. Code is clean.

- [ ] **Task 2.4: Create VERSION file**
  Create `VERSION` file at repository root containing `0.1.0`.
  **Acceptance:** VERSION file exists and is read correctly by package_zip.py.

- [ ] **Verification 2: Run package_zip.py with --dry-run against the actual repository. Verify the manifest includes the expected files and excludes the expected directories. If SKILL.md files exist, verify they are included.** [checkpoint marker]

---

## Phase 3: Stress Test Report Script

**Goal:** Build the `stress_test_report.py` script using TDD. After this phase, cross-skill stress test analysis is automated.

### Tasks

- [ ] **Task 3.1: Write test_stress_test_report.py (TDD Red)**
  Write the test file defining expected behavior:
  - Test: script finds all SKILL.md files in the specified directory
  - Test: script extracts YAML frontmatter (name, description, layer) from each skill
  - Test: script detects presence/absence of each of the 7 stress-test scenario sections
  - Test: script produces a skill x scenario presence matrix
  - Test: script produces per-scenario coverage summary (N of M skills address this scenario)
  - Test: script produces a full skill index (layer, name, description)
  - Test: script outputs in markdown format by default
  - Test: script outputs in text format with --format text
  - Test: script identifies skills missing stress-test sections
  - Test: script exits 0 if all skills have all scenarios, 1 if any are missing
  Create test fixtures with minimal SKILL.md files (some complete, some missing stress tests).
  **Acceptance:** Test file runs, all tests fail (Red).

- [ ] **Task 3.2: Implement stress_test_report.py (TDD Green)**
  Write the stress test report script using only Python stdlib:
  - Parse CLI arguments: `--path <directory>`, `--format text|markdown`
  - Recursively find all SKILL.md files
  - For each file: parse YAML frontmatter, scan for stress-test section headers (matching the 7 scenario names)
  - Build the presence matrix: skills (rows) x scenarios (columns)
  - Build the skill index: layer number, skill name, description (from frontmatter)
  - Generate per-scenario summary: count of skills addressing each scenario, list of skills missing each scenario
  - Generate strength/weakness heuristic: flag scenarios where more than 20% of skills are missing responses, flag skills missing more than 2 scenarios
  - Output in markdown or text format
  - Exit 0 if complete coverage, 1 if gaps exist
  **Acceptance:** All tests from Task 3.1 pass (Green).

- [ ] **Task 3.3: Refactor stress_test_report.py (TDD Refactor)**
  Review for:
  - Clean function decomposition (file discovery, parsing, matrix building, output formatting)
  - Markdown output uses tables for the matrix and the skill index
  - Text output is readable in terminal (aligned columns)
  - Add a `--verbose` flag that includes the first 100 characters of each stress-test response as a preview
  **Acceptance:** All tests still pass. Markdown output is well-formatted.

- [ ] **Verification 3: Run stress_test_report.py against the actual neos-core/ directory. If SKILL.md files exist, verify the report accurately reflects their stress-test coverage. If no SKILL.md files exist yet, run against test fixtures and verify output format.** [checkpoint marker]

---

## Phase 4: README and Skill Index

**Goal:** Write the top-level README that ties everything together. The README is written last because it references all other deliverables.

### Tasks

- [ ] **Task 4.1: Draft README.md**
  Write the top-level README with these sections:
  - **Title and Summary:** "NEOS -- New Earth Operating System. A modular governance skill stack for non-sovereign coordination." One paragraph explaining what NEOS is.
  - **What NEOS Is Not:** Not a nation-state, DAO, democracy, token system, belief system, or political ideology. It is an OS layer.
  - **The 10 Skill Layers:** Table with layer number, name, and one-sentence description. Link to each layer's README.
  - **First Ecosystem: OmniOne:** Brief context (GEV, SHUR, Bali, etc.) explaining that OmniOne examples appear throughout as the reference implementation.
  - **Repository Structure:** Directory tree with brief annotations.
  - **How to Use This Skill Stack:**
    - For AI Agents: Load a skill's SKILL.md. Read sections A-L for the process. Follow the step-by-step.
    - For Ecosystem Architects: Fork the repository. Read NEOS_PRINCIPLES.md to understand non-negotiable architecture. Replace OmniOne examples with your ecosystem's configuration. Run validate_skill.py to verify.
    - For Evaluators: Read this README, then NEOS_PRINCIPLES.md, then browse individual skills.
  - **Validation:** How to run `validate_skill.py`.
  - **Stress Testing:** How to run `stress_test_report.py`. Link to STRESS_TEST_PROTOCOL.md.
  - **Packaging:** How to run `package_zip.py`.
  - **Structural Principles:** Link to NEOS_PRINCIPLES.md with one-sentence summary.
  - **License:** Placeholder for project leadership decision.
  Use product-guidelines.md terminology throughout. Under 200 lines.
  **Acceptance:** README is navigational, accurate, under 200 lines, uses correct terminology.

- [ ] **Task 4.2: Generate skill index**
  Run `stress_test_report.py` to generate the full skill index. Review the index for:
  - All 50+ skills across 10 layers are listed
  - Each skill has layer number, name, and description
  - Skills are grouped by layer
  - The index can be included in the README as a reference section or linked as separate output
  If not all skills are complete yet, create a placeholder index structure that can be populated as skills are completed.
  **Acceptance:** Skill index is accurate, complete (or has documented placeholders for incomplete layers), and well-formatted.

- [ ] **Verification 4: Review README against the actual repository structure. Every file and directory referenced in the README must exist (or be noted as forthcoming). Every script referenced must work as described. Every document linked must exist.** [checkpoint marker]

---

## Phase 5: Cross-Layer Verification and Final Quality Gate

**Goal:** Run the full cross-layer dependency verification and confirm the entire NEOS skill stack is coherent, validated, and packaged.

### Tasks

- [ ] **Task 5.1: Implement cross-reference verification**
  Add a `--cross-reference` mode to `validate_skill.py` (or create a separate script `verify_cross_references.py`):
  - Scan all SKILL.md files
  - Extract `depends_on` from YAML frontmatter
  - Extract skill names mentioned in body text (pattern: "the <skill-name> skill" or "see <skill-name>")
  - Verify each referenced skill name corresponds to an actual SKILL.md
  - Build dependency graph (text output: each skill and its references)
  - Report: orphan references (references to non-existent skills), unreferenced skills (skills referenced by no other skill), circular dependencies (A depends on B depends on A)
  - Exit 0 if no orphan references, 1 if any exist
  **Acceptance:** Cross-reference verification runs against the full repository. Dependency graph is produced.

- [ ] **Task 5.2: Run full cross-layer verification**
  Execute the cross-reference verification against all 10 layers:
  - Verify all `depends_on` references resolve
  - Verify all in-text skill references resolve
  - Review the dependency graph for:
    - Layer I and III have no dependencies (foundation)
    - Layer VII depends on Layer I-VI (monitoring)
    - Layer VIII depends on Layer II and VII (emergency with safeguard)
    - Layer X depends on all layers (capstone)
  - Identify and document any circular dependencies
  - Identify and document any unreferenced skills (may be fine for utility skills)
  **Acceptance:** No orphan references. Dependency graph matches the expected architecture.

- [ ] **Task 5.3: Run full validation suite**
  Run `validate_skill.py` against every SKILL.md in the repository. Run `stress_test_report.py` to generate the full coverage report. Run `package_zip.py --dry-run` to verify packaging would succeed.
  Results:
  - All SKILL.md files pass validation
  - Stress test coverage is 100% (all skills, all 7 scenarios)
  - Packaging manifest includes all expected files
  **Acceptance:** All three tools report success.

- [ ] **Task 5.4: Final review and packaging**
  Review the complete deliverable set:
  - [ ] README.md is accurate and navigational
  - [ ] NEOS_PRINCIPLES.md covers all 10 principles with enforcement mechanisms
  - [ ] STRESS_TEST_PROTOCOL.md defines all 7 scenarios with evaluation criteria
  - [ ] validate_skill.py passes all SKILL.md files
  - [ ] stress_test_report.py generates complete coverage report
  - [ ] package_zip.py produces a valid distribution zip
  - [ ] Cross-reference verification reports no orphan references
  - [ ] Skill index is complete and accurate
  Run `package_zip.py --include-scripts` to produce the final distribution zip.
  **Acceptance:** Distribution zip exists. Manifest is printed. All quality gates pass.

- [ ] **Verification 5: Final global review. All documents exist and are accurate. All scripts run successfully. All SKILL.md files pass validation. Stress-test coverage is 100%. Cross-references are clean. Distribution zip is produced. The NEOS governance skill stack is complete and distributable. Commit: `neos(global): Complete packaging and cross-layer verification v0.1.0`** [checkpoint marker]
