"""Subprocess sandbox — asyncio subprocess with timeout, temp dir, env stripping.

This is the ONLY module that touches the OS.  It is designed to be the
single point of audit for all process-spawning and resource-limit logic.

Linux: resource.setrlimit for RLIMIT_AS (virtual memory) and RLIMIT_CPU
       are applied AFTER fork, BEFORE exec — limits apply to the child
       process only.

Windows: resource.setrlimit is unavailable.  The sandbox relies on
         asyncio timeout + SIGTERM/SIGKILL as the only resource guard.
         This is a documented v1 gap — see SECURITY.md.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import ExecPolicy

logger = logging.getLogger(__name__)

# Linux-only resource module
try:
    import resource as _resource  # pylint: disable=E0401
    _HAS_RESOURCE = True
    _RLIMIT_AS = _resource.RLIMIT_AS
    _RLIMIT_CPU = _resource.RLIMIT_CPU
except ImportError:
    _HAS_RESOURCE = False
    _RLIMIT_AS = 9  # placeholder
    _RLIMIT_CPU = 0  # placeholder


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimal safe environment variables passed through by default.
_MINIMAL_ENV: set[str] = {
    "PATH",
    "HOME",
    "TEMP",
    "TMP",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "SYSTEMROOT",    # Windows
    "PYTHONPATH",    # Needed for Python subprocesses to find packages
    "VIRTUAL_ENV",   # Needed for venv support
}

# Grace period between SIGTERM and SIGKILL (seconds)
_TERM_GRACE_SEC = 2.0


# ---------------------------------------------------------------------------
# Environment stripping
# ---------------------------------------------------------------------------


def build_subprocess_env(policy_env_allowlist: set[str] | None) -> dict[str, str]:
    """Build a sanitized environment dict for the subprocess.

    Parameters
    ----------
    policy_env_allowlist
        Explicit set of uppercase env var names to pass through.
        ``None`` → use ``_MINIMAL_ENV``.
        ``set()`` → fully stripped (only PATH).

    Returns
    -------
    dict[str, str]
        Sanitized env dict.
    """
    allow = policy_env_allowlist if policy_env_allowlist is not None else _MINIMAL_ENV

    env: dict[str, str] = {}
    for key in allow:
        val = os.environ.get(key)
        if val is not None:
            env[key] = val

    # Always ensure PATH is present
    if "PATH" not in env:
        env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")

    if not _HAS_RESOURCE:
        # On Windows, pass SYSTEMROOT if available
        if "SYSTEMROOT" not in env and "SYSTEMROOT" in os.environ:
            env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]

    return env


# ---------------------------------------------------------------------------
# Interpreter resolution
# ---------------------------------------------------------------------------


def _resolve_interpreter(language: str) -> tuple[str, list[str]]:
    """Return ``(executable, base_args)`` for *language*.

    Python uses ``sys.executable`` (the current interpreter, which
    preserves venv context).  JavaScript uses ``node`` from PATH.
    """
    if language == "python":
        return sys.executable, []
    elif language in ("javascript", "js", "node"):
        return "node", []
    else:
        raise ValueError(f"Unsupported language: {language}")


def _source_extension(language: str) -> str:
    """Return ``.py`` or ``.js`` for *language*."""
    return ".py" if language == "python" else ".js"


# ---------------------------------------------------------------------------
# Core execution
# ---------------------------------------------------------------------------


async def run_script(
    language: str,
    source: str,
    args: list[str],
    timeout_sec: float,
    policy: "ExecPolicy",
) -> "ExecResult":
    """Execute *source* as a subprocess and return structured results.

    This is the sole entry point for sandboxed execution.  All policy
    checks MUST be completed by the caller (via ``policy.py``) before
    invoking this function.

    Parameters
    ----------
    language
        ``"python"`` or ``"javascript"``.
    source
        The complete script source text.
    args
        Positional arguments to pass on the command line.
    timeout_sec
        Wall-clock timeout in seconds for the subprocess.
    policy
        The ExecPolicy (used for memory/CPU limits and truncation).

    Returns
    -------
    ExecResult
        Structured execution result.
    """
    from .schemas import ExecResult  # local to avoid circular import
    from .policy import check_output_size  # truncation

    start = time.perf_counter()
    tmp_dir: Path | None = None
    tmp_file: Path | None = None
    stdout_str = ""
    stderr_str = ""

    try:
        # ---- 1. Create temp directory ----
        tmp_dir = _create_temp_dir()

        # ---- 2. Write source to temp file ----
        ext = _source_extension(language)
        tmp_file = tmp_dir / f"script{ext}"
        tmp_file.write_text(source, encoding="utf-8")

        # ---- 3. Resolve interpreter ----
        exe, base_args = _resolve_interpreter(language)
        full_args = [exe, *base_args, str(tmp_file), *args]

        # ---- 4. Build sanitized env ----
        env = build_subprocess_env(policy.env_allowlist)

        logger.debug(
            "Executing: %s  cwd=%s  timeout=%.1fs  env_keys=%s",
            " ".join(full_args),
            str(tmp_dir),
            timeout_sec,
            sorted(env.keys()),
        )

        # ---- 5. Define preexec_fn for Linux resource limits ----
        if _HAS_RESOURCE and (policy.max_memory_mb > 0 or policy.max_cpu_sec > 0):

            def set_limits() -> None:
                """Apply resource limits in the child process."""
                if policy.max_memory_mb > 0:
                    _resource.setrlimit(
                        _RLIMIT_AS,  # type: ignore[arg-type]
                        (policy.max_memory_mb * 1024 * 1024,),  # type: ignore
                    )
                if policy.max_cpu_sec > 0:
                    _resource.setrlimit(
                        _RLIMIT_CPU,  # type: ignore[arg-type]
                        (int(policy.max_cpu_sec) + 1,),  # type: ignore
                    )
        else:
            set_limits = None

        # ---- 6. Spawn subprocess ----
        proc = await asyncio.create_subprocess_exec(
            *full_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(tmp_dir),
            env=env,
            preexec_fn=set_limits,
        )

        # ---- 7. Wait with timeout ----
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_sec,
            )
            kill = False
        except asyncio.TimeoutError:
            kill = True
            logger.warning("Subprocess timed out after %.1fs, killing", timeout_sec)

            # Graceful shutdown: SIGTERM first, then wait, then SIGKILL
            try:
                proc.terminate()
                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=_TERM_GRACE_SEC,
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    stdout_bytes, stderr_bytes = await proc.communicate()
            except ProcessLookupError:
                stdout_bytes, stderr_bytes = b"", b"[process already exited]".encode()

        # ---- 8. Decode output ----
        stdout_str = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr_str = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

        # ---- 9. Truncate output ----
        stdout_str, stderr_str, truncated = check_output_size(
            stdout_str, stderr_str, policy
        )

        exit_code = proc.returncode

        duration_ms = (time.perf_counter() - start) * 1000.0

        return ExecResult(
            ok=(exit_code == 0 and not kill),
            exit_code=exit_code,
            stdout=stdout_str,
            stderr=stderr_str,
            truncated=truncated,
            duration_ms=duration_ms,
            killed_by_timeout=kill,
        )

    except FileNotFoundError as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return ExecResult(
            ok=False,
            exit_code=None,
            stderr=f"Interpreter not found: {e}",
            duration_ms=duration_ms,
            policy_violation=f"Interpreter '{exe if 'exe' in dir() else language}' not found on PATH",
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        logger.exception("Sandbox execution failed")
        return ExecResult(
            ok=False,
            exit_code=None,
            stderr=f"Sandbox error: {type(e).__name__}: {e}",
            duration_ms=duration_ms,
            policy_violation=str(e),
        )

    finally:
        # ---- 10. Cleanup temp directory ----
        _cleanup_temp_dir(tmp_dir)


# ---------------------------------------------------------------------------
# Temp directory helpers
# ---------------------------------------------------------------------------


def _create_temp_dir() -> Path:
    """Create a unique temporary directory for this execution.

    Returns a ``Path`` inside the system temp dir, prefixed ``neos_exec_``.
    """
    tmp = Path(tempfile.mkdtemp(prefix="neos_exec_"))
    # Restrict permissions on POSIX
    if os.name == "posix":
        tmp.chmod(0o700)
    return tmp


def _cleanup_temp_dir(tmp_dir: Path | None) -> None:
    """Best-effort cleanup of *tmp_dir* and its contents."""
    if tmp_dir is None or not tmp_dir.exists():
        return

    # Remove files first
    for child in tmp_dir.iterdir():
        try:
            child.unlink(missing_ok=True)
        except OSError:
            pass

    # Remove directory
    try:
        tmp_dir.rmdir()
    except OSError:
        pass


__all__ = [
    "run_script",
    "build_subprocess_env",
]
