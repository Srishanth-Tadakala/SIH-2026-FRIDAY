"""Unit and Integration Tests for Maintenance Cognitive Agent (Sub-Phase 3.8).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Clean State Registration
2. Machine Run-Hour & Spares Inventory Maintenance Report Generation
3. Overdue Rotating Asset Detection (CHP-03 Overdue 2,000h Service)
4. Cyclic Deliberation Critique: Vetoing Startup of Overdue Machinery
5. Safe Machinery Action Acceptance (No Unnecessary Veto)
6. Deliberation Session Blackboard Critique Pub/Sub Integration
7. Interactive Maintenance Query Handling & Diagnostic Response
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
from backend.agents.specialized.maintenance import (
    AssetMaintenanceProfile,
    MaintenanceAgent,
    MaintenanceHealthReport,
    MaintenanceUrgency,
)
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine


class TestMaintenanceAgent:
    """Comprehensive test suite for MaintenanceAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = MaintenanceAgent(bus=bus, engine=engine, graph=graph)
        return agent, bus, engine, graph

    def test_initialization_and_clean_state(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent initializes with MAINTENANCE role and clean state."""
        agent, bus, engine, graph = setup_agent
        assert agent.role == AgentRole.MAINTENANCE
        assert agent._latest_report is None

    def test_generate_maintenance_report_chp_and_fleet(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify report generation aggregates machine hours, wear %, and inventory spares."""
        agent, bus, engine, graph = setup_agent

        report = agent.generate_maintenance_report()

        assert isinstance(report, MaintenanceHealthReport)
        assert report.station_id == "BHARATI"
        assert len(report.assets) >= 5

        asset_ids = {a.asset_id for a in report.assets}
        assert "chp_1" in asset_ids
        assert "chp_2" in asset_ids
        assert "chp_3" in asset_ids
        assert "pb01" in asset_ids
        assert "heli" in asset_ids

        for asset in report.assets:
            assert 0.0 <= asset.wear_percent <= 100.0
            assert asset.current_runtime_hours >= 0.0

        assert "generator_spares_percent" in report.inventory_spares_summary
        assert "vehicle_spares_percent" in report.inventory_spares_summary

    def test_overdue_asset_flagging(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify overdue machine (CHP-03 with 2190h on 2000h interval) is flagged OVERDUE."""
        agent, bus, engine, graph = setup_agent

        report = agent.generate_maintenance_report()

        chp3_profile = next(a for a in report.assets if a.asset_id == "chp_3")
        assert chp3_profile.urgency == MaintenanceUrgency.OVERDUE
        assert report.overdue_assets_count >= 1
        assert "2,000h service required" in chp3_profile.recommended_action
        assert any("Unit 3" in adv and "OVERDUE" in adv for adv in report.advisories)

    def test_cyclic_critique_overdue_generator_start_veto(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent vetoes candidate proposal that attempts to start overdue generator CHP-03."""
        agent, bus, engine, graph = setup_agent

        proposal_starting_chp3 = ActionProposal(
            title="Auto-Sequence Standby CHP-03 to Full Active Load",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[2].operating_state",
                    "value": "RUNNING",
                },
                {
                    "pillar": "energy",
                    "path": "chps[2].active_power_kw",
                    "value": 65.0,
                },
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Bring CHP-3 online to replace tripped unit.",
        )

        critique = agent.critique_proposal(proposal_starting_chp3)

        assert critique is not None
        assert critique["violates_constraint"] == "OVERDUE_MACHINERY_START_RESTRICTION"
        assert critique["severity"] == "CRITICAL"
        assert "OVERDUE" in critique["critique"]
        assert "Combined Heat & Power Unit 3" in critique["critique"]
        # Must recommend a healthy alternative generator (e.g. CHP-1 or CHP-2)
        assert "Switch to Combined Heat & Power Unit" in critique["critique"]

    def test_safe_generator_proposal_no_critique(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent permits proposal that commands a healthy machine with ample MTBF margin."""
        agent, bus, engine, graph = setup_agent

        proposal_starting_chp1 = ActionProposal(
            title="Auto-Sequence Standby CHP-01 to Full Active Load",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[0].operating_state",
                    "value": "RUNNING",
                }
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Start healthy unit CHP-01.",
        )

        critique = agent.critique_proposal(proposal_starting_chp1)
        assert critique is None  # Permitted without critique

    def test_pubsub_deliberation_session_critique_recording(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify bus pub/sub interception: receives PROPOSAL for overdue unit, publishes CRITIQUE to Planning."""
        agent, bus, engine, graph = setup_agent

        session = bus.create_session(trigger_alert={"anomaly": "GENERATOR_TRIP"})
        received_critiques: list[AgentMessage] = []

        bus.subscribe_type(MessageType.CRITIQUE, lambda msg: received_critiques.append(msg))

        bad_prop = ActionProposal(
            title="Start Standby CHP-03 for Microgrid Backup",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {
                    "pillar": "energy",
                    "path": "chps[2].operating_state",
                    "value": "RUNNING",
                }
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Power test.",
        )

        bus.publish(
            AgentMessage(
                sender=AgentRole.PLANNING,
                recipient=AgentRole.MAINTENANCE,
                message_type=MessageType.PROPOSAL,
                severity=SeverityLevel.WARNING,
                payload=bad_prop.to_dict(),
                session_id=session.session_id,
            )
        )

        assert len(received_critiques) == 1
        c_msg = received_critiques[0]
        assert c_msg.sender == AgentRole.MAINTENANCE
        assert c_msg.recipient == AgentRole.PLANNING
        assert c_msg.payload["violates_constraint"] == "OVERDUE_MACHINERY_START_RESTRICTION"

        assert len(session.critiques) == 1
        assert session.critiques[0]["violates_constraint"] == "OVERDUE_MACHINERY_START_RESTRICTION"

    def test_interactive_query_response(
        self, setup_agent: tuple[MaintenanceAgent, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify agent responds to QUERY messages with detailed maintenance report."""
        agent, bus, engine, graph = setup_agent

        received_responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda msg: received_responses.append(msg))

        bus.publish(
            AgentMessage(
                sender=AgentRole.FRIDAY_ORCHESTRATOR,
                recipient=AgentRole.MAINTENANCE,
                message_type=MessageType.QUERY,
                severity=SeverityLevel.INFO,
                payload={"query": "asset_status"},
                session_id="SES-MNT-QUERY-01",
            )
        )

        assert len(received_responses) == 1
        resp = received_responses[0]
        assert resp.message_type == MessageType.RESPONSE
        assert "maintenance_report" in resp.payload
        assert resp.payload["maintenance_report"]["station_id"] == "BHARATI"
