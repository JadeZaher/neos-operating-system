"""End-to-end tests for the NEOS agent service.

Spins up the actual Sanic service in-process, hits real HTTP endpoints,
and uses a judge LLM on the same configured model (low-token mode) to
check response quality.

Run from the agent/ directory:
    ..\.venv\Scripts\python.exe test_agent_service_e2e.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# --- Environment configuration before any agent imports ---
# Set a fixed session secret so cookie signing is deterministic.
os.environ.setdefault("SESSION_SECRET", "test-secret-0123456789abcdef")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("LOG_LEVEL", "error")
# Use a temp dir for NEOS_CORE_PATH so skill loading is fast and harmless.
_neos_core = tempfile.mkdtemp(prefix="neos_core_")
os.environ.setdefault("NEOS_CORE_PATH", _neos_core)
# Use a temp-file SQLite database so data persists across separate server runs.
_db_fd, _db_path = tempfile.mkstemp(prefix="neos_test_", suffix=".db")
os.close(_db_fd)
_db_url = f"sqlite+aiosqlite:///{Path(_db_path).as_posix()}"
os.environ.setdefault("DATABASE_URL", _db_url)

# OpenRouter-only e2e harness. The OPENROUTER_KEY and model can be overridden via env.
os.environ.setdefault("AI_PROVIDER", "openrouter")
os.environ.setdefault("AI_MODEL", "openrouter/qwen/qwen3-30b-a3b-instruct-2507")
os.environ.setdefault("AI_BASE_URL", "https://openrouter.ai/api/v1")

# Import after environment is configured.
from neos_agent.config import get_settings
from neos_agent.main import create_app
from neos_agent.ai.provider import acompletion
from sanic_testing import TestManager


def parse_sse(text: str) -> list[tuple[str, str]]:
    """Parse a raw SSE response body into (event, data) tuples."""
    events = []
    for block in text.split("\n\n"):
        lines = block.splitlines()
        event = "message"
        data_lines = []
        for line in lines:
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: "):
                data_lines.append(line[6:])
        if data_lines:
            events.append((event, "\n".join(data_lines)))
    return events


def collect_assistant_text(events: list[tuple[str, str]]) -> str:
    """Concatenate assistant 'append' events from an SSE stream."""
    parts = []
    for event, data in events:
        if event == "append":
            parts.append(data)
    return "\n".join(parts)


def collect_tool_calls(events: list[tuple[str, str]]) -> list[tuple[str, dict]]:
    """Extract tool call and result information from SSE events."""
    tools = []
    pending: dict[str, str] = {}
    for event, data in events:
        if event == "tool_start":
            try:
                obj = json.loads(data)
                pending[obj["name"]] = obj.get("args", {})
            except Exception:
                pass
        elif event == "tool_result":
            try:
                obj = json.loads(data)
                tools.append((obj["name"], obj))
            except Exception:
                pass
    return tools


async def judge_response(
    user_message: str, response_text: str, model: str, tool_results: list | None = None
) -> dict:
    """Use the same LLM to judge the agent response quality (low-token)."""
    tool_context = ""
    if tool_results:
        tool_context = (
            "\nTool(s) used by the agent and their returned data:\n"
            + json.dumps(tool_results, default=str, indent=2)[:1500]
            + "\n"
        )
    prompt = (
        "You are a strict response judge. The agent may use tools to look up data. "
        "If the response is based on tool data, it must be consistent with that data.\n"
        "User question: " + user_message + "\n"
        "Agent response: " + response_text + "\n"
        + tool_context
        + "Does the agent response directly and accurately answer the question? "
        "Output only one of: PASS or FAIL, then a one-sentence reason."
    )
    result = await acompletion(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=64,
        temperature=0.0,
    )
    if not result:
        return {"pass": False, "reason": "AI not configured (AI_API_KEY not set)"}
    content = result.get("content", "").strip()
    passed = content.upper().startswith("PASS")
    return {"pass": passed, "reason": content, "model": model}


def run_tests() -> list[dict]:
    """Run the e2e test suite."""
    settings = get_settings()
    model = settings.AI_MODEL

    app = create_app(settings=settings)
    TestManager(app)
    client = app.test_client

    results = []

    # ------------------------------------------------------------------
    # 1. Health check
    # ------------------------------------------------------------------
    print("[TEST] GET /")
    _, resp = client.get("/")
    if resp.status == 200 and resp.json.get("status") == "ok":
        print("  ✅ Health check passed")
        results.append({"name": "health", "status": "PASS", "elapsed": 0})
    else:
        print(f"  ❌ Health check failed: {resp.status} {resp.text}")
        results.append({"name": "health", "status": "FAIL", "error": resp.text})
        return results

    # ------------------------------------------------------------------
    # 2. Register a test user (public route)
    # ------------------------------------------------------------------
    print("[TEST] POST /api/v1/auth/register")
    _, resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "password": "testpass123",
            "display_name": "Test User",
        },
    )
    if resp.status != 200:
        print(f"  ❌ Register failed: {resp.status} {resp.text}")
        results.append({"name": "register", "status": "FAIL", "error": resp.text})
        return results

    print("  ✅ Registered test user")
    session_cookie = resp.cookies.get("neos_session")
    if not session_cookie:
        # Fallback: parse the Set-Cookie header if httpx didn't keep the cookie
        set_cookie = resp.headers.get("set-cookie", "")
        for part in set_cookie.split(";"):
            stripped = part.strip()
            if stripped.startswith("neos_session="):
                session_cookie = stripped.split("=", 1)[1]
                break
    if not session_cookie:
        print("  ❌ No session cookie returned")
        results.append({"name": "register", "status": "FAIL", "error": "No cookie"})
        return results

    # ------------------------------------------------------------------
    # 3. Auth /me
    # ------------------------------------------------------------------
    print("[TEST] GET /api/v1/auth/me")
    _, resp = client.get(
        "/api/v1/auth/me",
        cookies={"neos_session": session_cookie},
    )
    if resp.status == 200 and resp.json.get("member"):
        print("  ✅ /auth/me returned member")
        results.append({"name": "auth_me", "status": "PASS", "elapsed": 0})
    else:
        print(f"  ❌ /auth/me failed: {resp.status} {resp.text}")
        results.append({"name": "auth_me", "status": "FAIL", "error": resp.text})

    # ------------------------------------------------------------------
    # 4. Chat test with judge
    # ------------------------------------------------------------------
    user_message = "List the active members of OmniOne"
    print(f"[TEST] POST /api/v1/chat/send: {user_message!r}")
    start = time.perf_counter()
    _, resp = client.post(
        "/api/v1/chat/send",
        json={
            "message": user_message,
            "page_context": {"path": "/members"},
        },
        cookies={"neos_session": session_cookie},
        timeout=90,
    )
    elapsed = time.perf_counter() - start

    if resp.status != 200:
        print(f"  ❌ Chat failed: {resp.status} {resp.text}")
        results.append({"name": "chat", "status": "FAIL", "error": resp.text, "elapsed": elapsed})
        return results

    events = parse_sse(resp.text)
    response_text = collect_assistant_text(events)
    tool_calls = collect_tool_calls(events)
    print(f"  ✅ Chat returned in {elapsed:.2f}s")
    print(f"     Tools used: {[name for name, _ in tool_calls]}")
    print(f"     Assistant text ({len(response_text)} chars):")
    print(response_text[:500])

    if not response_text:
        print("  ❌ No assistant text in SSE stream")
        results.append({"name": "chat", "status": "FAIL", "error": "Empty response", "elapsed": elapsed})
        return results

    # Judge response quality using the same model in low-token mode.
    print("[TEST] Judge response (low-token mode)")
    judge = asyncio.run(
        judge_response(user_message, response_text, model, tool_calls)
    )
    print(f"  {'✅' if judge['pass'] else '❌'} Judge: {judge['reason']}")

    results.append({
        "name": "chat",
        "status": "PASS" if judge["pass"] else "FAIL",
        "elapsed": elapsed,
        "tools": [name for name, _ in tool_calls],
        "judge": judge,
    })

    return results


def main():
    print("=" * 70)
    print("NEOS Agent Service E2E Test Harness")
    print("=" * 70)
    print(f"DATABASE_URL: {os.environ['DATABASE_URL']}")
    print(f"AI_MODEL:     {os.environ.get('AI_MODEL')}")
    print(f"AI_BASE_URL:  {os.environ.get('AI_BASE_URL') or '(default)'}")
    print(f"AI key set:   {bool(get_settings().AI_API_KEY)}")
    print()

    try:
        results = run_tests()
    except Exception as e:
        print(f"\n❌ Test harness crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    passed = 0
    for r in results:
        status = r["status"]
        elapsed = r.get("elapsed", 0)
        print(f"  {status} {r['name']:20s} ({elapsed:.2f}s)")
        if status == "PASS":
            passed += 1
        else:
            print(f"       {r.get('error') or r.get('judge', {}).get('reason')}")

    print(f"\nPassed: {passed}/{len(results)}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
