# Agent Primitives and Context Management Matrix

## Overview

This document defines the complete agent primitive system that combines Alembic models, traits, functions, compliant skill formats, and configuration sections to create a perfect agent orchestration framework.

## The Perfect Agent Primitive Formula

```
Alembic Model + Trait + Functions with Traits + Compliant Skill Formats + Config Section = Agent Primitives & Context Management Matrix
```

## Core Components

### 1. Alembic Models (Data Foundation)

**Purpose**: Provide versioned, migratable database schema

**Implementation**:
- SQLAlchemy ORM models in `db/models/`
- Alembic migrations in `alembic/versions/`
- Automatic schema evolution
- Cross-database compatibility

**Example**:
```python
# db/models/agreement.py
class Agreement(Base):
    __tablename__ = "agreements"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    agreement_id: Mapped[str] = mapped_column(String(100))  # Business key
    status: Mapped[str] = mapped_column(String(50))
    # ... other fields
```

**Benefits**:
- Version-controlled schema
- Automatic migrations
- Type safety
- Relationship management

### 2. Traits (Behavioral Composability)

**Purpose**: Reusable behavioral patterns that can be composed onto models

**Implementation**:
- Trait classes with mixin methods
- Trait registry for dynamic composition
- Trait validation and conflict resolution

**Example**:
```python
# traits/auditable.py
class AuditableTrait:
    """Trait for entities that require audit trails."""
    
    async def log_audit(self, action: str, actor: str, changes: dict):
        """Log an audit event for this entity."""
        audit_record = AuditLog(
            entity_type=self.__class__.__name__,
            entity_id=self.id,
            action=action,
            actor=actor,
            changes=changes,
        )
        # ... save audit record

# traits/versioned.py
class VersionedTrait:
    """Trait for entities that support versioning."""
    
    async def create_version(self, change_description: str):
        """Create a new version of this entity."""
        version = EntityVersion(
            entity_type=self.__class__.__name__,
            entity_id=self.id,
            version_number=self.version + 1,
            change_description=change_description,
            data=self.to_dict(),
        )
        # ... save version

# traits/resolvable.py
class ResolvableTrait:
    """Trait for entities that can be resolved by identifiers."""
    
    @classmethod
    async def resolve_by_identifier(cls, identifier: str, db: AsyncSession, scope: dict):
        """Resolve entity by business key or UUID."""
        # ... resolution logic
```

**Benefits**:
- Composable behaviors
- Reusable patterns
- DRY principle
- Flexible model enhancement

### 3. Functions with Traits (Operation Layer)

**Purpose**: Domain-specific operations composed from traits

**Implementation**:
- CRUD functions generated from models
- Trait-enhanced operations
- Context-aware execution
- Error handling and validation

**Example**:
```python
# crud/agreement_crud.py
async def create_agreement(
    args: dict,
    db: AsyncSession,
    scope: dict | None = None
) -> dict:
    """Create agreement with audit trail and versioning."""
    # Use AuditableTrait
    await agreement.log_audit("create", scope.get("actor"), args)
    
    # Use VersionedTrait
    await agreement.create_version("Initial creation")
    
    # Use ResolvableTrait
    resolved = await Agreement.resolve_by_identifier(args["agreement_id"], db, scope)
    
    return {"success": True, "data": agreement.to_dict()}
```

**Benefits**:
- Consistent operations
- Automatic trait application
- Context awareness
- Error handling

### 4. Compliant Skill Formats (Declarative Configuration)

**Purpose**: YAML-based skill declarations that define agent capabilities

**Implementation**:
- SKILL.md files with YAML frontmatter
- Pipeline configuration
- Operation composition
- Validation and error handling

**Example**:
```yaml
---
name: agreement-creation
description: "Create a new agreement with validation and audit trail"
version: 1.0.0
traits: [auditable, versioned, resolvable]
target_tool:
  name: create_agreement
  pipeline:
    - op: validate
      args:
        type: required
        fields: [title, type, domain]
    - op: resolve
      args:
        entity_type: domain
        arg: domain
    - op: create
      args:
        entity: agreement
        defaults:
          status: draft
    - op: log_audit
      args:
        action: create
        entity_type: agreement
    - op: create_version
      args:
        entity: agreement
        change_description: "Initial creation"
---

# agreement-creation

## C. Trigger Conditions
- A circle needs to formalize a working agreement
- ...
```

**Benefits**:
- Declarative configuration
- No code generation needed
- Version-controlled skills
- Easy to understand and modify

### 5. Config Section (Context Management)

**Purpose**: Provide context and configuration for agent execution

**Implementation**:
- Agent configuration file
- Context injection
- Scope management
- Environment variables

**Example**:
```yaml
# agent/config.yaml
agent:
  name: "NEOS Governance Agent"
  version: "1.0.0"
  
context:
  default_scope:
    - ecosystem_ids
    - tenant_id
    - member_id
  
  session_management:
    enabled: true
    persistence: database
    ttl: 3600
  
  audit:
    enabled: true
    log_level: info
    include_changes: true
  
  versioning:
    enabled: true
    auto_create: true
    max_versions: 100
  
traits:
  auditable:
    enabled: true
    log_all_operations: true
  
  versioned:
    enabled: true
    auto_increment: true
  
  resolvable:
    enabled: true
    cache_ttl: 300

operations:
  validate:
    enabled: true
    strict_mode: true
  
  resolve:
    enabled: true
    cache_enabled: true
  
  create:
    enabled: true
    audit_required: true
    version_required: true
```

**Benefits**:
- Centralized configuration
- Environment-specific settings
- Feature toggles
- Context injection

## Context Management Matrix

### Context Layers

```
┌─────────────────────────────────────────────┐
│         Agent Session Context                │
│  (session_id, user_id, conversation_state)   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Ecosystem Scope Context               │
│  (ecosystem_ids, tenant_id, permissions)     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Page/Workflow Context                 │
│  (current_page, active_skill, workflow_id)   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Pipeline Execution Context            │
│  (resolved_entities, generated_keys, state) │
└─────────────────────────────────────────────┘
```

### Context Flow

1. **Agent Session Context**: Created when user starts conversation
   - Session ID for tracking
   - User authentication
   - Conversation state

2. **Ecosystem Scope Context**: Injected from environment
   - Ecosystem IDs for multi-tenant
   - Tenant ID for SaaS
   - User permissions

3. **Page/Workflow Context**: From frontend
   - Current page context
   - Active skill
   - Workflow state

4. **Pipeline Execution Context**: Built during execution
   - Resolved entities
   - Generated keys
   - Intermediate state

### Context Injection Points

```python
# Frontend → Agent
context = {
    "session_id": "uuid",
    "user_id": "uuid",
    "ecosystem_ids": ["uuid"],
    "tenant_id": "uuid",
    "page_context": {
        "current_page": "/agreements",
        "active_skill": "agreement-creation",
        "summary": "User viewing agreement list"
    }
}

# Agent → Pipeline
executor = PipelineExecutor(db, scope=context)

# Pipeline → Handlers
async def handler(args, context, db):
    scope = context.get("scope", {})
    ecosystem_ids = scope.get("ecosystem_ids")
    # ... use context
```

## Agent Skill Best Practices

### 1. Skill Structure

**Required Elements**:
- YAML frontmatter with metadata
- Pipeline configuration
- Trigger conditions (Section C)
- Required inputs (Section D)
- Step-by-step process (Section E)
- Output artifact (Section F)

**Best Practices**:
- Keep pipelines under 10 steps
- Use validation first
- Resolve dependencies before use
- Log audit events
- Create versions for state changes

### 2. Tool Use Best Practices

**Required Elements**:
- Clear tool name and description
- Input validation
- Error handling
- Context awareness
- Audit logging

**Best Practices**:
- Use generic operations when possible
- Register custom handlers for domain logic
- Return consistent result format
- Include error messages
- Log all state changes

### 3. Context Management Best Practices

**Required Elements**:
- Session tracking
- Scope injection
- Context preservation
- Privacy controls
- Audit trails

**Best Practices**:
- Use hierarchical context
- Inject scope at executor level
- Preserve context across pipeline steps
- Respect privacy settings
- Log context access

## Open Source Compatibility

### Generic Design Principles

1. **Framework Agnostic**: Works with any ORM, not just SQLAlchemy
2. **Database Agnostic**: Supports PostgreSQL, MySQL, SQLite, etc.
3. **Frontend Agnostic**: Works with React, Vue, Svelte, vanilla JS
4. **Agent Agnostic**: Compatible with Claude, GPT, local models
5. **Domain Agnostic**: Not tied to NEOS governance

### Configuration-Based

All behavior defined in YAML configuration files:
- Skill definitions
- Pipeline configurations
- Agent settings
- Trait configurations
- Context rules

### Pluggable Architecture

- Custom operation handlers
- Custom traits
- Custom validators
- Custom resolvers
- Custom workflow orchestrators

### API Compatibility

Standardized API contracts:
- Tool execution interface
- Context injection interface
- Result format
- Error handling
- Audit logging

## Frontend Integration

### Chat Interface Requirements

**Bubble Chat**:
- Compact design
- Quick actions
- Context summary
- Tool call display
- Session management

**Dedicated Page**:
- Full-featured interface
- Session sidebar
- Privacy controls
- Advanced context
- Workflow visualization

### Context Passing

```typescript
// Frontend → Agent
const context = {
  selectedEcosystemIds: ecosystemIds,
  pageContextSummary: getAISummary(),
  member: { id: member.id, display_name: member.display_name },
  ecosystemName: ecosystem.name,
  sessionId: sessionId,
  privacy: privacy,
};

// Agent → Frontend
interface AgentResponse {
  success: boolean;
  data: any;
  context: {
    session_id: string;
    active_skill: string;
    workflow_state: any;
  };
  tools: ToolCall[];
  artifacts: Artifact[];
}
```

### Tool Call Display

- Show tool name
- Show tool status
- Show tool result
- Link to artifacts
- Show thinking steps

## Commit Preparation

### Files to Commit

**Framework Core**:
- `agent/src/neos_agent/skills/pipeline_schema.py` (refactored to generic)
- `agent/src/neos_agent/skills/pipeline_executor.py` (refactored to generic)
- `agent/src/neos_agent/skills/loader.py` (updated for generic schema)
- `agent/src/neos_agent/agent/tool_registry.py` (refactored to generic)
- `agent/src/neos_agent/agent/neos_handlers.py` (NEOS-specific handlers)
- `agent/src/neos_agent/db/crud_generator.py` (CRUD generation)
- `agent/src/neos_agent/db/crud/` (generated CRUD modules)

**Documentation**:
- `agent/docs/GENERIC_PACKAGE_GUIDE.md` (generic usage guide)
- `agent/docs/GOVERNANCE_SKILL_PIPELINES.md` (skill examples)
- `agent/docs/AGENT_PRIMITIVES_MATRIX.md` (this document)
- `agent/docs/CODEGEN_FRAMEWORK.md` (updated)

**Tests**:
- `agent/test_pipeline.yaml` (test configuration)
- `agent/test_generic_framework.py` (end-to-end test)

### Commit Message

```
feat: Implement generic pipeline framework for agent orchestration

- Refactor pipeline schema to be framework-agnostic with extensible operation registry
- Add comprehensive operations: version control, audit trails, semantic search, workflow orchestration
- Implement pluggable handler system for domain-specific logic
- Create NEOS-specific handlers for governance operations
- Add end-to-end test suite validating framework with existing models
- Document generic package usage and governance skill pipeline examples
- Define agent primitives matrix: Alembic models + traits + functions + skill formats + config
- Ensure open-source compatibility with framework-agnostic design

This framework provides a declarative, composable system for orchestrating
domain logic through YAML configurations, supporting any SQLAlchemy models
and domain logic through pluggable handlers.
```

### Breaking Changes

- Pipeline schema renamed from NEOS-specific to generic operations
- Handler registration required for domain-specific operations
- Context injection changed from ecosystem_ids to generic scope dict

### Migration Guide

1. Update pipeline configurations to use generic operations
2. Register domain-specific handlers
3. Update context passing to use scope dict
4. Test existing skills with new framework

## Summary

The generic pipeline framework provides the perfect agent primitive system by combining:

1. **Alembic Models**: Versioned, migratable data foundation
2. **Traits**: Composable behavioral patterns
3. **Functions with Traits**: Domain-specific operations
4. **Compliant Skill Formats**: Declarative YAML configurations
5. **Config Section**: Centralized context management

This creates a complete agent orchestration framework that is:
- Generic and reusable across domains
- Open-source compatible
- Frontend agnostic
- Database agnostic
- Agent agnostic
- Configuration-based
- Extensible through plugins

The framework satisfies all NEOS governance skill requirements while being generic enough to plug into any open-source agent system.
