"""Planning / Recommendation Agent for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

COGNITIVE OBJECTIVE:
"What operational actions could be considered to resolve the incident safely?"

RESPONSIBILITIES:
1. Operational Playbook Formulation: Synthesizes diagnosed root causes, lookahead trajectories,
   and blast radius constraints to draft candidate ActionProposals.
2. Standard Operating Procedure (SOP) Matching: Maps physical faults to Antarctic station SOPs:
   - Generator trip -> Auto-start standby CHP-02, balance bus, load-shed non-critical labs.
   - Utilidor freeze -> Engage secondary trace heating, increase recirculation flow.
   - Katabatic blizzard -> Transition HVAC dampers to 90% recirc, elevate buffer heating.
   - Cold chain excursion -> Transfer auxiliary electrical feeder, restart compressor.
   - Fuel depletion -> Activate transfer pump skid from bulk fuel farm.
3. Tiered Autonomy Classification: Classifies proposals into Tier 1 (safe autonomous),
   Tier 2 (supervised 60s countdown), or Tier 3 (Commander PIN required).
4. Safety Pre-Screening: Validates candidate parameter overrides against Antarctic life-support
   guardrails via SafetyInterlockManager prior to dispatch.
5. Multi-Agent Deliberation Integration:
   - Dispatches PROPOSAL messages to What-If Agent (for forward sandbox simulation).
   - Dispatches PROPOSAL messages to F.R.I.D.A.Y. Chief AI Orchestrator.
   - Appends to DeliberationSession.candidate_proposals on the shared blackboard.
6. Interactive Query Support: Generates on-demand mitigation plans for operator queries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Literal
import uuid

from ...core.causal_graph import TwinCausalGraph
from ...core.engine import BharatiMasterTwinEngine
from ..framework.base_agent import BaseSpecializedAgent
from ..framework.bus import AgentMessageBus
from ..framework.models import (
    ActionProposal,
    AgentMessage,
    AgentRole,
    AutonomyTier,
    DeliberationSession,
    MessageType,
    ProposalStatus,
    SeverityLevel,
)
from ..framework.safety_interlock import SafetyInterlockManager
from ..framework.groq_brain import GroqBrainEngine


class PlanningAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for formulating operational mitigation action proposals."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
        episodes_repo: Any | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.PLANNING,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )
        self.episodes_repo = episodes_repo

        # Listen to incoming DIAGNOSIS and IMPACT_ASSESSMENT messages
        self.bus.subscribe_type(MessageType.IMPACT_ASSESSMENT, self.on_impact_assessment_received)
        self.bus.subscribe_type(MessageType.DIAGNOSIS, self.on_diagnosis_received)

        # Audit cache of generated proposals: proposal_id -> ActionProposal
        self._proposals: dict[str, ActionProposal] = {}

    def on_impact_assessment_received(self, message: AgentMessage) -> None:
        """Trigger comprehensive planning when an impact assessment is published."""
        session_id = message.session_id
        session = self.bus.get_session(session_id) if session_id else None

        proposals = self.formulate_proposals(
            session_id=session_id,
            trigger_payload=message.payload,
            session=session,
        )

        self._dispatch_proposals(proposals, session_id, session)

    def on_diagnosis_received(self, message: AgentMessage) -> None:
        """Formulate preliminary proposals upon receiving an initial diagnosis."""
        session_id = message.session_id
        session = self.bus.get_session(session_id) if session_id else None

        # Only formulate if session doesn't already have candidate proposals
        if session and session.candidate_proposals:
            return

        proposals = self.formulate_proposals(
            session_id=session_id,
            trigger_payload=message.payload,
            session=session,
        )

        self._dispatch_proposals(proposals, session_id, session)

    def _dispatch_proposals(
        self,
        proposals: list[ActionProposal],
        session_id: str,
        session: DeliberationSession | None,
    ) -> None:
        """Validate and dispatch candidate action proposals to What-If Agent and Orchestrator."""
        for proposal in proposals:
            # Pre-validate with safety interlocks
            val_res = self.safety_interlock.validate_proposal(proposal, self.engine)
            if not val_res.is_valid:
                proposal.status = ProposalStatus.REJECTED
                proposal.rationale += f" [SAFETY INTERLOCK REJECTION: {val_res.violation_code} - {val_res.violation_reason}]"
            else:
                proposal.tier = val_res.assigned_tier

            self._proposals[proposal.proposal_id] = proposal

            if session:
                session.candidate_proposals.append(proposal)

            prop_payload = proposal.to_dict()
            severity = (
                SeverityLevel.CRITICAL
                if proposal.tier == AutonomyTier.TIER_3_COMMANDER_CONFIRMATION
                else (
                    SeverityLevel.WARNING
                    if proposal.tier == AutonomyTier.TIER_2_SUPERVISED
                    else SeverityLevel.INFO
                )
            )

            # 1. Dispatch to What-If Agent for sandbox simulation verification
            self.publish_message(
                session_id=session_id,
                recipient=AgentRole.WHAT_IF,
                message_type=MessageType.PROPOSAL,
                severity=severity,
                payload=prop_payload,
                confidence=1.0,
            )

            # 2. Dispatch to F.R.I.D.A.Y. Chief AI Orchestrator
            self.publish_message(
                session_id=session_id,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.PROPOSAL,
                severity=severity,
                payload=prop_payload,
                confidence=1.0,
            )

    def handle_message(self, message: AgentMessage) -> None:
        """Handle direct operational queries from operator or orchestrator."""
        if message.message_type == MessageType.QUERY:
            node_id = message.payload.get("node_id", "chp_1")
            proposals = self.formulate_proposals(
                session_id=message.session_id,
                trigger_payload={"root_node_id": node_id, "root_cause_node_id": node_id},
            )

            for prop in proposals:
                self._proposals[prop.proposal_id] = prop

            self.publish_message(
                session_id=message.session_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                severity=SeverityLevel.INFO,
                payload={"proposals": [p.to_dict() for p in proposals]},
                confidence=1.0,
            )

    def formulate_proposals(
        self,
        session_id: str = "",
        trigger_payload: dict[str, Any] | None = None,
        session: DeliberationSession | None = None,
    ) -> list[ActionProposal]:
        """Synthesize incident context and formulate prioritized candidate ActionProposals."""
        trigger_payload = trigger_payload or {}
        root_node_id = (
            trigger_payload.get("root_node_id")
            or trigger_payload.get("root_cause_node_id")
            or (session.root_causes[0].get("root_cause_node_id") if session and session.root_causes else "chp_1")
        )

        # Dynamic Cognitive Plan Formulation via Groq LPU (Zero Rule-Based Playbooks)
        brain = GroqBrainEngine.get_instance()
        kpis = self.engine.get_station_kpis() if self.engine else {}

        # Retrieve empirical case precedents from episodic memory repository
        precedents: list[dict[str, Any]] = []
        if self.episodes_repo:
            try:
                precedents = self.episodes_repo.find_similar(root_node_id, limit=2)
            except Exception:
                precedents = []

        if not precedents:
            precedents = [
                {
                    "episode_id": "EP-HIST-DEFAULT",
                    "lessons_learned": "Prioritize life-support thermal inertia and balance 400V microgrid bus.",
                }
            ]

        weather = {
            "wind_speed_ms": kpis.get("wind_speed_ms", 15.0),
            "temp_c": kpis.get("ambient_temp_c", -18.0),
        }

        raw_proposals = brain.run_sync(
            brain.reason_planning(
                root_cause_id=root_node_id,
                causal_chain=[root_node_id],
                station_kpis=kpis,
                historical_precedents=precedents,
                weather=weather,
            )
        ) or []

        proposals: list[ActionProposal] = []
        for raw in raw_proposals:
            tier_val = raw.get("tier", "TIER_1_AUTONOMOUS")
            if isinstance(tier_val, str):
                try:
                    tier_enum = AutonomyTier[tier_val]
                except KeyError:
                    tier_enum = AutonomyTier.TIER_1_AUTONOMOUS
            elif isinstance(tier_val, AutonomyTier):
                tier_enum = tier_val
            else:
                tier_enum = AutonomyTier.TIER_1_AUTONOMOUS

            p = ActionProposal(
                title=raw.get("title", f"Dynamic Mitigation for {root_node_id}"),
                target_subsystem=raw.get("target_subsystem", "ENERGY"),
                parameter_overrides=raw.get("parameter_overrides", []),
                tier=tier_enum,
                rationale=raw.get("rationale", f"Reasoned mitigation for {root_node_id}"),
                projected_impact=raw.get("projected_impact", {}),
            )
            proposals.append(p)

        return proposals
