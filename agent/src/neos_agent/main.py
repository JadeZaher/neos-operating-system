"""Sanic application factory with lifecycle hooks.

Creates a Sanic app that loads the skill registry and initializes
the database on startup, and cleans up on shutdown.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

import uuid

from sanic import Sanic
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select

if TYPE_CHECKING:
    from neos_agent.config import Settings

logger = logging.getLogger(__name__)


def create_app(settings: "Settings | None" = None) -> Sanic:
    """Create and configure the NEOS Agent Sanic application.

    Args:
        settings: Optional Settings instance. If None, loads from environment.

    Returns:
        Configured Sanic application.
    """
    app = Sanic("neos-agent")

    # Load settings — when invoked via ``sanic --factory``, Sanic passes its
    # own argparse.Namespace as the first argument, so we need to check the type.
    from neos_agent.config import Settings, get_settings
    if not isinstance(settings, Settings):
        settings = get_settings()

    app.ctx.settings = settings

    # Configure CORS — sanic-ext reads app.config.CORS_ORIGINS automatically.
    app.config.CORS_ORIGINS = settings.CORS_ORIGINS

    # Configure logging
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Register lifecycle hooks
    @app.before_server_start
    async def load_skills(app, loop):
        """Load skill registry at startup."""
        from neos_agent.skills.registry import SkillRegistry

        registry = SkillRegistry()
        try:
            neos_path = Path(settings.NEOS_CORE_PATH).resolve()
            await registry.load_all(neos_path)
            logger.info("Loaded %d skills from %s", registry.count, neos_path)
        except Exception as e:
            logger.error("Failed to load skills: %s (running in degraded mode)", e)

        app.ctx.skills = registry

    @app.before_server_start
    async def init_db(app, loop):
        """Initialize database connection and ensure a default ecosystem exists."""
        try:
            from neos_agent.db.session import setup_db
            await setup_db(app, loop)
            logger.info("Database initialized")
        except Exception as e:
            logger.error("Failed to initialize database: %s", e)
            app.ctx.db = None
            app.ctx.db_engine = None
            return

        # Ensure a default OmniOne ecosystem exists
        try:
            from sqlalchemy import select
            from neos_agent.db.models import Ecosystem

            async with app.ctx.db() as session:
                result = await session.execute(
                    select(Ecosystem).limit(1)
                )
                if result.scalar_one_or_none() is None:
                    import uuid
                    ecosystem = Ecosystem(
                        id=uuid.uuid4(),
                        name="OmniOne",
                        description="First NEOS ecosystem, stewarded by Green Earth Vision",
                        status="active",
                    )
                    session.add(ecosystem)
                    await session.commit()
                    logger.info("Created default OmniOne ecosystem")
        except Exception as e:
            logger.warning("Could not ensure default ecosystem: %s", e)

    @app.after_server_stop
    async def close_db(app, loop):
        """Clean up database connections."""
        try:
            from neos_agent.db.session import teardown_db
            await teardown_db(app, loop)
        except Exception as e:
            logger.warning("Error during database cleanup: %s", e)

    # Register API blueprints
    from neos_agent.api.health import health_bp
    from neos_agent.api.skills import skills_bp

    app.blueprint(health_bp)
    app.blueprint(skills_bp)

    # Register dashboard view blueprints
    from neos_agent.views import register_views
    register_views(app)

    # Register ecosystem directory blueprint (public + auth routes)
    from neos_agent.views.ecosystems import ecosystems_bp
    app.blueprint(ecosystems_bp)

    # Register chat blueprint
    from neos_agent.views.chat import chat_bp
    app.blueprint(chat_bp)

    # Register auth blueprint
    from neos_agent.auth.routes import auth_bp
    app.blueprint(auth_bp)

    # Auth middleware — protect all non-public routes
    @app.on_request
    async def auth_middleware(request: Request):
        from neos_agent.auth.middleware import is_public_route, verify_session_cookie
        from neos_agent.db.models import AuthSession, Ecosystem, Member as MemberModel

        # Helper: parse selected ecosystem IDs from cookie
        def _parse_selected_cookie() -> list[uuid.UUID]:
            raw = request.cookies.get("neos_selected_ecosystems")
            if not raw:
                return []
            try:
                ids = json.loads(unquote(raw))
                if not isinstance(ids, list):
                    return []
                return [uuid.UUID(i) for i in ids[:10]]  # cap at 10
            except (json.JSONDecodeError, ValueError):
                return []

        # Helper: load ecosystem objects for given IDs (or member default)
        async def _load_ecosystems(db, member, selected_ids):
            if selected_ids:
                if member:
                    # Verify membership: keep only ecosystems where this member's DID
                    # has an active Member record, plus always include their own ecosystem.
                    member_result = await db.execute(
                        select(MemberModel.ecosystem_id).where(
                            MemberModel.did == member.did,
                            MemberModel.ecosystem_id.in_(selected_ids),
                            MemberModel.current_status == "active",
                        )
                    )
                    authorized_eco_ids = set(member_result.scalars().all())
                    # Always include the member's own ecosystem
                    authorized_eco_ids.add(member.ecosystem_id)
                    # Filter selected to only authorized
                    selected_ids = [eid for eid in selected_ids if eid in authorized_eco_ids]

                result = await db.execute(
                    select(Ecosystem).where(Ecosystem.id.in_(selected_ids))
                )
                ecosystems = list(result.scalars().all())
                eco_ids = [e.id for e in ecosystems]
                return ecosystems, eco_ids
            # Fallback: member's own ecosystem
            if member:
                eco = await db.get(Ecosystem, member.ecosystem_id)
                if eco:
                    return [eco], [eco.id]
            return [], []

        # Helper: resolve member from session cookie
        async def _try_resolve_member():
            cookie = request.cookies.get("neos_session")
            if not cookie:
                return None
            sid = verify_session_cookie(cookie, settings.SESSION_SECRET)
            if not sid:
                return None
            try:
                async with app.ctx.db() as db:
                    from datetime import datetime
                    result = await db.execute(
                        select(AuthSession).where(
                            AuthSession.id == uuid.UUID(sid),
                            AuthSession.expires_at > datetime.utcnow(),
                        )
                    )
                    auth_session = result.scalar_one_or_none()
                    if auth_session:
                        return await db.get(MemberModel, auth_session.member_id)
                    return None
            except Exception:
                logger.debug("Session resolve failed on public route")
            return None

        if is_public_route(request.path):
            # Still resolve session so logged-in users see personalized UI
            member = await _try_resolve_member()
            request.ctx.member = member
            selected_ids = _parse_selected_cookie()
            try:
                async with app.ctx.db() as db:
                    ecosystems, eco_ids = await _load_ecosystems(db, member, selected_ids)
            except Exception:
                ecosystems, eco_ids = [], []
            request.ctx.ecosystems = ecosystems
            request.ctx.selected_ecosystem_ids = eco_ids
            return None

        cookie = request.cookies.get("neos_session")
        if not cookie:
            return redirect("/auth/login")

        session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
        if not session_id:
            return redirect("/auth/login")

        try:
            async with app.ctx.db() as db:
                from datetime import datetime
                result = await db.execute(
                    select(AuthSession).where(
                        AuthSession.id == uuid.UUID(session_id),
                        AuthSession.expires_at > datetime.utcnow(),
                    )
                )
                auth_session = result.scalar_one_or_none()
                if not auth_session:
                    response = redirect("/auth/login")
                    response.delete_cookie("neos_session", path="/")
                    return response

                member = await db.get(MemberModel, auth_session.member_id)
                request.ctx.member = member

                # Load selected ecosystems from cookie (or fallback to member's)
                selected_ids = _parse_selected_cookie()
                ecosystems, eco_ids = await _load_ecosystems(db, member, selected_ids)
                request.ctx.ecosystems = ecosystems
                request.ctx.selected_ecosystem_ids = eco_ids
        except Exception:
            logger.exception("Auth middleware error")
            return redirect("/auth/login")

        return None

    # Root redirect
    @app.get("/")
    async def root(request: Request):
        if hasattr(request.ctx, "member") and request.ctx.member:
            return redirect("/dashboard")
        return redirect("/auth/login")

    # Catch-all: redirect unknown paths to the dashboard
    @app.exception(Exception)
    async def catch_all(request, exception):
        from sanic.exceptions import NotFound
        if isinstance(exception, NotFound):
            return redirect("/dashboard")
        raise exception

    return app


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="NEOS Agent")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--dev", action="store_true", help="Enable debug + auto-reload")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--single-process", action="store_true", help="Run in single process")
    args = parser.parse_args()

    # On Windows, Sanic's multiprocess reloader can't resolve the factory,
    # so we fall back to single_process + debug (no auto-reload).
    single = args.single_process or (args.dev and sys.platform == "win32")

    app = create_app()
    if single:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.dev,
            single_process=True,
        )
    else:
        app.run(
            host=args.host,
            port=args.port,
            dev=args.dev,
            workers=args.workers,
        )
