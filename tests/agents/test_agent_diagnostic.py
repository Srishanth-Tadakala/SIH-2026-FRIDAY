"""Unit and Integration Tests for Diagnostic / Root-Cause Agent (Sub-Phase 3.2).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean Message Bus Registration
2. Direct Generator Trip Root-Cause Isolation
3. Multi-Hop Fuel Starvation Causal Tracing (Day Tank -> Generator -> Grid -> Load)
4. Severe Katabatic Storm Environmental Root-Cause Identification
5. Utilidor Water Freeze Root-Cause Tracing
6. Deliberation Session Blackboard Recording & Downstream Agent Pub/Sub Dispatch
7. Interactive Query Response for On-Demand Diagnostic Inquiries
"""

from __future__ import annotations

import pytest

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.models import (
    AgentMessage,
    AgentRole,
    MessageType,
    SeverityLevel,
)
from backend.agents.specialized.diagnostic import DiagnosticAgent, DiagnosisResult
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestDiagnosticAgent:
    """Comprehensive test suite for DiagnosticAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = DiagnosticAgent(bus, engine, graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes cleanly with proper role and zero cached diagnoses."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.DIAGNOSTIC
        assert len(agent._diagnoses) == 0

    def test_direct_generator_trip_root_cause_diagnosis(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify generator trip is isolated as originating physical fault for power bus symptoms."""
        agent, bus, engine, graph = setup_agent

        # Inject generator trip scenario
        engine.inject_scenario(MasterScenario.GENERATOR_TRIP)
        engine.step(dt_seconds=5.0)

        # Symptom observed at Main Low Voltage Bus (mlvd_bus)
        diag = agent.diagnose_node(symptom_node_id="mlvd_bus", session_id="SES-GEN-001")

        assert isinstance(diag, DiagnosisResult)
        assert diag.symptom_node_id == "mlvd_bus"
        assert diag.root_cause_node_id == "chp_1"
        assert "chp_1" in diag.causal_chain
        assert "mlvd_bus" in diag.causal_chain
        assert diag.confidence >= 0.80
        assert not diag.is_environmental
        assert "Primary CHP Generator Tripped" in diag.evidence.get("condition", "")

    def test_multi_hop_fuel_depletion_root_cause(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify root cause traces back through generator to day tank when fuel is depleted."""
        agent, bus, engine, graph = setup_agent

        # Simulate day tank fuel exhaustion and resulting CHP trip
        engine.energy_registry.physics.fuel.day_tank_level_l = 30.0
        engine.energy_registry.physics.chps[0].active_power_kw = 0.0
        engine.energy_registry.physics.chps[0].running_status = False
        engine._refresh_all_readings()

        # Symptom observed downstream at mlvd_bus
        diag = agent.diagnose_node(symptom_node_id="mlvd_bus", session_id="SES-FUEL-001")

        assert diag.root_cause_node_id == "day_tank"
        assert "day_tank" in diag.causal_chain
        assert diag.confidence >= 0.80
        assert not diag.is_environmental
        assert "Day Tank Fuel Depletion" in diag.evidence.get("condition", "")
        assert "day_tank" == diag.causal_chain[0]

    def test_katabatic_storm_environmental_root_cause(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify extreme katabatic winds are recognized as an external environmental root cause."""
        agent, bus, engine, graph = setup_agent

        # Inject blizzard strike scenario
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)
        engine.step(dt_seconds=10.0)

        # Symptom observed at helipad deck
        diag = agent.diagnose_node(symptom_node_id="helipad", session_id="SES-BLZ-001")

        assert diag.root_cause_node_id == "env_katabatic"
        assert diag.is_environmental is True
        assert diag.confidence >= 0.80
        assert "Severe Katabatic Storm" in diag.evidence.get("condition", "")
        assert "Environmental stressor" in diag.explanation

    def test_utilidor_water_freeze_root_cause(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify RO plant stoppage is traced upstream to utilidor intake line freezing."""
        agent, bus, engine, graph = setup_agent

        # Inject water line freeze scenario
        engine.inject_scenario(MasterScenario.WATER_LINE_FREEZE)
        engine.step(dt_seconds=5.0)

        # Symptom observed at reverse osmosis plant (ro_plant)
        diag = agent.diagnose_node(symptom_node_id="ro_plant", session_id="SES-FRZ-001")

        assert diag.root_cause_node_id == "utilidor_water_line"
        assert "utilidor_water_line" in diag.causal_chain
        assert "ro_plant" in diag.causal_chain
        assert diag.evidence.get("pipe_temp_c", 10.0) <= 1.0

    def test_deliberation_session_integration_and_bus_dispatch(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify incoming ALERT triggers diagnosis, updates session blackboard, and dispatches DIAGNOSIS."""
        agent, bus, engine, graph = setup_agent

        # Step into generator trip
        engine.inject_scenario(MasterScenario.GENERATOR_TRIP)
        engine.step(dt_seconds=5.0)

        # Create deliberation session on bus
        session = bus.create_session(trigger_alert={"primary_sensor": "BHARATI.CHP.01.POWER"})
        sess_id = session.session_id

        # Capture downstream messages for Prediction and Planning
        pred_messages: list[AgentMessage] = []
        plan_messages: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.PREDICTION, lambda m: pred_messages.append(m))
        bus.subscribe_role(AgentRole.PLANNING, lambda m: plan_messages.append(m))

        # Dispatch ALERT from Situation Awareness
        alert = AgentMessage(
            sender=AgentRole.SITUATION_AWARENESS,
            recipient="BROADCAST",
            message_type=MessageType.ALERT,
            severity=SeverityLevel.CRITICAL,
            payload={
                "primary_sensor_id": "BHARATI.CHP.01.POWER",
                "subsystem": "ENERGY",
                "anomaly_type": "POWER_DROP",
                "observed_value": 0.0,
                "threshold_value": 50.0,
            },
            session_id=sess_id,
        )
        bus.publish(alert)

        # Check session blackboard updated
        assert len(session.root_causes) >= 1
        recorded_root = session.root_causes[0]
        assert recorded_root["root_cause_node_id"] == "chp_1"

        # Check downstream dispatch of DIAGNOSIS messages
        pred_diag = [m for m in pred_messages if m.message_type == MessageType.DIAGNOSIS]
        assert len(pred_diag) == 1
        assert pred_diag[0].payload["root_cause_node_id"] == "chp_1"

        plan_diag = [m for m in plan_messages if m.message_type == MessageType.DIAGNOSIS]
        assert len(plan_diag) == 1

    def test_interactive_query_response(
        self, setup_agent: tuple[DiagnosticAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent handles direct QUERY messages and responds with diagnostic explanation."""
        agent, bus, engine, graph = setup_agent

        responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: responses.append(m))

        query_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.DIAGNOSTIC,
            message_type=MessageType.QUERY,
            severity=SeverityLevel.INFO,
            payload={
                "query": "DIAGNOSE_NODE",
                "node_id": "zone_living",
            },
            session_id="SES-QUERY-DIAG-01",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        resp = responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert resp.payload["symptom_node_id"] == "zone_living"
        assert "causal_chain" in resp.payload
        assert "confidence" in resp.payload
        assert "explanation" in resp.payload
