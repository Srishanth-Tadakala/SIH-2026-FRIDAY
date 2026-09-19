"""F.R.I.D.A.Y. Chief AI / Master Orchestrator.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Central Supervisory Intelligence: Binds the 9 specialized cognitive agents
   (Situation Awareness, Diagnostic, Prediction, Risk & Impact, Planning, What-If,
   Mission Ops, Maintenance, Resource Optimizer) into a unified deliberation consensus.
2. Cross-Agent Arbitration: Resolves multi-objective trade-offs (e.g. Life Support vs
   Fuel Conservation vs Mission Communications vs Machinery Run-Hours) using deterministic
   multi-attribute utility scoring.
3. Human-in-the-Loop & Tiered Autonomy Governance: Enforces Antarctic safety guardrails:
   - Tier 1: Auto-executes safe reversible micro-actions.
   - Tier 2: Manages 60-second engineer review countdowns.
   - Tier 3: Enforces mandatory Commander PIN verification ("BHARATI-CMD-2026") for life-critical actions.
4. Transparent Incident Briefing Cards: Synthesizes explainable, auditable briefing cards
   for the Station Commander, detailing root causes, forward time-to-violation margins,
   counterfactual simulation deltas, and multi-agent critique rationales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Literal

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
from ..framework.safety_interlock import ExecutionResult, SafetyInterlockManager

logger = logging.getLogger(__name__)


@dataclass
class CommanderBriefingCard:
    """Structured, explainable incident briefing package synthesized for the Station Commander."""
    session_id: str
    incident_title: str
    severity: SeverityLevel
    incident_summary: str
    root_cause: str
    time_to_violation_str: str
    blast_radius_summary: str
    deliberation_summary: str
    consensus_plan: ActionProposal | None
    tier: AutonomyTier
    requires_pin: bool
    actions_summary: list[dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize briefing card for JSON streaming to frontend control room dashboard."""
        return {
            "session_id": self.session_id,
            "incident_title": self.incident_title,
            "severity": self.severity.value,
            "incident_summary": self.incident_summary,
            "root_cause": self.root_cause,
            "time_to_violation_str": self.time_to_violation_str,
            "blast_radius_summary": self.blast_radius_summary,
            "deliberation_summary": self.deliberation_summary,
            "consensus_plan": self.consensus_plan.to_dict() if self.consensus_plan else None,
            "tier": self.tier.value,
            "requires_pin": self.requires_pin,
            "actions_summary": self.actions_summary,
            "timestamp": self.timestamp,
        }


class FridayMasterOrchestrator(BaseSpecializedAgent):
    """F.R.I.D.A.Y. Chief AI and Master Orchestration Brain for Antarctic Station Management."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.FRIDAY_ORCHESTRATOR,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

        # Cache of synthesized briefing cards: session_id -> CommanderBriefingCard
        self._briefing_cards: dict[str, CommanderBriefingCard] = {}
        # Track processed messages to prevent duplicate evaluation
        self._processed_messages: set[str] = set()
        # Active incident tracking
        self._active_session_id: str | None = None

        # Subscribe to all key blackboard events across the multi-agent bus
        self.bus.subscribe_type(MessageType.ALERT, self._on_alert)
        self.bus.subscribe_type(MessageType.DIAGNOSIS, self._on_diagnosis)
        self.bus.subscribe_type(MessageType.PREDICTION_PROJECTION, self._on_prediction)
        self.bus.subscribe_type(MessageType.IMPACT_ASSESSMENT, self._on_impact)
        self.bus.subscribe_type(MessageType.PROPOSAL, self._on_proposal)
        self.bus.subscribe_type(MessageType.SIM_RESULT, self._on_sim_result)
        self.bus.subscribe_type(MessageType.CRITIQUE, self._on_critique)

    def handle_message(self, message: AgentMessage) -> None:
        """Handle direct messages addressed to FRIDAY_ORCHESTRATOR role."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        if message.message_type == MessageType.OPERATOR_COMMAND:
            self._handle_operator_command(message)
        elif message.message_type == MessageType.QUERY:
            self._handle_query(message)

    # -------------------------------------------------------------------------
    # Bus Event Listeners (Blackboard Ingestion)
    # -------------------------------------------------------------------------

    def _on_alert(self, message: AgentMessage) -> None:
        """Ingest anomaly alert from Situation Awareness."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session_id = message.session_id
        session = self.bus.get_session(session_id)
        if not session and session_id:
            session = self.bus.create_session(trigger_alert=message.payload)

        self._active_session_id = session_id

    def _on_diagnosis(self, message: AgentMessage) -> None:
        """Ingest root-cause diagnosis from Diagnostic Agent."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session:
            session.root_causes.append(message.payload)

    def _on_prediction(self, message: AgentMessage) -> None:
        """Ingest time-to-violation and trajectory lookahead from Prediction Agent."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session:
            session.predictions.append(message.payload)

    def _on_impact(self, message: AgentMessage) -> None:
        """Ingest blast-radius and threat matrix from Risk & Impact Agent."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session:
            session.risk_assessment = message.payload

    def _on_proposal(self, message: AgentMessage) -> None:
        """Ingest candidate action proposal from Planning Agent."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session:
            # Check if proposal is already in session
            prop_id = message.payload.get("proposal_id")
            existing_ids = {p.proposal_id for p in session.candidate_proposals}
            if prop_id and prop_id not in existing_ids:
                prop = ActionProposal(
                    title=message.payload.get("title", ""),
                    target_subsystem=message.payload.get("target_subsystem", ""),
                    parameter_overrides=message.payload.get("parameter_overrides", []),
                    tier=AutonomyTier(message.payload.get("tier", AutonomyTier.TIER_1_AUTONOMOUS.value)),
                    rationale=message.payload.get("rationale", ""),
                    proposal_id=prop_id,
                    projected_impact=message.payload.get("projected_impact", {}),
                    status=ProposalStatus(message.payload.get("status", ProposalStatus.DRAFT.value)),
                )
                session.candidate_proposals.append(prop)

    def _on_sim_result(self, message: AgentMessage) -> None:
        """Ingest What-If simulation verdict and trigger consensus arbitration."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session and session.candidate_proposals:
            # Update proposal simulation delta
            prop_id = message.payload.get("proposal_id")
            for prop in session.candidate_proposals:
                if prop.proposal_id == prop_id:
                    prop.simulation_delta = message.payload
                    prop.status = (
                        ProposalStatus.SIMULATED
                        if message.payload.get("is_safe", False)
                        else ProposalStatus.REJECTED
                    )

            # Check if arbitration can proceed
            self.arbitrate_session(message.session_id)

    def _on_critique(self, message: AgentMessage) -> None:
        """Ingest cyclic deliberation critiques from Mission Ops, Maintenance, or Resource Optimizer."""
        if message.message_id in self._processed_messages:
            return
        self._processed_messages.add(message.message_id)

        session = self.bus.get_session(message.session_id)
        if session:
            session.critiques.append(message.payload)
            # Re-arbitrate with new constraint
            self.arbitrate_session(message.session_id)

    # -------------------------------------------------------------------------
    # Consensus Arbitration & Briefing Synthesis
    # -------------------------------------------------------------------------

    def arbitrate_session(self, session_id: str) -> ActionProposal | None:
        """Arbitrate multi-agent trade-offs and select the optimal consensus operational plan."""
        session = self.bus.get_session(session_id)
        if not session or not session.candidate_proposals:
            return None

        # Gather critique constraints
        critical_veto_props = {
            c.get("proposal_id")
            for c in session.critiques
            if c.get("severity") in ("CRITICAL", "EMERGENCY")
        }

        viable_proposals: list[tuple[ActionProposal, float]] = []

        for prop in session.candidate_proposals:
            # 1. Reject if explicitly marked rejected or vetoed
            if prop.status in (ProposalStatus.REJECTED, ProposalStatus.VETOED):
                continue

            # 2. Reject if What-If simulation proved unsafe
            if prop.simulation_delta and not prop.simulation_delta.get("is_safe", True):
                continue

            # 3. Reject if an unresolved critical critique exists for this proposal
            if prop.proposal_id in critical_veto_props:
                prop.status = ProposalStatus.REJECTED
                continue

            # 4. Multi-objective scoring
            score = 100.0
            if prop.simulation_delta:
                sim = prop.simulation_delta
                score += float(sim.get("risk_reduction_pct", 0.0)) * 0.5
                score += float(sim.get("temp_difference_c", 0.0)) * 5.0
                score += float(sim.get("fuel_saved_l", 0.0)) * 0.2

            # Prefer lower autonomy tier if utility is equal (less friction, lower risk)
            if prop.tier == AutonomyTier.TIER_1_AUTONOMOUS:
                score += 10.0
            elif prop.tier == AutonomyTier.TIER_3_COMMANDER_CONFIRMATION:
                score -= 15.0

            viable_proposals.append((prop, score))

        if not viable_proposals:
            # No candidate passed all filters; keep existing or fallback
            return None

        # Sort by score descending
        viable_proposals.sort(key=lambda x: x[1], reverse=True)
        winning_proposal = viable_proposals[0][0]

        session.final_plan = winning_proposal

        # Synthesize Commander Briefing Card
        card = self.synthesize_briefing_card(session_id)
        self._briefing_cards[session_id] = card

        # Auto-execute Tier 1 proposals immediately
        if winning_proposal.tier == AutonomyTier.TIER_1_AUTONOMOUS and not session.resolved:
            self.execute_consensus_plan(session_id=session_id)

        return winning_proposal

    def synthesize_briefing_card(self, session_id: str) -> CommanderBriefingCard:
        """Synthesize an explainable, structured briefing card for the Station Commander."""
        session = self.bus.get_session(session_id)
        if not session:
            return CommanderBriefingCard(
                session_id=session_id,
                incident_title="Operational Status Briefing",
                severity=SeverityLevel.INFO,
                incident_summary="Station operating under nominal baseline parameters.",
                root_cause="None identified.",
                time_to_violation_str="No imminent threshold violation.",
                blast_radius_summary="All subsystems within green operating envelopes.",
                deliberation_summary="All 9 specialized agents in standby.",
                consensus_plan=None,
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                requires_pin=False,
            )

        # Extract trigger alert
        alert = session.trigger_alert or {}
        inc_title = alert.get("anomaly_type") or alert.get("title") or "Station Operational Anomaly"
        inc_summary = alert.get("description") or f"Anomaly detected on {alert.get('sensor_id', 'station telemetry')}."

        # Extract root cause
        if session.root_causes:
            rc = session.root_causes[0]
            root_cause_str = (
                f"Isolated to '{rc.get('root_cause_node_id', 'unknown')}' "
                f"({rc.get('explanation', 'Topological causal traversal verified')})."
            )
        else:
            root_cause_str = "Under continuous diagnostic evaluation."

        # Extract prediction time-to-violation
        ttv_str = "Stable: No threshold violation projected."
        if session.predictions:
            pred = session.predictions[0]
            min_ttf = pred.get("min_time_to_failure_minutes")
            if min_ttf is not None and min_ttf < 999.0:
                ttv_str = f"Time to Failure: {min_ttf:.1f} minutes under unmitigated baseline."

        # Extract risk blast radius
        blast_str = "Localized to primary equipment."
        if session.risk_assessment:
            risk = session.risk_assessment
            blast_str = (
                f"Criticality: {risk.get('criticality_tier', 'TIER_3')}. "
                f"Life Support Threat: {risk.get('life_support_threat', False)}. "
                f"Affected Nodes: {len(risk.get('affected_nodes', []))}."
            )

        # Extract deliberation narrative
        delib_notes: list[str] = []
        if session.candidate_proposals:
            delib_notes.append(f"Planning formulated {len(session.candidate_proposals)} candidate plan(s).")
        if session.critiques:
            delib_notes.append(f"{len(session.critiques)} critique(s) resolved across Mission, Maintenance & What-If.")
        delib_str = " ".join(delib_notes) if delib_notes else "Multi-agent consensus achieved without conflict."

        # Consensus plan
        final_plan = session.final_plan
        tier = final_plan.tier if final_plan else AutonomyTier.TIER_1_AUTONOMOUS
        requires_pin = tier == AutonomyTier.TIER_3_COMMANDER_CONFIRMATION

        actions_summary = final_plan.parameter_overrides if final_plan else []

        card = CommanderBriefingCard(
            session_id=session_id,
            incident_title=inc_title,
            severity=SeverityLevel.CRITICAL if requires_pin else SeverityLevel.WARNING,
            incident_summary=inc_summary,
            root_cause=root_cause_str,
            time_to_violation_str=ttv_str,
            blast_radius_summary=blast_str,
            deliberation_summary=delib_str,
            consensus_plan=final_plan,
            tier=tier,
            requires_pin=requires_pin,
            actions_summary=actions_summary,
        )

        self._briefing_cards[session_id] = card
        return card

    # -------------------------------------------------------------------------
    # Tiered Autonomy Execution Pipeline
    # -------------------------------------------------------------------------

    def execute_consensus_plan(
        self,
        session_id: str,
        commander_pin: str | None = None,
        bypass_supervision: bool = False,
    ) -> ExecutionResult:
        """Execute the validated consensus operational plan through the Safety Interlock Manager."""
        session = self.bus.get_session(session_id)
        if not session or not session.final_plan:
            return ExecutionResult(
                success=False,
                status=ProposalStatus.DRAFT,
                message=f"No finalized consensus plan found for session '{session_id}'.",
            )

        plan = session.final_plan

        # Execute through Safety Interlock Manager
        res = self.safety_interlock.execute_action(
            proposal=plan,
            engine=self.engine,
            commander_pin=commander_pin,
            bypass_supervision_wait=bypass_supervision,
        )

        if res.success:
            session.resolved = True
            # Publish consensus plan broadcast
            self.publish_message(
                session_id=session_id,
                recipient="BROADCAST",
                message_type=MessageType.CONSENSUS_PLAN,
                severity=SeverityLevel.INFO,
                payload={
                    "session_id": session_id,
                    "proposal_id": plan.proposal_id,
                    "plan_title": plan.title,
                    "applied_overrides": res.applied_overrides,
                    "status": res.status.value,
                    "message": res.message,
                },
                confidence=1.0,
            )

        return res

    # -------------------------------------------------------------------------
    # Command & Query Handling
    # -------------------------------------------------------------------------

    def _handle_operator_command(self, message: AgentMessage) -> None:
        """Handle execution commands from operator (e.g. Commander PIN authorization)."""
        payload = message.payload
        session_id = message.session_id or payload.get("session_id", self._active_session_id or "")
        pin = payload.get("commander_pin")
        bypass = bool(payload.get("bypass_supervision", False))

        res = self.execute_consensus_plan(
            session_id=session_id,
            commander_pin=pin,
            bypass_supervision=bypass,
        )

        self.publish_message(
            session_id=session_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            severity=SeverityLevel.INFO if res.success else SeverityLevel.WARNING,
            payload={
                "success": res.success,
                "status": res.status.value,
                "message": res.message,
                "applied_overrides": res.applied_overrides,
            },
            confidence=1.0,
        )

    def _handle_query(self, message: AgentMessage) -> None:
        """Provide comprehensive status of all agents, sessions, and control room briefing cards."""
        session_id = message.payload.get("session_id", self._active_session_id)
        if session_id and session_id in self._briefing_cards:
            resp_payload = {"briefing_card": self._briefing_cards[session_id].to_dict()}
        else:
            resp_payload = {"cognitive_status": self.get_cognitive_status()}

        self.publish_message(
            session_id=message.session_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            severity=SeverityLevel.INFO,
            payload=resp_payload,
            confidence=1.0,
        )

    def get_cognitive_status(self) -> dict[str, Any]:
        """Aggregate station status and cognitive multi-agent framework metrics."""
        kpis = self.engine.get_station_kpis()
        all_sessions = self.bus.get_all_sessions()
        active_count = sum(1 for s in all_sessions if not s.resolved)
        resolved_count = sum(1 for s in all_sessions if s.resolved)

        return {
            "orchestrator_status": "ONLINE_ACTIVE",
            "active_sessions_count": active_count,
            "resolved_sessions_count": resolved_count,
            "total_deliberation_sessions": len(all_sessions),
            "briefing_cards_count": len(self._briefing_cards),
            "active_scenario": self.engine.active_scenario.value,
            "station_kpis": kpis,
            "specialized_agents": [
                "SITUATION_AWARENESS",
                "DIAGNOSTIC",
                "PREDICTION",
                "RISK_IMPACT",
                "PLANNING",
                "WHAT_IF",
                "MISSION_OPS",
                "MAINTENANCE",
                "RESOURCE_OPTIMIZER",
            ],
        }
