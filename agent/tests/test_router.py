"""Tests for the skill transition router."""

from __future__ import annotations

import pytest

from neos_agent.agent.router import (
    TRANSITION_PATTERNS,
    SkillRouter,
    TransitionPattern,
)


@pytest.fixture
def router() -> SkillRouter:
    """Router with default transition patterns."""
    return SkillRouter()


# ---------------------------------------------------------------------------
# test_transition_agreement_to_advice
# ---------------------------------------------------------------------------


def test_transition_agreement_to_advice(router: SkillRouter):
    """After create_agreement_draft in agreement-creation -> act-advice-phase."""
    result = router.detect_transition(
        current_skill="agreement-creation",
        tool_calls=[{"name": "create_agreement_draft", "args": {}, "success": True}],
        agent_response="",
    )
    assert result == "act-advice-phase"


# ---------------------------------------------------------------------------
# test_transition_advice_to_consent
# ---------------------------------------------------------------------------


def test_transition_advice_to_consent(router: SkillRouter):
    """After update_agreement_status(consent) in advice -> act-consent-phase."""
    result = router.detect_transition(
        current_skill="act-advice-phase",
        tool_calls=[
            {
                "name": "update_agreement_status",
                "args": {"new_status": "consent"},
                "success": True,
            }
        ],
        agent_response="",
    )
    assert result == "act-consent-phase"


# ---------------------------------------------------------------------------
# test_transition_consent_to_test
# ---------------------------------------------------------------------------


def test_transition_consent_to_test(router: SkillRouter):
    """After update_agreement_status(test) -> act-test-phase."""
    result = router.detect_transition(
        current_skill="act-consent-phase",
        tool_calls=[
            {
                "name": "update_agreement_status",
                "args": {"new_status": "test"},
                "success": True,
            }
        ],
        agent_response="",
    )
    assert result == "act-test-phase"


# ---------------------------------------------------------------------------
# test_transition_consent_to_adopted
# ---------------------------------------------------------------------------


def test_transition_consent_to_adopted(router: SkillRouter):
    """After update_agreement_status(active) in consent -> None (process complete)."""
    result = router.detect_transition(
        current_skill="act-consent-phase",
        tool_calls=[
            {
                "name": "update_agreement_status",
                "args": {"new_status": "active"},
                "success": True,
            }
        ],
        agent_response="",
    )
    assert result is None


# ---------------------------------------------------------------------------
# test_no_transition_mid_process
# ---------------------------------------------------------------------------


def test_no_transition_mid_process(router: SkillRouter):
    """During normal operation with no matching tool calls -> None (stay)."""
    result = router.detect_transition(
        current_skill="act-advice-phase",
        tool_calls=[
            {"name": "some_other_tool", "args": {}, "success": True}
        ],
        agent_response="Just providing advice.",
    )
    assert result is None


# ---------------------------------------------------------------------------
# test_failed_tool_ignored
# ---------------------------------------------------------------------------


def test_failed_tool_ignored(router: SkillRouter):
    """Failed tool call should not trigger transition."""
    result = router.detect_transition(
        current_skill="agreement-creation",
        tool_calls=[
            {"name": "create_agreement_draft", "args": {}, "success": False}
        ],
        agent_response="",
    )
    assert result is None


# ---------------------------------------------------------------------------
# test_transition_exit_chain
# ---------------------------------------------------------------------------


def test_transition_exit_chain():
    """voluntary-exit -> commitment-unwinding (non-tool pattern not triggered by detect)."""
    # Non-tool-based transitions (trigger_tool=None) are not matched
    # by detect_transition, which only checks tool calls.
    # This tests that the pattern data exists for external use.
    router = SkillRouter()
    exit_patterns = [
        p for p in router.patterns
        if p.source_skill == "voluntary-exit"
    ]
    assert len(exit_patterns) == 2
    # Both patterns lead to commitment-unwinding
    assert all(p.destination_skill == "commitment-unwinding" for p in exit_patterns)
    # One is non-tool-based, one uses create_exit_record
    trigger_tools = {p.trigger_tool for p in exit_patterns}
    assert None in trigger_tools
    assert "create_exit_record" in trigger_tools

    # The detect_transition method returns None because no tool call matches
    result = router.detect_transition(
        current_skill="voluntary-exit",
        tool_calls=[],
        agent_response="Exit initiated.",
    )
    assert result is None


# ---------------------------------------------------------------------------
# test_emergency_chain
# ---------------------------------------------------------------------------


def test_emergency_chain():
    """Emergency chain: criteria -> crisis -> reversion -> review exists in patterns."""
    router = SkillRouter()
    chain = {
        "emergency-criteria-design": "crisis-coordination",
        "crisis-coordination": "emergency-reversion",
        "emergency-reversion": "post-emergency-review",
    }
    for source, destination in chain.items():
        matches = [
            p for p in router.patterns
            if p.source_skill == source and p.destination_skill == destination
        ]
        assert len(matches) >= 1, (
            f"Expected pattern {source} -> {destination}"
        )


# ---------------------------------------------------------------------------
# test_custom_pattern_added
# ---------------------------------------------------------------------------


def test_custom_pattern_added(router: SkillRouter):
    """add_pattern works and new pattern is used in detection."""
    custom = TransitionPattern(
        source_skill="custom-skill",
        trigger_tool="custom_tool",
        trigger_status=None,
        trigger_condition="Custom trigger",
        destination_skill="another-skill",
    )
    router.add_pattern(custom)

    result = router.detect_transition(
        current_skill="custom-skill",
        tool_calls=[{"name": "custom_tool", "args": {}, "success": True}],
        agent_response="",
    )
    assert result == "another-skill"


# ---------------------------------------------------------------------------
# test_unknown_skill_no_transition
# ---------------------------------------------------------------------------


def test_unknown_skill_no_transition(router: SkillRouter):
    """A skill not in any pattern produces no transition."""
    result = router.detect_transition(
        current_skill="nonexistent-skill-xyz",
        tool_calls=[{"name": "any_tool", "args": {}, "success": True}],
        agent_response="",
    )
    assert result is None
