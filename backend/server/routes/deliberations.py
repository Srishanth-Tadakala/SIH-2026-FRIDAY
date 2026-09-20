"""Deliberation Sessions API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides endpoints to inspect multi-agent deliberation sessions, candidate proposals,
agent critiques, and Commander Briefing Cards.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException

from backend.agents.framework.models import ProposalStatus
from ..state import get_server_state

router = APIRouter(prefix="/api/deliberations", tags=["Deliberations"])


@router.get("", response_model=list[dict[str, Any]])
def list_deliberation_sessions() -> list[dict[str, Any]]:
    """List all active and completed multi-agent deliberation sessions."""
    state = get_server_state()
    sessions = state.bus._sessions.values()
    results: list[dict[str, Any]] = []

    for s in sessions:
        results.append({
            "session_id": s.session_id,
            "created_at": s.created_at,
            "status": "RESOLVED" if s.resolved else "ACTIVE",
            "resolved": s.resolved,
            "trigger_alert": s.trigger_alert,
            "proposals_count": len(s.candidate_proposals),
            "critiques_count": len(s.critiques),
            "has_consensus": s.final_plan is not None,
            "winner_proposal_id": s.final_plan.proposal_id if s.final_plan else None,
        })

    # Sort descending by creation time
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results


@router.get("/{session_id}")
def get_deliberation_session(session_id: str) -> dict[str, Any]:
    """Retrieve complete deliberation session blackboard including proposals, simulations, and critiques."""
    state = get_server_state()
    session = state.bus.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Deliberation session '{session_id}' not found.")

    proposals_data = [
        p.to_dict() if hasattr(p, "to_dict") else dict(p.__dict__)
        for p in session.candidate_proposals
    ]

    sim_results = getattr(session, "simulation_results", [])
    sim_results_data = [
        sr.to_dict() if hasattr(sr, "to_dict") else dict(sr.__dict__)
        for sr in sim_results
    ]

    critiques_data = [
        c.to_dict() if hasattr(c, "to_dict") else dict(c.__dict__) if hasattr(c, "__dict__") else c
        for c in session.critiques
    ]

    consensus_data = (
        session.final_plan.to_dict()
        if session.final_plan and hasattr(session.final_plan, "to_dict")
        else None
    )

    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "status": "RESOLVED" if session.resolved else "ACTIVE",
        "resolved": session.resolved,
        "trigger_alert": session.trigger_alert,
        "root_causes": session.root_causes,
        "predictions": session.predictions,
        "risk_assessment": session.risk_assessment,
        "candidate_proposals": proposals_data,
        "simulation_results": sim_results_data,
        "critiques": critiques_data,
        "consensus_plan": consensus_data,
    }


@router.get("/{session_id}/briefing_card")
def get_commander_briefing_card(session_id: str) -> dict[str, Any]:
    """Synthesize or retrieve Commander Briefing Card for the specified session."""
    state = get_server_state()
    session = state.bus.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Deliberation session '{session_id}' not found.")

    # Arbitrate if consensus not yet evaluated
    if not session.final_plan and session.candidate_proposals:
        state.orchestrator.arbitrate_session(session_id)

    card = state.orchestrator.synthesize_briefing_card(session_id)
    if not card:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to synthesize Commander Briefing Card for session '{session_id}'. Insufficient proposals or data.",
        )

    return card.to_dict()
