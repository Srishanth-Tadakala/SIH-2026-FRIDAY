"""Action Execution & Safety Interlock API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Handles Tier 1 autonomous execution, Tier 2 supervised countdown queues, and
Tier 3 Commander PIN authorization gatekeeping.
"""

from __future__ import annotations

import time
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.agents.framework.models import ActionProposal, AutonomyTier, ProposalStatus
from ..state import get_server_state

router = APIRouter(prefix="/api/actions", tags=["Actions"])


class ActionProposalPayload(BaseModel):
    """Payload for submitting an action proposal for tiered execution."""
    plan_name: str
    strategy: str = "OPERATIONAL_MITIGATION"
    autonomy_tier: str = Field(default="TIER_1", description="TIER_1, TIER_2, or TIER_3")
    actions: list[dict[str, Any]]
    expected_outcome: str = "Restore nominal telemetry"
    resource_cost: float = Field(default=0.1, ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    bypass_supervision: bool = False
    commander_pin: str | None = Field(default=None, description="Station Commander PIN for immediate Tier 3 authorization")
    execution_token: str | None = Field(default=None, description="HMAC-SHA256 signed execution token")


class PinAuthorizationPayload(BaseModel):
    """Payload for authorizing high-risk Tier 3 commands via Commander PIN."""
    pin: str = Field(..., description="Station Commander authorization PIN (e.g. BHARATI-CMD-2026)")
    command: str = Field(default="COMMANDER_EMERGENCY_DISPATCH", description="Target command identifier")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Command execution parameters")
    action_id: str | None = Field(default=None, description="Optional pending action ID to execute upon authorization")


@router.post("/execute")
def execute_action(payload: ActionProposalPayload) -> dict[str, Any]:
    """Submit an action proposal for execution according to its Autonomy Tier."""
    state = get_server_state()

    t_str = payload.autonomy_tier.upper()
    if t_str in ("TIER_1", "TIER_1_AUTONOMOUS"):
        tier = AutonomyTier.TIER_1_AUTONOMOUS
    elif t_str in ("TIER_2", "TIER_2_SUPERVISED"):
        tier = AutonomyTier.TIER_2_SUPERVISED
    elif t_str in ("TIER_3", "TIER_3_COMMANDER_CONFIRMATION"):
        tier = AutonomyTier.TIER_3_COMMANDER_CONFIRMATION
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid autonomy tier '{payload.autonomy_tier}'. Valid tiers: TIER_1, TIER_2, TIER_3",
        )

    proposal = ActionProposal(
        title=payload.plan_name,
        target_subsystem=payload.strategy,
        parameter_overrides=payload.actions,
        tier=tier,
        rationale=payload.expected_outcome,
        proposal_id=f"ACT-{int(time.time() * 1000)}",
        status=ProposalStatus.DRAFT,
    )

    result = state.orchestrator.execute_proposal(
        proposal,
        bypass_supervision=payload.bypass_supervision,
        commander_pin=payload.commander_pin,
        execution_token=payload.execution_token,
    )
    res_dict = result.to_dict()
    res_dict["autonomy_tier"] = "TIER_1" if tier == AutonomyTier.TIER_1_AUTONOMOUS else ("TIER_2" if tier == AutonomyTier.TIER_2_SUPERVISED else "TIER_3")
    res_dict["action_id"] = proposal.proposal_id
    res_dict["plan_name"] = proposal.title
    return res_dict


@router.get("/history")
def get_action_history(station_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Retrieve full chronological audit trail of all executed physical actions and digital twin adjustments."""
    state = get_server_state()
    history = list(state.autonomous_action_history)
    if station_id:
        sid = station_id.lower()
        history = [a for a in history if a.get("station_id", "").lower() == sid]
    return history[-limit:]


@router.get("/pending")
def list_pending_supervised_actions() -> list[dict[str, Any]]:
    """List all actions currently queued in the Tier 2 supervised countdown review window."""
    state = get_server_state()
    return state.orchestrator.get_pending_supervised_actions()


@router.get("/pending_tier3")
def list_pending_tier3_actions() -> list[dict[str, Any]]:
    """List all Tier 3 actions held awaiting Commander PIN confirmation."""
    state = get_server_state()
    return state.orchestrator.get_pending_tier3_actions()


@router.post("/supervised/{action_id}/bypass")
def bypass_supervised_action(action_id: str) -> dict[str, Any]:
    """Operator supervisor bypass: immediately confirms and executes a Tier 2 action."""
    state = get_server_state()
    result = state.orchestrator.bypass_supervised_action(action_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Supervised action '{action_id}' not found or already executed.")
    res_dict = result.to_dict()
    res_dict["action_id"] = action_id
    return res_dict


@router.post("/supervised/{action_id}/cancel")
def cancel_supervised_action(action_id: str) -> dict[str, Any]:
    """Operator veto: cancels a pending Tier 2 supervised action before countdown expiry."""
    state = get_server_state()
    success = state.orchestrator.cancel_supervised_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Supervised action '{action_id}' not found or already executed.")
    return {
        "status": "SUCCESS",
        "action_id": action_id,
        "message": f"Supervised action '{action_id}' successfully vetoed and removed from queue.",
    }


@router.post("/tier3/{action_id}/cancel")
def cancel_tier3_action(action_id: str) -> dict[str, Any]:
    """Operator veto: cancels a pending Tier 3 action awaiting Commander confirmation."""
    state = get_server_state()
    success = state.orchestrator.cancel_tier3_action(action_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tier 3 action '{action_id}' not found or already executed.")
    return {
        "status": "SUCCESS",
        "action_id": action_id,
        "message": f"Tier 3 action '{action_id}' successfully cancelled and removed from queue.",
    }


@router.post("/authorize_pin")
def authorize_tier3_pin(payload: PinAuthorizationPayload) -> dict[str, Any]:
    """Verify Station Commander PIN for life-safety Tier 3 actions and execute if authenticated."""
    state = get_server_state()

    # Verify PIN with safety interlock manager
    is_valid = state.safety_interlock.verify_commander_authorization(
        command=payload.command,
        pin=payload.pin,
        parameters=payload.parameters,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="INVALID_PIN: Station Commander PIN verification failed. Action rejected and logged.",
        )

    # If action_id provided, execute the pending action (Tier 3 first, then Tier 2 fallback)
    executed_action = None
    if payload.action_id:
        res = state.orchestrator.authorize_and_execute_tier3(payload.action_id, commander_pin=payload.pin)
        if not res:
            res = state.orchestrator.bypass_supervised_action(payload.action_id)
        if res:
            executed_action = res.to_dict()

    return {
        "status": "AUTHORIZED",
        "command": payload.command,
        "timestamp": time.time(),
        "audit_message": "Commander authorization verified. Tier 3 interlock unlocked.",
        "executed_action": executed_action,
    }


class ActuatorCommandPayload(BaseModel):
    """Payload for commanding physical station actuators."""
    command: str = Field(..., description="START_CHP, STOP_CHP, SET_TRACE_HEATING, SET_BLIZZARD_DAMPERS, TOGGLE_SCIENCE_LOAD_SHED")
    parameters: dict[str, Any] = Field(default_factory=dict)
    pin: str | None = Field(default=None, description="Optional Commander PIN for life-critical actions")


class AutonomousModePayload(BaseModel):
    """Payload for configuring edge autonomous closed-loop governor."""
    autonomous_enabled: bool | None = Field(default=None, description="Enable or disable autonomous AI closed-loop control")
    continuous_running: bool | None = Field(default=None, description="Start or pause continuous 1 Hz simulation clock")
    speed: float | None = Field(default=None, description="Simulation speed factor: 1.0, 2.0, 5.0")


@router.get("/actuators/{station_id}")
def get_station_actuators(station_id: str) -> dict[str, Any]:
    """Fetch live operational states for all physical station actuators."""
    state = get_server_state()
    try:
        return state.get_actuator_state(station_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/actuators/{station_id}")
def execute_actuator_command(station_id: str, payload: ActuatorCommandPayload) -> dict[str, Any]:
    """Command physical station actuators directly or with supervisor authorization."""
    state = get_server_state()
    try:
        return state.set_actuator_command(
            station_id=station_id,
            command=payload.command,
            parameters=payload.parameters,
            pin=payload.pin,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/cognitive_logs/{station_id}")
def get_cognitive_logs(
    station_id: str,
    category: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve real-time cognitive perception and actuation logs ('What Was Noticed & What Was Done')."""
    state = get_server_state()
    return state.get_cognitive_logs(station_id=station_id, category=category, limit=limit)


@router.post("/autonomous_mode")
def configure_autonomous_mode(payload: AutonomousModePayload) -> dict[str, Any]:
    """Configure closed-loop autonomous AI governor and continuous simulation loop."""
    state = get_server_state()
    if payload.autonomous_enabled is not None:
        state.autonomous_mode_enabled = payload.autonomous_enabled
        state.log_cognitive_event(
            category="EDGE_AUTHORITY",
            title=f"Autonomous Closed-Loop AI: {'ENABLED' if payload.autonomous_enabled else 'SUSPENDED'}",
            details=f"F.R.I.D.A.Y. edge closed-loop governor set to {payload.autonomous_enabled}.",
            severity="INFO",
        )
    if payload.continuous_running is not None:
        if payload.continuous_running:
            state.start_continuous_loop()
        else:
            state.stop_continuous_loop()
    if payload.speed is not None:
        state.continuous_speed = max(0.1, min(10.0, payload.speed))

    return {
        "autonomous_enabled": state.autonomous_mode_enabled,
        "continuous_running": state.is_continuous_loop_running,
        "speed": state.continuous_speed,
        "edge_blackout_mode": state.orchestrator.edge_blackout_mode,
    }


@router.get("/edge_status/{station_id}")
def get_edge_status(station_id: str) -> dict[str, Any]:
    """Fetch Polar Blackout edge command authority metrics and queue backlog."""
    state = get_server_state()
    try:
        act_state = state.get_actuator_state(station_id)
        return act_state["edge_status"]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
