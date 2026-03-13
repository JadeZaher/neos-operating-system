"""Tests for neos_agent.skills.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from neos_agent.skills.loader import (
    ParsedSkill,
    SkillContent,
    SkillMeta,
    SkillParseError,
    discover_skill_files,
    parse_frontmatter,
    parse_sections,
    parse_skill_file,
)


# ---------------------------------------------------------------------------
# Minimal valid SKILL.md fixture
# ---------------------------------------------------------------------------

SAMPLE_SKILL_MD = """\
---
name: test-skill
description: "A test skill for unit testing"
layer: 1
version: 0.1.0
depends_on: [domain-mapping]
---

# test-skill

## A. Structural Problem It Solves

Without this skill, units operate without a common test framework.
This skill establishes a minimal testing protocol for validation.
All governance tests pass through this skill.

## B. Domain Scope

Applies to all units within the ecosystem boundary.
Covers both internal and inter-unit testing scenarios.
Does not apply to ad-hoc informal checks.

## C. Trigger Conditions

- A new skill is introduced and requires validation.
- An existing skill is amended and must be re-tested.
- A governance audit requests verification of a skill's correctness.

## D. Required Inputs

- **Skill identifier**: the name of the skill being tested.
- **Test context**: the scenario or condition under test.
- **Executor identity**: who is running the test and their authority scope.

## E. Step-by-Step Process

1. Identify the skill to be tested.
2. Prepare the test context and required inputs.
3. Execute the test scenario step by step.
4. Record results and compare against expected outcomes.
5. Document pass/fail and any deviations.

## F. Output Artifact

- **Test record**: a structured record of test execution, result, and timestamp.
- **Pass/fail status**: explicit signal consumed by validators.
- Stored in the skill registry under the skill's test history.

## G. Authority Boundary Check

Execution of this skill requires only the authority of the skill executor.
No cross-domain permissions are required for standard test runs.
Escalation to OSC is only needed if a test reveals a systemic violation.

## H. Capture Resistance Check

Test results are recorded immutably with executor identity attached.
No single executor can modify a test record after submission.
Independent monitoring may audit test history at any time.

## I. Failure Containment Logic

If a test fails, the skill is flagged and quarantined from live execution.
Quarantine is lifted only after the root cause is resolved and a new test passes.
Failure propagation is limited to skills that directly depend on the failing skill.

## J. Expiry / Review Condition

This skill is reviewed annually or whenever a dependent skill is amended.
The test record for each run expires after 90 days unless renewed.
Review is triggered automatically by the agreement-review skill.

## K. Exit Compatibility Check

Test records are portable and included in the standard portable-record export.
Exiting participants retain access to test records they initiated.
No proprietary formats are used; all records are plain text or YAML.

## L. Cross-Unit Interoperability Impact

This skill can be invoked by any unit without cross-unit negotiation.
Results are interoperable across all NEOS-compliant ecosystems.
Units sharing skills must share compatible test records on request.

## OmniOne Walkthrough

**Scenario**: The TH team adds a new test-skill to OmniOne's governance stack.

1. GEV initiates a test run for the new skill in the TH ACT channel.
2. An AE member records the test context (skill ID: test-skill, context: initial validation).
3. The executor (AE) follows the step-by-step process above.
4. The test record is submitted to the agreement registry with a pass status.
5. OSC is notified; no escalation is required.

## Stress Tests

**Scenario 1 — Executor conflict of interest**: An AE member tries to test a skill they authored.
Resolution: A separate AE member is assigned as executor; the author is recused per the capture-pattern-recognition skill.

**Scenario 2 — Missing inputs**: A test is triggered but the test context is absent.
Resolution: The skill halts at Step 2 and requests the missing input before proceeding.
"""


# ---------------------------------------------------------------------------
# parse_frontmatter tests
# ---------------------------------------------------------------------------


def test_parse_frontmatter_valid():
    fm, errors = parse_frontmatter(SAMPLE_SKILL_MD)
    assert errors == []
    assert fm["name"] == "test-skill"
    assert fm["description"] == "A test skill for unit testing"
    assert fm["layer"] == "1"           # raw string, int conversion is in parse_skill_file
    assert fm["version"] == "0.1.0"
    assert fm["depends_on"] == ["domain-mapping"]


def test_parse_frontmatter_missing_delimiters():
    content = "name: test-skill\nlayer: 1\n"
    fm, errors = parse_frontmatter(content)
    assert len(errors) > 0
    assert "---" in errors[0] or "frontmatter" in errors[0].lower()
    assert fm == {}


def test_parse_frontmatter_empty_depends():
    content = "---\nname: x\ndescription: d\nlayer: 1\nversion: 0.1.0\ndepends_on: []\n---\n"
    fm, errors = parse_frontmatter(content)
    assert errors == []
    assert fm["depends_on"] == []


def test_parse_frontmatter_inline_list():
    content = "---\nname: x\ndescription: d\nlayer: 2\nversion: 0.1.0\ndepends_on: [skill-a, skill-b]\n---\n"
    fm, errors = parse_frontmatter(content)
    assert errors == []
    assert fm["depends_on"] == ["skill-a", "skill-b"]


def test_parse_frontmatter_quoted_values():
    # Double-quoted description
    content_double = '---\nname: x\ndescription: "A double-quoted description"\nlayer: 1\nversion: 0.1.0\ndepends_on: []\n---\n'
    fm_double, _ = parse_frontmatter(content_double)
    assert fm_double["description"] == "A double-quoted description"

    # Single-quoted description
    content_single = "---\nname: x\ndescription: 'A single-quoted description'\nlayer: 1\nversion: 0.1.0\ndepends_on: []\n---\n"
    fm_single, _ = parse_frontmatter(content_single)
    assert fm_single["description"] == "A single-quoted description"


# ---------------------------------------------------------------------------
# parse_sections tests
# ---------------------------------------------------------------------------


def test_parse_sections_valid():
    sections = parse_sections(SAMPLE_SKILL_MD)
    letters = list("ABCDEFGHIJKL")
    for letter in letters:
        assert letter in sections, f"Section {letter} missing from result"
        assert sections[letter] is not None, f"Section {letter} should not be None"
        assert sections[letter].strip() != "", f"Section {letter} should have content"


def test_parse_sections_missing_section():
    # Remove section D entirely from the content
    lines = SAMPLE_SKILL_MD.split("\n")
    filtered = [
        line for line in lines
        if "## D. Required Inputs" not in line
        and not line.startswith("- **Skill identifier**")
        and not line.startswith("- **Test context**")
        and not line.startswith("- **Executor identity**")
    ]
    # Crude removal — just strip the header line and check None is returned
    content_without_d = "\n".join(
        line for line in SAMPLE_SKILL_MD.split("\n")
        if "## D. Required Inputs" not in line
    )
    # Actually we need the whole block gone; easiest: build content with D missing
    no_d_content = (
        "---\n"
        "name: x\n"
        "description: d\n"
        "layer: 1\n"
        "version: 0.1.0\n"
        "depends_on: []\n"
        "---\n\n"
        "## A. Structural Problem It Solves\n\nSome content.\n\n"
        "## B. Domain Scope\n\nSome content.\n\n"
        "## C. Trigger Conditions\n\nSome content.\n\n"
        # D is intentionally omitted
        "## E. Step-by-Step Process\n\nSome content.\n\n"
        "## F. Output Artifact\n\nSome content.\n\n"
        "## G. Authority Boundary Check\n\nSome content.\n\n"
        "## H. Capture Resistance Check\n\nSome content.\n\n"
        "## I. Failure Containment Logic\n\nSome content.\n\n"
        "## J. Expiry / Review Condition\n\nSome content.\n\n"
        "## K. Exit Compatibility Check\n\nSome content.\n\n"
        "## L. Cross-Unit Interoperability Impact\n\nSome content.\n"
    )
    sections = parse_sections(no_d_content)
    assert sections["D"] is None
    # All other present sections should be non-None
    for letter in "ABCEFGHIJKL":
        assert sections[letter] is not None, f"Section {letter} should be present"


# ---------------------------------------------------------------------------
# parse_skill_file tests
# ---------------------------------------------------------------------------


def test_parse_skill_file_valid(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    result = parse_skill_file(skill_file)

    assert isinstance(result, ParsedSkill)
    assert result.meta.name == "test-skill"
    assert result.meta.layer == 1
    assert isinstance(result.meta.layer, int)
    assert result.meta.version == "0.1.0"
    assert result.meta.depends_on == ["domain-mapping"]
    assert result.meta.description == "A test skill for unit testing"


def test_parse_skill_file_missing_file(tmp_path):
    missing = tmp_path / "nonexistent" / "SKILL.md"
    with pytest.raises(SkillParseError, match="Cannot read"):
        parse_skill_file(missing)


def test_parse_skill_file_raw_text(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    result = parse_skill_file(skill_file)
    assert result.content.raw_text == SAMPLE_SKILL_MD


def test_parse_skill_file_layer_is_int(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    result = parse_skill_file(skill_file)
    assert isinstance(result.meta.layer, int)
    assert result.meta.layer == 1


def test_parse_skill_file_invalid_frontmatter(tmp_path):
    bad_content = "No frontmatter here at all.\n\n## A. Structural Problem It Solves\n\nContent.\n"
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(bad_content, encoding="utf-8")

    with pytest.raises(SkillParseError, match="frontmatter"):
        parse_skill_file(skill_file)


def test_parse_skill_file_missing_required_fields(tmp_path):
    incomplete = "---\nname: only-name\n---\n\n## A. Structural Problem It Solves\n\nContent.\n"
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(incomplete, encoding="utf-8")

    with pytest.raises(SkillParseError, match="Missing required frontmatter fields"):
        parse_skill_file(skill_file)


def test_parse_skill_file_invalid_layer(tmp_path):
    bad_layer = (
        "---\n"
        "name: x\n"
        "description: d\n"
        "layer: not-a-number\n"
        "version: 0.1.0\n"
        "depends_on: []\n"
        "---\n"
    )
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(bad_layer, encoding="utf-8")

    with pytest.raises(SkillParseError, match="Invalid layer"):
        parse_skill_file(skill_file)


# ---------------------------------------------------------------------------
# discover_skill_files tests
# ---------------------------------------------------------------------------


def test_discover_skill_files(tmp_path):
    # Create two SKILL.md files in different subdirectories
    (tmp_path / "skill-alpha").mkdir()
    (tmp_path / "skill-beta").mkdir()
    file_a = tmp_path / "skill-alpha" / "SKILL.md"
    file_b = tmp_path / "skill-beta" / "SKILL.md"
    file_a.write_text(SAMPLE_SKILL_MD, encoding="utf-8")
    file_b.write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    results = discover_skill_files(tmp_path)

    assert len(results) == 2
    # All results are absolute Paths
    for p in results:
        assert p.is_absolute()
        assert p.name == "SKILL.md"
    # Results are sorted
    assert results == sorted(results)


def test_discover_skill_files_empty_dir(tmp_path):
    results = discover_skill_files(tmp_path)
    assert results == []


def test_discover_skill_files_nested(tmp_path):
    # SKILL.md nested two levels deep
    deep = tmp_path / "layer-01" / "some-skill"
    deep.mkdir(parents=True)
    (deep / "SKILL.md").write_text(SAMPLE_SKILL_MD, encoding="utf-8")

    results = discover_skill_files(tmp_path)
    assert len(results) == 1
    assert results[0].name == "SKILL.md"


# ---------------------------------------------------------------------------
# Integration test — real neos-core
# ---------------------------------------------------------------------------


def _neos_core_path() -> Path:
    """Resolve neos-core relative to the agent/ directory."""
    # agent/ is one level above tests/
    agent_dir = Path(__file__).parent.parent
    return (agent_dir / ".." / "neos-core").resolve()


def test_discover_real_neos_core():
    neos_core = _neos_core_path()
    if not neos_core.exists():
        pytest.skip(f"neos-core not found at {neos_core}")

    skills = discover_skill_files(neos_core)
    assert len(skills) == 54, (
        f"Expected 54 SKILL.md files, found {len(skills)}. "
        f"Files: {[str(s) for s in skills]}"
    )


def test_parse_all_real_skills():
    """Every real SKILL.md must parse without error."""
    neos_core = _neos_core_path()
    if not neos_core.exists():
        pytest.skip(f"neos-core not found at {neos_core}")

    skill_files = discover_skill_files(neos_core)
    errors: list[str] = []
    for path in skill_files:
        try:
            skill = parse_skill_file(path)
            assert skill.meta.name, f"{path}: meta.name is empty"
            assert isinstance(skill.meta.layer, int), f"{path}: layer is not int"
        except SkillParseError as e:
            errors.append(str(e))

    assert errors == [], "Some real skills failed to parse:\n" + "\n".join(errors)
