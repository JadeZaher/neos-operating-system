"""NEOS governance tool for escalation-triage (Layer 6).

Auto-generated from SKILL.md on 2026-06-10T17:59:13.
Source: C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-06-conflict\escalation-triage\SKILL.md

This file is generated. To regenerate, run:
    python -m scratch.codegen generate escalation-triage
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = __import__("logging").getLogger(__name__)

# Re-import helpers from the main governance_tools module at runtime.
# In production these would be in a shared utilities module.
try:
    from neos_agent.agent.governance_tools import (
        _get_first_ecosystem_id,
        _resolve_member,
        _today,
        ToolDef,
    )
except ImportError:
    # Fallback for scratch testing
    pass

from __future__ import annotations

from pydantic import BaseModel, Field


class EscalationTriageInput(BaseModel):
    """Input schema for escalation-triage (Layer 6).

    Assess conflict severity, scope, root cause, and safety to route each situation to the right resolution tier -- direct dialogue, coaching, harm circle, or community-wide assessment -- so that no conflict is over-escalated or swept aside.
    """

    conflict_report_or_observation: str = Field(description="a description of the situation from the reporting party, including what happened, who is involved, and what impact has been experienced. Format: written or verbal, documented by the triager.")
    reporting_party_identity: str = Field(description="who brought the conflict forward -- the person harmed, a witness, a facilitator, or a steward. The relationship of the reporter to the conflict affects the assessment.")
    domain_reference: str = Field(description="the ETHOS, circle, and governance context where the conflict is occurring, verified against domain-mapping.")
    prior_resolution_attempts: str = Field(description="any direct dialogue, informal conversation, or previous triage that has already occurred, including outcomes and why the conflict persists.")
    safety_flag: Optional[str] = Field(description="optional but prioritized", default=None)



async def escalation_triage(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None,
) -> dict:
    """Assess conflict severity, scope, root cause, and safety to route each situation to the right resolution tier -- direct dialogue, coaching, harm circle, or community-wide assessment -- so that no conflict is over-escalated or swept aside.

    Auto-generated from C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-06-conflict\escalation-triage\SKILL.md
    Layer: 6 | Version: 0.1.0
    Dependencies: harm-circle, nvc-dialogue, coaching-intervention, domain-mapping

    Steps:
    1. Receive the report.
    2. Assess safety.
    3. Evaluate triage dimensions.
    4. Determine the routing.
    5. Consult the affected parties.
    6. Document and hand off.
    """

    # ---- Required field validation ----
    conflict_report_or_observation = args.get('conflict_report_or_observation', '')
    reporting_party_identity = args.get('reporting_party_identity', '')
    domain_reference = args.get('domain_reference', '')
    prior_resolution_attempts = args.get('prior_resolution_attempts', '')

    if not conflict_report_or_observation:
        return {"success": False, "error": "conflict_report_or_observation is required."}
    if not reporting_party_identity:
        return {"success": False, "error": "reporting_party_identity is required."}
    if not domain_reference:
        return {"success": False, "error": "domain_reference is required."}
    if not prior_resolution_attempts:
        return {"success": False, "error": "prior_resolution_attempts is required."}

    # ---- Ecosystem ID resolution ----
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}

    # ---- TODO: Implement skill logic ----
    # This stub was generated from C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-06-conflict\escalation-triage\SKILL.md
    # Steps to implement (6 total):
    #   1. Receive the report.
    #   2. Assess safety.
    #   3. Evaluate triage dimensions.
    #   4. Determine the routing.
    #   5. Consult the affected parties.
    #   6. Document and hand off.

    return {
        "success": True,
        "data": {
            "skill": "escalation-triage",
            "layer": 6,
            "version": "0.1.0",
            "message": "Stub for escalation-triage — implementation pending.",
        },
    }

        def get_escalation_triage_tooldef() -> object:
            """Return the ToolDef entry for escalation-triage."""
            return escalation_triage_TOOLDEF


        escalation_triage_TOOLDEF = ToolDef(
    name="escalation_triage",
    description="Assess conflict severity, scope, root cause, and safety to route each situation to the right resolution tier -- direct dialogue, coaching, harm circle, or community-wide assessment -- so that no conflict is over-escalated or swept aside.",
    parameters={
        "type": "object",
        "properties": {
                "conflict_report_or_observation": {
            "type": "string",
            "description": "a description of the situation from the reporting party, including what happened, who is involved, and what impact has been experienced. Format: written or verbal, documented by the triager.",
        },
        "reporting_party_identity": {
            "type": "string",
            "description": "who brought the conflict forward -- the person harmed, a witness, a facilitator, or a steward. The relationship of the reporter to the conflict affects the assessment.",
        },
        "domain_reference": {
            "type": "string",
            "description": "the ETHOS, circle, and governance context where the conflict is occurring, verified against domain-mapping.",
        },
        "prior_resolution_attempts": {
            "type": "string",
            "description": "any direct dialogue, informal conversation, or previous triage that has already occurred, including outcomes and why the conflict persists.",
        },
        "safety_flag": {
            "type": "string",
            "description": "optional but prioritized",
        },
        },
        "required": ["conflict_report_or_observation", "reporting_party_identity", "domain_reference", "prior_resolution_attempts"],
    },
    handler=escalation_triage,
),
