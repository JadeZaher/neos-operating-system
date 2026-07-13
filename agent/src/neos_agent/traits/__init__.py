"""Composable traits for agent primitives and domain logic.

Traits provide reusable behavioral patterns that can be mixed into
models, handlers, and pipeline operations. They are the building blocks
for the agent primitives matrix.
"""

from __future__ import annotations

from typing import Any

from neos_agent.traits.auditable import AuditableTrait
from neos_agent.traits.versioned import VersionedTrait
from neos_agent.traits.resolvable import ResolvableTrait
from neos_agent.traits.indexable import IndexableTrait
from neos_agent.traits.session_aware import SessionAwareTrait


__all__ = [
    "AuditableTrait",
    "VersionedTrait",
    "ResolvableTrait",
    "IndexableTrait",
    "SessionAwareTrait",
    "TraitRegistry",
]


class TraitRegistry:
    """Registry for traits and their application rules.

    Allows domains to register and compose traits dynamically,
    supporting the agent primitives matrix.
    """

    def __init__(self) -> None:
        self._traits: dict[str, type] = {}
        self._register_builtin_traits()

    def _register_builtin_traits(self) -> None:
        """Register built-in generic traits."""
        self.register("auditable", AuditableTrait)
        self.register("versioned", VersionedTrait)
        self.register("resolvable", ResolvableTrait)
        self.register("indexable", IndexableTrait)
        self.register("session_aware", SessionAwareTrait)

    def register(self, name: str, trait: type) -> None:
        """Register a trait by name."""
        self._traits[name] = trait

    def get(self, name: str) -> type | None:
        """Get a trait class by name."""
        return self._traits.get(name)

    def list_traits(self) -> list[str]:
        """List registered trait names."""
        return list(self._traits.keys())

    def apply(
        self,
        target: Any,
        trait_names: list[str],
    ) -> dict[str, Any]:
        """Apply traits to a target object and return the composed context.

        Args:
            target: The object or class to apply traits to
            trait_names: List of trait names to apply

        Returns:
            Context dict with composed trait capabilities
        """
        context = {}
        for name in trait_names:
            trait = self.get(name)
            if trait:
                context[name] = trait()
        return context
