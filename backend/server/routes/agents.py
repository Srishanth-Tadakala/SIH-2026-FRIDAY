"""Cognitive Agents API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Inspects the 10 cognitive agents, agent internal status, and message bus statistics.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException

from backend.agents.framework.models import AgentRole
from ..state import get_server_state

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("/status")
def get_agents_status() -> dict[str, Any]:
    """Retrieve operational status for all 10 cognitive agents in the society."""
    state = get_server_state()
    orch_status = state.orchestrator.get_cognitive_status()

    # Collect individual agent statuses
    agents_info: dict[str, Any] = {
        "FRIDAY_ORCHESTRATOR": {
            "role": "FRIDAY_ORCHESTRATOR",
            "status": "ONLINE_ACTIVE",
            "active_session_id": state.orchestrator._active_session_id,
            "briefing_cards_count": len(state.orchestrator._briefing_cards),
            "processed_messages_count": len(state.orchestrator._processed_messages),
            "supervised_actions_count": len(state.orchestrator.get_pending_supervised_actions()),
        },
        "SITUATION_AWARENESS": {
            "role": "SITUATION_AWARENESS",
            "status": "ONLINE_ACTIVE",
            "active_anomalies": len(state.situation_awareness._active_anomalies),
            "anomaly_keys": list(state.situation_awareness._active_anomalies.keys()),
        },
        "DIAGNOSTIC": {
            "role": "DIAGNOSTIC",
            "status": "ONLINE_ACTIVE",
            "has_latest_diagnosis": getattr(state.diagnostic, "_latest_diagnosis", None) is not None,
        },
        "PREDICTION": {
            "role": "PREDICTION",
            "status": "ONLINE_ACTIVE",
            "has_latest_projection": getattr(state.prediction, "_latest_projection", None) is not None,
        },
        "RISK_IMPACT": {
            "role": "RISK_IMPACT",
            "status": "ONLINE_ACTIVE",
            "has_latest_assessment": getattr(state.risk_impact, "_latest_assessment", None) is not None,
        },
        "PLANNING": {
            "role": "PLANNING",
            "status": "ONLINE_ACTIVE",
            "has_latest_plan": getattr(state.planning, "_latest_plan", None) is not None,
        },
        "WHAT_IF": {
            "role": "WHAT_IF",
            "status": "ONLINE_ACTIVE",
            "has_latest_simulation": getattr(state.what_if, "_latest_verdict", None) is not None,
        },
        "MISSION_OPS": {
            "role": "MISSION_OPS",
            "status": "ONLINE_ACTIVE",
            "has_assessment": getattr(state.mission_ops, "_latest_assessment", None) is not None,
        },
        "MAINTENANCE": {
            "role": "MAINTENANCE",
            "status": "ONLINE_ACTIVE",
            "has_report": getattr(state.maintenance, "_latest_report", None) is not None,
        },
        "RESOURCE_OPTIMIZER": {
            "role": "RESOURCE_OPTIMIZER",
            "status": "ONLINE_ACTIVE",
            "has_plan": getattr(state.resource_optimizer, "_latest_plan", None) is not None,
        },
    }

    return {
        "orchestrator_status": "ONLINE_ACTIVE",
        "total_agents": 10,
        "agents": agents_info,
        "bus_message_count": len(state.bus.get_history()),
        "active_deliberation_sessions": len(state.bus.get_active_sessions()),
    }


@router.get("/bus/stats")
def get_bus_statistics() -> dict[str, Any]:
    """Retrieve message bus throughput and subscription statistics."""
    state = get_server_state()
    history = state.bus.get_history()
    active_sessions = state.bus.get_active_sessions()

    # Breakdown by message type
    type_counts: dict[str, int] = {}
    sender_counts: dict[str, int] = {}
    for m in history:
        t_val = m.message_type.value if hasattr(m.message_type, "value") else str(m.message_type)
        s_val = m.sender.value if hasattr(m.sender, "value") else str(m.sender)
        type_counts[t_val] = type_counts.get(t_val, 0) + 1
        sender_counts[s_val] = sender_counts.get(s_val, 0) + 1

    return {
        "total_messages_published": len(history),
        "active_sessions_count": len(active_sessions),
        "active_session_ids": [s.session_id for s in active_sessions],
        "message_counts_by_type": type_counts,
        "message_counts_by_sender": sender_counts,
    }


@router.get("/{agent_role}")
def get_agent_detail(agent_role: str) -> dict[str, Any]:
    """Retrieve detailed state and message memory for a specific cognitive agent."""
    state = get_server_state()
    role_str = agent_role.upper()
    try:
        role = AgentRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent role '{agent_role}'. Valid roles: {[r.value for r in AgentRole]}",
        )

    # Find agent by role
    agent_map = {
        AgentRole.FRIDAY_ORCHESTRATOR: state.orchestrator,
        AgentRole.SITUATION_AWARENESS: state.situation_awareness,
        AgentRole.DIAGNOSTIC: state.diagnostic,
        AgentRole.PREDICTION: state.prediction,
        AgentRole.RISK_IMPACT: state.risk_impact,
        AgentRole.PLANNING: state.planning,
        AgentRole.WHAT_IF: state.what_if,
        AgentRole.MISSION_OPS: state.mission_ops,
        AgentRole.MAINTENANCE: state.maintenance,
        AgentRole.RESOURCE_OPTIMIZER: state.resource_optimizer,
    }

    agent = agent_map.get(role)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_role}' not found.")

    recent_messages = [
        {
            "message_id": m.message_id,
            "sender": m.sender.value if hasattr(m.sender, "value") else str(m.sender),
            "recipient": m.recipient.value if hasattr(m.recipient, "value") else str(m.recipient),
            "message_type": m.message_type.value if hasattr(m.message_type, "value") else str(m.message_type),
            "severity": m.severity.value if hasattr(m.severity, "value") else str(m.severity),
            "timestamp": m.timestamp,
        }
        for m in state.bus.get_history()
        if m.sender == role or m.recipient == role or m.recipient == "BROADCAST"
    ][-10:]

    return {
        "role": role.value,
        "status": "ONLINE_ACTIVE",
        "recent_messages_count": len(recent_messages),
        "recent_messages": recent_messages,
    }
