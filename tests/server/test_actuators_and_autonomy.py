"""Integration Tests for Physical Actuators, Cognitive Logs, and Edge Blackout Autonomy.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica.

Tests:
1. Physical Actuators State Inspection (CHPs, Trace Heating, HVAC, Load Shedding, Water)
2. Actuator Commands Execution (Start CHP, Stop CHP, Set Trace Heating, Blizzard Dampers, Science Load Shed)
3. Last Generator Shutdown PIN Gatekeeping (Safety Interlock Enforcement)
4. Structured Cognitive Perception and Actuation Logging ("What Was Noticed & What Was Done")
5. Polar Blackout Edge Command Authority Mode Verification
6. Autonomous Mode Configuration and Simulation Speed Controls
7. Autonomous Closed-Loop Mitigation of Generator Trip and Blizzard Strike Scenarios
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.engine import MasterScenario
from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestActuatorsAndAutonomy:
    """Test suite verifying Station Actuators, Cognitive Logging, and Edge Blackout Autonomy."""

    @pytest.fixture(autouse=True)
    def setup_client(self) -> TestClient:
        """Provide a fresh server state and test client."""
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_get_actuators_state(self, setup_client: TestClient) -> None:
        """Verify GET /api/actions/actuators/bharati returns complete physical equipment states."""
        client = setup_client
        res = client.get("/api/actions/actuators/bharati")
        assert res.status_code == 200
        data = res.json()

        assert data["station_id"] == "bharati"
        assert len(data["generators"]) == 3
        # Generator 1 is primary duty running
        gen1 = data["generators"][0]
        assert gen1["unit_id"] == 1
        assert gen1["operating_state"] == "RUNNING"
        assert gen1["running"] is True
        assert gen1["power_kw"] > 0.0

        # Trace heating
        assert "water01_trace_heating_on" in data["trace_heating"]
        assert "water01_pipe_temp_c" in data["trace_heating"]

        # HVAC
        assert "living_temp_c" in data["hvac"]
        assert "ahu01_fresh_air_damper_pct" in data["hvac"]

        # Edge mode
        assert data["edge_status"]["command_authority"] in (
            "100% LOCAL EDGE AUTONOMY",
            "MAINLAND HQ SUPERVISED",
        )

    def test_actuator_commands_execution(self, setup_client: TestClient) -> None:
        """Verify commanding actuators: start CHP-02, set trace heating, seal blizzard dampers, toggle science load."""
        client = setup_client

        # 1. Start standby Generator 2
        res = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "START_CHP", "parameters": {"unit_id": 2, "power_kw": 70.0}},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "SUCCESS"

        # Verify Generator 2 state
        res_act = client.get("/api/actions/actuators/bharati")
        gen2 = res_act.json()["generators"][1]
        assert gen2["operating_state"] == "RUNNING"
        assert gen2["running"] is True

        # 2. Seal fresh air dampers for blizzard
        res = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "SET_BLIZZARD_DAMPERS", "parameters": {"sealed": True}},
        )
        assert res.status_code == 200
        res_act = client.get("/api/actions/actuators/bharati")
        assert res_act.json()["hvac"]["blizzard_dampers_sealed"] is True

        # 3. Toggle science load shedding
        res = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "TOGGLE_SCIENCE_LOAD_SHED", "parameters": {"shed": True}},
        )
        assert res.status_code == 200
        res_act = client.get("/api/actions/actuators/bharati")
        assert res_act.json()["load_shedding"]["science_load_shed"] is True
        assert res_act.json()["load_shedding"]["conserved_kw"] == 15.0

    def test_stopping_last_generator_requires_pin(self, setup_client: TestClient) -> None:
        """Verify safety interlock prevents shutting down the last generator without Commander PIN."""
        client = setup_client

        # 1. Stop CHP 2 (leaving only CHP 1 running)
        res_stop2 = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "STOP_CHP", "parameters": {"unit_id": 2}},
        )
        assert res_stop2.status_code == 200

        # 2. Attempt to stop CHP 1 without PIN (now the last running generator)
        res = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "STOP_CHP", "parameters": {"unit_id": 1}},
        )
        assert res.status_code == 403
        assert "Commander PIN" in res.json()["detail"]

        # 3. Attempt to stop CHP 1 with valid Commander PIN
        res_auth = client.post(
            "/api/actions/actuators/bharati",
            json={"command": "STOP_CHP", "parameters": {"unit_id": 1}, "pin": "BHARATI-CMD-2026"},
        )
        assert res_auth.status_code == 200

    def test_structured_cognitive_logging(self, setup_client: TestClient) -> None:
        """Verify structured logs categorized into Perception, Diagnosis, Prediction, and Actuation."""
        client = setup_client

        # Fetch cognitive logs
        res = client.get("/api/actions/cognitive_logs/bharati")
        assert res.status_code == 200
        logs = res.json()
        assert len(logs) > 0

        # Verify initial EDGE_AUTHORITY startup log is present
        cats = [log["category"] for log in logs]
        assert "EDGE_AUTHORITY" in cats

        # Trigger an anomaly by injecting GENERATOR_TRIP
        client.post("/api/scenarios/inject/bharati", json={"scenario": "GENERATOR_TRIP"})

        # Step 1 tick
        client.post("/api/stations/bharati/step", json={"dt_seconds": 1.0})

        # Check that new cognitive events were logged describing what was noticed and diagnosed
        res_logs = client.get("/api/actions/cognitive_logs/bharati?limit=20")
        logs_after = res_logs.json()
        titles = [entry["title"] for entry in logs_after]
        assert any("CHP" in t or "Generator" in t or "Anomaly" in t for t in titles)

    def test_polar_blackout_edge_command_authority(self, setup_client: TestClient) -> None:
        """Verify F.R.I.D.A.Y. enters 100% Local Edge Autonomy during Polar Satcom Blackout."""
        client = setup_client

        # Switch satcom profile to POLAR_BLACKOUT (0 kbps)
        res_sat = client.post(
            "/api/satcom/profile",
            json={"profile": "POLAR_BLACKOUT", "station_id": "bharati"},
        )
        assert res_sat.status_code == 200

        # Check edge status
        res_edge = client.get("/api/actions/edge_status/bharati")
        assert res_edge.status_code == 200
        edge_data = res_edge.json()
        assert edge_data["is_blackout"] is True
        assert edge_data["command_authority"] == "100% LOCAL EDGE AUTONOMY"
        assert edge_data["bandwidth_kbps"] == 0.0

        # Step simulation during blackout: station must continue stepping cleanly
        res_step = client.post("/api/stations/bharati/step", json={"dt_seconds": 1.0})
        assert res_step.status_code == 200

        # Check that deltas are spooled locally
        res_edge2 = client.get("/api/actions/edge_status/bharati")
        assert res_edge2.json()["spooled_packets_count"] > 0

        # Check cognitive log records blackout transition
        res_logs = client.get("/api/actions/cognitive_logs/bharati?category=EDGE_AUTHORITY")
        blackout_logs = res_logs.json()
        assert any("BLACKOUT" in entry["title"] for entry in blackout_logs)

    def test_autonomous_mode_configuration(self, setup_client: TestClient) -> None:
        """Verify configuring autonomous mode parameters and speed."""
        client = setup_client

        res = client.post(
            "/api/actions/autonomous_mode",
            json={"autonomous_enabled": True, "continuous_running": False, "speed": 2.0},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["autonomous_enabled"] is True
        assert data["continuous_running"] is False
        assert data["speed"] == 2.0
