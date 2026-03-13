"""Skill loader — parses SKILL.md files into structured dataclasses.

Reuses parsing patterns from scripts/validate_skill.py, adapted for
the agent webservice runtime.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SkillParseError(Exception):
    """Raised when a SKILL.md file cannot be parsed."""


@dataclass(frozen=True)
class SkillMeta:
    """Metadata from SKILL.md frontmatter."""
    name: str
    description: str
    layer: int
    version: str
    depends_on: list[str]
    file_path: str


@dataclass(frozen=True)
class SkillContent:
    """Parsed content from SKILL.md body."""
    sections: dict[str, str | None]  # Letter -> section text or None
    raw_text: str                     # Full file content


@dataclass(frozen=True)
class ParsedSkill:
    """Complete parsed skill with metadata and content."""
    meta: SkillMeta
    content: SkillContent


# 12 required sections
REQUIRED_SECTIONS: list[tuple[str, str]] = [
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

_SECTION_STOP_RE = re.compile(
    r"^#{1,3}\s+(?:[A-L][\.\:\)]|OmniOne|Stress)", re.IGNORECASE
)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], list[str]]:
    """Extract YAML frontmatter between --- delimiters.

    Returns (parsed_dict, errors). Errors list is non-empty only when
    the frontmatter block itself is absent or structurally broken.
    """
    lines = content.split("\n")
    delimiters: list[int] = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            delimiters.append(i)
            if len(delimiters) == 2:
                break

    if len(delimiters) < 2:
        return {}, ["Missing YAML frontmatter — no --- delimiters found"]

    fm_lines = lines[delimiters[0] + 1 : delimiters[1]]
    frontmatter: dict[str, Any] = {}

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
            frontmatter[key] = [
                item.strip().strip("\"'") for item in items if item.strip()
            ]
        else:
            frontmatter[key] = value

    return frontmatter, []


def parse_sections(content: str) -> dict[str, str | None]:
    """Extract all 12 sections (A through L) into a dict keyed by letter.

    Returns dict where value is the section text (without header line)
    or None if the section was not found.
    """
    lines = content.split("\n")
    sections: dict[str, str | None] = {}

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
            content_lines: list[str] = []
            for j in range(found_idx + 1, len(lines)):
                if _SECTION_STOP_RE.match(lines[j]):
                    break
                content_lines.append(lines[j])
            sections[letter] = "\n".join(content_lines)
        else:
            sections[letter] = None

    return sections


def parse_skill_file(file_path: Path) -> ParsedSkill:
    """Parse a SKILL.md file into a ParsedSkill.

    Raises SkillParseError if the file is missing, unreadable,
    or has invalid/incomplete frontmatter.
    """
    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        raise SkillParseError(f"Cannot read {file_path}: {e}") from e

    frontmatter, errors = parse_frontmatter(raw_text)
    if errors:
        raise SkillParseError(f"Invalid frontmatter in {file_path}: {'; '.join(errors)}")

    # Validate required fields
    required = ["name", "description", "layer", "version", "depends_on"]
    missing = [f for f in required if f not in frontmatter]
    if missing:
        raise SkillParseError(
            f"Missing required frontmatter fields in {file_path}: {', '.join(missing)}"
        )

    # Convert layer to int
    try:
        layer = int(frontmatter["layer"])
    except (ValueError, TypeError) as e:
        raise SkillParseError(
            f"Invalid layer value in {file_path}: {frontmatter['layer']!r}"
        ) from e

    # Ensure depends_on is a list
    depends_on = frontmatter["depends_on"]
    if not isinstance(depends_on, list):
        depends_on = []

    meta = SkillMeta(
        name=frontmatter["name"],
        description=frontmatter["description"],
        layer=layer,
        version=frontmatter["version"],
        depends_on=depends_on,
        file_path=str(file_path.resolve()),
    )

    sections = parse_sections(raw_text)
    content = SkillContent(sections=sections, raw_text=raw_text)

    return ParsedSkill(meta=meta, content=content)


def discover_skill_files(root: Path) -> list[Path]:
    """Walk root directory to find all SKILL.md files.

    Returns sorted list of absolute paths.
    """
    skill_files: list[Path] = []
    for path in root.rglob("SKILL.md"):
        skill_files.append(path.resolve())
    return sorted(skill_files)
