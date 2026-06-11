"""exec_script — async entry point that wires policy + sandbox + schemas.

This is the single public API for script execution.  It:

1. Normalises the language enum (accepts str or ScriptLanguage).
2. Resolves the effective policy (default or caller-supplied), merging
   any per-call ``allowed_imports`` override.
3. Runs all pre-execution policy gates via
   :func:`policy.enforce_all_policy_gates`.
4. Delegates to :func:`sandbox.run_script` for the actual subprocess.
5. Returns a structured :class:`ExecResult`.

Design invariants
-----------------
- **Never** spawns a subprocess before policy gates pass.
- Every :class:`PolicyViolation` is caught and returned as an
  ``ok=False`` :class:`ExecResult` — never propagated as an exception
  to the caller.
- The *allowed_imports* parameter is a per-call safety valve: it can
  *widen* the import allowlist but never *narrow* it below the policy
  floor (the policy is the floor, the override is additive).
"""

from __future__ import annotations

import logging
from typing import Any

from .schemas import (
    ExecPolicy,
    ExecResult,
    ScriptLanguage,
    apply_default_policy,
)
from .policy import (
    PolicyViolation,
    enforce_all_policy_gates,
)
from .sandbox import run_script

logger = logging.getLogger(__name__)


async def exec_script(
    language: str | ScriptLanguage,
    source: str,
    args: list[str] | None = None,
    timeout_ms: float | None = None,
    allowed_imports: dict[str, set[str]] | None = None,
    *,
    policy: ExecPolicy | None = None,
) -> ExecResult:
    """Execute a script in a sandboxed subprocess.

    This is the **only** entry point callers should use.  It enforces
    every policy gate before touching the OS and converts all failures
    into structured :class:`ExecResult` values.

    Parameters
    ----------
    language
        ``"python"`` or ``"javascript"`` (or the enum directly).
    source
        Complete script source text — not a filename.
    args
        Positional arguments passed on the command line after the
        temporary script path.  Defaults to empty.
    timeout_ms
        Optional wall-clock timeout in milliseconds.  Capped by the
        policy's ``max_timeout_sec``.  If ``None``, the policy maximum
        is used.
    allowed_imports
        Per-call import allowlist **override**.  When a dict is
        provided the keys are ``ScriptLanguage`` values (``"python"`` /
        ``"javascript"``) and the values are :class:`set` of module
        prefixes.  The override is **merged** with the policy's
        existing allowlist (union) — it can only widen, never narrow.
        Use this to grant temporary access to ``json`` or ``math`` when
        the default policy is fully locked down.
    policy
        :class:`ExecPolicy` to use.  Defaults to
        :data:`schemas.DEFAULT_POLICY` — a maximally conservative
        policy (Python only, safe stdlib imports, 10 s timeout, 64 KiB
        output, 512 MiB memory, 5 s CPU on Linux).

    Returns
    -------
    ExecResult
        Always returns a structured result — never raises.
    """
    # ---- 1. Normalise language -------------------------------------------
    if isinstance(language, str):
        try:
            language = ScriptLanguage(language)
        except ValueError:
            return ExecResult(
                ok=False,
                policy_violation=(
                    f"Unknown language: '{language}'. "
                    f"Supported: {[l.value for l in ScriptLanguage]}"
                ),
            )

    # ---- 2. Resolve policy -----------------------------------------------
    effective_policy = apply_default_policy(policy)

    # ---- 3. Merge allowed_imports override (additive only) ----------------
    if allowed_imports is not None:
        merged = dict(effective_policy.allowed_imports)
        for lang_key, mods in allowed_imports.items():
            existing = merged.get(lang_key, set())
            merged[lang_key] = existing | mods
        effective_policy = effective_policy.model_copy(
            update={"allowed_imports": merged}
        )

    # ---- 4. Run pre-execution policy gates --------------------------------
    try:
        effective_timeout = enforce_all_policy_gates(
            language=language,
            source=source,
            timeout_ms=timeout_ms,
            policy=effective_policy,
        )
    except PolicyViolation as e:
        logger.info("Policy gate blocked execution: %s", e)
        return ExecResult(
            ok=False,
            policy_violation=str(e),
        )

    # ---- 5. Execute in sandbox -------------------------------------------
    return await run_script(
        language=language.value,
        source=source,
        args=args or [],
        timeout_sec=effective_timeout,
        policy=effective_policy,
    )


__all__ = ["exec_script"]
