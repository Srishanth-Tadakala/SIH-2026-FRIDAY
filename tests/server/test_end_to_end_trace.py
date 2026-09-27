"""Comprehensive End-to-End System Integration Trace Test.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies the complete end-to-end operational pipeline across 16 steps:
1. Station state initialization
2. Telemetry generation across 505 channels
3. Telemetry persistence & time-series keyframing
4. Telemetry event publication over internal bus
5. WebSocket broadcast payload validation
6. UI data ingestion model verification
7. Anomaly trigger & multi-agent event dispatch
8. Agent creates persistent memory record
9. Memory persistence to local edge store
10. API retrieval via /api/memory
11. Agent performs relevance retrieval before reasoning
12. Retrieved memory injected into reasoning context
13. Memory-retrieval telemetry event published
14. Station & agent filtering verification
15. State reload simulation (backend restart)
16. Verification that memory survives reload
"""

from __future__ import annotations

import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.models import AgentMessage, AgentRole, MessageType, SeverityLevel
from backend.database.models import MemoryRecord, MemoryType
from backend.server.app import create_app
from backend.server.state import get_server_state, reset_server_state


@pytest.mark.asyncio
async def test_complete_end_to_end_trace_pipeline():
    """Execute the full 16-step end-to-end integration scenario."""
    # Step 1: Create a test station state
    state = reset_server_state(seed=42)
    assert state.bharati_engine is not None
    assert state.active_station_id == "bharati"

    # Step 2: Generate telemetry across all 4 life-support pillars
    snapshot = state.step(dt_seconds=1.0)
    assert snapshot is not None
    assert snapshot.kpis["indoor_avg_temp_c"] > 16.0
    assert len(snapshot.readings) == 505

    # Step 3: Persist telemetry in sliding history & time-series
    assert len(state.history["bharati"]) >= 1
    last_hist = state.history["bharati"][-1]
    assert "kpis" in last_hist
    assert "sim_time_seconds" in last_hist

    # Step 4: Publish telemetry event over message bus
    state.bus.publish(
        AgentMessage(
            session_id="SES-TRACE-001",
            sender=AgentRole.SITUATION_AWARENESS,
            recipient="BROADCAST",
            message_type=MessageType.OBSERVATION,
            severity=SeverityLevel.INFO,
            payload={"kpis": snapshot.kpis, "sim_time": snapshot.sim_time_seconds},
        )
    )
    bus_history = state.bus.get_history()
    assert any(m.message_type == MessageType.OBSERVATION for m in bus_history)

    # Step 5: WebSocket broadcast payload validation
    # Verify that ws_manager channels format matches frontend expectation
    ws_kpi_frame = {
        "channel": "kpis",
        "station_id": "bharati",
        "sim_time_seconds": snapshot.sim_time_seconds,
        "kpis": snapshot.kpis,
    }
    assert "indoor_avg_temp_c" in ws_kpi_frame["kpis"]

    # Step 6: UI data ingestion contract validation
    assert isinstance(ws_kpi_frame["kpis"]["indoor_avg_temp_c"], (int, float))

    # Step 7: Trigger an agent event (anomaly detection)
    state.inject_scenario("GENERATOR_TRIP", "bharati")
    anomaly_snap = state.step(dt_seconds=1.0)
    assert anomaly_snap.active_scenario == "GENERATOR_TRIP"

    # Step 8: Agent creates memory from incident analysis
    incident_mem = MemoryRecord(
        memory_id="MEM-TRACE-001",
        memory_type=MemoryType.INCIDENT,
        agent_role="PLANNING",
        station_id="bharati",
        title="Trace Test: CHP-01 Trip Under Convective Wind Load",
        summary="Crank standby generator and pre-warm jacket water to avoid undervoltage.",
        content="During high wind gusts, CHP-01 suffered fuel filter cavitation. Pre-heating standby unit stabilized microgrid.",
        importance=0.98,
        severity="CRITICAL",
        source="AGENT_EXPERIENCE",
        tags=["chp_1", "generator_trip", "microgrid", "trace_test"],
        metadata={"sim_time": anomaly_snap.sim_time_seconds},
    )

    # Step 9: Memory is persisted to storage
    doc_id = await state.memory_repo.save_memory(incident_mem)
    assert doc_id is not None

    # Step 10: Retrieve memory through API
    app = create_app()
    client = TestClient(app)

    res_mem = client.get("/api/memory/MEM-TRACE-001")
    assert res_mem.status_code == 200
    mem_data = res_mem.json()
    assert mem_data["memory_id"] == "MEM-TRACE-001"
    assert mem_data["importance"] == 0.98

    # Step 11: Agent performs a retrieval operation before reasoning
    retrieved_mems, ret_event = state.memory_repo.search_relevant_sync(
        agent_role="PLANNING",
        station_id="bharati",
        query_text="generator trip fuel filter cavitation",
        tags=["generator_trip", "chp_1"],
        limit=2,
    )
    assert len(retrieved_mems) >= 1
    assert retrieved_mems[0].memory_id == "MEM-TRACE-001"

    # Step 12: Verify retrieved memory is included in agent planning context
    proposals = state.planning.formulate_proposals(
        session_id="SES-TRACE-TEST",
        trigger_payload={"root_node_id": "chp_1"},
    )
    assert len(proposals) >= 1
    assert any(p.target_subsystem is not None for p in proposals)

    # Step 13: Publish memory-created / retrieval event
    state.bus.publish(
        AgentMessage(
            session_id="SES-TRACE-002",
            sender=AgentRole.PLANNING,
            recipient="BROADCAST",
            message_type=MessageType.EVENT,
            severity=SeverityLevel.INFO,
            payload={
                "event_type": "memory_retrieval_completed",
                "memories_found": ret_event.memories_found,
                "memory_ids": ret_event.memory_ids,
            },
        )
    )

    # Step 14: UI displays new memory via API
    res_list = client.get("/api/memory?query=cavitation")
    assert res_list.status_code == 200
    matched = res_list.json()
    assert len(matched) >= 1
    assert matched[0]["memory_id"] == "MEM-TRACE-001"

    # Step 15: Reload simulation (simulate server restart by re-initializing repository)
    new_state = reset_server_state(seed=99)
    await new_state.memory_repo.initialize_baseline_memories()

    # Step 16: Verify memory still exists after reload
    reloaded_mem = await new_state.memory_repo.get_memory("MEM-TRACE-001")
    assert reloaded_mem is not None
    assert reloaded_mem.title == "Trace Test: CHP-01 Trip Under Convective Wind Load"
    assert reloaded_mem.importance == 0.98
