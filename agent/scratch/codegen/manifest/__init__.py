"""Manifest generation — maps skill_id to generated tool paths.

Produces a TOML or YAML manifest that tracks:
- Which SKILL.md maps to which generated tool file
- Generation timestamps
- Version hashes for drift detection
- Rollout status (stub / implemented / production)
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from ..ir import SkillSpec


# Known kebab-case → snake_case tool name mappings (populated from
# governance_tools.py inspection). Updated by `drift` command.
_KNOWN_ALIASES: dict[str, str] = {
    # Layer 1: Agreement
    "agreement-creation": "create_agreement_draft",
    "agreement-amendment": "update_agreement_status",
    "agreement-registry": "search_agreements",
    "agreement-review": "get_agreement",
    "universal-agreement-field": "get_universal_field",
    # Layer 2: Authority
    "authority-boundary-negotiation": "check_authority",
    "domain-mapping": "create_domain_draft",
    "domain-review": "get_domain",
    "member-lifecycle": "get_active_members",
    "role-assignment": "get_member_roles",
    "role-sunset": "get_member_roles",
    "role-transfer": "get_member_roles",
    # Layer 3: ACT Engine
    "act-advice-phase": "record_advice",
    "act-consent-phase": "record_consent_position",
    "act-test-phase": "get_proposal",
    "consensus-check": "check_quorum",
    "proposal-creation": "create_proposal",
    "proposal-resolution": "update_proposal_status",
    # Layer 4: Economic
    "access-economy-transition": "create_ecosystem",
    "commons-monitoring": "get_ecosystem",
    "funding-pool-stewardship": "create_ecosystem",
    "participatory-allocation": "create_ecosystem",
    "resource-request": "create_proposal",
    # Layer 5: Inter-unit
    "cross-ethos-request": "create_proposal",
    "federation-agreement": "create_agreement_draft",
    "inter-unit-liaison": "get_member_roles",
    "polycentric-conflict-navigation": "triage_conflict",
    "shared-resource-stewardship": "create_domain_draft",
    # Layer 6: Conflict
    "coaching-intervention": "create_conflict_case",
    "community-impact-assessment": "create_conflict_case",
    "escalation-triage": "triage_conflict",
    "harm-circle": "create_conflict_case",
    "nvc-dialogue": "create_conflict_case",
    "repair-agreement": "create_repair_agreement",
    # Layer 7: Safeguard
    "capture-pattern-recognition": "create_safeguard_audit",
    "governance-health-audit": "create_safeguard_audit",
    "independent-monitoring": "create_safeguard_audit",
    "safeguard-trigger-design": "create_safeguard_audit",
    "structural-diversity-maintenance": "create_safeguard_audit",
    # Layer 8: Emergency
    "crisis-coordination": "declare_emergency",
    "emergency-criteria-design": "declare_emergency",
    "emergency-reversion": "get_emergency_state",
    "post-emergency-review": "get_emergency_state",
    "pre-authorization-protocol": "declare_emergency",
    # Layer 9: Memory
    "agreement-versioning": "update_agreement_status",
    "decision-record": "create_decision_record",
    "precedent-challenge": "search_precedents",
    "precedent-search": "search_precedents",
    "semantic-tagging": "search_agreements",
    # Layer 10: Exit
    "commitment-unwinding": "update_agreement_status",
    "ethos-dissolution": "get_ecosystem",
    "portable-record": "create_exit_record",
    "re-entry-integration": "get_active_members",
    "voluntary-exit": "create_exit_record",
}


def get_alias(skill_id: str) -> str:
    """Return the snake_case tool name for a kebab-case skill ID."""
    return _KNOWN_ALIASES.get(skill_id, skill_id.replace("-", "_"))


def build_manifest(
    specs: list[SkillSpec],
    generated_dir: Path,
    aliases: dict[str, str] | None = None,
) -> str:
    """Build a TOML manifest mapping skills to generated tool paths.

    Args:
        specs: List of parsed SkillSpec objects.
        generated_dir: Directory where generated tools live.
        aliases: Optional kebab-case → snake_case mapping. If None,
                 uses _KNOWN_ALIASES.

    Returns:
        TOML-formatted string.
    """
    if aliases is None:
        aliases = _KNOWN_ALIASES

    lines: list[str] = [
        "# NEOS Governance Tool Manifest",
        f"# Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"# Skill count: {len(specs)}",
        "",
        "[manifest]",
        f"version = \"1.0\"",
        f"generated_at = \"{datetime.now().isoformat(timespec='seconds')}\"",
        "",
    ]

    # ---- Aliases table ----
    lines.append("# Maps kebab-case skill IDs (from SKILL.md names) to")
    lines.append("# snake_case tool names (from governance_tools.py ToolDef entries).")
    lines.append("[aliases]")
    for skill_id, tool_name in sorted(aliases.items()):
        lines.append(f'{skill_id} = "{tool_name}"')
    lines.append("")

    by_layer: dict[int, list[SkillSpec]] = {}
    for spec in specs:
        by_layer.setdefault(spec.layer, []).append(spec)

    for layer in sorted(by_layer):
        lines.append(f"# ---- Layer {layer} ----")
        lines.append("")
        for spec in sorted(by_layer[layer], key=lambda s: s.name):
            tool_filename = f"{spec.tool_name}.py"
            schema_filename = f"{spec.tool_name}_schema.py"
            source_hash = _hash_file(Path(spec.source_path)) if Path(spec.source_path).exists() else "unknown"

            lines.append(f"[[skills]]")
            lines.append(f'skill_id = "{spec.name}"')
            lines.append(f'skill_name = "{spec.name.replace("-", " ").title()}"')
            lines.append(f"layer = {spec.layer}")
            lines.append(f'version = "{spec.version}"')
            lines.append(f'source_path = "{spec.source_path}"')
            lines.append(f'source_hash = "{source_hash}"')
            lines.append(f'tool_file = "generated/{tool_filename}"')
            lines.append(f'schema_file = "generated/{schema_filename}"')
            lines.append(f'aliased_tool = "{aliases.get(spec.name, spec.tool_name)}"')
            # Emit TOML-valid array (strings must use double quotes)
            deps_toml = "[" + ", ".join(f'"{d}"' for d in spec.depends_on) + "]"
            lines.append(f'dependencies = {deps_toml}')
            lines.append(f'rollout_status = "stub"')
            lines.append("")

    return "\n".join(lines)


def build_skill_index(specs: list[SkillSpec]) -> dict[str, SkillSpec]:
    """Build an in-memory index: tool_name → SkillSpec."""
    return {spec.tool_name: spec for spec in specs}


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
