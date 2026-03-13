#!/usr/bin/env python3
"""NEOS Stress Test Report -- aggregated stress test summary across all skills.

Usage:
    python stress_test_report.py [--path <neos-core-dir>] [--format text|markdown]

Scans all SKILL.md files and produces:
  a) Coverage matrix (skills x scenarios)
  b) Per-scenario summary (coverage count, missing skills)
  c) Strength/weakness analysis (response quality heuristic)
  d) Full skill index (all skills with layer, name, description)

Exit codes: 0 = success
"""

import argparse
import os
import re
import sys
from pathlib import Path


# --- Constants ---

STRESS_TEST_SCENARIOS = [
    "Capital Influx",
    "Emergency Crisis",
    "Leadership Charisma Capture",
    "High Conflict",
    "Large-Scale Replication",
    "External Legal Pressure",
    "Sudden Exit",
]

# Keywords that indicate structural strength in a stress-test response
STRENGTH_KEYWORDS = [
    "prevent", "protect", "safeguard", "ensure", "require",
    "structural", "consent", "accountability", "review",
    "automatic", "mandatory", "flag", "escalat",
]


# --- Frontmatter Parsing (simple regex, no PyYAML) ---

def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter between --- delimiters.

    Returns a dict with extracted fields. Uses simple regex parsing
    since we cannot depend on PyYAML.
    """
    lines = content.split("\n")
    delimiters = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            delimiters.append(i)
            if len(delimiters) == 2:
                break

    if len(delimiters) < 2:
        return {}

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

    return frontmatter


# --- Skill Discovery ---

def find_skill_files(neos_core_dir: Path) -> list:
    """Find all SKILL.md files under neos-core/ recursively."""
    skill_files = []
    for root, _dirs, files in os.walk(neos_core_dir):
        for fname in files:
            if fname == "SKILL.md":
                skill_files.append(Path(root) / fname)
    return sorted(skill_files)


# --- Stress Test Extraction ---

def extract_stress_tests(content: str) -> dict:
    """Extract stress-test scenario responses from SKILL.md content.

    Returns a dict mapping scenario name -> response text.
    Only includes scenarios that are actually present.
    """
    results = {}

    # Find stress-test section headers (### 1. Capital Influx, etc.)
    # Match patterns like "### 1. Capital Influx" or "### 1. Capital Influx Scenario"
    scenario_pattern = re.compile(
        r"^###\s+\d+\.\s+(.+?)$",
        re.MULTILINE,
    )

    matches = list(scenario_pattern.finditer(content))

    for i, match in enumerate(matches):
        scenario_title = match.group(1).strip()
        start = match.end()
        # Content runs until the next ### header or end of major section
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            # Look for end of file or next ## header
            next_section = re.search(r"^##\s+", content[start:], re.MULTILINE)
            end = start + next_section.start() if next_section else len(content)

        response_text = content[start:end].strip()

        # Map to canonical scenario names
        canonical = _match_canonical_scenario(scenario_title)
        if canonical:
            results[canonical] = response_text

    return results


def _match_canonical_scenario(title: str) -> str:
    """Match a scenario title to its canonical name.

    Returns the canonical name or empty string if no match.
    """
    title_lower = title.lower()
    for scenario in STRESS_TEST_SCENARIOS:
        if scenario.lower() in title_lower:
            return scenario
    return ""


# --- Analysis ---

def analyze_response_strength(response_text: str) -> dict:
    """Analyze the structural strength of a stress-test response.

    Returns a dict with:
      - word_count: total words
      - keyword_count: number of strength keywords found
      - rating: "strong", "moderate", or "weak"
    """
    words = response_text.split()
    word_count = len(words)

    text_lower = response_text.lower()
    keyword_count = sum(1 for kw in STRENGTH_KEYWORDS if kw in text_lower)

    if word_count >= 50 and keyword_count >= 3:
        rating = "strong"
    elif word_count >= 25 and keyword_count >= 1:
        rating = "moderate"
    else:
        rating = "weak"

    return {
        "word_count": word_count,
        "keyword_count": keyword_count,
        "rating": rating,
    }


# --- Skill Data Collection ---

def collect_skill_data(skill_files: list) -> list:
    """Collect frontmatter and stress-test data from all skills.

    Returns a list of dicts, each with:
      - path: file path
      - name: skill name
      - description: skill description
      - layer: layer number
      - version: version string
      - depends_on: dependency list
      - stress_tests: {scenario_name: response_text}
      - stress_analysis: {scenario_name: {word_count, keyword_count, rating}}
    """
    skills = []

    for skill_path in skill_files:
        content = skill_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        stress_tests = extract_stress_tests(content)

        stress_analysis = {}
        for scenario, response in stress_tests.items():
            stress_analysis[scenario] = analyze_response_strength(response)

        skills.append({
            "path": str(skill_path),
            "name": fm.get("name", skill_path.parent.name),
            "description": fm.get("description", ""),
            "layer": fm.get("layer", "?"),
            "version": fm.get("version", "?"),
            "depends_on": fm.get("depends_on", []),
            "stress_tests": stress_tests,
            "stress_analysis": stress_analysis,
        })

    return skills


# --- Report Generation ---

def generate_markdown_report(skills: list) -> str:
    """Generate a markdown-formatted stress test report."""
    lines = []

    lines.append("# NEOS Stress Test Report")
    lines.append("")
    lines.append(f"Total skills analyzed: {len(skills)}")
    lines.append("")

    # --- Coverage Matrix ---
    lines.append("## Coverage Matrix")
    lines.append("")

    # Table header
    header = "| Skill | Layer |"
    separator = "|-------|-------|"
    for scenario in STRESS_TEST_SCENARIOS:
        short = _abbreviate_scenario(scenario)
        header += f" {short} |"
        separator += "------|"

    lines.append(header)
    lines.append(separator)

    for skill in sorted(skills, key=lambda s: (str(s["layer"]), s["name"])):
        row = f"| {skill['name']} | {skill['layer']} |"
        for scenario in STRESS_TEST_SCENARIOS:
            if scenario in skill["stress_tests"]:
                analysis = skill["stress_analysis"].get(scenario, {})
                rating = analysis.get("rating", "?")
                symbol = {"strong": "++", "moderate": "+", "weak": "~"}.get(rating, "?")
                row += f" {symbol} |"
            else:
                row += " - |"
        lines.append(row)

    lines.append("")

    # Legend
    lines.append("**Legend:** `++` strong | `+` moderate | `~` weak | `-` absent")
    lines.append("")

    # --- Per-Scenario Summary ---
    lines.append("## Per-Scenario Summary")
    lines.append("")

    for scenario in STRESS_TEST_SCENARIOS:
        lines.append(f"### {scenario}")
        lines.append("")

        covered = [s for s in skills if scenario in s["stress_tests"]]
        missing = [s for s in skills if scenario not in s["stress_tests"]]

        lines.append(f"- **Coverage:** {len(covered)}/{len(skills)} skills")

        if missing:
            missing_names = ", ".join(s["name"] for s in missing)
            lines.append(f"- **Missing:** {missing_names}")

        if covered:
            ratings = [
                s["stress_analysis"][scenario]["rating"]
                for s in covered
                if scenario in s["stress_analysis"]
            ]
            strong = ratings.count("strong")
            moderate = ratings.count("moderate")
            weak = ratings.count("weak")
            lines.append(f"- **Quality:** {strong} strong, {moderate} moderate, {weak} weak")

        lines.append("")

    # --- Strength/Weakness Analysis ---
    lines.append("## Strength/Weakness Analysis")
    lines.append("")

    # Find skills with strongest and weakest coverage
    for skill in sorted(skills, key=lambda s: s["name"]):
        total_scenarios = len(STRESS_TEST_SCENARIOS)
        covered_count = len(skill["stress_tests"])
        coverage_pct = (covered_count / total_scenarios * 100) if total_scenarios > 0 else 0

        ratings = [a["rating"] for a in skill["stress_analysis"].values()]
        strong = ratings.count("strong")
        moderate = ratings.count("moderate")
        weak = ratings.count("weak")

        lines.append(f"- **{skill['name']}** (Layer {skill['layer']}): "
                      f"{covered_count}/{total_scenarios} scenarios ({coverage_pct:.0f}%) | "
                      f"{strong} strong, {moderate} moderate, {weak} weak")

    lines.append("")

    # --- Skill Index ---
    lines.append("## Skill Index")
    lines.append("")
    lines.append("| Layer | Name | Description | Version |")
    lines.append("|-------|------|-------------|---------|")

    for skill in sorted(skills, key=lambda s: (str(s["layer"]), s["name"])):
        desc = skill["description"]
        # Truncate long descriptions for the table
        if len(desc) > 80:
            desc = desc[:77] + "..."
        lines.append(f"| {skill['layer']} | {skill['name']} | {desc} | {skill['version']} |")

    lines.append("")

    return "\n".join(lines)


def generate_text_report(skills: list) -> str:
    """Generate a plain text stress test report."""
    lines = []

    lines.append("NEOS STRESS TEST REPORT")
    lines.append("=" * 60)
    lines.append(f"Total skills analyzed: {len(skills)}")
    lines.append("")

    # --- Coverage Matrix ---
    lines.append("COVERAGE MATRIX")
    lines.append("-" * 60)

    # Column header
    scenario_shorts = [_abbreviate_scenario(s) for s in STRESS_TEST_SCENARIOS]
    header = f"{'Skill':<30} {'Lyr':>3} " + " ".join(f"{s:>5}" for s in scenario_shorts)
    lines.append(header)
    lines.append("-" * len(header))

    for skill in sorted(skills, key=lambda s: (str(s["layer"]), s["name"])):
        name = skill["name"]
        if len(name) > 28:
            name = name[:25] + "..."
        row = f"{name:<30} {str(skill['layer']):>3} "
        for scenario in STRESS_TEST_SCENARIOS:
            if scenario in skill["stress_tests"]:
                analysis = skill["stress_analysis"].get(scenario, {})
                rating = analysis.get("rating", "?")
                symbol = {"strong": "++", "moderate": "+", "weak": "~"}.get(rating, "?")
                row += f"{symbol:>5} "
            else:
                row += f"{'-':>5} "
        lines.append(row)

    lines.append("")
    lines.append("Legend: ++ strong | + moderate | ~ weak | - absent")
    lines.append("")

    # --- Per-Scenario Summary ---
    lines.append("PER-SCENARIO SUMMARY")
    lines.append("-" * 60)

    for scenario in STRESS_TEST_SCENARIOS:
        covered = [s for s in skills if scenario in s["stress_tests"]]
        missing = [s for s in skills if scenario not in s["stress_tests"]]

        lines.append(f"\n  {scenario}")
        lines.append(f"    Coverage: {len(covered)}/{len(skills)} skills")

        if missing:
            missing_names = ", ".join(s["name"] for s in missing)
            lines.append(f"    Missing: {missing_names}")

        if covered:
            ratings = [
                s["stress_analysis"][scenario]["rating"]
                for s in covered
                if scenario in s["stress_analysis"]
            ]
            strong = ratings.count("strong")
            moderate = ratings.count("moderate")
            weak = ratings.count("weak")
            lines.append(f"    Quality: {strong} strong, {moderate} moderate, {weak} weak")

    lines.append("")

    # --- Strength/Weakness Analysis ---
    lines.append("STRENGTH/WEAKNESS ANALYSIS")
    lines.append("-" * 60)

    for skill in sorted(skills, key=lambda s: s["name"]):
        total_scenarios = len(STRESS_TEST_SCENARIOS)
        covered_count = len(skill["stress_tests"])
        coverage_pct = (covered_count / total_scenarios * 100) if total_scenarios > 0 else 0

        ratings = [a["rating"] for a in skill["stress_analysis"].values()]
        strong = ratings.count("strong")
        moderate = ratings.count("moderate")
        weak = ratings.count("weak")

        lines.append(f"  {skill['name']} (Layer {skill['layer']}): "
                      f"{covered_count}/{total_scenarios} scenarios ({coverage_pct:.0f}%) | "
                      f"{strong} strong, {moderate} moderate, {weak} weak")

    lines.append("")

    # --- Skill Index ---
    lines.append("SKILL INDEX")
    lines.append("-" * 60)

    for skill in sorted(skills, key=lambda s: (str(s["layer"]), s["name"])):
        lines.append(f"  Layer {skill['layer']}: {skill['name']}")
        if skill["description"]:
            desc = skill["description"]
            if len(desc) > 70:
                desc = desc[:67] + "..."
            lines.append(f"    {desc}")
        lines.append(f"    Version: {skill['version']}")
        lines.append("")

    return "\n".join(lines)


def _abbreviate_scenario(scenario: str) -> str:
    """Create a short abbreviation for a scenario name."""
    abbreviations = {
        "Capital Influx": "Cap",
        "Emergency Crisis": "Emrg",
        "Leadership Charisma Capture": "Lead",
        "High Conflict": "Conf",
        "Large-Scale Replication": "Scal",
        "External Legal Pressure": "Legl",
        "Sudden Exit": "Exit",
    }
    return abbreviations.get(scenario, scenario[:4])


# --- Entry Point ---

def main():
    parser = argparse.ArgumentParser(
        description="Generate aggregated stress test report for NEOS skills."
    )
    parser.add_argument(
        "--path",
        type=str,
        default="neos-core",
        help="Path to neos-core directory (default: neos-core/)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    neos_core_dir = Path(args.path).resolve()
    if not neos_core_dir.exists():
        print(f"Error: directory not found: {neos_core_dir}", file=sys.stderr)
        sys.exit(1)

    skill_files = find_skill_files(neos_core_dir)
    if not skill_files:
        print(f"No SKILL.md files found in: {neos_core_dir}", file=sys.stderr)
        sys.exit(1)

    skills = collect_skill_data(skill_files)

    if args.format == "markdown":
        report = generate_markdown_report(skills)
    else:
        report = generate_text_report(skills)

    print(report)
    sys.exit(0)


if __name__ == "__main__":
    main()
