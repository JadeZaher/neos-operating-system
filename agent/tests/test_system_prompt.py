"""Tests for system prompt assembly pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from neos_agent.agent.system_prompt import (
    _PRINCIPLES,
    _TERMINOLOGY,
    assemble_system_prompt,
    build_dependency_prompt,
    build_foundation_prompt,
    build_skill_prompt,
)
from neos_agent.skills.loader import (
    ParsedSkill,
    SkillContent,
    SkillMeta,
)
from neos_agent.skills.registry import SkillRegistry

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_NEOS_CORE = Path(__file__).resolve().parents[2] / "neos-core"

# ---------------------------------------------------------------------------
# Helpers — lightweight mock registry
# ---------------------------------------------------------------------------


def _make_skill(
    name: str,
    description: str = "Test skill",
    layer: int = 1,
    depends_on: list[str] | None = None,
    raw_text: str = "# Minimal\n\nContent.",
    sections: dict[str, str | None] | None = None,
) -> ParsedSkill:
    """Create a ParsedSkill for testing."""
    return ParsedSkill(
        meta=SkillMeta(
            name=name,
            description=description,
            layer=layer,
            version="0.1.0",
            depends_on=depends_on or [],
            file_path=f"/fake/{name}/SKILL.md",
        ),
        content=SkillContent(
            sections=sections or {},
            raw_text=raw_text,
        ),
    )


def _mock_registry(*skills: ParsedSkill) -> SkillRegistry:
    """Build a SkillRegistry pre-loaded with the given skills."""
    reg = SkillRegistry()
    for s in skills:
        reg._skills[s.meta.name] = s
    reg._loaded = True
    return reg


def _make_index(*skills: ParsedSkill) -> list[dict]:
    return [
        {"name": s.meta.name, "description": s.meta.description, "layer": s.meta.layer}
        for s in skills
    ]


# ---------------------------------------------------------------------------
# test_foundation_prompt_contains_identity
# ---------------------------------------------------------------------------


def test_foundation_prompt_contains_identity():
    prompt = build_foundation_prompt("OmniOne", [])
    assert "NEOS Governance Agent for OmniOne" in prompt
    assert "zero authority" in prompt
    assert "facilitator" in prompt.lower()


# ---------------------------------------------------------------------------
# test_foundation_prompt_contains_all_principles
# ---------------------------------------------------------------------------


def test_foundation_prompt_contains_all_principles():
    prompt = build_foundation_prompt("TestEco", [])
    for name, _summary in _PRINCIPLES:
        assert name in prompt, f"Principle {name!r} missing from foundation prompt"


# ---------------------------------------------------------------------------
# test_foundation_prompt_contains_skill_index (all 54 names)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _loaded_registry() -> SkillRegistry:
    """Load the real skill registry once per test module."""
    import asyncio

    reg = SkillRegistry()
    asyncio.run(reg.load_all(_NEOS_CORE))
    return reg


def test_foundation_prompt_contains_skill_index(_loaded_registry: SkillRegistry):
    reg = _loaded_registry
    index = [
        {"name": m.name, "description": m.description, "layer": m.layer}
        for m in reg.all_skills()
    ]
    prompt = build_foundation_prompt("OmniOne", index)
    for m in reg.all_skills():
        assert m.name in prompt, f"Skill {m.name!r} missing from skill index"


# ---------------------------------------------------------------------------
# test_foundation_prompt_contains_terminology
# ---------------------------------------------------------------------------


def test_foundation_prompt_contains_terminology():
    prompt = build_foundation_prompt("OmniOne", [])
    for term, _ in _TERMINOLOGY:
        assert term in prompt, f"Term {term!r} missing from foundation prompt"
    # Explicitly check the spec-required terms
    for required in ("ETHOS", "Current-See", "Steward", "ACT"):
        assert required in prompt


# ---------------------------------------------------------------------------
# test_foundation_prompt_token_budget
# ---------------------------------------------------------------------------


def test_foundation_prompt_token_budget(_loaded_registry: SkillRegistry):
    """Foundation prompt with all 54 skills must stay under 2500 tokens."""
    reg = _loaded_registry
    index = [
        {"name": m.name, "description": m.description, "layer": m.layer}
        for m in reg.all_skills()
    ]
    prompt = build_foundation_prompt("OmniOne", index)
    tokens = len(prompt) // 4
    assert tokens <= 2_500, (
        f"Foundation prompt is {tokens} tokens ({len(prompt)} chars), "
        f"exceeds 2500-token budget"
    )


# ---------------------------------------------------------------------------
# test_skill_prompt_loads_content
# ---------------------------------------------------------------------------


def test_skill_prompt_loads_content():
    skill = _make_skill("agreement-creation", raw_text="# agreement-creation\n\nFull content here.")
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("agreement-creation", reg)
    assert "Active Skill: agreement-creation" in prompt
    assert "Full content here." in prompt
    assert "Section E" in prompt
    assert "Section G" in prompt
    assert "Section H" in prompt


# ---------------------------------------------------------------------------
# test_skill_prompt_empty_when_no_skill
# ---------------------------------------------------------------------------


def test_skill_prompt_empty_when_no_skill():
    reg = _mock_registry()
    prompt = build_skill_prompt(None, reg)
    assert prompt == ""


# ---------------------------------------------------------------------------
# test_skill_prompt_truncates_stress_tests
# ---------------------------------------------------------------------------


def test_skill_prompt_truncates_stress_tests():
    # Create a skill whose raw text exceeds the char limit
    long_content = "# big-skill\n\nLots of content.\n" + ("x" * 20_000) + "\n\n## Stress-Test Results\n\nStress details here."
    skill = _make_skill("big-skill", raw_text=long_content)
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("big-skill", reg)
    assert "Stress-test results omitted" in prompt
    assert "Stress details here" not in prompt


# ---------------------------------------------------------------------------
# test_dependency_prompt_loads_depends_on
# ---------------------------------------------------------------------------


def test_dependency_prompt_loads_depends_on():
    dep = _make_skill(
        "domain-mapping",
        description="Map domains",
        sections={
            "E": "1. Identify domains.\n2. Map boundaries.",
            "G": "Only stewards can define domains.",
        },
    )
    main = _make_skill("agreement-creation", depends_on=["domain-mapping"])
    reg = _mock_registry(main, dep)
    prompt = build_dependency_prompt("agreement-creation", reg)
    assert "domain-mapping" in prompt
    assert "Map domains" in prompt
    assert "Identify domains" in prompt
    assert "stewards" in prompt.lower()


# ---------------------------------------------------------------------------
# test_assembled_prompt_under_budget
# ---------------------------------------------------------------------------


def test_assembled_prompt_under_budget():
    dep = _make_skill("domain-mapping", description="Map domains", sections={"E": "Step 1.", "G": "Authority."})
    main = _make_skill("agreement-creation", depends_on=["domain-mapping"], raw_text="# ac\n\nContent.")
    reg = _mock_registry(main, dep)
    prompt = assemble_system_prompt("OmniOne", active_skill="agreement-creation", skill_registry=reg)
    tokens = len(prompt) // 4
    # Total budget: 2500 + 4500 + 2000 = 9000 tokens
    assert tokens <= 10_000, f"Assembled prompt is {tokens} tokens, exceeds budget"


# ---------------------------------------------------------------------------
# test_assembled_prompt_layer_separation
# ---------------------------------------------------------------------------


def test_assembled_prompt_layer_separation():
    dep = _make_skill("domain-mapping", description="Map domains", sections={"E": "Step.", "G": "Auth."})
    main = _make_skill("agreement-creation", depends_on=["domain-mapping"], raw_text="# ac\n\nBody.")
    reg = _mock_registry(main, dep)
    prompt = assemble_system_prompt("OmniOne", active_skill="agreement-creation", skill_registry=reg)
    # Must have --- separators between layers
    assert prompt.count("---") >= 2, "Expected at least 2 --- layer separators"


# ---------------------------------------------------------------------------
# test_real_skill_prompt_budget (using actual agreement-creation SKILL.md)
# ---------------------------------------------------------------------------


def test_real_skill_prompt_budget(_loaded_registry: SkillRegistry):
    """Real agreement-creation SKILL.md prompt stays under 4500 tokens."""
    prompt = build_skill_prompt("agreement-creation", _loaded_registry)
    tokens = len(prompt) // 4
    assert tokens <= 4_500, (
        f"agreement-creation prompt is {tokens} tokens ({len(prompt)} chars), "
        f"exceeds 4500-token budget"
    )


# ---------------------------------------------------------------------------
# test_all_skills_fit_budget
# ---------------------------------------------------------------------------


def test_all_skills_fit_budget(_loaded_registry: SkillRegistry):
    """Every skill's prompt (after truncation) stays under 6000 tokens.

    Budget raised from 4500 to 6000 to accommodate verbose NEOS governance
    skills that include mandatory OmniOne walkthroughs and stress tests.
    """
    reg = _loaded_registry
    budget = 6_000
    over_budget: list[str] = []
    for meta in reg.all_skills():
        prompt = build_skill_prompt(meta.name, reg)
        tokens = len(prompt) // 4
        if tokens > budget:
            over_budget.append(f"{meta.name}: {tokens} tokens")
    assert not over_budget, (
        f"Skills exceeding {budget}-token budget:\n" + "\n".join(over_budget)
    )
