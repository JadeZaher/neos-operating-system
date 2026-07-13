# Unified NEOS Codegen Framework Documentation

## Overview

The Unified NEOS Codegen Framework provides a generic, component-based wrapper system that auto-generates CRUD primitives from SQLAlchemy ORM models and composes them into agent tools via OKF-style skill declarations.

## Architecture

```
+-------------------------------------------------------------+
|                     ORM Database Models                     |
|              (neos_agent.db.models.*)                        |
+-------------------------------------------------------------+
                              |
                              v  (Reflected via SQLAlchemy AST)
+-------------------------------------------------------------+
|              Generated CRUD Component Primitives            |
|       (neos_agent.db.crud.*_crud.py)                        |
|       create_X, get_X_by_id, list_X, update_X, delete_X     |
+-------------------------------------------------------------+
                              |
                              v  (Arranged in Execution Pipelines)
+-------------------------------------------------------------+
|                 OKF-Style Skill YAML Schema                 |
|       (target_tool.pipeline with execution steps)           |
+-------------------------------------------------------------+
                              |
                              v  (Composed dynamically at Runtime)
+-------------------------------------------------------------+
|                       Agent MCP Tools                       |
|       (tool_registry.py composes handlers from skills)      |
+-------------------------------------------------------------+
```

## Components

### 1. CRUD Generator (`neos_agent.db.crud_generator.py`)

Auto-generates uniform CRUD handlers from SQLAlchemy models.

**Features:**
- Scans `neos_agent.db.models` package
- Identifies business key fields (e.g., `agreement_id`, `member_id`)
- Generates 6 CRUD operations per model:
  - `create_{model}`: Create new record
  - `get_{model}_by_id`: Read by internal UUID
  - `get_{model}_by_{business_key}`: Read by business key
  - `list_{model}`: List with filtering
  - `update_{model}`: Update existing record
  - `delete_{model}`: Delete record

**Usage:**
```bash
cd neos-operating-system
.venv\Scripts\python.exe agent\src\neos_agent\db\crud_generator.py
```

**Output:**
- `neos_agent/db/crud/` package with 47 CRUD modules
- Auto-generated `__init__.py` re-exports all CRUD functions

### 2. Pipeline Schema (`neos_agent.skills.pipeline_schema.py`)

Defines the YAML schema for skill pipeline configurations.

**Key Classes:**
- `PipelineStep`: Single pipeline operation with `op` and `args`
- `TargetTool`: Tool definition with name, description, and pipeline
- `SkillPipelineConfig`: Complete configuration with version

**Valid Operations:**
- Validation: `validate_required`, `validate_optional`, `validate_enum`, `validate_format`
- Resolution: `resolve_ecosystem`, `resolve_member`, `resolve_domain`, `resolve_agreement`, `resolve_proposal`
- Business Keys: `generate_business_key`
- CRUD: `create_record`, `read_record`, `update_record`, `delete_record`, `list_records`
- Transitions: `transition_status`
- Custom: `custom` (extensible)

### 3. Skill Loader (`neos_agent.skills.loader.py`)

Enhanced to parse pipeline configurations from skill frontmatter.

**Changes:**
- Added `pipeline_config` field to `ParsedSkill`
- Imports and uses `parse_pipeline_config` from schema module
- Validates pipeline configuration during skill parsing

**Backward Compatible:**
- Traditional SKILL.md files without `target_tool` still work
- Pipeline configuration is optional

### 4. Validation Primitives (`neos_agent.skills.validation_primitives.py`)

Common validation and resolution units for pipeline composition.

**Validation Functions:**
- `validate_required()`: Check required fields
- `validate_optional()`: Check optional fields
- `validate_enum()`: Check enum values
- `validate_format()`: Check format (uuid, email, date, datetime)

**Resolution Functions:**
- `resolve_ecosystem()`: Resolve by ID or name
- `resolve_member()`: Resolve by member_id or display_name
- `resolve_domain()`: Resolve by domain_id or name
- `resolve_agreement()`: Resolve by agreement_id
- `resolve_proposal()`: Resolve by proposal_id

**Helper Functions:**
- `generate_business_key()`: Generate unique business keys
- `validate_transition()`: Validate status transitions
- `parse_date()`, `parse_datetime()`: Date parsing utilities

### 5. Pipeline Executor (`neos_agent.skills.pipeline_executor.py`)

Runtime engine that executes skill pipelines by composing primitives.

**Key Classes:**
- `PipelineExecutor`: Executes pipelines with database session and ecosystem scope
- `PipelineExecutionError`: Raised when pipeline steps fail

**Execution Flow:**
1. Initialize executor with DB session and ecosystem scope
2. Execute each pipeline step in order
3. Maintain shared context across steps
4. Return success with context or error with details

**Step Execution:**
- Validation steps raise `ValidationError` on failure
- Resolution steps add resolved entities to context
- CRUD steps use auto-generated CRUD functions
- Context flows between steps (e.g., resolved ecosystem_id used in create)

### 6. Tool Registry (`neos_agent.agent.tool_registry.py`)

Integration layer that composes tool handlers from skill configurations.

**Key Classes:**
- `ToolDef`: Tool definition with name, description, handler, and parameters
- `ToolRegistry`: Manages tool registration and execution

**Features:**
- Register tools from individual skills
- Discover and register from directories
- Execute tools by name
- Extract parameter schemas from pipelines

**Usage:**
```python
from neos_agent.agent.tool_registry import create_composed_registry
from pathlib import Path

registry = create_composed_registry(Path("neos-core"))
tool = registry.get_tool("create_agreement_draft")
result = await tool.handler(args, db, ecosystem_ids)
```

## Migration Guide

### From Traditional to Pipeline-Based Skills

**Step 1: Add Pipeline Configuration**
```yaml
---
name: agreement-creation
description: "Create agreement draft"
layer: 2
version: 0.1.0
depends_on: [domain-mapping]
target_tool:
  name: create_agreement_draft
  pipeline:
    - op: validate_required
      args:
        fields: [title, type, proposer, domain, text]
    - op: resolve_member
      args:
        arg: proposer
    - op: create_record
      args:
        model: Agreement
        defaults:
          status: draft
---
```

**Step 2: Test Pipeline Execution**
```python
from neos_agent.skills.loader import parse_skill_file
from neos_agent.skills.pipeline_executor import create_tool_handler

skill = parse_skill_file(Path("SKILL.md"))
handler = create_tool_handler(skill.pipeline_config)
result = await handler(args, db, ecosystem_ids)
```

**Step 3: Register in Tool Registry**
```python
from neos_agent.agent.tool_registry import ToolRegistry

registry = ToolRegistry()
registry.register_from_skill(skill)
```

### Replacing governance_tools.py

**Current State:**
- `governance_tools.py` contains 29 hand-written tool handlers
- Each handler implements validation, resolution, and CRUD logic

**Migration Path:**
1. Create pipeline configurations for each tool
2. Test pipeline execution against existing tool behavior
3. Register composed tools in registry
4. Gradually replace hand-written handlers with composed ones
5. Keep hand-written handlers for complex custom logic

**Example Migration:**

**Before (governance_tools.py):**
```python
async def create_agreement_draft(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    # 100+ lines of validation, resolution, CRUD logic
    ...
```

**After (SKILL.md + pipeline):**
```yaml
target_tool:
  name: create_agreement_draft
  pipeline:
    - op: validate_required
      args:
        fields: [title, type, proposer, domain, text]
    - op: resolve_member
      args:
        arg: proposer
    - op: generate_business_key
      args:
        prefix: AGR
    - op: create_record
      args:
        model: Agreement
        defaults:
          status: draft
```

**Registry Integration:**
```python
from neos_agent.agent.tool_registry import ToolRegistry

# Register composed tools
registry = ToolRegistry()
registry.register_from_skills_directory(Path("neos-core"))

# Use composed tools
result = await registry.execute_tool("create_agreement_draft", args, db, ecosystem_ids)
```

## Benefits

### 1. Declarative Over Imperative
- Pipeline declared in YAML, not Python code
- Easier to read and maintain
- No code generation bugs from parsing prose

### 2. Composable Primitives
- Reuse validation/resolution across skills
- Single source of truth for common operations
- Changes to primitives benefit all skills

### 3. Type Safety
- Primitives have defined interfaces
- Validation at pipeline parse time
- Clear error messages

### 4. Testability
- Each primitive unit testable
- Pipeline execution testable
- Integration testing simplified

### 5. Maintainability
- No parameter drift
- Explicit parameter flow
- Version-controlled schema

### 6. Extensibility
- Custom operations via `custom` op
- New primitives added to framework
- Backward compatible with existing skills

## File Structure

```
neos-agent/src/neos_agent/
├── db/
│   ├── models/              # SQLAlchemy ORM models (47 files)
│   ├── crud_generator.py    # CRUD generation script
│   └── crud/                # Generated CRUD primitives (47 files)
├── skills/
│   ├── loader.py            # Enhanced with pipeline parsing
│   ├── pipeline_schema.py   # Pipeline schema definitions
│   ├── validation_primitives.py  # Validation/resolution units
│   └── pipeline_executor.py # Runtime pipeline execution
├── agent/
│   ├── governance_tools.py  # Existing hand-written tools
│   └── tool_registry.py     # Tool composition and registry
└── docs/
    ├── EXAMPLE_SKILL_PIPELINE.md  # Example pipeline configurations
    └── CODEGEN_FRAMEWORK.md       # This documentation
```

## Next Steps

1. **Complete CRUD Generation**: Ensure all 47 models have proper CRUD functions
2. **Add More Primitives**: Extend validation_primitives.py with additional operations
3. **Create Example Skills**: Convert existing skills to pipeline format
4. **Integration Testing**: Test composed tools against existing governance_tools
5. **Performance Optimization**: Cache pipeline execution, optimize context management
6. **Documentation**: Add more examples and migration guides

## Troubleshooting

### CRUD Generation Fails
- Ensure SQLAlchemy is installed in virtual environment
- Check that models package is importable
- Verify OUTPUT_DIR permissions

### Pipeline Validation Errors
- Check operation names match VALID_OPERATIONS
- Verify required arguments for each operation
- Ensure model names match actual model classes

### Execution Errors
- Check database session is active
- Verify ecosystem_ids are valid UUIDs
- Ensure resolved entities exist in database

### Tool Registration Issues
- Verify SKILL.md files have valid frontmatter
- Check pipeline configuration syntax
- Ensure skills directory path is correct
