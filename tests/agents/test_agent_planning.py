"""Unit and Integration Tests for Planning / Recommendation Agent (Sub-Phase 3.5).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean Message Bus Registration
2. Generator Trip SOP Playbook Formulation (Standby CHP-02 Start & Load Shedding)
3. Utilidor Water Freeze Mitigation Playbook Formulation
4. Katabatic Blizzard HVAC Recirculation & Mission Grounding Playbook Formulation
5. Safety Interlock Guardrail Pre-Screening & Violation Rejection
6. Deliberation Session Blackboard Integration & Pub/Sub Dispatch to What-If Agent
7. Interactive Query Response for Operational Proposal Generation
"""

from __future__ import annotations

import pytest

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.models import (
    ActionProposal,
    AgentMessage,
    AgentRole,
    AutonomyTier,
    MessageType,
    ProposalStatus,
    SeverityLevel,
)
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.agents.specialized.planning import PlanningAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine


class TestPlanningAgent:
    """Comprehensive test suite for PlanningAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = PlanningAgent(bus, engine, graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with PLANNING role and empty cache."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.PLANNING
        assert len(agent._proposals) == 0

    def test_generator_trip_sop_proposal_formulation(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify generator trip yields standby sequencing and load-shedding proposals."""
        agent, bus, engine, graph = setup_agent

        proposals = agent.formulate_proposals(
            session_id="SES-GEN-PLAN-01",
            trigger_payload={"root_node_id": "chp_1"},
        )

        assert len(proposals) >= 2
        p1 = proposals[0]
        assert "CHP-02" in p1.title or "Standby" in p1.title
        assert p1.target_subsystem == "ENERGY"
        assert p1.tier == AutonomyTier.TIER_1_AUTONOMOUS
        assert any(o["path"] == "chps[1].operating_state" for o in p1.parameter_overrides)
        assert any(o["value"] == "RUNNING" for o in p1.parameter_overrides)

        p2 = proposals[1]
        assert "Load Shedding" in p2.title
        assert p2.target_subsystem == "ENERGY"

    def test_utilidor_freeze_mitigation_proposal(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify utilidor water line freezing formulates auxiliary trace heating proposals."""
        agent, bus, engine, graph = setup_agent

        proposals = agent.formulate_proposals(
            session_id="SES-H2O-PLAN-01",
            trigger_payload={"root_node_id": "utilidor_water_line"},
        )

        assert len(proposals) >= 1
        p = proposals[0]
        assert "Trace Heating" in p.title
        assert p.target_subsystem == "INFRASTRUCTURE"
        assert any(o["path"] == "pipelines.water01_trace_heating_on" for o in p.parameter_overrides)
        assert any(o["value"] is True for o in p.parameter_overrides)

    def test_katabatic_blizzard_hvac_recirculation_proposal(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify blizzard wind surge formulates HVAC damper recirculation and mission hold proposals."""
        agent, bus, engine, graph = setup_agent

        proposals = agent.formulate_proposals(
            session_id="SES-BLZ-PLAN-01",
            trigger_payload={"root_node_id": "env_katabatic"},
        )

        assert len(proposals) >= 2
        p_hvac = proposals[0]
        assert "Recirculation" in p_hvac.title or "AHU" in p_hvac.title
        assert p_hvac.target_subsystem == "INFRASTRUCTURE"

        p_ops = proposals[1]
        assert "Traverses" in p_ops.title or "Flight" in p_ops.title
        assert p_ops.target_subsystem == "LOGISTICS"

    def test_safety_interlock_guardrail_rejection_of_invalid_proposal(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify proposals attempting to violate life-support floor (< 16°C) are rejected by safety manager."""
        agent, bus, engine, graph = setup_agent

        # Unsafe proposal attempting to set habitat temp to 12.0°C
        unsafe_proposal = ActionProposal(
            title="Aggressive Thermal Load Shedding",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[
                {
                    "pillar": "infrastructure",
                    "path": "building.temp_living_c",
                    "value": 12.0,  # Below 16.0°C life-support floor
                }
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Aggressively shed heating to conserve power.",
        )

        agent._dispatch_proposals([unsafe_proposal], "SES-UNSAFE-01", None)

        assert unsafe_proposal.status == ProposalStatus.REJECTED
        assert "ERR_THERMAL_LIFE_SUPPORT" in unsafe_proposal.rationale

    def test_deliberation_session_blackboard_and_whatif_dispatch(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify incoming IMPACT_ASSESSMENT updates session candidate_proposals and dispatches PROPOSAL."""
        agent, bus, engine, graph = setup_agent

        # Create deliberation session on bus
        session = bus.create_session(trigger_alert={"anomaly": "GENERATOR_TRIP"})
        session.root_causes.append({"root_cause_node_id": "chp_1"})
        sess_id = session.session_id

        # Capture downstream messages for What-If Agent and Orchestrator
        whatif_messages: list[AgentMessage] = []
        orch_messages: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.WHAT_IF, lambda m: whatif_messages.append(m))
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: orch_messages.append(m))

        # Publish IMPACT_ASSESSMENT
        impact_msg = AgentMessage(
            sender=AgentRole.RISK_IMPACT,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.IMPACT_ASSESSMENT,
            severity=SeverityLevel.CRITICAL,
            payload={
                "root_node_id": "chp_1",
                "composite_severity_score": 75.0,
            },
            session_id=sess_id,
        )
        bus.publish(impact_msg)

        # Verify candidate proposals recorded on session blackboard
        assert len(session.candidate_proposals) >= 1
        assert session.candidate_proposals[0].target_subsystem == "ENERGY"

        # Verify PROPOSAL messages dispatched to What-If Agent
        whatif_props = [m for m in whatif_messages if m.message_type == MessageType.PROPOSAL]
        assert len(whatif_props) >= 1
        assert whatif_props[0].payload["target_subsystem"] == "ENERGY"

        # Verify PROPOSAL messages dispatched to Orchestrator
        orch_props = [m for m in orch_messages if m.message_type == MessageType.PROPOSAL]
        assert len(orch_props) >= 1

    def test_interactive_query_response(
        self, setup_agent: tuple[PlanningAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent handles direct operator queries and returns candidate proposals."""
        agent, bus, engine, graph = setup_agent

        responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: responses.append(m))

        query_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.QUERY,
            severity=SeverityLevel.INFO,
            payload={"node_id": "day_tank"},
            session_id="SES-QUERY-PLAN-01",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        resp = responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert "proposals" in resp.payload
        assert len(resp.payload["proposals"]) >= 1
        assert "Fuel Farm" in resp.payload["proposals"][0]["title"]
