# Example Skill with Pipeline Configuration

This document demonstrates the new OKF-style pipeline configuration format for NEOS skills.

## Traditional SKILL.md Format

Traditional SKILL.md files contain natural language prose sections (D. Required Inputs, E. Step-by-Step Process, etc.) that describe the skill but require manual parsing to generate tool handlers.

## New Pipeline-Based Format

The new format adds a `target_tool` section to the YAML frontmatter that declaratively specifies the execution pipeline using composed primitives.

## Example: Agreement Creation Skill

```yaml
---
name: agreement-creation
description: "Create a new agreement in draft status with validation and business key generation"
layer: 2
version: 0.1.0
depends_on: [domain-mapping, member-resolution]
target_tool:
  name: create_agreement_draft
  description: "Create a new agreement draft with validated inputs and auto-generated business key"
  pipeline:
    - op: validate_required
      args:
        fields: [title, type, proposer, domain, text]
    - op: validate_enum
      args:
        field: type
        values: [space, access, organizational, uaf, culture_code]
    - op: resolve_ecosystem
      args:
        arg: ecosystem_id
    - op: resolve_member
      args:
        arg: proposer
    - op: resolve_domain
      args:
        arg: domain
    - op: generate_business_key
      args:
        prefix: AGR
    - op: create_record
      args:
        model: Agreement
        defaults:
          status: draft
          version: "0.1"
          hierarchy_level: domain
---

# agreement-creation

## C. Trigger Conditions

- A circle needs to formalize a working agreement
- An existing agreement needs to be amended
- A new domain requires governance structure

## D. Required Inputs

- **Title**: Agreement title
- **Type**: Agreement type (space, access, organizational, uaf, culture_code)
- **Proposer**: Member proposing the agreement
- **Domain**: Domain the agreement governs
- **Text**: Full agreement text

## E. Step-by-Step Process

1. Validate required fields are present
2. Validate agreement type is in allowed values
3. Resolve ecosystem context
4. Resolve proposer member identity
5. Resolve domain context
6. Generate business key (AGR-{domain}-{year}-{seq})
7. Create agreement record with defaults

## F. Output Artifact

Agreement record with generated business key, draft status, and version 0.1

## G. Authority Boundary Check

- Proposer must be active member in the ecosystem
- Domain must exist within the ecosystem

## H. Capture Resistance Check

- No single member can flood agreement creation
- Rate limits apply per proposer

## I. Failure Containment Logic

- Validation failures return clear error messages
- Resolution failures indicate missing entities

## J. Expiry / Review Condition

- Draft agreements expire after 90 days without status transition

## K. Exit Compatibility Check

- Agreement creator can exit; agreement remains with ecosystem

## L. Cross-Unit Interoperability Impact

- Cross-ecosystem agreements use shared_ecosystem_ids field
```

## Example: Proposal Creation Skill

```yaml
---
name: proposal-creation
description: "Create and submit a formal proposal through the ACT process"
layer: 3
version: 0.1.0
depends_on: [domain-mapping]
target_tool:
  name: create_proposal
  description: "Create a new proposal with ACT routing and consent mode determination"
  pipeline:
    - op: validate_required
      args:
        fields: [title, type, proposer, proposed_change, rationale]
    - op: validate_enum
      args:
        field: type
        values: [ecoplan, genplan, amendment, resource_request, policy_change]
    - op: resolve_ecosystem
      args:
        arg: ecosystem_id
    - op: resolve_member
      args:
        arg: proposer
    - op: resolve_domain
      args:
        arg: affected_domain
    - op: generate_business_key
      args:
        prefix: PROP
    - op: create_record
      args:
        model: Proposal
        defaults:
          status: created
          version: "1.0"
          decision_type: consent
---
```

## Pipeline Operation Reference

### Validation Operations

- **validate_required**: Ensures fields are present and non-empty
  - `fields`: List of required field names
  
- **validate_optional**: Ensures optional fields, if present, are non-empty
  - `fields`: List of optional field names
  
- **validate_enum**: Ensures field value is in allowed set
  - `field`: Field name to validate
  - `values`: List of allowed values
  
- **validate_format**: Ensures field matches format (uuid, email, date, datetime)
  - `field`: Field name to validate
  - `format`: Format type

### Resolution Operations

- **resolve_ecosystem**: Resolve ecosystem by ID or name
  - `arg`: Argument name containing ecosystem identifier
  
- **resolve_member**: Resolve member by member_id or display_name
  - `arg`: Argument name containing member identifier
  
- **resolve_domain**: Resolve domain by domain_id or name
  - `arg`: Argument name containing domain identifier
  
- **resolve_agreement**: Resolve agreement by agreement_id
  - `arg`: Argument name containing agreement identifier
  
- **resolve_proposal**: Resolve proposal by proposal_id
  - `arg`: Argument name containing proposal identifier

### Business Key Generation

- **generate_business_key**: Generate unique business key
  - `prefix`: Key prefix (AGR, PROP, etc.)
  - `pattern`: Optional pattern for key generation

### CRUD Operations

- **create_record**: Create new database record
  - `model`: Model class name (Agreement, Member, etc.)
  - `defaults`: Default field values
  
- **read_record**: Read record by key
  - `model`: Model class name
  - `key`: Field name to query by
  
- **update_record**: Update existing record
  - `model`: Model class name
  - `key`: Field name to identify record
  
- **delete_record**: Delete record
  - `model`: Model class name
  - `key`: Field name to identify record
  
- **list_records**: List records with filters
  - `model`: Model class name
  - `filters`: Optional filter criteria

### Transition Operations

- **transition_status**: Validate and execute status transition
  - `model`: Model class name
  - `field`: Status field name
  - `transitions`: Valid transition map

## Migration Path

Existing SKILL.md files can be gradually migrated to the new format:

1. Keep existing prose sections (C-L) for documentation
2. Add `target_tool` section to frontmatter
3. Define pipeline using composed primitives
4. Test pipeline execution
5. Remove prose sections once pipeline is validated

## Benefits

- **Declarative**: Pipeline is declared in YAML, not imperative code
- **Composable**: Reuse validation and resolution primitives across skills
- **Type-safe**: Primitives have defined interfaces and error handling
- **Testable**: Each primitive can be unit tested independently
- **Maintainable**: Changes to primitives automatically benefit all skills
- **No parameter drift**: Pipeline explicitly defines parameter flow
