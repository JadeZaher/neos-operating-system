"""Disabled accounts cannot establish sessions through any interactive credential family."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from neos_agent.db.models import AuthChallenge, AuthSession, User
from neos_agent.api.auth import _hash_password as hash_password
from .test_oauth import FAKE_GOOGLE_USER, _bound_callback, _cookie_header, _create_app, _setup_db


@pytest.mark.parametrize("method", ["password", "did", "google", "linkedin"])
async def test_disabled_user_cannot_create_auth_session(method):
    engine, factory = await _setup_db()
    app = _create_app(factory)
    did = "did:key:zDisabledFixture"
    async with factory() as session:
        session.add(User(username="disabled-fixture", password_hash=hash_password("fixture-password-123"), display_name="Disabled fixture",
            did=did, oauth_provider=method if method in {"google", "linkedin"} else None,
            oauth_id=str(FAKE_GOOGLE_USER["id"]) if method in {"google", "linkedin"} else None, disabled_at=datetime.now()))
        session.add(AuthChallenge(did=did, challenge="fixture-challenge", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)))
        await session.commit()
    try:
        if method == "password":
            _, response = await app.asgi_client.post("/api/v1/auth/login", json={"username": "disabled-fixture", "password": "fixture-password-123"})
            assert response.status == 401
        elif method == "did":
            with patch("neos_agent.api.auth.verify_did_signature", return_value=True):
                _, response = await app.asgi_client.post("/api/v1/auth/verify", json={"did": did, "challenge": "fixture-challenge", "signature": "00"})
            assert response.status == 403
        else:
            callback, cookies = _bound_callback(method, code="offline-fixture-code")
            with patch(f"neos_agent.api.oauth._exchange_{method}_code", new=AsyncMock(return_value=FAKE_GOOGLE_USER)):
                _, response = await app.asgi_client.get(callback, cookies=cookies, follow_redirects=False)
            assert response.status == 302 and "account_unavailable" in response.headers["location"]
        assert not _cookie_header(response, "neos_session")
        async with factory() as session:
            assert await session.scalar(select(func.count()).select_from(AuthSession)) == 0
    finally:
        await engine.dispose()
