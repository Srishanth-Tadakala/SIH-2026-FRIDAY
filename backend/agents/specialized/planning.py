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


class PlanningAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for formulating operational mitigation action proposals."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.PLANNING,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

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

        proposals: list[ActionProposal] = []

        # -----------------------------------------------------------------
        # Playbook 1: Generator Trip / Power Deficit (chp_1, chp_2, mlvd_bus)
        # -----------------------------------------------------------------
        if root_node_id in ("chp_1", "chp_2", "chp_3", "mlvd_bus"):
            alt_unit = 2 if root_node_id == "chp_1" else 1
            alt_idx = alt_unit - 1

            p1 = ActionProposal(
                title=f"Auto-Sequence Standby CHP-{alt_unit:02d} to Active Duty",
                target_subsystem="ENERGY",
                parameter_overrides=[
                    {
                        "pillar": "energy",
                        "path": f"chps[{alt_idx}].operating_state",
                        "value": "RUNNING",
                    },
                    {
                        "pillar": "energy",
                        "path": f"chps[{alt_idx}].active_power_kw",
                        "value": 65.0,
                    },
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale=(
                    f"Bring standby generator CHP-{alt_unit:02d} online to replace tripped primary generator "
                    f"'{root_node_id}', restoring 400V MLVD bus and hydronic exhaust heat recovery."
                ),
                projected_impact={
                    "restores_kw": 65.0,
                    "prevents_blackout": True,
                    "stabilizes_habitat": True,
                },
            )
            proposals.append(p1)

            p2 = ActionProposal(
                title="Non-Essential Science Load Shedding",
                target_subsystem="ENERGY",
                parameter_overrides=[
                    {
                        "pillar": "infrastructure",
                        "path": "building.temp_lab_c",
                        "value": 18.0,
                    }
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Shed secondary laboratory auxiliary heating to conserve critical battery bus reserves.",
                projected_impact={
                    "kw_shed": 12.5,
                    "extends_ups_buffer_hours": 1.5,
                },
            )
            proposals.append(p2)

        # -----------------------------------------------------------------
        # Playbook 2: Utilidor Fresh Water Line Freeze (utilidor_water_line, ro_plant)
        # -----------------------------------------------------------------
        elif root_node_id in ("utilidor_water_line", "ro_plant", "seawater_intake"):
            p1 = ActionProposal(
                title="Engage Auxiliary Trace Heating & Thermal Recirculation Flush",
                target_subsystem="INFRASTRUCTURE",
                parameter_overrides=[
                    {
                        "pillar": "infrastructure",
                        "path": "pipelines.water01_trace_heating_on",
                        "value": True,
                    },
                    {
                        "pillar": "infrastructure",
                        "path": "pipelines.water01_pipe_temp_c",
                        "value": 4.5,
                    },
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Activate secondary electric heat-tracing tape and cycle warm water to prevent ice crystal formation.",
                projected_impact={
                    "recovers_pipe_temp_c": 4.5,
                    "prevents_rupture": True,
                    "safeguards_potable_supply": True,
                },
            )
            proposals.append(p1)

        # -----------------------------------------------------------------
        # Playbook 3: Katabatic Blizzard Surge (env_katabatic, building_envelope)
        # -----------------------------------------------------------------
        elif root_node_id in ("env_katabatic", "building_envelope", "env_ambient"):
            p1 = ActionProposal(
                title="Transition HVAC AHU-01/02 to 90% Recirculation & Boost Hydronic Heating",
                target_subsystem="INFRASTRUCTURE",
                parameter_overrides=[
                    {
                        "pillar": "infrastructure",
                        "path": "building.temp_living_c",
                        "value": 21.5,
                    }
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Seal fresh air intake dampers against windchill infiltration and elevate glycol loop target.",
                projected_impact={
                    "thermal_buffer_c": 5.5,
                    "maintains_life_support": True,
                },
            )
            proposals.append(p1)

            p2 = ActionProposal(
                title="Ground Outdoor Traverses & Suspend Flight Operations",
                target_subsystem="LOGISTICS",
                parameter_overrides=[
                    {
                        "pillar": "logistics",
                        "path": "routes.surface_traction_index",
                        "value": 25.0,
                    }
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Issue whiteout advisory, lock perimeter ground routes, and halt helipad operations.",
                projected_impact={
                    "mitigates_crew_exposure": True,
                    "zero_field_casualties": True,
                },
            )
            proposals.append(p2)

        # -----------------------------------------------------------------
        # Playbook 4: Cold Chain Provisions Excursion (reefer_01)
        # -----------------------------------------------------------------
        elif root_node_id == "reefer_01":
            p1 = ActionProposal(
                title="Transfer Reefer-01 to Auxiliary Bus & Cycle Backup Compressor",
                target_subsystem="LOGISTICS",
                parameter_overrides=[
                    {
                        "pillar": "energy",
                        "path": "chps[0].active_power_kw",
                        "value": 68.0,
                    }
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Reroute power feed from MLVD sub-feeder B to restore Reefer-01 compressor cooling.",
                projected_impact={
                    "restores_core_temp_c": -22.0,
                    "protects_winterover_food": True,
                },
            )
            proposals.append(p1)

        # -----------------------------------------------------------------
        # Playbook 5: Day Tank Fuel Depletion (day_tank, fuel_transfer_pump)
        # -----------------------------------------------------------------
        elif root_node_id in ("day_tank", "fuel_transfer_pump", "bulk_fuel_farm"):
            p1 = ActionProposal(
                title="Initiate Bulk Fuel Farm Pump Skid Transfer to Day Tank",
                target_subsystem="ENERGY",
                parameter_overrides=[
                    {
                        "pillar": "energy",
                        "path": "fuel.transfer_pump_running",
                        "value": True,
                    },
                    {
                        "pillar": "energy",
                        "path": "fuel.day_tank_level_l",
                        "value": 850.0,
                    },
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale="Engage transfer pump skid to replenish day tank from bulk fuel tanks before generator starvation.",
                projected_impact={
                    "refills_day_tank_l": 850.0,
                    "prevents_generator_shutdown": True,
                },
            )
            proposals.append(p1)

        # Default fallback proposal
        if not proposals:
            p_def = ActionProposal(
                title=f"Stabilize Subsystem '{root_node_id}' Operational Envelope",
                target_subsystem="INFRASTRUCTURE",
                parameter_overrides=[
                    {
                        "pillar": "infrastructure",
                        "path": "building.temp_living_c",
                        "value": 21.0,
                    }
                ],
                tier=AutonomyTier.TIER_1_AUTONOMOUS,
                rationale=f"Automated stabilization of {root_node_id} to maintain baseline life-support.",
                projected_impact={"stabilization": True},
            )
            proposals.append(p_def)

        return proposals
