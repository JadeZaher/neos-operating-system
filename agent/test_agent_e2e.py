"""End-to-end test harness for the NEOS agent AI provider.

Tests the LiteLLM integration without the full Sanic server.
Requires a valid AI_API_KEY in the environment.
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback
from pathlib import Path

# Add src to path so this can be run from the agent directory
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))


def test_imports():
    """Test that the agent modules can be imported."""
    print("[TEST] Importing neos_agent modules...")
    try:
        from neos_agent.config import get_settings
        from neos_agent.ai.provider import acompletion, is_ai_enabled
        print("  ✅ Core module imports succeeded")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_litellm_import():
    """Test that litellm can be imported without errors."""
    print("[TEST] Importing litellm...")
    try:
        import litellm
        from importlib.metadata import version as pkg_version
        try:
            version = pkg_version("litellm")
        except Exception:
            version = "unknown"
        print(f"  ✅ litellm version: {version}")
        return True
    except Exception as e:
        print(f"  ❌ litellm import failed: {e}")
        traceback.print_exc()
        return False


def test_ai_enabled():
    """Test AI enabled check."""
    print("[TEST] Checking is_ai_enabled()...")
    try:
        from neos_agent.ai.provider import is_ai_enabled
        enabled = is_ai_enabled()
        print(f"  ✅ AI enabled: {enabled}")
        return enabled
    except Exception as e:
        print(f"  ❌ is_ai_enabled() failed: {e}")
        traceback.print_exc()
        return False


async def test_completion():
    """Test a simple AI completion."""
    print("[TEST] Testing acompletion()...")
    try:
        from neos_agent.ai.provider import acompletion

        result = await acompletion(
            messages=[{"role": "user", "content": "Say 'NEOS agent OK' in three words."}],
            model="openrouter/quasar-alpha",
            max_tokens=20,
            temperature=0.0,
        )

        if result is None:
            print("  ⚠️  acompletion returned None (AI disabled or no API key)")
            return False

        content = result.get("content", "")
        print(f"  ✅ Completion succeeded")
        print(f"     Model: {result.get('model')}")
        print(f"     Response: {content[:200]}")
        print(f"     Usage: {result.get('usage')}")
        return True
    except Exception as e:
        print(f"  ❌ Completion failed: {e}")
        traceback.print_exc()
        return False


def show_env():
    """Show relevant settings without exposing secrets."""
    from neos_agent.config import get_settings
    settings = get_settings()
    print("[INFO] Settings:")
    print(f"  AI_API_KEY length: {len(settings.AI_API_KEY)}")
    print(f"  AI key configured: {bool(settings.AI_API_KEY)}")
    print(f"  AI_MODEL: {settings.AI_MODEL}")
    print(f"  AI_BASE_URL: {settings.AI_BASE_URL}")
    print(f"  AI_PROVIDER: {settings.AI_PROVIDER}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("NEOS Agent End-to-End Test Harness")
    print("=" * 60)

    show_env()

    results = []
    results.append(("imports", test_imports()))
    results.append(("litellm_import", test_litellm_import()))
    results.append(("ai_enabled", test_ai_enabled()))
    results.append(("completion", await test_completion()))

    print("=" * 60)
    print("Results:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    print("=" * 60)

    all_passed = all(passed for _, passed in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())
