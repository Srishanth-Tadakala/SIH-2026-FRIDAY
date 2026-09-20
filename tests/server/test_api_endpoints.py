"""Unit and Integration Tests for F.R.I.D.A.Y. FastAPI REST API (Sub-Phase 4.1).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica.

Tests:
1. System Health Check & Operational Readiness Probe
2. Dual-Station Listing, Detail, and Metadata Verification
3. Active Station Context Switching & Simulation Clock Stepping
4. Full Telemetry Snapshot, KPIs, Alerts, and Historical Buffers
5. 4-Pillar Filtering & Single Sensor O(1) Lookups
6. Cognitive Agent Society Status & Bus Statistics
7. Crisis Scenario Injection & Situation Awareness Trigger
8. Deliberation Session Blackboard & Commander Briefing Card
9. Tier 1 / Tier 2 Execution Pipeline & Supervisor Bypass/Veto
10. Tier 3 Mandatory Commander PIN Gatekeeping & Rejection
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestFastAPIServerEndpoints:
    """Comprehensive test suite for F.R.I.D.A.Y. FastAPI Server Endpoints."""

    @pytest.fixture(autouse=True)
    def setup_client(self) -> TestClient:
        """Provide a fresh server state and test client for each test."""
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_system_health_check(self, setup_client: TestClient) -> None:
        """Verify GET /api/health returns 200 with online status and dual-station metadata."""
        client = setup_client
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ONLINE"
        assert "bharati" in data["managed_stations"]
        assert "maitri" in data["managed_stations"]
        assert data["active_station"] == "bharati"
        assert data["sensor_count"] == 505
        assert data["cognitive_agents_count"] == 10
        assert data["interlocks_active"] is True

    def test_dual_stations_listing_and_detail(self, setup_client: TestClient) -> None:
        """Verify listing both stations and fetching individual station details."""
        client = setup_client
        res = client.get("/api/stations")
        assert res.status_code == 200
        stations = res.json()
        assert len(stations) == 2
        station_ids = [s["station_id"] for s in stations]
        assert "bharati" in station_ids
        assert "maitri" in station_ids

        # Fetch Bharati detail
        res_b = client.get("/api/stations/bharati")
        assert res_b.status_code == 200
        b_data = res_b.json()
        assert b_data["station_name"] == "Bharati Research Station"
        assert b_data["coordinates"]["latitude"] == -69.4078
        assert b_data["is_active_context"] is True

        # Fetch Maitri detail
        res_m = client.get("/api/stations/maitri")
        assert res_m.status_code == 200
        m_data = res_m.json()
        assert m_data["station_name"] == "Maitri Research Station"
        assert m_data["coordinates"]["latitude"] == -70.7661
        assert m_data["is_active_context"] is False

        # Non-existent station 404
        res_none = client.get("/api/stations/dakshin_gangotri")
        assert res_none.status_code == 404

    def test_active_station_switching_and_clock_step(self, setup_client: TestClient) -> None:
        """Verify switching the active station context and stepping the simulation clock."""
        client = setup_client

        # Switch to Maitri
        res_switch = client.post("/api/stations/active/maitri")
        assert res_switch.status_code == 200
        assert res_switch.json()["active_station_id"] == "maitri"

        # Check health reflects Maitri
        res_health = client.get("/api/health")
        assert res_health.json()["active_station"] == "maitri"

        # Step Maitri simulation clock forward by 10 seconds
        res_step = client.post("/api/stations/maitri/step", json={"dt_seconds": 10.0})
        assert res_step.status_code == 200
        step_data = res_step.json()
        assert step_data["sim_time_seconds"] == 10.0
        assert "kpis" in step_data

        # Restore active station to Bharati
        client.post("/api/stations/active/bharati")

    def test_telemetry_snapshot_kpis_and_alerts(self, setup_client: TestClient) -> None:
        """Verify full snapshot, high-level KPIs, alerts, and historical buffers."""
        client = setup_client

        # Full Snapshot
        res_snap = client.get("/api/telemetry/bharati/snapshot")
        assert res_snap.status_code == 200
        snap = res_snap.json()
        assert snap["station_id"] == "bharati"
        assert snap["sensor_count"] == 505
        assert len(snap["readings"]) == 505
        assert "kpis" in snap
        assert "alerts" in snap

        # KPIs
        res_kpis = client.get("/api/telemetry/bharati/kpis")
        assert res_kpis.status_code == 200
        kpis = res_kpis.json()["kpis"]
        assert "total_generation_kw" in kpis
        assert "indoor_avg_temp_c" in kpis
        assert "fuel_autonomy_days" in kpis
        assert "composite_risk_score" in kpis

        # Alerts
        res_alerts = client.get("/api/telemetry/bharati/alerts")
        assert res_alerts.status_code == 200
        assert "alerts" in res_alerts.json()

        # History
        res_hist = client.get("/api/telemetry/bharati/history?limit=10")
        assert res_hist.status_code == 200
        hist_data = res_hist.json()
        assert hist_data["station_id"] == "bharati"
        assert hist_data["count"] >= 1

    def test_telemetry_pillar_filtering_and_single_sensor_lookup(self, setup_client: TestClient) -> None:
        """Verify filtered pillar sensor readings and O(1) single sensor lookups."""
        client = setup_client

        # Filter by Energy pillar
        res_energy = client.get("/api/telemetry/bharati/pillars/energy")
        assert res_energy.status_code == 200
        e_data = res_energy.json()
        assert e_data["pillar"] == "energy"
        assert e_data["sensor_count"] == 140

        # Filter by Infrastructure pillar
        res_infra = client.get("/api/telemetry/bharati/pillars/infrastructure")
        assert res_infra.status_code == 200
        i_data = res_infra.json()
        assert i_data["sensor_count"] == 180

        # Invalid pillar returns 400
        res_bad_pillar = client.get("/api/telemetry/bharati/pillars/quantum")
        assert res_bad_pillar.status_code == 400

        # Lookup single valid sensor
        res_sensor = client.get("/api/telemetry/bharati/sensors/ENV-WX-TEMP")
        assert res_sensor.status_code == 200
        s_data = res_sensor.json()
        assert s_data["sensor_id"] == "ENV-WX-TEMP"
        assert "reading" in s_data

        # Non-existent sensor returns 404
        res_bad_sensor = client.get("/api/telemetry/bharati/sensors/non_existent_id_xyz")
        assert res_bad_sensor.status_code == 404

    def test_agents_status_and_bus_statistics(self, setup_client: TestClient) -> None:
        """Verify cognitive agents inspection and message bus statistics."""
        client = setup_client

        # Get status for all 10 agents
        res = client.get("/api/agents/status")
        assert res.status_code == 200
        data = res.json()
        assert data["total_agents"] == 10
        assert "FRIDAY_ORCHESTRATOR" in data["agents"]
        assert "SITUATION_AWARENESS" in data["agents"]
        assert "RESOURCE_OPTIMIZER" in data["agents"]

        # Bus stats
        res_bus = client.get("/api/agents/bus/stats")
        assert res_bus.status_code == 200
        b_data = res_bus.json()
        assert "total_messages_published" in b_data
        assert "active_sessions_count" in b_data

        # Single agent detail
        res_agent = client.get("/api/agents/situation_awareness")
        assert res_agent.status_code == 200
        assert res_agent.json()["role"] == "SITUATION_AWARENESS"

        # Invalid role returns 400
        res_invalid = client.get("/api/agents/astro_physicist")
        assert res_invalid.status_code == 400

    def test_crisis_scenario_injection_and_deliberation_trigger(self, setup_client: TestClient) -> None:
        """Verify scenario injection, physics disruption, and situation awareness alert trigger."""
        client = setup_client

        # List scenarios
        res_scenarios = client.get("/api/scenarios")
        assert res_scenarios.status_code == 200
        sc_list = res_scenarios.json()
        assert len(sc_list) == 8

        # Inject BLIZZARD_STRIKE into Bharati
        res_inject = client.post(
            "/api/scenarios/inject",
            json={"scenario": "BLIZZARD_STRIKE", "station_id": "bharati", "parameters": {"wind_speed_mps": 38.0}},
        )
        assert res_inject.status_code == 200
        inj_data = res_inject.json()
        assert inj_data["active_scenario"] == "BLIZZARD_STRIKE"
        assert inj_data["kpis"]["wind_speed_mps"] == 38.0
        assert len(inj_data["active_alerts"]) > 0

        # Verify deliberation sessions created
        res_sessions = client.get("/api/deliberations")
        assert res_sessions.status_code == 200
        sessions = res_sessions.json()
        assert len(sessions) >= 1

        # Clear scenario back to NORMAL
        res_clear = client.post("/api/scenarios/clear", json={"station_id": "bharati"})
        assert res_clear.status_code == 200
        assert res_clear.json()["active_scenario"] == "NORMAL"

    def test_deliberation_session_detail_and_briefing_card(self, setup_client: TestClient) -> None:
        """Verify retrieving deliberation blackboard details and synthesizing Commander Briefing Cards."""
        client = setup_client

        # Inject blizzard to produce a session
        client.post(
            "/api/scenarios/inject",
            json={"scenario": "BLIZZARD_STRIKE", "station_id": "bharati"},
        )

        # Get active session ID
        res_sessions = client.get("/api/deliberations")
        assert len(res_sessions.json()) >= 1
        sid = res_sessions.json()[0]["session_id"]

        # Fetch session details
        res_detail = client.get(f"/api/deliberations/{sid}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert detail["session_id"] == sid
        assert "trigger_alert" in detail

        # Non-existent session returns 404
        res_404 = client.get("/api/deliberations/session-non-existent")
        assert res_404.status_code == 404

    def test_tiered_action_execution_pipeline(self, setup_client: TestClient) -> None:
        """Verify Tier 1 autonomous execution, Tier 2 supervised countdown queue, bypass, and veto."""
        client = setup_client

        # Tier 1 execution: immediate
        res_t1 = client.post(
            "/api/actions/execute",
            json={
                "plan_name": "RO Filter Backwash Routine",
                "strategy": "ROUTINE_CYCLE",
                "autonomy_tier": "TIER_1",
                "actions": [{"action_type": "VALVE_FLUSH", "target": "ro_filter_01", "parameters": {}}],
            },
        )
        assert res_t1.status_code == 200
        t1_data = res_t1.json()
        assert t1_data["autonomy_tier"] == "TIER_1"
        assert t1_data["status"] == "EXECUTED"

        # Tier 2 execution: enters supervised countdown queue
        res_t2 = client.post(
            "/api/actions/execute",
            json={
                "plan_name": "CHP-2 Heat Exchanger Throttle",
                "strategy": "OPERATIONAL_TRIM",
                "autonomy_tier": "TIER_2",
                "actions": [{"action_type": "THROTTLE_DAMPER", "target": "chp_2_damper", "parameters": {"pct": 25.0}}],
                "bypass_supervision": False,
            },
        )
        assert res_t2.status_code == 200
        t2_data = res_t2.json()
        assert t2_data["autonomy_tier"] == "TIER_2"
        assert t2_data["status"] == "PENDING_SUPERVISION"
        action_id = t2_data["action_id"]

        # Verify action appears in pending queue
        res_pending = client.get("/api/actions/pending")
        assert res_pending.status_code == 200
        pending_list = res_pending.json()
        assert any(a["action_id"] == action_id for a in pending_list)

        # Supervisor bypass executes immediately
        res_bypass = client.post(f"/api/actions/supervised/{action_id}/bypass")
        assert res_bypass.status_code == 200
        assert res_bypass.json()["status"] == "EXECUTED"

        # Test operator veto / cancellation
        res_t2_cancel = client.post(
            "/api/actions/execute",
            json={
                "plan_name": "Auxiliary Heater Cutoff",
                "strategy": "OPERATIONAL_TRIM",
                "autonomy_tier": "TIER_2",
                "actions": [{"action_type": "HEATER_OFF", "target": "aux_heater", "parameters": {}}],
            },
        )
        cancel_id = res_t2_cancel.json()["action_id"]
        res_cancel = client.post(f"/api/actions/supervised/{cancel_id}/cancel")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "SUCCESS"

    def test_tier_3_commander_pin_gatekeeping(self, setup_client: TestClient) -> None:
        """Verify Tier 3 Commander PIN authorization gatekeeping and invalid PIN rejection."""
        client = setup_client

        # Attempt authorization with incorrect PIN -> 403 Forbidden
        res_invalid = client.post(
            "/api/actions/authorize_pin",
            json={
                "pin": "WRONG-PIN-1234",
                "command": "TOTAL_LOAD_SHED",
                "parameters": {"bus_id": "mlvd_main"},
            },
        )
        assert res_invalid.status_code == 403
        assert "INVALID_PIN" in res_invalid.json()["detail"]

        # Authorize with correct Station Commander PIN
        res_valid = client.post(
            "/api/actions/authorize_pin",
            json={
                "pin": "BHARATI-CMD-2026",
                "command": "TOTAL_LOAD_SHED",
                "parameters": {"bus_id": "mlvd_main"},
            },
        )
        assert res_valid.status_code == 200
        val_data = res_valid.json()
        assert val_data["status"] == "AUTHORIZED"
        assert val_data["command"] == "TOTAL_LOAD_SHED"
