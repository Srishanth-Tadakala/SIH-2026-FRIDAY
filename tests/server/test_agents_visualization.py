"""Integration Tests for Cognitive Agent Society Representation and Causal Graph API.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from backend.core.engine import MasterScenario
from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestAgentSocietyAndCausalGraph:
    @pytest.fixture(autouse=True)
    def setup_client(self) -> TestClient:
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_get_agents_society_status(self, setup_client: TestClient) -> None:
        client = setup_client
        res = client.get("/api/agents/status")
        assert res.status_code == 200
        data = res.json()

        assert data["total_agents"] == 10
        assert "FRIDAY_ORCHESTRATOR" in data["agents"]
        assert "SITUATION_AWARENESS" in data["agents"]
        assert "DIAGNOSTIC" in data["agents"]
        assert "PREDICTION" in data["agents"]
        assert "WHAT_IF" in data["agents"]

        # Verify active deliberation phase
        phase = data["active_deliberation_phase"]
        assert phase["phase"] == 1
        assert phase["status"] == "NOMINAL"

    def test_causal_graph_export(self, setup_client: TestClient) -> None:
        client = setup_client
        res = client.get("/api/agents/causal_graph")
        assert res.status_code == 200
        data = res.json()

        assert data["station_id"] == "bharati"
        assert data["total_nodes"] >= 30
        assert data["total_edges"] >= 40

        # Check nodes structure
        nodes = data["nodes"]
        node_ids = [n["id"] for n in nodes]
        assert "chp_1" in node_ids
        assert "mlvd_bus" in node_ids
        assert "zone_living" in node_ids
        assert "utilidor_water_line" in node_ids

    def test_blast_radius_calculation(self, setup_client: TestClient) -> None:
        client = setup_client
        res = client.get("/api/agents/causal_graph/blast_radius/chp_1")
        assert res.status_code == 200
        data = res.json()

        assert data["node_id"] == "chp_1"
        blast = data["blast_radius"]
        assert blast["total_affected_assets"] > 0
        assert blast["life_support_threat"] is True
        assert len(data["downstream_impacts"]) > 0

    def test_agent_role_detail_and_messages(self, setup_client: TestClient) -> None:
        client = setup_client
        res = client.get("/api/agents/DIAGNOSTIC")
        assert res.status_code == 200
        data = res.json()

        assert data["role"] == "DIAGNOSTIC"
        assert "runtime" in data
        assert "objective" in data["runtime"]
        assert "recent_messages" in data
