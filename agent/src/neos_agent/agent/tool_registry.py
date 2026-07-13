"""Generic tool registry for domain logic orchestration.

This module provides the integration layer between pipeline configurations
and tool interfaces. It dynamically composes tool handlers from
configurations and works with any SQLAlchemy models and domain logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from neos_agent.skills.loader import discover_skill_files, parse_skill_file, ParsedSkill
from neos_agent.skills.pipeline_executor import create_tool_handler
from neos_agent.skills.pipeline_schema import PipelineConfig


@dataclass(frozen=True)
class ToolDef:
    """Tool definition for agent interface."""
    name: str
    description: str
    handler: Callable
    parameters: dict[str, Any] | None = None


class ToolRegistry:
    """Generic registry for tools composed from pipeline configurations.
    
    Works with any domain logic, SQLAlchemy models, and pipeline configurations.
    """
    
    def __init__(self, handler_registry: dict[str, Callable] | None = None):
        """Initialize tool registry.
        
        Args:
            handler_registry: Optional dict of operation handlers to register with all tools
        """
        self.tools: dict[str, ToolDef] = {}
        self.configs: dict[str, PipelineConfig] = {}
        self.handler_registry = handler_registry or {}
    
    def register_tool(self, tool_def: ToolDef) -> None:
        """Register a tool definition.
        
        Args:
            tool_def: Tool definition to register
        """
        self.tools[tool_def.name] = tool_def
    
    def register_from_config(self, config: PipelineConfig) -> None:
        """Register a tool from a pipeline configuration.
        
        Args:
            config: Pipeline configuration
        """
        self.configs[config.target_tool.name] = config
        
        # Create handler from pipeline
        handler = create_tool_handler(config, self.handler_registry)
        
        # Create tool definition
        tool_def = ToolDef(
            name=config.target_tool.name,
            description=config.target_tool.description,
            handler=handler,
            parameters=self._extract_parameters(config),
        )
        
        self.register_tool(tool_def)
    
    def register_from_skill(self, skill: ParsedSkill) -> None:
        """Register a tool from a parsed skill configuration.
        
        Args:
            skill: Parsed skill with pipeline configuration
        """
        if not skill.pipeline_config:
            return
        
        self.register_from_config(skill.pipeline_config)
    
    def register_from_skills_directory(self, skills_dir: Path) -> None:
        """Discover and register tools from all skills in a directory.
        
        Args:
            skills_dir: Directory containing SKILL.md files
        """
        skill_files = discover_skill_files(skills_dir)
        
        for skill_file in skill_files:
            try:
                skill = parse_skill_file(skill_file)
                self.register_from_skill(skill)
            except Exception as e:
                # Log error but continue processing other skills
                print(f"Failed to load skill {skill_file}: {e}")
    
    def get_tool(self, name: str) -> ToolDef | None:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool definition or None if not found
        """
        return self.tools.get(name)
    
    def get_all_tools(self) -> list[ToolDef]:
        """Get all registered tools.
        
        Returns:
            List of all tool definitions
        """
        return list(self.tools.values())
    
    def execute_tool(
        self,
        name: str,
        args: dict,
        db: AsyncSession,
        scope: dict[str, Any] | None = None
    ) -> dict:
        """Execute a tool by name.
        
        Args:
            name: Tool name
            args: Tool arguments
            db: Database session
            scope: Optional scope dict (e.g., ecosystem_ids, tenant_id)
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found"}
        
        return tool.handler(args, db, scope)
    
    def _extract_parameters(self, config: PipelineConfig) -> dict[str, Any]:
        """Extract parameter schema from pipeline configuration.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Parameter schema dict
        """
        # This is a simplified version - in production you'd build
        # a proper JSON schema from the pipeline steps
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        
        # Extract required fields from validate steps
        for step in config.target_tool.pipeline:
            if step.op == "validate":
                validate_type = step.args.get("type")
                if validate_type == "required":
                    fields = step.args.get("fields", [])
                    parameters["required"].extend(fields)
                    for field in fields:
                        parameters["properties"][field] = {"type": "string"}
        
        return parameters


def create_composed_registry(
    skills_dir: Path | None = None,
    handler_registry: dict[str, Callable] | None = None
) -> ToolRegistry:
    """Create a tool registry composed from skill configurations.
    
    Args:
        skills_dir: Optional directory containing SKILL.md files
        handler_registry: Optional dict of operation handlers
        
    Returns:
        ToolRegistry with dynamically composed tools
    """
    registry = ToolRegistry(handler_registry)
    
    if skills_dir:
        registry.register_from_skills_directory(skills_dir)
    
    return registry


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_global_registry() -> ToolRegistry:
    """Get or create the global tool registry.
    
    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ToolRegistry()
    
    return _global_registry


def initialize_registry(skills_dir: Path) -> ToolRegistry:
    """Initialize the global registry from skills directory.
    
    Args:
        skills_dir: Directory containing SKILL.md files
        
    Returns:
        Initialized ToolRegistry
    """
    global _global_registry
    _global_registry = create_composed_registry(skills_dir)
    return _global_registry
