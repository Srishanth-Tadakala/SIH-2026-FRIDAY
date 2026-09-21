"""Database & Distributed Memory API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides endpoints for:
- 2-Step Database Status & Health (Local Station Edge DB & Mainland Cloud Atlas).
- Historical Incident Episodes & Case-Based Reasoning Memory retrieval.
- Digital Twin Equipment Lifecycle Ledger (running hours, wear, maintenance).
- Manual & automated Satcom Store-and-Forward synchronization triggers.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query

from ..state import get_server_state

router = APIRouter(prefix="/api/database", tags=["Database & Distributed Memory"])


@router.get("/status")
def get_database_subsystem_status() -> dict[str, Any]:
    """Retrieve operational status for Local Station DB, Cloud Atlas, and Satcom Sync Worker."""
    state = get_server_state()
    db_status = state.db_manager.get_status()
    sync_metrics = state.db_sync_worker.get_metrics()
    
    return {
        "database": db_status,
        "satcom_synchronizer": sync_metrics,
        "active_station": state.active_station_id,
        "is_polar_blackout": state.orchestrator.edge_blackout_mode,
    }


@router.get("/episodes")
async def list_incident_episodes(
    station_id: str | None = Query(default=None, description="Filter by station ID ('bharati' or 'maitri')"),
    limit: int = Query(default=15, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve historical crisis episodes and case-based precedents."""
    state = get_server_state()
    episodes = await state.episodes_repo.get_recent_episodes(station_id=station_id, limit=limit)
    return [ep.to_dict() for ep in episodes]


@router.get("/episodes/{episode_id}")
async def get_incident_episode(episode_id: str) -> dict[str, Any]:
    """Retrieve full details, context, and lessons learned for a specific episode."""
    state = get_server_state()
    doc = await state.db_manager.find_one_record("station_episodes", {"episode_id": episode_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Episode '{episode_id}' not found.")
    return doc


@router.get("/equipment")
async def list_equipment_lifecycle(
    station_id: str | None = Query(default=None, description="Station ID ('bharati' or 'maitri')"),
) -> list[dict[str, Any]]:
    """Retrieve digital twin equipment lifecycle ledger with running hours and health status."""
    state = get_server_state()
    target_sid = station_id or state.active_station_id
    assets = await state.equipment_repo.get_all_equipment(station_id=target_sid)
    return [a.to_dict() for a in assets]


@router.get("/audits")
async def list_operator_audits(
    station_id: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Retrieve operator action and Tier 3 PIN authorization audits."""
    state = get_server_state()
    audits = await state.audit_repo.get_recent_audits(station_id=station_id, limit=limit)
    return [a.to_dict() for a in audits]


@router.post("/sync")
async def trigger_satcom_sync() -> dict[str, Any]:
    """Manually trigger store-and-forward batch replication to Mainland HQ Cloud Atlas."""
    state = get_server_state()
    synced_count = await state.db_sync_worker.sync_pending_batches()
    metrics = state.db_sync_worker.get_metrics()
    return {
        "status": "SUCCESS",
        "synced_records_count": synced_count,
        "metrics": metrics,
    }
