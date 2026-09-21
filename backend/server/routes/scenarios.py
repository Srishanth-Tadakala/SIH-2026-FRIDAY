"""Scenario Injection API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Allows operator and automated testing of crisis disturbance scenarios (Katabatic Blizzards,
Generator Trips, Utilidor Freezes, etc.) across the digital twin.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.engine import MasterScenario
from ..state import get_server_state

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


class ScenarioInjectRequest(BaseModel):
    """Payload to trigger a physical station disturbance scenario."""
    scenario: str = Field(..., description="Scenario identifier (e.g. BLIZZARD_STRIKE, GENERATOR_TRIP)")
    station_id: str | None = Field(default=None, description="Target station ID ('bharati' or 'maitri')")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Custom physical override parameters")


class ScenarioClearRequest(BaseModel):
    """Payload to clear disturbances and restore nominal station operation."""
    station_id: str | None = Field(default=None, description="Target station ID to reset")


@router.get("", response_model=list[dict[str, Any]])
def list_available_scenarios() -> list[dict[str, Any]]:
    """List all available physical and operational scenarios supported by the digital twin."""
    descriptions = {
        MasterScenario.NORMAL: "Baseline steady-state operation across all 4 pillars.",
        MasterScenario.BLIZZARD_STRIKE: "Extreme katabatic blizzard: 140 km/h winds, -32°C, whiteout visibility, snow drift.",
        MasterScenario.GENERATOR_TRIP: "Instantaneous generator mechanical/electrical trip requiring standby dispatch.",
        MasterScenario.WATER_LINE_FREEZE: "Trace heating failure and sub-zero freeze on utilidor water supply line.",
        MasterScenario.COLD_CHAIN_EXCURSION: "Refrigeration compressor failure on Reefer-01 food storage container.",
        MasterScenario.FUEL_TRANSFER_LEAK: "Bulk fuel transfer pump failure and day-tank supply restriction.",
        MasterScenario.HEAVY_CARGO_OPERATION: "Active marine offloading at Quilty Bay with Mantis crane and PistenBully haulage.",
        MasterScenario.MISSION_FIELD_DEPLOYMENT: "Long-range science traverse deployed onto the Polar Plateau.",
    }

    return [
        {
            "scenario": sc.value,
            "name": sc.value.replace("_", " ").title(),
            "description": descriptions.get(sc, ""),
        }
        for sc in MasterScenario
    ]


@router.post("/inject")
def inject_scenario(req: ScenarioInjectRequest) -> dict[str, Any]:
    """Inject a physical crisis scenario into the digital twin and trigger the deliberation loop."""
    state = get_server_state()

    try:
        scenario_enum = MasterScenario(req.scenario.upper())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{req.scenario}'. Valid scenarios: {[s.value for s in MasterScenario]}",
        )

    try:
        snapshot = state.inject_scenario(
            scenario=scenario_enum,
            station_id=req.station_id,
            **req.parameters,
        )
        return {
            "status": "SUCCESS",
            "station_id": snapshot.station_id,
            "active_scenario": snapshot.active_scenario,
            "sim_time_seconds": snapshot.sim_time_seconds,
            "timestamp_iso": snapshot.timestamp_iso,
            "kpis": snapshot.kpis,
            "active_alerts": snapshot.alerts,
            "active_sessions_count": len(state.bus.get_active_sessions()),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/inject/{station_id}")
def inject_scenario_with_station(station_id: str, req: ScenarioInjectRequest) -> dict[str, Any]:
    """Inject scenario into specific station provided via URL path."""
    req.station_id = station_id
    return inject_scenario(req)


@router.post("/clear")
def clear_scenario(req: ScenarioClearRequest | None = None) -> dict[str, Any]:
    """Reset station to nominal baseline and restore healthy telemetry."""
    state = get_server_state()
    target_sid = req.station_id if req is not None else None

    try:
        snapshot = state.clear_scenario(station_id=target_sid)
        return {
            "status": "SUCCESS",
            "station_id": snapshot.station_id,
            "active_scenario": snapshot.active_scenario,
            "sim_time_seconds": snapshot.sim_time_seconds,
            "message": "Station successfully restored to NORMAL baseline.",
            "kpis": snapshot.kpis,
            "active_alerts": snapshot.alerts,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/clear/{station_id}")
def clear_scenario_with_station(station_id: str, req: ScenarioClearRequest | None = None) -> dict[str, Any]:
    """Reset specific station provided via URL path to nominal baseline."""
    req = req or ScenarioClearRequest(station_id=station_id)
    req.station_id = station_id
    return clear_scenario(req)
