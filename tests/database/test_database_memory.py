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
async def test_equipment_repo_buffering_and_batch_flush():
    """Verify high-frequency equipment runtime updates are batched in-memory and flushed properly."""
    db = DatabaseManager()
    repo = EquipmentRepository(db)
    await repo.initialize_station_assets("bharati")

    chp2 = await repo.get_asset("chp_2", "bharati")
    assert chp2 is not None
    initial_hours = chp2.total_running_hours

    # 1. High frequency 1-second simulation ticks (10 ticks = 10s < 60s threshold)
    for _ in range(10):
        await repo.accumulate_runtime("chp_2", "bharati", dt_seconds=1.0, is_running=True)

    # In-memory buffer holds the 10 seconds
    assert repo._runtime_buffer[("chp_2", "bharati")] == pytest.approx(10.0, 0.01)

    # Direct database read verifies persistent store has NOT been written yet
    raw_doc = await db.find_one_record(
        "equipment_lifecycle", {"equipment_id": "chp_2", "station_id": "bharati"}
    )
    assert raw_doc["total_running_hours"] == initial_hours

    # 2. Explicit flush commits pending in-memory buffer
    await repo.flush_all_buffers()
    assert repo._runtime_buffer.get(("chp_2", "bharati"), 0.0) == 0.0

    raw_doc_after = await db.find_one_record(
        "equipment_lifecycle", {"equipment_id": "chp_2", "station_id": "bharati"}
    )
    assert raw_doc_after["total_running_hours"] == pytest.approx(initial_hours + (10.0 / 3600.0), 0.0001)

    # 3. Vibration anomaly bypasses buffering and flushes immediately
    await repo.accumulate_runtime(
        "chp_2", "bharati", dt_seconds=1.0, is_running=True, extra_vibration_mms=4.5
    )
    assert repo._runtime_buffer.get(("chp_2", "bharati"), 0.0) == 0.0
    raw_doc_vibe = await db.find_one_record(
        "equipment_lifecycle", {"equipment_id": "chp_2", "station_id": "bharati"}
    )
    assert raw_doc_vibe["vibration_rms_mms"] >= 4.5


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


@pytest.mark.asyncio
async def test_memory_repository_end_to_end():
    """Verify complete MemoryRepository pipeline: seeding, saving, filtering, searching, and telemetry."""
    from backend.database.models import MemoryRecord, MemoryType
    from backend.database.repositories.memory_repo import MemoryRepository

    db = DatabaseManager()
    repo = MemoryRepository(db)

    # 1. Initialize baseline memories
    await repo.initialize_baseline_memories()
    stats = await repo.get_memory_stats()
    assert stats["total_memories"] >= 6
    assert "PLANNING" in stats["counts_by_agent"]

    # 2. Save an agent-scoped memory
    test_mem = MemoryRecord(
        memory_id="MEM-TEST-999",
        memory_type=MemoryType.INCIDENT,
        agent_role="PLANNING",
        station_id="bharati",
        title="BESS Rapid Discharge Thermal Lockout",
        summary="Prevent battery cell thermal runaway by tapering discharge current at 15% SoC.",
        content="During rapid discharge at -25°C, internal cell impedance generates thermal gradients. Tapering current limit from 200A to 80A preserves battery lifecycle and avoids bus undervoltage trip.",
        importance=0.96,
        severity="CRITICAL",
        source="AGENT_EXPERIENCE",
        tags=["battery", "bess", "thermal_runaway", "soc", "microgrid"],
    )
    doc_id = await repo.save_memory(test_mem)
    assert doc_id is not None

    # 3. Retrieve by ID
    retrieved = await repo.get_memory("MEM-TEST-999")
    assert retrieved is not None
    assert retrieved.title == "BESS Rapid Discharge Thermal Lockout"
    assert retrieved.importance == 0.96

    # 4. Filter by agent role and station
    planning_mems = await repo.list_memories(agent_role="PLANNING", station_id="bharati")
    assert len(planning_mems) >= 2
    assert any(m.memory_id == "MEM-TEST-999" for m in planning_mems)

    # 5. Filter by severity and keyword
    crit_mems = await repo.list_memories(severity="CRITICAL", search_query="thermal")
    assert len(crit_mems) >= 1
    assert any("thermal" in m.title.lower() or "thermal" in m.content.lower() for m in crit_mems)

    # 6. Semantic & keyword relevance search
    results, event = await repo.search_relevant_memories(
        agent_role="PLANNING",
        station_id="bharati",
        query_text="bess battery discharge current",
        tags=["battery", "bess"],
        limit=2,
    )
    assert len(results) >= 1
    assert results[0].memory_id == "MEM-TEST-999"
    assert event.memories_found >= 1
    assert "MEM-TEST-999" in event.memory_ids
    assert event.retrieval_latency_ms >= 0.0
    assert event.context_size_bytes > 0
    assert event.memory_injection_success is True

    # 7. Synchronous relevance search for agent runtime loop
    sync_results, sync_event = repo.search_relevant_sync(
        agent_role="PLANNING",
        station_id="bharati",
        query_text="chp generator cold start",
        tags=["chp_1", "cold_crank"],
        limit=2,
    )
    assert len(sync_results) >= 1
    assert sync_event.memories_found >= 1
    assert sync_event.retrieval_latency_ms >= 0.0


def test_memory_and_alerts_api_endpoints():
    """Verify REST API endpoints for /api/memory and /api/alerts."""
    from fastapi.testclient import TestClient
    from backend.server.app import create_app
    from backend.server.state import reset_server_state

    reset_server_state(seed=42)
    app = create_app()
    client = TestClient(app)

    # 1. Test GET /api/memory
    res_mem = client.get("/api/memory")
    assert res_mem.status_code == 200
    mems = res_mem.json()
    assert isinstance(mems, list)
    assert len(mems) >= 6

    # 2. Test GET /api/memory/stats/summary
    res_stats = client.get("/api/memory/stats/summary")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert "total_memories" in stats_data
    assert "counts_by_agent" in stats_data

    # 3. Test POST /api/memory/search
    res_search = client.post(
        "/api/memory/search",
        json={"query": "chp generator", "agent_role": "PLANNING", "station_id": "bharati", "tags": ["chp_1"]},
    )
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["memories_found"] >= 1
    assert "retrieval_event" in search_data

    # 4. Test GET /api/memory/agent/PLANNING
    res_agent_mem = client.get("/api/memory/agent/PLANNING")
    assert res_agent_mem.status_code == 200
    assert len(res_agent_mem.json()) >= 1

    # 5. Test GET /api/memory/station/bharati
    res_station_mem = client.get("/api/memory/station/bharati")
    assert res_station_mem.status_code == 200
    assert len(res_station_mem.json()) >= 1

    # 6. Test GET /api/alerts
    res_alerts = client.get("/api/alerts")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert isinstance(alerts, list)

    # 7. Test GET /api/alerts/summary
    res_alert_sum = client.get("/api/alerts/summary")
    assert res_alert_sum.status_code == 200
    sum_data = res_alert_sum.json()
    assert "total_active_alerts" in sum_data
    assert "critical_count" in sum_data


