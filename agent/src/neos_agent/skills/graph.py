"""Dependency graph for NEOS governance skills.

Builds a directed acyclic graph from depends_on fields.
Supports topological sorting, cycle detection, and dependency queries.
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neos_agent.skills.loader import SkillMeta


class SkillGraph:
    """DAG of skill dependencies with query capabilities."""

    def __init__(self) -> None:
        self._forward: dict[str, list[str]] = {}   # skill -> its dependencies
        self._reverse: dict[str, list[str]] = {}   # skill -> its dependents

    def add_skill(self, name: str, depends_on: list[str]) -> None:
        """Add a skill and its dependencies to the graph."""
        if name not in self._forward:
            self._forward[name] = []
        if name not in self._reverse:
            self._reverse[name] = []

        for dep in depends_on:
            if dep not in self._forward[name]:
                self._forward[name].append(dep)
            # Ensure dep node exists
            if dep not in self._forward:
                self._forward[dep] = []
            if dep not in self._reverse:
                self._reverse[dep] = []
            if name not in self._reverse[dep]:
                self._reverse[dep].append(name)

    def build_from_skills(self, skills: list[SkillMeta]) -> None:
        """Populate graph from a list of SkillMeta objects."""
        for skill in skills:
            self.add_skill(skill.name, skill.depends_on)

    def topological_order(self) -> list[str]:
        """Return skills in topological order (Kahn's algorithm).

        Every skill appears after all its dependencies.
        Raises ValueError if a cycle is detected.
        """
        # in_degree[X] = number of direct dependencies X has
        in_degree: dict[str, int] = {}
        for name in self._forward:
            in_degree[name] = len(self._forward[name])

        heap: list[str] = [name for name, deg in in_degree.items() if deg == 0]
        heapq.heapify(heap)
        result: list[str] = []

        while heap:
            node = heapq.heappop(heap)
            result.append(node)

            # For each dependent of this node, decrement their in-degree
            for dependent in sorted(self._reverse.get(node, [])):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(heap, dependent)

        if len(result) != len(self._forward):
            raise ValueError(
                f"Cycle detected: processed {len(result)} of {len(self._forward)} skills"
            )

        return result

    def detect_cycles(self) -> list[list[str]]:
        """Detect cycles in the dependency graph.

        Returns a list containing one entry if a cycle exists, empty list if not.
        Delegates to topological_order() which raises ValueError on cycles.
        The single cycle entry contains ["cycle_detected", <error_message>].
        """
        try:
            self.topological_order()
            return []
        except ValueError as exc:
            return [["cycle_detected", str(exc)]]

    def dependencies_of(self, name: str) -> set[str]:
        """Return all transitive dependencies of a skill."""
        if name not in self._forward:
            raise KeyError(f"Unknown skill: {name!r}")

        result: set[str] = set()
        stack = list(self._forward[name])

        while stack:
            dep = stack.pop()
            if dep not in result:
                result.add(dep)
                stack.extend(self._forward.get(dep, []))

        return result

    def direct_dependencies_of(self, name: str) -> list[str]:
        """Return immediate dependencies of a skill."""
        if name not in self._forward:
            raise KeyError(f"Unknown skill: {name!r}")
        return list(self._forward[name])

    def dependents_of(self, name: str) -> set[str]:
        """Return all transitive dependents of a skill (reverse)."""
        if name not in self._reverse:
            raise KeyError(f"Unknown skill: {name!r}")

        result: set[str] = set()
        stack = list(self._reverse[name])

        while stack:
            dep = stack.pop()
            if dep not in result:
                result.add(dep)
                stack.extend(self._reverse.get(dep, []))

        return result

    def direct_dependents_of(self, name: str) -> list[str]:
        """Return immediate dependents of a skill (reverse)."""
        if name not in self._reverse:
            raise KeyError(f"Unknown skill: {name!r}")
        return list(self._reverse[name])

    def has_skill(self, name: str) -> bool:
        """Check if a skill exists in the graph."""
        return name in self._forward

    @property
    def skill_names(self) -> list[str]:
        """Return sorted list of all skill names."""
        return sorted(self._forward.keys())
