"""Skill transition router for the NEOS governance agent.

Detects when a governance process should transition to another skill
based on tool calls and their outcomes. Transitions are data-driven
via TransitionPattern declarations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionPattern:
    """Declarative description of a skill-to-skill transition.

    Attributes
    ----------
    source_skill:
        Name of the currently active skill.
    trigger_tool:
        Tool name that triggers this transition, or ``None`` for
        non-tool-based transitions.
    trigger_status:
        Status value in tool args that triggers this transition,
        or ``None`` if any invocation of the tool suffices.
    trigger_condition:
        Human-readable description of when this fires.
    destination_skill:
        Skill to transition to, or ``None`` if the process is complete.
    """

    source_skill: str
    trigger_tool: str | None
    trigger_status: str | None
    trigger_condition: str
    destination_skill: str | None


# ---------------------------------------------------------------------------
# Default transition table
# ---------------------------------------------------------------------------

TRANSITION_PATTERNS: list[TransitionPattern] = [
    # Layer I — Agreement lifecycle
    TransitionPattern(
        "agreement-creation", "create_agreement_draft", None,
        "Agreement draft created, ready for ACT", "act-advice-phase",
    ),
    TransitionPattern(
        "agreement-review", "create_agreement_draft", None,
        "Review identifies amendment needed", "agreement-amendment",
    ),
    TransitionPattern(
        "agreement-amendment", "create_agreement_draft", None,
        "Amendment drafted, needs ACT", "act-advice-phase",
    ),

    # Layer III — ACT decision engine
    TransitionPattern(
        "act-advice-phase", "update_agreement_status", "consent",
        "Advice complete, entering consent", "act-consent-phase",
    ),
    TransitionPattern(
        "act-consent-phase", "update_agreement_status", "test",
        "Consent achieved, entering test", "act-test-phase",
    ),
    TransitionPattern(
        "act-consent-phase", "update_agreement_status", "active",
        "Consent achieved, adopted directly", None,
    ),
    TransitionPattern(
        "act-test-phase", "update_agreement_status", "active",
        "Test complete, adopted", None,
    ),

    # Layer IV — Resource request
    TransitionPattern(
        "resource-request", "create_proposal", None,
        "Request requires ACT process", "act-advice-phase",
    ),

    # Layer VI — Conflict / repair
    TransitionPattern(
        "harm-circle", "create_agreement_draft", None,
        "Harm acknowledged, repair needed", "repair-agreement",
    ),
    TransitionPattern(
        "escalation-triage", None, None,
        "Escalated to GAIA Level 4", "coaching-intervention",
    ),
    TransitionPattern(
        "escalation-triage", "triage_conflict", None,
        "Conflict triaged, routed to resolution", None,
    ),
    TransitionPattern(
        "nvc-dialogue", "create_conflict_case", None,
        "NVC dialogue initiated for conflict", "escalation-triage",
    ),

    # Layer X — Exit
    TransitionPattern(
        "voluntary-exit", None, None,
        "Exit initiated, commitments to unwind", "commitment-unwinding",
    ),
    TransitionPattern(
        "voluntary-exit", "create_exit_record", None,
        "Exit declared, beginning commitment unwinding", "commitment-unwinding",
    ),
    TransitionPattern(
        "commitment-unwinding", None, None,
        "All obligations resolved", "portable-record",
    ),

    # Layer VIII — Emergency
    TransitionPattern(
        "emergency-criteria-design", None, None,
        "Emergency declared", "crisis-coordination",
    ),
    TransitionPattern(
        "emergency-criteria-design", "declare_emergency", None,
        "Emergency criteria met, circuit breaker opening", "crisis-coordination",
    ),
    TransitionPattern(
        "crisis-coordination", None, None,
        "Emergency ends", "emergency-reversion",
    ),
    TransitionPattern(
        "emergency-reversion", None, None,
        "Authority reverted", "post-emergency-review",
    ),
]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


class SkillRouter:
    """Deterministic skill transition router.

    Examines tool call results against declared ``TransitionPattern``
    entries to decide whether the current governance process should
    move to a different skill.
    """

    def __init__(
        self,
        patterns: list[TransitionPattern] | None = None,
    ) -> None:
        self.patterns: list[TransitionPattern] = (
            patterns if patterns is not None else list(TRANSITION_PATTERNS)
        )

    def detect_transition(
        self,
        current_skill: str,
        tool_calls: list[dict],
        agent_response: str,
    ) -> str | None:
        """Determine if a skill transition should occur.

        Parameters
        ----------
        current_skill:
            Name of the currently active skill.
        tool_calls:
            List of tool call dicts, each with keys:
            ``name`` (str), ``args`` (dict), ``success`` (bool).
        agent_response:
            The agent's latest text response (reserved for future
            heuristic matching; not used by tool-based patterns).

        Returns
        -------
        str | None
            Destination skill name, or ``None`` if no transition
            applies (which can mean "process complete" when a pattern
            with ``destination_skill=None`` matches, or simply
            "stay in current skill").
        """
        for tc in tool_calls:
            # Skip failed tool calls
            if not tc.get("success", True):
                continue

            for p in self.patterns:
                if p.source_skill != current_skill:
                    continue
                if p.trigger_tool is None:
                    continue
                if p.trigger_tool != tc["name"]:
                    continue

                # Tool matches — check status constraint
                if p.trigger_status is not None:
                    if tc.get("args", {}).get("new_status") != p.trigger_status:
                        continue

                return p.destination_skill

        return None

    def add_pattern(self, pattern: TransitionPattern) -> None:
        """Append a custom transition pattern."""
        self.patterns.append(pattern)
