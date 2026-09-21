"""Unit tests for F.R.I.D.A.Y. 2-Step Distributed Database & Cognitive Memory System.

Tests:
1. DatabaseManager connection probing and dual-mode resilient storage.
2. EpisodesRepository: seeding historical cases, CBR lookup, lifecycle logging.
3. EquipmentRepository: asset lifecycle, running hours accumulation, wear tracking.
4. DialogueRepository: inter-agent dialogue audit trail logging.
5. AuditRepository: commander override and autonomous safety actuation audits.
6. SatcomDatabaseSyncWorker: store-and-forward sync under nominal and blackout conditions.
"""

import asyncio
import pytest
from datetime import datetime, timezone

from backend.database.connection import DatabaseManager
from backend.database.models import (
    EpisodeRecord,
    DialogueRecord,
    EquipmentLifecycleRecord,
    OperatorAuditRecord,
    SyncStatus,
)
from backend.database.repositories.episodes_repo import EpisodesRepository
from backend.database.repositories.equipment_repo import EquipmentRepository
from backend.database.repositories.dialogue_repo import DialogueRepository
from backend.database.repositories.audit_repo import AuditRepository
from backend.database.sync_worker import SatcomDatabaseSyncWorker


@pytest.mark.asyncio
async def test_database_manager_resilience_and_crud():
    """Test DatabaseManager initializes, falls back cleanly to embedded store, and executes CRUD."""
    db = DatabaseManager()
    await db.probe_connections()

    # Verify status report contains required keys
    status = db.get_status()
    assert "local_station_db" in status
    assert "mainland_cloud_db" in status
    assert "distributed_sync" in status

    # Test insert
    test_doc = {"test_id": "T001", "name": "Bharati Sensor Grid", "value": 42.0}
    doc_id = await db.insert_record("test_col", test_doc)
    assert doc_id is not None

    # Test count
    count = await db.count_records("test_col")
    assert count >= 1

    # Test find
    records = await db.find_records("test_col", filter_dict={"test_id": "T001"})
    assert len(records) == 1
    assert records[0]["name"] == "Bharati Sensor Grid"
    assert records[0]["value"] == 42.0

    # Test update
    updated = await db.update_record(
        "test_col",
        filter_dict={"test_id": "T001"},
        update_dict={"$set": {"value": 99.0}},
    )
    assert updated is True

    records_after = await db.find_records("test_col", filter_dict={"test_id": "T001"})
    assert records_after[0]["value"] == 99.0


@pytest.mark.asyncio
async def test_episodes_repo_cbr_and_lifecycle():
    """Test EpisodesRepository seeding, Case-Based Reasoning query, and lifecycle finalization."""
    db = DatabaseManager()
    repo = EpisodesRepository(db)

    # 1. Seed baseline precedents
    await repo.initialize_precedents()
    all_eps = await repo.get_recent_episodes()
    assert len(all_eps) >= 3

    # 2. Case-Based Reasoning lookup for GENERATOR_TRIP
    similar = await repo.find_similar_episodes(
        incident_type="GENERATOR_TRIP",
        ambient_temp_c=-30.0,
        limit=2,
    )
    assert len(similar) >= 1
    assert similar[0].incident_type == "GENERATOR_TRIP"
    assert "chp_1" in similar[0].root_cause_diagnosis.get("isolated_component", "")
    assert "lessons_learned" in similar[0].to_dict()

    # 3. Create a new incident episode
    new_ep = EpisodeRecord(
        session_id="SES-TEST-999",
        station_id="bharati",
        incident_type="UTILIDOR_PIPE_FREEZE_RISK",
        severity="CRITICAL",
        start_sim_time=100.0,
        environmental_context={"ambient_temp_c": -35.0, "wind_speed_mps": 30.0},
        initial_kpis={"total_generation_kw": 120.0, "indoor_temp_c": 18.0},
    )
    await repo.save_episode(new_ep)

    # 4. Finalize episode with consensus plan and lessons learned
    finalized = await repo.finalize_episode(
        session_id="SES-TEST-999",
        consensus_plan={"plan_title": "Auxiliary Trace Heat Flush", "tier": "TIER_1"},
        outcome={"status": "RESOLVED_SUCCESSFULLY", "recovery_duration_sec": 120.0},
        lessons_learned="Recirculation flush rapidly restored flow velocity before freezing.",
        end_sim_time=220.0,
    )
    assert finalized is True

    # 5. Verify update
    updated_ep = await repo.find_similar_episodes("UTILIDOR_PIPE_FREEZE_RISK", limit=1)
    assert len(updated_ep) >= 1


@pytest.mark.asyncio
async def test_equipment_repo_lifecycle_and_wear():
    """Test EquipmentRepository asset seeding and runtime accumulation."""
    db = DatabaseManager()
    repo = EquipmentRepository(db)

    # Seed assets for Bharati
    await repo.initialize_station_assets("bharati")
    assets = await repo.get_all_assets("bharati")
    assert len(assets) >= 5

    chp1 = await repo.get_asset("chp_1", "bharati")
    assert chp1 is not None
    initial_hours = chp1.total_running_hours

    # Accumulate 3600 seconds (1.0 hour) of operation
    await repo.accumulate_runtime("chp_1", "bharati", dt_seconds=3600.0, is_running=True)

    chp1_after = await repo.get_asset("chp_1", "bharati")
    assert chp1_after is not None
    assert chp1_after.total_running_hours == pytest.approx(initial_hours + 1.0, 0.01)
    assert chp1_after.sync_status == SyncStatus.PENDING_HQ_SYNC


@pytest.mark.asyncio
async def test_dialogue_and_audit_repositories():
    """Test inter-agent dialogue message logging and operator audit ledger."""
    db = DatabaseManager()
    diag_repo = DialogueRepository(db)
    audit_repo = AuditRepository(db)

    # Test Dialogue logging
    d_msg = DialogueRecord(
        session_id="SES-TEST-001",
        station_id="bharati",
        sim_time_seconds=45.0,
        sender="SITUATION_AWARENESS",
        recipient="DIAGNOSTIC",
        message_type="ALERT",
        severity="WARNING",
        confidence=0.92,
        payload={"sensor": "temp_water_utilidor", "observed": 1.2},
    )
    d_id = await diag_repo.log_message(d_msg)
    assert d_id is not None

    recent_dialogues = await diag_repo.get_recent_dialogues(session_id="SES-TEST-001")
    assert len(recent_dialogues) >= 1
    assert recent_dialogues[0].sender == "SITUATION_AWARENESS"

    # Test Audit logging
    a_rec = OperatorAuditRecord(
        action_type="COMMANDER_OVERRIDE",
        operator_id="COMMANDER",
        station_id="bharati",
        authorized=True,
        details="Manual Heat Exchanger Bypass to prevent thermal stagnation in loop B.",
        target_component="heat_exchanger_bypass_valve",
    )
    a_id = await audit_repo.log_audit(a_rec)
    assert a_id is not None

    recent_audits = await audit_repo.get_recent_audits(limit=5)
    assert len(recent_audits) >= 1
    assert recent_audits[0].action_type == "COMMANDER_OVERRIDE"
    assert recent_audits[0].authorized is True


@pytest.mark.asyncio
async def test_satcom_store_and_forward_sync_worker():
    """Test SatcomDatabaseSyncWorker store-and-forward batch replication."""
    db = DatabaseManager()
    ep_repo = EpisodesRepository(db)
    await ep_repo.initialize_precedents()

    # Create a pending episode
    ep = EpisodeRecord(
        session_id="SES-SYNC-TEST",
        station_id="bharati",
        incident_type="BLIZZARD_STRIKE",
        severity="WARNING",
        start_sim_time=0.0,
        sync_status=SyncStatus.PENDING_HQ_SYNC,
    )
    await ep_repo.save_episode(ep)

    # Scenario A: Polar Blackout (0 kbps link)
    is_connected = False
    worker = SatcomDatabaseSyncWorker(
        db_manager=db,
        is_link_connected_fn=lambda: is_connected,
        sync_interval_seconds=1.0,
    )

    stats_blackout = await worker.sync_pending_records_now()
    assert stats_blackout["synced_count"] == 0
    assert stats_blackout["pending_count"] >= 1
    assert stats_blackout["link_connected"] is False

    # Scenario B: Satcom Link Restored
    is_connected = True
    stats_restored = await worker.sync_pending_records_now()
    assert stats_restored["link_connected"] is True
    assert stats_restored["synced_count"] >= 1


def test_database_api_routes():
    """Test FastAPI REST endpoints for Database & Cognitive Memory subsystem."""
    from fastapi.testclient import TestClient
    from backend.server.app import create_app
    from backend.server.state import reset_server_state

    reset_server_state(seed=42)
    app = create_app()
    client = TestClient(app)

    # 1. Test /api/database/status
    res_status = client.get("/api/database/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "database" in data_status
    assert "satcom_synchronizer" in data_status
    assert "active_station" in data_status

    # 2. Test /api/database/episodes
    res_episodes = client.get("/api/database/episodes")
    assert res_episodes.status_code == 200
    data_episodes = res_episodes.json()
    assert isinstance(data_episodes, list)

    # 3. Test /api/database/equipment
    res_eq = client.get("/api/database/equipment?station_id=bharati")
    assert res_eq.status_code == 200
    data_eq = res_eq.json()
    assert isinstance(data_eq, list)

    # 4. Test /api/database/audits
    res_audits = client.get("/api/database/audits")
    assert res_audits.status_code == 200
    data_audits = res_audits.json()
    assert isinstance(data_audits, list)

    # 5. Test /api/database/sync
    res_sync = client.post("/api/database/sync")
    assert res_sync.status_code == 200
    data_sync = res_sync.json()
    assert data_sync["status"] == "SUCCESS"
    assert "metrics" in data_sync

