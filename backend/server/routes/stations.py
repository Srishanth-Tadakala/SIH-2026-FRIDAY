"""Station Management API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Handles dual-station metadata (Bharati & Maitri), station switching, and manual clock stepping.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..state import get_server_state

router = APIRouter(prefix="/api/stations", tags=["Stations"])


class StepRequest(BaseModel):
    """Simulation clock step parameters."""
    dt_seconds: float = Field(default=1.0, ge=0.1, le=3600.0, description="Step duration in simulation seconds")


@router.get("", response_model=list[dict[str, Any]])
def list_stations() -> list[dict[str, Any]]:
    """List all managed Antarctic research stations with real-time health summaries."""
    state = get_server_state()
    return state.get_all_stations_summary()


@router.get("/{station_id}")
def get_station_detail(station_id: str) -> dict[str, Any]:
    """Retrieve detailed metadata, location, and KPI status for a specific station."""
    state = get_server_state()
    try:
        return state.get_station_summary(station_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/active/{station_id}")
def set_active_station(station_id: str) -> dict[str, Any]:
    """Switch the active station context for the cognitive agent society."""
    state = get_server_state()
    try:
        state.set_active_station(station_id)
        return {
            "status": "SUCCESS",
            "active_station_id": state.active_station_id,
            "message": f"Active station switched to {station_id.upper()}",
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{station_id}/step")
def step_station_clock(station_id: str, req: StepRequest | None = None) -> dict[str, Any]:
    """Advance the station digital twin simulation clock forward by dt_seconds."""
    state = get_server_state()
    dt = req.dt_seconds if req is not None else 1.0
    try:
        snapshot = state.step(station_id=station_id, dt_seconds=dt)
        return {
            "status": "SUCCESS",
            "station_id": station_id,
            "sim_time_seconds": snapshot.sim_time_seconds,
            "timestamp_iso": snapshot.timestamp_iso,
            "kpis": snapshot.kpis,
            "alerts": snapshot.alerts,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
