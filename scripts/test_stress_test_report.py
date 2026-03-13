#!/usr/bin/env python3
"""Tests for stress_test_report.py -- NEOS stress test summary report.

TDD Red Phase: These tests define what stress_test_report.py should do.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTER = os.path.join(SCRIPT_DIR, "stress_test_report.py")


def run_reporter(*args):
    """Run stress_test_report.py with given args and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, REPORTER, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# --- Fixture SKILL.md content ---

FULL_SKILL = """---
name: test-skill-alpha
description: "A test skill with all stress tests."
layer: 1
version: 0.1.0
depends_on: []
---

# test-skill-alpha

## A. Structural Problem It Solves

This skill solves an important governance problem.
It provides structure for decision-making.
It ensures traceability and transparency.

## OmniOne Walkthrough

Example walkthrough content.

## Stress-Test Results

### 1. Capital Influx

A donor offers $500K contingent on a specific outcome.
The skill prevents bypassing the governance process.
Capital influence is structurally contained by the consent mechanism.

### 2. Emergency Crisis

A natural disaster requires immediate action.
The compressed timeline still maintains consent requirements.
Post-emergency review ensures accountability.

### 3. Leadership Charisma Capture

A charismatic leader attempts to override objections.
The structural protections prevent charismatic capture.
Integration rounds require substantive engagement.

### 4. High Conflict / Polarization

Two factions want mutually exclusive outcomes.
Coaching escalation brings a neutral facilitator.
The third-solution approach is pursued.

### 5. Large-Scale Replication

The ecosystem grows from 50 to 5,000 members.
Domain-scoped action keeps processes manageable.
Facilitation training scales through train-the-trainer.

### 6. External Legal Pressure

A government demands contradicting regulations.
External mandates do not bypass internal governance.
The UAF sovereignty principle applies.

### 7. Sudden Exit of 30% of Participants

Nearly a third of members leave suddenly.
Existing outcomes remain valid. Quorum thresholds adapt.
The registry flags entries for stewardship transition.
"""

MISSING_SCENARIOS_SKILL = """---
name: test-skill-beta
description: "A test skill missing some stress tests."
layer: 2
version: 0.2.0
depends_on: [test-skill-alpha]
---

# test-skill-beta

## A. Structural Problem It Solves

This skill solves another important problem.
Structure is provided for a different function.
Traceability is maintained.

## OmniOne Walkthrough

Example walkthrough.

## Stress-Test Results

### 1. Capital Influx

Response to capital influx scenario.
The skill handles financial pressure.
Structural safeguards are in place.

### 2. Emergency Crisis

Response to emergency crisis.
Compressed timelines are handled.
Accountability is maintained.

### 5. Large-Scale Replication

The skill scales effectively.
Domain-scoping keeps things manageable.
Training programs support growth.
"""

SECOND_LAYER_SKILL = """---
name: test-skill-gamma
description: "A second-layer test skill."
layer: 2
version: 0.1.0
depends_on: [test-skill-alpha]
---

# test-skill-gamma

## A. Structural Problem It Solves

Another governance skill for testing.
Provides structure for a third function.
Ensures proper governance.

## OmniOne Walkthrough

Example walkthrough.

## Stress-Test Results

### 1. Capital Influx

Capital influx response.
The skill handles it.
Structural safeguards exist.

### 2. Emergency Crisis

Emergency response.
Timelines are handled.
Accountability maintained.

### 3. Leadership Charisma Capture

Charismatic capture response.
Structural protections in place.
Integration rounds required.

### 4. High Conflict / Polarization

Conflict response.
Neutral facilitation.
Third-solution approach.

### 5. Large-Scale Replication

Scale response.
Domain-scoping.
Training programs.

### 6. External Legal Pressure

Legal pressure response.
Internal governance maintained.
Sovereignty principle applied.

### 7. Sudden Exit of 30% of Participants

Exit response.
Outcomes remain valid.
Quorum adapts.
"""


def create_test_tree(base_dir, skills=None):
    """Create a minimal neos-core tree with given skill contents.

    skills: list of (layer_dir, skill_name, content) tuples.
    Returns the neos-core directory path.
    """
    if skills is None:
        skills = [
            ("layer-01-agreement", "test-skill-alpha", FULL_SKILL),
        ]

    neos_core = os.path.join(base_dir, "neos-core")
    os.makedirs(neos_core, exist_ok=True)

    for layer_dir, skill_name, content in skills:
        skill_dir = os.path.join(neos_core, layer_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
            f.write(content)

    return neos_core


class TestSkillDiscovery(unittest.TestCase):
    """Test: reporter finds all SKILL.md files."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
            ("layer-02-authority", "skill-b", MISSING_SCENARIOS_SKILL),
            ("layer-02-authority", "skill-c", SECOND_LAYER_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_skill_discovery(self):
        """Reporter should find all SKILL.md files in the tree."""
        code, stdout, stderr = run_reporter("--path", self.neos_core)
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # All three skills should be mentioned
        self.assertIn("test-skill-alpha", stdout)
        self.assertIn("test-skill-beta", stdout)
        self.assertIn("test-skill-gamma", stdout)


class TestFrontmatterExtraction(unittest.TestCase):
    """Test: reporter extracts name, description, layer from frontmatter."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_frontmatter_extraction(self):
        """Reporter should extract and display skill name, description, layer."""
        code, stdout, stderr = run_reporter("--path", self.neos_core)
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Name from frontmatter
        self.assertIn("test-skill-alpha", stdout)
        # Layer number
        self.assertIn("1", stdout)


class TestStressTestDetection(unittest.TestCase):
    """Test: reporter detects all 7 stress-test scenarios."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_stress_test_detection(self):
        """Reporter should detect all 7 scenarios for a complete skill."""
        code, stdout, stderr = run_reporter("--path", self.neos_core)
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # All 7 scenario names should appear in the report
        scenarios = [
            "Capital Influx",
            "Emergency Crisis",
            "Leadership Charisma Capture",
            "High Conflict",
            "Large-Scale Replication",
            "External Legal Pressure",
            "Sudden Exit",
        ]
        for scenario in scenarios:
            self.assertIn(scenario, stdout, f"Scenario '{scenario}' should appear in report")


class TestMissingScenarioReported(unittest.TestCase):
    """Test: reporter flags skills missing stress-test scenarios."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-02-authority", "skill-b", MISSING_SCENARIOS_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_missing_scenario_reported(self):
        """Reporter should flag missing scenarios for incomplete skills."""
        code, stdout, stderr = run_reporter("--path", self.neos_core)
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # The skill is missing scenarios 3, 4, 6, 7
        output_lower = stdout.lower()
        self.assertTrue(
            "missing" in output_lower or "absent" in output_lower or "-" in stdout,
            f"Should indicate missing scenarios. Got:\n{stdout}"
        )


class TestSkillIndexGeneration(unittest.TestCase):
    """Test: reporter produces a complete skill index."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
            ("layer-02-authority", "skill-b", MISSING_SCENARIOS_SKILL),
            ("layer-02-authority", "skill-c", SECOND_LAYER_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_skill_index_generation(self):
        """Reporter should produce a skill index listing all skills."""
        code, stdout, stderr = run_reporter("--path", self.neos_core)
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Index should contain all skill names
        self.assertIn("test-skill-alpha", stdout)
        self.assertIn("test-skill-beta", stdout)
        self.assertIn("test-skill-gamma", stdout)
        # Should contain layer info
        output_lower = stdout.lower()
        self.assertTrue(
            "index" in output_lower or "skill" in output_lower,
            f"Should have a skill index section. Got:\n{stdout}"
        )


class TestMarkdownFormat(unittest.TestCase):
    """Test: markdown format output is valid markdown."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_markdown_format(self):
        """Markdown format should produce valid markdown with headers."""
        code, stdout, stderr = run_reporter(
            "--path", self.neos_core,
            "--format", "markdown",
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Markdown should have headers
        self.assertIn("#", stdout, "Markdown output should contain headers")
        # Should have table-like structure or list markers
        self.assertTrue(
            "|" in stdout or "-" in stdout,
            "Markdown should contain tables or list markers"
        )


class TestTextFormat(unittest.TestCase):
    """Test: text format output is plain text."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_test_tree(self.tmp_dir, [
            ("layer-01-agreement", "skill-a", FULL_SKILL),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_text_format(self):
        """Text format should produce plain text without markdown headers."""
        code, stdout, stderr = run_reporter(
            "--path", self.neos_core,
            "--format", "text",
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Should have content
        self.assertTrue(len(stdout.strip()) > 0, "Text output should not be empty")
        # Should mention scenarios
        self.assertIn("Capital Influx", stdout)


if __name__ == "__main__":
    unittest.main()
