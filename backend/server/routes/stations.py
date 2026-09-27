"""Station Management API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Handles dual-station metadata (Bharati & Maitri), station switching, and manual clock stepping.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.station_service import StationService, get_station_service
from ..state import get_server_state

router = APIRouter(prefix="/api/stations", tags=["Stations"])


class StepRequest(BaseModel):
    """Simulation clock step parameters."""
    dt_seconds: float = Field(default=1.0, ge=0.1, le=3600.0, description="Step duration in simulation seconds")


@router.get("", response_model=list[dict[str, Any]])
def list_stations(service: StationService = Depends(get_station_service)) -> list[dict[str, Any]]:
    """List all managed Antarctic research stations with real-time health summaries."""
    return service.get_all_stations_summary()


@router.get("/{station_id}")
def get_station_detail(station_id: str, service: StationService = Depends(get_station_service)) -> dict[str, Any]:
    """Retrieve detailed metadata, location, and KPI status for a specific station."""
    try:
        return service.get_station_summary(station_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/active/{station_id}")
def set_active_station(station_id: str, service: StationService = Depends(get_station_service)) -> dict[str, Any]:
    """Switch the active station context for the cognitive agent society."""
    try:
        active_id = service.set_active_station(station_id)
        return {
            "status": "SUCCESS",
            "active_station_id": active_id,
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


@router.get("/{station_id}/telemetry")
def get_station_telemetry(station_id: str) -> dict[str, Any]:
    """Retrieve full live telemetry snapshot for a specific Antarctic station."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    engine = state.stations[sid]
    snapshot = engine.get_snapshot()
    return snapshot.to_dict()


@router.get("/{station_id}/health")
def get_station_health(station_id: str) -> dict[str, Any]:
    """Retrieve operational health, risk indices, and SCADA connectivity for a station."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    engine = state.stations[sid]
    snapshot = engine.get_snapshot()
    kpis = snapshot.kpis

    risk_score = kpis.get("composite_risk_score", 0.0)
    health_pct = max(0.0, min(100.0, round((1.0 - (risk_score / 100.0)) * 100, 1)))

    return {
        "station_id": sid,
        "station_name": engine.station_name,
        "health_percentage": health_pct,
        "composite_risk_score": risk_score,
        "operational_status": "NORMAL" if risk_score < 40 else ("WARNING" if risk_score < 70 else "CRITICAL"),
        "subsystems": {
            "energy": "NORMAL" if kpis.get("indoor_avg_temp_c", 20.0) > 10.0 else "WARNING",
            "thermal": "NORMAL" if kpis.get("indoor_avg_temp_c", 20.0) > 15.0 else "WARNING",
            "life_support": "NORMAL" if kpis.get("air_quality_index", 30) < 80 else "WARNING",
            "satcom": "NORMAL" if state.satcom_service.active_profile.name != "POLAR_BLACKOUT" else "DEGRADED",
        },
        "telemetry_source": "SIMULATED_TWIN" if getattr(engine, "is_simulation", True) else "PHYSICAL_SCADA",
        "last_updated_utc": snapshot.timestamp_iso,
    }


@router.get("/{station_id}/alerts")
def get_station_alerts(station_id: str) -> list[dict[str, Any]]:
    """Retrieve active life-safety and operational alerts for a station."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    engine = state.stations[sid]
    return engine.get_active_alerts()
