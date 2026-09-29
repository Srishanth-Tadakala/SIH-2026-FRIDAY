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


# ==============================================================================
# DTN Bundle Protocol Endpoints (RFC 9171 / BPv7)
# ==============================================================================

class DtnSendBundleRequest(BaseModel):
    destination_eid: str = Field(..., description="Destination Endpoint ID (e.g. dtn://ncpor.gov.in/telemetry)")
    payload: Any = Field(..., description="Payload data (dict, list, or string)")
    source_eid: str | None = Field(default=None, description="Optional custom source EID")
    priority: int = Field(default=1, ge=0, le=2, description="Priority: 0=BULK, 1=NORMAL, 2=EXPEDITE_EMERGENCY")
    lifetime_seconds: int = Field(default=86400, ge=60, description="Bundle TTL in seconds")
    custody_transfer_requested: bool = Field(default=True, description="Request custodial handover confirmation")


class DtnContactWindowRequest(BaseModel):
    carrier_eid: str = Field(
        default="dtn://sat.cartosat-2f/transponder01",
        description="Flyby satellite or convoy carrier EID",
    )
    bandwidth_bytes_limit: int = Field(default=5_000_000, description="Max bytes transmittable during pass")
    max_bundles: int = Field(default=50, description="Max bundles to dispatch")


@router.get("/dtn/status")
def get_dtn_agent_status() -> dict[str, Any]:
    """Retrieve operational status, queue counts, and metrics for the DTN Bundle Agent."""
    state = get_server_state()
    if not hasattr(state, "dtn_agent"):
        raise HTTPException(status_code=503, detail="DTN Bundle Agent not initialized.")

    return state.dtn_agent.get_status()


@router.get("/dtn/bundles")
def list_dtn_bundles() -> dict[str, Any]:
    """Inspect queued bundles by priority level."""
    state = get_server_state()
    if not hasattr(state, "dtn_agent"):
        raise HTTPException(status_code=503, detail="DTN Bundle Agent not initialized.")

    agent = state.dtn_agent
    return {
        "local_eid": agent.local_eid,
        "queues": {
            p.name: [b.model_dump() for b in q]
            for p, q in agent._queues.items()
        },
        "delivered_count": len(agent._delivered_bundles),
    }


@router.post("/dtn/send")
def send_dtn_bundle(req: DtnSendBundleRequest) -> dict[str, Any]:
    """Enqueue a new RFC 9171 bundle for store-carry-forward transmission."""
    state = get_server_state()
    if not hasattr(state, "dtn_agent"):
        raise HTTPException(status_code=503, detail="DTN Bundle Agent not initialized.")

    from ...satcom.dtn_bundle import BundlePriority
    priority_enum = BundlePriority(req.priority)

    bundle = state.dtn_agent.create_and_enqueue_bundle(
        destination_eid=req.destination_eid,
        payload=req.payload,
        source_eid=req.source_eid,
        priority=priority_enum,
        lifetime_seconds=req.lifetime_seconds,
        custody_transfer_requested=req.custody_transfer_requested,
    )

    return {
        "status": "QUEUED",
        "bundle_id": bundle.bundle_id,
        "source_eid": bundle.source_eid,
        "destination_eid": bundle.destination_eid,
        "priority": priority_enum.name,
        "payload_size_bytes": bundle.payload_size_bytes,
        "payload_sha256": bundle.payload_sha256,
        "lifetime_seconds": bundle.lifetime_seconds,
    }


@router.post("/dtn/contact-window")
def simulate_dtn_contact_window(req: DtnContactWindowRequest) -> dict[str, Any]:
    """Simulate an opportunistic LEO satellite flyby or convoy contact to flush bundles."""
    state = get_server_state()
    if not hasattr(state, "dtn_agent"):
        raise HTTPException(status_code=503, detail="DTN Bundle Agent not initialized.")

    dispatched = state.dtn_agent.dispatch_contact_window(
        carrier_eid=req.carrier_eid,
        bandwidth_bytes_limit=req.bandwidth_bytes_limit,
        max_bundles=req.max_bundles,
    )

    return {
        "status": "CONTACT_WINDOW_COMPLETED",
        "carrier_eid": req.carrier_eid,
        "dispatched_count": len(dispatched),
        "dispatched_bundles": [
            {
                "bundle_id": b.bundle_id,
                "priority": b.priority.name,
                "destination_eid": b.destination_eid,
                "size_bytes": b.payload_size_bytes,
            }
            for b in dispatched
        ],
    }

