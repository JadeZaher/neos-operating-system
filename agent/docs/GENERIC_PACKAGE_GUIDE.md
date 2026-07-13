# Generic Domain Logic Orchestration Package

This guide explains how to use the pipeline framework as a generic package for orchestrating domain logic and data strategy with any SQLAlchemy models.

## Overview

The pipeline framework provides a declarative, composable way to define and execute domain logic operations through YAML/JSON configurations. It works with any SQLAlchemy models and can be extended for any domain.

## Architecture

```
+-------------------------------------------------------------+
|              Domain-Specific SQLAlchemy Models               |
|              (Your ORM models - any domain)                  |
+-------------------------------------------------------------+
                              |
                              v  (Auto-generated or custom)
+-------------------------------------------------------------+
|              CRUD/Domain Operation Handlers                  |
|              (Your domain-specific logic)                     |
+-------------------------------------------------------------+
                              |
                              v  (Declared in YAML/JSON)
+-------------------------------------------------------------+
|              Generic Pipeline Configuration                  |
|              (validate, resolve, create, etc.)                |
+-------------------------------------------------------------+
                              |
                              v  (Composed at runtime)
+-------------------------------------------------------------+
|              Generic Pipeline Executor                       |
|              (Pluggable handler registry)                    |
+-------------------------------------------------------------+
                              |
                              v  (Exposed as tools)
+-------------------------------------------------------------+
|              Your Application Interface                       |
|              (API, CLI, agent, etc.)                         |
+-------------------------------------------------------------+
```

## Core Components

### 1. Pipeline Schema (`pipeline_schema.py`)

Framework-agnostic schema definitions with extensible operation registry.

**Key Features:**
- Generic operation types (validate, resolve, create, etc.)
- Extensible operation registry for custom operations
- Support for both YAML and JSON configurations
- Validation against operation schemas

**Built-in Operations:**
- **validate**: Field validation (required, optional, enum, format)
- **transform**: Data transformation and normalization
- **resolve**: Entity resolution by identifier
- **generate_key**: Business key generation
- **create/read/update/delete**: CRUD operations
- **transition**: State machine transitions
- **branch/parallel/loop**: Workflow control flow
- **http_request/message**: External integrations
- **custom**: Custom handler execution

### 2. Pipeline Executor (`pipeline_executor.py`)

Generic runtime engine with pluggable operation handlers.

**Key Features:**
- Pluggable handler registry for domain-specific logic
- Shared context across pipeline steps
- Generic error handling and validation
- Scope support (multi-tenant, ecosystem, etc.)

### 3. Tool Registry (`tool_registry.py`)

Integration layer for composing tools from configurations.

**Key Features:**
- Register tools from pipeline configurations
- Execute tools by name
- Parameter schema extraction
- Handler registry injection

## Usage Examples

### Example 1: E-Commerce Order Processing

**Domain Models:**
```python
# models.py
from sqlalchemy import ORM
from datetime import datetime

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))

class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    sku: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50))
    customer_id: Mapped[uuid.UUID] = mapped_column(GUID())
    status: Mapped[str] = mapped_column(String(50))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
```

**Pipeline Configuration:**
```yaml
name: create_order
description: "Create a new order with validation and business key generation"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [customer_email, items]
  - op: validate
    args:
      type: format
      field: customer_email
      format: email
  - op: resolve
    args:
      entity_type: customer
      arg: customer_email
      by_field: email
  - op: generate_key
    args:
      pattern: "ORD-{year}-{seq}"
      prefix: ORD
  - op: create
    args:
      entity: order
      defaults:
        status: pending
```

**Domain-Specific Handlers:**
```python
# handlers.py
from sqlalchemy import select
from pipeline_executor import PipelineExecutor

async def resolve_customer_handler(args, context, db):
    """Resolve customer by email."""
    email = args.get("arg_value") or context.get("customer_email")
    stmt = select(Customer).where(Customer.email == email)
    result = await db.execute(stmt)
    customer = result.scalars().first()
    
    if not customer:
        raise ValidationError("customer", f"Customer with email {email} not found")
    
    return {"customer_id": customer.id, "customer": customer}

async def create_order_handler(args, context, db):
    """Create order with items."""
    order_data = {
        "id": uuid.uuid4(),
        "order_number": context.get("generated_key"),
        "customer_id": context.get("customer_id"),
        "status": args.get("defaults", {}).get("status", "pending"),
        "total": calculate_total(context.get("items")),
    }
    
    order = Order(**order_data)
    db.add(order)
    await db.flush()
    
    return {"order_id": order.id, "order_number": order.order_number}

# Register handlers
registry = ToolRegistry(handler_registry={
    "resolve": resolve_customer_handler,
    "create": create_order_handler,
})
```

### Example 2: Healthcare Patient Management

**Pipeline Configuration:**
```yaml
name: register_patient
description: "Register new patient with validation and record creation"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [name, date_of_birth, contact_email]
  - op: validate
    args:
      type: format
      field: date_of_birth
      format: date
  - op: validate
    args:
      type: format
      field: contact_email
      format: email
  - op: generate_key
    args:
      pattern: "PAT-{year}-{seq}"
      prefix: PAT
  - op: create
    args:
      entity: patient
      defaults:
        registration_status: active
  - op: transition
    args:
      entity: patient
      field: registration_status
      to: active
      transitions:
        pending: [active, rejected]
        active: [inactive]
        inactive: [active]
```

### Example 3: Manufacturing Workflow

**Pipeline with Control Flow:**
```yaml
name: process_manufacturing_order
description: "Process manufacturing order with quality checks"
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [product_id, quantity, due_date]
  - op: resolve
    args:
      entity_type: product
      arg: product_id
  - op: branch
    args:
      condition: quantity > 1000
      if_true:
        - op: custom
          args:
            handler: require_manager_approval
      if_false:
        - op: custom
          args:
            handler: auto_approve
  - op: create
    args:
      entity: manufacturing_order
  - op: parallel
    args:
      steps:
        - op: custom
          args:
            handler: schedule_production
        - op: custom
          args:
            handler: reserve_materials
  - op: loop
    args:
      over: [quality_check_1, quality_check_2, quality_check_3]
      steps:
        - op: custom
          args:
            handler: perform_quality_check
```

## Setting Up for Your Domain

### Step 1: Define Your Models

```python
# your_models.py
from sqlalchemy import ORM
from your_base import Base

class YourEntity(Base):
    __tablename__ = "your_entities"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True)
    business_key: Mapped[str] = mapped_column(String(50))
    # ... your fields
```

### Step 2: Create Domain Handlers

```python
# your_handlers.py
from sqlalchemy import select

async def your_resolve_handler(args, context, db):
    """Resolve your entity by identifier."""
    identifier = args.get("arg_value")
    stmt = select(YourEntity).where(YourEntity.business_key == identifier)
    result = await db.execute(stmt)
    entity = result.scalars().first()
    
    if not entity:
        raise ValidationError("entity", f"Entity {identifier} not found")
    
    return {"entity_id": entity.id, "entity": entity}

async def your_create_handler(args, context, db):
    """Create your entity."""
    entity = YourEntity(
        id=uuid.uuid4(),
        business_key=context.get("generated_key"),
        # ... merge args, context, defaults
    )
    db.add(entity)
    await db.flush()
    
    return {"id": entity.id, "business_key": entity.business_key}
```

### Step 3: Register Handlers and Create Registry

```python
# your_app.py
from pipeline_executor import PipelineExecutor
from tool_registry import ToolRegistry, create_composed_registry

# Define handler registry
handler_registry = {
    "resolve": your_resolve_handler,
    "create": your_create_handler,
    # ... add more handlers as needed
}

# Create tool registry
registry = create_composed_registry(
    skills_dir=Path("your_pipeline_configs"),
    handler_registry=handler_registry
)

# Or register individual configs
from pipeline_schema import load_pipeline_config_from_yaml

config, errors = load_pipeline_config_from_yaml(yaml_content)
if not errors:
    registry.register_from_config(config)
```

### Step 4: Execute Tools

```python
# Execute tool
result = await registry.execute_tool(
    "your_tool_name",
    {"field1": "value1", "field2": "value2"},
    db_session,
    scope={"tenant_id": tenant_id}
)

if result["success"]:
    print(f"Success: {result['data']}")
else:
    print(f"Error: {result['error']}")
```

## Extending the Framework

### Adding Custom Operations

```python
from pipeline_schema import get_operation_registry

registry = get_operation_registry()

registry.register_operation("your_custom_op", {
    "description": "Your custom operation",
    "required_args": ["field1"],
    "optional_args": ["field2", "field3"],
})

# Register handler
executor.register_handler("your_custom_op", your_custom_handler)
```

### Custom Validation Types

```python
async def custom_validate_handler(args, context, db):
    """Custom validation logic."""
    validate_type = args.get("type")
    
    if validate_type == "your_custom_type":
        # Your validation logic
        field = args.get("field")
        value = context.get(field)
        
        if not your_validation_function(value):
            raise ValidationError(field, "Custom validation failed")
    
    return {}

executor.register_handler("validate", custom_validate_handler)
```

### Integration with Alembic

The framework works seamlessly with Alembic migrations:

1. **Model-First Approach**: Define SQLAlchemy models, use Alembic for migrations
2. **CRUD Generation**: Use or extend the CRUD generator for your models
3. **Pipeline Configuration**: Define pipelines that work with your current schema
4. **Schema Evolution**: Update pipelines when schema changes via Alembic

```python
# Example: Schema-aware pipeline
- op: validate
  args:
    type: required
    fields: [new_field_added_in_migration]  # Works after migration
```

## Configuration Formats

### YAML Format

```yaml
name: your_tool
version: 1.0.0
pipeline:
  - op: validate
    args:
      type: required
      fields: [field1, field2]
```

### JSON Format

```json
{
  "name": "your_tool",
  "version": "1.0.0",
  "pipeline": [
    {
      "op": "validate",
      "args": {
        "type": "required",
        "fields": ["field1", "field2"]
      }
    }
  ]
}
```

### Python Dict Format

```python
config = {
    "name": "your_tool",
    "version": "1.0.0",
    "pipeline": [
        {
            "op": "validate",
            "args": {
                "type": "required",
                "fields": ["field1", "field2"]
            }
        }
    ]
}

from pipeline_schema import parse_pipeline_config
parsed_config, errors = parse_pipeline_config(config)
```

## Best Practices

### 1. Handler Design
- Keep handlers focused and single-purpose
- Use consistent error handling (ValidationError for validation errors)
- Return dict results that merge into context
- Use async/await for database operations

### 2. Pipeline Design
- Start with validation steps
- Resolve dependencies before using them
- Use context to share resolved entities
- Keep pipelines under 10 steps for maintainability

### 3. Error Handling
- Use ValidationError for input validation
- Use PipelineExecutionError for logic errors
- Provide clear error messages
- Log errors for debugging

### 4. Testing
- Unit test individual handlers
- Integration test pipeline execution
- Test error scenarios
- Test with different scope values

### 5. Performance
- Use database indexes for resolved fields
- Cache frequently resolved entities
- Batch operations when possible
- Use async for concurrent operations

## Migration from NEOS-Specific Code

If you're migrating from the NEOS-specific implementation:

1. **Update Operation Names**: Change NEOS-specific ops to generic ops
   - `validate_required` → `validate` with `type: required`
   - `resolve_member` → `resolve` with `entity_type: member`
   - `create_record` → `create` with `entity: your_model`

2. **Register Domain Handlers**: Create handlers for your domain logic
3. **Update Scope**: Use generic scope dict instead of ecosystem_ids
4. **Update Configurations**: Convert YAML configs to use generic operations

## Package Structure for Reuse

To use this as a standalone package:

```
your-orchestration-package/
├── your_domain/
│   ├── models.py              # Your SQLAlchemy models
│   ├── handlers.py            # Your domain handlers
│   └── pipelines/             # Your pipeline configs
│       ├── tool1.yaml
│       └── tool2.yaml
├── orchestration/
│   ├── pipeline_schema.py     # Generic schema (from this framework)
│   ├── pipeline_executor.py  # Generic executor (from this framework)
│   └── tool_registry.py      # Generic registry (from this framework)
└── your_app.py               # Your application entry point
```

## Conclusion

This framework provides a generic, extensible foundation for orchestrating domain logic across any SQLAlchemy-based application. The declarative pipeline configuration separates business logic from implementation, making it easier to maintain, test, and evolve your domain operations.
