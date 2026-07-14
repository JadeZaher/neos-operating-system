"""Tests for the human-in-the-loop (HITL) parser and utilities."""

from __future__ import annotations

import pytest

from neos_agent.agent.hitl import (
    parse_approval_request,
    format_approval_request_block,
    format_approval_response,
)


def test_parse_valid_approval_request():
    text = (
        "Which type of agreement should we create?\n\n"
        "```json\n"
        '{"type": "approval_request", "question": "Agreement type?", '
        '"options": ["Space", "Access", "Organizational"], "allow_other": true}\n'
        "```"
    )
    cleaned, request = parse_approval_request(text)

    assert request is not None
    assert request["question"] == "Agreement type?"
    assert request["options"] == ["Space", "Access", "Organizational"]
    assert request["allow_other"] is True
    assert "```json" not in cleaned
    assert "Agreement type?" not in cleaned


def test_parse_approval_request_without_allow_other():
    text = (
        "Please choose:\n\n"
        "```json\n"
        '{"type": "approval_request", "question": "Continue?", '
        '"options": ["Yes", "No"]}\n'
        "```"
    )
    cleaned, request = parse_approval_request(text)

    assert request is not None
    assert request["question"] == "Continue?"
    assert request["options"] == ["Yes", "No"]
    assert request["allow_other"] is True  # default


def test_parse_returns_original_text_when_no_block():
    text = "This is a normal assistant message."
    cleaned, request = parse_approval_request(text)

    assert request is None
    assert cleaned == text


def test_parse_returns_original_text_for_malformed_json():
    text = (
        "Question?\n\n"
        "```json\n"
        "{not valid json\n"
        "```"
    )
    cleaned, request = parse_approval_request(text)

    assert request is None
    assert cleaned == text


def test_parse_returns_original_text_when_type_missing():
    text = (
        "```json\n"
        '{"question": "What?", "options": ["A", "B"]}\n'
        "```"
    )
    cleaned, request = parse_approval_request(text)

    assert request is None
    assert "```json" in cleaned


def test_parse_requires_at_least_two_options():
    text = (
        "```json\n"
        '{"type": "approval_request", "question": "What?", "options": ["Only"]}\n'
        "```"
    )
    cleaned, request = parse_approval_request(text)

    assert request is None
    assert "```json" in cleaned


def test_format_approval_request_block():
    block = format_approval_request_block(
        question="Pick one",
        options=["A", "B"],
        allow_other=False,
    )
    cleaned, request = parse_approval_request(block)

    assert request is not None
    assert request["question"] == "Pick one"
    assert request["options"] == ["A", "B"]
    assert request["allow_other"] is False


def test_format_approval_response_selection():
    assert format_approval_response("A") == "A"


def test_format_approval_response_other():
    assert format_approval_response("Other", "my custom text") == "Other: my custom text"


@pytest.mark.asyncio
async def test_request_human_input_tool():
    from neos_agent.agent.governance_tools import execute_tool

    result = await execute_tool(
        "request_human_input",
        {
            "question": "Which agreement?",
            "options": ["Space", "Access"],
            "allow_other": True,
        },
        db_session=None,
    )

    assert result["success"] is True
    data = result["data"]
    assert data["requires_input"] is True
    assert data["question"] == "Which agreement?"
    assert data["options"] == ["Space", "Access"]
    assert data["allow_other"] is True
    assert "input_id" in data


@pytest.mark.asyncio
async def test_request_human_input_tool_requires_two_options():
    from neos_agent.agent.governance_tools import execute_tool

    result = await execute_tool(
        "request_human_input",
        {"question": "Which?", "options": ["One"]},
        db_session=None,
    )

    assert result["success"] is False
    assert "two" in result["error"].lower()
