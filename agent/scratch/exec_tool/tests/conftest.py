"""Shared fixtures and configuration for exec_tool tests."""

import pytest

from exec_tool.schemas import (
    ExecPolicy,
    ScriptLanguage,
    DEFAULT_POLICY,
)


@pytest.fixture
def default_policy() -> ExecPolicy:
    """The restrictive default policy: Python only, safe stdlib, 10 s."""
    return DEFAULT_POLICY.model_copy(deep=True)


@pytest.fixture
def permissive_policy() -> ExecPolicy:
    """A fully-open policy for testing JS and import-heavy scripts."""
    return ExecPolicy(
        allowed_languages={ScriptLanguage.python, ScriptLanguage.javascript},
        allowed_imports={
            "python": {
                "json", "math", "csv", "re", "datetime", "collections",
                "itertools", "functools", "pathlib", "typing", "textwrap",
                "string", "decimal", "fractions", "statistics", "random",
                "uuid", "hashlib", "base64", "binascii", "copy", "pprint",
                "enum", "dataclasses", "operator", "html", "codecs", "io",
                "gzip", "zipfile", "tarfile", "calendar", "zoneinfo",
                "logging", "time", "os",
            },
            "javascript": set(),
        },
        max_timeout_sec=15.0,
        max_output_bytes=65_536,
        max_memory_mb=512,
        max_cpu_sec=10.0,
    )


@pytest.fixture
def tiny_output_policy() -> ExecPolicy:
    """Policy with very small output limit (512 bytes) for truncation tests."""
    return ExecPolicy(
        allowed_languages={ScriptLanguage.python},
        allowed_imports={"python": {"json", "time", "sys"}},
        max_timeout_sec=10.0,
        max_output_bytes=512,
        max_memory_mb=512,
        max_cpu_sec=5.0,
    )


@pytest.fixture
def short_timeout_policy() -> ExecPolicy:
    """Policy with a 1-second timeout for timeout-enforcement tests."""
    return ExecPolicy(
        allowed_languages={ScriptLanguage.python},
        allowed_imports={"python": {"time"}},
        max_timeout_sec=1.0,
        max_output_bytes=65_536,
        max_memory_mb=512,
        max_cpu_sec=2.0,
    )
