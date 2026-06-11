"""IR dataclasses for the SKILL.md → tool codegen pipeline.

These are the canonical structured representations that sit between the
parser (which reads SKILL.md markdown) and the generator (which emits
Python tool functions + Pydantic schemas).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InputSpec:
    """A single required/optional input from section D of SKILL.md."""

    name: str
    description: str
    type_hint: str = "str"  # str, int, bool, list[str], dict, date, uuid
    required: bool = True
    provider: str = ""  # who provides it
    format_desc: str = ""  # format description (ISO date, UUID, etc.)


@dataclass
class StepSpec:
    """A single step from section E of SKILL.md."""

    number: int
    title: str = ""
    description: str = ""
    actors: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)  # conditions gating next step
    timeline: str = ""  # e.g. "48 hours", "3-7 days"
    references: list[str] = field(default_factory=list)  # referenced skill names


@dataclass
class OutputSpec:
    """Output artifact definition from section F of SKILL.md."""

    template_ref: str = ""  # assets/whatever.yaml
    description: str = ""
    fields: list[str] = field(default_factory=list)
    access: str = ""  # who can access


@dataclass
class ConstraintSpec:
    """Authority constraints and no-go actions from section G."""

    rules: list[str] = field(default_factory=list)
    unilateral_no_gos: list[str] = field(default_factory=list)
    authority_levels: list[str] = field(default_factory=list)


@dataclass
class CaptureVector:
    """A single capture vector from section H."""

    name: str  # capital, charismatic, emergency, informal
    description: str = ""
    mitigations: list[str] = field(default_factory=list)


@dataclass
class FailureMode:
    """A single failure mode from section I."""

    trigger: str = ""
    consequence: str = ""
    fallback: str = ""


@dataclass
class ReviewConfig:
    """Review/expiry configuration from section J."""

    review_interval: str = ""  # e.g. "quarterly", "annual"
    auto_expire_conditions: list[str] = field(default_factory=list)
    missed_review_action: str = ""


@dataclass
class ExitRule:
    """Exit compatibility rules from section K."""

    obligations_that_cease: list[str] = field(default_factory=list)
    obligations_that_transfer: list[str] = field(default_factory=list)
    obligations_that_survive: list[str] = field(default_factory=list)
    wind_down_days: int = 30


@dataclass
class InteropRule:
    """Cross-unit interoperability rules from section L."""

    notification_requirements: list[str] = field(default_factory=list)
    cross_unit_registration: list[str] = field(default_factory=list)
    extensibility_points: list[str] = field(default_factory=list)


@dataclass
class SkillSpec:
    """Complete structured specification for a single governance skill.

    This is the canonical IR produced by the parser and consumed by the
    generator and validators.
    """

    # ---- Frontmatter ----
    name: str = ""
    description: str = ""
    layer: int = 0
    version: str = "0.1.0"
    depends_on: list[str] = field(default_factory=list)
    source_path: str = ""

    # ---- Sections ----
    trigger_conditions: list[str] = field(default_factory=list)  # C
    inputs: list[InputSpec] = field(default_factory=list)  # D
    steps: list[StepSpec] = field(default_factory=list)  # E
    outputs: OutputSpec = field(default_factory=OutputSpec)  # F
    constraints: ConstraintSpec = field(default_factory=ConstraintSpec)  # G
    capture_vectors: list[CaptureVector] = field(default_factory=list)  # H
    failure_modes: list[FailureMode] = field(default_factory=list)  # I
    review_config: ReviewConfig = field(default_factory=ReviewConfig)  # J
    exit_rules: ExitRule = field(default_factory=ExitRule)  # K
    interop_rules: InteropRule = field(default_factory=InteropRule)  # L

    # ---- Extra ----
    raw_sections: dict[str, str | None] = field(default_factory=dict)

    @property
    def tool_name(self) -> str:
        """Derive Python tool function name from skill name."""
        return self.name.replace("-", "_")

    @property
    def schema_class_name(self) -> str:
        """Derive Pydantic schema class name."""
        parts = self.name.replace("-", " ").title().replace(" ", "")
        return f"{parts}Input"

    @property
    def required_inputs(self) -> list[InputSpec]:
        """Return only required inputs."""
        return [i for i in self.inputs if i.required]

    @property
    def optional_inputs(self) -> list[InputSpec]:
        """Return only optional inputs."""
        return [i for i in self.inputs if not i.required]

    def as_generated_tool(self) -> dict[str, Any]:
        """Return a dict suitable for the ToolDef registry.

        This is the bridge format between the IR and the actual ToolDef
        list in governance_tools.py.
        """
        required_names = [i.name for i in self.required_inputs]
        properties: dict[str, Any] = {}
        for inp in self.inputs:
            prop: dict[str, Any] = {
                "type": "string",
                "description": inp.description,
            }
            properties[inp.name] = prop

        return {
            "name": self.tool_name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_names,
            },
        }
