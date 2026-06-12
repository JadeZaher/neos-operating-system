"""SKILL.md parser — produces SkillSpec IR from markdown source.

Reuses parsing patterns from neos_agent.skills.loader for frontmatter and
section extraction, then enriches with structured parsing of D (inputs),
E (steps), and the constraint/invariant sections.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..ir import (
    CaptureVector,
    ConstraintSpec,
    ExitRule,
    FailureMode,
    InputSpec,
    InteropRule,
    OutputSpec,
    ReviewConfig,
    SkillSpec,
    StepSpec,
)

# ---------------------------------------------------------------------------
# Frontmatter parsing (from skills/loader.py)
# ---------------------------------------------------------------------------


def _parse_frontmatter(content: str) -> tuple[dict[str, object], list[str]]:
    """Extract YAML frontmatter between --- delimiters."""
    lines = content.split("\n")
    delimiters: list[int] = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            delimiters.append(i)
            if len(delimiters) == 2:
                break
    if len(delimiters) < 2:
        return {}, ["Missing YAML frontmatter"]

    fm_lines = lines[delimiters[0] + 1 : delimiters[1]]
    frontmatter: dict[str, object] = {}
    for line in fm_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if value == "[]":
            frontmatter[key] = []
        elif value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            frontmatter[key] = [it.strip().strip("\"'") for it in items if it.strip()]
        else:
            frontmatter[key] = value
    return frontmatter, []


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

SECTION_HEADERS = [
    ("A", "Structural Problem It Solves"),
    ("B", "Domain Scope"),
    ("C", "Trigger Conditions"),
    ("D", "Required Inputs"),
    ("E", "Step-by-Step Process"),
    ("F", "Output Artifact"),
    ("G", "Authority Boundary Check"),
    ("H", "Capture Resistance Check"),
    ("I", "Failure Containment Logic"),
    ("J", "Expiry / Review Condition"),
    ("K", "Exit Compatibility Check"),
    ("L", "Cross-Unit Interoperability Impact"),
]

_SECTION_STOP_RE = re.compile(
    r"^#{1,3}\s+(?:[A-L][\.\:\)]|OmniOne|Stress)", re.IGNORECASE
)


def _extract_sections(content: str) -> dict[str, str | None]:
    """Extract all 12 sections (A-L) into a dict keyed by letter."""
    lines = content.split("\n")
    sections: dict[str, str | None] = {}
    for letter, title in SECTION_HEADERS:
        pattern = re.compile(
            rf"^#+\s*{re.escape(letter)}[\.\:\)]\s*{re.escape(title)}",
            re.IGNORECASE,
        )
        found_idx = None
        for i, line in enumerate(lines):
            if pattern.search(line):
                found_idx = i
                break
        if found_idx is not None:
            content_lines: list[str] = []
            in_code_fence = False
            for j in range(found_idx + 1, len(lines)):
                if _SECTION_STOP_RE.match(lines[j]):
                    break
                # Track code fences so we skip their content
                stripped = lines[j].strip()
                if stripped.startswith("```") or stripped.startswith("~~~"):
                    in_code_fence = not in_code_fence
                    continue
                if in_code_fence:
                    continue
                content_lines.append(lines[j])
            sections[letter] = "\n".join(content_lines)
        else:
            sections[letter] = None
    return sections


# ---------------------------------------------------------------------------
# Structured section parsers
# ---------------------------------------------------------------------------

# Pattern for inputs in section D: **Name**: description
# (The leading "- " is stripped by splitting, so match from start)
_INPUT_BULLET = re.compile(
    r"^\*?\*(.+?)\*?\*\s*[:：]\s*(.+)", re.MULTILINE
)
# Also match **Name** (description) — parenthetical
_INPUT_PAREN = re.compile(
    r"^\*?\*(.+?)\*?\*\s*\((.+?)\)", re.MULTILINE
)

# Pattern for steps in section E: N. **Title.** Description
_STEP_PATTERN = re.compile(
    r"^\d+\.\s+\*\*(.+?)\*\*\.?\s*(.*)", re.MULTILINE
)

# Pattern for timeline in steps: "Timeline: X days" or "Timeline: X-Y days"
_TIMELINE_PAT = re.compile(r"[Tt]imeline:\s*(.+)", re.MULTILINE)


def _parse_inputs(section_text: str | None) -> list[InputSpec]:
    """Parse section D into list of InputSpec."""
    if not section_text:
        return []
    inputs: list[InputSpec] = []
    # Split on bullet points (- or * or numbered list)
    bullets = re.split(r"\n\s*[-*]\s+|\n\s*\d+\.\s+", section_text)
    for bullet in bullets:
        bullet = bullet.strip()
        if not bullet:
            continue
        m = _INPUT_BULLET.match(bullet)
        if not m:
            m = _INPUT_PAREN.match(bullet)
        if m:
            name = m.group(1).strip()
            desc = m.group(2).strip()
            required = _is_input_required(name, desc, section_text)
            type_hint = _infer_type_hint(name, desc)
            inputs.append(InputSpec(
                name=_snake_case(name),
                description=desc,
                type_hint=type_hint,
                required=required,
            ))
    return inputs


# ---- Type inference heuristics (gap #1) ----

# Identity/name patterns: words that contain "id" but are NOT UUID identifiers
_NON_ID_PATTERNS = re.compile(
    r'(?:identity|video|audio|provide|evidence|consideration|'
    r'confidential|incident|accident|president|residence|knowledge|'
    r'guide|divide|bride|slide|tide|ride|side|hide|wide)',
    re.IGNORECASE,
)

# Patterns that indicate type hints from field name
_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r'(?:^|_)(?:date|day|timeline|deadline|schedule)(?:_|$)', re.IGNORECASE), 'date'),
    (re.compile(r'(?:^|_)(?:count|amount|number|score|total|quantity|threshold|limit)(?:_|$)', re.IGNORECASE), 'int'),
    (re.compile(r'(?:^|_)(?:flag|is_|has_|enabled|active|locked|archived|approved)(?:_|$)', re.IGNORECASE), 'bool'),
    (re.compile(r'(?:^|_)(?:list|items|entries|members|parties|partners|collection|array|co_sponsors|sponsors)(?:_|$)', re.IGNORECASE), 'list[str]'),
    (re.compile(r'(?:^|_)(?:config|settings|metadata|options|properties)(?:_|$)', re.IGNORECASE), 'dict'),
]


def _infer_type_hint(name: str, desc: str) -> str:
    """Infer Python type from field name patterns and description keywords.

    Order of precedence: name-based patterns > description keywords > default 'str'.
    """
    name_lower = name.lower()
    desc_lower = desc.lower()

    # 1. Check name-based patterns first (most reliable)
    for pattern, py_type in _TYPE_PATTERNS:
        if pattern.search(name_lower):
            return py_type

    # 2. Check description keywords
    if "boolean" in desc_lower or "true/false" in desc_lower:
        return "bool"
    if "iso date" in desc_lower or "yyyy-mm-dd" in desc_lower or "date string" in desc_lower:
        return "date"
    if "list of" in desc_lower or "array of" in desc_lower:
        return "list[str]"
    if "integer" in desc_lower or "whole number" in desc_lower:
        return "int"

    # 3. UUID detection: only if name ends with _id or _uuid (not identity/evidence)
    if re.search(r'(?:^|_)id$', name_lower) or re.search(r'(?:^|_)uuid(?:_|$)', name_lower):
        return "uuid"
    if "uuid" in desc_lower and not _NON_ID_PATTERNS.search(name_lower):
        return "uuid"

    return "str"


# ---- Optional input detection (gap #2) ----

_OPTIONAL_PHRASES = re.compile(
    r'(?:may be|optional|if needed|if applicable|if desired|if available|'
    r'may optionally|can be provided|can be omitted|'
    r'not required|configurable|at the proposer\'s discretion|'
    r'at the member\'s discretion|left blank|if assigned|if provided|'
    r'if sunset follows|if applicable)',
    re.IGNORECASE,
)

_OPTIONAL_LEADING = re.compile(
    r'^\*\*(?:Optional|If|When)\b', re.IGNORECASE,
)


def _is_input_required(name: str, desc: str, full_section: str) -> bool:
    """Determine if an input is required by scanning both the bullet and the
    full section text for optionality signals.

    Checks:
      1. Explicit 'optional' keyword in description
      2. Contextual phrases ('may be', 'if needed', etc.)
      3. Leading 'Optional' / 'If' / 'When' in bullet title
      4. Full section text contextual scan for this input name
    """
    desc_lower = desc.lower()

    # 1. Explicit optional keyword
    if "optional" in desc_lower or "configurable" in desc_lower:
        return False

    # 2. Contextual optionality phrases
    if _OPTIONAL_PHRASES.search(desc):
        return False

    # 3. Leading optional marker in name
    if _OPTIONAL_LEADING.match(name):
        return False

    # 4. Full section contextual scan: does the section mention this field
    #    with optional/conditional phrasing?
    section_lower = full_section.lower()
    snake_name = _snake_case(name)
    # Check if the input name appears near optionality indicators
    for phrase in [
        rf'{re.escape(snake_name)}.*(?:may be|optional|if needed)',
        rf'(?:may be|optional|if needed|if applicable).*{re.escape(snake_name)}',
    ]:
        if re.search(phrase, section_lower, re.DOTALL):
            return False

    return True


def _parse_steps(section_text: str | None) -> list[StepSpec]:
    """Parse section E into list of StepSpec."""
    if not section_text:
        return []
    steps: list[StepSpec] = []
    # Find all numbered steps with bold titles
    for m in _STEP_PATTERN.finditer(section_text):
        title = m.group(1).strip()
        body = m.group(2).strip()
        # Extract step number from match start position context
        # The regex matches the full "N. **Title.**" prefix so step number is implicit
        step_num = len(steps) + 1

        # Extract timeline
        tm = _TIMELINE_PAT.search(body)
        timeline = tm.group(1).strip() if tm else ""

        # Extract skill references (refs to other skills)
        refs = re.findall(r"per (?:the )?([a-z][a-z-]+)(?: skill)?", body, re.IGNORECASE)
        refs = list(set(refs))  # deduplicate

        steps.append(StepSpec(
            number=step_num,
            title=title,
            description=body.strip(),
            timeline=timeline,
            references=refs,
        ))
    return sorted(steps, key=lambda s: s.number)


def _parse_outputs(section_text: str | None) -> OutputSpec:
    """Parse section F into OutputSpec."""
    if not section_text:
        return OutputSpec()
    # Find template reference
    tmpl = re.search(r"`?(assets/[\w\-./]+\.ya?ml)`?", section_text)
    fields = re.findall(r'\*\*?([\w\s]+)\*\*?\s*[：:]', section_text)
    return OutputSpec(
        template_ref=tmpl.group(1) if tmpl else "",
        description=section_text.strip()[:200],
        fields=[f.strip() for f in fields],
        access="ecosystem members" if "all" in section_text.lower() else "scope-dependent",
    )


def _parse_constraints(section_text: str | None) -> ConstraintSpec:
    """Parse section G into ConstraintSpec."""
    if not section_text:
        return ConstraintSpec()
    rules: list[str] = []
    no_gos: list[str] = []
    for line in section_text.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue
        text = line[1:].strip()
        # Bold text is usually the headline rule
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        if any(phrase in text.lower() for phrase in [
            "no one can", "cannot", "no individual", "no body",
            "no single", "no participant", "no proposal", "no member",
        ]):
            no_gos.append(text)
        else:
            rules.append(text)
    return ConstraintSpec(
        rules=rules,
        unilateral_no_gos=no_gos,
    )


def _parse_capture_vectors(section_text: str | None) -> list[CaptureVector]:
    """Parse section H into list of CaptureVector.

    Handles capture headers with slashes like:
        **Charismatic capture / proposal fatigue.**
    """
    if not section_text:
        return []
    vectors: list[CaptureVector] = []
    # Match bold text that starts with a known capture type name, but may
    # continue with extra descriptive text (including slashes) before the
    # closing ** or .**
    capture_names = r"(?:capital|charismatic|emergency|informal)\s+capture"
    pattern = re.compile(
        rf"\*\*({capture_names}[^*]*?)\*\*\s*(.*?)(?=\n\*\*|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    for m in pattern.finditer(section_text):
        raw_name = m.group(1).strip()
        body = m.group(2).strip()
        # Normalize name: strip trailing '.' and get the capture type prefix
        raw_name = raw_name.rstrip(".")
        # Extract the canonical capture type (first two words: e.g. "Charismatic capture")
        name_match = re.match(
            r"(capital|charismatic|emergency|informal)\s+capture",
            raw_name,
            re.IGNORECASE,
        )
        clean_name = name_match.group(1).lower() if name_match else raw_name.lower()
        # Extract mitigation sentences
        mitigations = re.findall(
            r"[^.]*\b(prevent|protect|ensure|eliminate|structur|visible)\b[^.]*\.",
            body,
        )
        if not mitigations:
            mitigations = [body[:200]]
        vectors.append(CaptureVector(
            name=clean_name,
            description=body[:200],
            mitigations=[mt.strip() for mt in mitigations],
        ))
    return vectors


def _parse_failure_modes(section_text: str | None) -> list[FailureMode]:
    """Parse section I into list of FailureMode."""
    if not section_text:
        return []
    modes: list[FailureMode] = []
    bullets = re.split(r"\n\s*-\s+", section_text)
    for bullet in bullets:
        bullet = bullet.strip()
        if not bullet or len(bullet) < 20:
            continue
        # Extract bold trigger phrase and the fallback after ":"
        trigger_match = re.match(r"\*?\*(.+?)\*?\*\s*[：:]?\s*(.*)", bullet)
        if trigger_match:
            trigger = trigger_match.group(1).strip()
            body = trigger_match.group(2).strip()
        else:
            trigger = bullet[:80]
            body = bullet[80:] if len(bullet) > 80 else ""
        modes.append(FailureMode(trigger=trigger, fallback=body[:300]))
    return modes


def _parse_review_config(section_text: str | None) -> ReviewConfig:
    """Parse section J into ReviewConfig."""
    if not section_text:
        return ReviewConfig()
    interval = "annual"
    if "quarter" in section_text.lower():
        interval = "quarterly"
    elif "semi-annual" in section_text.lower():
        interval = "semi-annual"
    elif "monthly" in section_text.lower():
        interval = "monthly"

    expires = re.findall(r"auto.?expire[^.]*\.", section_text, re.IGNORECASE)
    missed = ""
    missed_match = re.search(r"missed[^.]*(?:escalat|notif)[^.]*\.", section_text, re.IGNORECASE)
    if missed_match:
        missed = missed_match.group(0).strip()

    return ReviewConfig(
        review_interval=interval,
        auto_expire_conditions=[e.strip() for e in expires],
        missed_review_action=missed,
    )


def _parse_exit_rules(section_text: str | None) -> ExitRule:
    """Parse section K into ExitRule."""
    if not section_text:
        return ExitRule()
    cease = re.findall(r"(?:cancel|cease|archived?|terminate)[^.]*\.", section_text, re.IGNORECASE)
    transfer = re.findall(r"(?:transfer|reassign|handoff|adopt)[^.]*\.", section_text, re.IGNORECASE)
    survive = re.findall(r"(?:survive|persist|remain|retain)[^.]*\.", section_text, re.IGNORECASE)
    wind_down = 30
    wind_match = re.search(r"(\d+)[- ]day", section_text)
    if wind_match:
        wind_down = int(wind_match.group(1))
    return ExitRule(
        obligations_that_cease=[c.strip() for c in cease[:3]],
        obligations_that_transfer=[t.strip() for t in transfer[:3]],
        obligations_that_survive=[s.strip() for s in survive[:3]],
        wind_down_days=wind_down,
    )


def _parse_interop(section_text: str | None) -> InteropRule:
    """Parse section L into InteropRule."""
    if not section_text:
        return InteropRule()
    notifications = re.findall(r"(?:notif|publish|communicat)[^.]*\.", section_text, re.IGNORECASE)
    registrations = re.findall(r"(?:register|track|record|link)[^.]*\.", section_text, re.IGNORECASE)
    extensibility = re.findall(r"(?:extens|defer|pending|Layer V)[^.]*\.", section_text, re.IGNORECASE)
    return InteropRule(
        notification_requirements=[n.strip() for n in notifications[:3]],
        cross_unit_registration=[r.strip() for r in registrations[:3]],
        extensibility_points=[e.strip() for e in extensibility[:3]],
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snake_case(text: str) -> str:
    """Convert display name to snake_case identifier."""
    # Remove special chars, lower, spaces → underscores
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "_", text.strip().lower())
    return text


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


def parse_skill_file(file_path: Path | str) -> SkillSpec:
    """Parse a SKILL.md file into a full SkillSpec IR.

    Args:
        file_path: Path to a SKILL.md file.

    Returns:
        SkillSpec with all sections parsed.

    Raises:
        FileNotFoundError: if file_path does not exist.
        ValueError: if frontmatter is missing or malformed.
    """
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    frontmatter, errors = _parse_frontmatter(content)
    if errors:
        raise ValueError(f"Frontmatter error in {path}: {'; '.join(errors)}")

    sections = _extract_sections(content)

    # Parse structured data from each section
    inputs = _parse_inputs(sections.get("D"))
    steps = _parse_steps(sections.get("E"))
    outputs = _parse_outputs(sections.get("F"))
    constraints = _parse_constraints(sections.get("G"))
    capture_vectors = _parse_capture_vectors(sections.get("H"))
    failure_modes = _parse_failure_modes(sections.get("I"))
    review_config = _parse_review_config(sections.get("J"))
    exit_rules = _parse_exit_rules(sections.get("K"))
    interop_rules = _parse_interop(sections.get("L"))

    # Trigger conditions from section C (or header if missing)
    triggers: list[str] = []
    c_text = sections.get("C")
    if c_text:
        triggers = [
            b.strip()[1:].strip()  # remove leading -
            for b in re.split(r"\n\s*-\s+", c_text)
            if b.strip() and len(b.strip()) > 10
        ]

    layer = int(frontmatter.get("layer", 0))
    depends_on = frontmatter.get("depends_on", [])
    if not isinstance(depends_on, list):
        depends_on = []

    return SkillSpec(
        name=str(frontmatter.get("name", "")),
        description=str(frontmatter.get("description", "")),
        layer=layer,
        version=str(frontmatter.get("version", "0.1.0")),
        depends_on=depends_on,
        source_path=str(path.resolve()),
        trigger_conditions=triggers,
        inputs=inputs,
        steps=steps,
        outputs=outputs,
        constraints=constraints,
        capture_vectors=capture_vectors,
        failure_modes=failure_modes,
        review_config=review_config,
        exit_rules=exit_rules,
        interop_rules=interop_rules,
        raw_sections=sections,
    )
