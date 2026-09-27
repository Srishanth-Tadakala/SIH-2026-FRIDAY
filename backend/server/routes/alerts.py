"""Operational Life-Safety Alerts API Router for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides real-time and historical operational alerts from the digital twin and multi-agent society.
"""

from __future__ import annotations

import time
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import User, get_current_user
from ..state import get_server_state

router = APIRouter(prefix="/api/alerts", tags=["Alerts & Alarms"])

# In-memory acknowledgment registry: alert_id -> { acknowledged_by, timestamp_utc }
_acknowledged_alerts: dict[str, dict[str, Any]] = {}


class AcknowledgeAlertPayload(BaseModel):
    note: str = Field(default="", description="Operator acknowledgment note")


@router.get("")
def list_active_alerts(
    station_id: str | None = Query(default=None, description="Station ID ('bharati' or 'maitri')"),
    severity: str | None = Query(default=None, description="Filter by severity ('CRITICAL', 'WARNING', 'EMERGENCY')"),
) -> list[dict[str, Any]]:
    """Retrieve all currently active operational and life-safety alerts across stations."""
    state = get_server_state()
    stations_to_check = [station_id.lower()] if station_id else list(state.stations.keys())

    all_alerts: list[dict[str, Any]] = []

    for sid in stations_to_check:
        if sid not in state.stations:
            continue
        engine = state.stations[sid]
        raw_alerts = engine.get_active_alerts()
        snapshot = engine.get_snapshot()

        for idx, a in enumerate(raw_alerts):
            subsystem = a.get("subsystem", "GENERAL")
            sev = a.get("severity", "WARNING").upper()
            msg = a.get("message", "")

            # Deterministic alert ID based on station, subsystem, and symptom
            alert_id = f"ALT-{sid[:2].upper()}-{subsystem[:4].upper()}-{abs(hash(msg)) % 10000:04d}"

            # Check if acknowledged
            ack_info = _acknowledged_alerts.get(alert_id)

            if severity and sev != severity.upper():
                continue

            all_alerts.append({
                "id": alert_id,
                "station_id": sid,
                "station_name": engine.station_name,
                "timestamp": snapshot.timestamp_iso,
                "severity": sev,
                "source": subsystem,
                "message": msg,
                "status": "ACKNOWLEDGED" if ack_info else "ACTIVE",
                "acknowledged_by": ack_info.get("acknowledged_by") if ack_info else None,
                "acknowledged_at": ack_info.get("timestamp_utc") if ack_info else None,
                "related_agent": "SITUATION_AWARENESS" if sev == "WARNING" else "DIAGNOSTIC",
                "related_telemetry": {
                    "sim_time_seconds": snapshot.sim_time_seconds,
                    "indoor_temp_c": snapshot.kpis.get("indoor_avg_temp_c"),
                    "ambient_temp_c": snapshot.kpis.get("ambient_temp_c"),
                    "wind_speed_mps": snapshot.kpis.get("wind_speed_mps"),
                    "composite_risk_score": snapshot.kpis.get("composite_risk_score"),
                },
            })

    return all_alerts


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    payload: AcknowledgeAlertPayload | None = None,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Acknowledge an active life-safety alert with operator credentials."""
    _acknowledged_alerts[alert_id] = {
        "acknowledged_by": current_user.username,
        "note": payload.note if payload else "",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return {
        "status": "SUCCESS",
        "alert_id": alert_id,
        "acknowledged": True,
        "operator": current_user.username,
        "timestamp": _acknowledged_alerts[alert_id]["timestamp_utc"],
    }


@router.get("/summary")
def get_alerts_summary(
    station_id: str | None = Query(default=None),
) -> dict[str, Any]:
    """Get aggregated alert metrics (total active, critical, warning, unacknowledged)."""
    active_alerts = list_active_alerts(station_id=station_id)
    critical_count = sum(1 for a in active_alerts if a["severity"] in ("CRITICAL", "EMERGENCY"))
    warning_count = sum(1 for a in active_alerts if a["severity"] == "WARNING")
    unack_count = sum(1 for a in active_alerts if a["status"] == "ACTIVE")

    return {
        "total_active_alerts": len(active_alerts),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "unacknowledged_count": unack_count,
        "alerts": active_alerts,
    }
