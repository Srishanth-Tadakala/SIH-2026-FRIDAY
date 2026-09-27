"""Dedicated Health Probes and Observability Endpoints for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import time
from typing import Any, Dict
from fastapi import APIRouter, Response, status

from ..state import get_server_state

router = APIRouter(tags=["System Health & Observability"])


@router.get("/health/liveness", summary="Kubernetes / Docker Liveness Probe")
def liveness_probe() -> dict[str, str]:
    """Basic liveness probe checking that the application process is alive."""
    return {"status": "ALIVE", "timestamp": str(time.time())}


@router.get("/health/readiness", summary="Subsystem Readiness Probe")
def readiness_probe(response: Response) -> dict[str, Any]:
    """Comprehensive readiness probe checking digital twin, agent bus, and persistence subsystems."""
    state = get_server_state()
    checks: Dict[str, Any] = {}
    all_ready = True

    # 1. Digital Twin Engines
    bharati_ok = "bharati" in state.stations and state.stations["bharati"].sensor_count == 505
    maitri_ok = "maitri" in state.stations and state.stations["maitri"].sensor_count == 505
    checks["digital_twin_engines"] = {
        "ready": bharati_ok and maitri_ok,
        "bharati_sensors": state.stations["bharati"].sensor_count if "bharati" in state.stations else 0,
        "maitri_sensors": state.stations["maitri"].sensor_count if "maitri" in state.stations else 0,
    }
    if not (bharati_ok and maitri_ok):
        all_ready = False

    # 2. Agent Message Bus
    bus_ready = state.bus is not None and hasattr(state.bus, "publish")
    checks["agent_message_bus"] = {
        "ready": bus_ready,
        "queued_messages": len(state.bus._message_history) if bus_ready else 0,
    }
    if not bus_ready:
        all_ready = False

    # 3. Satcom Emulators & Sync
    satcom_ready = len(state.satcom_emulators) > 0 and state.db_sync_worker is not None
    checks["satcom_sync_worker"] = {
        "ready": satcom_ready,
        "emulators_active": len(state.satcom_emulators),
        "is_running": state.db_sync_worker.is_running if state.db_sync_worker else False,
    }
    if not satcom_ready:
        all_ready = False

    # 4. Database Connection / Fallback
    db_ready = state.db_manager is not None and state.db_manager.is_initialized
    checks["database_persistence"] = {
        "ready": db_ready,
        "is_fallback_active": state.db_manager.is_fallback_active if state.db_manager else True,
    }
    if not db_ready:
        all_ready = False

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "READY" if all_ready else "DEGRADED",
        "timestamp": time.time(),
        "uptime_seconds": round(time.time() - state.server_start_time, 2),
        "subsystems": checks,
    }


@router.get("/api/health/metrics", summary="Station Telemetry & Platform Metrics")
def operational_metrics() -> dict[str, Any]:
    """Expose runtime metrics for monitoring dashboards."""
    state = get_server_state()
    engine = state.get_engine()
    kpis = engine.get_station_kpis()

    return {
        "uptime_seconds": round(time.time() - state.server_start_time, 2),
        "active_station": state.active_station_id,
        "total_stations": len(state.stations),
        "sensor_count": engine.sensor_count,
        "agent_count": 10,
        "sim_elapsed_seconds": engine.clock.elapsed_seconds,
        "sim_clock_iso": engine.clock.isoformat(),
        "safety_lockout_active": time.time() < state.safety_interlock._lockout_until,
        "pending_tier3_count": len(state.safety_interlock._pending_tier3_queue),
        "power_load_kw": kpis.get("active_load_kw", 0.0),
        "indoor_temp_c": kpis.get("indoor_temp_c", 0.0),
        "grid_frequency_hz": kpis.get("grid_frequency_hz", 50.0),
        "bus_history_depth": len(state.bus._message_history),
    }
