"""Decorator-based registration of exec_script into GOVERNANCE_TOOLS.

This module injects the ``exec_script`` tool into the NEOS agent's
``GOVERNANCE_TOOLS`` list **without modifying** ``governance_tools.py``.
It does so by importing the module-level list and appending a
:class:`ToolDef` at import time.

Usage (typically in an ``__init__.py`` or startup hook)::

    from exec_tool.registry import register_exec_tool
    from exec_tool.exec_tool import exec_script

    register_exec_tool(exec_script)

After registration the tool appears in:
- ``GOVERNANCE_TOOLS`` (list of ToolDef)
- ``_TOOL_HANDLERS`` (dispatch dict)
- ``get_tool_definitions()`` output
- ``execute_tool("exec_script", ...)`` dispatch

Double-registration is idempotent — the second call logs a warning
and returns without modifying the lists.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool parameter schema (JSON Schema for Claude API)
# ---------------------------------------------------------------------------

_EXEC_TOOL_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string",
            "enum": ["python", "javascript"],
            "description": (
                "Scripting language to execute. 'python' uses the same "
                "interpreter as the agent process. 'javascript' requires "
                "a 'node' binary on PATH."
            ),
        },
        "source": {
            "type": "string",
            "description": "Full source code of the script to execute.",
        },
        "args": {
            "type": "array",
            "items": {"type": "string"},
            "description": (
                "Positional arguments passed to the script on the command line."
            ),
        },
        "timeout_ms": {
            "type": "number",
            "description": (
                "Override the default timeout in milliseconds. "
                "Capped by the policy's max_timeout_sec (default 10 s)."
            ),
        },
        "allowed_imports": {
            "type": "object",
            "description": (
                "Per-language import allowlist override. Keys are language "
                "names ('python', 'javascript'), values are arrays of module "
                "prefixes. The override is merged with (never replaces) the "
                "policy allowlist. Example: "
                '{"python": ["json", "math"]}'
            ),
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
    "required": ["language", "source"],
}


# ---------------------------------------------------------------------------
# Handler builder
# ---------------------------------------------------------------------------


def _build_handler(exec_fn: Callable) -> Callable:
    """Wrap *exec_fn* so it conforms to the governance-tool signature.

    Governance tools expect::

        async def handler(args: dict, db: AsyncSession, ecosystem_ids=None) -> dict

    We adapt the :func:`exec_script` signature and convert the returned
    :class:`ExecResult` into the ``{"success": ..., "data": ...}`` dict
    format.
    """

    async def _handler(
        args: dict,
        db: Any = None,
        ecosystem_ids: list | None = None,
    ) -> dict:
        """Governance-tool handler wrapping exec_script."""
        try:
            result = await exec_fn(
                language=args.get("language", "python"),
                source=args["source"],
                args=args.get("args"),
                timeout_ms=args.get("timeout_ms"),
                allowed_imports=args.get("allowed_imports"),
            )
        except Exception:
            logger.exception("exec_script handler crashed")
            return {
                "success": False,
                "error": "exec_script internal error — see agent logs",
            }

        return {
            "success": result.ok,
            "data": result.model_dump(),
        }

    # Preserve metadata for introspection
    _handler.__name__ = "exec_script_handler"
    _handler.__doc__ = (
        "Governance-tool wrapper for exec_script.\n\n"
        "Delegates to :func:`exec_tool.exec_tool.exec_script`."
    )
    return _handler


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_exec_tool(exec_fn: Callable) -> None:
    """Register *exec_fn* as the ``exec_script`` governance tool.

    Appends a :class:`ToolDef` to ``GOVERNANCE_TOOLS`` and updates the
    ``_TOOL_HANDLERS`` dispatch dict.  Safe to call multiple times —
    subsequent calls are no-ops.

    Parameters
    ----------
    exec_fn
        The async function to register — typically
        :func:`exec_tool.exec_tool.exec_script`.
    """
    # Deferred imports so this module is importable even when
    # governance_tools is not on the path (e.g. during testing).
    from neos_agent.agent.governance_tools import GOVERNANCE_TOOLS, ToolDef

    # Access the private dispatch dict
    import neos_agent.agent.governance_tools as _gt

    # Idempotency guard
    existing_names = {t.name for t in GOVERNANCE_TOOLS}
    if "exec_script" in existing_names:
        logger.warning("exec_script already registered — skipping duplicate")
        return

    handler = _build_handler(exec_fn)

    tool_def = ToolDef(
        name="exec_script",
        description=(
            "Execute a Python or JavaScript script in a sandboxed subprocess. "
            "Scripts are subject to policy gates: language allowlisting, import "
            "scanning, timeout enforcement, and output truncation. Returns "
            "stdout, stderr, exit code, and wall-clock duration in milliseconds. "
            "The default policy permits only Python with safe stdlib imports "
            "(json, math, csv, re, datetime, collections, itertools, etc.) — "
            "no os, subprocess, socket, or network access."
        ),
        parameters=_EXEC_TOOL_PARAMETERS,
        handler=handler,
    )

    GOVERNANCE_TOOLS.append(tool_def)
    _gt._TOOL_HANDLERS["exec_script"] = handler  # type: ignore[attr-defined]

    logger.info(
        "exec_script registered in GOVERNANCE_TOOLS (now %d tools)",
        len(GOVERNANCE_TOOLS),
    )


__all__ = ["register_exec_tool"]
