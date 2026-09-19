"""Risk & Impact Agent for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

COGNITIVE OBJECTIVE:
"What could this affect across station life-support, crew safety, and mission operations?"

RESPONSIBILITIES:
1. Downstream Blast Radius Quantification: Traverses outgoing dependency edges on TwinCausalGraph
   to map the full cascade of impacted equipment, zones, and life-support assets.
2. Life-Support Threat Evaluation: Assesses immediate threats to crew habitat thermal envelope,
   potable water minimum reserves (1,500 L floor), medical ward power, and refuge shelter readiness.
3. Mission Capability Degradation: Quantifies impact on outdoor field traverses, PistenBully hauler
   readiness, helipad flight operations, and marine cargo offloading.
4. Composite Incident Severity Scoring: Synthesizes graph topological criticality with time-to-violation
   urgency from Prediction Agent to compute a calibrated 0–100 severity index.
5. Multi-Agent Deliberation Integration:
   - Subscribes to PREDICTION_PROJECTION and DIAGNOSIS messages.
   - Automatically populates DeliberationSession.risk_assessment on the shared blackboard.
   - Dispatches structured IMPACT_ASSESSMENT messages to Planning and F.R.I.D.A.Y. Orchestrator.
6. Interactive Query Support: Responds to operator requests evaluating the blast radius of any asset.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Literal

from ...core.causal_graph import NodeType, TwinCausalGraph
from ...core.engine import BharatiMasterTwinEngine
from ..framework.base_agent import BaseSpecializedAgent
from ..framework.bus import AgentMessageBus
from ..framework.models import (
    AgentMessage,
    AgentRole,
    DeliberationSession,
    MessageType,
    SeverityLevel,
)


@dataclass
class ImpactAssessment:
    """Comprehensive blast radius and operational consequence assessment."""
    assessment_id: str
    session_id: str
    root_node_id: str
    root_node_name: str
    threat_level: SeverityLevel
    composite_severity_score: float  # 0.0 to 100.0
    life_support_threat: bool
    human_safety_risk: str  # "NEGLIGIBLE", "MODERATE", "SEVERE", "LIFE_THREATENING"
    affected_asset_count: int
    affected_subsystems: list[str]
    cascading_chain: list[str]
    life_support_details: dict[str, Any]
    mission_impact_details: dict[str, Any]
    time_to_critical_seconds: float | None
    containment_priorities: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize assessment to dictionary."""
        return asdict(self)


class RiskImpactAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for blast radius and crew safety risk assessment."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
    ) -> None:
        super().__init__(
            role=AgentRole.RISK_IMPACT,
            bus=bus,
            engine=engine,
            graph=graph,
        )

        # Listen to PREDICTION_PROJECTION and DIAGNOSIS messages
        self.bus.subscribe_type(MessageType.PREDICTION_PROJECTION, self.on_prediction_received)
        self.bus.subscribe_type(MessageType.DIAGNOSIS, self.on_diagnosis_received)

        # Audit cache of assessments: assessment_id -> ImpactAssessment
        self._assessments: dict[str, ImpactAssessment] = {}

    def on_prediction_received(self, message: AgentMessage) -> None:
        """Evaluate blast radius and risk when a forward projection is published."""
        payload = message.payload
        session_id = message.session_id

        # Determine target node from session or prediction payload
        node_id = "mlvd_bus"  # default
        session = self.bus.get_session(session_id) if session_id else None

        if session and session.root_causes:
            node_id = session.root_causes[0].get("root_cause_node_id", node_id)
        elif "root_node_id" in payload:
            node_id = payload["root_node_id"]

        time_to_crit = payload.get("time_to_critical_seconds")

        assessment = self.assess_impact(
            target_node_id=node_id,
            session_id=session_id,
            time_to_critical_seconds=time_to_crit,
        )

        self._record_and_dispatch(assessment, session)

    def on_diagnosis_received(self, message: AgentMessage) -> None:
        """Evaluate initial blast radius when a diagnosis is published."""
        payload = message.payload
        session_id = message.session_id
        node_id = payload.get("root_cause_node_id", "mlvd_bus")

        session = self.bus.get_session(session_id) if session_id else None

        assessment = self.assess_impact(
            target_node_id=node_id,
            session_id=session_id,
            time_to_critical_seconds=None,
        )

        self._record_and_dispatch(assessment, session)

    def _record_and_dispatch(
        self, assessment: ImpactAssessment, session: DeliberationSession | None
    ) -> None:
        """Update session blackboard and publish assessment to Planning and Orchestrator."""
        self._assessments[assessment.assessment_id] = assessment

        if session:
            session.risk_assessment = assessment.to_dict()

        # Publish to Planning Agent
        self.publish_message(
            session_id=assessment.session_id,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.IMPACT_ASSESSMENT,
            severity=assessment.threat_level,
            payload=assessment.to_dict(),
            confidence=0.95,
        )

        # Publish to F.R.I.D.A.Y. Orchestrator
        self.publish_message(
            session_id=assessment.session_id,
            recipient=AgentRole.FRIDAY_ORCHESTRATOR,
            message_type=MessageType.IMPACT_ASSESSMENT,
            severity=assessment.threat_level,
            payload=assessment.to_dict(),
            confidence=0.95,
        )

    def handle_message(self, message: AgentMessage) -> None:
        """Handle on-demand queries from operator or orchestrator."""
        if message.message_type == MessageType.QUERY:
            node_id = message.payload.get("node_id", "mlvd_bus")
            time_to_crit = message.payload.get("time_to_critical_seconds")

            assessment = self.assess_impact(
                target_node_id=node_id,
                session_id=message.session_id,
                time_to_critical_seconds=time_to_crit,
            )

            self.publish_message(
                session_id=message.session_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                severity=SeverityLevel.INFO,
                payload=assessment.to_dict(),
                confidence=0.95,
            )

    def assess_impact(
        self,
        target_node_id: str,
        session_id: str = "",
        time_to_critical_seconds: float | None = None,
    ) -> ImpactAssessment:
        """Synthesize causal graph blast radius with digital twin telemetry and lookahead urgency."""
        # 1. Compute topological blast radius from causal graph
        blast = self.graph.calculate_blast_radius(target_node_id)
        downstream = self.graph.get_downstream_impacts(target_node_id, max_depth=6)

        root_node = self.graph.get_node(target_node_id)
        root_name = root_node.name if root_node else target_node_id

        # 2. Extract station state and KPIs
        kpis = self.engine.get_station_kpis()
        living_temp = kpis.get("indoor_avg_temp_c", 21.0)
        fuel_days = kpis.get("fuel_autonomy_days", 45.0)
        water_days = kpis.get("water_autonomy_days", 18.0)
        running_gens = kpis.get("running_generators", 1)

        # 3. Assess Life-Support Impact
        life_support_threat = blast.get("life_support_threat", False)
        impacted_node_ids = {d["impacted_node_id"] for d in downstream}
        impacted_node_ids.add(target_node_id)

        living_threatened = "zone_living" in impacted_node_ids
        water_threatened = (
            "utilidor_water_line" in impacted_node_ids
            or "ro_plant" in impacted_node_ids
            or "potable_reservoir" in impacted_node_ids
        )
        medical_threatened = "zone_medical" in impacted_node_ids
        shelter_threatened = "emergency_shelter" in impacted_node_ids

        life_support_details = {
            "living_zone_threatened": living_threatened,
            "current_indoor_temp_c": living_temp,
            "water_system_threatened": water_threatened,
            "water_autonomy_days": water_days,
            "medical_ward_threatened": medical_threatened,
            "emergency_refuge_threatened": shelter_threatened,
        }

        # 4. Assess Mission Impact
        helipad_threatened = "helipad" in impacted_node_ids
        route_threatened = (
            "station_ring_route" in impacted_node_ids
            or "fast_ice_route" in impacted_node_ids
        )
        reefer_threatened = "reefer_01" in impacted_node_ids
        fleet_threatened = "pb_01" in impacted_node_ids

        mission_details = {
            "helipad_operational": not helipad_threatened,
            "ground_traverse_clear": not route_threatened,
            "cold_chain_provision_safe": not reefer_threatened,
            "fleet_readiness": "RESTRICTED" if fleet_threatened else "NOMINAL",
        }

        # 5. Calculate Calibrated Severity Score (0 to 100)
        base_severity = float(blast.get("severity_score", 30.0))

        # Add time-to-violation urgency weight
        urgency_multiplier = 1.0
        if time_to_critical_seconds is not None:
            if time_to_critical_seconds < 1800.0:  # Under 30 mins
                urgency_multiplier = 1.35
            elif time_to_critical_seconds < 3600.0:  # Under 1 hour
                urgency_multiplier = 1.20
            elif time_to_critical_seconds < 7200.0:  # Under 2 hours
                urgency_multiplier = 1.10

        composite_score = min(100.0, round(base_severity * urgency_multiplier, 1))

        # If station total blackout or living quarters dropping below 15°C
        if running_gens == 0 or living_temp < 15.0:
            composite_score = max(composite_score, 92.0)
            life_support_threat = True

        # 6. Human Safety Risk Level
        if composite_score >= 85.0 and life_support_threat:
            human_safety = "LIFE_THREATENING"
            threat_level = SeverityLevel.EMERGENCY
        elif composite_score >= 65.0:
            human_safety = "SEVERE"
            threat_level = SeverityLevel.CRITICAL
        elif composite_score >= 40.0:
            human_safety = "MODERATE"
            threat_level = SeverityLevel.WARNING
        else:
            human_safety = "NEGLIGIBLE"
            threat_level = SeverityLevel.INFO

        # 7. Formulate Containment Priorities
        priorities: list[str] = []
        if living_threatened or living_temp < 17.0:
            priorities.append("Prioritize habitat thermal recovery (maintain >= 16.0°C life-support floor).")
        if running_gens == 0:
            priorities.append("Immediate black-start or transfer to standby CHP generator plant.")
        if water_threatened:
            priorities.append("Protect utilidor fresh water line against freezing (verify trace heating).")
        if helipad_threatened:
            priorities.append("Issue NOTAM / suspend air transport until wind and visibility clear.")
        if reefer_threatened:
            priorities.append("Switch cold storage reefer to auxiliary power feed to preserve provisions.")

        if not priorities:
            priorities.append("Maintain continuous perception; all primary life-support systems stable.")

        cascading_chain = [d["impacted_node_id"] for d in downstream]

        asm_id = f"RSK-{int(time.time() * 1000) % 1000000:06d}"

        return ImpactAssessment(
            assessment_id=asm_id,
            session_id=session_id or f"SES-{asm_id}",
            root_node_id=target_node_id,
            root_node_name=root_name,
            threat_level=threat_level,
            composite_severity_score=composite_score,
            life_support_threat=life_support_threat,
            human_safety_risk=human_safety,
            affected_asset_count=len(impacted_node_ids),
            affected_subsystems=blast.get("affected_subsystems", []),
            cascading_chain=cascading_chain,
            life_support_details=life_support_details,
            mission_impact_details=mission_details,
            time_to_critical_seconds=time_to_critical_seconds,
            containment_priorities=priorities,
        )
