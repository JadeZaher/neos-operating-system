"""Tests for system prompt assembly pipeline."""

from __future__ import annotations

import logging
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
    assert "personal governance operator" in prompt
    assert "Carry out a clear, permitted request through the tools" in prompt
    assert "never invent their preference or decide for the group" in prompt
    assert "Before describing a record's current state" in prompt
    assert "Never infer its live state from the question" in prompt


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
    """Foundation prompt with all 54 skills must stay under 3300 tokens.

    The nominal foundation budget is 2,500 tokens (a soft warn-only target
    inside ``build_foundation_prompt``). The ceiling has been raised twice
    by design: once for the Global Rules block (authority scope, 30-day
    wind-down, capture taxonomy, federation extensibility), and once for
    the Tool Use Protocol section (sequencing rules to prevent out-of-order
    tool calls). Both additions are repaid many times over by the per-skill
    Layer 2 strip and by reduced failure-rate / retry tokens downstream.
    The hard ceiling enforced here is 3,300 tokens.
    """
    reg = _loaded_registry
    index = [
        {"name": m.name, "description": m.description, "layer": m.layer}
        for m in reg.all_skills()
    ]
    prompt = build_foundation_prompt("OmniOne", index)
    tokens = len(prompt) // 4
    assert tokens <= 3_300, (
        f"Foundation prompt is {tokens} tokens ({len(prompt)} chars), "
        f"exceeds 3300-token hard ceiling"
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
# test_build_skill_prompt_strips_section_a
# ---------------------------------------------------------------------------


def test_build_skill_prompt_strips_section_a():
    """Section A content is unconditionally stripped at runtime."""
    raw = (
        "---\nname: x\n---\n\n"
        "# big-skill\n\n"
        "## A. Structural Problem It Solves\n\n"
        "Section A body text that must not appear in the prompt.\n\n"
        "## C. Trigger Conditions\n\nFire when needed.\n\n"
        "## E. Step-by-Step Process\n\n1. Go.\n"
    )
    skill = _make_skill("strip-a-skill", raw_text=raw)
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("strip-a-skill", reg)
    assert "Section A body text" not in prompt
    assert "Structural Problem It Solves" not in prompt
    # Surrounding sections survive.
    assert "Trigger Conditions" in prompt
    assert "Step-by-Step Process" in prompt


# ---------------------------------------------------------------------------
# test_build_skill_prompt_strips_section_b
# ---------------------------------------------------------------------------


def test_build_skill_prompt_strips_section_b():
    """Section B content is unconditionally stripped at runtime."""
    raw = (
        "---\nname: x\n---\n\n"
        "# big-skill\n\n"
        "## A. Structural Problem It Solves\n\nAlpha.\n\n"
        "## B. Domain Scope\n\n"
        "Section B body text that must not appear in the prompt.\n\n"
        "## C. Trigger Conditions\n\nFire when needed.\n"
    )
    skill = _make_skill("strip-b-skill", raw_text=raw)
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("strip-b-skill", reg)
    assert "Section B body text" not in prompt
    assert "Domain Scope" not in prompt
    assert "Trigger Conditions" in prompt


# ---------------------------------------------------------------------------
# test_build_skill_prompt_strips_omnione_walkthrough
# ---------------------------------------------------------------------------


def test_build_skill_prompt_strips_omnione_walkthrough():
    """OmniOne Walkthrough section is unconditionally stripped."""
    raw = (
        "---\nname: x\n---\n\n"
        "# big-skill\n\n"
        "## C. Trigger Conditions\n\nFire.\n\n"
        "## E. Step-by-Step Process\n\n1. Go.\n\n"
        "## OmniOne Walkthrough\n\n"
        "Walkthrough body text that must not appear.\n\n"
        "## Stress-Test Results\n\nStress body.\n"
    )
    skill = _make_skill("strip-omnione-skill", raw_text=raw)
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("strip-omnione-skill", reg)
    assert "Walkthrough body text" not in prompt
    assert "OmniOne Walkthrough" not in prompt
    # Other operational content survives.
    assert "Step-by-Step Process" in prompt


# ---------------------------------------------------------------------------
# test_build_skill_prompt_strips_stress_test
# ---------------------------------------------------------------------------


def test_build_skill_prompt_strips_stress_test():
    """Stress-Test Results section is unconditionally stripped (no
    truncation placeholder)."""
    raw = (
        "---\nname: x\n---\n\n"
        "# big-skill\n\n"
        "## C. Trigger Conditions\n\nFire.\n\n"
        "## E. Step-by-Step Process\n\n1. Go.\n\n"
        "## Stress-Test Results\n\n"
        "Stress test narrative that must not appear.\n"
    )
    skill = _make_skill("strip-stress-skill", raw_text=raw)
    reg = _mock_registry(skill)
    prompt = build_skill_prompt("strip-stress-skill", reg)
    assert "Stress test narrative" not in prompt
    assert "Stress-Test Results" not in prompt
    assert "Step-by-Step Process" in prompt


# ---------------------------------------------------------------------------
# test_foundation_contains_global_rules
# ---------------------------------------------------------------------------


def test_foundation_contains_global_rules():
    """The foundation prompt now exposes the lifted ``Global Rules`` block."""
    prompt = build_foundation_prompt(["OmniOne"], [])
    assert "## Global Rules" in prompt
    assert "Capture taxonomy" in prompt
    assert "30-day exit wind-down" in prompt
    assert "Authority scope" in prompt
    assert "Layer V federation extensibility" in prompt


# ---------------------------------------------------------------------------
# test_act_guide_follows_the_lifecycle_table
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("move, line", [
    (dict(source="advice", target="consent", gate="advice", automatic=True),
     "- advice -> consent: by itself once the advice rounds it needs have advice."),
    (dict(source="advice", target="consent", gate="advice"),
     "- advice -> consent: the author or a steward moves it, once the advice rounds it needs have advice."),
    (dict(source="advice", target="consent", gate="advice", proposer_until_deadline=True),
     "- advice -> consent: the author moves it, once the advice rounds it needs have advice; another steward only "
     "after the advice deadline has passed and the author has not (no deadline: only the author)."),
    (dict(source="test", target="ratified", gate="test", steward_only=True),
     "- test -> ratified: a steward who did not write it confirms it once the test evidence is in."),
])
def test_act_guide_follows_the_lifecycle_table(monkeypatch, move, line):
    """The prompt's ACT guide is generated from PROPOSAL_LIFECYCLE, so an owner's table edit reaches the assistant."""
    from neos_agent.agent import system_prompt
    from neos_agent.services.act_gates import Lifecycle, Move

    monkeypatch.setattr(system_prompt, "PROPOSAL_LIFECYCLE", Lifecycle(moves=(Move(**move),), withdrawn="withdrawn"))
    prompt = build_foundation_prompt(["OmniOne"], [])
    assert line in prompt
    # Only a steward-confirmed move brings the "another steward confirms" guidance; only the proposer's
    # advice close brings the ADVICE_CLOSE_PROPOSER_ONLY guidance.
    assert ("another member the moderator role" in prompt) is bool(move.get("steward_only"))
    assert ("ADVICE_CLOSE_PROPOSER_ONLY" in prompt) is bool(move.get("proposer_until_deadline"))


# ---------------------------------------------------------------------------
# test_foundation_budget_warning_logged
# ---------------------------------------------------------------------------


def test_foundation_budget_warning_logged(caplog):
    """A foundation prompt that exceeds the soft budget logs a warning."""
    # Build a skill index that bloats the foundation prompt well past
    # the 2,500-token (~10,000-char) budget.
    big_index = [
        {
            "name": f"skill-{i:03d}",
            "description": "x" * 200,  # description gets truncated, but names accumulate
            "layer": (i % 10) + 1,
        }
        for i in range(500)
    ]
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="neos_agent.agent.system_prompt"):
        prompt = build_foundation_prompt(["OmniOne"], big_index)
    assert len(prompt) // 4 > 2_500, "test setup did not exceed budget"
    warnings = [
        rec for rec in caplog.records
        if rec.levelno == logging.WARNING
        and "Foundation prompt" in rec.getMessage()
    ]
    assert warnings, "Expected a budget warning to be logged"


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


def test_runtime_lifecycle_policy_follows_and_overrides_stale_skill_prose():
    stale = "The advice window closes automatically at the deadline."
    reg = _mock_registry(_make_skill("act-advice-phase", raw_text=stale))
    prompt = assemble_system_prompt(active_skill="act-advice-phase", skill_registry=reg, response_mode="skill")
    assert stale in prompt
    assert prompt.index("## Current application policy (authoritative)") > prompt.index(stale)
    assert prompt.rfind("Advice never ends by itself") > prompt.index(stale)
    assert "Current state does not prove who changed it or why" in prompt


def test_real_advice_skill_and_runtime_agree_on_overdue_advice(_loaded_registry):
    from neos_agent.services.act_gates import PROPOSAL_LIFECYCLE

    assert PROPOSAL_LIFECYCLE.automatic_move("advice") is None
    closure = next(move for move in PROPOSAL_LIFECYCLE.moves if (move.source, move.target) == ("advice", "consent"))
    assert closure.proposer_until_deadline and closure.gate == "advice"

    skill = build_skill_prompt("act-advice-phase", _loaded_registry)
    prompt = assemble_system_prompt(
        active_skill="act-advice-phase", skill_registry=_loaded_registry, response_mode="skill",
    )
    assert "members can still submit advice while the proposal remains in Advice" in skill
    assert "another steward may close it only after the recorded advice deadline has passed" in skill
    assert "With no deadline, only the proposer can close it" in skill
    assert "A deadline is a reminder" in skill
    assert "Advice never ends by itself" in prompt
    for text in (skill, prompt):
        assert "No late advice is accepted" not in text
        assert "At the deadline, the advice window closes" not in text
        assert "hard deadline" not in text

    consent = build_skill_prompt("act-consent-phase", _loaded_registry)
    assert "A passed deadline alone does not start Consent" in consent
    asset = (_NEOS_CORE / "layer-03-act-engine/act-advice-phase/assets/advice-log-template.yaml").read_text(encoding="utf-8")
    assert "actual closure date; a deadline alone does not close advice" in asset


def test_platform_help_uses_verified_profile_controls_and_bounded_routes():
    prompt = assemble_system_prompt(response_mode="platform")
    assert "sidebar [Me](/me)" in prompt
    assert "choose the Profile tab" in prompt
    assert "Display name textbox, then press Save profile" in prompt
    assert "immediately editable" in prompt
    assert "[Messaging](/messaging)" in prompt
    assert "say you do not know the exact steps" in prompt
    assert "Never guess button labels, menus, tabs, or routes" in prompt


def test_real_proposal_skill_qualifies_formal_checklists_for_executable_app_drafts(_loaded_registry):
    skill = build_skill_prompt("proposal-creation", _loaded_registry)
    prompt = assemble_system_prompt(active_skill="proposal-creation", skill_registry=_loaded_registry, response_mode="skill")
    assert "formal proposal readiness inputs" in skill
    assert "Current NEOS app adapter: draft and opening for advice" in skill
    assert "Do not ask for a reason or domain before creating this app draft" in skill
    assert "Reason not yet provided by the member." in skill
    assert "domain-creation checklist is not a proposal-draft prerequisite" in skill
    assert skill.index("Current NEOS app adapter") < skill.index("Formal readiness and later governance process")
    assert "Neither a missing reason nor an unchosen domain blocks this app draft" in prompt
    assert "complete every explicitly requested read" in prompt.lower()
    asset = (_NEOS_CORE / "layer-03-act-engine/proposal-creation/assets/proposal-template.yaml").read_text(encoding="utf-8")
    assert "optional for an app draft" in asset


@pytest.mark.parametrize("mode, expected", [
    ("platform", "Answer as platform help"), ("framework", "Answer a governance question directly"),
])
def test_direct_context_keeps_tools_and_exit_rules_without_loading_a_skill(mode, expected):
    reg = _mock_registry(_make_skill("voluntary-exit", raw_text="UNSELECTED SKILL BODY"))
    prompt = assemble_system_prompt(skill_registry=reg, response_mode=mode)
    assert expected in prompt and "UNSELECTED SKILL BODY" not in prompt
    assert "leaving is voluntary and has no penalty" in prompt
    assert "portable copy of your records" in prompt
    assert "When several ecosystems are selected, ask WHICH ECOSYSTEM" in prompt
    assert "An unspecified date" in prompt and "first Saturday" in prompt
