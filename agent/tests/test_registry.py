"""Tests for SkillRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from neos_agent.skills.registry import SkillRegistry

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# agent/tests/ -> agent/ -> NewEarth/ -> neos-core/
_NEOS_CORE = Path(__file__).resolve().parents[2] / "neos-core"

# ---------------------------------------------------------------------------
# Sample SKILL.md content — a complete, parseable file
# ---------------------------------------------------------------------------

SAMPLE_SKILL_ALPHA = """\
---
name: test-skill-alpha
description: "Alpha test skill"
layer: 1
version: 0.1.0
depends_on: []
---

# test-skill-alpha

## A. Structural Problem It Solves

This skill prevents informal governance decisions.
It ensures all actions are traceable and legitimate.
Structural clarity is maintained through formal process.

## B. Domain Scope

Applies to all formal decisions within TH or AE circles.
Scope is bounded by the unit's AZPO.
Cross-unit implications trigger inter-unit skill.

## C. Trigger Conditions

Triggered when a proposal is submitted to TH.
Also triggered by AE unit governance motions.
Any actor may trigger with a valid proposal form.

## D. Required Inputs

A written proposal with rationale.
Sponsorship from at least one TH member.
Current agreement registry state.

## E. Step-by-Step Process

Step 1: Submit proposal to TH facilitator.
Step 2: Facilitator validates format and completeness.
Step 3: Proposal enters consent round within 72 hours.

## F. Output Artifact

A recorded decision entry in the agreement registry.
Signed by facilitator and at least one witness.
Timestamped and versioned.

## G. Authority Boundary Check

Check that proposer has standing in the relevant circle.
Verify proposal does not override OSC decisions.
Confirm GAIA level does not exceed unit authority.

## H. Capture Resistance Check

No single actor can block or fast-track unilaterally.
At least 3 TH members must participate in consent round.
Facilitator role rotates — no permanent appointment.

## I. Failure Containment Logic

If consent round fails, proposal returns to drafting.
Facilitator logs the objection with rationale.
A second round may be called after 48-hour cooling.

## J. Expiry / Review Condition

Decision is reviewed annually or on triggering event.
TH may call early review by consent motion.
Expired decisions default to prior agreement version.

## K. Exit Compatibility Check

Departing members retain right to reference decisions made during tenure.
Decisions remain valid after member exit.
No retroactive revocation without consensus.

## L. Cross-Unit Interoperability Impact

Decisions affecting multiple units require inter-unit skill.
Shared resources governed by bilateral agreement.
OSC notified of all cross-unit decisions.

## OmniOne Walkthrough

TH member Alice proposes a change to the meeting cadence.
Facilitator Bob validates the proposal format.
Consent round is held; no reasoned objections received.
Decision is recorded in the agreement registry.

## Stress-Test Results

### 1. Capital Influx

Proposal for new resource allocation submitted. Consent round proceeds normally.

### 2. Emergency Crisis

Emergency proposals bypass standard 72-hour window with OSC approval.

### 3. Leadership Charisma Capture

Rotation of facilitator role prevents capture by charismatic leader.

### 4. High Conflict / Polarization

Objections are documented and addressed in revision cycle.

### 5. Large-Scale Replication

Each new unit instantiates its own agreement registry.

### 6. External Legal Pressure

External demands are treated as inputs to a new proposal, not override.

### 7. Sudden Exit of 30% of Participants

Quorum rules apply; decisions are suspended until quorum is restored.
"""

SAMPLE_SKILL_BETA = """\
---
name: test-skill-beta
description: "Beta test skill"
layer: 2
version: 0.1.0
depends_on: [test-skill-alpha]
---

# test-skill-beta

## A. Structural Problem It Solves

Builds on alpha to handle escalated decisions.
Prevents authority vacuum when alpha process is contested.
Provides clear escalation path.

## B. Domain Scope

Applies when alpha-level consent fails twice.
Scope includes all escalated TH decisions.
OSC is notified on entry.

## C. Trigger Conditions

Triggered when two consecutive consent rounds fail.
Also triggered by explicit escalation request from any TH member.
Facilitator may trigger on procedural breakdown.

## D. Required Inputs

Alpha-level decision record showing two failed rounds.
Written escalation rationale from requesting member.
Facilitator log of both prior rounds.

## E. Step-by-Step Process

Step 1: Facilitator packages the failure record.
Step 2: Package sent to OSC within 24 hours.
Step 3: OSC convenes within 72 hours to resolve.

## F. Output Artifact

OSC resolution memo with binding decision.
Distributed to all TH members and AE units affected.
Logged in agreement registry under escalated decisions.

## G. Authority Boundary Check

OSC authority supersedes TH for escalated matters.
Check that OSC quorum is met before resolution.
Resolution must align with Master Plan principles.

## H. Capture Resistance Check

OSC decisions require consensus not consent.
No member may abstain without documented reason.
Third-party witness required for all OSC sessions.

## I. Failure Containment Logic

If OSC fails to resolve, matter escalates to Steward Review.
Facilitator logs all proceedings.
Status quo maintained pending resolution.

## J. Expiry / Review Condition

OSC resolution reviewed at next annual cycle.
May be revisited if new material facts emerge.
TH may petition OSC for reconsideration by consensus.

## K. Exit Compatibility Check

Exiting members bound by OSC resolutions made during tenure.
New members inherit prior OSC resolutions.
No retroactive changes without full consensus.

## L. Cross-Unit Interoperability Impact

OSC resolutions bind all units within OmniOne.
Inter-unit implications documented in resolution memo.
AE units notified within 48 hours.

## OmniOne Walkthrough

TH fails to reach consent on resource allocation after two rounds.
Facilitator escalates to OSC with full failure record.
OSC convenes and reaches consensus resolution within 72 hours.
Resolution logged and distributed.

## Stress-Test Results

### 1. Capital Influx

Large capital influx triggers escalation when TH deadlocks.

### 2. Emergency Crisis

Emergency bypass available to OSC when time-sensitive.

### 3. Leadership Charisma Capture

OSC consensus requirement prevents single actor capture.

### 4. High Conflict / Polarization

OSC structured process de-escalates polarized deadlocks.

### 5. Large-Scale Replication

Each ecosystem maintains own OSC-equivalent for escalation.

### 6. External Legal Pressure

External legal demands processed through OSC resolution pathway.

### 7. Sudden Exit of 30% of Participants

OSC quorum rules adjusted for emergency membership gaps.
"""

MALFORMED_SKILL = """\
This file has no frontmatter at all.
Just some random text.
No YAML delimiters present.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_skill(tmp_path: Path, layer_dir: str, skill_dir: str, content: str) -> Path:
    """Write a SKILL.md into tmp_path/layer_dir/skill_dir/SKILL.md."""
    skill_path = tmp_path / layer_dir / skill_dir / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(content, encoding="utf-8")
    return skill_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadAll:
    async def test_load_all_populates_registry(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)

        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        assert registry.count >= 2
        assert "test-skill-alpha" in registry.all_names()
        assert "test-skill-beta" in registry.all_names()

    async def test_load_all_from_real_neos_core(self) -> None:
        """Integration test: load all 54 skills from the actual neos-core directory."""
        if not _NEOS_CORE.exists():
            pytest.skip(f"neos-core not found at {_NEOS_CORE}")

        registry = SkillRegistry()
        await registry.load_all(_NEOS_CORE)

        assert registry.count == 54, (
            f"Expected 54 skills, got {registry.count}. "
            f"Loaded: {registry.all_names()}"
        )

    async def test_partial_load_on_parse_error(self, tmp_path: Path) -> None:
        """A malformed SKILL.md is skipped; valid ones still load."""
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-01-test", "bad-skill", MALFORMED_SKILL)

        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        # Only the valid skill loads
        assert "test-skill-alpha" in registry.all_names()
        assert "bad-skill" not in registry.all_names()
        assert registry.count == 1


class TestIsLoaded:
    async def test_is_loaded_before_and_after(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        registry = SkillRegistry()

        assert registry.is_loaded is False
        await registry.load_all(tmp_path)
        assert registry.is_loaded is True


class TestGet:
    async def test_get_existing_skill(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        skill = registry.get("test-skill-alpha")
        assert skill.meta.name == "test-skill-alpha"
        assert skill.content.raw_text == SAMPLE_SKILL_ALPHA

    async def test_get_nonexistent_skill_raises(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        with pytest.raises(KeyError, match="nonexistent"):
            registry.get("nonexistent")

    async def test_get_meta(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        meta = registry.get_meta("test-skill-alpha")
        assert meta.name == "test-skill-alpha"
        assert meta.layer == 1
        assert meta.version == "0.1.0"
        assert meta.depends_on == []


class TestListByLayer:
    async def test_list_by_layer(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        layer1 = registry.list_by_layer(1)
        assert len(layer1) == 1
        assert layer1[0].name == "test-skill-alpha"

        layer2 = registry.list_by_layer(2)
        assert len(layer2) == 1
        assert layer2[0].name == "test-skill-beta"

    async def test_list_by_layer_empty(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        assert registry.list_by_layer(99) == []


class TestAllSkills:
    async def test_all_skills(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        skills = registry.all_skills()
        names = {s.name for s in skills}
        assert "test-skill-alpha" in names
        assert "test-skill-beta" in names


class TestAllNames:
    async def test_all_names(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        names = registry.all_names()
        # Should be sorted
        assert names == sorted(names)
        assert "test-skill-alpha" in names
        assert "test-skill-beta" in names


class TestCount:
    async def test_count(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        assert registry.count == 2


class TestGraph:
    async def test_graph_populated(self, tmp_path: Path) -> None:
        write_skill(tmp_path, "layer-01-test", "test-skill-alpha", SAMPLE_SKILL_ALPHA)
        write_skill(tmp_path, "layer-02-test", "test-skill-beta", SAMPLE_SKILL_BETA)
        registry = SkillRegistry()
        await registry.load_all(tmp_path)

        graph = registry.graph
        assert graph.has_skill("test-skill-alpha")
        assert graph.has_skill("test-skill-beta")
        # beta depends on alpha
        assert "test-skill-alpha" in graph.dependencies_of("test-skill-beta")
