"""Integration tests for SkillGraph against real neos-core data."""

from __future__ import annotations

from pathlib import Path

import pytest

from neos_agent.skills.graph import SkillGraph
from neos_agent.skills.loader import discover_skill_files, parse_skill_file


def _neos_core_path() -> Path:
    agent_dir = Path(__file__).parent.parent
    return (agent_dir / ".." / "neos-core").resolve()


@pytest.fixture
def real_graph() -> SkillGraph:
    """Build a SkillGraph from the real neos-core skills."""
    neos_core = _neos_core_path()
    if not neos_core.exists():
        pytest.skip(f"neos-core not found at {neos_core}")

    skill_files = discover_skill_files(neos_core)
    graph = SkillGraph()
    metas = []
    for path in skill_files:
        skill = parse_skill_file(path)
        metas.append(skill.meta)
    graph.build_from_skills(metas)
    return graph


def test_real_graph_has_54_skills(real_graph: SkillGraph) -> None:
    assert len(real_graph.skill_names) == 54


def test_real_graph_no_cycles(real_graph: SkillGraph) -> None:
    """The real neos-core skill graph should be acyclic."""
    cycles = real_graph.detect_cycles()
    assert cycles == [], f"Unexpected cycles in neos-core: {cycles}"


def test_real_graph_topological_order(real_graph: SkillGraph) -> None:
    """Topological sort should succeed and return all 54 skills."""
    order = real_graph.topological_order()
    assert len(order) == 54
    # Every skill in the order must exist in the graph
    for name in order:
        assert real_graph.has_skill(name)


def test_real_graph_root_skills_first(real_graph: SkillGraph) -> None:
    """Skills with no dependencies should appear early in topological order."""
    order = real_graph.topological_order()
    for name in order[:10]:  # first 10 should include root skills
        deps = real_graph.direct_dependencies_of(name)
        # Root skills have no deps; non-root ones at least have deps resolved earlier
        for dep in deps:
            assert order.index(dep) < order.index(name)


def test_real_graph_dependency_integrity(real_graph: SkillGraph) -> None:
    """Every depends_on reference should resolve to an existing skill."""
    for name in real_graph.skill_names:
        for dep in real_graph.direct_dependencies_of(name):
            assert real_graph.has_skill(dep), (
                f"Skill {name!r} depends on {dep!r} which doesn't exist in the graph"
            )


def test_real_graph_domain_mapping_is_foundation(real_graph: SkillGraph) -> None:
    """domain-mapping should be a widely-depended-on foundation skill."""
    assert real_graph.has_skill("domain-mapping")
    dependents = real_graph.dependents_of("domain-mapping")
    # domain-mapping is a Layer I skill depended on by many
    assert len(dependents) >= 5, (
        f"Expected domain-mapping to have >=5 dependents, got {len(dependents)}"
    )
