"""NEOS governance tool for emergency-criteria-design (Layer 8).

Auto-generated from SKILL.md on 2026-06-10T07:59:56.
Source: C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-08-emergency\emergency-criteria-design\SKILL.md

This file is generated. To regenerate, run:
    python -m scratch.codegen generate emergency-criteria-design
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


class EmergencyCriteriaDesignInput(BaseModel):
    """Input schema for emergency-criteria-design (Layer 8).

    Define objective, measurable emergency criteria with matching exit conditions -- run this before any crisis arrives so the ecosystem never debates whether an emergency is real while one is happening.
    """

    risk_assessment: str = Field(description="a structured identification of credible emergency scenarios for the ETHOS's domain, informed by geographic, financial, legal, and operational context")
    existing_criteria_registry: str = Field(description="all currently active emergency criteria for the scope, to prevent duplication and ensure coherence")
    safeguard_trigger_registry: str = Field(description="active Layer VII triggers that may interact with emergency thresholds (per safeguard-trigger-design)")
    act_process_access: str = Field(description="criteria must be designed and installed through the Advice-Consent-Test protocol (Layer III)")
    domain_boundary: str = Field(description="the scope boundary from domain-mapping, confirming which ETHOS or ecosystem the criteria apply to")
    stakeholder_input: str = Field(description="affected participants who will provide consent during installation")



async def emergency_criteria_design(
    args: dict,
    db: AsyncSession,
    ecosystem_ids: list | None = None,
) -> dict:
    """Define objective, measurable emergency criteria with matching exit conditions -- run this before any crisis arrives so the ecosystem never debates whether an emergency is real while one is happening.

    Auto-generated from C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-08-emergency\emergency-criteria-design\SKILL.md
    Layer: 8 | Version: 0.1.0
    Dependencies: agreement-creation, act-consent-phase, safeguard-trigger-design

    Steps:
    1. Conduct risk assessment.
    2. Define entry criteria.
    3. Define matching exit criteria.
    4. Define maximum duration.
    5. Map to circuit breaker states.
    6. Cross-reference safeguard triggers.
    7. Enter ACT Advice phase.
    8. Enter ACT Consent phase.
    9. Install in Emergency Criteria Registry.
    10. Schedule review.
    """

    # ---- Required field validation ----
    risk_assessment = args.get('risk_assessment', '')
    existing_criteria_registry = args.get('existing_criteria_registry', '')
    safeguard_trigger_registry = args.get('safeguard_trigger_registry', '')
    act_process_access = args.get('act_process_access', '')
    domain_boundary = args.get('domain_boundary', '')
    stakeholder_input = args.get('stakeholder_input', '')

    if not risk_assessment:
        return {"success": False, "error": "risk_assessment is required."}
    if not existing_criteria_registry:
        return {"success": False, "error": "existing_criteria_registry is required."}
    if not safeguard_trigger_registry:
        return {"success": False, "error": "safeguard_trigger_registry is required."}
    if not act_process_access:
        return {"success": False, "error": "act_process_access is required."}
    if not domain_boundary:
        return {"success": False, "error": "domain_boundary is required."}
    if not stakeholder_input:
        return {"success": False, "error": "stakeholder_input is required."}

    # ---- Ecosystem ID resolution ----
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}

    # ---- TODO: Implement skill logic ----
    # This stub was generated from C:\Users\atooz\Programming\NEOS\neos-operating-system\neos-core\layer-08-emergency\emergency-criteria-design\SKILL.md
    # Steps to implement (10 total):
    #   1. Conduct risk assessment.
    #   2. Define entry criteria.
    #   3. Define matching exit criteria.
    #   4. Define maximum duration. (refs: emergency-reversion, crisis-coordination)
    #   5. Map to circuit breaker states.
    #   6. Cross-reference safeguard triggers.
    #   7. Enter ACT Advice phase. (refs: act-advice-phase)
    #   8. Enter ACT Consent phase. (refs: act-consent-phase)
    #   9. Install in Emergency Criteria Registry.
    #   10. Schedule review.

    return {
        "success": True,
        "data": {
            "skill": "emergency-criteria-design",
            "layer": 8,
            "version": "0.1.0",
            "message": "Stub for emergency-criteria-design — implementation pending.",
        },
    }

        def get_emergency_criteria_design_tooldef() -> object:
            """Return the ToolDef entry for emergency-criteria-design."""
            return emergency_criteria_design_TOOLDEF


        emergency_criteria_design_TOOLDEF = ToolDef(
    name="emergency_criteria_design",
    description="Define objective, measurable emergency criteria with matching exit conditions -- run this before any crisis arrives so the ecosystem never debates whether an emergency is real while one is happening.",
    parameters={
        "type": "object",
        "properties": {
                "risk_assessment": {
            "type": "string",
            "description": "a structured identification of credible emergency scenarios for the ETHOS's domain, informed by geographic, financial, legal, and operational context",
        },
        "existing_criteria_registry": {
            "type": "string",
            "description": "all currently active emergency criteria for the scope, to prevent duplication and ensure coherence",
        },
        "safeguard_trigger_registry": {
            "type": "string",
            "description": "active Layer VII triggers that may interact with emergency thresholds (per safeguard-trigger-design)",
        },
        "act_process_access": {
            "type": "string",
            "description": "criteria must be designed and installed through the Advice-Consent-Test protocol (Layer III)",
        },
        "domain_boundary": {
            "type": "string",
            "description": "the scope boundary from domain-mapping, confirming which ETHOS or ecosystem the criteria apply to",
        },
        "stakeholder_input": {
            "type": "string",
            "description": "affected participants who will provide consent during installation",
        },
        },
        "required": ["risk_assessment", "existing_criteria_registry", "safeguard_trigger_registry", "act_process_access", "domain_boundary", "stakeholder_input"],
    },
    handler=emergency_criteria_design,
),
