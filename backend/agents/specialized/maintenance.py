"""Maintenance Specialized Cognitive Agent.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Prevent Catastrophic Mechanical Failure: Monitors machine run-hours against strict
   service intervals (Cummins QSK19 CHPs, PistenBully 300 snowcats, RO pumps).
2. Spares Inventory Defense (Madrid Protocol): Tracks wear indices and flags stockout
   risks under Antarctic winter logistics isolation (9 months with zero resupply).
3. Cyclic Deliberation Critique: Intercepts load-rebalancing and generator-switching
   proposals. If a proposal attempts to start or overload an overdue unit, Maintenance
   vetoes the proposal and recommends a healthy alternative machine with more MTBF margin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
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
    DeliberationSession,
    MessageType,
    SeverityLevel,
)
from ..framework.safety_interlock import SafetyInterlockManager

logger = logging.getLogger(__name__)


class MaintenanceUrgency(str, Enum):
    """Urgency classification for station asset maintenance."""
    NORMAL = "NORMAL"
    SERVICE_DUE_SOON = "SERVICE_DUE_SOON"  # < 100 hours remaining
    OVERDUE = "OVERDUE"                    # Past interval
    CRITICAL_WEAR = "CRITICAL_WEAR"        # Wear > 95% or overdue + missing spares
    GROUNDED = "GROUNDED"                  # Out of service


@dataclass
class AssetMaintenanceProfile:
    """Operational run-hour telemetry and service status for a physical asset."""
    asset_id: str
    asset_name: str
    subsystem: str
    current_runtime_hours: float
    service_interval_hours: float
    hours_until_service: float
    wear_percent: float
    urgency: MaintenanceUrgency
    spares_available: bool
    recommended_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "subsystem": self.subsystem,
            "current_runtime_hours": round(self.current_runtime_hours, 1),
            "service_interval_hours": round(self.service_interval_hours, 1),
            "hours_until_service": round(self.hours_until_service, 1),
            "wear_percent": round(self.wear_percent, 1),
            "urgency": self.urgency.value,
            "spares_available": self.spares_available,
            "recommended_action": self.recommended_action,
        }


@dataclass
class MaintenanceHealthReport:
    """Comprehensive station-wide equipment health and spare parts status report."""
    report_id: str
    station_id: str = "BHARATI"
    assets: list[AssetMaintenanceProfile] = field(default_factory=list)
    overdue_assets_count: int = 0
    critical_spares_risk_score: float = 0.0
    inventory_spares_summary: dict[str, float] = field(default_factory=dict)
    advisories: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "station_id": self.station_id,
            "assets": [a.to_dict() for a in self.assets],
            "overdue_assets_count": self.overdue_assets_count,
            "critical_spares_risk_score": self.critical_spares_risk_score,
            "inventory_spares_summary": self.inventory_spares_summary,
            "advisories": self.advisories,
            "timestamp": self.timestamp,
        }


class MaintenanceAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for equipment health, MTBF margins, and spares tracking."""

    # Standard Antarctic machinery maintenance specifications
    ASSET_SPECS: dict[str, dict[str, Any]] = {
        "chp_1": {
            "name": "Combined Heat & Power Unit 1 (Cummins QSK19)",
            "subsystem": "ENERGY",
            "interval_hours": 2000.0,
            "spares_key": "generator_spares_percent",
        },
        "chp_2": {
            "name": "Combined Heat & Power Unit 2 (Cummins QSK19)",
            "subsystem": "ENERGY",
            "interval_hours": 2000.0,
            "spares_key": "generator_spares_percent",
        },
        "chp_3": {
            "name": "Combined Heat & Power Unit 3 (Cummins QSK19)",
            "subsystem": "ENERGY",
            "interval_hours": 2000.0,
            "spares_key": "generator_spares_percent",
        },
        "pb01": {
            "name": "PistenBully 300 Polar Tracked Snowcat",
            "subsystem": "LOGISTICS",
            "interval_hours": 500.0,
            "spares_key": "vehicle_spares_percent",
        },
        "heli": {
            "name": "Kamov Ka-32 / Bell 407 Polar Helicopter",
            "subsystem": "LOGISTICS",
            "interval_hours": 100.0,
            "spares_key": "vehicle_spares_percent",
        },
    }

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.MAINTENANCE,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

        # Cache of latest generated maintenance report
        self._latest_report: MaintenanceHealthReport | None = None

    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages routed to MAINTENANCE role or broadcast."""
        if message.sender == self.role:
            return

        if message.message_type == MessageType.PROPOSAL:
            self._handle_proposal(message)
        elif message.message_type == MessageType.ALERT:
            self._handle_alert(message)
        elif message.message_type == MessageType.QUERY:
            self._handle_query(message)

    def _handle_proposal(self, message: AgentMessage) -> None:
        """Critique candidate proposals from Planning Agent to prevent running overdue machinery."""
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
        """Re-assess maintenance health when an equipment or logistics alert occurs."""
        report = self.generate_maintenance_report()
        self._latest_report = report

        if report.overdue_assets_count > 0 or report.critical_spares_risk_score > 0.3:
            self.publish_message(
                session_id=message.session_id,
                recipient=AgentRole.FRIDAY_ORCHESTRATOR,
                message_type=MessageType.ADVISORY,
                severity=SeverityLevel.WARNING,
                payload=report.to_dict(),
                confidence=1.0,
            )

    def _handle_query(self, message: AgentMessage) -> None:
        """Respond with current maintenance report and asset health metrics."""
        report = self.generate_maintenance_report()
        self._latest_report = report
        self.publish_message(
            session_id=message.session_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            severity=SeverityLevel.INFO,
            payload={"maintenance_report": report.to_dict()},
            confidence=1.0,
        )

    def generate_maintenance_report(self) -> MaintenanceHealthReport:
        """Compute current wear indices, hours until service, and spares availability across all assets."""
        profiles: list[AssetMaintenanceProfile] = []
        advisories: list[str] = []
        overdue_count = 0

        # Read spares inventory from logistics
        inv_state = self.engine.logistics_registry.physics.inventory
        spares_summary = {
            "generator_spares_percent": inv_state.generator_spares_percent,
            "vehicle_spares_percent": inv_state.vehicle_spares_percent,
            "water_treatment_spares_percent": inv_state.water_treatment_spares_percent,
            "emergency_batteries_count": inv_state.emergency_batteries_count,
            "stockout_risk_score": inv_state.stockout_risk_score,
        }

        # 1. Evaluate CHPs
        chps = self.engine.energy_registry.physics.chps
        for idx, chp in enumerate(chps):
            asset_id = f"chp_{idx + 1}"
            spec = self.ASSET_SPECS[asset_id]
            interval = spec["interval_hours"]
            runtime = chp.runtime_hours

            # Calculate remaining hours in current service cycle
            cycle_runtime = runtime % interval
            hours_remaining = interval - cycle_runtime
            wear_pct = min(100.0, (cycle_runtime / interval) * 100.0)

            # Check if overdue (e.g. if cycle_runtime is within 10 hours or past interval threshold)
            # In practical terms: if runtime exceeds 2000, 4000, 6000 and cycle_runtime < 100 with wear near 100%
            # Or if runtime > interval and cycle has rolled over without maintenance log
            is_overdue = (runtime >= interval and cycle_runtime < 250.0 and runtime > 2000.0) or (hours_remaining <= 0.0)
            spares_ok = inv_state.generator_spares_percent >= 40.0

            if is_overdue:
                urgency = MaintenanceUrgency.OVERDUE
                overdue_count += 1
                rec_action = f"Immediate 2,000h service required for {spec['name']} (Lube oil, injectors, fuel filters)."
                advisories.append(f"{spec['name']} is OVERDUE for scheduled maintenance.")
            elif hours_remaining <= 150.0:
                urgency = MaintenanceUrgency.SERVICE_DUE_SOON
                rec_action = f"Stage service spares for {spec['name']}; {hours_remaining:.1f} hours remaining."
                advisories.append(f"{spec['name']} service due in {hours_remaining:.1f} hours.")
            else:
                urgency = MaintenanceUrgency.NORMAL
                rec_action = f"Operating normally. Next service in {hours_remaining:.1f}h."

            profiles.append(
                AssetMaintenanceProfile(
                    asset_id=asset_id,
                    asset_name=spec["name"],
                    subsystem=spec["subsystem"],
                    current_runtime_hours=runtime,
                    service_interval_hours=interval,
                    hours_until_service=hours_remaining,
                    wear_percent=wear_pct,
                    urgency=urgency,
                    spares_available=spares_ok,
                    recommended_action=rec_action,
                )
            )

        # 2. Evaluate PistenBully Fleet (PB-01)
        pb_state = self.engine.logistics_registry.physics.fleet.pb01
        pb_spec = self.ASSET_SPECS["pb01"]
        pb_runtime = pb_state.engine_hours
        pb_interval = pb_spec["interval_hours"]
        pb_cycle = pb_runtime % pb_interval
        pb_remaining = pb_interval - pb_cycle
        pb_wear = min(100.0, (pb_cycle / pb_interval) * 100.0)
        pb_spares_ok = inv_state.vehicle_spares_percent >= 40.0

        if pb_remaining <= 0:
            pb_urg = MaintenanceUrgency.OVERDUE
            overdue_count += 1
            pb_action = "PistenBully 01 track and hydraulic filter service overdue."
        elif pb_remaining <= 50.0:
            pb_urg = MaintenanceUrgency.SERVICE_DUE_SOON
            pb_action = f"PistenBully 01 service due in {pb_remaining:.1f}h."
        else:
            pb_urg = MaintenanceUrgency.NORMAL
            pb_action = "PistenBully 01 operational."

        profiles.append(
            AssetMaintenanceProfile(
                asset_id="pb01",
                asset_name=pb_spec["name"],
                subsystem=pb_spec["subsystem"],
                current_runtime_hours=pb_runtime,
                service_interval_hours=pb_interval,
                hours_until_service=pb_remaining,
                wear_percent=pb_wear,
                urgency=pb_urg,
                spares_available=pb_spares_ok,
                recommended_action=pb_action,
            )
        )

        # 3. Evaluate Helicopter Airframe
        heli_state = self.engine.logistics_registry.physics.aviation.heli
        heli_spec = self.ASSET_SPECS["heli"]
        h_runtime = heli_state.cumulative_flight_hours
        h_interval = heli_spec["interval_hours"]
        h_cycle = h_runtime % h_interval
        h_remaining = h_interval - h_cycle
        h_wear = min(100.0, (h_cycle / h_interval) * 100.0)

        profiles.append(
            AssetMaintenanceProfile(
                asset_id="heli",
                asset_name=heli_spec["name"],
                subsystem=heli_spec["subsystem"],
                current_runtime_hours=h_runtime,
                service_interval_hours=h_interval,
                hours_until_service=h_remaining,
                wear_percent=h_wear,
                urgency=MaintenanceUrgency.NORMAL if h_remaining > 20.0 else MaintenanceUrgency.SERVICE_DUE_SOON,
                spares_available=inv_state.vehicle_spares_percent >= 40.0,
                recommended_action=f"Airframe log normal ({h_remaining:.1f}h to 100h inspection).",
            )
        )

        report = MaintenanceHealthReport(
            report_id=f"MNT-{int(time.time())}",
            station_id="BHARATI",
            assets=profiles,
            overdue_assets_count=overdue_count,
            critical_spares_risk_score=inv_state.stockout_risk_score,
            inventory_spares_summary=spares_summary,
            advisories=advisories,
        )

        self._latest_report = report
        return report

    def critique_proposal(
        self, proposal: ActionProposal | dict[str, Any], session_id: str = ""
    ) -> dict[str, Any] | None:
        """Formulate a deliberation critique if a candidate proposal attempts to start or load an overdue asset."""
        # Normalize proposal fields
        if isinstance(proposal, ActionProposal):
            title = proposal.title
            prop_id = proposal.proposal_id
            overrides = proposal.parameter_overrides
        else:
            title = proposal.get("title", "Unnamed Plan")
            prop_id = proposal.get("proposal_id", "ACT-UNKNOWN")
            overrides = proposal.get("parameter_overrides", [])

        report = self.generate_maintenance_report()
        profiles_by_id = {p.asset_id: p for p in report.assets}

        # Check if proposal activates any generator
        for item in overrides:
            path = (item.get("path") or item.get("target_path", "")).lower()
            val = str(item.get("value", "")).upper()

            # Inspect generator activations
            for idx in range(3):
                asset_key = f"chp_{idx + 1}"
                pattern = f"chps[{idx}]"
                if pattern in path and ("operating_state" in path or "active_power" in path):
                    # Check if command is starting the unit
                    is_start = val == "RUNNING" or (isinstance(item.get("value"), (int, float)) and item.get("value") > 10.0)
                    if is_start and asset_key in profiles_by_id:
                        profile = profiles_by_id[asset_key]
                        if profile.urgency in (MaintenanceUrgency.OVERDUE, MaintenanceUrgency.CRITICAL_WEAR):
                            # Find healthier alternative generator
                            alt_candidates = [
                                p for p in report.assets
                                if p.asset_id.startswith("chp_") and p.asset_id != asset_key and p.urgency == MaintenanceUrgency.NORMAL
                            ]
                            alt_candidates.sort(key=lambda p: p.hours_until_service, reverse=True)
                            alt_rec = (
                                f"Switch to {alt_candidates[0].asset_name} ({alt_candidates[0].hours_until_service:.1f}h service margin remaining)."
                                if alt_candidates
                                else "Engage emergency load shedding to avoid generator overload."
                            )

                            return {
                                "proposal_id": prop_id,
                                "plan_title": title,
                                "critique_agent": self.role.value,
                                "violates_constraint": "OVERDUE_MACHINERY_START_RESTRICTION",
                                "target_asset": profile.asset_name,
                                "severity": "CRITICAL",
                                "critique": (
                                    f"VETO/CRITIQUE: Plan '{title}' attempts to start '{profile.asset_name}', which is "
                                    f"OVERDUE for scheduled 2,000h maintenance (Runtime: {profile.current_runtime_hours:.1f}h). "
                                    "Starting an overdue unit under Antarctic winter conditions risks severe fuel injector seizure "
                                    f"or turbocharger failure. Recommendation: {alt_rec}"
                                ),
                                "recommended_action": "REGENERATE_OR_MODIFY",
                            }

        return None
