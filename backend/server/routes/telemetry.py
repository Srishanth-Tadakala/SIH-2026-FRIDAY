"""Telemetry API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides granular 4-pillar telemetry, full snapshots, individual sensor lookups,
alerts, and historical time-series data for station dashboards.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query

from ..state import get_server_state

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/{station_id}/snapshot")
def get_station_snapshot(station_id: str) -> dict[str, Any]:
    """Retrieve full digital twin snapshot for a station including all 505 sensor readings."""
    state = get_server_state()
    try:
        engine = state.get_engine(station_id)
        snap = engine.get_snapshot()
        return {
            "station_id": snap.station_id,
            "timestamp_iso": snap.timestamp_iso,
            "sim_time_seconds": snap.sim_time_seconds,
            "active_scenario": snap.active_scenario,
            "sensor_count": snap.sensor_count,
            "kpis": snap.kpis,
            "alerts": snap.alerts,
            "readings": snap.readings,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{station_id}/kpis")
def get_station_kpis(station_id: str) -> dict[str, Any]:
    """Retrieve aggregated high-level KPIs (generation, load, temperatures, autonomy, risk)."""
    state = get_server_state()
    try:
        engine = state.get_engine(station_id)
        return {
            "station_id": engine.station_id,
            "timestamp_iso": engine.clock.isoformat(),
            "sim_time_seconds": engine.clock.elapsed_seconds,
            "kpis": engine.get_station_kpis(),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{station_id}/alerts")
def get_station_alerts(station_id: str) -> dict[str, Any]:
    """Retrieve all currently active operational and life-safety alerts."""
    state = get_server_state()
    try:
        engine = state.get_engine(station_id)
        alerts = engine.get_active_alerts()
        return {
            "station_id": engine.station_id,
            "alert_count": len(alerts),
            "alerts": alerts,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{station_id}/pillars/{pillar}")
def get_pillar_telemetry(station_id: str, pillar: str) -> dict[str, Any]:
    """Retrieve filtered sensor readings for a specific pillar (energy, infrastructure, environment, logistics)."""
    state = get_server_state()
    try:
        engine = state.get_engine(station_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    p = pillar.lower()
    if p == "energy":
        readings = engine.energy_registry.read_all()
    elif p in ("infrastructure", "infra"):
        readings = engine.infra_registry.read_all()
    elif p in ("environment", "env"):
        readings = engine.env_registry.read_all()
    elif p in ("logistics", "log"):
        readings = engine.logistics_registry.read_all()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown pillar '{pillar}'. Valid pillars: energy, infrastructure, environment, logistics",
        )

    return {
        "station_id": engine.station_id,
        "pillar": p,
        "sensor_count": len(readings),
        "readings": readings,
    }


@router.get("/{station_id}/sensors/{sensor_id}")
def get_sensor_reading(station_id: str, sensor_id: str) -> dict[str, Any]:
    """Lookup an individual sensor reading across all 4 pillars in O(1) time."""
    state = get_server_state()
    try:
        engine = state.get_engine(station_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        reading = engine.get_sensor_reading(sensor_id)
        if hasattr(reading, "to_dict"):
            data = reading.to_dict()
        elif hasattr(reading, "__dict__"):
            data = dict(reading.__dict__)
        else:
            data = {"value": reading}
        return {
            "station_id": engine.station_id,
            "sensor_id": sensor_id,
            "reading": data,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{station_id}/history")
def get_station_history(station_id: str, limit: int = Query(default=60, ge=1, le=120)) -> dict[str, Any]:
    """Retrieve sliding time-series history of KPIs and alert counts for trending."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.history:
        raise HTTPException(status_code=404, detail=f"Station '{sid}' not found.")

    items = list(state.history[sid])
    return {
        "station_id": sid,
        "count": min(len(items), limit),
        "history": items[-limit:],
    }
