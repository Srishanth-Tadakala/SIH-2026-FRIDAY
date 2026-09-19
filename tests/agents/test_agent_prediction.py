"""Unit and Integration Tests for Prediction Agent (Sub-Phase 3.3).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean Message Bus Registration
2. Stable Forward Trajectory Projection under Nominal Conditions
3. Thermal Decay Time-to-Violation Estimation during Cold Stress
4. Day Tank Fuel Depletion Time-to-Failure Calculation
5. Utilidor Pipe Freeze Time-to-Failure Calculation
6. Deliberation Session Blackboard Integration & Downstream Pub/Sub Dispatch
7. Interactive Query Response for Lookahead Trajectories
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
from backend.agents.specialized.prediction import PredictionAgent, PredictionProjection
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestPredictionAgent:
    """Comprehensive test suite for PredictionAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = PredictionAgent(bus, engine, graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with PREDICTION role and empty audit cache."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.PREDICTION
        assert len(agent._predictions) == 0

    def test_stable_forward_projection_nominal_conditions(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify forward simulation under normal conditions projects a stable trajectory with zero breaches."""
        agent, bus, engine, graph = setup_agent

        projection = agent.project_forward(duration_hours=4.0, session_id="SES-NOM-01")

        assert isinstance(projection, PredictionProjection)
        assert projection.session_id == "SES-NOM-01"
        assert projection.current_trend in ("STABLE", "MODERATE_DRIFT")
        assert "15m" in projection.horizons
        assert "1h" in projection.horizons
        assert "4h" in projection.horizons
        assert projection.horizons["4h"]["indoor_temp_c"] >= 16.0
        assert len(projection.trajectory["time_hours"]) > 0
        assert projection.confidence >= 0.90
        assert "STABLE FORWARD TRAJECTORY" in projection.summary or "No life-support" in projection.summary

    def test_thermal_decay_time_to_violation_in_blizzard(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify thermal decay under extreme windchill and total heating failure triggers TtV warning."""
        agent, bus, engine, graph = setup_agent

        # Simulate severe blizzard and drop heating
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)
        engine.infra_registry.physics.building.temp_living_c = 17.5  # Already near threshold
        engine._refresh_all_readings()

        ttf_info = agent.calculate_time_to_failure("thermal")

        assert ttf_info["metric"] == "INDOOR_TEMPERATURE"
        assert ttf_info["status"] in ("PROJECTED_BREACH", "IMMEDIATE_BREACH")
        assert ttf_info["threshold"] == 16.0
        if ttf_info["status"] == "PROJECTED_BREACH":
            assert ttf_info["time_to_failure_seconds"] > 0
            assert ttf_info["time_to_failure_minutes"] > 0

    def test_day_tank_fuel_exhaustion_time_to_failure(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify targeted fuel depletion calculation accurately computes remaining hours."""
        agent, bus, engine, graph = setup_agent

        # Set day tank to 120 liters remaining
        engine.energy_registry.physics.fuel.day_tank_level_l = 120.0
        engine._refresh_all_readings()

        ttf_fuel = agent.calculate_time_to_failure("fuel")

        assert ttf_fuel["metric"] == "DAY_TANK_FUEL"
        assert ttf_fuel["status"] == "DEPLETION_TRACKED"
        assert ttf_fuel["time_to_failure_hours"] == 5.0  # 120 L / 24 L/h = 5.0 hours
        assert ttf_fuel["time_to_failure_seconds"] == 18000.0

    def test_utilidor_pipe_freeze_time_to_failure(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify freeze time estimation for utilidor fresh water lines."""
        agent, bus, engine, graph = setup_agent

        # Set pipe temperature to 2.0°C under freezing ambient
        engine.infra_registry.physics.pipelines.water01_pipe_temp_c = 2.0
        engine._refresh_all_readings()

        ttf_pipe = agent.calculate_time_to_failure("pipe")

        assert ttf_pipe["metric"] == "UTILIDOR_WATER_PIPE"
        assert ttf_pipe["time_to_failure_seconds"] > 0
        assert ttf_pipe["time_to_failure_minutes"] > 0
        assert ttf_pipe["threshold_c"] == 0.0

    def test_deliberation_session_integration_and_bus_dispatch(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify incoming DIAGNOSIS triggers lookahead, updates session blackboard, and dispatches PREDICTION_PROJECTION."""
        agent, bus, engine, graph = setup_agent

        # Create deliberation session on bus
        session = bus.create_session(trigger_alert={"anomaly": "GENERATOR_TRIP"})
        sess_id = session.session_id

        # Capture downstream messages for Risk & Impact and Planning
        risk_messages: list[AgentMessage] = []
        plan_messages: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.RISK_IMPACT, lambda m: risk_messages.append(m))
        bus.subscribe_role(AgentRole.PLANNING, lambda m: plan_messages.append(m))

        # Publish a DIAGNOSIS message
        diag_msg = AgentMessage(
            sender=AgentRole.DIAGNOSTIC,
            recipient=AgentRole.PREDICTION,
            message_type=MessageType.DIAGNOSIS,
            severity=SeverityLevel.CRITICAL,
            payload={
                "root_cause_node_id": "chp_1",
                "explanation": "Primary generator tripped on high coolant temperature.",
            },
            session_id=sess_id,
        )
        bus.publish(diag_msg)

        # Check session blackboard updated with predictions
        assert len(session.predictions) >= 1
        recorded_pred = session.predictions[0]
        assert "horizons" in recorded_pred
        assert "15m" in recorded_pred["horizons"]
        assert "1h" in recorded_pred["horizons"]
        assert "4h" in recorded_pred["horizons"]

        # Check downstream dispatch of PREDICTION_PROJECTION
        risk_proj = [m for m in risk_messages if m.message_type == MessageType.PREDICTION_PROJECTION]
        assert len(risk_proj) == 1
        assert "horizons" in risk_proj[0].payload

        plan_proj = [m for m in plan_messages if m.message_type == MessageType.PREDICTION_PROJECTION]
        assert len(plan_proj) == 1

    def test_interactive_query_response(
        self, setup_agent: tuple[PredictionAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent responds to direct operator queries with trajectory forecast."""
        agent, bus, engine, graph = setup_agent

        responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: responses.append(m))

        query_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.PREDICTION,
            message_type=MessageType.QUERY,
            severity=SeverityLevel.INFO,
            payload={"duration_hours": 2.0},
            session_id="SES-QUERY-PRED-01",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        resp = responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert "horizons" in resp.payload
        assert "trajectory" in resp.payload
        assert "summary" in resp.payload
        assert resp.confidence >= 0.90
