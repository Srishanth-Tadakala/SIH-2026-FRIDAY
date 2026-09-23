"""Copilot REST Routes for "Ask F.R.I.D.A.Y." Interactive Commander AI.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...agents.framework.groq_brain import GroqBrainEngine
from ...database.models import CopilotChatRecord
from ..state import get_server_state

logger = logging.getLogger("friday.server.routes.copilot")

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot"])


class CopilotChatRequest(BaseModel):
    message: str = Field(..., description="Query from Commander or Hackathon Judge", min_length=1)
    station_id: str = Field(default="bharati", description="Target Antarctic station ID")


class SetKeyRequest(BaseModel):
    api_key: str = Field(..., description="Groq API key starting with gsk_")


@router.post("/chat")
async def copilot_chat(request: CopilotChatRequest) -> dict[str, Any]:
    """Interactive real-time consultation with F.R.I.D.A.Y. Chief AI Orchestrator with persistent conversation history."""
    server_state = get_server_state()
    engine = server_state.get_engine(request.station_id)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Station '{request.station_id}' not found.")

    brain = GroqBrainEngine.get_instance()
    kpis = engine.get_station_kpis() if hasattr(engine, "get_station_kpis") else {}

    # Collect active alerts
    alerts: list[dict[str, Any]] = []
    if hasattr(server_state, "bus") and server_state.bus:
        active_sessions = server_state.bus.get_active_sessions()
        for sess in active_sessions:
            if sess.trigger_alert:
                alerts.append(sess.trigger_alert)

    # Collect recent case memory precedents
    recent_episodes: list[dict[str, Any]] = []
    if hasattr(server_state, "episodes_repo") and server_state.episodes_repo:
        try:
            records = await server_state.episodes_repo.get_recent_episodes(
                station_id=request.station_id, limit=3
            )
            recent_episodes = [
                ep.to_dict() if hasattr(ep, "to_dict") else dict(ep) for ep in records
            ]
        except Exception as e:
            logger.warning("Failed retrieving episodic memory for copilot: %s", e)
            recent_episodes = []

    res = await brain.reason_copilot_chat(
        user_message=request.message,
        station_id=request.station_id,
        kpis=kpis,
        active_alerts=alerts,
        recent_episodes=recent_episodes,
    )

    reply_text = res.get("reply", "No response generated.")
    cited_sensors = res.get("cited_sensors", [])
    suggested_followups = res.get("suggested_followups", [])
    operational_status = res.get("operational_status", "NOMINAL")

    # Persist user inquiry to edge database
    try:
        user_rec = CopilotChatRecord(
            station_id=request.station_id,
            role="user",
            message=request.message,
        )
        await server_state.copilot_repo.save_message(user_rec)

        # Persist assistant reply to edge database
        asst_rec = CopilotChatRecord(
            station_id=request.station_id,
            role="assistant",
            message=reply_text,
            cited_sensors=cited_sensors,
            suggested_followups=suggested_followups,
            operational_status=operational_status,
            model_used=brain.last_model_used,
            latency_ms=brain.last_latency_ms,
        )
        await server_state.copilot_repo.save_message(asst_rec)
    except Exception as e:
        logger.warning("Failed saving copilot chat to persistent storage: %s", e)

    return {
        "status": "SUCCESS",
        "station_id": request.station_id,
        "reply": reply_text,
        "cited_sensors": cited_sensors,
        "suggested_followups": suggested_followups,
        "operational_status": operational_status,
        "latency_ms": brain.last_latency_ms,
        "model_used": brain.last_model_used,
        "is_live_groq": brain.is_live_available(),
        "timestamp": time.time(),
    }


class ClearHistoryRequest(BaseModel):
    station_id: str | None = None


@router.get("/history")
async def get_copilot_history(
    station_id: str = "bharati",
    limit: int = 50,
) -> dict[str, Any]:
    """Retrieve persistent conversation history for the specified station."""
    server_state = get_server_state()
    records = await server_state.copilot_repo.get_history(station_id=station_id, limit=limit)
    dict_list = [r.to_dict() for r in records]
    return {
        "status": "SUCCESS",
        "station_id": station_id,
        "count": len(dict_list),
        "total": len(dict_list),
        "messages": dict_list,
        "history": dict_list,
    }


@router.post("/clear")
async def clear_copilot_history(
    req: ClearHistoryRequest | None = None,
    station_id: str | None = None,
) -> dict[str, Any]:
    """Clear persistent conversation history for the specified station."""
    target_station = (req.station_id if req and req.station_id else None) or station_id or "bharati"
    server_state = get_server_state()
    deleted = await server_state.copilot_repo.clear_history(station_id=target_station)
    return {
        "status": "SUCCESS",
        "station_id": target_station,
        "deleted_count": deleted,
        "message": f"Cleared {deleted} persistent chat records for {target_station}.",
    }


@router.get("/suggested_queries")
def get_suggested_queries() -> dict[str, Any]:
    """Return high-value prompt suggestions for hackathon jury demonstration."""
    return {
        "status": "SUCCESS",
        "suggested_queries": [
            "Explain the causal root cause of the current generator alert",
            "What is our projected fuel autonomy and time-to-violation?",
            "Assess blast radius of an unmitigated Katabatic blizzard",
            "How does F.R.I.D.A.Y. maintain station safety during 0 kbps polar blackout?",
            "What operational mitigation is recommended for utilidor water line freezing?",
            "Why did What-If simulator reject candidate plan #2?",
        ],
    }


@router.post("/set_key")
def set_groq_api_key(request: SetKeyRequest) -> dict[str, Any]:
    """Dynamically configure Groq LPU API key at runtime without restarting server."""
    brain = GroqBrainEngine.get_instance()
    is_live = brain.set_api_key(request.api_key)
    return {
        "status": "SUCCESS",
        "is_live_available": is_live,
        "model_name": brain.model_name,
        "message": (
            "Live Groq LPU reasoning active."
            if is_live
            else "Groq API key registered, but live connection failed. Edge neural fallback active."
        ),
    }


@router.get("/status")
def get_copilot_status() -> dict[str, Any]:
    """Return Groq LPU inference metrics and engine readiness."""
    brain = GroqBrainEngine.get_instance()
    return {
        "status": "SUCCESS",
        "is_live_available": brain.is_live_available(),
        "model_name": brain.model_name,
        "total_inferences": brain.total_inferences,
        "total_tokens_in": brain.total_tokens_in,
        "total_tokens_out": brain.total_tokens_out,
        "last_latency_ms": brain.last_latency_ms,
        "has_api_key": bool(brain.api_key),
    }
