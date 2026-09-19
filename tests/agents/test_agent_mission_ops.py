"""Unit and Integration Tests for Mission Operations Cognitive Agent (Sub-Phase 3.7).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean State Registration
2. Nominal Mission Envelope Assessment (Safe Weather, Open Traverses)
3. Blizzard Severe Weather Triggers & Mandatory Recall (Grounded Aviation, Closed Routes)
4. Field Team Overdue & Radio Silence Distress Detection
5. Cyclic Deliberation Critique: Defense of Mission Communications Infrastructure
6. Cyclic Deliberation Critique: Outdoor Blizzard Crew Exposure Veto
7. Deliberation Session Pub/Sub Interception & Critique Blackboard Recording
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
from backend.agents.specialized.mission_ops import (
    FieldPartyStatus,
    MissionFeasibilityAssessment,
    MissionOperationalStatus,
    MissionOpsAgent,
)
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestMissionOpsAgent:
    """Comprehensive test suite for MissionOpsAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = MissionOpsAgent(bus=bus, engine=engine, graph=graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with MISSION_OPS role and clean state."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.MISSION_OPS
        assert agent._latest_assessment is None

    def test_nominal_mission_envelope_assessment(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify nominal weather conditions result in open routes and clear flight status."""
        agent, bus, engine, graph = setup_agent

        assessment = agent.assess_mission_envelope()

        assert isinstance(assessment, MissionFeasibilityAssessment)
        assert assessment.overall_status in (MissionOperationalStatus.NOMINAL, MissionOperationalStatus.ADVISORY)
        assert assessment.aviation_status in ("CLEAR", "CAUTION")
        assert assessment.ground_traverse_status in ("OPEN", "CAUTION")
        assert "wind_chill_c" in assessment.weather_summary
        assert len(assessment.field_parties) >= 1
        assert assessment.field_parties[0].team_id == "TEAM-FIELD-01"

    def test_blizzard_severe_weather_mandatory_recall(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify katabatic blizzard conditions trigger immediate flight grounding and traverse recall."""
        agent, bus, engine, graph = setup_agent

        # Inject extreme blizzard into master engine
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)

        assessment = agent.assess_mission_envelope()

        assert assessment.overall_status == MissionOperationalStatus.RECALL_MANDATORY
        assert assessment.aviation_status == "GROUNDED"
        assert assessment.ground_traverse_status == "CLOSED"
        assert len(assessment.mandatory_actions) > 0
        assert any("RECALL" in action for action in assessment.mandatory_actions)

    def test_field_team_overdue_and_radio_loss_detection(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify detection of overdue return margin and lost radio communication."""
        agent, bus, engine, graph = setup_agent

        # Simulate overdue field team with radio silence
        log_phy = engine.logistics_registry.physics
        log_phy.missions.team01.status = "IN_PROGRESS"
        log_phy.missions.team01.return_margin_minutes = -35.0  # 35 minutes overdue
        log_phy.missions.team01.radio_check_status = "SILENCE"

        assessment = agent.assess_mission_envelope()

        assert assessment.overall_status == MissionOperationalStatus.RECALL_MANDATORY
        t1 = assessment.field_parties[0]
        assert t1.is_safe is False
        assert "Radio check SILENCE" in t1.safety_note
        assert "Overdue" in t1.safety_note
        assert any("search party" in a.lower() for a in assessment.mandatory_actions)

    def test_cyclic_critique_defense_of_mission_comms(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent vetoes any proposal that attempts to shed communications during field deployment."""
        agent, bus, engine, graph = setup_agent

        # Field party is actively out
        engine.logistics_registry.physics.missions.field_personnel_count = 3.0
        engine.logistics_registry.physics.missions.team01.status = "IN_PROGRESS"

        dangerous_proposal = ActionProposal(
            title="Load Shedding: Turn Off Telemetry and Radio Mast Repeater",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "comms.radio_repeater_power",
                    "value": False,
                }
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Shed secondary electrical bus loads.",
        )

        critique = agent.critique_proposal(dangerous_proposal)

        assert critique is not None
        assert critique["violates_constraint"] == "MISSION_COMMS_PRESERVATION"
        assert critique["severity"] == "CRITICAL"
        assert "VETO/CRITIQUE" in critique["critique"]
        assert "Team 01" in critique["critique"]

    def test_cyclic_critique_outdoor_blizzard_exposure_veto(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent vetoes plans scheduling outdoor physical tasks during severe blizzard."""
        agent, bus, engine, graph = setup_agent

        # Set severe blizzard wind
        engine.env_registry.physics.weather.wind_speed_mps = 30.0

        outdoor_proposal = ActionProposal(
            title="Manual Outdoor Fuel Valve Realignment",
            target_subsystem="LOGISTICS",
            parameter_overrides=[
                {
                    "pillar": "logistics",
                    "path": "outdoor.snowcat_transfer_skid",
                    "value": True,
                }
            ],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Send technician to realign exterior transfer valve.",
        )

        critique = agent.critique_proposal(outdoor_proposal)

        assert critique is not None
        assert critique["violates_constraint"] == "OUTDOOR_CREW_EXPOSURE_LIMIT"
        assert "VETO/CRITIQUE" in critique["critique"]
        assert "blizzard" in critique["critique"].lower()

    def test_pubsub_deliberation_session_critique_dispatch(
        self, setup_agent: tuple[MissionOpsAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify bus message interception: receives PROPOSAL, publishes CRITIQUE to Planning and blackboard."""
        agent, bus, engine, graph = setup_agent

        session = bus.create_session(trigger_alert={"anomaly": "POWER_DEFICIT"})
        received_critiques: list[AgentMessage] = []

        bus.subscribe_type(MessageType.CRITIQUE, lambda msg: received_critiques.append(msg))

        # Ensure field team is deployed
        engine.logistics_registry.physics.missions.field_personnel_count = 4.0
        engine.logistics_registry.physics.missions.team01.status = "IN_PROGRESS"

        prop_cutting_comms = ActionProposal(
            title="Emergency Shedding of Comms Antenna Mast",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "subsystem.satcom_antenna_heater",
                    "value": False,
                }
            ],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Cut satcom power to save kW.",
        )

        # Dispatch proposal to bus
        bus.publish(
            AgentMessage(
                sender=AgentRole.PLANNING,
                recipient=AgentRole.MISSION_OPS,
                message_type=MessageType.PROPOSAL,
                severity=SeverityLevel.WARNING,
                payload=prop_cutting_comms.to_dict(),
                session_id=session.session_id,
            )
        )

        assert len(received_critiques) == 1
        critique_msg = received_critiques[0]
        assert critique_msg.sender == AgentRole.MISSION_OPS
        assert critique_msg.recipient == AgentRole.PLANNING
        assert critique_msg.payload["violates_constraint"] == "MISSION_COMMS_PRESERVATION"

        # Verify critique recorded on session blackboard
        assert len(session.critiques) == 1
        assert session.critiques[0]["violates_constraint"] == "MISSION_COMMS_PRESERVATION"
