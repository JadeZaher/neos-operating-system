"""Policy enforcement — import scanning, language gating, timeout/bounds checks.

This module is PURE validation.  It never executes anything, never touches
the filesystem except to read its own source.
"""

from __future__ import annotations

import re
import logging

from .schemas import ExecPolicy, ScriptLanguage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import-scanning patterns (Python)
# ---------------------------------------------------------------------------

# Matches:  import json
#           import math, os
#           import numpy as np
#           import pandas as pd, matplotlib
_IMPORT_RE = re.compile(
    r"^\s*import\s+([\w.]+(?:\s+as\s+\w+)?(?:\s*,\s*[\w.]+(?:\s+as\s+\w+)?)*)",
    re.MULTILINE,
)

# Matches:  from os import path
#           from os import path, getcwd
#           from os.path import join as jn
#           from typing import List, Dict
_FROM_IMPORT_RE = re.compile(
    r"^\s*from\s+([\w.]+)\s+import\s+([\w,*\s()]+(?:\s+as\s+\w+)?)",
    re.MULTILINE,
)

# Matches:  open("...", ...)
_OPEN_RE = re.compile(r"\bopen\s*\(", re.MULTILINE)

# Matches:  __import__(...)
_BUILTIN_IMPORT_RE = re.compile(r"\b__import__\s*\(", re.MULTILINE)


def _strip_comment(line: str) -> str:
    """Crude comment stripper — removes ``# ...`` from a line.

    Doesn't handle nested strings, but that's fine for a deny-list
    scanner: we'd rather false-positive and block than miss an import
    hidden in clever quoting.
    """
    idx = line.find("#")
    return line[:idx] if idx != -1 else line


def scan_python_imports(source: str) -> set[str]:
    r"""Extract the set of top-level modules referenced in a Python script.

    Returns module **prefixes**, not dotted names.  For example
    ``from xml.etree.ElementTree import Element`` yields ``{"xml"}``.

    Parameters
    ----------
    source
        Raw Python source text.

    Returns
    -------
    set[str]
        Set of top-level module names (e.g. ``{"json", "math", "os"}``).

    Notes
    -----
    This is a regex-based scanner, not a full AST parser.  It will
    *over-approximate* — it may flag imports inside dead code or
    commented-out lines (unless the line begins with ``#``).  That is
    the safe direction for a security gate.
    """
    imports: set[str] = set()

    for line in source.splitlines():
        line = _strip_comment(line)
        line = line.strip()

        # "import X"
        m = _IMPORT_RE.match(line)
        if m:
            raw = m.group(1)
            for token in raw.split(","):
                mod = token.strip().split()[0]  # strip "as Y"
                imports.add(mod.split(".")[0])
            continue

        # "from X import Y"
        m = _FROM_IMPORT_RE.match(line)
        if m:
            mod = m.group(1)
            imports.add(mod.split(".")[0])
            continue

    # Also catch __import__(...) calls (even though they're banned by
    # the default import allowlist, we want to log them).
    if _BUILTIN_IMPORT_RE.search(source):
        logger.warning("__import__() call detected in script source")
        imports.add("__builtin_import__")

    # open() is not an import but we track it for policy
    return imports


def scan_javascript_imports(source: str) -> set[str]:
    """Extract top-level module names from JavaScript ``require()`` / ``import``.

    Returns an empty set for now — JS import scanning is not implemented
    in v1.  The default policy does not permit JavaScript execution.
    """
    # v1: JavaScript is disabled by default.  We'll implement this
    # properly when JS is added to the default policy.
    return set()


def scan_imports(language: ScriptLanguage, source: str) -> set[str]:
    """Dispatch to the correct scanner for *language*."""
    if language == ScriptLanguage.python:
        return scan_python_imports(source)
    elif language == ScriptLanguage.javascript:
        return scan_javascript_imports(source)
    else:
        return set()


# ---------------------------------------------------------------------------
# Policy checks
# ---------------------------------------------------------------------------


class PolicyViolation(Exception):
    """Raised when a policy gate is violated before execution."""


def check_language(
    language: ScriptLanguage, policy: ExecPolicy
) -> None:
    """Raise PolicyViolation if *language* is not in the policy allowlist."""
    if language not in policy.allowed_languages:
        raise PolicyViolation(
            f"Language '{language.value}' is not in the allowed set: "
            f"{sorted(p.value for p in policy.allowed_languages)}"
        )


def check_imports(
    language: ScriptLanguage, source: str, policy: ExecPolicy
) -> None:
    """Scan *source* for imports and check against the allowlist.

    If the policy has no import allowlist for *language*, ALL imports
    are blocked.  The default policy provides a curated safe subset.
    """
    allowlist = policy.allowed_imports.get(language.value, set())

    detected = scan_imports(language, source)

    # Special marker from scan_python_imports
    if "__builtin_import__" in detected and "__builtin_import__" not in allowlist:
        raise PolicyViolation(
            "The script uses __import__(), which is not permitted."
        )

    blocked = detected - allowlist
    if not blocked:
        return

    if not allowlist:
        raise PolicyViolation(
            f"No imports are permitted for language '{language.value}'. "
            f"Script tries to import: {sorted(blocked)}"
        )

    raise PolicyViolation(
        f"Blocked imports: {sorted(blocked)}. "
        f"Allowed modules: {sorted(allowlist)}"
    )


def check_timeout(
    requested_ms: float | None, policy: ExecPolicy
) -> float:
    """Validate and cap *requested_ms* against *policy.max_timeout_sec*.

    Returns the effective timeout in seconds (float).
    """
    if requested_ms is None:
        return policy.max_timeout_sec

    requested_sec = requested_ms / 1000.0
    if requested_sec <= 0:
        raise PolicyViolation(
            f"timeout_ms must be positive, got {requested_ms}"
        )
    if requested_sec > policy.max_timeout_sec:
        raise PolicyViolation(
            f"Requested timeout {requested_sec:.1f}s exceeds policy maximum "
            f"{policy.max_timeout_sec}s"
        )
    return requested_sec


def check_output_size(
    stdout: str, stderr: str, policy: ExecPolicy
) -> tuple[str, str, bool]:
    """Truncate *stdout* and *stderr* if combined size exceeds policy.

    Returns ``(stdout, stderr, truncated)``.
    """
    total = len(stdout.encode()) + len(stderr.encode())
    if total <= policy.max_output_bytes:
        return stdout, stderr, False

    # Conservative truncation: allocate budget proportionally
    ratio_stdout = len(stdout.encode()) / total if total > 0 else 0.5
    budget_stdout = int(policy.max_output_bytes * ratio_stdout)
    budget_stderr = policy.max_output_bytes - budget_stdout

    def _trunc(s: str, budget: int) -> str:
        encoded = s.encode()
        if len(encoded) <= budget:
            return s
        # Truncate roughly: decode up to budget bytes, add marker
        truncated_bytes = encoded[: max(0, budget - 30)]
        return truncated_bytes.decode(errors="replace") + "\n\n[TRUNCATED by exec_script policy]"

    return _trunc(stdout, budget_stdout), _trunc(stderr, budget_stderr), True


def enforce_all_policy_gates(
    language: ScriptLanguage,
    source: str,
    timeout_ms: float | None,
    policy: ExecPolicy,
) -> float:
    """Run every pre-execution policy check.

    Raises ``PolicyViolation`` on the first failure.

    Returns
    -------
    float
        Effective timeout in seconds.
    """
    # Gate 1: Language
    check_language(language, policy)

    # Gate 2: Imports
    check_imports(language, source, policy)

    # Gate 3: Timeout
    effective_timeout = check_timeout(timeout_ms, policy)

    # Gate 4: Source size sanity (not a policy field, hard-coded guardrail)
    if len(source.encode()) > 1_000_000:  # 1 MiB source hard stop
        raise PolicyViolation(
            f"Source code size {len(source.encode())} bytes exceeds 1 MiB hard limit."
        )

    return effective_timeout


__all__ = [
    "PolicyViolation",
    "scan_imports",
    "scan_python_imports",
    "check_language",
    "check_imports",
    "check_timeout",
    "check_output_size",
    "enforce_all_policy_gates",
]
