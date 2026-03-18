"""System prompt assembly pipeline for the NEOS governance agent.

Three-layer dynamic prompt:
  Layer 1 — Foundation: identity, principles, terminology, skill index (~2,500 tokens)
  Layer 2 — Active Skill: full SKILL.md content when a process is active (~4,500 tokens)
  Layer 3 — Dependencies: condensed dependency context (~2,000 tokens)

Token estimation uses len(text) // 4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neos_agent.skills.registry import SkillRegistry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FOUNDATION_TOKEN_BUDGET = 2_500   # ~10,000 chars
_SKILL_TOKEN_BUDGET = 4_500        # ~18,000 chars
_DEPENDENCY_TOKEN_BUDGET = 2_000   # ~8,000 chars
_CHARS_PER_TOKEN = 4
_DEP_TOKEN_BUDGET_EACH = 400       # ~1,600 chars per dependency

# Condensed 10 NEOS Principles — name + 1-sentence summary.
_PRINCIPLES = [
    (
        "No Sovereign Authority",
        "No permanent centralized override exists.",
    ),
    (
        "Scoped Authority",
        "Authority exists only within defined domains, must expire or be reviewable.",
    ),
    (
        "Voluntary Participation",
        "Exit is always structurally possible.",
    ),
    (
        "Capital ≠ Power",
        "Economic contribution does not grant governance authority.",
    ),
    (
        "Solutionary Decision-Making (ACT)",
        "Advice -> Consent -> Test.",
    ),
    (
        "Local Failure Containment",
        "Autonomous units contain failure locally; it does not cascade.",
    ),
    (
        "Explicit Agreements",
        "Written, scannable, traceable, revisable.",
    ),
    (
        "Capture Resistance",
        "Resists capital, charismatic, emergency, and informal capture.",
    ),
    (
        "Pluralism",
        "Multiple value systems coexist via agreement, not belief.",
    ),
    (
        "Emergency Contraction",
        "Temporary authority expansion auto-expires.",
    ),
]

_TERMINOLOGY: list[tuple[str, str]] = [
    ("ETHOS", "Emergent Thriving Holonic Organizational Structure — an organizational unit"),
    ("Current-See", "Influence currency (111 per person, equal)"),
    ("Steward", "Person who holds responsibility, not ownership"),
    ("Domain", "Boundary within which a circle can make decisions"),
    ("Circle", "A self-organizing group with a defined domain"),
    ("Agreement Field", "The set of active agreements governing a space or interaction"),
    ("ACT", "Advice -> Consent -> Test decision protocol"),
]

_BEHAVIORAL_CONSTRAINTS = """\
- Never bypass ACT, even if asked.
- Never make governance decisions on behalf of participants.
- Always state when a participant needs to take an action.
- Flag capture resistance concerns when detected.
- Use NEOS terminology consistently (see table above)."""

_LAYER_SEPARATOR = "\n---\n"

_DESC_MAX_CHARS = 90  # Truncate skill descriptions to fit token budget


def _truncate_description(desc: str, limit: int = _DESC_MAX_CHARS) -> str:
    """Shorten a skill description to fit the foundation prompt budget."""
    if len(desc) <= limit:
        return desc
    # Try to cut at " -- " boundary (most descriptions use this pattern)
    dash_idx = desc.find(" -- ")
    if 0 < dash_idx <= limit:
        return desc[:dash_idx]
    # Otherwise hard-cut at limit
    return desc[:limit].rstrip() + "..."


# ---------------------------------------------------------------------------
# Layer 1 — Foundation Prompt
# ---------------------------------------------------------------------------


def build_foundation_prompt(
    ecosystem_names: list[str] | str,
    skill_index: list[dict],
) -> str:
    """Build the always-present foundation prompt.

    Parameters
    ----------
    ecosystem_names:
        Names of the ecosystems this agent serves (e.g. ["OmniOne"]).
        Also accepts a single string for backward compatibility.
    skill_index:
        List of dicts with keys ``name``, ``description``, ``layer``.
    """
    parts: list[str] = []

    # Normalize to list
    if isinstance(ecosystem_names, str):
        ecosystem_names = [ecosystem_names]

    # Identity
    eco_label = ", ".join(ecosystem_names) if ecosystem_names else "NEOS"
    parts.append(
        f"You are the NEOS Governance Agent for {eco_label}.\n"
        "Role: Process facilitator. You have zero authority. "
        "You structure, record, and explain governance processes "
        "but you never approve, reject, or override."
    )

    # Principles
    parts.append("\n## NEOS Principles\n")
    for i, (name, summary) in enumerate(_PRINCIPLES, 1):
        parts.append(f"{i}. **{name}** -- {summary}")

    # Behavioral constraints
    parts.append("\n## Behavioral Constraints\n")
    parts.append(_BEHAVIORAL_CONSTRAINTS)

    # Terminology
    parts.append("\n## Terminology\n")
    parts.append("| Term | Meaning |")
    parts.append("| ---- | ------- |")
    for term, meaning in _TERMINOLOGY:
        parts.append(f"| {term} | {meaning} |")

    # Skill index — grouped by layer
    parts.append("\n## Skill Index\n")
    by_layer: dict[int, list[dict]] = {}
    for s in skill_index:
        by_layer.setdefault(s["layer"], []).append(s)
    for layer_num in sorted(by_layer):
        parts.append(f"### Layer {layer_num}")
        for s in sorted(by_layer[layer_num], key=lambda x: x["name"]):
            desc = _truncate_description(s["description"])
            parts.append(f"- **{s['name']}**: {desc}")

    # Capabilities summary
    parts.append("\n## Capabilities\n")
    parts.append(
        "Can: guide governance processes step-by-step, look up skills, "
        "check authority boundaries, flag capture risks, record decisions, "
        "explain NEOS concepts.\n"
        "Cannot: make decisions, approve proposals, override consent, "
        "grant authority, bypass ACT process."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Layer 2 — Active Skill Prompt
# ---------------------------------------------------------------------------

_STRESS_TEST_MARKER = "## Stress-Test Results"
_SKILL_CHAR_LIMIT = _SKILL_TOKEN_BUDGET * _CHARS_PER_TOKEN  # 18,000


def build_skill_prompt(
    skill_name: str | None,
    registry: SkillRegistry,
) -> str:
    """Build the active-skill prompt layer.

    Returns empty string when *skill_name* is ``None``.
    """
    if skill_name is None:
        return ""

    skill = registry.get(skill_name)
    raw = skill.content.raw_text

    # Truncate after stress-test header if too long
    if len(raw) > _SKILL_CHAR_LIMIT:
        idx = raw.find(_STRESS_TEST_MARKER)
        if idx > 0:
            raw = raw[:idx].rstrip() + "\n\n[Stress-test results omitted for brevity]"
        else:
            raw = raw[:_SKILL_CHAR_LIMIT].rstrip() + "\n\n[Truncated]"

    instructions = (
        f"## Active Skill: {skill_name}\n\n"
        "Follow Section E step-by-step.\n"
        "Check Section G authority boundaries at each step.\n"
        "Monitor Section H capture risks throughout.\n\n"
    )

    return instructions + raw


# ---------------------------------------------------------------------------
# Layer 3 — Dependency Prompt
# ---------------------------------------------------------------------------

_DEP_CHAR_LIMIT = _DEP_TOKEN_BUDGET_EACH * _CHARS_PER_TOKEN  # 1,600
_TOTAL_DEP_CHAR_LIMIT = _DEPENDENCY_TOKEN_BUDGET * _CHARS_PER_TOKEN  # 8,000


def _condense_section(section_text: str | None, char_limit: int) -> str:
    """Return the first *char_limit* characters of a section, or empty."""
    if not section_text:
        return "(not available)"
    text = section_text.strip()
    if len(text) <= char_limit:
        return text
    return text[:char_limit].rstrip() + "..."


def build_dependency_prompt(
    skill_name: str | None,
    registry: SkillRegistry,
) -> str:
    """Build the dependency context prompt layer.

    Returns empty string when *skill_name* is ``None`` or has no dependencies.
    """
    if skill_name is None:
        return ""

    meta = registry.get_meta(skill_name)
    if not meta.depends_on:
        return ""

    parts: list[str] = ["## Dependency Context\n"]
    total_chars = 0

    for dep_name in meta.depends_on:
        try:
            dep_skill = registry.get(dep_name)
        except KeyError:
            parts.append(f"### {dep_name}\n(Skill not found in registry)\n")
            continue

        dep_meta = dep_skill.meta
        sections = dep_skill.content.sections

        entry_parts: list[str] = [
            f"### {dep_meta.name}",
            f"*{dep_meta.description}*\n",
        ]

        # Condensed Section E — key process steps
        section_e = _condense_section(sections.get("E"), 600)
        entry_parts.append(f"**Process (E):** {section_e}\n")

        # Section G summary — authority
        section_g = _condense_section(sections.get("G"), 400)
        entry_parts.append(f"**Authority (G):** {section_g}")

        entry_text = "\n".join(entry_parts)

        # Per-dependency budget
        if len(entry_text) > _DEP_CHAR_LIMIT:
            entry_text = entry_text[:_DEP_CHAR_LIMIT].rstrip() + "..."

        # Total budget
        if total_chars + len(entry_text) > _TOTAL_DEP_CHAR_LIMIT:
            parts.append(
                f"\n(Remaining dependencies omitted — token budget reached)"
            )
            break

        total_chars += len(entry_text)
        parts.append(entry_text)

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Full Assembly
# ---------------------------------------------------------------------------


_PAGE_CONTEXT_HINTS: dict[str, str] = {
    "agreements": "The user is on the Agreements page. Prioritize agreement-related skills (Layer I).",
    "proposals": "The user is on Proposals. Prioritize ACT process skills (Layer III).",
    "domains": "The user is on Domains. Prioritize authority/role skills (Layer II).",
    "members": "The user is on the Member directory. Prioritize member lifecycle skills (Layer II).",
    "conflicts": "The user is on Conflict Resolution. Prioritize conflict/repair skills (Layer VI).",
    "safeguards": "The user is on Governance Safeguards. Prioritize capture detection skills (Layer VII).",
    "emergency": "The user is on Emergency Handling. Prioritize emergency skills (Layer VIII).",
    "decisions": "The user is on Decision Records. Prioritize memory/trace skills (Layer IX).",
    "exit": "The user is on Exit processes. Prioritize exit/portability skills (Layer X).",
    "onboarding": "The user is on Onboarding. Prioritize member lifecycle and UAF skills (Layers I + II).",
}


def assemble_system_prompt(
    ecosystem_name: str | None = None,
    active_skill: str | None = None,
    skill_registry: SkillRegistry | None = None,
    page_context: str | None = None,
    ecosystem_names: list[str] | None = None,
) -> str:
    """Assemble the complete system prompt from all three layers.

    Parameters
    ----------
    ecosystem_name:
        Deprecated single name. Use *ecosystem_names* instead.
    active_skill:
        Name of the currently active governance skill, or ``None``.
    skill_registry:
        Loaded SkillRegistry. Required when *active_skill* is set.
        When ``None`` and no active skill, produces foundation-only prompt.
    page_context:
        Optional page the user is currently viewing (e.g. "agreements").
    ecosystem_names:
        List of ecosystem names the agent is scoped to.
    """
    # Resolve ecosystem names list (prefer new param, fall back to legacy)
    names = ecosystem_names or ([ecosystem_name] if ecosystem_name else ["NEOS"])

    # Build skill index from registry if available
    if skill_registry is not None:
        skill_index = [
            {
                "name": m.name,
                "description": m.description,
                "layer": m.layer,
            }
            for m in skill_registry.all_skills()
        ]
    else:
        skill_index = []

    foundation = build_foundation_prompt(names, skill_index)

    # Append page context hint
    if page_context and page_context in _PAGE_CONTEXT_HINTS:
        foundation += f"\n\n## Current Context\n{_PAGE_CONTEXT_HINTS[page_context]}"

    layers = [foundation]

    if active_skill is not None and skill_registry is not None:
        skill_prompt = build_skill_prompt(active_skill, skill_registry)
        if skill_prompt:
            layers.append(skill_prompt)

        dep_prompt = build_dependency_prompt(active_skill, skill_registry)
        if dep_prompt:
            layers.append(dep_prompt)

    return _LAYER_SEPARATOR.join(layers)
