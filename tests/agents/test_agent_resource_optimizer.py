"""Unit and Integration Tests for Resource Optimization Cognitive Agent (Sub-Phase 3.9).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean State Registration
2. Optimal Dispatch Computation (Single-Unit Sweet-Spot Consolidation)
3. High Load Dual-Unit Balanced Sharing Dispatch
4. Cyclic Deliberation Critique: Wet Stacking Underload Prevention Veto
5. Cyclic Deliberation Critique: Excessive Generation Fuel Waste Prevention
6. Deliberation Session Blackboard Critique Pub/Sub Integration
7. Interactive Query Handling with Custom Optimization Objectives
"""

from __future__ import annotations

import pytest

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.models import (
    ActionProposal,
    AgentMessage,
    AgentRole,
    AutonomyTier,
    DeliberationSession,
    MessageType,
    SeverityLevel,
)
from backend.agents.specialized.resource_optimizer import (
    CHPDispatchRecommendation,
    OptimizationObjective,
    ResourceOptimizationPlan,
    ResourceOptimizerAgent,
)
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine


class TestResourceOptimizerAgent:
    """Comprehensive test suite for ResourceOptimizerAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = ResourceOptimizerAgent(bus=bus, engine=engine, graph=graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with RESOURCE_OPTIMIZER role and clean state."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.RESOURCE_OPTIMIZER
        assert agent._latest_plan is None

    def test_compute_optimal_dispatch_single_unit(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify standard essential load (~65 kW) yields single-unit consolidated dispatch in optimal band."""
        agent, bus, engine, graph = setup_agent

        # Simulate reduced station load (essential night-time / non-essential load shed)
        engine.energy_registry.physics.total_station_load_kw = 65.0

        plan = agent.compute_optimal_dispatch(objective=OptimizationObjective.BALANCED)

        assert isinstance(plan, ResourceOptimizationPlan)
        assert plan.objective == OptimizationObjective.BALANCED
        assert len(plan.chp_dispatches) == 3

        # Exactly 1 unit running, 2 in standby
        running_units = [c for c in plan.chp_dispatches if c.recommended_state == "RUNNING"]
        standby_units = [c for c in plan.chp_dispatches if c.recommended_state == "STANDBY"]
        assert len(running_units) == 1
        assert len(standby_units) == 2

        # Running unit is in sweet-spot band
        assert running_units[0].is_optimal_band is True
        assert plan.daily_fuel_burn_l > 0.0
        assert len(plan.optimizations_applied) > 0

    def test_compute_optimal_dispatch_dual_unit_heavy_load(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify heavy load (~110 kW) yields dual-unit balanced load sharing."""
        agent, bus, engine, graph = setup_agent

        # Simulate heavy heating and lab electrical load
        engine.energy_registry.physics.chps[0].active_power_kw = 55.0
        engine.energy_registry.physics.chps[1].active_power_kw = 55.0
        engine.energy_registry.physics.chps[0].running_status = True
        engine.energy_registry.physics.chps[1].running_status = True

        plan = agent.compute_optimal_dispatch(objective=OptimizationObjective.MAX_FUEL_CONSERVATION)

        assert isinstance(plan, ResourceOptimizationPlan)
        running_units = [c for c in plan.chp_dispatches if c.recommended_state == "RUNNING"]
        assert len(running_units) >= 2
        for u in running_units:
            assert u.load_factor_percent > 40.0

    def test_cyclic_critique_wet_stacking_underload_veto(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent critiques proposals that run multiple generators below 40% load (wet stacking)."""
        agent, bus, engine, graph = setup_agent

        # Proposing to split load into two underloaded 25 kW generators
        underloaded_proposal = ActionProposal(
            title="Split Load Across CHP-01 and CHP-02 at Low Output",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[0].active_power_kw",
                    "value": 25.0,
                },
                {
                    "pillar": "energy",
                    "path": "chps[1].active_power_kw",
                    "value": 25.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Run two generators for redundancy.",
        )

        critique = agent.critique_proposal(underloaded_proposal)

        assert critique is not None
        assert critique["violates_constraint"] == "ENGINE_WET_STACKING_PREVENTION"
        assert critique["severity"] == "WARNING"
        assert "wet stacking" in critique["critique"].lower()
        assert "Consolidate load onto a single generator" in critique["critique"]

    def test_cyclic_critique_excessive_generation_fuel_waste(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent critiques proposals commanding excessive generator headroom above station demand."""
        agent, bus, engine, graph = setup_agent

        kpis = engine.get_station_kpis()
        actual_load = float(kpis["station_electrical_load_kw"])

        # Commanding 2 generators to generate actual_load + 80 kW (way above station load)
        wasteful_proposal = ActionProposal(
            title="Run Maximum Generation Reserves on Both CHPs",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[0].active_power_kw",
                    "value": actual_load + 40.0,
                },
                {
                    "pillar": "energy",
                    "path": "chps[1].active_power_kw",
                    "value": 40.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Maximize spinning reserve.",
        )

        critique = agent.critique_proposal(wasteful_proposal)

        assert critique is not None
        assert critique["violates_constraint"] == "EXCESSIVE_FUEL_CONSUMPTION"
        assert "Throttle surplus generator capacity" in critique["critique"]

    def test_pubsub_deliberation_session_critique_integration(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify bus pub/sub interception: receives PROPOSAL, publishes CRITIQUE to Planning and logs on blackboard."""
        agent, bus, engine, graph = setup_agent

        session = bus.create_session(trigger_alert={"anomaly": "HIGH_FUEL_BURN"})
        received_critiques: list[AgentMessage] = []

        bus.subscribe_type(MessageType.CRITIQUE, lambda msg: received_critiques.append(msg))

        bad_prop = ActionProposal(
            title="Dual Underloaded Generator Sequence",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[0].active_power_kw",
                    "value": 20.0,
                },
                {
                    "pillar": "energy",
                    "path": "chps[1].active_power_kw",
                    "value": 20.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Test wet-stacking pub/sub.",
        )

        bus.publish(
            AgentMessage(
                sender=AgentRole.PLANNING,
                recipient=AgentRole.RESOURCE_OPTIMIZER,
                message_type=MessageType.PROPOSAL,
                severity=SeverityLevel.WARNING,
                payload=bad_prop.to_dict(),
                session_id=session.session_id,
            )
        )

        assert len(received_critiques) == 1
        c_msg = received_critiques[0]
        assert c_msg.sender == AgentRole.RESOURCE_OPTIMIZER
        assert c_msg.recipient == AgentRole.PLANNING
        assert c_msg.payload["violates_constraint"] == "ENGINE_WET_STACKING_PREVENTION"

        assert len(session.critiques) == 1
        assert session.critiques[0]["violates_constraint"] == "ENGINE_WET_STACKING_PREVENTION"

    def test_interactive_query_response(
        self, setup_agent: tuple[ResourceOptimizerAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent responds to QUERY messages with detailed optimization plan."""
        agent, bus, engine, graph = setup_agent

        received_responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda msg: received_responses.append(msg))

        bus.publish(
            AgentMessage(
                sender=AgentRole.FRIDAY_ORCHESTRATOR,
                recipient=AgentRole.RESOURCE_OPTIMIZER,
                message_type=MessageType.QUERY,
                severity=SeverityLevel.INFO,
                payload={"objective": "MAX_FUEL_CONSERVATION"},
                session_id="SES-RES-QUERY-01",
            )
        )

        assert len(received_responses) == 1
        resp = received_responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert "resource_plan" in resp.payload
        assert resp.payload["resource_plan"]["objective"] == "MAX_FUEL_CONSERVATION"
