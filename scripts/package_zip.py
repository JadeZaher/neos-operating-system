#!/usr/bin/env python3
"""NEOS Skill Stack Packager -- packages neos-core into a distributable zip.

Usage:
    python package_zip.py [--output <path>] [--include-scripts] [--project-root <dir>]

Packages neos-core/ contents into a versioned zip file after validating all
SKILL.md files. Prints a manifest of included files and total size.

Exit codes: 0 = success, 1 = failure
"""

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path


# --- Constants ---

# Directories to exclude entirely (matched against path components)
EXCLUDED_DIRS = {
    "conductor",
    ".git",
    "__pycache__",
    "reference-docs",
    "fixtures",
}

# File patterns to exclude
EXCLUDED_FILE_PREFIXES = ("test_",)
EXCLUDED_FILE_SUFFIXES = (".pyc",)
EXCLUDED_FILES = {".gitignore"}


# --- Helpers ---

def read_version(neos_core_dir: Path) -> str:
    """Read the version string from neos-core/VERSION.

    Returns the stripped version string.
    Raises SystemExit if the file is missing or empty.
    """
    version_file = neos_core_dir / "VERSION"
    if not version_file.exists():
        print(f"Error: VERSION file not found at {version_file}", file=sys.stderr)
        sys.exit(1)

    version = version_file.read_text(encoding="utf-8").strip()
    if not version:
        print(f"Error: VERSION file is empty at {version_file}", file=sys.stderr)
        sys.exit(1)

    return version


def find_skill_files(neos_core_dir: Path) -> list:
    """Find all SKILL.md files under neos-core/."""
    skill_files = []
    for root, _dirs, files in os.walk(neos_core_dir):
        for fname in files:
            if fname == "SKILL.md":
                skill_files.append(Path(root) / fname)
    return sorted(skill_files)


def run_validation(project_root: Path, neos_core_dir: Path) -> bool:
    """Run validate_skill.py on the neos-core directory.

    Returns True if validation passes, False otherwise.
    """
    validator = project_root / "scripts" / "validate_skill.py"
    if not validator.exists():
        print(f"Warning: validate_skill.py not found at {validator}, skipping validation")
        return True

    skill_files = find_skill_files(neos_core_dir)
    if not skill_files:
        print("Warning: No SKILL.md files found, skipping validation")
        return True

    print(f"Validating {len(skill_files)} SKILL.md file(s)...")
    result = subprocess.run(
        [sys.executable, str(validator), str(neos_core_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Validation FAILED:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return False

    print("Validation passed.")
    return True


def should_exclude(rel_path: Path) -> bool:
    """Check if a relative path should be excluded from the zip."""
    parts = rel_path.parts

    # Check directory exclusions
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True

    # Check file-level exclusions
    filename = rel_path.name
    if filename in EXCLUDED_FILES:
        return True

    for prefix in EXCLUDED_FILE_PREFIXES:
        if filename.startswith(prefix):
            return True

    for suffix in EXCLUDED_FILE_SUFFIXES:
        if filename.endswith(suffix):
            return True

    return False


def collect_files(project_root: Path, include_scripts: bool) -> list:
    """Collect all files to include in the zip.

    Returns a list of (absolute_path, archive_name) tuples.
    """
    files = []
    neos_core_dir = project_root / "neos-core"

    # Walk neos-core/ and add all non-excluded files
    for root, dirs, filenames in os.walk(neos_core_dir):
        root_path = Path(root)
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for fname in filenames:
            file_path = root_path / fname
            rel_to_project = file_path.relative_to(project_root)

            if should_exclude(rel_to_project):
                continue

            # Archive name is relative to project root
            archive_name = str(rel_to_project).replace("\\", "/")
            files.append((file_path, archive_name))

    # Optionally include scripts/validate_skill.py
    if include_scripts:
        validator = project_root / "scripts" / "validate_skill.py"
        if validator.exists():
            archive_name = "scripts/validate_skill.py"
            files.append((validator, archive_name))

    return sorted(files, key=lambda x: x[1])


def format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def create_zip(output_path: Path, files: list) -> int:
    """Create the zip file from the collected file list.

    Returns the total uncompressed size in bytes.
    """
    total_size = 0
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for abs_path, archive_name in files:
            zf.write(abs_path, archive_name)
            total_size += abs_path.stat().st_size

    return total_size


def print_manifest(files: list, total_size: int, output_path: Path, version: str):
    """Print the manifest of included files and summary."""
    print(f"\nNEOS Skill Stack v{version}")
    print(f"{'=' * 60}")
    print(f"Output: {output_path}")
    print(f"\nIncluded files ({len(files)}):")
    for _, archive_name in files:
        print(f"  {archive_name}")
    print(f"\nTotal size (uncompressed): {format_size(total_size)}")
    zip_size = output_path.stat().st_size
    print(f"Zip size: {format_size(zip_size)}")
    print(f"\nPackaging complete: {output_path.name}")


# --- Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="Package the NEOS skill stack into a distributable zip."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output zip file path (default: neos-core-vX.Y.Z.zip in project root)",
    )
    parser.add_argument(
        "--include-scripts",
        action="store_true",
        help="Include scripts/validate_skill.py in the zip",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: parent of scripts/)",
    )
    args = parser.parse_args()

    # Resolve project root
    if args.project_root:
        project_root = Path(args.project_root).resolve()
    else:
        # Default: parent directory of this script's directory
        project_root = Path(__file__).resolve().parent.parent

    neos_core_dir = project_root / "neos-core"
    if not neos_core_dir.exists():
        print(f"Error: neos-core/ directory not found at {neos_core_dir}", file=sys.stderr)
        sys.exit(1)

    # Read version
    version = read_version(neos_core_dir)

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = project_root / f"neos-core-v{version}.zip"

    # Run validation
    if not run_validation(project_root, neos_core_dir):
        print("\nPackaging aborted due to validation failures.", file=sys.stderr)
        sys.exit(1)

    # Collect files
    files = collect_files(project_root, args.include_scripts)
    if not files:
        print("Error: No files found to package.", file=sys.stderr)
        sys.exit(1)

    # Create zip
    total_size = create_zip(output_path, files)

    # Print manifest
    print_manifest(files, total_size, output_path, version)

    sys.exit(0)


if __name__ == "__main__":
    main()
