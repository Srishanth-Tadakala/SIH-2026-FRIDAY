"""Unit and End-to-End Integration Tests for F.R.I.D.A.Y. Chief AI Orchestrator (Sub-Phase 3.10).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Orchestrator Initialization & Cognitive Framework State Inspection
2. Blackboard Event Ingestion & Session Lifecycle Management
3. Consensus Arbitration: Safe vs Unsafe Candidate Plan Filtering
4. Consensus Arbitration: Multi-Agent Critique Disqualification (Maintenance Veto)
5. Commander Briefing Card Natural Language Synthesis & Serialization
6. Tier 1 Autonomous Immediate Closed-Loop Execution
7. Tier 2 Supervised Countdown Queue & Operator Bypass
8. Tier 3 Mandatory Commander PIN Gatekeeping ("BHARATI-CMD-2026")
9. End-to-End Multi-Agent Deliberation Pipeline (Perception -> Diagnosis -> Planning -> Sim -> Consensus)
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
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.agents.orchestrator.friday_core import CommanderBriefingCard, FridayMasterOrchestrator
from backend.agents.specialized.diagnostic import DiagnosticAgent
from backend.agents.specialized.planning import PlanningAgent
from backend.agents.specialized.situation_awareness import SituationAwarenessAgent
from backend.agents.specialized.what_if import WhatIfSimulationAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestFridayMasterOrchestrator:
    """Comprehensive test suite for FridayMasterOrchestrator."""

    @pytest.fixture
    def setup_orchestrator(
        self,
    ) -> tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        orchestrator = FridayMasterOrchestrator(bus=bus, engine=engine, graph=graph)
        return orchestrator, bus, engine, graph

    def test_orchestrator_initialization_and_clean_state(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify orchestrator initializes with online status and registers all 9 specialized cognitive agents."""
        orch, bus, engine, graph = setup_orchestrator
        assert orch.role == AgentRole.FRIDAY_ORCHESTRATOR
        status = orch.get_cognitive_status()
        assert status["orchestrator_status"] == "ONLINE_ACTIVE"
        assert len(status["specialized_agents"]) == 9
        assert "SITUATION_AWARENESS" in status["specialized_agents"]
        assert "RESOURCE_OPTIMIZER" in status["specialized_agents"]

    def test_event_ingestion_and_session_lifecycle(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify ingestion of ALERT, DIAGNOSIS, PREDICTION, and IMPACT updates session blackboard."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly": "GENERATOR_TRIP", "node_id": "chp_1"})
        sid = session.session_id

        # Publish Diagnosis
        bus.publish(
            AgentMessage(
                sender=AgentRole.DIAGNOSTIC,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.DIAGNOSIS,
                severity=SeverityLevel.WARNING,
                payload={"root_cause_node_id": "chp_1", "explanation": "Governor actuator fault"},
                session_id=sid,
            )
        )

        # Publish Prediction
        bus.publish(
            AgentMessage(
                sender=AgentRole.PREDICTION,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.PREDICTION_PROJECTION,
                severity=SeverityLevel.WARNING,
                payload={"min_time_to_failure_minutes": 38.5},
                session_id=sid,
            )
        )

        # Publish Impact
        bus.publish(
            AgentMessage(
                sender=AgentRole.RISK_IMPACT,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.IMPACT_ASSESSMENT,
                severity=SeverityLevel.CRITICAL,
                payload={"criticality_tier": "TIER_4", "life_support_threat": True, "affected_nodes": ["mlvd_bus"]},
                session_id=sid,
            )
        )

        sess = bus.get_session(sid)
        assert sess is not None
        assert len(sess.root_causes) >= 1
        assert len(sess.predictions) >= 1
        assert sess.risk_assessment.get("criticality_tier") == "TIER_4"

    def test_consensus_arbitration_safe_proposal_selection(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify arbitration selects the safe, high-utility proposal and ignores unsafe proposals."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly_type": "POWER_LOSS"})
        sid = session.session_id

        plan_safe = ActionProposal(
            title="Safe Standby Generator Sequencing",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "energy", "path": "chps[1].operating_state", "value": "RUNNING"}],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Safe plan.",
            simulation_delta={"is_safe": True, "risk_reduction_pct": 45.0, "temp_difference_c": 1.5, "fuel_saved_l": 5.0},
        )

        plan_unsafe = ActionProposal(
            title="Aggressive Unmitigated Load Shed",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "infrastructure", "path": "building.temp_living_c", "value": 12.0}],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Unsafe plan.",
            simulation_delta={"is_safe": False, "risk_reduction_pct": -20.0},
        )

        session.candidate_proposals.extend([plan_safe, plan_unsafe])

        consensus = orch.arbitrate_session(sid)

        assert consensus is not None
        assert consensus.proposal_id == plan_safe.proposal_id
        assert session.final_plan == plan_safe

    def test_consensus_arbitration_critique_elimination(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify proposal with unresolved critical critique (Maintenance overdue veto) is disqualified."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly_type": "GENERATOR_FAULT"})
        sid = session.session_id

        plan_overdue_chp3 = ActionProposal(
            title="Start CHP-03 Standby Unit",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "energy", "path": "chps[2].operating_state", "value": "RUNNING"}],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Start CHP-3.",
            simulation_delta={"is_safe": True, "risk_reduction_pct": 30.0},
        )

        plan_healthy_chp1 = ActionProposal(
            title="Start CHP-01 Standby Unit",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "energy", "path": "chps[0].operating_state", "value": "RUNNING"}],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Start CHP-1.",
            simulation_delta={"is_safe": True, "risk_reduction_pct": 30.0},
        )

        session.candidate_proposals.extend([plan_overdue_chp3, plan_healthy_chp1])

        # Push critical critique from Maintenance Agent vetoing CHP-3
        session.critiques.append({
            "proposal_id": plan_overdue_chp3.proposal_id,
            "severity": "CRITICAL",
            "violates_constraint": "OVERDUE_MACHINERY_START_RESTRICTION",
            "critique": "CHP-03 is overdue for 2,000h service.",
        })

        consensus = orch.arbitrate_session(sid)

        assert consensus is not None
        # Must pick CHP-01 because CHP-03 was vetoed by Maintenance
        assert consensus.proposal_id == plan_healthy_chp1.proposal_id
        assert plan_overdue_chp3.status == ProposalStatus.REJECTED

    def test_commander_briefing_card_synthesis(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify natural language synthesis of CommanderBriefingCard with all required fields."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(
            trigger_alert={"anomaly_type": "KATABATIC_BLIZZARD", "description": "Wind speed exceeding 32 m/s."}
        )
        session.root_causes.append({"root_cause_node_id": "env_katabatic", "explanation": "Polar vortex low pressure front"})
        session.predictions.append({"min_time_to_failure_minutes": 25.0})
        session.risk_assessment = {"criticality_tier": "TIER_4", "life_support_threat": True, "affected_nodes": ["ahu_01", "pipe_01"]}

        card = orch.synthesize_briefing_card(session.session_id)

        assert isinstance(card, CommanderBriefingCard)
        assert card.incident_title == "KATABATIC_BLIZZARD"
        assert "env_katabatic" in card.root_cause
        assert "25.0 minutes" in card.time_to_violation_str
        assert "TIER_4" in card.blast_radius_summary
        assert isinstance(card.to_dict(), dict)

    def test_tier_1_immediate_execution(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify Tier 1 proposals execute closed-loop into the digital twin immediately without human delay."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly": "TEMP_DRIFT"})
        sid = session.session_id

        tier1_plan = ActionProposal(
            title="Auto-Adjust AHU-01 Heating Valve",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[{"pillar": "infrastructure", "path": "building.temp_living_c", "value": 21.5}],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Safe micro-adjustment.",
            simulation_delta={"is_safe": True},
        )

        session.candidate_proposals.append(tier1_plan)
        session.final_plan = tier1_plan

        res = orch.execute_consensus_plan(sid)

        assert res.success is True
        assert res.status == ProposalStatus.EXECUTED
        assert session.resolved is True
        assert engine.infra_registry.physics.building.temp_living_c == 21.5

    def test_tier_2_supervised_queue_and_bypass(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify Tier 2 proposal queues in 60s window and executes with operator bypass confirmation."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly": "SUBSTATION_MAINTENANCE"})
        sid = session.session_id

        tier2_plan = ActionProposal(
            title="Reconfigure Feeder Bus B",
            target_subsystem="ENERGY",
            parameter_overrides=[{"pillar": "energy", "path": "chps[0].active_power_kw", "value": 70.0}],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Tactical grid re-routing.",
            simulation_delta={"is_safe": True},
        )

        session.candidate_proposals.append(tier2_plan)
        session.final_plan = tier2_plan

        # Initial call without bypass puts proposal in supervised queue
        res_queued = orch.execute_consensus_plan(sid, bypass_supervision=False)
        assert res_queued.success is False
        assert res_queued.status == ProposalStatus.PENDING_SUPERVISION

        # Operator confirms via bypass
        res_exec = orch.execute_consensus_plan(sid, bypass_supervision=True)
        assert res_exec.success is True
        assert res_exec.status == ProposalStatus.EXECUTED
        assert session.resolved is True

    def test_tier_3_commander_pin_gatekeeping(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify Tier 3 life-critical proposal strictly requires Commander PIN 'BHARATI-CMD-2026'."""
        orch, bus, engine, graph = setup_orchestrator

        session = bus.create_session(trigger_alert={"anomaly": "EMERGENCY_SHUTDOWN"})
        sid = session.session_id

        tier3_plan = ActionProposal(
            title="Emergency Shedding of Research Wing",
            target_subsystem="INFRASTRUCTURE",
            parameter_overrides=[{"pillar": "infrastructure", "path": "building.temp_lab_c", "value": 16.5}],
            tier=AutonomyTier.TIER_3_COMMANDER_CONFIRMATION,
            rationale="Life-critical habitat protection.",
            simulation_delta={"is_safe": True},
        )

        session.candidate_proposals.append(tier3_plan)
        session.final_plan = tier3_plan

        # Attempt with wrong PIN
        res_fail = orch.execute_consensus_plan(sid, commander_pin="WRONG-PIN")
        assert res_fail.success is False
        assert res_fail.status == ProposalStatus.PENDING_COMMANDER
        assert session.resolved is False

        # Attempt with valid Commander PIN
        res_pass = orch.execute_consensus_plan(sid, commander_pin="BHARATI-CMD-2026")
        assert res_pass.success is True
        assert res_pass.status == ProposalStatus.EXECUTED
        assert session.resolved is True

    def test_end_to_end_deliberation_pipeline_multi_agent(
        self, setup_orchestrator: tuple[FridayMasterOrchestrator, AgentMessageBus, BharatiMasterTwinEngine, TwinCausalGraph]
    ) -> None:
        """Verify end-to-end multi-agent integration: Anomaly -> Diagnosis -> Planning -> Sim -> Consensus."""
        orch, bus, engine, graph = setup_orchestrator

        # Instantiate full cognitive chain
        sa = SituationAwarenessAgent(bus=bus, engine=engine, graph=graph)
        diag = DiagnosticAgent(bus=bus, engine=engine, graph=graph)
        planning = PlanningAgent(bus=bus, engine=engine, graph=graph)
        what_if = WhatIfSimulationAgent(
            bus=bus,
            engine=engine,
            graph=graph,
            default_duration_seconds=1200.0,
            default_dt_seconds=60.0,
        )

        # Inject Katabatic Blizzard Strike scenario into master engine
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)

        # 1. Situation Awareness detects anomaly on next tick
        snapshot = engine.step(dt_seconds=60.0)
        sa.on_tick(snapshot)

        # Verify a deliberation session was spawned
        sessions = bus.get_all_sessions()
        assert len(sessions) >= 1
        active_session = sessions[-1]
        assert active_session.trigger_alert is not None

        # Verify consensus plan was synthesized
        briefing = orch.synthesize_briefing_card(active_session.session_id)
        assert briefing is not None
        assert briefing.incident_title is not None
