"""Code generator — emits Python tool functions, Pydantic schemas, and
ToolDef entries from SkillSpec IR.

Usage:
    from scratch.codegen.parser import parse_skill_file
    from scratch.codegen.generator import generate_tool, generate_all

    spec = parse_skill_file("path/to/SKILL.md")
    code = generate_tool(spec)
    print(code)
"""

from __future__ import annotations

import textwrap
from datetime import datetime

from ..ir import InputSpec, SkillSpec


# ---------------------------------------------------------------------------
# Type mapping: IR type_hint → Python type
# ---------------------------------------------------------------------------

TYPE_MAP: dict[str, str] = {
    "str": "str",
    "int": "int",
    "bool": "bool",
    "float": "float",
    "date": "str",       # ISO date strings at runtime
    "uuid": "str",       # UUID strings at runtime
    "list[str]": "list[str]",
    "dict": "dict",
}

JSON_SCHEMA_TYPE_MAP: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "bool": "boolean",
    "float": "number",
    "date": "string",
    "uuid": "string",
    "list[str]": "array",
    "dict": "object",
}


# ---------------------------------------------------------------------------
# Pydantic schema generator
# ---------------------------------------------------------------------------

def _generate_pydantic_schema(spec: SkillSpec) -> str:
    """Generate a Pydantic BaseModel for the skill's inputs."""
    lines: list[str] = []
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from pydantic import BaseModel, Field")
    lines.append("")
    lines.append("")
    lines.append(f"class {spec.schema_class_name}(BaseModel):")
    lines.append(f'    """Input schema for {spec.name} (Layer {spec.layer}).')
    lines.append("")
    lines.append(f"    {spec.description}")
    lines.append('    """')
    lines.append("")

    for inp in spec.inputs:
        field_kwargs = []
        # Description
        clean_desc = (
            inp.description.replace('"', "'")
            .replace("\n", " ")
            .strip()[:200]
        )
        field_kwargs.append(f'description="{clean_desc}"')
        # Default for optional
        if not inp.required:
            field_kwargs.append("default=None")

        py_type = TYPE_MAP.get(inp.type_hint, "str")
        if not inp.required:
            py_type = f"Optional[{py_type}]"

        field_str = ", ".join(field_kwargs)
        lines.append(f"    {inp.name}: {py_type} = Field({field_str})")

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Handler stub generator
# ---------------------------------------------------------------------------

def _generate_handler_stub(spec: SkillSpec) -> str:
    """Generate the async handler function stub."""
    lines: list[str] = []
    lines.append("")
    lines.append("")
    lines.append(f"async def {spec.tool_name}(")
    lines.append("    args: dict,")
    lines.append("    db: AsyncSession,")
    lines.append("    ecosystem_ids: list | None = None,")
    lines.append(") -> dict:")
    lines.append(f'    """{spec.description}')
    lines.append("")
    lines.append(f"    Auto-generated from {spec.source_path}")
    lines.append(f"    Layer: {spec.layer} | Version: {spec.version}")
    lines.append(f"    Dependencies: {', '.join(spec.depends_on) if spec.depends_on else 'none'}")
    lines.append("")
    lines.append("    Steps:")
    for step in spec.steps:
        lines.append(f"    {step.number}. {step.title}")
    lines.append('    """')
    lines.append("")

    # Input validation block
    required = [i for i in spec.inputs if i.required]
    if required:
        lines.append("    # ---- Required field validation ----")
        for inp in required:
            lines.append(f"    {inp.name} = args.get('{inp.name}', '')")
        lines.append("")
        for inp in required:
            lines.append(f"    if not {inp.name}:")
            lines.append(f'        return {{"success": False, "error": "{inp.name} is required."}}')
        lines.append("")

    # Ecosystem ID resolution
    lines.append("    # ---- Ecosystem ID resolution ----")
    lines.append("    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)")
    lines.append("    if eco_id is None:")
    lines.append('        return {"success": False, "error": "No ecosystem configured."}')
    lines.append("")

    # Placeholder implementation
    lines.append("    # ---- TODO: Implement skill logic ----")
    lines.append(f"    # This stub was generated from {spec.source_path}")
    lines.append(f"    # Steps to implement ({len(spec.steps)} total):")
    for step in spec.steps:
        refs_str = f" (refs: {', '.join(step.references)})" if step.references else ""
        lines.append(f"    #   {step.number}. {step.title}{refs_str}")
    lines.append("")
    lines.append("    return {")
    lines.append('        "success": True,')
    lines.append('        "data": {')
    lines.append(f'            "skill": "{spec.name}",')
    lines.append(f'            "layer": {spec.layer},')
    lines.append(f'            "version": "{spec.version}",')
    lines.append(f'            "message": "Stub for {spec.name} — implementation pending.",')
    lines.append("        },")
    lines.append("    }")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ToolDef entry generator
# ---------------------------------------------------------------------------

def _generate_tooldef_entry(spec: SkillSpec) -> str:
    """Generate a ToolDef(...) entry suitable for the GOVERNANCE_TOOLS list."""
    required_names = [i.name for i in spec.required_inputs]

    # Build properties dict as string
    props_lines: list[str] = []
    for inp in spec.inputs:
        props_lines.append(f'                "{inp.name}": {{')
        props_lines.append(f'                    "type": "{JSON_SCHEMA_TYPE_MAP.get(inp.type_hint, "string")}",')
        clean_desc = inp.description.replace('"', "'").replace("\n", " ").strip()[:200]
        props_lines.append(f'                    "description": "{clean_desc}",')
        props_lines.append("                },")

    props_str = "\n".join(props_lines)
    required_str = ", ".join(f'"{n}"' for n in required_names)

    return textwrap.dedent(f"""\
        ToolDef(
            name="{spec.tool_name}",
            description="{spec.description}",
            parameters={{
                "type": "object",
                "properties": {{
        {props_str}
                }},
                "required": [{required_str}],
            }},
            handler={spec.tool_name},
        ),""")


# ---------------------------------------------------------------------------
# Full file generator
# ---------------------------------------------------------------------------

def generate_tool_file(spec: SkillSpec) -> str:
    """Generate a complete Python tool file for a single skill.

    Returns a string containing the full module content.
    """
    header = textwrap.dedent(f"""\
        \"\"\"NEOS governance tool for {spec.name} (Layer {spec.layer}).

        Auto-generated from SKILL.md on {datetime.now().isoformat(timespec="seconds")}.
        Source: {spec.source_path}

        This file is generated. To regenerate, run:
            python -m scratch.codegen generate {spec.name}
        \"\"\"

        from __future__ import annotations

        import uuid
        from datetime import date, datetime, timedelta, timezone
        from typing import Any, Optional

        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import AsyncSession

        logger = __import__("logging").getLogger(__name__)

        # Re-import helpers from the main governance_tools module at runtime.
        # In production these would be in a shared utilities module.
        try:
            from neos_agent.agent.governance_tools import (
                _get_first_ecosystem_id,
                _resolve_member,
                _today,
                ToolDef,
            )
        except ImportError:
            # Fallback for scratch testing
            pass
    """)

    pydantic_schema = _generate_pydantic_schema(spec)
    handler_stub = _generate_handler_stub(spec)
    tooldef = _generate_tooldef_entry(spec)

    # Optional: generate a `get_X_tooldef()` function
    export_func = textwrap.dedent(f"""\

        def get_{spec.tool_name}_tooldef() -> object:
            \"\"\"Return the ToolDef entry for {spec.name}.\"\"\"
            return {spec.tool_name}_TOOLDEF


        {spec.tool_name}_TOOLDEF = {tooldef}
    """)

    parts = [header, pydantic_schema, handler_stub, export_func]
    return "\n".join(parts)


def generate_all(specs: list[SkillSpec]) -> dict[str, str]:
    """Generate tool files for multiple skills.

    Returns dict mapping skill name → generated Python source.
    """
    return {spec.name: generate_tool_file(spec) for spec in specs}


# ---------------------------------------------------------------------------
# Pydantic schema-only generator (for use in API validation layers)
# ---------------------------------------------------------------------------

def generate_schema_only(spec: SkillSpec) -> str:
    """Generate only the Pydantic schema (no handler)."""
    return _generate_pydantic_schema(spec)


# ---------------------------------------------------------------------------
# Manifest snippet generator
# ---------------------------------------------------------------------------

def generate_manifest_entry(spec: SkillSpec) -> dict:
    """Generate a manifest entry for this skill."""
    return {
        "skill_id": spec.name,
        "skill_name": spec.name.replace("-", " ").title(),
        "layer": spec.layer,
        "version": spec.version,
        "generated_tool": f"neos_agent.agent.generated.{spec.tool_name}",
        "generated_schema": f"neos_agent.agent.generated.schemas.{spec.schema_class_name}",
        "source_skill_md": spec.source_path,
        "depends_on": spec.depends_on,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
