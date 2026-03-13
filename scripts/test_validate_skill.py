#!/usr/bin/env python3
"""Tests for validate_skill.py — NEOS Skill Validator.

TDD Red Phase: These tests define what validate_skill.py should do.
All tests will FAIL until validate_skill.py is implemented.
"""

import os
import subprocess
import sys
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(SCRIPT_DIR, "validate_skill.py")
FIXTURES = os.path.join(SCRIPT_DIR, "fixtures")


def run_validator(path):
    """Run validate_skill.py and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, VALIDATOR, path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestValidSkill(unittest.TestCase):
    """Test: valid SKILL.md passes all checks."""

    def test_valid_skill_passes(self):
        """Valid SKILL.md with all sections and content should pass."""
        path = os.path.join(FIXTURES, "valid_skill.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 0, f"Valid skill should pass. Output:\n{stdout}")
        self.assertIn("PASS", stdout)


class TestFrontmatterValidation(unittest.TestCase):
    """Test: YAML frontmatter validation."""

    def test_missing_frontmatter_fails(self):
        """Missing YAML frontmatter should fail."""
        path = os.path.join(FIXTURES, "invalid_no_frontmatter.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without frontmatter")
        output = (stdout + " ").lower()
        self.assertIn("frontmatter", output, "Error should mention frontmatter")

    def test_missing_field_name_fails(self):
        """Missing required field 'name' should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_field_name.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without 'name' field")
        output = (stdout + " ").lower()
        self.assertIn("name", output, "Error should mention 'name' field")

    def test_missing_field_description_fails(self):
        """Missing required field 'description' should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_field_description.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without 'description' field")
        output = (stdout + " ").lower()
        self.assertIn("description", output, "Error should mention 'description' field")

    def test_missing_field_layer_fails(self):
        """Missing required field 'layer' should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_field_layer.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without 'layer' field")
        output = (stdout + " ").lower()
        self.assertIn("layer", output, "Error should mention 'layer' field")

    def test_missing_field_version_fails(self):
        """Missing required field 'version' should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_field_version.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without 'version' field")
        output = (stdout + " ").lower()
        self.assertIn("version", output, "Error should mention 'version' field")

    def test_missing_field_depends_on_fails(self):
        """Missing required field 'depends_on' should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_field_depends_on.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without 'depends_on' field")
        output = (stdout + " ").lower()
        self.assertIn("depends_on", output, "Error should mention 'depends_on' field")


class TestSectionValidation(unittest.TestCase):
    """Test: all 12 sections (A-L) must be present with substantive content."""

    def test_missing_section_a_fails(self):
        """Missing section A should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_section_a.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without section A")
        output = (stdout + " ").lower()
        self.assertIn("section", output)
        self.assertIn("a", output)

    def test_missing_section_b_fails(self):
        """Missing section B should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_section_b.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without section B")
        output = (stdout + " ").lower()
        self.assertIn("section", output)

    def test_missing_section_l_fails(self):
        """Missing section L (last section) should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_section_l.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without section L")
        output = (stdout + " ").lower()
        self.assertIn("section", output)

    def test_empty_section_fails(self):
        """Empty section (header only, no content) should fail."""
        path = os.path.join(FIXTURES, "invalid_empty_section.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail if section is empty")
        output = (stdout + " ").lower()
        # Should mention emptiness or lack of substantive content
        self.assertTrue(
            "empty" in output or "substantive" in output or "content" in output,
            f"Error should indicate insufficient section content. Got: {stdout}"
        )


class TestWalkthroughValidation(unittest.TestCase):
    """Test: OmniOne walkthrough section must be present."""

    def test_missing_omnione_walkthrough_fails(self):
        """Missing OmniOne Walkthrough section should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_omnione.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without OmniOne walkthrough")
        output = (stdout + " ").lower()
        self.assertTrue(
            "omnione" in output or "walkthrough" in output,
            f"Error should mention OmniOne walkthrough. Got: {stdout}"
        )


class TestStressTestValidation(unittest.TestCase):
    """Test: all 7 stress-test scenarios must be present."""

    def test_missing_stress_tests_fails(self):
        """Missing stress-test results section should fail."""
        path = os.path.join(FIXTURES, "invalid_missing_stress_tests.md")
        code, stdout, _ = run_validator(path)
        self.assertEqual(code, 1, "Should fail without stress-test scenarios")
        output = (stdout + " ").lower()
        self.assertTrue(
            "stress" in output or "scenario" in output,
            f"Error should mention stress-test scenarios. Got: {stdout}"
        )


class TestDirectoryScanning(unittest.TestCase):
    """Test: validator can accept directory and recursively find SKILL.md files."""

    def test_directory_recursion(self):
        """Validator should scan directory recursively for SKILL.md files."""
        # The validator should accept a directory path and search for SKILL.md files
        # This test just validates the mechanism works (behavior defined by validator)
        code, stdout, _ = run_validator(FIXTURES)
        # Should indicate it processed directory or found files
        output = (stdout + " ").lower()
        # Either found files or explicitly stated no SKILL.md files found
        self.assertTrue(
            "skill.md" in output or "processed" in output or "found" in output,
            f"Validator should indicate directory processing. Got: {stdout}"
        )


class TestExitCodes(unittest.TestCase):
    """Test: exit codes 0 (pass) and 1 (fail)."""

    def test_exit_code_0_on_pass(self):
        """Valid SKILL.md should return exit code 0."""
        path = os.path.join(FIXTURES, "valid_skill.md")
        code, _, _ = run_validator(path)
        self.assertEqual(code, 0, "Exit code should be 0 for valid skill")

    def test_exit_code_1_on_fail(self):
        """Invalid SKILL.md should return exit code 1."""
        path = os.path.join(FIXTURES, "invalid_no_frontmatter.md")
        code, _, _ = run_validator(path)
        self.assertEqual(code, 1, "Exit code should be 1 for invalid skill")


if __name__ == "__main__":
    unittest.main()
