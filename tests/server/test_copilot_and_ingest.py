"""Unit and Integration Tests for Groq Copilot, SCADA Ingestion, and Cryptographic Security.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.groq_brain import GroqBrainEngine
from backend.agents.framework.models import ActionProposal, AutonomyTier
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.core.engine import BharatiMasterTwinEngine
from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestCopilotAndSCADAIngest:
    """Test suite covering Groq Copilot, Telemetry Ingestion, and Cryptographic Security."""

    @pytest.fixture(autouse=True)
    def setup_client(self) -> TestClient:
        """Provide a fresh server state and test client for each test."""
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_copilot_status_endpoint(self, setup_client: TestClient) -> None:
        """Verify GET /api/copilot/status returns Groq LPU metrics."""
        client = setup_client
        res = client.get("/api/copilot/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "model_name" in data
        assert "total_inferences" in data
        assert "is_live_available" in data

    def test_copilot_suggested_queries(self, setup_client: TestClient) -> None:
        """Verify GET /api/copilot/suggested_queries returns curated questions."""
        client = setup_client
        res = client.get("/api/copilot/suggested_queries")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert len(data["suggested_queries"]) >= 3

    def test_copilot_chat_endpoint(self, setup_client: TestClient) -> None:
        """Verify POST /api/copilot/chat answers inquiries with telemetry citations."""
        client = setup_client
        res = client.post(
            "/api/copilot/chat",
            json={
                "message": "What is the status of our power generation?",
                "station_id": "bharati",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert len(data["reply"]) > 10
        assert "cited_sensors" in data
        assert "suggested_followups" in data
        assert data["operational_status"] in ("NOMINAL", "ACTIVE_DISRUPTION", "DEFENSE_ACTIVE")

    def test_copilot_set_key_endpoint(self, setup_client: TestClient) -> None:
        """Verify POST /api/copilot/set_key updates Groq API configuration."""
        client = setup_client
        res = client.post(
            "/api/copilot/set_key",
            json={"api_key": "gsk_test_demo_mock_key_for_evaluation_12345"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "model_name" in data

    def test_telemetry_batch_ingest(self, setup_client: TestClient) -> None:
        """Verify POST /api/telemetry/ingest updates twin sensor readings from external PLC."""
        client = setup_client
        payload = {
            "station_id": "bharati",
            "source": "FIELD_PLC_SCHNEIDER_M340",
            "readings": [
                {
                    "sensor_id": "BHARATI.CHP.01.ACTIVE_POWER",
                    "value": 72.5,
                    "quality": "GOOD",
                },
                {
                    "sensor_id": "BHARATI-PIPE-WATER01-TEMP",
                    "value": 6.8,
                    "quality": "GOOD",
                },
            ],
        }
        res = client.post("/api/telemetry/ingest", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "INGESTED"
        assert data["points_ingested"] == 2
        assert data["source"] == "FIELD_PLC_SCHNEIDER_M340"

    def test_telemetry_single_reading_ingest(self, setup_client: TestClient) -> None:
        """Verify POST /api/telemetry/ingest accepts single flat sensor readings."""
        client = setup_client
        payload = {
            "station_id": "bharati",
            "sensor_id": "BHARATI-BLDG-Z01-TEMP",
            "value": 22.4,
            "quality": "GOOD",
        }
        res = client.post("/api/telemetry/ingest", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "INGESTED"
        assert data["points_ingested"] == 1

    def test_telemetry_ingest_status(self, setup_client: TestClient) -> None:
        """Verify GET /api/telemetry/ingest/status returns gateway health and throughput."""
        client = setup_client
        res = client.get("/api/telemetry/ingest/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "OPERATIONAL"
        assert "supported_protocols" in data
        assert "total_readings_ingested" in data

    def test_cryptographic_pin_and_lockout(self) -> None:
        """Verify PBKDF2 salt hashing and 5-attempt brute-force rate-limiting lockout."""
        mgr = SafetyInterlockManager(commander_pin="BHARATI-CMD-2026")

        # Correct PIN succeeds
        assert mgr.verify_commander_authorization("EXEC", "BHARATI-CMD-2026") is True

        # 4 failed attempts do not lock out
        for _ in range(4):
            assert mgr.verify_commander_authorization("EXEC", "WRONG_PIN") is False
        assert mgr._lockout_until == 0.0

        # 5th failed attempt triggers lockout
        assert mgr.verify_commander_authorization("EXEC", "WRONG_PIN") is False
        assert mgr._lockout_until > time.time()

        # Even correct PIN is rejected during active lockout
        assert mgr.verify_commander_authorization("EXEC", "BHARATI-CMD-2026") is False

    def test_hmac_execution_token_workflow(self) -> None:
        """Verify HMAC-SHA256 execution token generation and Tier 3 authorization."""
        mgr = SafetyInterlockManager()
        engine = BharatiMasterTwinEngine()

        proposal = ActionProposal(
            title="Emergency Diesel Generator Shutdown",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {"pillar": "energy", "path": "chps[0].operating_state", "value": "OFF"}
            ],
            tier=AutonomyTier.TIER_3_COMMANDER_CONFIRMATION,
            rationale="Commander-authorized emergency shutdown",
        )

        # 1. Attempt without token or PIN -> fails with PENDING_COMMANDER
        res_no_auth = mgr.execute_action(proposal, engine)
        assert res_no_auth.success is False

        # 2. Generate HMAC execution token
        token = mgr.generate_execution_token(proposal.proposal_id, ttl_seconds=60.0)
        assert mgr.verify_execution_token(proposal.proposal_id, token) is True
        assert mgr.verify_execution_token("OTHER_PROPOSAL_ID", token) is False

        # 3. Attempt with valid HMAC execution token -> succeeds
        res_token_auth = mgr.execute_action(proposal, engine, execution_token=token)
        assert res_token_auth.success is True

    @pytest.mark.asyncio
    async def test_copilot_grounded_episodic_memory_integration(self) -> None:
        """Verify Copilot queries episodic memory and incorporates historical precedent."""
        from backend.server.state import get_server_state
        state = get_server_state(seed=42)
        await state.initialize_database()

        app = create_app()
        client = TestClient(app)
        res = client.post(
            "/api/copilot/chat",
            json={
                "message": "What is our contingency if generator 1 fails?",
                "station_id": "bharati",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "precedent" in data["reply"].lower() or "grounded" in data["reply"].lower()

    def test_groq_shared_sync_executor(self) -> None:
        """Verify GroqBrainEngine reuses a shared ThreadPoolExecutor without thread churn."""
        executor1 = GroqBrainEngine._get_sync_executor()
        executor2 = GroqBrainEngine._get_sync_executor()
        assert executor1 is executor2
        assert executor1._max_workers == 8

        brain = GroqBrainEngine()
        async def dummy_coro():
            return "ok"
        result = brain.run_sync(dummy_coro())
        assert result == "ok"

    def test_modbus_api_endpoints(self, setup_client: TestClient) -> None:
        """Verify Modbus status, register catalog, and coil write endpoints."""
        client = setup_client
        # 1. Ingest status includes modbus_bridge
        resp = client.get("/api/telemetry/ingest/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "modbus_bridge" in data
        assert data["modbus_bridge"]["station_id"] == "bharati"

        # 2. Modbus status endpoint
        resp_status = client.get("/api/telemetry/modbus/status")
        assert resp_status.status_code == 200
        status_data = resp_status.json()
        assert status_data["station_id"] == "bharati"
        assert "total_polls" in status_data
        assert "registered_point_count" in status_data
        assert status_data["registered_point_count"] >= 15

        # 3. Modbus registers catalog endpoint
        resp_catalog = client.get("/api/telemetry/modbus/registers")
        assert resp_catalog.status_code == 200
        catalog = resp_catalog.json()
        assert "holding_registers" in catalog
        assert "coils" in catalog
        assert len(catalog["holding_registers"]) >= 15
        assert len(catalog["coils"]) >= 5

        # Verify specific catalog entry
        reg_ids = [r["sensor_id"] for r in catalog["holding_registers"]]
        assert "BHARATI.CHP.01.ACTIVE_POWER" in reg_ids
        assert "BHARATI-PIPE-WATER01-TEMP" in reg_ids


