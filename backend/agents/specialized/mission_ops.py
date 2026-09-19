"""Mission Operations Specialized Cognitive Agent.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Crew Safety First: Enforces hard environmental limits on field traverses, snowcat
   routes, and helicopter sorties to prevent hypothermia, crevasses, and whiteouts.
2. Field Expedition Envelope Tracking: Monitors active field parties (Team 01, Team 02),
   distance from station, return margin minutes, and radio check status (zero PII).
3. Cyclic Deliberation Critique: Protects mission-critical communications (comms mast,
   satellite uplinks, radio repeaters) and high-priority scientific research instruments
   from being shed by load-balancing proposals during field deployments.
4. Autonomous Weather Advisory: Automatically calculates wind chill and blizzard limits
   to trigger traverse recalls and flight grounding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
import math
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
    DeliberationSession,
    MessageType,
    SeverityLevel,
)
from ..framework.safety_interlock import SafetyInterlockManager

logger = logging.getLogger(__name__)


class MissionOperationalStatus(str, Enum):
    """Overall station operational status for field expeditions and aviation."""
    NOMINAL = "NOMINAL"
    ADVISORY = "ADVISORY"
    RESTRICTED = "RESTRICTED"
    RECALL_MANDATORY = "RECALL_MANDATORY"
    EMERGENCY_SHELTER = "EMERGENCY_SHELTER"


@dataclass
class FieldPartyStatus:
    """Operational telemetry and safety status for an active field party."""
    team_id: str
    status: str
    distance_km: float
    radio_status: str
    return_margin_minutes: float
    is_safe: bool
    safety_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_id": self.team_id,
            "status": self.status,
            "distance_km": self.distance_km,
            "radio_status": self.radio_status,
            "return_margin_minutes": self.return_margin_minutes,
            "is_safe": self.is_safe,
            "safety_note": self.safety_note,
        }


@dataclass
class MissionFeasibilityAssessment:
    """Comprehensive operational assessment of all active expeditions, aviation, and routes."""
    assessment_id: str
    overall_status: MissionOperationalStatus
    aviation_status: Literal["CLEAR", "CAUTION", "GROUNDED"]
    ground_traverse_status: Literal["OPEN", "CAUTION", "RESTRICTED", "CLOSED"]
    crevasse_risk_level: Literal["LOW", "MODERATE", "HIGH"]
    weather_summary: dict[str, Any]
    field_parties: list[FieldPartyStatus] = field(default_factory=list)
    active_field_personnel: int = 0
    station_personnel: int = 24
    critical_comms_required: bool = False
    advisories: list[str] = field(default_factory=list)
    mandatory_actions: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "overall_status": self.overall_status.value,
            "aviation_status": self.aviation_status,
            "ground_traverse_status": self.ground_traverse_status,
            "crevasse_risk_level": self.crevasse_risk_level,
            "weather_summary": self.weather_summary,
            "field_parties": [p.to_dict() for p in self.field_parties],
            "active_field_personnel": self.active_field_personnel,
            "station_personnel": self.station_personnel,
            "critical_comms_required": self.critical_comms_required,
            "advisories": self.advisories,
            "mandatory_actions": self.mandatory_actions,
            "timestamp": self.timestamp,
        }


class MissionOpsAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for mission safety, field expedition envelopes, and comms defense."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.MISSION_OPS,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

        # Cache of recent feasibility assessments
        self._latest_assessment: MissionFeasibilityAssessment | None = None

    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages routed to MISSION_OPS role or broadcast."""
        if message.sender == self.role:
            return

        if message.message_type == MessageType.PROPOSAL:
            self._handle_proposal(message)
        elif message.message_type == MessageType.ALERT:
            self._handle_alert(message)
        elif message.message_type == MessageType.QUERY:
            self._handle_query(message)

    def _handle_proposal(self, message: AgentMessage) -> None:
        """Critique candidate proposals from Planning Agent to defend crew comms and field safety."""
        proposal_data = message.payload
        session_id = message.session_id
        session = self.bus.get_session(session_id) if session_id else None

        critique = self.critique_proposal(proposal_data, session_id=session_id)
        if critique:
            self.publish_message(
                session_id=session_id,
                recipient=AgentRole.PLANNING,
                message_type=MessageType.CRITIQUE,
                severity=SeverityLevel.WARNING,
                payload=critique,
                confidence=1.0,
            )
            if session:
                session.critiques.append(critique)

    def _handle_alert(self, message: AgentMessage) -> None:
        """Re-assess mission envelope when a weather, power, or logistics alert is received."""
        alert_payload = message.payload
        assessment = self.assess_mission_envelope(trigger_payload=alert_payload)
        self._latest_assessment = assessment

        if assessment.overall_status in (
            MissionOperationalStatus.ADVISORY,
            MissionOperationalStatus.RESTRICTED,
            MissionOperationalStatus.RECALL_MANDATORY,
            MissionOperationalStatus.EMERGENCY_SHELTER,
        ):
            severity = (
                SeverityLevel.EMERGENCY
                if assessment.overall_status in (MissionOperationalStatus.RECALL_MANDATORY, MissionOperationalStatus.EMERGENCY_SHELTER)
                else SeverityLevel.WARNING
            )
            self.publish_message(
                session_id=message.session_id,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.ADVISORY,
                severity=severity,
                payload=assessment.to_dict(),
                confidence=1.0,
            )

    def _handle_query(self, message: AgentMessage) -> None:
        """Respond with the current mission feasibility assessment."""
        assessment = self.assess_mission_envelope()
        self._latest_assessment = assessment
        self.publish_message(
            session_id=message.session_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            severity=SeverityLevel.INFO,
            payload={"mission_assessment": assessment.to_dict()},
            confidence=1.0,
        )

    def assess_mission_envelope(
        self, trigger_payload: dict[str, Any] | None = None
    ) -> MissionFeasibilityAssessment:
        """Evaluate weather limits, active field teams, aviation, and routes across Bharati Station."""
        # 1. Read environment physics
        env_phy = self.engine.env_registry.physics
        wind_mps = env_phy.weather.wind_speed_mps
        temp_c = env_phy.weather.ambient_temperature_c
        visibility_m = getattr(env_phy.weather, "visibility_m", 10000.0)

        # Calculate Antarctic wind chill index (°C)
        wind_kph = max(1.0, wind_mps * 3.6)
        if temp_c <= 10.0 and wind_kph >= 4.8:
            wind_chill_c = round(
                13.12 + 0.6215 * temp_c - 11.37 * (wind_kph ** 0.16) + 0.3965 * temp_c * (wind_kph ** 0.16),
                1,
            )
        else:
            wind_chill_c = temp_c

        weather_summary = {
            "wind_speed_mps": round(wind_mps, 1),
            "wind_speed_kph": round(wind_kph, 1),
            "ambient_temp_c": round(temp_c, 1),
            "wind_chill_c": wind_chill_c,
            "visibility_meters": round(visibility_m, 0),
        }

        # 2. Read logistics physics
        log_phy = self.engine.logistics_registry.physics
        m_state = log_phy.missions
        r_state = log_phy.routes

        field_pax = int(m_state.field_personnel_count)
        station_pax = int(m_state.station_personnel_count)

        advisories: list[str] = []
        mandatory_actions: list[str] = []

        # 3. Assess field teams
        field_parties: list[FieldPartyStatus] = []
        team01 = m_state.team01
        t1_safe = True
        t1_notes: list[str] = []

        if team01.status in ("IN_PROGRESS", "RETURNING"):
            if team01.radio_check_status in ("OVERDUE", "SILENCE"):
                t1_safe = False
                t1_notes.append(f"Radio check {team01.radio_check_status} (Last known: {team01.distance_km:.1f} km)")
                mandatory_actions.append("Initiate HF directional radio sweep and standby search party")

            if team01.return_margin_minutes < 0:
                t1_safe = False
                t1_notes.append(f"Overdue return cutoff by {abs(team01.return_margin_minutes):.0f} minutes")
                mandatory_actions.append(f"Team 01 overdue ({team01.return_margin_minutes:.0f}m): Dispatch tracked PistenBully search team")
            elif team01.return_margin_minutes < 60.0:
                t1_notes.append(f"Tight return margin ({team01.return_margin_minutes:.0f}m remaining)")
                advisories.append("Direct Team 01 to commence immediate return to Bharati Station")

        field_parties.append(
            FieldPartyStatus(
                team_id="TEAM-FIELD-01",
                status=team01.status,
                distance_km=team01.distance_km,
                radio_status=team01.radio_check_status,
                return_margin_minutes=team01.return_margin_minutes,
                is_safe=t1_safe,
                safety_note="; ".join(t1_notes) if t1_notes else "Operating within safe operational envelope.",
            )
        )

        # 4. Assess Weather Safety Limits & Thresholds
        # Polar flight rules: Wind > 18 m/s or visibility < 800m grounds aviation
        if wind_mps >= 18.0 or visibility_m < 800.0:
            aviation_status: Literal["CLEAR", "CAUTION", "GROUNDED"] = "GROUNDED"
            advisories.append(f"Helicopter flight operations grounded: Wind {wind_mps:.1f} m/s / Vis {visibility_m:.0f} m")
        elif wind_mps >= 12.0 or visibility_m < 2000.0:
            aviation_status = "CAUTION"
            advisories.append(f"Aviation flight window marginal: Wind {wind_mps:.1f} m/s")
        else:
            aviation_status = "CLEAR"

        # Polar traverse rules: Wind >= 25 m/s or visibility < 300m = whiteout / mandatory recall
        crevasse_risk: Literal["LOW", "MODERATE", "HIGH"] = (
            "HIGH" if r_state.crevasse_risk == "HIGH" or wind_mps >= 22.0
            else ("MODERATE" if r_state.crevasse_risk == "MODERATE" or wind_mps >= 15.0 else "LOW")
        )

        if wind_mps >= 25.0 or visibility_m < 300.0 or wind_chill_c < -50.0:
            ground_traverse_status: Literal["OPEN", "CAUTION", "RESTRICTED", "CLOSED"] = "CLOSED"
            overall_status = MissionOperationalStatus.RECALL_MANDATORY
            mandatory_actions.append(
                f"MANDATORY RECALL: Katabatic blizzard conditions (Wind: {wind_mps:.1f} m/s, Chill: {wind_chill_c:.1f}°C). "
                "Recall all outdoor personnel to station or nearest emergency refuge container immediately."
            )
        elif wind_mps >= 15.0 or visibility_m < 1500.0 or not t1_safe:
            ground_traverse_status = "RESTRICTED"
            overall_status = (
                MissionOperationalStatus.RECALL_MANDATORY if not t1_safe
                else MissionOperationalStatus.RESTRICTED
            )
            advisories.append("Traverse routes restricted: Weather deterioration / low surface traction")
        elif team01.status in ("IN_PROGRESS", "RETURNING") and team01.return_margin_minutes < 90.0:
            ground_traverse_status = "CAUTION"
            overall_status = MissionOperationalStatus.ADVISORY
        else:
            ground_traverse_status = "OPEN"
            overall_status = MissionOperationalStatus.NOMINAL

        critical_comms_required = field_pax > 0 or team01.status in ("IN_PROGRESS", "RETURNING")

        assessment = MissionFeasibilityAssessment(
            assessment_id=f"MSN-{int(time.time())}",
            overall_status=overall_status,
            aviation_status=aviation_status,
            ground_traverse_status=ground_traverse_status,
            crevasse_risk_level=crevasse_risk,
            weather_summary=weather_summary,
            field_parties=field_parties,
            active_field_personnel=field_pax,
            station_personnel=station_pax,
            critical_comms_required=critical_comms_required,
            advisories=advisories,
            mandatory_actions=mandatory_actions,
        )

        self._latest_assessment = assessment
        return assessment

    def critique_proposal(
        self, proposal: ActionProposal | dict[str, Any], session_id: str = ""
    ) -> dict[str, Any] | None:
        """Formulate a cyclic deliberation critique if a candidate plan harms mission communications or crew safety."""
        # Normalize proposal fields
        if isinstance(proposal, ActionProposal):
            title = proposal.title
            prop_id = proposal.proposal_id
            overrides = proposal.parameter_overrides
        else:
            title = proposal.get("title", "Unnamed Plan")
            prop_id = proposal.get("proposal_id", "ACT-UNKNOWN")
            overrides = proposal.get("parameter_overrides", [])

        log_phy = self.engine.logistics_registry.physics
        field_pax = int(log_phy.missions.field_personnel_count)
        active_missions = int(log_phy.missions.active_missions_count)
        team01 = log_phy.missions.team01
        env_phy = self.engine.env_registry.physics
        wind_mps = env_phy.weather.wind_speed_mps

        # 1. Comms Defense Check:
        # If field personnel are deployed outside, forbid cutting power to radio repeaters or comms mast
        if field_pax > 0 or active_missions > 0 or team01.status in ("IN_PROGRESS", "RETURNING"):
            for item in overrides:
                path = (item.get("path") or item.get("target_path", "")).lower()
                val = item.get("value")
                # Look for load shedding on communications or radio assets
                if any(k in path for k in ("comms", "radio", "satcom", "antenna", "telemetry", "repeater")):
                    if val is False or (isinstance(val, (int, float)) and val <= 0.5):
                        return {
                            "proposal_id": prop_id,
                            "plan_title": title,
                            "critique_agent": self.role.value,
                            "violates_constraint": "MISSION_COMMS_PRESERVATION",
                            "severity": "CRITICAL",
                            "critique": (
                                f"VETO/CRITIQUE: Plan '{title}' shuts down mission communications '{path}' while "
                                f"Team 01 is deployed {team01.distance_km:.1f} km from Bharati ({field_pax} field pax). "
                                "Field personnel require uninterrupted radio telemetry link. "
                                "Recommendation: Protect comms sub-bus; shed unoccupied laboratory auxiliary heating instead."
                            ),
                            "recommended_action": "REGENERATE_OR_MODIFY",
                        }

        # 2. Outdoor Maintenance Blizzard Veto Check:
        # If wind is >= 25 m/s, reject proposals requiring manual outdoor physical tasks
        if wind_mps >= 25.0:
            for item in overrides:
                path = (item.get("path") or item.get("target_path", "")).lower()
                if any(k in path for k in ("outdoor", "traverse", "snowcat", "exterior", "yard")):
                    return {
                        "proposal_id": prop_id,
                        "plan_title": title,
                        "critique_agent": self.role.value,
                        "violates_constraint": "OUTDOOR_CREW_EXPOSURE_LIMIT",
                        "severity": "CRITICAL",
                        "critique": (
                            f"VETO/CRITIQUE: Plan '{title}' requires external operations on '{path}' during a severe "
                            f"katabatic blizzard (wind: {wind_mps:.1f} m/s). Immediate hypothermia and whiteout hazard. "
                            "Recommendation: Postpone outdoor physical interventions until wind drops below 15 m/s."
                        ),
                        "recommended_action": "REGENERATE_OR_MODIFY",
                    }

        return None
