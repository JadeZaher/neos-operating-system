"""Human-in-the-loop (HITL) protocol for the NEOS governance agent.

Provides parsing for structured approval-request blocks that the agent can emit
when it needs a choice, approval, or agreement-question answer from a user.
The frontend uses these blocks to render option buttons and an ``Other``
free-form text field.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Regex matching a Markdown JSON code block that contains an approval_request
_APPROVAL_REQUEST_BLOCK_RE = re.compile(
    r"```json\s*(\{.*?\"type\"\s*:\s*\"approval_request\".*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)

# Fallback: match any ```json block containing the approval_request type
_APPROVAL_REQUEST_FENCE_RE = re.compile(
    r"```json\s*\n(.*?)\n\s*```",
    re.DOTALL | re.IGNORECASE,
)


_ApprovalRequest = dict[str, Any]


def _is_approval_request(data: Any) -> bool:
    """Return True if *data* is a valid approval_request payload."""
    return (
        isinstance(data, dict)
        and data.get("type") == "approval_request"
        and isinstance(data.get("question"), str)
        and data.get("question").strip()
        and isinstance(data.get("options"), list)
        and len(data.get("options", [])) >= 2
        and all(isinstance(o, str) for o in data.get("options", []))
    )


def parse_approval_request(text: str) -> tuple[str, dict[str, Any] | None]:
    """Parse an ``approval_request`` JSON block from assistant text.

    The agent can embed a machine-readable block in a Markdown code fence:

    ```json
    {
      "type": "approval_request",
      "question": "What type of agreement should we create?",
      "options": ["Space agreement", "Access agreement", "Organizational agreement"],
      "allow_other": true
    }
    ```

    The returned text has the JSON block removed so the user never sees the raw
    markup. The returned payload contains the question, options, and the
    ``allow_other`` flag.

    Parameters
    ----------
    text:
        The assistant's raw message text.

    Returns
    -------
    tuple[str, dict | None]
        ``(cleaned_text, approval_request)``. The approval_request is ``None``
        when no valid block is found.
    """
    if not text or not isinstance(text, str):
        return text or "", None

    # First try the targeted regex.
    match = _APPROVAL_REQUEST_BLOCK_RE.search(text)
    if not match:
        # Fallback: scan every JSON fence for an approval_request payload.
        for candidate in _APPROVAL_REQUEST_FENCE_RE.finditer(text):
            try:
                data = json.loads(candidate.group(1))
            except json.JSONDecodeError:
                continue
            if _is_approval_request(data):
                match = candidate
                break

    if not match:
        return text, None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        logger.warning("Malformed approval_request JSON block: %s", exc)
        return text, None

    if not _is_approval_request(data):
        return text, None

    cleaned_text = (text[: match.start()] + text[match.end() :]).strip()
    # Collapse any double blank lines created by the removal.
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    approval_request = {
        "question": data["question"].strip(),
        "options": [str(o).strip() for o in data["options"]],
        "allow_other": bool(data.get("allow_other", True)),
    }

    return cleaned_text, approval_request


def format_approval_request_block(
    question: str,
    options: list[str],
    allow_other: bool = True,
) -> str:
    """Format an ``approval_request`` block for the agent to emit.

    Parameters
    ----------
    question:
        The human-readable question to display.
    options:
        List of concrete choices (2-6 recommended).
    allow_other:
        Whether the user may provide a free-form alternative.

    Returns
    -------
    str
        A Markdown JSON code block that ``parse_approval_request`` can read.
    """
    payload = {
        "type": "approval_request",
        "question": question.strip(),
        "options": [str(o).strip() for o in options],
        "allow_other": bool(allow_other),
    }
    return f"```json\n{json.dumps(payload, indent=2)}\n```"


def format_approval_response(selection: str, other_text: str | None = None) -> str:
    """Format a user response to an ``approval_request``.

    If ``other_text`` is provided, it is returned as the free-form ``Other``
    response. Otherwise, ``selection`` is returned as the user's answer.
    """
    if other_text:
        return f"Other: {other_text.strip()}"
    return selection.strip()
