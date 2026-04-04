#!/usr/bin/env python3
"""Generate TypeScript interfaces from Pydantic models.

Usage:
    python scripts/generate_types.py [output_path]

Default output: ../../charting-the-course/client/src/types/api.ts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the agent src is importable when run from the scripts directory or repo root
_SCRIPTS_DIR = Path(__file__).resolve().parent
_AGENT_SRC = _SCRIPTS_DIR.parent / "agent" / "src"
if str(_AGENT_SRC) not in sys.path:
    sys.path.insert(0, str(_AGENT_SRC))

from neos_agent.api.schemas import ApiError, HealthResponse, SkillItem, SkillsResponse  # noqa: E402

# Models to export, in order
MODELS = [HealthResponse, SkillItem, SkillsResponse, ApiError]

# JSON Schema → TypeScript primitive mapping
_PRIMITIVE_MAP: dict[str, str] = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "null": "null",
}


def _json_schema_type_to_ts(prop_schema: dict, defs: dict[str, dict]) -> str:
    """Convert a single JSON Schema property definition to a TypeScript type string."""
    # Handle $ref
    if "$ref" in prop_schema:
        ref_name = prop_schema["$ref"].split("/")[-1]
        return ref_name

    # Handle anyOf (e.g. Optional[X] → X | null)
    if "anyOf" in prop_schema:
        parts = [_json_schema_type_to_ts(part, defs) for part in prop_schema["anyOf"]]
        return " | ".join(parts)

    schema_type = prop_schema.get("type")

    # Array
    if schema_type == "array":
        items = prop_schema.get("items", {})
        item_ts = _json_schema_type_to_ts(items, defs)
        return f"{item_ts}[]"

    # Primitive
    if schema_type in _PRIMITIVE_MAP:
        return _PRIMITIVE_MAP[schema_type]

    # Fallback
    return "unknown"


def _model_to_ts_interface(model_cls, defs: dict[str, dict]) -> str:
    """Convert a Pydantic model class to a TypeScript interface string."""
    schema = model_cls.model_json_schema()
    props = schema.get("properties", {})
    required_fields: set[str] = set(schema.get("required", []))

    lines: list[str] = [f"export interface {model_cls.__name__} {{"]
    for field_name, field_schema in props.items():
        ts_type = _json_schema_type_to_ts(field_schema, defs)
        optional_marker = "" if field_name in required_fields else "?"
        lines.append(f"  {field_name}{optional_marker}: {ts_type};")
    lines.append("}")
    return "\n".join(lines)


def generate(output_path: Path) -> None:
    header = "// Auto-generated from Pydantic models — do not edit manually\n"

    # Collect $defs from all model schemas (for cross-model ref resolution)
    combined_defs: dict[str, dict] = {}
    for model in MODELS:
        schema = model.model_json_schema()
        combined_defs.update(schema.get("$defs", {}))

    interfaces: list[str] = []
    for model in MODELS:
        interfaces.append(_model_to_ts_interface(model, combined_defs))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(header + "\n" + "\n\n".join(interfaces) + "\n", encoding="utf-8")
    print(f"Written: {output_path}")


def main() -> None:
    default_output = (
        _SCRIPTS_DIR.parent.parent / "charting-the-course" / "client" / "src" / "types" / "api.ts"
    )
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output
    generate(output_path)


if __name__ == "__main__":
    main()
