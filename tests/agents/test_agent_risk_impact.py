"""Unit and Integration Tests for Risk & Impact Agent (Sub-Phase 3.4).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean Message Bus Registration
2. Generator Trip Downstream Blast Radius & Life-Support Threat Quantification
3. Katabatic Blizzard Mission Impact & Helipad/Traverse Restrictions
4. Utilidor Pipe Freeze Water Cycle Threat Evaluation
5. Urgency Multiplier Escalation on Short Time-to-Violation
6. Deliberation Session Blackboard Integration & Pub/Sub Dispatch to Planning
7. Interactive Query Response for On-Demand Asset Impact Assessments
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
from backend.agents.specialized.risk_impact import ImpactAssessment, RiskImpactAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestRiskImpactAgent:
    """Comprehensive test suite for RiskImpactAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = RiskImpactAgent(bus, engine, graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with RISK_IMPACT role and empty local cache."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.RISK_IMPACT
        assert len(agent._assessments) == 0

    def test_generator_trip_blast_radius_assessment(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify generator trip yields extensive blast radius with life-support threats."""
        agent, bus, engine, graph = setup_agent

        assessment = agent.assess_impact(target_node_id="chp_1", session_id="SES-GEN-RSK-01")

        assert isinstance(assessment, ImpactAssessment)
        assert assessment.root_node_id == "chp_1"
        assert assessment.affected_asset_count >= 5
        assert assessment.life_support_threat is True
        assert assessment.composite_severity_score >= 60.0
        assert assessment.human_safety_risk in ("SEVERE", "LIFE_THREATENING")
        assert "ENERGY" in assessment.affected_subsystems
        assert len(assessment.containment_priorities) > 0

    def test_katabatic_blizzard_mission_impact(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify extreme katabatic winds threaten aviation and ground traverse operations."""
        agent, bus, engine, graph = setup_agent

        assessment = agent.assess_impact(target_node_id="env_katabatic", session_id="SES-BLZ-RSK-01")

        assert assessment.root_node_id == "env_katabatic"
        assert assessment.mission_impact_details["helipad_operational"] is False
        assert assessment.mission_impact_details["ground_traverse_clear"] is False
        assert any("NOTAM" in p or "air transport" in p for p in assessment.containment_priorities)

    def test_utilidor_pipe_freeze_water_cycle_threat(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify utilidor water line freezing flags water system life-support threat."""
        agent, bus, engine, graph = setup_agent

        assessment = agent.assess_impact(target_node_id="utilidor_water_line", session_id="SES-H2O-RSK-01")

        assert assessment.root_node_id == "utilidor_water_line"
        assert assessment.life_support_details["water_system_threatened"] is True
        assert any("fresh water line" in p for p in assessment.containment_priorities)

    def test_urgency_multiplier_short_time_to_violation(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify short Time-to-Violation accelerates composite severity score."""
        agent, bus, engine, graph = setup_agent

        # Baseline assessment without urgent time to breach
        base_asm = agent.assess_impact(target_node_id="reefer_01", time_to_critical_seconds=None)

        # Urgent assessment with breach projected in 15 minutes (900 seconds)
        urgent_asm = agent.assess_impact(target_node_id="reefer_01", time_to_critical_seconds=900.0)

        assert urgent_asm.composite_severity_score > base_asm.composite_severity_score
        assert urgent_asm.time_to_critical_seconds == 900.0

    def test_deliberation_session_blackboard_and_bus_dispatch(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify incoming PREDICTION_PROJECTION updates session blackboard and dispatches IMPACT_ASSESSMENT."""
        agent, bus, engine, graph = setup_agent

        # Create deliberation session on bus with diagnosed root cause
        session = bus.create_session(trigger_alert={"anomaly": "GENERATOR_TRIP"})
        session.root_causes.append({"root_cause_node_id": "chp_1"})
        sess_id = session.session_id

        # Capture downstream messages for Planning and Orchestrator
        plan_messages: list[AgentMessage] = []
        orch_messages: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.PLANNING, lambda m: plan_messages.append(m))
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: orch_messages.append(m))

        # Dispatch PREDICTION_PROJECTION message
        pred_msg = AgentMessage(
            sender=AgentRole.PREDICTION,
            recipient=AgentRole.RISK_IMPACT,
            message_type=MessageType.PREDICTION_PROJECTION,
            severity=SeverityLevel.CRITICAL,
            payload={
                "time_to_critical_seconds": 1800.0,
                "critical_breach_type": "THERMAL_LIFE_SUPPORT_BREACH",
            },
            session_id=sess_id,
        )
        bus.publish(pred_msg)

        # Verify session blackboard updated with risk_assessment
        assert session.risk_assessment is not None
        assert "composite_severity_score" in session.risk_assessment
        assert session.risk_assessment["root_node_id"] == "chp_1"

        # Verify dispatched messages
        plan_asm = [m for m in plan_messages if m.message_type == MessageType.IMPACT_ASSESSMENT]
        assert len(plan_asm) == 1
        assert plan_asm[0].payload["root_node_id"] == "chp_1"

        orch_asm = [m for m in orch_messages if m.message_type == MessageType.IMPACT_ASSESSMENT]
        assert len(orch_asm) == 1

    def test_interactive_query_response(
        self, setup_agent: tuple[RiskImpactAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent handles on-demand operator queries for specific node blast radius."""
        agent, bus, engine, graph = setup_agent

        responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: responses.append(m))

        query_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.RISK_IMPACT,
            message_type=MessageType.QUERY,
            severity=SeverityLevel.INFO,
            payload={"node_id": "reefer_01"},
            session_id="SES-QUERY-RSK-01",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        resp = responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert resp.payload["root_node_id"] == "reefer_01"
        assert "composite_severity_score" in resp.payload
        assert "containment_priorities" in resp.payload
