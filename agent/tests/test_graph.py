"""Tests for SkillGraph dependency graph."""

from __future__ import annotations

import pytest

from neos_agent.skills.graph import SkillGraph
from neos_agent.skills.loader import SkillMeta


def make_meta(name: str, depends_on: list[str] | None = None) -> SkillMeta:
    return SkillMeta(
        name=name,
        description=f"Test skill {name}",
        layer=1,
        version="0.1.0",
        depends_on=depends_on or [],
        file_path=f"/fake/{name}/SKILL.md",
    )


def build_abcd() -> SkillGraph:
    """Build a simple linear chain: A <- B <- C <- D (D depends on C, C on A+B, B on A)."""
    g = SkillGraph()
    skills = [
        make_meta("A"),
        make_meta("B", ["A"]),
        make_meta("C", ["A", "B"]),
        make_meta("D", ["C"]),
    ]
    g.build_from_skills(skills)
    return g


class TestBuildFromSkills:
    def test_build_from_skills(self) -> None:
        g = build_abcd()
        assert g.has_skill("A")
        assert g.has_skill("B")
        assert g.has_skill("C")
        assert g.has_skill("D")
        assert len(g.skill_names) == 4


class TestTopologicalOrder:
    def test_topological_order_simple(self) -> None:
        g = build_abcd()
        order = g.topological_order()
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")
        assert order.index("C") < order.index("D")

    def test_topological_order_root_nodes(self) -> None:
        """Skills with no deps should come first."""
        g = build_abcd()
        order = g.topological_order()
        # A has no dependencies — should be first
        assert order[0] == "A"

    def test_topological_order_all_present(self) -> None:
        g = build_abcd()
        order = g.topological_order()
        assert set(order) == {"A", "B", "C", "D"}

    def test_topological_order_raises_on_cycle(self) -> None:
        g = SkillGraph()
        g.add_skill("X", ["Y"])
        g.add_skill("Y", ["Z"])
        g.add_skill("Z", ["X"])
        with pytest.raises(ValueError, match="Cycle detected"):
            g.topological_order()


class TestDetectCycles:
    def test_detect_cycles_none(self) -> None:
        g = build_abcd()
        assert g.detect_cycles() == []

    def test_detect_cycles_found(self) -> None:
        g = SkillGraph()
        g.add_skill("X", ["Y"])
        g.add_skill("Y", ["Z"])
        g.add_skill("Z", ["X"])
        cycles = g.detect_cycles()
        assert len(cycles) > 0
        # Each cycle should contain at least two elements
        for cycle in cycles:
            assert len(cycle) >= 2

    def test_detect_cycles_empty_graph(self) -> None:
        g = SkillGraph()
        assert g.detect_cycles() == []


class TestDependenciesOf:
    def test_dependencies_of_transitive(self) -> None:
        g = build_abcd()
        deps = g.dependencies_of("D")
        # D depends on C, which depends on A and B, which depends on A
        assert "A" in deps
        assert "B" in deps
        assert "C" in deps
        assert "D" not in deps

    def test_dependencies_of_direct_only(self) -> None:
        g = build_abcd()
        deps = g.dependencies_of("B")
        assert deps == {"A"}

    def test_dependencies_of_root_node(self) -> None:
        g = build_abcd()
        assert g.dependencies_of("A") == set()

    def test_dependencies_of_unknown_raises(self) -> None:
        g = build_abcd()
        with pytest.raises(KeyError, match="nonexistent"):
            g.dependencies_of("nonexistent")


class TestDirectDependenciesOf:
    def test_direct_dependencies_of(self) -> None:
        g = build_abcd()
        direct = g.direct_dependencies_of("C")
        # C directly depends on A and B, not D
        assert set(direct) == {"A", "B"}
        assert "D" not in direct

    def test_direct_dependencies_of_root(self) -> None:
        g = build_abcd()
        assert g.direct_dependencies_of("A") == []

    def test_direct_dependencies_of_unknown_raises(self) -> None:
        g = build_abcd()
        with pytest.raises(KeyError):
            g.direct_dependencies_of("nonexistent")


class TestDependentsOf:
    def test_dependents_of_transitive(self) -> None:
        g = build_abcd()
        dependents = g.dependents_of("A")
        # A is depended on by B, C (via B), and D (via C)
        assert "B" in dependents
        assert "C" in dependents
        assert "D" in dependents
        assert "A" not in dependents

    def test_dependents_of_leaf_node(self) -> None:
        g = build_abcd()
        assert g.dependents_of("D") == set()

    def test_dependents_of_unknown_raises(self) -> None:
        g = build_abcd()
        with pytest.raises(KeyError, match="nonexistent"):
            g.dependents_of("nonexistent")


class TestDirectDependentsOf:
    def test_direct_dependents_of(self) -> None:
        g = build_abcd()
        direct = g.direct_dependents_of("A")
        # A is directly depended on by B and C, not D (D only through C)
        assert set(direct) == {"B", "C"}
        assert "D" not in direct

    def test_direct_dependents_of_leaf(self) -> None:
        g = build_abcd()
        assert g.direct_dependents_of("D") == []

    def test_direct_dependents_of_unknown_raises(self) -> None:
        g = build_abcd()
        with pytest.raises(KeyError):
            g.direct_dependents_of("nonexistent")


class TestHasSkill:
    def test_has_skill_true(self) -> None:
        g = build_abcd()
        assert g.has_skill("A") is True
        assert g.has_skill("D") is True

    def test_has_skill_false(self) -> None:
        g = build_abcd()
        assert g.has_skill("nonexistent") is False

    def test_has_skill_empty_graph(self) -> None:
        g = SkillGraph()
        assert g.has_skill("anything") is False


class TestSkillNames:
    def test_skill_names(self) -> None:
        g = build_abcd()
        names = g.skill_names
        assert names == sorted(["A", "B", "C", "D"])

    def test_skill_names_empty(self) -> None:
        g = SkillGraph()
        assert g.skill_names == []


class TestEmptyDependsOn:
    def test_empty_depends_on(self) -> None:
        """Root nodes with no dependencies work correctly."""
        g = SkillGraph()
        g.add_skill("standalone", [])
        assert g.has_skill("standalone")
        assert g.direct_dependencies_of("standalone") == []
        assert g.dependencies_of("standalone") == set()
        assert g.topological_order() == ["standalone"]


class TestUnknownSkillRaises:
    def test_unknown_skill_raises(self) -> None:
        g = build_abcd()
        with pytest.raises(KeyError):
            g.dependencies_of("nonexistent")
        with pytest.raises(KeyError):
            g.dependents_of("nonexistent")
        with pytest.raises(KeyError):
            g.direct_dependencies_of("nonexistent")
        with pytest.raises(KeyError):
            g.direct_dependents_of("nonexistent")
