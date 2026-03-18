#!/usr/bin/env python3
"""Tests for package_zip.py -- NEOS skill stack packaging.

TDD Red Phase: These tests define what package_zip.py should do.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGER = os.path.join(SCRIPT_DIR, "package_zip.py")


def run_packager(*args):
    """Run package_zip.py with given args and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, PACKAGER, *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def create_minimal_neos_tree(base_dir):
    """Create a minimal neos-core directory tree for testing.

    Returns the path to the neos-core directory.
    """
    neos_core = os.path.join(base_dir, "neos-core")
    os.makedirs(neos_core, exist_ok=True)

    # VERSION file
    with open(os.path.join(neos_core, "VERSION"), "w") as f:
        f.write("1.2.3\n")

    # Top-level docs
    with open(os.path.join(neos_core, "README.md"), "w") as f:
        f.write("# NEOS Core\n")
    with open(os.path.join(neos_core, "NEOS_PRINCIPLES.md"), "w") as f:
        f.write("# NEOS Principles\n")
    with open(os.path.join(neos_core, "STRESS_TEST_PROTOCOL.md"), "w") as f:
        f.write("# Stress Test Protocol\n")

    # A valid SKILL.md (minimal but valid for validator)
    skill_dir = os.path.join(neos_core, "layer-01-agreement", "test-skill")
    os.makedirs(skill_dir, exist_ok=True)
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(_VALID_SKILL_CONTENT)

    # An assets directory
    assets_dir = os.path.join(skill_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    with open(os.path.join(assets_dir, "template.yaml"), "w") as f:
        f.write("template: true\n")

    # A references directory
    refs_dir = os.path.join(skill_dir, "references")
    os.makedirs(refs_dir, exist_ok=True)
    with open(os.path.join(refs_dir, "notes.md"), "w") as f:
        f.write("# Reference notes\n")

    return neos_core


def create_validate_skill_stub(base_dir, should_pass=True):
    """Create a stub validate_skill.py in scripts/ that passes or fails."""
    scripts_dir = os.path.join(base_dir, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    exit_code = 0 if should_pass else 1
    with open(os.path.join(scripts_dir, "validate_skill.py"), "w") as f:
        f.write(f"import sys\nsys.exit({exit_code})\n")
    return os.path.join(scripts_dir, "validate_skill.py")


# Minimal valid SKILL.md content matching the validator requirements
_VALID_SKILL_CONTENT = """---
name: test-skill
description: "A test skill."
layer: 1
version: 0.1.0
depends_on: []
---

# test-skill

## A. Structural Problem It Solves

Without this skill, there is no structured process for this governance function.
This leads to informal authority and untracked decisions.
The skill ensures traceability, legitimacy, and structural clarity.

## B. Domain Scope

This skill applies to any domain where this governance function is needed.
It covers all agreement types and all participant roles.
The scope includes both intra-circle and cross-circle applications.

## C. Trigger Conditions

The skill is triggered when a participant identifies a need.
Additional triggers include scheduled review dates and threshold events.
Emergency triggers follow the provisional emergency expediting rules.

## D. Required Inputs

The required inputs include the proposer's identity and their authority scope.
The affected parties and domain must be clearly identified.
A rationale must be provided along with the relevant documentation.

## E. Step-by-Step Process

Step 1: Identify the need and gather documentation.
Step 2: Verify no conflicts with existing agreements.
Step 3: Route the proposal to the appropriate ACT decision level.
Step 4: Follow the full ACT cycle as appropriate.
Step 5: Produce the output artifact and register it.

## F. Output Artifact

The output is a versioned document with a unique identifier.
The document includes full text, ratification record, and review date.
It is registered in the agreement registry upon completion.

## G. Authority Boundary Check

No individual can take unilateral action outside their defined domain.
Circle-internal actions require circle consent; cross-circle actions require broader consent.
Ecosystem-level actions require OSC consensus.

## H. Capture Resistance Check

Capital capture is addressed by ensuring funding conditions do not bypass the ACT process.
Charismatic capture is addressed by structurally protecting objectors.
Emergency capture is addressed by maintaining consent requirements.
Informal capture is prevented by requiring formal registration.

## I. Failure Containment Logic

If consent fails, the proposal returns to the advice phase.
If quorum is not met, the timeline is extended.
If the process stalls, an automatic reminder is sent.
Ambiguous outcomes require a mandatory clarification round.

## J. Expiry / Review Condition

All outputs have a default review date based on their type.
Missed reviews trigger an escalation notice.
Review intervals are configurable but have mandatory minimums.

## K. Exit Compatibility Check

When a participant exits, their obligations cease except for stewarded asset return.
A 30-day wind-down period applies.
The participant retains rights to their original works.
Agreements they authored remain valid.

## L. Cross-Unit Interoperability Impact

Actions in one ETHOS that affect another trigger cross-unit notification.
The affected ETHOS must consent through their own ACT process.
Cross-ETHOS outcomes are registered in both units' registries.
Federation with other NEOS ecosystems uses inter-unit coordination.

## OmniOne Walkthrough

A TH member named Amara identifies a need for the described governance function within the SHUR Bali community. Amara follows the step-by-step process, starting with a synergy check against the agreement registry. During the advice phase, feedback is gathered from all 12 affected SHUR residents over a 7-day window. The consent phase proceeds with 10 of 12 participants. The output artifact is registered with a one-year review date.

## Stress-Test Results

### 1. Capital Influx

A donor offers $500K contingent on a specific outcome. The skill's authority boundary check prevents bypassing the ACT process. The proposal goes through the full advice and consent phases. The capture resistance check flags the funding condition. The consent phase proceeds without modification. The outcome is determined by reasoned evaluation.

### 2. Emergency Crisis

A natural disaster requires immediate action within 24 hours. Three circle members jointly declare an emergency. The advice window is compressed to 24 hours and quorum cannot drop below 50%. A formal consent round is still required. Decisions are flagged for post-emergency review. The auto-revert window is set to 30 days.

### 3. Leadership Charisma Capture

A charismatic leader attempts to push an outcome by framing objections as obstructionism. The consent phase structurally protects objectors. The facilitator cannot override objections. Social pressure is flagged as a capture risk. Integration rounds require substantive engagement with objections.

### 4. High Conflict / Polarization

Two factions want mutually exclusive outcomes. Coaching escalation brings a neutral coach. The coach facilitates finding a third solution. The Doing Both Solution is considered. If coaching fails, escalation to Alignment Sense Making occurs.

### 5. Large-Scale Replication

OmniOne grows from 50 to 5,000 members across multiple ETHOS. The skill scales through domain-scoped action. Local actions stay within their circle's domain. The agreement registry handles scale through domain-based filtering. Facilitation training scales through train-the-trainer.

### 6. External Legal Pressure

A government requires OmniOne to implement contradicting regulations. The external mandate does not automatically become an agreement. A proposal goes through the full ACT process. Members may individually comply without ecosystem-wide agreement. The UAF sovereignty principle evaluates external pressure on its own terms.

### 7. Sudden Exit of 30% of Participants

Nearly a third of members leave following a disagreement. Existing outcomes remain valid. Automatic review is triggered for outcomes where departed members were key parties. Quorum thresholds adapt to current participant count. The registry flags entries for stewardship transition.
"""


class TestVersionFileReading(unittest.TestCase):
    """Test: package_zip reads VERSION file correctly."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_version_file_reading(self):
        """Package reads VERSION and uses it in filename."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        self.assertIn("1.2.3", stdout, "Output should mention version")

    def test_default_output_filename_includes_version(self):
        """Default output filename should be neos-core-vX.Y.Z.zip."""
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # The default filename should contain the version
        self.assertIn("neos-core-v1.2.3.zip", stdout)

    def test_missing_version_file_fails(self):
        """Missing VERSION file should cause failure."""
        os.remove(os.path.join(self.neos_core, "VERSION"))
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 1, "Should fail without VERSION file")


class TestManifestGeneration(unittest.TestCase):
    """Test: correct manifest of included files is generated."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_manifest_generation(self):
        """Package should print manifest listing included files."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Manifest should list key files
        self.assertIn("SKILL.md", stdout)
        self.assertIn("README.md", stdout)

    def test_manifest_shows_total_size(self):
        """Manifest output should show total size."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        # Should mention size somewhere
        output_lower = stdout.lower()
        self.assertTrue(
            "size" in output_lower or "bytes" in output_lower or "kb" in output_lower,
            f"Should mention file size. Got: {stdout}"
        )


class TestExcludedFiles(unittest.TestCase):
    """Test: excluded files are not in the zip."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

        # Create files that should be excluded
        conductor_dir = os.path.join(self.tmp_dir, "conductor")
        os.makedirs(conductor_dir, exist_ok=True)
        with open(os.path.join(conductor_dir, "product.md"), "w") as f:
            f.write("# Product\n")

        git_dir = os.path.join(self.tmp_dir, ".git")
        os.makedirs(git_dir, exist_ok=True)
        with open(os.path.join(git_dir, "config"), "w") as f:
            f.write("[core]\n")

        pycache_dir = os.path.join(self.neos_core, "__pycache__")
        os.makedirs(pycache_dir, exist_ok=True)
        with open(os.path.join(pycache_dir, "cache.pyc"), "w") as f:
            f.write("cached")

        # test_ files
        scripts_dir = os.path.join(self.tmp_dir, "scripts")
        with open(os.path.join(scripts_dir, "test_something.py"), "w") as f:
            f.write("# test\n")

        # .gitignore
        with open(os.path.join(self.tmp_dir, ".gitignore"), "w") as f:
            f.write("*.pyc\n")

        # reference-docs/
        ref_docs = os.path.join(self.tmp_dir, "reference-docs")
        os.makedirs(ref_docs, exist_ok=True)
        with open(os.path.join(ref_docs, "doc.md"), "w") as f:
            f.write("# Doc\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_excluded_files(self):
        """conductor/, .git/, __pycache__/, test_*, .pyc, .gitignore, reference-docs/ excluded."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        self.assertTrue(os.path.exists(output_path), "Zip file should exist")

        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            for name in names:
                self.assertNotIn("conductor", name, f"conductor/ should be excluded: {name}")
                self.assertNotIn(".git", name, f".git/ should be excluded: {name}")
                self.assertNotIn("__pycache__", name, f"__pycache__/ should be excluded: {name}")
                self.assertFalse(name.endswith(".pyc"), f".pyc should be excluded: {name}")
                self.assertNotIn("reference-docs", name, f"reference-docs/ should be excluded: {name}")
                # test_ files excluded (but test within a larger word is fine)
                basename = os.path.basename(name)
                if basename:
                    self.assertFalse(
                        basename.startswith("test_"),
                        f"test_ files should be excluded: {name}"
                    )


class TestIncludedFiles(unittest.TestCase):
    """Test: required files are in the zip."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_included_files(self):
        """SKILL.md, assets/, README.md, NEOS_PRINCIPLES.md, STRESS_TEST_PROTOCOL.md included."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        self.assertTrue(os.path.exists(output_path))

        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            names_str = "\n".join(names)

            # Check key files are present (use forward slash for zip paths)
            self.assertTrue(
                any("SKILL.md" in n for n in names),
                f"SKILL.md should be included. Files:\n{names_str}"
            )
            self.assertTrue(
                any("README.md" in n for n in names),
                f"README.md should be included. Files:\n{names_str}"
            )
            self.assertTrue(
                any("NEOS_PRINCIPLES.md" in n for n in names),
                f"NEOS_PRINCIPLES.md should be included. Files:\n{names_str}"
            )
            self.assertTrue(
                any("STRESS_TEST_PROTOCOL.md" in n for n in names),
                f"STRESS_TEST_PROTOCOL.md should be included. Files:\n{names_str}"
            )
            self.assertTrue(
                any("template.yaml" in n for n in names),
                f"Assets should be included. Files:\n{names_str}"
            )
            self.assertTrue(
                any("references" in n for n in names),
                f"References should be included. Files:\n{names_str}"
            )


class TestValidationFailureAborts(unittest.TestCase):
    """Test: packaging aborts when skill validation fails."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        # Create a validator stub that FAILS
        create_validate_skill_stub(self.tmp_dir, should_pass=False)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_validation_failure_aborts(self):
        """Packaging should abort (exit 1) when validation fails."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 1, f"Should fail when validation fails.\nstdout: {stdout}\nstderr: {stderr}")
        # The zip should not be created (or should be cleaned up)
        self.assertFalse(
            os.path.exists(output_path),
            "Zip file should not exist when validation fails"
        )


class TestIncludeScriptsFlag(unittest.TestCase):
    """Test: --include-scripts adds validate_skill.py to the zip."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_include_scripts_flag(self):
        """--include-scripts adds validate_skill.py to the zip."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
            "--include-scripts",
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")

        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            self.assertTrue(
                any("validate_skill.py" in n for n in names),
                f"validate_skill.py should be included with --include-scripts. Files:\n{chr(10).join(names)}"
            )

    def test_without_include_scripts_flag(self):
        """Without --include-scripts, validate_skill.py should NOT be in the zip."""
        output_path = os.path.join(self.tmp_dir, "output.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")

        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            self.assertFalse(
                any("validate_skill.py" in n for n in names),
                f"validate_skill.py should NOT be included without --include-scripts. Files:\n{chr(10).join(names)}"
            )


class TestOutputFilename(unittest.TestCase):
    """Test: default and custom output paths."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.neos_core = create_minimal_neos_tree(self.tmp_dir)
        create_validate_skill_stub(self.tmp_dir, should_pass=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_custom_output_path(self):
        """Custom --output path is used."""
        output_path = os.path.join(self.tmp_dir, "custom-name.zip")
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
            "--output", output_path,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        self.assertTrue(os.path.exists(output_path), "Custom output path should be used")

    def test_default_output_path(self):
        """Default output path is neos-core-vX.Y.Z.zip in project root."""
        code, stdout, stderr = run_packager(
            "--project-root", self.tmp_dir,
        )
        self.assertEqual(code, 0, f"Should succeed.\nstdout: {stdout}\nstderr: {stderr}")
        default_path = os.path.join(self.tmp_dir, "neos-core-v1.2.3.zip")
        self.assertTrue(
            os.path.exists(default_path),
            f"Default output file neos-core-v1.2.3.zip should exist at {default_path}"
        )


if __name__ == "__main__":
    unittest.main()
