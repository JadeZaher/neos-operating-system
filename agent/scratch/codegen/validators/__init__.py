"""Drift detection validators — compare hand-written governance_tools.py against
the IR parsed from SKILL.md.

Detects:
- Missing tools (SKILL.md exists but no corresponding tool)
- Orphan tools (tool exists but no SKILL.md)
- Parameter drift (SKILL.md section D inputs vs. tool parameters)
- Description drift
- Required-field mismatch
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..ir import SkillSpec


@dataclass
class DriftIssue:
    """A single drift finding."""

    severity: str  # error, warning, info
    category: str  # missing_tool, orphan_tool, param_mismatch, field_mismatch, missing_schema
    skill_name: str
    message: str
    skill_says: str = ""
    tool_says: str = ""


@dataclass
class DriftReport:
    """Complete drift report for a skill or a set of skills."""

    skill_name: str = ""
    tool_name: str = ""
    issues: list[DriftIssue] = field(default_factory=list)
    match_score: float = 1.0  # 1.0 = perfect match, 0.0 = total drift

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


# ---------------------------------------------------------------------------
# Tool metadata extraction from governance_tools.py
# ---------------------------------------------------------------------------

def _extract_tool_metadata(tool_def: dict) -> dict[str, Any]:
    """Extract parameter metadata from a JSON-schema-style ToolDef entry."""
    params = tool_def.get("parameters", {})
    properties = params.get("properties", {})
    required_list = params.get("required", [])

    param_info: dict[str, dict] = {}
    for name, prop in properties.items():
        param_info[name] = {
            "type": prop.get("type", "string"),
            "description": prop.get("description", ""),
            "required": name in required_list,
        }
    return param_info


# ---------------------------------------------------------------------------
# Drift check for a single skill
# ---------------------------------------------------------------------------

def check_skill_drift(
    spec: SkillSpec,
    tool_def: dict | None,
) -> DriftReport:
    """Compare a SkillSpec against a ToolDef and produce a drift report.

    Args:
        spec: Parsed SkillSpec from SKILL.md.
        tool_def: ToolDef dict from governance_tools.py (None if not found).

    Returns:
        DriftReport with all findings.
    """
    report = DriftReport(skill_name=spec.name, tool_name=spec.tool_name)

    if tool_def is None:
        report.issues.append(DriftIssue(
            severity="error",
            category="missing_tool",
            skill_name=spec.name,
            message=f"No tool found for skill '{spec.name}'. Expected tool name: '{spec.tool_name}'.",
        ))
        report.match_score = 0.0
        return report

    tool_params = _extract_tool_metadata(tool_def)

    # Compare parameter names — section D inputs vs. tool parameters
    skill_params = {i.name for i in spec.inputs}
    tool_param_names = set(tool_params.keys())

    # Parameters in SKILL.md but not in tool
    missing_in_tool = skill_params - tool_param_names
    for p in sorted(missing_in_tool):
        inp = next(i for i in spec.inputs if i.name == p)
        report.issues.append(DriftIssue(
            severity="warning",
            category="param_mismatch",
            skill_name=spec.name,
            message=f"Input '{p}' defined in SKILL.md section D but missing from tool parameters.",
            skill_says=f"Input '{p}': {inp.description[:100]}",
            tool_says="(not present in tool)",
        ))

    # Parameters in tool but not in SKILL.md
    extra_in_tool = tool_param_names - skill_params
    for p in sorted(extra_in_tool):
        report.issues.append(DriftIssue(
            severity="info",
            category="param_mismatch",
            skill_name=spec.name,
            message=f"Parameter '{p}' exists in tool but is not listed in SKILL.md section D.",
            skill_says="(not listed in SKILL.md)",
            tool_says=tool_params[p].get("description", "")[:100],
        ))

    # Compare required fields
    skill_required = {i.name for i in spec.required_inputs}
    tool_required = {n for n, p in tool_params.items() if p.get("required")}

    for p in sorted(skill_required - tool_required):
        report.issues.append(DriftIssue(
            severity="warning",
            category="field_mismatch",
            skill_name=spec.name,
            message=f"Input '{p}' is required in SKILL.md but optional in tool.",
            skill_says="required",
            tool_says="optional",
        ))

    for p in sorted(tool_required - skill_required):
        report.issues.append(DriftIssue(
            severity="info",
            category="field_mismatch",
            skill_name=spec.name,
            message=f"Parameter '{p}' is required in tool but optional in SKILL.md.",
            skill_says="(not listed as required)",
            tool_says="required",
        ))

    # Description comparison
    skill_desc = spec.description.lower().strip()
    tool_desc = tool_def.get("description", "").lower().strip()
    if skill_desc and tool_desc:
        # Simple word-level overlap check
        skill_words = set(re.findall(r"\w+", skill_desc))
        tool_words = set(re.findall(r"\w+", tool_desc))
        if skill_words and tool_words:
            overlap = skill_words & tool_words
            score = len(overlap) / max(len(skill_words), 1)
            if score < 0.3:
                report.issues.append(DriftIssue(
                    severity="warning",
                    category="param_mismatch",
                    skill_name=spec.name,
                    message=f"Low description overlap ({score:.0%}) between SKILL.md and tool definition.",
                    skill_says=spec.description[:150],
                    tool_says=tool_def.get("description", "")[:150],
                ))

    # Calculate match score
    total_checks = max(len(spec.inputs), 1) + 1  # params + description
    penalty = len(report.issues) * 0.1
    report.match_score = max(0.0, 1.0 - min(1.0, penalty))

    return report


# ---------------------------------------------------------------------------
# Batch drift check
# ---------------------------------------------------------------------------

def check_all_drift(
    specs: list[SkillSpec],
    existing_tools: dict[str, dict],  # tool_name → ToolDef-as-dict
    aliases: dict[str, str] | None = None,  # skill_id → tool_name
) -> tuple[list[DriftReport], list[str]]:
    """Run drift checks across all skills and tools.

    Args:
        specs: Parsed SkillSpecs from SKILL.md files.
        existing_tools: ToolDef dicts keyed by tool name.
        aliases: Optional mapping from kebab-case skill IDs to snake_case
                 tool names. If provided, uses this to find the matching
                 tool instead of the default kebab→snake conversion.

    Returns:
        (reports, orphan_tool_names) — reports for each skill, plus
        a list of tool names with no corresponding SKILL.md.
    """
    reports: list[DriftReport] = []
    # Build reverse mapping: tool_name → [skill_specs]
    spec_by_tool: dict[str, list[SkillSpec]] = {}
    for s in specs:
        if aliases:
            target_tool = aliases.get(s.name, s.tool_name)
        else:
            target_tool = s.tool_name
        spec_by_tool.setdefault(target_tool, []).append(s)

    # Check each skill
    for spec in specs:
        if aliases:
            target_tool = aliases.get(spec.name, spec.tool_name)
        else:
            target_tool = spec.tool_name
        tool_def = existing_tools.get(target_tool)
        if tool_def is None and aliases and spec.name in aliases:
            # Aliased name doesn't match any actual tool either — skip the
            # generic check_skill_drift (which would add a redundant error)
            # and build the report directly.
            report = DriftReport(skill_name=spec.name, tool_name=target_tool)
            report.issues.append(DriftIssue(
                severity="error",
                category="missing_tool",
                skill_name=spec.name,
                message=f"No tool found for skill '{spec.name}'. Aliased name: '{target_tool}' not found in governance_tools.py.",
            ))
            report.match_score = 0.0
        else:
            report = check_skill_drift(spec, tool_def)
            report.tool_name = target_tool
        reports.append(report)

    # Find orphan tools (tools with no SKILL.md)
    all_target_names = set(spec_by_tool.keys())
    orphans = [
        tname for tname in existing_tools
        if tname not in all_target_names
    ]

    return reports, orphans


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def _safe_str(text: str, max_len: int = 200) -> str:
    """Sanitize a string for console output: strip non-ASCII, truncate."""
    text = text.encode("ascii", errors="replace").decode("ascii")
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def format_drift_report(report: DriftReport, verbose: bool = False) -> str:
    """Format a single DriftReport as a readable string."""
    lines: list[str] = []
    status_icon = "CLEAN" if report.is_clean else "DRIFT"
    lines.append(f"{status_icon} {report.skill_name} -> {report.tool_name}  (match: {report.match_score:.0%})")

    if report.is_clean:
        lines.append("  No drift detected.")
        return "\n".join(lines)

    for issue in report.issues:
        icon = {"error": "[ERR]", "warning": "[WARN]", "info": "[INFO]"}.get(issue.severity, "[?]")
        lines.append(f"  {icon} [{issue.category}] {_safe_str(issue.message)}")
        if verbose and issue.skill_says:
            lines.append(f"      SKILL.md: {_safe_str(issue.skill_says)}")
        if verbose and issue.tool_says:
            lines.append(f"      Tool:     {_safe_str(issue.tool_says)}")

    return "\n".join(lines)


def format_summary(
    reports: list[DriftReport],
    orphans: list[str],
) -> str:
    """Format a summary of all drift reports."""
    clean = sum(1 for r in reports if r.is_clean)
    drift = sum(1 for r in reports if not r.is_clean)
    total_issues = sum(len(r.issues) for r in reports)
    errors = sum(r.error_count for r in reports)
    warnings = sum(r.warning_count for r in reports)

    lines = [
        "=" * 60,
        "DRIFT DETECTION SUMMARY",
        "=" * 60,
        f"Skills checked:    {len(reports)}",
        f"  Clean:           {clean}",
        f"  Drift detected:  {drift}",
        f"  Orphan tools:    {len(orphans)}",
        f"Total issues:     {total_issues}",
        f"  Errors:          {errors}",
        f"  Warnings:        {warnings}",
        "=" * 60,
    ]

    if orphans:
        lines.append("")
        lines.append("ORPHAN TOOLS (no SKILL.md found):")
        for t in sorted(orphans):
            lines.append(f"  - {t}")

    return "\n".join(lines)
