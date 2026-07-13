# Governance Skill Pipeline Examples

This document demonstrates how NEOS governance skills can use the generic pipeline framework to orchestrate complex governance workflows.

## Harm Circle Process

```yaml
name: initiate_harm_circle
description: "Initiate a harm circle process with safety assessment and participant preparation"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [person_harmed, person_caused_harm, incident_description]
  - op: resolve
    args:
      entity_type: member
      arg: person_harmed
  - op: resolve
    args:
      entity_type: member
      arg: person_caused_harm
  - op: create_session
    args:
      session_type: harm_circle
      context:
        incident_type: safety
  - op: create
    args:
      entity: harm_circle
      defaults:
        status: preparation
        safety_flags: []
  - op: log_audit
    args:
      action: create
      entity_type: harm_circle
      entity_id: "{harm_circle_id}"
      actor: "{session_id}"
  - op: start_workflow
    args:
      workflow_type: harm_circle_process
      initial_context:
        circle_id: "{harm_circle_id}"
        session_id: "{session_id}"
```

## Governance Health Audit

```yaml
name: request_governance_audit
description: "Request a governance health audit with indicator scoring"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [audit_scope, co_signers]
  - op: resolve
    args:
      entity_type: ecosystem
      arg: ecosystem_id
  - op: create_session
    args:
      session_type: governance_audit
  - op: create
    args:
      entity: audit_request
      defaults:
        status: pending_team_formation
  - op: log_audit
    args:
      action: create
      entity_type: audit_request
      entity_id: "{audit_request_id}"
  - op: start_workflow
    args:
      workflow_type: audit_workflow
      initial_context:
        audit_id: "{audit_request_id}"
        indicators: [structural_diversity, participation_rate, decision_quality, conflict_resolution, resource_allocation, accountability, transparency, learning_adaptation]
```

## Emergency Management

```yaml
name: declare_emergency
description: "Declare an emergency with pre-authorization and authority activation"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [emergency_type, severity, justification]
  - op: validate
    args:
      type: enum
      field: severity
      values: [low, medium, high, critical]
  - op: resolve
    args:
      entity_type: emergency_criteria
      arg: emergency_type
  - op: transition
    args:
      entity: emergency_state
      field: state
      to: open
      transitions:
        closed: [open]
        open: [half_open, closed]
        half_open: [open, closed]
  - op: create_session
    args:
      session_type: emergency_declaration
  - op: create
    args:
      entity: emergency_declaration
      defaults:
        status: active
        authority_level: emergency
  - op: log_audit
    args:
      action: emergency_declare
      entity_type: emergency_declaration
      entity_id: "{emergency_declaration_id}"
      metadata:
        severity: "{severity}"
        justification: "{justification}"
  - op: start_workflow
    args:
      workflow_type: emergency_response
      initial_context:
        emergency_id: "{emergency_declaration_id}"
        authority_activated: true
```

## ACT Test Phase

```yaml
name: start_act_test_phase
description: "Start ACT test phase with success criteria and test reporting"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [proposal_id, test_duration, success_criteria]
  - op: resolve
    args:
      entity_type: proposal
      arg: proposal_id
  - op: transition
    args:
      entity: proposal
      field: status
      to: test
      transitions:
        consent: [test, reverted]
        test: [adopted, reverted]
  - op: create
    args:
      entity: proposal_test
      defaults:
        status: in_progress
  - op: create
    args:
      entity: success_criterion
      defaults:
        status: pending
  - op: log_audit
    args:
      action: test_phase_start
      entity_type: proposal_test
      entity_id: "{proposal_test_id}"
  - op: start_workflow
    args:
      workflow_type: act_test_workflow
      initial_context:
        test_id: "{proposal_test_id}"
        proposal_id: "{proposal_id}"
        success_criteria: "{success_criteria}"
```

## Culture Code Management

```yaml
name: create_culture_code
description: "Create a culture code for a domain with version control"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [domain_id, culture_code_content, version_description]
  - op: resolve
    args:
      entity_type: domain
      arg: domain_id
  - op: create
    args:
      entity: culture_code
      defaults:
        status: draft
        version: "1.0"
  - op: create_version
    args:
      entity: culture_code
      version_number: "1.0"
      change_description: "{version_description}"
  - op: log_audit
    args:
      action: create
      entity_type: culture_code
      entity_id: "{culture_code_id}"
  - op: index_entity
    args:
      entity_type: culture_code
      entity_id: "{culture_code_id}"
      content: "{culture_code_content}"
      tags: [culture, governance, domain]
```

## Economic Coordination

```yaml
name: allocate_resources
description: "Allocate resources through participatory funding process"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [funding_pool_id, allocation_proposal, amount]
  - op: resolve
    args:
      entity_type: funding_pool
      arg: funding_pool_id
  - op: create
    args:
      entity: participatory_allocation
      defaults:
        status: voting
  - op: create_session
    args:
      session_type: resource_allocation
  - op: start_workflow
    args:
      workflow_type: participatory_funding
      initial_context:
        allocation_id: "{participatory_allocation_id}"
        pool_id: "{funding_pool_id}"
        amount: "{amount}"
  - op: log_audit
    args:
      action: allocation_proposed
      entity_type: participatory_allocation
      entity_id: "{participatory_allocation_id}"
```

## Memory & Precedent System

```yaml
name: create_decision_record
description: "Create a decision record with semantic indexing for precedent search"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [decision_context, decision_outcome, rationale]
  - op: create
    args:
      entity: decision_record
      defaults:
        status: published
  - op: index_entity
    args:
      entity_type: decision_record
      entity_id: "{decision_record_id}"
      content: "{decision_context} {decision_outcome} {rationale}"
      tags: [decision, precedent, governance]
      metadata:
        decision_type: governance
        impact_level: high
  - op: log_audit
    args:
      action: create
      entity_type: decision_record
      entity_id: "{decision_record_id}"
  - op: semantic_search
    args:
      query: "similar governance decisions"
      entity_types: [decision_record]
      limit: 5
```

## Exit Portability

```yaml
name: initiate_exit_process
description: "Initiate exit process with commitment unwinding and portable record generation"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [member_id, exit_reason, commitments_to_unwind]
  - op: resolve
    args:
      entity_type: member
      arg: member_id
  - op: create_session
    args:
      session_type: exit_process
  - op: create
    args:
      entity: exit_process
      defaults:
        status: in_progress
  - op: create
    args:
      entity: commitment_unwinding
      defaults:
        status: tracking
  - op: start_workflow
    args:
      workflow_type: exit_portability
      initial_context:
        exit_id: "{exit_process_id}"
        member_id: "{member_id}"
        commitments: "{commitments_to_unwind}"
  - op: log_audit
    args:
      action: exit_initiated
      entity_type: exit_process
      entity_id: "{exit_process_id}"
      metadata:
        exit_reason: "{exit_reason}"
```

## Multi-Skill Workflow Example

```yaml
name: complete_agreement_lifecycle
description: "Complete agreement lifecycle from proposal to adoption with test phase"
version: 1.0.0
pipeline:
  # Phase 1: Create proposal
  - op: validate
    args:
      type: required
      fields: [title, type, proposer, domain, text]
  - op: resolve
    args:
      entity_type: member
      arg: proposer
  - op: resolve
    args:
      entity_type: domain
      arg: domain
  - op: generate_key
    args:
      pattern: "PROP-{year}-{seq}"
      prefix: PROP
  - op: create
    args:
      entity: proposal
      defaults:
        status: created
  - op: log_audit
    args:
      action: create
      entity_type: proposal
      entity_id: "{proposal_id}"
  
  # Phase 2: Advice phase
  - op: transition
    args:
      entity: proposal
      field: status
      to: advice
      transitions:
        created: [advice]
  - op: start_workflow
    args:
      workflow_type: advice_phase
      initial_context:
        proposal_id: "{proposal_id}"
  
  # Phase 3: Consent phase
  - op: transition
    args:
      entity: proposal
      field: status
      to: consent
      transitions:
        advice: [consent, withdrawn]
  
  # Phase 4: Test phase
  - op: transition
    args:
      entity: proposal
      field: status
      to: test
      transitions:
        consent: [test, reverted]
  - op: create
    args:
      entity: proposal_test
      defaults:
        status: in_progress
  - op: start_workflow
    args:
      workflow_type: act_test_workflow
      initial_context:
        proposal_id: "{proposal_id}"
  
  # Phase 5: Adoption
  - op: transition
    args:
      entity: proposal
      field: status
      to: adopted
      transitions:
        test: [adopted, reverted]
  - op: create
    args:
      entity: agreement
      defaults:
        status: active
        version: "1.0"
  - op: create_version
    args:
      entity: agreement
      version_number: "1.0"
      change_description: "Initial adoption from proposal {proposal_id}"
  - op: log_audit
    args:
      action: adopt
      entity_type: agreement
      entity_id: "{agreement_id}"
      metadata:
        from_proposal: "{proposal_id}"
```

## State Machine Transition Example

```yaml
name: transition_emergency_state
description: "Transition emergency state through open → half_open → closed lifecycle"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [emergency_id, target_state]
  - op: validate
    args:
      type: enum
      field: target_state
      values: [open, half_open, closed]
  - op: read
    args:
      entity: emergency_declaration
      key: emergency_id
  - op: transition
    args:
      entity: emergency_state
      field: state
      to: "{target_state}"
      transitions:
        closed: [open]
        open: [half_open, closed]
        half_open: [open, closed]
  - op: log_audit
    args:
      action: state_transition
      entity_type: emergency_state
      entity_id: "{emergency_id}"
      metadata:
        from_state: "{current_state}"
        to_state: "{target_state}"
```

## Cross-Skill Data Sharing Example

```yaml
name: create_agreement_from_precedent
description: "Create new agreement based on precedent with semantic search"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [domain, search_query]
  - op: semantic_search
    args:
      query: "{search_query}"
      entity_types: [agreement, decision_record]
      limit: 3
  - op: get_version
    args:
      entity: agreement
      version_id: "{precedent_version_id}"
  - op: create
    args:
      entity: agreement
      defaults:
        status: draft
        based_on_precedent: "{precedent_id}"
  - op: compare_versions
    args:
      entity: agreement
      version_id_1: "{precedent_version_id}"
      version_id_2: "{new_agreement_id}"
  - op: log_audit
    args:
      action: create_from_precedent
      entity_type: agreement
      entity_id: "{new_agreement_id}"
      metadata:
        precedent_id: "{precedent_id}"
```

## Agent Session Tracking Example

```yaml
name: multi_step_governance_workflow
description: "Multi-step governance workflow with agent session tracking"
version: 1.0.0
pipeline:
  - op: create_session
    args:
      session_type: governance_workflow
      context:
        workflow_name: "agreement_creation"
        user_intent: "create new governance agreement"
  - op: update_session
    args:
      session_id: "{session_id}"
      state: in_progress
      context:
        current_step: "validation"
  - op: validate
    args:
      type: required
      fields: [title, type, domain]
  - op: update_session
    args:
      session_id: "{session_id}"
      state: in_progress
      context:
        current_step: "resolution"
  - op: resolve
    args:
      entity_type: domain
      arg: domain
  - op: update_session
    args:
      session_id: "{session_id}"
      state: in_progress
      context:
        current_step: "creation"
  - op: create
    args:
      entity: agreement
  - op: update_session
    args:
      session_id: "{session_id}"
      state: completed
      context:
        current_step: "completed"
        result: "agreement_created"
```

## Framework Capabilities Summary

The generic pipeline framework now supports all governance skill requirements from the conductor tracks:

### ✅ Harm Circle Process
- Multi-step workflow orchestration
- Safety assessment tracking
- Participant resolution
- Session management

### ✅ Governance Health Audit
- Indicator-based scoring
- Audit workflow management
- Team formation and independence verification
- Comprehensive audit trails

### ✅ Emergency Management
- State machine transitions (open → half_open → closed)
- Pre-authorization protocols
- Authority activation
- Post-emergency review workflows

### ✅ ACT Test Phase
- Success criteria management
- Test reporting and outcome tracking
- Complete ACT lifecycle support
- Proposal state transitions

### ✅ Culture Code & Domain Hierarchy
- Version control for culture codes
- Hierarchical domain operations
- Structured element management
- Culture code versioning

### ✅ Economic Coordination
- Resource allocation workflows
- Participatory funding mechanisms
- Funding pool stewardship
- Economic transaction tracking

### ✅ Memory & Precedent System
- Semantic search capabilities
- Decision record management
- Precedent indexing and retrieval
- Cross-skill data sharing

### ✅ Exit Portability
- Commitment unwinding workflows
- Portable record generation
- Re-entry integration processes
- Exit process orchestration

### ✅ Agent Integration
- Session tracking and management
- Context preservation across skills
- MCP tool integration support
- Workflow orchestration

### ✅ System Integrity
- Comprehensive audit trails
- Version control for all entities
- Anti-capture detection support
- Integrity verification workflows
