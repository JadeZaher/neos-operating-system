"""Generic pipeline executor for domain logic orchestration.

This module provides a framework-agnostic runtime engine that executes
pipeline configurations by composing validation, resolution, CRUD, and
custom operations into callable handlers. Works with any SQLAlchemy models
and domain logic.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from neos_agent.skills.pipeline_schema import (
    PipelineStep,
    PipelineConfig,
    OperationRegistry,
    get_operation_registry,
)


class ValidationError(Exception):
    """Raised when validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class PipelineExecutionError(Exception):
    """Raised when pipeline execution fails."""
    def __init__(self, step: int, message: str):
        self.step = step
        self.message = message
        super().__init__(f"Step {step}: {message}")


class OperationHandler:
    """Base class for operation handlers."""
    
    async def execute(self, args: dict, context: dict[str, Any], db: AsyncSession) -> Any:
        """Execute the operation.
        
        Args:
            args: Operation-specific arguments
            context: Shared pipeline context
            db: Database session
            
        Returns:
            Operation result (added to context)
        """
        raise NotImplementedError


class PipelineExecutor:
    """Generic pipeline executor for domain logic orchestration.
    
    Executes pipeline configurations by composing operation handlers.
    Works with any SQLAlchemy models and domain logic through
    pluggable operation handlers.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        operation_registry: OperationRegistry | None = None,
        scope: dict[str, Any] | None = None
    ):
        """Initialize executor with database session and operation registry.
        
        Args:
            db: Async database session
            operation_registry: Operation registry (uses global if None)
            scope: Optional scope dict (e.g., ecosystem_ids, tenant_id)
        """
        self.db = db
        self.registry = operation_registry or get_operation_registry()
        self.scope = scope or {}
        self.context: dict[str, Any] = {}  # Shared context across pipeline steps
        self.handlers: dict[str, Callable] = {}  # Registered operation handlers
    
    def register_handler(self, operation: str, handler: Callable) -> None:
        """Register a custom operation handler.
        
        Args:
            operation: Operation name
            handler: Async function that takes (args, context, db) and returns result
        """
        self.handlers[operation] = handler
    
    async def execute(self, config: PipelineConfig, args: dict) -> dict:
        """Execute a complete pipeline.
        
        Args:
            config: Pipeline configuration
            args: Input arguments for the tool
            
        Returns:
            Result dict with success/data or error
        """
        try:
            # Add scope to context for handlers to access
            self.context["scope"] = self.scope
            
            # Add input args to context
            self.context.update(args)
            
            # Execute each step in order
            for i, step in enumerate(config.target_tool.pipeline):
                result = await self._execute_step(step, args, i)
                
                # Update context with step results
                if isinstance(result, dict):
                    self.context.update(result)
            
            # Return success with context
            return {
                "success": True,
                "data": self.context,
                "tool": config.target_tool.name,
            }
        
        except ValidationError as e:
            return {
                "success": False,
                "error": f"Validation error: {e.message}",
                "field": e.field,
            }
        
        except PipelineExecutionError as e:
            return {
                "success": False,
                "error": e.message,
                "step": e.step,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Pipeline execution failed: {str(e)}",
            }
    
    async def _execute_step(self, step: PipelineStep, args: dict, step_index: int) -> Any:
        """Execute a single pipeline step.
        
        Args:
            step: Pipeline step to execute
            args: Input arguments
            step_index: Step index for error reporting
            
        Returns:
            Step result (added to context)
        """
        op = step.op
        step_args = step.args
        
        # Check if custom handler is registered
        if op in self.handlers:
            handler = self.handlers[op]
            try:
                result = await handler(step_args, self.context, self.db)
                return result
            except Exception as e:
                raise PipelineExecutionError(step_index, f"Handler '{op}' failed: {str(e)}")
        
        # Built-in generic operations
        # These are stub implementations - domains should register their own handlers
        # or use the generic handler registry
        
        if op == "validate":
            return await self._handle_validate(step_args, args)
        
        elif op == "transform":
            return await self._handle_transform(step_args, args)
        
        elif op == "resolve":
            return await self._handle_resolve(step_args, args, step_index)
        
        elif op == "generate_key":
            return await self._handle_generate_key(step_args, step_index)
        
        elif op in ("create", "read", "update", "delete"):
            return await self._handle_crud(op, step_args, args, step_index)
        
        elif op == "transition":
            return await self._handle_transition(step_args, args, step_index)
        
        elif op == "branch":
            return await self._handle_branch(step_args, args)
        
        elif op == "parallel":
            return await self._handle_parallel(step_args, args, step_index)
        
        elif op == "loop":
            return await self._handle_loop(step_args, args, step_index)
        
        elif op == "custom":
            return await self._handle_custom(step_args, step_index)
        
        # Version control operations
        elif op in ("create_version", "get_version", "list_versions", "compare_versions"):
            return await self._handle_version_control(op, step_args, step_index)
        
        # Audit trail operations
        elif op in ("log_audit", "get_audit_trail"):
            return await self._handle_audit_trail(op, step_args, step_index)
        
        # Agent session operations
        elif op in ("create_session", "update_session", "get_session"):
            return await self._handle_agent_session(op, step_args, step_index)
        
        # Semantic search operations
        elif op in ("index_entity", "semantic_search", "get_similar"):
            return await self._handle_semantic_search(op, step_args, step_index)
        
        # Workflow orchestration operations
        elif op in ("start_workflow", "advance_workflow", "get_workflow_state", "cancel_workflow"):
            return await self._handle_workflow_orchestration(op, step_args, step_index)
        
        else:
            raise PipelineExecutionError(step_index, f"Unknown operation '{op}'")
    
    async def _handle_validate(self, step_args: dict, args: dict) -> dict:
        """Handle validate operation."""
        validate_type = step_args.get("type")
        
        if validate_type == "required":
            fields = step_args.get("fields", [])
            for field in fields:
                if field not in args or not args[field]:
                    raise ValidationError(field, f"'{field}' is required")
        
        elif validate_type == "optional":
            fields = step_args.get("fields", [])
            for field in fields:
                if field in args and not args[field]:
                    raise ValidationError(field, f"'{field}' must not be empty if provided")
        
        elif validate_type == "enum":
            field = step_args.get("field")
            values = step_args.get("values", [])
            if field in args and args[field] not in values:
                raise ValidationError(field, f"'{args[field]}' is not valid. Must be one of: {values}")
        
        elif validate_type == "format":
            field = step_args.get("field")
            format_type = step_args.get("format")
            if field in args and args[field]:
                self._validate_format(field, args[field], format_type)
        
        return {}
    
    def _validate_format(self, field: str, value: Any, format_type: str) -> None:
        """Validate field format."""
        if format_type == "uuid":
            try:
                uuid.UUID(value)
            except ValueError:
                raise ValidationError(field, f"'{value}' is not a valid UUID")
        
        elif format_type == "email":
            if "@" not in str(value) or "." not in str(value).split("@")[-1]:
                raise ValidationError(field, f"'{value}' is not a valid email")
        
        elif format_type == "date":
            try:
                date.fromisoformat(value)
            except (ValueError, TypeError):
                raise ValidationError(field, f"'{value}' is not a valid date (use YYYY-MM-DD)")
        
        elif format_type == "datetime":
            try:
                datetime.fromisoformat(value)
            except (ValueError, TypeError):
                raise ValidationError(field, f"'{value}' is not a valid datetime")
    
    async def _handle_transform(self, step_args: dict, args: dict) -> dict:
        """Handle transform operation."""
        transform_type = step_args.get("type")
        
        if transform_type == "mapping":
            mapping = step_args.get("mapping", {})
            field = step_args.get("field")
            if field in args and args[field] in mapping:
                return {f"{field}_transformed": mapping[args[field]]}
        
        return {}
    
    async def _handle_resolve(self, step_args: dict, args: dict, step_index: int) -> dict:
        """Handle resolve operation - requires domain-specific handler."""
        # This is a stub - domains should register their own resolve handlers
        entity_type = step_args.get("entity_type")
        raise PipelineExecutionError(
            step_index,
            f"Resolve operation for '{entity_type}' requires domain-specific handler. "
            f"Register a handler using executor.register_handler('resolve', your_handler)"
        )
    
    async def _handle_generate_key(self, step_args: dict, step_index: int) -> dict:
        """Handle generate_key operation."""
        pattern = step_args.get("pattern")
        prefix = step_args.get("prefix", "")
        
        # Simple implementation - domains can override
        key = f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
        return {"generated_key": key}
    
    async def _handle_crud(self, op: str, step_args: dict, args: dict, step_index: int) -> dict:
        """Handle CRUD operations - requires domain-specific handler."""
        entity = step_args.get("entity")
        raise PipelineExecutionError(
            step_index,
            f"CRUD operation '{op}' for '{entity}' requires domain-specific handler. "
            f"Register a handler using executor.register_handler('{op}', your_handler)"
        )
    
    async def _handle_transition(self, step_args: dict, args: dict, step_index: int) -> dict:
        """Handle transition operation - requires domain-specific handler."""
        entity = step_args.get("entity")
        raise PipelineExecutionError(
            step_index,
            f"Transition operation for '{entity}' requires domain-specific handler. "
            f"Register a handler using executor.register_handler('transition', your_handler)"
        )
    
    async def _handle_branch(self, step_args: dict, args: dict) -> dict:
        """Handle branch operation."""
        condition = step_args.get("condition")
        # Simple implementation - evaluate condition
        if condition:
            if_true = step_args.get("if_true")
            return {"branch_result": if_true}
        else:
            if_false = step_args.get("if_false")
            return {"branch_result": if_false}
    
    async def _handle_parallel(self, step_args: dict, args: dict, step_index: int) -> dict:
        """Handle parallel operation."""
        steps = step_args.get("steps", [])
        # Simple implementation - execute sequentially for now
        results = []
        for step in steps:
            result = await self._execute_step(step, args, step_index)
            results.append(result)
        return {"parallel_results": results}
    
    async def _handle_loop(self, step_args: dict, args: dict, step_index: int) -> dict:
        """Handle loop operation."""
        over = step_args.get("over")
        steps = step_args.get("steps", [])
        # Simple implementation
        results = []
        for item in over:
            loop_context = {"loop_item": item}
            self.context.update(loop_context)
            for step in steps:
                result = await self._execute_step(step, args, step_index)
                results.append(result)
        return {"loop_results": results}
    
    async def _handle_custom(self, step_args: dict, step_index: int) -> dict:
        """Handle custom operation."""
        handler = step_args.get("handler")
        raise PipelineExecutionError(
            step_index,
            f"Custom handler '{handler}' not found. "
            f"Register using executor.register_handler('{handler}', your_handler)"
        )
    
    async def _handle_version_control(self, op: str, step_args: dict, step_index: int) -> dict:
        """Handle version control operations."""
        entity = step_args.get("entity")
        raise PipelineExecutionError(
            step_index,
            f"Version control operation '{op}' for '{entity}' requires domain-specific handler. "
            f"Register using executor.register_handler('{op}', your_handler)"
        )
    
    async def _handle_audit_trail(self, op: str, step_args: dict, step_index: int) -> dict:
        """Handle audit trail operations."""
        entity_type = step_args.get("entity_type")
        raise PipelineExecutionError(
            step_index,
            f"Audit trail operation '{op}' for '{entity_type}' requires domain-specific handler. "
            f"Register using executor.register_handler('{op}', your_handler)"
        )
    
    async def _handle_agent_session(self, op: str, step_args: dict, step_index: int) -> dict:
        """Handle agent session operations."""
        session_id = step_args.get("session_id")
        raise PipelineExecutionError(
            step_index,
            f"Agent session operation '{op}' requires domain-specific handler. "
            f"Register using executor.register_handler('{op}', your_handler)"
        )
    
    async def _handle_semantic_search(self, op: str, step_args: dict, step_index: int) -> dict:
        """Handle semantic search operations."""
        entity_type = step_args.get("entity_type")
        raise PipelineExecutionError(
            step_index,
            f"Semantic search operation '{op}' for '{entity_type}' requires domain-specific handler. "
            f"Register using executor.register_handler('{op}', your_handler)"
        )
    
    async def _handle_workflow_orchestration(self, op: str, step_args: dict, step_index: int) -> dict:
        """Handle workflow orchestration operations."""
        workflow_type = step_args.get("workflow_type")
        raise PipelineExecutionError(
            step_index,
            f"Workflow operation '{op}' for '{workflow_type}' requires domain-specific handler. "
            f"Register using executor.register_handler('{op}', your_handler)"
        )


def create_tool_handler(config: PipelineConfig, handler_registry: dict[str, Callable] | None = None):
    """Create a callable tool handler from a pipeline configuration.
    
    Args:
        config: Pipeline configuration
        handler_registry: Optional dict of operation handlers to register
        
    Returns:
        Async function that takes (args, db, scope) and returns dict
    """
    async def handler(args: dict, db: AsyncSession, scope: dict[str, Any] | None = None) -> dict:
        executor = PipelineExecutor(db, scope=scope)
        
        # Register custom handlers if provided
        if handler_registry:
            for op, handler_func in handler_registry.items():
                executor.register_handler(op, handler_func)
        
        return await executor.execute(config, args)
    
    handler.__name__ = config.target_tool.name
    handler.__doc__ = config.target_tool.description or f"Tool: {config.target_tool.name}"
    
    return handler
