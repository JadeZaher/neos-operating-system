#!/usr/bin/env python3
"""NEOS Skill Validator -- validates SKILL.md files against the NEOS specification.

Usage:
    python validate_skill.py <path>                    # Validate a single file or directory
    python validate_skill.py <path> --verbose          # Show all checks performed
    python validate_skill.py <path> --cross-reference  # Cross-reference dependency check

Validates:
  - YAML frontmatter with required fields (name, description, layer, version, depends_on)
  - All 12 sections (A through L) present with substantive content
  - OmniOne walkthrough present
  - All 7 stress-test scenarios present
  - Under 500 lines

Cross-reference mode (--cross-reference):
  - Verifies all depends_on entries point to real skills
  - Scans body text for references to other skills
  - Reports orphan references (to non-existent skills)
  - Reports unreferenced skills (nothing depends on them)
  - Produces a dependency list

Exit codes: 0 = all pass, 1 = any fail
"""

import os
import re
import sys


# --- Constants ---

REQUIRED_FRONTMATTER = {
    "name": str,
    "description": str,
    "layer": int,
    "version": str,
    "depends_on": list,
}

REQUIRED_SECTIONS = [
    ("A", "Structural Problem It Solves"),
    ("B", "Domain Scope"),
    ("C", "Trigger Conditions"),
    ("D", "Required Inputs"),
    ("E", "Step-by-Step Process"),
    ("F", "Output Artifact"),
    ("G", "Authority Boundary Check"),
    ("H", "Capture Resistance Check"),
    ("I", "Failure Containment Logic"),
    ("J", "Expiry / Review Condition"),
    ("K", "Exit Compatibility Check"),
    ("L", "Cross-Unit Interoperability Impact"),
]

STRESS_TEST_SCENARIOS = [
    "Capital Influx",
    "Emergency Crisis",
    "Leadership Charisma Capture",
    "High Conflict",
    "Large-Scale Replication",
    "External Legal Pressure",
    "Sudden Exit of 30%",
]

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# Matches any section or major named header that terminates section content.
# Covers ## A., ### A:, ## OmniOne, ## Stress, etc.
_SECTION_STOP_RE = re.compile(
    r"^#{1,3}\s+(?:[A-L][\.\:\)]|OmniOne|Stress)", re.IGNORECASE
)


# --- Frontmatter Parsing ---

def parse_frontmatter(content):
    """Parse YAML frontmatter between --- delimiters. Returns (dict, errors).

    Errors list is non-empty only when the frontmatter block itself is absent
    or structurally broken. Field-level errors come from validate_frontmatter().
    """
    lines = content.split("\n")

    delimiters = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            delimiters.append(i)
            if len(delimiters) == 2:
                break

    if len(delimiters) < 2:
        return {}, ["Missing YAML frontmatter -- add a --- ... --- block at the top of the file"]

    fm_lines = lines[delimiters[0] + 1 : delimiters[1]]
    frontmatter = {}

    for line in fm_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        # Strip surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # Parse list values
        if value == "[]":
            frontmatter[key] = []
        elif value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            frontmatter[key] = [item.strip().strip("\"'") for item in items if item.strip()]
        else:
            frontmatter[key] = value

    return frontmatter, []


def validate_frontmatter(frontmatter):
    """Validate frontmatter has all required fields with correct types.

    Returns a list of error strings. Each error names the field and says
    exactly what the author needs to fix.
    """
    errors = []

    for field, expected_type in REQUIRED_FRONTMATTER.items():
        if field not in frontmatter:
            errors.append(
                f"Missing required frontmatter field '{field}' -- add '{field}: <value>' inside the --- block"
            )
            continue

        value = frontmatter[field]

        if expected_type == int:
            try:
                int(value)
            except (ValueError, TypeError):
                errors.append(
                    f"Frontmatter field '{field}' must be an integer (e.g. layer: 1), got: {value!r}"
                )

        elif expected_type == str:
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"Frontmatter field '{field}' must be a non-empty string, got: {value!r}"
                )

        elif expected_type == list:
            if not isinstance(value, list):
                errors.append(
                    f"Frontmatter field '{field}' must be a list (e.g. depends_on: [] or [skill-a, skill-b]), got: {value!r}"
                )

    # Semver check (only when version is present and a string)
    if "version" in frontmatter:
        version = frontmatter["version"]
        if isinstance(version, str) and not SEMVER_PATTERN.match(version):
            errors.append(
                f"Frontmatter 'version' must follow semver format X.Y.Z (e.g. 1.0.0), got: {version!r}"
            )

    return errors


# --- Section Validation ---

def find_sections(content):
    """Find all required sections, returning {letter: (header_line, content_lines)}.

    A section's content runs from the line after its header until the next
    section-level header (A-L, OmniOne, or Stress) or end of file.
    Returns None for any section that is not found.
    """
    lines = content.split("\n")
    sections = {}

    for letter, title in REQUIRED_SECTIONS:
        pattern = re.compile(
            rf"^#+\s*{re.escape(letter)}[\.\:\)]\s*{re.escape(title)}",
            re.IGNORECASE,
        )

        found_idx = None
        for i, line in enumerate(lines):
            if pattern.search(line):
                found_idx = i
                break

        if found_idx is not None:
            content_lines = []
            for j in range(found_idx + 1, len(lines)):
                if _SECTION_STOP_RE.match(lines[j]):
                    break
                content_lines.append(lines[j])
            sections[letter] = (lines[found_idx], content_lines)
        else:
            sections[letter] = None

    return sections


def validate_sections(content):
    """Validate all 12 sections (A-L) exist with substantive content.

    Substantive = at least 3 non-empty, non-comment lines OR 30+ words.
    Returns a list of error strings that name the missing/empty section.
    """
    errors = []
    sections = find_sections(content)

    for letter, title in REQUIRED_SECTIONS:
        if sections.get(letter) is None:
            errors.append(
                f"Missing section '{letter}. {title}' -- add a header like '## {letter}. {title}' with content"
            )
            continue

        _, content_lines = sections[letter]
        substantive = [
            ln for ln in content_lines
            if ln.strip() and not ln.strip().startswith("<!--")
        ]
        total_words = sum(len(ln.split()) for ln in substantive)

        if len(substantive) < 3 and total_words < 30:
            errors.append(
                f"Section '{letter}. {title}' has insufficient content "
                f"({len(substantive)} substantive lines, {total_words} words) -- "
                f"add at least 3 lines or 30 words of content"
            )

    return errors


# --- Walkthrough & Stress Test Validation ---

def validate_walkthrough(content):
    """Check that an OmniOne Walkthrough section header is present."""
    pattern = re.compile(
        r"^#{1,3}\s+(?:OmniOne\s+Walkthrough|OmniOne\s+Example)",
        re.IGNORECASE | re.MULTILINE,
    )
    if not pattern.search(content):
        return [
            "Missing 'OmniOne Walkthrough' section -- add a header like '## OmniOne Walkthrough' "
            "followed by a concrete step-by-step example using OmniOne roles (TH, AE, OSC, GEV)"
        ]
    return []


def validate_stress_tests(content):
    """Check all 7 stress-test scenarios are present (case-insensitive substring match).

    Returns one error per missing scenario.
    """
    errors = []
    content_lower = content.lower()
    for scenario in STRESS_TEST_SCENARIOS:
        if scenario.lower() not in content_lower:
            errors.append(
                f"Missing stress-test scenario '{scenario}' -- "
                f"add a narrative block covering this scenario in the Stress Tests section"
            )
    return errors


# --- Line Count ---

def validate_line_count(content):
    """Check file is under 500 lines."""
    line_count = len(content.split("\n"))
    if line_count > 500:
        return [
            f"File exceeds 500-line limit ({line_count} lines) -- "
            f"split into multiple skill files or trim non-essential prose"
        ]
    return []


# --- Core Validation Orchestrator ---

def validate_file(filepath, verbose=False):
    """Validate a single SKILL.md file. Returns (passed: bool, errors: list[str]).

    When verbose=True, prints a check-by-check trace to stdout showing both
    passing and failing checks.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, OSError) as e:
        return False, [f"Cannot read file: {e}"]

    all_errors = []

    def _report(label, errors, pass_msg):
        """Print verbose trace for one check group."""
        if not verbose:
            return
        if errors:
            print(f"    [fail]  {label}")
            for err in errors:
                print(f"            - {err}")
        else:
            print(f"    [pass]  {pass_msg}")

    if verbose:
        print(f"\n  Checking: {filepath}")
        print("    [check] YAML frontmatter...")

    frontmatter, parse_errors = parse_frontmatter(content)
    if parse_errors:
        all_errors.extend(parse_errors)
        _report("YAML frontmatter", parse_errors, "")
        fm_errors = []
    else:
        fm_errors = validate_frontmatter(frontmatter)
        all_errors.extend(fm_errors)
        _report("Frontmatter fields", fm_errors, "Frontmatter valid (all 5 fields present)")

    if verbose:
        print("    [check] Required sections (A-L)...")
    section_errors = validate_sections(content)
    all_errors.extend(section_errors)
    _report("Sections A-L", section_errors, "All 12 sections present with substantive content")

    if verbose:
        print("    [check] OmniOne walkthrough...")
    walk_errors = validate_walkthrough(content)
    all_errors.extend(walk_errors)
    _report("OmniOne walkthrough", walk_errors, "OmniOne walkthrough section found")

    if verbose:
        print("    [check] Stress-test scenarios...")
    stress_errors = validate_stress_tests(content)
    all_errors.extend(stress_errors)
    _report("Stress-test scenarios", stress_errors, "All 7 stress-test scenarios found")

    if verbose:
        print("    [check] Line count...")
    line_errors = validate_line_count(content)
    all_errors.extend(line_errors)
    if not line_errors:
        line_count = len(content.split("\n"))
        _report("Line count", line_errors, f"{line_count} lines (within 500-line limit)")
    else:
        _report("Line count", line_errors, "")

    return len(all_errors) == 0, all_errors


# --- File Discovery ---

def find_skill_files(path):
    """Return all SKILL.md file paths under path (file or directory, recursive)."""
    if os.path.isfile(path):
        return [path]

    skill_files = []
    for root, _dirs, files in os.walk(path):
        for fname in files:
            if fname == "SKILL.md":
                skill_files.append(os.path.join(root, fname))

    return sorted(skill_files)


# --- Output Formatting ---

def _print_result(filepath, passed, errors):
    """Print the single-line result (PASS/FAIL) for one file."""
    if passed:
        print(f"PASS: {filepath}")
    else:
        print(f"FAIL: {filepath}")
        for err in errors:
            print(f"  - {err}")


# --- Cross-Reference Validation ---

# Pattern to match references like "the agreement-creation skill" or "per agreement-creation"
_SKILL_REF_PATTERN = re.compile(
    r"(?:the\s+|per\s+|from\s+|via\s+|using\s+|see\s+|invoke[sd]?\s+)([a-z][a-z0-9-]+(?:-[a-z0-9]+)+)\b",
    re.IGNORECASE,
)


def _extract_skill_name_from_path(filepath):
    """Extract the skill directory name from a SKILL.md path."""
    # SKILL.md is in a directory named after the skill
    return os.path.basename(os.path.dirname(filepath))


def _load_skill_metadata(filepath):
    """Load frontmatter and body text from a SKILL.md file.

    Returns (frontmatter_dict, body_text) or (None, None) on error.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (IOError, OSError):
        return None, None

    frontmatter, errors = parse_frontmatter(content)
    if errors:
        return None, content

    return frontmatter, content


def cross_reference_check(path):
    """Run cross-reference validation on all SKILL.md files under path.

    Checks:
      1. Every depends_on entry points to a real SKILL.md
      2. Body text references to skill names match existing skills
      3. Reports orphan references (to non-existent skills)
      4. Reports unreferenced skills (nothing depends on them)
      5. Produces a dependency list

    Returns (passed: bool, report_lines: list[str]).
    """
    files = find_skill_files(path)
    if not files:
        return False, [f"No SKILL.md files found at: {path}"]

    # Build skill registry: directory_name -> filepath
    skill_registry = {}
    for filepath in files:
        dir_name = _extract_skill_name_from_path(filepath)
        skill_registry[dir_name] = filepath

    # Also build name->dir_name map from frontmatter names
    fm_name_to_dir = {}
    skill_data = {}

    for filepath in files:
        dir_name = _extract_skill_name_from_path(filepath)
        frontmatter, body = _load_skill_metadata(filepath)
        if frontmatter is None:
            frontmatter = {}
        fm_name = frontmatter.get("name", dir_name)
        fm_name_to_dir[fm_name] = dir_name
        depends_on = frontmatter.get("depends_on", [])
        if not isinstance(depends_on, list):
            depends_on = []
        skill_data[dir_name] = {
            "filepath": filepath,
            "name": fm_name,
            "depends_on": depends_on,
            "body": body or "",
        }

    # All known skill names (both directory names and frontmatter names)
    all_known_names = set(skill_registry.keys()) | set(fm_name_to_dir.keys())

    errors = []
    warnings = []
    dependency_list = []
    depended_on = set()  # Skills that something depends on

    # Check depends_on entries
    for dir_name, data in sorted(skill_data.items()):
        for dep in data["depends_on"]:
            dependency_list.append((data["name"], dep))
            if dep in all_known_names:
                depended_on.add(dep)
            else:
                errors.append(
                    f"Orphan dependency: '{data['name']}' depends on '{dep}' "
                    f"which does not correspond to any SKILL.md"
                )

    # Scan body text for references to skill names
    body_refs = {}  # skill_name -> set of referenced skill names
    for dir_name, data in sorted(skill_data.items()):
        refs = set()
        for match in _SKILL_REF_PATTERN.finditer(data["body"]):
            ref_name = match.group(1).lower()
            # Only flag if it looks like a skill name (has hyphens, multi-word)
            if ref_name != dir_name and ref_name != data["name"]:
                refs.add(ref_name)

        body_refs[dir_name] = refs

        # Check if body references point to real skills
        for ref in refs:
            if ref not in all_known_names:
                # Only report if it really looks like a skill reference
                # (skip common phrases that match the pattern)
                if len(ref) > 5 and "-" in ref:
                    warnings.append(
                        f"Possible orphan reference in '{data['name']}': "
                        f"mentions '{ref}' which is not a known skill"
                    )
            else:
                depended_on.add(ref)

    # Find unreferenced skills (nothing depends on them, not referenced in body)
    unreferenced = []
    for dir_name, data in sorted(skill_data.items()):
        name = data["name"]
        if name not in depended_on and dir_name not in depended_on:
            unreferenced.append(name)

    # Build report
    report = []
    report.append(f"Cross-Reference Report for {len(skill_data)} skills")
    report.append("=" * 60)

    # Dependency list
    report.append("\nDependency List:")
    if dependency_list:
        for source, target in sorted(dependency_list):
            status = "OK" if target in all_known_names else "MISSING"
            report.append(f"  {source} -> {target} [{status}]")
    else:
        report.append("  (no dependencies declared)")

    # Errors
    if errors:
        report.append(f"\nOrphan Dependencies ({len(errors)}):")
        for err in errors:
            report.append(f"  - {err}")

    # Warnings (body text references)
    if warnings:
        report.append(f"\nPossible Orphan References ({len(warnings)}):")
        for warn in warnings:
            report.append(f"  - {warn}")

    # Unreferenced skills
    if unreferenced:
        report.append(f"\nUnreferenced Skills ({len(unreferenced)}) -- nothing depends on these:")
        for name in unreferenced:
            report.append(f"  - {name}")

    # Summary
    report.append(f"\nSummary:")
    report.append(f"  Total skills: {len(skill_data)}")
    report.append(f"  Dependencies declared: {len(dependency_list)}")
    report.append(f"  Orphan dependencies: {len(errors)}")
    report.append(f"  Possible orphan references: {len(warnings)}")
    report.append(f"  Unreferenced skills: {len(unreferenced)}")

    passed = len(errors) == 0
    return passed, report


# --- Entry Point ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_skill.py <path> [--verbose] [--cross-reference]")
        print("  <path>              Path to a SKILL.md file or directory to scan recursively")
        print("  --verbose           Show all checks performed (passing and failing)")
        print("  --cross-reference   Cross-reference dependency verification")
        sys.exit(1)

    path = sys.argv[1]
    verbose = "--verbose" in sys.argv
    cross_ref = "--cross-reference" in sys.argv

    if not os.path.exists(path):
        print(f"Error: path does not exist: {path}")
        sys.exit(1)

    # Cross-reference mode
    if cross_ref:
        passed, report = cross_reference_check(path)
        for line in report:
            print(line)
        sys.exit(0 if passed else 1)

    # Standard validation mode
    files = find_skill_files(path)
    if not files:
        print(f"No SKILL.md files found at: {path}")
        sys.exit(1)

    if verbose:
        print(f"Validating {len(files)} SKILL.md file(s)...")

    results = []
    for filepath in files:
        passed, errors = validate_file(filepath, verbose=verbose)
        results.append((filepath, passed, errors))
        _print_result(filepath, passed, errors)

    if verbose:
        passed_count = sum(1 for _, p, _ in results if p)
        total = len(results)
        print(f"\n{'=' * 60}")
        print(f"Results: {passed_count}/{total} passed")

    any_failed = any(not p for _, p, _ in results)
    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
