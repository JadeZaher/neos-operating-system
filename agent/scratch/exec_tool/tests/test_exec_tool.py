"""Tests for exec_script — the sandboxed async entry point.

Run from the scratch directory::

    cd .../agent/scratch
    python -m pytest exec_tool/tests/test_exec_tool.py -v
"""

from __future__ import annotations

import os
import shutil
import textwrap

import pytest

from exec_tool.exec_tool import exec_script
from exec_tool.schemas import ExecPolicy, ScriptLanguage
from exec_tool.policy import PolicyViolation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NODE_AVAILABLE = shutil.which("node") is not None

# ---------------------------------------------------------------------------
# 1. Happy-path: Python
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_python(default_policy):
    """A trivial Python script prints a greeting and exits 0."""
    result = await exec_script(
        language="python",
        source='print("hello from exec_script")',
        policy=default_policy,
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert "hello from exec_script" in result.stdout
    assert result.stderr == "" or result.stderr is not None
    assert result.truncated is False
    assert result.killed_by_timeout is False
    assert result.policy_violation is None
    assert result.duration_ms > 0


@pytest.mark.asyncio
async def test_happy_python_with_args(default_policy):
    """A Python script reads command-line arguments."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import sys, json
            data = {"args": sys.argv[1:], "sum": sum(map(int, sys.argv[1:]))}
            print(json.dumps(data))
        """),
        args=["3", "5", "7"],
        allowed_imports={"python": {"sys"}},
        policy=default_policy,
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert '"sum": 15' in result.stdout
    assert '"args": ["3", "5", "7"]' in result.stdout


@pytest.mark.asyncio
async def test_happy_python_stdout_stderr(default_policy):
    """A script that writes to both stdout and stderr."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import sys
            print("out1")
            print("out2", file=sys.stderr)
            print("out3")
        """),
        allowed_imports={"python": {"sys"}},
        policy=default_policy,
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert "out1" in result.stdout
    assert "out3" in result.stdout
    assert "out2" in result.stderr


# ---------------------------------------------------------------------------
# 2. Happy-path: Node.js
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skipif(not _NODE_AVAILABLE, reason="node not on PATH")
async def test_happy_node(permissive_policy):
    """A trivial JavaScript script prints a greeting and exits 0."""
    result = await exec_script(
        language="javascript",
        source='console.log("hello from node");',
        policy=permissive_policy,
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert "hello from node" in result.stdout


@pytest.mark.asyncio
@pytest.mark.skipif(not _NODE_AVAILABLE, reason="node not on PATH")
async def test_happy_node_with_args(permissive_policy):
    """A JS script that reads process.argv."""
    result = await exec_script(
        language="javascript",
        source=(
            "const args = process.argv.slice(2);"
            "console.log(JSON.stringify({args, sum: args.reduce((a,b) => a+ +b, 0)}));"
        ),
        args=["2", "4", "6"],
        policy=permissive_policy,
    )
    assert result.ok is True
    assert result.exit_code == 0
    assert "12" in result.stdout


@pytest.mark.asyncio
@pytest.mark.skipif(not _NODE_AVAILABLE, reason="node not on PATH")
async def test_happy_node_exit_nonzero(permissive_policy):
    """A JS script that exits with code 1."""
    result = await exec_script(
        language="javascript",
        source="process.exit(1);",
        policy=permissive_policy,
    )
    assert result.ok is False
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# 3. Timeout enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_kills_process(short_timeout_policy):
    """A script that sleeps longer than the policy timeout is killed."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import time
            time.sleep(10)
            print("should not see this")
        """),
        # Request a 500 ms timeout, which is under the 1 s policy max
        timeout_ms=500,
        policy=short_timeout_policy,
    )
    assert result.ok is False
    assert result.killed_by_timeout is True
    assert "should not see this" not in result.stdout


@pytest.mark.asyncio
async def test_timeout_request_exceeds_policy(short_timeout_policy):
    """Requesting a timeout above the policy cap is denied."""
    result = await exec_script(
        language="python",
        source="print('hello')",
        timeout_ms=5_000,  # 5 s > 1 s policy cap
        policy=short_timeout_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "timeout" in result.policy_violation.lower()


# ---------------------------------------------------------------------------
# 4. Output truncation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_output_truncation(tiny_output_policy):
    """Output exceeding the 512-byte limit is truncated with a marker."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import json
            # ~2 KB of output — well over the 512 B policy cap
            payload = {"key": "x" * 2000}
            print(json.dumps(payload))
        """),
        policy=tiny_output_policy,
    )
    assert result.truncated is True
    assert "[TRUNCATED" in result.stdout
    # The original output was ~2 KB; truncated+budget is ≤ 512 bytes
    assert len(result.stdout.encode()) <= 600  # small fudge for the marker


@pytest.mark.asyncio
async def test_output_under_limit_not_truncated(tiny_output_policy):
    """Output within the limit is not truncated."""
    result = await exec_script(
        language="python",
        source='print("short")',
        policy=tiny_output_policy,
    )
    assert result.ok is True
    assert result.truncated is False


# ---------------------------------------------------------------------------
# 5. Blocked imports
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blocked_import_os(default_policy):
    """Importing 'os' is blocked by the default policy."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import os
            print(os.getcwd())
        """),
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "os" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_blocked_import_socket(default_policy):
    """Importing 'socket' is blocked by the default policy."""
    result = await exec_script(
        language="python",
        source="import socket\nprint('never')",
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "socket" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_blocked_import_from_os(default_policy):
    """'from os import getcwd' is also blocked."""
    result = await exec_script(
        language="python",
        source="from os import getcwd\nprint(getcwd())",
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "os" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_blocked_import_subprocess(default_policy):
    """Importing 'subprocess' is blocked by the default policy."""
    result = await exec_script(
        language="python",
        source="import subprocess\nsubprocess.run(['echo','hi'])",
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "subprocess" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_blocked_builtin_import(default_policy):
    """Using __import__() is detected and blocked."""
    result = await exec_script(
        language="python",
        source='json = __import__("json")\nprint(json.dumps({"a":1}))',
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "__import__" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_allowed_imports_override(default_policy):
    """Passing allowed_imports lets a blocked import through."""
    result = await exec_script(
        language="python",
        source='import time\nprint("epoch:", time.time())',
        allowed_imports={"python": {"time"}},
        policy=default_policy,
    )
    assert result.ok is True
    assert "epoch:" in result.stdout


# ---------------------------------------------------------------------------
# 6. Policy denial — forbidden language
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_policy_denial_unknown_language():
    """Passing an unrecognised language string returns ok=False."""
    result = await exec_script(
        language="ruby",
        source="puts 'hello'",
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "ruby" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_policy_denial_javascript_disabled_by_default():
    """Default policy blocks JavaScript execution."""
    result = await exec_script(
        language="javascript",
        source='console.log("hello");',
        # default policy — Python only
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "javascript" in result.policy_violation.lower()


@pytest.mark.asyncio
async def test_policy_denial_no_imports_allowed():
    """A policy with an empty import dict blocks all imports."""
    strict_policy = ExecPolicy(
        allowed_languages={ScriptLanguage.python},
        allowed_imports={},  # empty — nothing allowed
        max_timeout_sec=10.0,
        max_output_bytes=65_536,
    )
    result = await exec_script(
        language="python",
        source='import json\nprint(json.dumps({"a":1}))',
        policy=strict_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "json" in result.policy_violation.lower()


# ---------------------------------------------------------------------------
# 7. Oversized output and source rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_oversized_output_combined_stdout_stderr(tiny_output_policy):
    """Truncation triggers when stdout + stderr exceed the budget."""
    result = await exec_script(
        language="python",
        source=textwrap.dedent("""\
            import sys, json
            payload = {"data": "x" * 1500}
            dumped = json.dumps(payload)
            print(dumped)
            print("stderr spam", file=sys.stderr)
        """),
        policy=tiny_output_policy,
    )
    assert result.truncated is True
    assert "[TRUNCATED" in result.stdout or "[TRUNCATED" in result.stderr


@pytest.mark.asyncio
async def test_source_size_hard_limit():
    """Source code over 1 MiB triggers a policy violation."""
    big_source = "# " + "x" * 1_050_000  # > 1 MiB
    result = await exec_script(
        language="python",
        source=big_source,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    assert "MiB" in result.policy_violation or "size" in result.policy_violation.lower()


# ---------------------------------------------------------------------------
# 8. Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_args_list(default_policy):
    """Empty args list is handled gracefully."""
    result = await exec_script(
        language="python",
        source='print("ok")',
        args=[],
        policy=default_policy,
    )
    assert result.ok is True


@pytest.mark.asyncio
async def test_script_syntax_error(default_policy):
    """A Python script with a syntax error returns non-zero exit code."""
    result = await exec_script(
        language="python",
        source="print(   \n  # missing close paren",
        policy=default_policy,
    )
    assert result.ok is False
    # exit_code is non-zero on syntax error
    if result.exit_code is not None:
        assert result.exit_code != 0
    assert "SyntaxError" in result.stderr or result.exit_code == 1


@pytest.mark.asyncio
async def test_script_runtime_exception(default_policy):
    """A script that raises an unhandled exception exits non-zero."""
    result = await exec_script(
        language="python",
        source='raise ValueError("test error")',
        policy=default_policy,
    )
    assert result.ok is False
    assert result.exit_code != 0
    assert "ValueError" in result.stderr or "test error" in result.stderr


@pytest.mark.asyncio
async def test_duration_ms_positive(default_policy):
    """Every execution records a positive wall-clock duration."""
    result = await exec_script(
        language="python",
        source="print('hello')",
        policy=default_policy,
    )
    assert result.duration_ms > 0


@pytest.mark.asyncio
async def test_exec_result_is_serializable(default_policy):
    """ExecResult can be dumped to a JSON-safe dict."""
    result = await exec_script(
        language="python",
        source="print('hello')",
        policy=default_policy,
    )
    d = result.model_dump()
    assert isinstance(d, dict)
    assert "ok" in d
    assert "exit_code" in d
    assert "stdout" in d
    assert "stderr" in d
    assert "duration_ms" in d


# ---------------------------------------------------------------------------
# 9. exec()/eval() bypass prevention and env-stripping verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blocked_exec_builtin(default_policy):
    """A script using exec() to import os is rejected by policy."""
    result = await exec_script(
        language="python",
        source='exec("import os; print(os.getcwd())")',
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    msg = result.policy_violation.lower()
    assert "exec" in msg or "eval" in msg or "__import__" in msg


@pytest.mark.asyncio
async def test_blocked_eval_builtin(default_policy):
    """A script using eval() to invoke __import__ is rejected by policy."""
    result = await exec_script(
        language="python",
        source="eval(\"__import__('os').getcwd()\")",
        policy=default_policy,
    )
    assert result.ok is False
    assert result.policy_violation is not None
    msg = result.policy_violation.lower()
    assert "exec" in msg or "eval" in msg or "__import__" in msg


@pytest.mark.asyncio
async def test_pythonpath_stripped_from_env(default_policy):
    """The subprocess does not receive PYTHONPATH even when set in the host env."""
    # Inject a recognisable value into the current process environment so
    # that, if sandbox.py were to pass PYTHONPATH through, the child would
    # see it.
    sentinel = "/tmp/attacker_controlled_path_sentinel"
    original = os.environ.get("PYTHONPATH")
    os.environ["PYTHONPATH"] = sentinel
    try:
        result = await exec_script(
            language="python",
            source=textwrap.dedent("""\
                import os, json
                pp = os.environ.get("PYTHONPATH")
                print(json.dumps({"PYTHONPATH": pp}))
            """),
            # Allow os for the subprocess so we can inspect its env;
            # the point is that PYTHONPATH from the HOST is not passed through.
            allowed_imports={"python": {"os", "json"}},
            policy=default_policy,
        )
    finally:
        # Restore original env state regardless of test outcome
        if original is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = original

    assert result.ok is True
    assert sentinel not in result.stdout
    # The subprocess should report PYTHONPATH as absent (null in JSON)
    assert '"PYTHONPATH": null' in result.stdout
