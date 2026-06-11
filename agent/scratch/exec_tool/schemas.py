"""Pydantic input/output schemas for the NEOS exec_script tool.

These define the wire format for LLM-to-tool calls and tool-to-LLM
responses.  Every field carries a description usable as JSON Schema
tool parameter documentation.
"""

from __future__ import annotations

from datetime import timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Language enum
# ---------------------------------------------------------------------------


class ScriptLanguage(str, Enum):
    """Languages the exec_script tool can target.

    ``python`` is always available.  ``javascript`` (Node.js) requires
    a ``node`` binary on the host PATH.
    """

    python = "python"
    javascript = "javascript"


# ---------------------------------------------------------------------------
# ExecPolicy — restrictive defaults
# ---------------------------------------------------------------------------


class ExecPolicy(BaseModel):
    """Runtime policy controlling what scripts may run and how.

    The *default instance* below encodes a maximally-conservative policy
    suitable for a governance agent that must never execute arbitrary
    LLM-supplied code without an explicit, auditable gate.

    Field semantics
    ---------------
    allowed_languages
        Set of languages the tool will accept.  Default: Python only.
    allowed_imports
        Per-language allowlist of importable modules / packages.
        An empty dict means *no* imports are permitted (not even stdlib).
        The default for Python permits only safe stdlib modules that
        perform pure data transforms (no os, no subprocess, no socket).
    max_timeout_sec
        Wall-clock timeout in seconds for a single *exec_script* call.
        Default 10 s.  The tool enforces this with an asyncio timeout.
    max_output_bytes
        Upper bound on combined stdout + stderr captured.  Output beyond
        this limit is truncated with a ``truncated: true`` marker.
        Default 65_536 (64 KiB).
    max_memory_mb
        Virtual-memory limit in MiB enforced via ``RLIMIT_AS`` on Linux.
        Ignored on non-Linux hosts.  Default 512 MiB.
    max_cpu_sec
        CPU-time limit enforced via ``RLIMIT_CPU`` on Linux.  Default 5 s.
        Ignored on non-Linux hosts.
    env_allowlist
        Environment variables passed through to the subprocess, as a set
        of uppercase names.  If ``None``, the subprocess receives a minimal
        env with only ``PATH``, ``HOME``, ``TEMP``, ``TMP``, ``TMPDIR``,
        ``LANG``, and ``LC_ALL``.  Set to an explicit empty set ``set()``
        for a fully stripped environment.
        Default: ``None`` (minimal safe set).
    """

    allowed_languages: set[ScriptLanguage] = Field(
        default_factory=lambda: {ScriptLanguage.python},
        description="Languages the tool will accept for execution.",
    )
    allowed_imports: dict[str, set[str]] = Field(
        default_factory=dict,
        description=(
            "Per-language allowlist of importable modules. "
            "Empty dict = no imports permitted."
        ),
    )
    max_timeout_sec: float = Field(
        default=10.0,
        ge=0.1,
        le=300.0,
        description="Maximum wall-clock timeout in seconds.",
    )
    max_output_bytes: int = Field(
        default=65_536,
        ge=1,
        le=10 * 1024 * 1024,  # 10 MiB hard cap
        description="Maximum combined stdout+stderr in bytes.",
    )
    max_memory_mb: int = Field(
        default=512,
        ge=16,
        le=8192,
        description="Virtual-memory limit in MiB (Linux only).",
    )
    max_cpu_sec: float = Field(
        default=5.0,
        ge=1.0,
        le=300.0,
        description="CPU-time limit in seconds (Linux only).",
    )
    env_allowlist: set[str] | None = Field(
        default=None,
        description=(
            "Environment variables to pass through, or None for minimal safe set."
        ),
    )

    @model_validator(mode="after")
    def _validate_import_keys(self) -> ExecPolicy:
        """Ensure allowed_imports keys are known ScriptLanguage values."""
        valid = {lang.value for lang in ScriptLanguage}
        for lang in self.allowed_imports:
            if lang not in valid:
                raise ValueError(
                    f"allowed_imports key '{lang}' is not a known ScriptLanguage"
                )
        return self


# ---------------------------------------------------------------------------
# Default policy instance (restrictive)
# ---------------------------------------------------------------------------

# Safe Python stdlib modules for pure data transforms.
# Deliberately excludes: os, sys, subprocess, socket, shutil, http,
# urllib, pickle, ctypes, importlib, multiprocessing, threading, asyncio,
# signal, pty, pwd, grp, crypt, platform, gc, etc.
_DEFAULT_PYTHON_IMPORTS: set[str] = {
    "json",
    "csv",
    "re",
    "datetime",
    "math",
    "collections",
    "itertools",
    "functools",
    "pathlib",
    "typing",
    "textwrap",
    "string",
    "decimal",
    "fractions",
    "statistics",
    "random",
    "uuid",
    "hashlib",
    "base64",
    "binascii",
    "copy",
    "pprint",
    "enum",
    "dataclasses",
    "operator",
    "html",
    "xml.etree.ElementTree",
    "urllib.parse",
    "codecs",
    "io",
    "gzip",
    "zipfile",
    "tarfile",
    "calendar",
    "zoneinfo",
    "logging",
}

DEFAULT_POLICY = ExecPolicy(
    allowed_languages={ScriptLanguage.python},
    allowed_imports={"python": _DEFAULT_PYTHON_IMPORTS.copy()},
    max_timeout_sec=10.0,
    max_output_bytes=65_536,
    max_memory_mb=512,
    max_cpu_sec=5.0,
    env_allowlist=None,
)


# ---------------------------------------------------------------------------
# ExecRequest — what the LLM sends
# ---------------------------------------------------------------------------


class ExecRequest(BaseModel):
    """A single script-execution request from the agent.

    ``source`` is the **complete script text**, not a filename.
    The tool writes it to a temporary file and runs the appropriate
    interpreter.
    """

    language: ScriptLanguage = Field(
        ...,
        description="Scripting language: 'python' or 'javascript'.",
    )
    source: str = Field(
        ...,
        min_length=1,
        description="Full source code of the script to execute.",
    )
    args: list[str] = Field(
        default_factory=list,
        description="Positional arguments passed to the script on the command line.",
    )
    timeout_ms: float | None = Field(
        default=None,
        description=(
            "Override the default timeout in milliseconds. "
            "Capped by ExecPolicy.max_timeout_sec."
        ),
    )


# ---------------------------------------------------------------------------
# ExecResult — what the tool returns
# ---------------------------------------------------------------------------


class ExecResult(BaseModel):
    """Structured result from a script execution.

    Fields
    ------
    ok
        ``True`` iff the process exited with code 0 and no policy gate
        was violated.
    exit_code
        The raw process exit code, or ``None`` if the process was killed.
    stdout
        Captured stdout, possibly truncated.
    stderr
        Captured stderr, possibly truncated.
    truncated
        ``True`` when combined output exceeded ``max_output_bytes``.
    duration_ms
        Wall-clock duration of the execution in milliseconds.
    policy_violation
        When a policy check failed *before* execution, this carries the
        reason string.  ``None`` otherwise.
    killed_by_timeout
        ``True`` when ``max_timeout_sec`` was exceeded and the process
        was sent SIGKILL.
    """

    ok: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    duration_ms: float = 0.0
    policy_violation: str | None = None
    killed_by_timeout: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def apply_default_policy(policy: ExecPolicy | None) -> ExecPolicy:
    """Return *policy* or the restrictive default.

    This is the single-point-of-truth for defaulting, so that every
    code path that needs a policy can call it.
    """
    return policy if policy is not None else DEFAULT_POLICY
