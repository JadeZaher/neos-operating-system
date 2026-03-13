"""Dashboard view blueprints for the NEOS governance webservice.

Registers all Sanic blueprints for the dashboard UI — agreements,
domains, members, proposals, decisions, conflicts, safeguards,
emergency, exit, onboarding, and the dashboard home page.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sanic import Sanic

from neos_agent.views.dashboard import dashboard_bp
from neos_agent.views.agreements import agreements_bp
from neos_agent.views.domains import domains_bp
from neos_agent.views.members import members_bp
from neos_agent.views.proposals import proposals_bp
from neos_agent.views.decisions import decisions_bp
from neos_agent.views.conflicts import conflicts_bp
from neos_agent.views.safeguards import safeguards_bp
from neos_agent.views.emergency import emergency_bp
from neos_agent.views.exit import exit_bp
from neos_agent.views.onboarding import onboarding_bp


def register_views(app: "Sanic") -> None:
    """Register all dashboard view blueprints on the Sanic app.

    Args:
        app: The Sanic application instance.
    """
    app.blueprint(dashboard_bp)
    app.blueprint(agreements_bp)
    app.blueprint(domains_bp)
    app.blueprint(members_bp)
    app.blueprint(proposals_bp)
    app.blueprint(decisions_bp)
    app.blueprint(conflicts_bp)
    app.blueprint(safeguards_bp)
    app.blueprint(emergency_bp)
    app.blueprint(exit_bp)
    app.blueprint(onboarding_bp)
