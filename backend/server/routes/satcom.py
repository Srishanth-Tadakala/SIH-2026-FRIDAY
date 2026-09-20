"""Satcom Bandwidth-Aware Synchronization API Endpoints.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Provides:
- Channel profile configuration (LAN, Inmarsat 64k, Iridium 9.6k, Blackout 0k).
- Real-time bandwidth savings and compression ratios.
- Mainland mirror digital twin state inspection and checksum verification.
- Blackout prioritized spool queue recovery and resync triggering.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..state import get_server_state

router = APIRouter(prefix="/api/satcom", tags=["Polar Satcom Sync"])


class ProfileChangeRequest(BaseModel):
    profile: str = Field(
        ...,
        description="Target profile: LAN_DIRECT, INMARSAT_STANDARD, IRIDIUM_LOW, POLAR_BLACKOUT",
    )
    station_id: str | None = Field(
        default=None,
        description="Optional station ID ('bharati' or 'maitri'). If omitted, applies to all.",
    )


class SyncTriggerRequest(BaseModel):
    force_keyframe: bool = Field(
        default=False,
        description="If True, forces transmission of a full 505-sensor baseline keyframe.",
    )


class RecoveryRequest(BaseModel):
    new_profile: str = Field(
        default="INMARSAT_STANDARD",
        description="Profile to restore connection to (e.g. INMARSAT_STANDARD, LAN_DIRECT).",
    )


@router.get("/status")
def get_all_satcom_status() -> dict[str, Any]:
    """Retrieve satcom channel metrics, bandwidth savings, and mirror sync for all stations."""
    state = get_server_state()
    stations_data = {}
    for sid in state.stations.keys():
        stations_data[sid] = state.get_satcom_summary(sid)

    return {
        "status": "ONLINE",
        "system": "Polar Satcom Bandwidth-Aware Telemetry Engine",
        "managed_stations": stations_data,
    }


@router.get("/{station_id}/summary")
def get_station_satcom_summary(station_id: str) -> dict[str, Any]:
    """Retrieve detailed satcom telemetry and mirror twin state for a specific station."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(
            status_code=404,
            detail=f"Station '{sid}' not found. Valid stations: {list(state.stations.keys())}",
        )
    return state.get_satcom_summary(sid)


@router.get("/{station_id}/mirror")
def get_mainland_mirror_twin(station_id: str) -> dict[str, Any]:
    """Retrieve the Mainland Mirror Twin state (reconstructed at NCPOR Goa HQ)."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.mainland_mirrors:
        raise HTTPException(status_code=404, detail=f"Station '{sid}' not found.")

    mirror = state.mainland_mirrors[sid]
    return {
        "station_id": sid,
        "sync_status": mirror.sync_status,
        "is_synchronized": mirror.is_synchronized(),
        "last_seq_num": mirror.last_seq_num,
        "last_sim_time_seconds": mirror.last_sim_time_seconds,
        "sensor_count": len(mirror.get_all_readings()),
        "state_checksum": mirror.get_state_checksum(),
        "kpis": mirror.get_kpis(),
        "alerts": mirror.get_alerts(),
        "readings": mirror.get_all_readings(),
        "total_frames_received": mirror.total_frames_received,
        "lost_frames_count": mirror.lost_frames_count,
    }


@router.post("/profile")
def set_satcom_profile(req: ProfileChangeRequest) -> dict[str, Any]:
    """Update active polar satcom profile (e.g. inject blackout or switch to Inmarsat)."""
    state = get_server_state()
    valid_profiles = ["LAN_DIRECT", "INMARSAT_STANDARD", "IRIDIUM_LOW", "POLAR_BLACKOUT"]
    if req.profile.upper() not in valid_profiles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid profile '{req.profile}'. Valid profiles: {valid_profiles}",
        )

    state.set_satcom_profile(req.profile.upper(), station_id=req.station_id)
    return {
        "status": "SUCCESS",
        "new_profile": req.profile.upper(),
        "target_station": req.station_id or "ALL_STATIONS",
    }


@router.post("/{station_id}/sync")
def trigger_satcom_sync(station_id: str, req: SyncTriggerRequest) -> dict[str, Any]:
    """Trigger manual satcom frame encoding, compression, transmission, and mainland mirror sync."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{sid}' not found.")

    frame, tx_stats = state.sync_station_telemetry(sid, force_keyframe=req.force_keyframe)
    return {
        "station_id": sid,
        "frame_id": frame.frame_id,
        "frame_type": frame.frame_type.value,
        "seq_num": frame.seq_num,
        "delta_count": frame.delta_count,
        "total_sensors": frame.total_sensors,
        "tx_stats": tx_stats,
    }


@router.post("/{station_id}/recover")
def recover_satcom_blackout(station_id: str, req: RecoveryRequest) -> dict[str, Any]:
    """Drain spooled blackout queue and synchronize Mainland Mirror Twin upon link recovery."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{sid}' not found.")

    applied_summaries = state.recover_satcom_blackout(sid, new_profile=req.new_profile)
    mirror = state.mainland_mirrors[sid]

    return {
        "station_id": sid,
        "recovered_frames_count": len(applied_summaries),
        "drained_frames": applied_summaries,
        "new_profile": req.new_profile,
        "mirror_sync_status": mirror.sync_status,
        "is_synchronized": mirror.is_synchronized(),
    }


@router.post("/{station_id}/resync")
def trigger_keyframe_resync(station_id: str) -> dict[str, Any]:
    """Force transmission of a full 505-sensor baseline keyframe to heal sequence gaps."""
    state = get_server_state()
    sid = station_id.lower()
    if sid not in state.stations:
        raise HTTPException(status_code=404, detail=f"Station '{sid}' not found.")

    frame, tx_stats = state.sync_station_telemetry(sid, force_keyframe=True)
    mirror = state.mainland_mirrors[sid]

    return {
        "station_id": sid,
        "status": "RESYNCHRONIZED",
        "frame_id": frame.frame_id,
        "seq_num": frame.seq_num,
        "sensor_count": len(mirror.get_all_readings()),
        "mirror_sync_status": mirror.sync_status,
        "is_synchronized": mirror.is_synchronized(),
        "state_checksum": mirror.get_state_checksum(),
        "tx_stats": tx_stats,
    }
