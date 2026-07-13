"""Generic pipeline schema for domain logic orchestration.

This module defines a framework-agnostic schema for execution pipeline
configurations that compose CRUD primitives, validation rules, and custom
operations into reusable tools. Designed to work with any SQLAlchemy-based
domain logic and data strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineStep:
    """A single step in an execution pipeline.
    
    Generic operation definition that can be extended for any domain logic.
    """
    op: str  # Operation name (e.g., "validate", "resolve", "create", "custom")
    args: dict[str, Any] = field(default_factory=dict)  # Operation-specific arguments
    description: str = ""  # Human-readable description of this step


@dataclass(frozen=True)
class TargetTool:
    """Target tool definition for a skill or domain operation."""
    name: str  # Tool name (e.g., "create_record", "process_order")
    pipeline: list[PipelineStep]  # Ordered execution steps
    description: str = ""  # Human-readable description
    version: str = "1.0.0"  # Tool version
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass(frozen=True)
class PipelineConfig:
    """Complete pipeline configuration from skill or config file.
    
    Framework-agnostic configuration that can be used with any
    SQLAlchemy models and domain logic.
    """
    target_tool: TargetTool
    version: str = "1.0.0"
    metadata: dict[str, Any] = field(default_factory=dict)


class OperationRegistry:
    """Registry for valid operation types and their schemas.
    
    This allows the framework to be extended with custom operations
    without modifying core code. Domains can register their own
    operation types and validation schemas.
    """
    
    def __init__(self):
        self._operations: dict[str, dict[str, Any]] = {}
        self._register_builtin_operations()
    
    def register_operation(self, name: str, schema: dict[str, Any]) -> None:
        """Register a custom operation type.
        
        Args:
            name: Operation name
            schema: Schema dict with 'description', 'required_args', 'optional_args'
        """
        self._operations[name] = schema
    
    def get_operation_schema(self, name: str) -> dict[str, Any] | None:
        """Get schema for an operation type."""
        return self._operations.get(name)
    
    def is_valid_operation(self, name: str) -> bool:
        """Check if an operation type is registered."""
        return name in self._operations
    
    def list_operations(self) -> list[str]:
        """List all registered operation types."""
        return list(self._operations.keys())
    
    def _register_builtin_operations(self) -> None:
        """Register built-in generic operations."""
        
        # Validation operations
        self.register_operation("validate", {
            "description": "Validate input fields against rules",
            "required_args": ["type"],
            "optional_args": ["field", "fields", "values", "format", "pattern"],
        })
        
        self.register_operation("transform", {
            "description": "Transform or normalize input data",
            "required_args": ["type"],
            "optional_args": ["field", "fields", "mapping", "function"],
        })
        
        # Resolution operations
        self.register_operation("resolve", {
            "description": "Resolve entity reference by identifier",
            "required_args": ["entity_type"],
            "optional_args": ["arg", "by_field", "scope"],
        })
        
        # Business key generation
        self.register_operation("generate_key", {
            "description": "Generate unique business key",
            "required_args": ["pattern"],
            "optional_args": ["prefix", "scope", "sequence_field"],
        })
        
        # CRUD operations
        self.register_operation("create", {
            "description": "Create new database record",
            "required_args": ["entity"],
            "optional_args": ["defaults", "before_hooks", "after_hooks"],
        })
        
        self.register_operation("read", {
            "description": "Read database record(s)",
            "required_args": ["entity"],
            "optional_args": ["key", "keys", "filters", "limit", "offset", "order_by"],
        })
        
        self.register_operation("update", {
            "description": "Update existing database record",
            "required_args": ["entity"],
            "optional_args": ["key", "keys", "values", "before_hooks", "after_hooks"],
        })
        
        self.register_operation("delete", {
            "description": "Delete database record(s)",
            "required_args": ["entity"],
            "optional_args": ["key", "keys", "filters", "before_hooks", "after_hooks"],
        })
        
        # State transition operations
        self.register_operation("transition", {
            "description": "Execute state transition with validation",
            "required_args": ["entity", "field"],
            "optional_args": ["to", "transitions", "validator", "before_hooks", "after_hooks"],
        })
        
        # Workflow operations
        self.register_operation("branch", {
            "description": "Conditional branching based on conditions",
            "required_args": ["condition"],
            "optional_args": ["if_true", "if_false", "branches"],
        })
        
        self.register_operation("parallel", {
            "description": "Execute steps in parallel",
            "required_args": ["steps"],
            "optional_args": ["merge_strategy"],
        })
        
        self.register_operation("loop", {
            "description": "Iterate over collection",
            "required_args": ["over", "steps"],
            "optional_args": ["as", "while", "until", "max_iterations"],
        })
        
        # External operations
        self.register_operation("http_request", {
            "description": "Make HTTP request to external service",
            "required_args": ["url", "method"],
            "optional_args": ["headers", "body", "query_params", "timeout"],
        })
        
        self.register_operation("message", {
            "description": "Send message to queue or topic",
            "required_args": ["destination", "payload"],
            "optional_args": ["headers", "properties"],
        })
        
        # Custom operations
        self.register_operation("custom", {
            "description": "Execute custom handler function",
            "required_args": ["handler"],
            "optional_args": ["args", "module", "class"],
        })
        
        # Version control operations
        self.register_operation("create_version", {
            "description": "Create a new version of an entity",
            "required_args": ["entity"],
            "optional_args": ["version_number", "change_description", "parent_version_id"],
        })
        
        self.register_operation("get_version", {
            "description": "Get a specific version of an entity",
            "required_args": ["entity", "version_id"],
            "optional_args": [],
        })
        
        self.register_operation("list_versions", {
            "description": "List all versions of an entity",
            "required_args": ["entity", "entity_id"],
            "optional_args": ["limit", "order"],
        })
        
        self.register_operation("compare_versions", {
            "description": "Compare two versions of an entity",
            "required_args": ["entity", "version_id_1", "version_id_2"],
            "optional_args": [],
        })
        
        # Audit trail operations
        self.register_operation("log_audit", {
            "description": "Log an audit event",
            "required_args": ["action", "entity_type", "entity_id"],
            "optional_args": ["actor", "changes", "metadata"],
        })
        
        self.register_operation("get_audit_trail", {
            "description": "Get audit trail for an entity",
            "required_args": ["entity_type", "entity_id"],
            "optional_args": ["limit", "offset", "from_date", "to_date"],
        })
        
        # Agent session operations
        self.register_operation("create_session", {
            "description": "Create an agent session for workflow tracking",
            "required_args": ["session_type"],
            "optional_args": ["context", "metadata"],
        })
        
        self.register_operation("update_session", {
            "description": "Update agent session state",
            "required_args": ["session_id"],
            "optional_args": ["state", "context", "metadata"],
        })
        
        self.register_operation("get_session", {
            "description": "Get agent session details",
            "required_args": ["session_id"],
            "optional_args": [],
        })
        
        # Semantic search operations
        self.register_operation("index_entity", {
            "description": "Index an entity for semantic search",
            "required_args": ["entity_type", "entity_id", "content"],
            "optional_args": ["tags", "metadata"],
        })
        
        self.register_operation("semantic_search", {
            "description": "Perform semantic search",
            "required_args": ["query"],
            "optional_args": ["entity_types", "filters", "limit"],
        })
        
        self.register_operation("get_similar", {
            "description": "Find similar entities",
            "required_args": ["entity_type", "entity_id"],
            "optional_args": ["limit", "threshold"],
        })
        
        # Workflow orchestration operations
        self.register_operation("start_workflow", {
            "description": "Start a multi-step workflow",
            "required_args": ["workflow_type"],
            "optional_args": ["initial_context", "participants"],
        })
        
        self.register_operation("advance_workflow", {
            "description": "Advance workflow to next step",
            "required_args": ["workflow_id", "step_name"],
            "optional_args": ["step_context"],
        })
        
        self.register_operation("get_workflow_state", {
            "description": "Get current workflow state",
            "required_args": ["workflow_id"],
            "optional_args": [],
        })
        
        self.register_operation("cancel_workflow", {
            "description": "Cancel a workflow",
            "required_args": ["workflow_id"],
            "optional_args": ["reason"],
        })


# Global operation registry
_global_registry: OperationRegistry | None = None


def get_operation_registry() -> OperationRegistry:
    """Get or create the global operation registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = OperationRegistry()
    return _global_registry


def validate_pipeline_step(step: dict[str, Any], registry: OperationRegistry | None = None) -> tuple[bool, str | None]:
    """Validate a pipeline step dictionary against operation registry.
    
    Args:
        step: Pipeline step dictionary
        registry: Operation registry (uses global if None)
    
    Returns:
        (is_valid, error_message)
    """
    if registry is None:
        registry = get_operation_registry()
    
    if "op" not in step:
        return False, "Pipeline step missing 'op' field"
    
    op = step["op"]
    if not registry.is_valid_operation(op):
        return False, f"Invalid operation '{op}'. Must be one of: {registry.list_operations()}"
    
    # Validate operation-specific arguments against schema
    schema = registry.get_operation_schema(op)
    if not schema:
        return True, None  # No schema to validate against
    
    args = step.get("args", {})
    required_args = schema.get("required_args", [])
    
    # Check required arguments
    for required_arg in required_args:
        if required_arg not in args:
            return False, f"Operation '{op}' requires '{required_arg}' argument"
    
    return True, None


def parse_pipeline_config(
    frontmatter: dict[str, Any],
    registry: OperationRegistry | None = None
) -> tuple[PipelineConfig | None, list[str]]:
    """Parse pipeline configuration from frontmatter or config dict.
    
    Args:
        frontmatter: Dictionary containing pipeline configuration
        registry: Operation registry (uses global if None)
    
    Returns:
        (config, errors). Errors list is non-empty if parsing fails.
    """
    if registry is None:
        registry = get_operation_registry()
    
    errors = []
    
    # Support both "target_tool" (NEOS) and "pipeline" (generic) keys
    if "target_tool" in frontmatter:
        tool_data = frontmatter["target_tool"]
    elif "pipeline" in frontmatter:
        tool_data = frontmatter
    else:
        return None, ["Missing 'target_tool' or 'pipeline' in configuration"]
    
    if not isinstance(tool_data, dict):
        errors.append("Pipeline configuration must be a dictionary")
        return None, errors
    
    if "name" not in tool_data:
        errors.append("Pipeline configuration missing 'name' field")
        return None, errors
    
    if "pipeline" not in tool_data:
        errors.append("Pipeline configuration missing 'pipeline' field")
        return None, errors
    
    pipeline_data = tool_data["pipeline"]
    if not isinstance(pipeline_data, list):
        errors.append("'pipeline' must be a list")
        return None, errors
    
    # Parse pipeline steps
    pipeline_steps = []
    for i, step_data in enumerate(pipeline_data):
        if not isinstance(step_data, dict):
            errors.append(f"Pipeline step {i} must be a dictionary")
            continue
        
        is_valid, error = validate_pipeline_step(step_data, registry)
        if not is_valid:
            errors.append(f"Pipeline step {i}: {error}")
            continue
        
        step = PipelineStep(
            op=step_data["op"],
            args=step_data.get("args", {}),
            description=step_data.get("description", "")
        )
        pipeline_steps.append(step)
    
    if errors:
        return None, errors
    
    target_tool = TargetTool(
        name=tool_data["name"],
        pipeline=pipeline_steps,
        description=tool_data.get("description", ""),
        version=tool_data.get("version", "1.0.0"),
        metadata=tool_data.get("metadata", {})
    )
    
    config = PipelineConfig(
        target_tool=target_tool,
        version=frontmatter.get("version", "1.0.0"),
        metadata=frontmatter.get("metadata", {})
    )
    
    return config, []


def load_pipeline_config_from_yaml(yaml_content: str, registry: OperationRegistry | None = None) -> tuple[PipelineConfig | None, list[str]]:
    """Load pipeline configuration from YAML content.
    
    Args:
        yaml_content: YAML string containing pipeline configuration
        registry: Operation registry (uses global if None)
    
    Returns:
        (config, errors). Errors list is non-empty if parsing fails.
    """
    try:
        import yaml
    except ImportError:
        return None, ["PyYAML is required to parse YAML configurations"]
    
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return None, [f"YAML parsing error: {e}"]
    
    if not isinstance(data, dict):
        return None, ["YAML content must be a dictionary"]
    
    return parse_pipeline_config(data, registry)


def load_pipeline_config_from_json(json_content: str, registry: OperationRegistry | None = None) -> tuple[PipelineConfig | None, list[str]]:
    """Load pipeline configuration from JSON content.
    
    Args:
        json_content: JSON string containing pipeline configuration
        registry: Operation registry (uses global if None)
    
    Returns:
        (config, errors). Errors list is non-empty if parsing fails.
    """
    import json
    
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        return None, [f"JSON parsing error: {e}"]
    
    if not isinstance(data, dict):
        return None, ["JSON content must be a dictionary"]
    
    return parse_pipeline_config(data, registry)
