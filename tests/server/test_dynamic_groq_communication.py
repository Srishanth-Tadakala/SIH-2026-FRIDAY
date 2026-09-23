"""Unit and Integration Tests for Dynamic Groq-Powered Multi-Agent Communication & Response Styling.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.groq_brain import GroqBrainEngine, get_groq_brain
from backend.agents.framework.models import ActionProposal, AutonomyTier, MessageType, SeverityLevel
from backend.server.app import create_app
from backend.server.state import reset_server_state, get_server_state


class TestDynamicGroqCommunication:
    """Test suite covering runtime Groq key injection, dynamic dialogue synthesis, and response formatting."""

    @pytest.fixture(autouse=True)
    def setup_client(self) -> TestClient:
        """Provide a fresh server state and test client for each test."""
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_agents_set_groq_key_and_status(self, setup_client: TestClient) -> None:
        """Verify POST /api/agents/set_groq_key dynamically registers the key and updates /api/agents/groq_status."""
        client = setup_client

        # Initial status
        res0 = client.get("/api/agents/groq_status")
        assert res0.status_code == 200
        data0 = res0.json()
        assert data0["status"] == "SUCCESS"
        assert "model_name" in data0

        # Set key dynamically
        test_key = "gsk_dynamic_antarctic_defense_key_demo_98765"
        res1 = client.post("/api/agents/set_groq_key", json={"api_key": test_key})
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["status"] == "SUCCESS"
        assert "model_name" in data1
        assert "is_live_available" in data1

        # Verify key was recorded on singleton
        brain = GroqBrainEngine.get_instance()
        assert brain.api_key == test_key

        # Verify status endpoint reflects key presence
        res2 = client.get("/api/agents/groq_status")
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["has_api_key"] is True
        assert data2["model_name"] == brain.model_name

    def test_copilot_and_agents_status_parity(self, setup_client: TestClient) -> None:
        """Verify /api/copilot/status and /api/agents/groq_status return synchronized engine status."""
        client = setup_client
        res_copilot = client.get("/api/copilot/status")
        res_agents = client.get("/api/agents/groq_status")

        assert res_copilot.status_code == 200
        assert res_agents.status_code == 200

        data_c = res_copilot.json()
        data_a = res_agents.json()

        assert data_c["model_name"] == data_a["model_name"]
        assert data_c["total_inferences"] == data_a["total_inferences"]
        assert data_c["has_api_key"] == data_a["has_api_key"]

    def test_copilot_response_style_and_badges(self, setup_client: TestClient) -> None:
        """Verify POST /api/copilot/chat returns defense-grade executive sections with badges, telemetry, and precedents."""
        client = setup_client

        # Test power-related inquiry
        res = client.post(
            "/api/copilot/chat",
            json={
                "message": "Explain our microgrid stability and generator load status.",
                "station_id": "bharati",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"

        reply = data["reply"]

        # 1. Executive Status Badge
        assert "**[OPERATIONAL STATUS:" in reply
        assert "BHARATI STATION (69.4°S, 76.2°E)]**" in reply

        # 2. Required Executive Sections
        assert "### 🧭 Operational Assessment" in reply
        assert "### 📊 Real-Time Telemetry Citations" in reply
        assert "### 🧠 Multi-Agent Society Consensus" in reply
        assert "### 📜 Empirical Expedition Precedent" in reply
        assert "### 👉 Suggested Tactical Actions" in reply

        # 3. Telemetry metrics in backticks
        assert " kW`" in reply or "°C`" in reply

        # 4. Citations & Suggested Followups
        assert len(data["cited_sensors"]) >= 1
        assert len(data["suggested_followups"]) >= 2
        assert data["operational_status"] in ("NOMINAL", "ACTIVE DEFENSE", "ACTIVE_DISRUPTION")

    def test_copilot_blackout_and_edge_synthesis_query(self, setup_client: TestClient) -> None:
        """Verify copilot chat accurately answers inquiries regarding satcom blackout autonomy."""
        client = setup_client
        res = client.post(
            "/api/copilot/chat",
            json={
                "message": "How does F.R.I.D.A.Y. maintain station safety during 0 kbps polar blackout?",
                "station_id": "bharati",
            },
        )
        assert res.status_code == 200
        data = res.json()
        reply = data["reply"]

        assert "Polar Blackout" in reply or "blackout" in reply.lower()
        assert "### 🧭 Operational Assessment" in reply
        assert "### 📜 Empirical Expedition Precedent" in reply

    def test_dynamic_agent_dialogue_turn_generation(self) -> None:
        """Verify GroqBrainEngine generates expressive, domain-tailored dialogue turns for specialized agents."""
        brain = get_groq_brain()

        # Test Diagnostic turn
        diag_turn = brain.run_sync(
            brain.reason_agent_dialogue_turn(
                sender="DIAGNOSTIC_AGENT",
                recipient="FRIDAY_ORCHESTRATOR",
                message_type="DIAGNOSIS",
                session_context={"root_cause": "generator_fuel_line_freeze", "severity": "CRITICAL"},
            )
        )
        assert diag_turn is not None
        assert "dialogue_text" in diag_turn
        assert "technical_summary" in diag_turn
        assert "confidence" in diag_turn
        assert len(diag_turn["dialogue_text"]) > 20
        assert "causal" in diag_turn["dialogue_text"].lower() or "dag" in diag_turn["dialogue_text"].lower()

        # Test What-If turn
        what_if_turn = brain.run_sync(
            brain.reason_agent_dialogue_turn(
                sender="WHAT_IF_AGENT",
                recipient="FRIDAY_ORCHESTRATOR",
                message_type="SIM_RESULT",
                session_context={"proposal_id": "PROP-01", "risk_reduction": 78.4},
            )
        )
        assert what_if_turn is not None
        assert "sandbox" in what_if_turn["dialogue_text"].lower() or "simulation" in what_if_turn["dialogue_text"].lower()
        assert what_if_turn["confidence"] >= 0.8

    def test_briefing_card_digital_twin_and_madrid_enrichment(self) -> None:
        """Verify FridayMasterOrchestrator synthesizes briefing cards enriched with digital twin verification metrics."""
        state = get_server_state()
        orchestrator = state.orchestrator

        # Create deliberation session with simulated proposal
        session = state.bus.create_session(
            trigger_alert={"anomaly_type": "GENERATOR_FREQUENCY_DRIFT", "sensor_id": "sensor_bus_freq_hz"}
        )

        proposal = ActionProposal(
            title="Auto-Sequence Standby CHP-02 and Shed Non-Essential Loads",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "energy", "path": "chps[1].operating_state", "value": "RUNNING"}],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Restore 400V bus stability grounded on 35th IAE precedent.",
            simulation_delta={"risk_reduction_pct": 82.5, "temp_difference_c": 2.1, "is_safe": True},
        )
        session.candidate_proposals.append(proposal)
        session.final_plan = proposal

        # Synthesize briefing card
        card = orchestrator.synthesize_briefing_card(session.session_id)
        assert card is not None
        assert "82.5%" in card.deliberation_summary or "risk reduction" in card.deliberation_summary.lower()
        assert "Madrid Protocol" in card.deliberation_summary

        # Verify card serialization
        c_dict = card.to_dict()
        assert c_dict["session_id"] == session.session_id
        assert c_dict["tier"] == "TIER_1_AUTONOMOUS"
        assert c_dict["requires_pin"] is False

    def test_inter_agent_messages_have_expressive_summaries(self) -> None:
        """Verify that BaseSpecializedAgent automatically attaches clean summaries to published messages."""
        state = get_server_state()
        diag_agent = state.diagnostic
        assert diag_agent is not None

        # Publish test diagnostic message
        msg = diag_agent.publish_message(
            session_id="test_session_audit",
            recipient="BROADCAST",
            message_type=MessageType.DIAGNOSIS,
            severity=SeverityLevel.WARNING,
            payload={
                "explanation": "Bayesian DAG traversal isolated root cause to CHP-01 heat exchanger fouling.",
                "root_cause": "chp01_heat_exchanger",
            },
        )

        assert "summary" in msg.payload
        assert "Bayesian DAG" in msg.payload["summary"]
