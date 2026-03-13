"""In-memory skill registry loaded at startup.

Provides fast lookup by name, by layer, and full listing.
Uses frozen dataclasses for multi-worker safety.
"""

from __future__ import annotations

import logging
from pathlib import Path

from neos_agent.skills.graph import SkillGraph
from neos_agent.skills.loader import (
    ParsedSkill,
    SkillMeta,
    SkillParseError,
    discover_skill_files,
    parse_skill_file,
)

logger = logging.getLogger(__name__)


class SkillRegistry:
    """In-memory index of all parsed skills."""

    def __init__(self) -> None:
        self._skills: dict[str, ParsedSkill] = {}
        self._graph: SkillGraph = SkillGraph()
        self._loaded: bool = False

    async def load_all(self, neos_core_path: Path | str) -> None:
        """Discover and parse all skills from neos-core.

        Logs warnings for unparseable skills but does not abort.
        """
        root = Path(neos_core_path).resolve()
        files = discover_skill_files(root)
        logger.info("Discovered %d SKILL.md files in %s", len(files), root)

        for file_path in files:
            try:
                skill = parse_skill_file(file_path)
                self._skills[skill.meta.name] = skill
            except SkillParseError as e:
                logger.warning("Skipping unparseable skill %s: %s", file_path, e)

        # Build dependency graph
        self._graph = SkillGraph()
        self._graph.build_from_skills([s.meta for s in self._skills.values()])

        self._loaded = True
        logger.info("Loaded %d skills into registry", len(self._skills))

    def get(self, name: str) -> ParsedSkill:
        """Return full ParsedSkill by name. Raises KeyError if not found."""
        if name not in self._skills:
            raise KeyError(f"Unknown skill: {name!r}")
        return self._skills[name]

    def get_meta(self, name: str) -> SkillMeta:
        """Return SkillMeta (without full content) by name."""
        return self.get(name).meta

    def list_by_layer(self, layer: int) -> list[SkillMeta]:
        """Return all skills in a given layer."""
        return [
            s.meta for s in self._skills.values()
            if s.meta.layer == layer
        ]

    def all_skills(self) -> list[SkillMeta]:
        """Return all SkillMeta objects."""
        return [s.meta for s in self._skills.values()]

    def all_names(self) -> list[str]:
        """Return sorted list of all skill names."""
        return sorted(self._skills.keys())

    @property
    def count(self) -> int:
        """Number of loaded skills."""
        return len(self._skills)

    @property
    def graph(self) -> SkillGraph:
        """Return the populated SkillGraph."""
        return self._graph

    @property
    def is_loaded(self) -> bool:
        """Whether load_all has completed."""
        return self._loaded
