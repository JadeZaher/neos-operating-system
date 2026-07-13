---
name: skill-name-here
description: "Pushy description that errs toward triggering this skill -- describe the governance function it performs."
layer: 0
version: 0.1.0
depends_on: []

# === Codegen v2 fields (deterministic tool generation) ===
target_tool:
  name: snake_case_tool_name          # Exact function name in governance_tools.py
  description: "One-line tool description for Claude API. Must match the tool's docstring."
  handler: governance_tools.snake_case_tool_name   # dotted path to handler function
  model: models.ModelClassName        # ORM model this tool primarily operates on
  action: create | read | update | delete | search  # CRUD action type

  parameters:
    - name: param_name
      type: string | integer | boolean | date | uuid | array | object
      required: true
      description: "One-line description for Claude API parameter docs."
    - name: optional_param
      type: string
      required: false
      description: "Optional parameter description."

  output:
    success_fields:
      - name: field_name
        type: string
        description: "Field in the success response."
    error_cases:
      - condition: "missing required field"
        message: "'{field}' is required."
      - condition: "member not found"
        message: "Proposer '{name}' is not an active member."
---

# skill-name-here

## A. Structural Problem It Solves

... (unchanged prose sections) ...
