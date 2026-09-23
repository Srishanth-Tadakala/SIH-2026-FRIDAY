"""Cognitive Agents API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides:
- Operational status, runtime activity, and hypotheses for all 10 cognitive agents.
- Message bus throughput and subscription metrics.
- Topological Causal Dependency Graph export (35 nodes, 45 edges).
- On-demand Causal Blast Radius calculation.
- Detailed agent memory, objectives, and recent dialogue audit trail.
"""

from __future__ import annotations

import time
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.framework.groq_brain import GroqBrainEngine
from backend.agents.framework.models import AgentRole
from ..state import get_server_state

router = APIRouter(prefix="/api/agents", tags=["Agents"])


class SetGroqKeyRequest(BaseModel):
    api_key: str = Field(..., description="Groq API key (starts with gsk_)", min_length=10)


@router.post("/set_groq_key")
def set_agent_groq_key(request: SetGroqKeyRequest) -> dict[str, Any]:
    """Dynamically register or update the Groq API key for all 10 cognitive agents at runtime."""
    brain = GroqBrainEngine.get_instance()
    is_live = brain.set_api_key(request.api_key)
    return {
        "status": "SUCCESS",
        "is_live_available": is_live,
        "model_name": brain.model_name,
        "message": (
            "Live Groq LPU dynamic reasoning active across all 10 agents."
            if is_live
            else "Groq API key registered; edge neural fallback active until live handshake succeeds."
        ),
    }


@router.get("/groq_status")
def get_agents_groq_status() -> dict[str, Any]:
    """Retrieve Groq LPU engine status, model details, inference count, and latency metrics."""
    brain = GroqBrainEngine.get_instance()
    return brain.get_groq_status()


@router.get("/status")
def get_agents_status() -> dict[str, Any]:
    """Retrieve dynamic operational status for all 10 cognitive agents in the society."""
    state = get_server_state()
    return state.get_agent_society_status()


@router.get("/bus/stats")
def get_bus_statistics() -> dict[str, Any]:
    """Retrieve message bus throughput and subscription statistics."""
    state = get_server_state()
    history = state.bus.get_history()
    active_sessions = state.bus.get_active_sessions()

    # Breakdown by message type and sender
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
        "active_deliberation_phase": state.active_deliberation_phase,
    }


@router.get("/causal_graph")
def get_causal_graph() -> dict[str, Any]:
    """Retrieve complete topological causal dependency graph for station digital twin.
    
    Includes 35 nodes, 45 directed physical edges, 2D layout coordinates,
    subsystems, criticality levels, and active root-cause status tags.
    """
    state = get_server_state()
    topology = state.graph.export_react_flow_topology()

    # Identify currently diagnosed root-cause or active symptom nodes
    active_nodes: set[str] = set()
    latest_causes = []
    active_sessions = state.bus.get_active_sessions()
    for s in active_sessions:
        for rc in s.root_causes:
            r_id = rc.get("root_cause_node_id")
            if r_id:
                active_nodes.add(r_id)
                latest_causes.append(r_id)
            for path_node in rc.get("causal_chain", []):
                active_nodes.add(path_node)

    # Decorate nodes with active anomaly indicators
    for n in topology["nodes"]:
        n_id = n["id"]
        is_root = n_id in latest_causes
        is_involved = n_id in active_nodes
        n["data"]["isRootCause"] = is_root
        n["data"]["isCausalPath"] = is_involved
        n["data"]["status"] = "CRITICAL_FAULT" if is_root else "IMPACTED" if is_involved else "NOMINAL"

    return {
        "station_id": state.active_station_id,
        "total_nodes": len(topology["nodes"]),
        "total_edges": len(topology["edges"]),
        "nodes": topology["nodes"],
        "edges": topology["edges"],
        "active_fault_nodes": list(active_nodes),
    }


@router.get("/causal_graph/blast_radius/{node_id}")
def get_node_blast_radius(node_id: str) -> dict[str, Any]:
    """Calculate forward cascading failure blast radius and severity for any station node."""
    state = get_server_state()
    if node_id not in state.graph._nodes:
        raise HTTPException(status_code=404, detail=f"Causal node '{node_id}' not found in station topology.")

    blast = state.graph.calculate_blast_radius(node_id)
    impacts = state.graph.get_downstream_impacts(node_id, max_depth=6)
    return {
        "node_id": node_id,
        "blast_radius": blast,
        "downstream_impacts": impacts,
    }


@router.get("/{agent_role}")
def get_agent_detail(agent_role: str) -> dict[str, Any]:
    """Retrieve detailed runtime state, objective, and message audit trail for a specific cognitive agent."""
    state = get_server_state()
    role_str = agent_role.upper()
    try:
        role = AgentRole(role_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent role '{agent_role}'. Valid roles: {[r.value for r in AgentRole]}",
        )

    # Agent runtime state profile
    runtime_info = state.agent_runtime_states.get(role.value, {})

    # Extract recent dialogue messages with full payload summary
    recent_messages = []
    for m in reversed(state.bus.get_history()):
        if m.sender == role or m.recipient == role or m.recipient == "BROADCAST":
            recent_messages.append({
                "message_id": m.message_id,
                "session_id": m.session_id,
                "sender": m.sender.value if hasattr(m.sender, "value") else str(m.sender),
                "recipient": m.recipient.value if hasattr(m.recipient, "value") else str(m.recipient),
                "message_type": m.message_type.value if hasattr(m.message_type, "value") else str(m.message_type),
                "severity": m.severity.value if hasattr(m.severity, "value") else str(m.severity),
                "confidence": round(float(m.confidence), 2),
                "timestamp": m.timestamp,
                "summary": m.payload.get("summary") or m.payload.get("title") or m.payload.get("explanation") or str(m.payload)[:120],
                "payload": m.payload,
            })
            if len(recent_messages) >= 12:
                break

    return {
        "role": role.value,
        "runtime": runtime_info,
        "recent_messages_count": len(recent_messages),
        "recent_messages": recent_messages,
    }
