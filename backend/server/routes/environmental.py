"""Polar Environmental & Space Weather API Endpoints for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides REST interfaces for:
- Live NOAA Space Weather (Kp index, G/S/R scales, solar wind speed, IMF Bz)
- Polar Cap Absorption (PCA) & Satcom HF Attenuation Warnings
- Simulated Geomagnetic Storm Scenarios for emergency validation drills
"""

from __future__ import annotations

import time
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..state import get_server_state

router = APIRouter(prefix="/api/environmental", tags=["Polar Environment & Space Weather"])


class StormSimulationRequest(BaseModel):
    g_level: str = Field(
        default="G4",
        description="Geomagnetic storm level: G1 (Minor), G2 (Moderate), G3 (Strong), G4 (Severe), G5 (Extreme)",
    )


@router.get("/space-weather/current")
def get_current_space_weather() -> dict[str, Any]:
    """Retrieve the latest space weather metrics and calculated polar absorption risk."""
    server_state = get_server_state()
    if not hasattr(server_state, "space_weather_engine"):
        raise HTTPException(status_code=503, detail="Space weather engine not initialized.")

    metrics = server_state.space_weather_engine.get_latest_metrics()
    return metrics.model_dump()


@router.get("/space-weather/status")
def get_space_weather_engine_status() -> dict[str, Any]:
    """Return operational diagnostics, poll counts, and NOAA SWPC connection health."""
    server_state = get_server_state()
    if not hasattr(server_state, "space_weather_engine"):
        raise HTTPException(status_code=503, detail="Space weather engine not initialized.")

    return server_state.space_weather_engine.get_status()


@router.post("/space-weather/poll")
async def trigger_space_weather_poll() -> dict[str, Any]:
    """Trigger an immediate live poll from NOAA SWPC (or synthetic baseline fallback)."""
    server_state = get_server_state()
    if not hasattr(server_state, "space_weather_engine"):
        raise HTTPException(status_code=503, detail="Space weather engine not initialized.")

    metrics = await server_state.space_weather_engine.poll_now()
    return {
        "status": "SUCCESS",
        "timestamp": time.time(),
        "metrics": metrics.model_dump(),
    }


@router.post("/space-weather/simulate-storm")
def simulate_geomagnetic_storm(payload: StormSimulationRequest) -> dict[str, Any]:
    """Inject a simulated geomagnetic storm scenario (G1-G5) to test satcom and station governors."""
    server_state = get_server_state()
    if not hasattr(server_state, "space_weather_engine"):
        raise HTTPException(status_code=503, detail="Space weather engine not initialized.")

    valid_levels = ("G1", "G2", "G3", "G4", "G5")
    if payload.g_level.upper() not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid storm level: {payload.g_level}. Must be one of: {valid_levels}",
        )

    storm_metrics = server_state.space_weather_engine.simulate_geomagnetic_storm(payload.g_level)
    return {
        "status": "STORM_INJECTED",
        "scenario": payload.g_level.upper(),
        "timestamp": time.time(),
        "metrics": storm_metrics.model_dump(),
    }
