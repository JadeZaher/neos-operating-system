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
from sanic.response import json as json_response, redirect
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
    # Credentials cannot be used with wildcard origins per the CORS spec.
    app.config.CORS_SUPPORTS_CREDENTIALS = settings.CORS_ORIGINS != "*"
    app.config.CORS_ALLOW_HEADERS = "content-type,authorization,x-requested-with"
    app.config.CORS_ALLOW_METHODS = "GET,POST,PUT,DELETE,PATCH,OPTIONS"

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
            import neos_agent.db.course_models  # noqa: F401 — register course/quiz tables
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
    from neos_agent.api.auth import auth_api_bp
    from neos_agent.api.ecosystems import ecosystems_api_bp
    from neos_agent.api.dashboard import dashboard_api_bp
    from neos_agent.api.agreements import agreements_api_bp
    from neos_agent.api.proposals import proposals_api_bp
    from neos_agent.api.members import members_api_bp
    from neos_agent.api.domains import domains_api_bp
    from neos_agent.api.decisions import decisions_api_bp
    from neos_agent.api.onboarding import onboarding_api_bp
    from neos_agent.api.conflicts import conflicts_api_bp
    from neos_agent.api.messaging import messaging_api_bp
    from neos_agent.api.courses import courses_api_bp
    from neos_agent.api.quizzes import quizzes_api_bp
    from neos_agent.api.chat import chat_api_bp
    from neos_agent.api.emergency import emergency_api_bp
    from neos_agent.api.exit import exit_api_bp
    from neos_agent.api.safeguards import safeguards_api_bp
    from neos_agent.api.discover import discover_api_bp
    from neos_agent.api.ai_assist import ai_assist_bp
    from neos_agent.api.compliance import compliance_api_bp
    from neos_agent.api.notifications import notifications_api_bp
    from neos_agent.api.oauth import oauth_bp
    from neos_agent.api.orientation import orientation_api_bp

    app.blueprint(health_bp)
    app.blueprint(skills_bp)
    app.blueprint(auth_api_bp)
    app.blueprint(ecosystems_api_bp)
    app.blueprint(dashboard_api_bp)
    app.blueprint(agreements_api_bp)
    app.blueprint(proposals_api_bp)
    app.blueprint(members_api_bp)
    app.blueprint(domains_api_bp)
    app.blueprint(decisions_api_bp)
    app.blueprint(onboarding_api_bp)
    app.blueprint(conflicts_api_bp)
    app.blueprint(messaging_api_bp)
    app.blueprint(courses_api_bp)
    app.blueprint(quizzes_api_bp)
    app.blueprint(chat_api_bp)
    app.blueprint(emergency_api_bp)
    app.blueprint(exit_api_bp)
    app.blueprint(safeguards_api_bp)
    app.blueprint(discover_api_bp)
    app.blueprint(ai_assist_bp)
    app.blueprint(compliance_api_bp)
    app.blueprint(notifications_api_bp)
    app.blueprint(oauth_bp)
    app.blueprint(orientation_api_bp)

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

    # Register messaging blueprint (WebSocket + REST)
    from neos_agent.messaging.routes import messaging_bp
    app.blueprint(messaging_bp)

    # Start background cron service
    @app.after_server_start
    async def start_cron(app, loop):
        """Start the background cron loop for governance deadlines."""
        import asyncio
        from neos_agent.services.cron import run_cron_loop
        app.ctx.cron_task = asyncio.create_task(run_cron_loop(app))
        logger.info("Cron service started")

    @app.before_server_stop
    async def stop_cron(app, loop):
        """Cancel the background cron loop."""
        cron_task = getattr(app.ctx, "cron_task", None)
        if cron_task and not cron_task.done():
            cron_task.cancel()
            logger.info("Cron service stopped")

    # Auth middleware — protect all non-public routes
    @app.on_request
    async def auth_middleware(request: Request):
        from neos_agent.auth.middleware import is_public_route, verify_session_cookie
        from neos_agent.db.models import AuthSession, Ecosystem, Member as MemberModel, User as UserModel
        from neos_agent.auth.ecosystem_scope import EcosystemScope

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

        # Helper: load ecosystem objects for given IDs (or user default)
        # Returns (selected_ecosystems, selected_ids, all_authorized_ids)
        async def _load_ecosystems(db, user, selected_ids):
            # First, determine ALL ecosystems the user is authorized for
            all_authorized_ids = set()
            primary_eco_id = None
            if user:
                member_result = await db.execute(
                    select(MemberModel.ecosystem_id).where(
                        MemberModel.user_id == user.id,
                        MemberModel.current_status == "active",
                    )
                )
                all_authorized_ids = set(member_result.scalars().all())
                if all_authorized_ids:
                    primary_eco_id = next(iter(all_authorized_ids))

            if selected_ids:
                # Filter selected_ids to only authorized ones
                if user:
                    selected_ids = [eid for eid in selected_ids if eid in all_authorized_ids]

                result = await db.execute(
                    select(Ecosystem).where(Ecosystem.id.in_(selected_ids))
                )
                ecosystems = list(result.scalars().all())
                eco_ids = [e.id for e in ecosystems]
                return ecosystems, eco_ids, list(all_authorized_ids)
            if primary_eco_id:
                eco = await db.get(Ecosystem, primary_eco_id)
                if eco:
                    return [eco], [eco.id], list(all_authorized_ids)
            return [], [], list(all_authorized_ids)

        # Helper: resolve user from session cookie
        async def _try_resolve_user():
            cookie = request.cookies.get("neos_session")
            if not cookie:
                return None
            sid = verify_session_cookie(cookie, settings.SESSION_SECRET)
            if not sid:
                return None
            try:
                async with app.ctx.db() as db:
                    from datetime import datetime, timezone
                    result = await db.execute(
                        select(AuthSession).where(
                            AuthSession.id == uuid.UUID(sid),
                            AuthSession.expires_at > datetime.now(timezone.utc),
                        )
                    )
                    auth_session = result.scalar_one_or_none()
                    if auth_session:
                        return await db.get(UserModel, auth_session.user_id)
                    return None
            except Exception:
                logger.debug("Session resolve failed on public route")
            return None

        # CORS preflight requests (OPTIONS) never carry cookies — let them through
        if request.method == "OPTIONS":
            return None

        if is_public_route(request.path):
            user = await _try_resolve_user()
            request.ctx.user = user
            selected_ids = _parse_selected_cookie()
            try:
                async with app.ctx.db() as db:
                    ecosystems, eco_ids, all_auth_ids = await _load_ecosystems(db, user, selected_ids)
                    # Load primary member for backward compat
                    if user:
                        member_result = await db.execute(
                            select(MemberModel).where(MemberModel.user_id == user.id).limit(1)
                        )
                        request.ctx.member = member_result.scalar_one_or_none()
                    else:
                        request.ctx.member = None
            except Exception:
                ecosystems, eco_ids, all_auth_ids = [], [], []
                request.ctx.member = None
                request.ctx.ecosystem_scope = EcosystemScope.empty()
            request.ctx.ecosystems = ecosystems
            request.ctx.selected_ecosystem_ids = eco_ids
            request.ctx.authorized_ecosystem_ids = all_auth_ids
            request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems(ecosystems, eco_ids)
            return None

        def _unauth(delete_cookie: bool = False):
            """Return 401 JSON for API routes; redirect browsers to login."""
            if request.path.startswith("/api/"):
                resp = json_response({"error": "Unauthorized"}, status=401)
                if delete_cookie:
                    resp.delete_cookie("neos_session", path="/")
                return resp
            resp = redirect("/auth/login")
            if delete_cookie:
                resp.delete_cookie("neos_session", path="/")
            return resp

        cookie = request.cookies.get("neos_session")
        if not cookie:
            return _unauth()

        session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
        if not session_id:
            return _unauth(delete_cookie=True)

        try:
            async with app.ctx.db() as db:
                from datetime import datetime, timezone
                result = await db.execute(
                    select(AuthSession).where(
                        AuthSession.id == uuid.UUID(session_id),
                        AuthSession.expires_at > datetime.now(timezone.utc),
                    )
                )
                auth_session = result.scalar_one_or_none()
                if not auth_session:
                    return _unauth(delete_cookie=True)

                user = await db.get(UserModel, auth_session.user_id)
                request.ctx.user = user

                selected_ids = _parse_selected_cookie()
                ecosystems, eco_ids, all_auth_ids = await _load_ecosystems(db, user, selected_ids)

                # Load member in first selected ecosystem for backward compat
                member = None
                if user and eco_ids:
                    member_result = await db.execute(
                        select(MemberModel).where(
                            MemberModel.user_id == user.id,
                            MemberModel.ecosystem_id.in_(eco_ids),
                        ).limit(1)
                    )
                    member = member_result.scalar_one_or_none()
                if member is None and user:
                    # Fallback: any member for this user
                    member_result = await db.execute(
                        select(MemberModel).where(MemberModel.user_id == user.id).limit(1)
                    )
                    member = member_result.scalar_one_or_none()

                request.ctx.member = member
                request.ctx.ecosystems = ecosystems
                request.ctx.selected_ecosystem_ids = eco_ids
                request.ctx.authorized_ecosystem_ids = all_auth_ids
                request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems(ecosystems, eco_ids)
        except Exception:
            logger.exception("Auth middleware error")
            return _unauth()

        return None

    # Root redirect
    @app.get("/")
    async def root(request: Request):
        if hasattr(request.ctx, "member") and request.ctx.member:
            return redirect("/dashboard")
        return redirect("/auth/login")

    # Catch-all: redirect unknown paths to the dashboard
    from sanic.exceptions import NotFound
    @app.exception(NotFound)
    async def catch_not_found(request, exception):
        return redirect("/dashboard")

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
    parser.add_argument("--ssl-cert", default=None, help="Path to TLS certificate file")
    parser.add_argument("--ssl-key", default=None, help="Path to TLS private key file")
    args = parser.parse_args()

    # Sanic's multiprocess reloader can't resolve the factory when the app is
    # instantiated inside __main__, so dev mode always runs single-process.
    single = args.single_process or args.dev

    ssl = None
    if args.ssl_cert and args.ssl_key:
        ssl = {"cert": args.ssl_cert, "key": args.ssl_key}

    app = create_app()
    if single:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.dev,
            single_process=True,
            ssl=ssl,
        )
    else:
        app.run(
            host=args.host,
            port=args.port,
            dev=args.dev,
            workers=args.workers,
            ssl=ssl,
        )
