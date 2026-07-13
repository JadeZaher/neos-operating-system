"""CRUD Generator — auto-generates CRUD primitives from SQLAlchemy models.

This script scans the neos_agent.db.models package and generates uniform CRUD
handlers (create, read_by_id, read_by_key, update, delete, list_filtered) for
each model. The generated handlers follow a consistent interface suitable for
composition into skill pipelines.

Usage:
    python -m neos_agent.db.crud_generator
"""

from __future__ import annotations

import inspect
import importlib
import pathlib
from typing import Any, get_type_hints

from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.orm import DeclarativeBase


MODELS_PACKAGE = "neos_agent.db.models"
OUTPUT_DIR = pathlib.Path(__file__).parent / "crud"


def get_model_classes() -> dict[str, type[DeclarativeBase]]:
    """Import and return all model classes from the models package."""
    models_module = importlib.import_module(MODELS_PACKAGE)
    
    model_classes = {}
    for name in dir(models_module):
        obj = getattr(models_module, name)
        # Skip private attributes and non-classes
        if name.startswith("_") or not inspect.isclass(obj):
            continue
        # Skip non-ORM classes (Base, GUID, TimestampMixin)
        if not hasattr(obj, "__tablename__"):
            continue
        model_classes[name] = obj
    
    return model_classes


def get_business_key_field(model_class: type[DeclarativeBase]) -> str | None:
    """Identify the business key field for a model (e.g., agreement_id, member_id)."""
    mapper = sqlalchemy_inspect(model_class)
    for column in mapper.columns:
        # Look for fields ending in _id that are not the primary key
        if column.key.endswith("_id") and not column.primary_key:
            return column.key
    return None


def get_required_fields(model_class: type[DeclarativeBase]) -> list[str]:
    """Get list of non-nullable fields (excluding auto-generated ones)."""
    mapper = sqlalchemy_inspect(model_class)
    required = []
    for column in mapper.columns:
        # Skip auto-generated fields (id, created_at, updated_at)
        if column.key in ("id", "created_at", "updated_at"):
            continue
        # Skip foreign keys that reference other tables
        if column.foreign_keys:
            continue
        # Include non-nullable fields
        if not column.nullable:
            required.append(column.key)
    return required


def generate_crud_module(model_name: str, model_class: type[DeclarativeBase]) -> str:
    """Generate CRUD handler code for a single model."""
    business_key = get_business_key_field(model_class)
    required_fields = get_required_fields(model_class)
    
    # Import statements
    imports = [
        "from __future__ import annotations",
        "",
        "import uuid",
        "from datetime import date, datetime",
        "from typing import Any, Optional",
        "",
        "from sqlalchemy import select, func, or_",
        "from sqlalchemy.ext.asyncio import AsyncSession",
        "from sqlalchemy.orm import selectinload",
        "",
        f"from {MODELS_PACKAGE} import {model_name}",
    ]
    
    # Helper function to resolve ecosystem_id
    ecosystem_helper = f"""

async def _get_first_ecosystem_id(
    db: AsyncSession, ecosystem_ids: list | None = None
) -> uuid.UUID | None:
    \"\"\"Return the first ecosystem ID from the caller's scope.

    If no scope is provided, fall back to looking up the lone active ecosystem.
    Returns None only when no scope is given AND the DB doesn't contain
    exactly one ecosystem.
    \"\"\"
    from neos_agent.db.models import Ecosystem
    
    if ecosystem_ids:
        return ecosystem_ids[0]
    stmt = select(Ecosystem.id).limit(2)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if len(rows) == 1:
        return rows[0]
    return None
"""
    
    # Generate create handler
    create_handler = f"""

async def create_{model_name.lower()}(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"Create a new {model_name} record.\"\"\"
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {{"success": False, "error": "No ecosystem configured."}}
    
    # Validate required fields
    required = {required_fields}
    for field in required:
        if field not in args or not args[field]:
            return {{"success": False, "error": f"'{{field}}' is required."}}
    
    # Create instance
    instance = {model_name}(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        **{{k: v for k, v in args.items() if k in required}}
    )
    db.add(instance)
    await db.flush()
    
    return {{
        "success": True,
        "data": {{
            "id": str(instance.id),
            "message": "{model_name} created successfully.",
        }},
    }}
"""
    
    # Generate read_by_id handler
    read_by_id = f"""

async def get_{model_name.lower()}_by_id(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"Get {model_name} by internal UUID id.\"\"\"
    id_str = args.get("id", "")
    if not id_str:
        return {{"success": False, "error": "id is required."}}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {{"success": False, "error": "Invalid UUID format for id."}}
    
    stmt = select({model_name}).where({model_name}.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where({model_name}.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {{"success": False, "error": f"{model_name} not found."}}
    
    # Convert to dict (simplified - could use serializer)
    data = {{
        "id": str(instance.id),
        "ecosystem_id": str(instance.ecosystem_id),
    }}
    # Add other fields dynamically
    mapper = sqlalchemy_inspect({model_name})
    for column in mapper.columns:
        if column.key not in ("id", "ecosystem_id"):
            value = getattr(instance, column.key)
            if isinstance(value, (date, datetime)):
                data[column.key] = str(value)
            elif isinstance(value, uuid.UUID):
                data[column.key] = str(value)
            else:
                data[column.key] = value
    
    return {{"success": True, "data": data}}
"""
    
    # Generate read_by_key handler if business key exists
    read_by_key = ""
    if business_key:
        read_by_key = f"""

async def get_{model_name.lower()}_by_{business_key}(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"Get {model_name} by business key {business_key}.\"\"\"
    key_value = args.get("{business_key}", "")
    if not key_value:
        return {{"success": False, "error": "{business_key} is required."}}
    
    stmt = select({model_name}).where({model_name}.{business_key} == key_value)
    if ecosystem_ids:
        stmt = stmt.where({model_name}.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {{"success": False, "error": f"{model_name} with {business_key}='{{key_value}}' not found."}}
    
    # Convert to dict
    data = {{
        "id": str(instance.id),
        "{business_key}": getattr(instance, business_key),
        "ecosystem_id": str(instance.ecosystem_id),
    }}
    
    return {{"success": True, "data": data}}
"""
    
    # Generate list_filtered handler
    list_filtered = f"""

async def list_{model_name.lower()}(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"List {model_name} records with optional filtering.\"\"\"
    stmt = select({model_name})
    
    if ecosystem_ids:
        stmt = stmt.where({model_name}.ecosystem_id.in_(ecosystem_ids))
    
    # Apply filters from args (simple equality filters)
    mapper = sqlalchemy_inspect({model_name})
    for column in mapper.columns:
        if column.key in args and args[column.key]:
            stmt = stmt.where(getattr({model_name}, column.key) == args[column.key])
    
    # Apply limit
    limit = args.get("limit", 50)
    stmt = stmt.limit(limit)
    
    result = await db.execute(stmt)
    instances = result.scalars().all()
    
    # Convert to list of dicts
    items = []
    for instance in instances:
        data = {{
            "id": str(instance.id),
            "ecosystem_id": str(instance.ecosystem_id),
        }}
        for column in mapper.columns:
            if column.key not in ("id", "ecosystem_id"):
                value = getattr(instance, column.key)
                if isinstance(value, (date, datetime)):
                    data[column.key] = str(value)
                elif isinstance(value, uuid.UUID):
                    data[column.key] = str(value)
                else:
                    data[column.key] = value
        items.append(data)
    
    return {{
        "success": True,
        "data": {{
            "items": items,
            "count": len(items),
        }},
    }}
"""
    
    # Generate update handler
    update_handler = f"""

async def update_{model_name.lower()}(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"Update {model_name} by id.\"\"\"
    id_str = args.get("id", "")
    if not id_str:
        return {{"success": False, "error": "id is required."}}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {{"success": False, "error": "Invalid UUID format for id."}}
    
    stmt = select({model_name}).where({model_name}.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where({model_name}.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {{"success": False, "error": f"{model_name} not found."}}
    
    # Update fields from args (excluding id and ecosystem_id)
    for key, value in args.items():
        if key not in ("id", "ecosystem_id") and hasattr(instance, key):
            setattr(instance, key, value)
    
    await db.flush()
    
    return {{
        "success": True,
        "data": {{
            "id": str(instance.id),
            "message": "{model_name} updated successfully.",
        }},
    }}
"""
    
    # Generate delete handler
    delete_handler = f"""

async def delete_{model_name.lower()}(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None
) -> dict:
    \"\"\"Delete {model_name} by id.\"\"\"
    id_str = args.get("id", "")
    if not id_str:
        return {{"success": False, "error": "id is required."}}
    
    try:
        id_uuid = uuid.UUID(id_str)
    except ValueError:
        return {{"success": False, "error": "Invalid UUID format for id."}}
    
    stmt = select({model_name}).where({model_name}.id == id_uuid)
    if ecosystem_ids:
        stmt = stmt.where({model_name}.ecosystem_id.in_(ecosystem_ids))
    
    result = await db.execute(stmt)
    instance = result.scalars().first()
    
    if instance is None:
        return {{"success": False, "error": f"{model_name} not found."}}
    
    await db.delete(instance)
    await db.flush()
    
    return {{
        "success": True,
        "data": {{
            "id": str(id_uuid),
            "message": "{model_name} deleted successfully.",
        }},
    }}
"""
    
    # Combine all parts
    code_parts = imports + [ecosystem_helper, create_handler, read_by_id, read_by_key, list_filtered, update_handler, delete_handler]
    return "\n".join(code_parts)


def generate_crud_package():
    """Generate CRUD modules for all models."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Generate __init__.py
    init_content = "\"\"\"Auto-generated CRUD primitives for NEOS models.\"\"\"\n\n"
    init_content += "# This file is auto-generated by crud_generator.py\n"
    init_content += "# Do not edit manually\n\n"
    
    model_classes = get_model_classes()
    
    for model_name, model_class in model_classes.items():
        print(f"Generating CRUD for {model_name}...")
        
        # Generate module
        module_code = generate_crud_module(model_name, model_class)
        
        # Write module file
        module_path = OUTPUT_DIR / f"{model_name.lower()}_crud.py"
        module_path.write_text(module_code, encoding="utf-8")
        
        # Add to __init__.py
        init_content += f"from .{model_name.lower()}_crud import (\n"
        init_content += f"    create_{model_name.lower()},\n"
        init_content += f"    get_{model_name.lower()}_by_id,\n"
        if get_business_key_field(model_class):
            bk = get_business_key_field(model_class)
            init_content += f"    get_{model_name.lower()}_by_{bk},\n"
        init_content += f"    list_{model_name.lower()},\n"
        init_content += f"    update_{model_name.lower()},\n"
        init_content += f"    delete_{model_name.lower()},\n"
        init_content += ")\n\n"
    
    # Write __init__.py
    (OUTPUT_DIR / "__init__.py").write_text(init_content, encoding="utf-8")
    
    print(f"\nCRUD primitives generated in {OUTPUT_DIR}")
    print(f"Generated {len(model_classes)} model CRUD modules")


if __name__ == "__main__":
    generate_crud_package()
