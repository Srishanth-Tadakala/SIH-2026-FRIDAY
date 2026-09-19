"""Unit and Integration Tests for What-If / Simulation Cognitive Agent (Sub-Phase 3.6).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean Message Bus Registration
2. Counterfactual Simulation: Baseline vs Candidate Trajectory Delta Scoring
3. Unsafe Plan Rejection & Counterfactual Critique Formulation
4. Pub/Sub Proposal Evaluation & Cyclic Feedback Loop (SIM_RESULT + CRITIQUE)
5. Multi-Proposal Comparative Ranking & Trade-Off Analysis
6. Explicit Simulation Request Handling & Response Dispatch
7. Zero Mutation Contamination of Master Engine State
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
    ProposalStatus,
    SeverityLevel,
)
from backend.agents.specialized.what_if import PlanSimulationVerdict, WhatIfSimulationAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestWhatIfSimulationAgent:
    """Comprehensive test suite for WhatIfSimulationAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = WhatIfSimulationAgent(
            bus=bus,
            engine=engine,
            graph=graph,
            default_duration_seconds=3600.0,  # 1 hour for fast test execution
            default_dt_seconds=60.0,
        )
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with WHAT_IF role and clean verdict history."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.WHAT_IF
        assert len(agent._verdicts) == 0
        assert len(agent._sim_history) == 0
        assert agent.default_duration_seconds == 3600.0

    def test_counterfactual_simulation_baseline_vs_candidate(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify candidate proposal is evaluated against baseline and populates delta metrics."""
        agent, bus, engine, graph = setup_agent

        # Simulate generator trip scenario
        engine.inject_scenario(MasterScenario.GENERATOR_TRIP)

        proposal = ActionProposal(
            title="Auto-Sequence Standby CHP-02 to Active Duty",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[1].operating_state",
                    "value": "RUNNING",
                },
                {
                    "pillar": "energy",
                    "path": "chps[1].active_power_kw",
                    "value": 65.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Start standby generator to restore bus voltage and thermal loop.",
        )

        verdict = agent.evaluate_proposal(proposal, duration_seconds=1800.0, dt_seconds=60.0)

        assert isinstance(verdict, PlanSimulationVerdict)
        assert verdict.proposal_id == proposal.proposal_id
        assert verdict.plan_title == proposal.title
        assert verdict.duration_hours == 0.5
        assert verdict.recommendation in ("APPROVE", "MODIFY")
        assert proposal.simulation_delta is not None
        assert proposal.simulation_delta["proposal_id"] == proposal.proposal_id
        assert proposal.status == ProposalStatus.SIMULATED
        assert verdict.proposal_id in agent._verdicts

    def test_unsafe_plan_rejection_and_counterfactual_critique(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify plans violating life-support floors are rejected with detailed critiques."""
        agent, bus, engine, graph = setup_agent

        # Inject extreme cold override that forces indoor temp below 16.0°C life-support floor
        unsafe_proposal = ActionProposal(
            title="Severe Load Shedding of Life-Support Heaters",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 11.5,
                }
            ],
            tier=AutonomyTier.TIER_3_COMMANDER_CONFIRMATION,
            rationale="Aggressively shut down heating to conserve battery buffer.",
        )

        verdict = agent.evaluate_proposal(unsafe_proposal, duration_seconds=1800.0, dt_seconds=60.0)

        assert verdict.is_safe is False
        assert verdict.recommendation == "REJECT"
        assert len(verdict.violations) > 0
        assert any("16" in v for v in verdict.violations)
        assert verdict.counterfactual_critique is not None
        assert "CRITIQUE" in verdict.counterfactual_critique
        assert unsafe_proposal.status == ProposalStatus.REJECTED

    def test_pubsub_proposal_evaluation_and_feedback_dispatch(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify pub-sub message flow: receives PROPOSAL, dispatches SIM_RESULT and CRITIQUE."""
        agent, bus, engine, graph = setup_agent

        session = bus.create_session(trigger_alert={"anomaly": "TEMP_DROP"})
        received_messages: list[AgentMessage] = []

        bus.subscribe_type(MessageType.SIM_RESULT, lambda msg: received_messages.append(msg))
        bus.subscribe_type(MessageType.CRITIQUE, lambda msg: received_messages.append(msg))

        unsafe_prop = ActionProposal(
            title="Shed Habitat Heating During Blizzard",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 12.0,
                }
            ],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Test unsafe proposal dispatch.",
        )

        # Dispatch proposal to WHAT_IF agent
        bus.publish(
            AgentMessage(
                sender=AgentRole.PLANNING,
                recipient=AgentRole.WHAT_IF,
                message_type=MessageType.PROPOSAL,
                severity=SeverityLevel.WARNING,
                payload=unsafe_prop.to_dict(),
                session_id=session.session_id,
            )
        )

        sim_results = [m for m in received_messages if m.message_type == MessageType.SIM_RESULT]
        critiques = [m for m in received_messages if m.message_type == MessageType.CRITIQUE]

        # Verify SIM_RESULT was broadcast to Orchestrator and Planning
        assert len(sim_results) >= 1
        # Verify CRITIQUE was published to Planning because the plan was unsafe
        assert len(critiques) >= 1
        assert critiques[0].recipient == AgentRole.PLANNING
        assert len(session.critiques) >= 1
        assert session.critiques[0]["recommended_action"] == "REGENERATE_OR_MODIFY"

    def test_multi_proposal_comparative_ranking(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify multiple candidate proposals are simulated and ranked safely."""
        agent, bus, engine, graph = setup_agent

        plan_safe = ActionProposal(
            title="Safe Plan: Auxiliary Warmup",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 21.0,
                }
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Maintain comfortable living environment.",
        )

        plan_unsafe = ActionProposal(
            title="Unsafe Plan: Zero Heating",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 9.0,
                }
            ],
            tier=AutonomyTier.TIER_3_COMMANDER_CONFIRMATION,
            rationale="Hypothermia hazard test.",
        )

        verdicts = agent.compare_proposals([plan_unsafe, plan_safe], duration_seconds=1200.0, dt_seconds=60.0)

        assert len(verdicts) == 2
        # The safe plan MUST be ranked first
        assert verdicts[0].plan_title == plan_safe.title
        assert verdicts[0].is_safe is True
        assert verdicts[1].plan_title == plan_unsafe.title
        assert verdicts[1].is_safe is False

    def test_explicit_sim_request_handling(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify handling of direct SIM_REQUEST messages with custom horizons."""
        agent, bus, engine, graph = setup_agent

        received_responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda msg: received_responses.append(msg))

        req_message = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.WHAT_IF,
            message_type=MessageType.SIM_REQUEST,
            severity=SeverityLevel.INFO,
            payload={
                "proposal": {
                    "proposal_id": "ACT-CUSTOM-01",
                    "title": "Custom Test Sim",
                    "parameter_overrides": [],
                },
                "duration_seconds": 1800.0,
                "dt_seconds": 60.0,
            },
            session_id="SES-SIM-001",
        )

        bus.publish(req_message)

        assert len(received_responses) == 1
        resp = received_responses[0]
        assert resp.message_type == MessageType.SIM_RESULT
        assert resp.payload["proposal_id"] == "ACT-CUSTOM-01"
        assert resp.payload["duration_hours"] == 0.5

    def test_zero_mutation_contamination(
        self, setup_agent: tuple[WhatIfSimulationAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify that forward simulations run in complete memory isolation without altering master twin."""
        agent, bus, engine, graph = setup_agent

        initial_time = engine.clock.elapsed_seconds
        initial_temp = engine.infra_registry.physics.building.temp_living_c
        initial_chp_kw = engine.energy_registry.physics.chps[0].active_power_kw

        radical_proposal = ActionProposal(
            title="Radical Test Proposal",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 35.0,
                },
                {
                    "pillar": "energy",
                    "path": "chps[0].active_power_kw",
                    "value": 150.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Ensure isolated simulation does not mutate master state.",
        )

        # Run multi-step forward simulation
        verdict = agent.evaluate_proposal(radical_proposal, duration_seconds=3600.0, dt_seconds=60.0)

        assert verdict is not None
        # Master twin state MUST remain exactly as it was prior to simulation
        assert engine.clock.elapsed_seconds == initial_time
        assert engine.infra_registry.physics.building.temp_living_c == initial_temp
        assert engine.energy_registry.physics.chps[0].active_power_kw == initial_chp_kw
