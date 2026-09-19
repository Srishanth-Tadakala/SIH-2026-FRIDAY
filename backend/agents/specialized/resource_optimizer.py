"""Resource Optimization Specialized Cognitive Agent.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Engine Sweet-Spot Operation: Allocates electrical generation so active CHPs operate
   in their optimal Brake Specific Fuel Consumption (BSFC) band (60% to 80% load),
   maximizing waste-heat thermal recovery into the primary glycol loop.
2. Wet Stacking & Carbon Fouling Prevention: Flags and prevents running diesel generators
   below 40% load for prolonged periods under sub-zero polar conditions.
3. Potable Water Desalination Co-Generation: Synchronizes energy-intensive Reverse
   Osmosis (RO) filtration runs with periods of surplus thermal/electrical headroom.
4. Cyclic Deliberation Critique: Intercepts load-balancing and generator proposals from
   the Planning Agent, vetoing or optimizing multi-unit underloading into efficient
   single-unit consolidated dispatch schedules.
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


class OptimizationObjective(str, Enum):
    """Operational objective for station resource optimization."""
    BALANCED = "BALANCED"                          # Fuel economy + thermal security + battery buffer
    MAX_FUEL_CONSERVATION = "MAX_FUEL_CONSERVATION"  # Emergency winter fuel preservation
    MAX_THERMAL_SECURITY = "MAX_THERMAL_SECURITY"    # Extreme blizzard wind-chill heating
    BATTERY_LIFE_PRESERVATION = "BATTERY_LIFE_PRESERVATION" # Minimize UPS battery cycling


@dataclass
class CHPDispatchRecommendation:
    """Optimal operating point and load factor for an individual generator."""
    chp_index: int
    recommended_state: Literal["RUNNING", "STANDBY", "OFF"]
    recommended_load_kw: float
    load_factor_percent: float
    fuel_flow_lph: float
    is_optimal_band: bool
    efficiency_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chp_index": self.chp_index,
            "recommended_state": self.recommended_state,
            "recommended_load_kw": round(self.recommended_load_kw, 1),
            "load_factor_percent": round(self.load_factor_percent, 1),
            "fuel_flow_lph": round(self.fuel_flow_lph, 1),
            "is_optimal_band": self.is_optimal_band,
            "efficiency_note": self.efficiency_note,
        }


@dataclass
class ResourceOptimizationPlan:
    """Comprehensive multi-pillar resource dispatch plan for Bharati Station."""
    plan_id: str
    objective: OptimizationObjective
    current_electrical_load_kw: float
    recommended_generation_kw: float
    chp_dispatches: list[CHPDispatchRecommendation]
    daily_fuel_burn_l: float
    projected_fuel_savings_l_per_day: float
    fuel_autonomy_days: float
    ro_water_schedule: str
    battery_peak_shaving_active: bool
    optimizations_applied: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "objective": self.objective.value,
            "current_electrical_load_kw": round(self.current_electrical_load_kw, 1),
            "recommended_generation_kw": round(self.recommended_generation_kw, 1),
            "chp_dispatches": [c.to_dict() for c in self.chp_dispatches],
            "daily_fuel_burn_l": round(self.daily_fuel_burn_l, 1),
            "projected_fuel_savings_l_per_day": round(self.projected_fuel_savings_l_per_day, 1),
            "fuel_autonomy_days": round(self.fuel_autonomy_days, 1),
            "ro_water_schedule": self.ro_water_schedule,
            "battery_peak_shaving_active": self.battery_peak_shaving_active,
            "optimizations_applied": self.optimizations_applied,
            "timestamp": self.timestamp,
        }


class ResourceOptimizerAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for optimal energy dispatch and fuel/water conservation."""

    # Continuous rating for 100 kVA Cummins QSK19 at 0.88 power factor ~ 80 kW
    CHP_RATED_KW: float = 80.0
    SWEET_SPOT_MIN_KW: float = 48.0   # 60% load factor
    SWEET_SPOT_MAX_KW: float = 68.0   # 85% load factor
    WET_STACKING_LIMIT_KW: float = 32.0 # 40% load factor (sub-40% causes exhaust unburnt carbon)

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        super().__init__(
            role=AgentRole.RESOURCE_OPTIMIZER,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

        self._latest_plan: ResourceOptimizationPlan | None = None

    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages routed to RESOURCE_OPTIMIZER role or broadcast."""
        if message.sender == self.role:
            return

        if message.message_type == MessageType.PROPOSAL:
            self._handle_proposal(message)
        elif message.message_type == MessageType.ALERT:
            self._handle_alert(message)
        elif message.message_type == MessageType.QUERY:
            self._handle_query(message)

    def _handle_proposal(self, message: AgentMessage) -> None:
        """Critique candidate proposals from Planning Agent to optimize resource efficiency."""
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
        """Recompute optimal dispatch schedule upon grid power or fuel alerts."""
        plan = self.compute_optimal_dispatch()
        self._latest_plan = plan

        self.publish_message(
            session_id=message.session_id,
            recipient=AgentRole.FRIDAY_ORCHESTRATOR,
            message_type=MessageType.ADVISORY,
            severity=SeverityLevel.INFO,
            payload=plan.to_dict(),
            confidence=1.0,
        )

    def _handle_query(self, message: AgentMessage) -> None:
        """Respond with the current optimal resource dispatch plan."""
        obj_str = message.payload.get("objective", "BALANCED")
        try:
            obj = OptimizationObjective(obj_str)
        except ValueError:
            obj = OptimizationObjective.BALANCED

        plan = self.compute_optimal_dispatch(objective=obj)
        self._latest_plan = plan
        self.publish_message(
            session_id=message.session_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            severity=SeverityLevel.INFO,
            payload={"resource_plan": plan.to_dict()},
            confidence=1.0,
        )

    def compute_optimal_dispatch(
        self, objective: OptimizationObjective = OptimizationObjective.BALANCED
    ) -> ResourceOptimizationPlan:
        """Solve for Pareto-optimal CHP load dispatch, water production, and fuel burn."""
        kpis = self.engine.get_station_kpis()
        station_load = float(kpis["station_electrical_load_kw"])
        total_fuel = float(kpis["total_fuel_reserve_l"])
        autonomy_days = float(kpis["fuel_autonomy_days"])

        optimizations: list[str] = []

        # 1. Determine optimal number of running CHPs to stay in sweet-spot band
        # Capacity per CHP = 80 kW
        if station_load <= 72.0:
            active_units_count = 1
            optimizations.append("Single-unit consolidated dispatch (avoids multi-unit idling losses)")
        elif station_load <= 140.0:
            active_units_count = 2
            optimizations.append("Dual-unit balanced load sharing (both units within 50-85% optimal band)")
        else:
            active_units_count = 3
            optimizations.append("Tri-unit full station capacity dispatch")

        load_per_active_unit = round(station_load / max(active_units_count, 1), 1)

        dispatches: list[CHPDispatchRecommendation] = []
        total_fuel_lph = 0.0

        for i in range(3):
            chp_idx = i + 1
            if i < active_units_count:
                unit_kw = load_per_active_unit
                state: Literal["RUNNING", "STANDBY", "OFF"] = "RUNNING"
                load_pct = (unit_kw / self.CHP_RATED_KW) * 100.0
                # Fuel model: base idle ~ 3.5 LPH + 0.24 L/kWh
                unit_lph = 3.5 + (0.24 * unit_kw)
                in_optimal = self.SWEET_SPOT_MIN_KW <= unit_kw <= self.SWEET_SPOT_MAX_KW
                note = (
                    "Operating in optimal thermal recovery & low BSFC band."
                    if in_optimal
                    else ("High specific fuel consumption (underloaded)" if unit_kw < self.WET_STACKING_LIMIT_KW else "Near continuous limit")
                )
            else:
                unit_kw = 0.0
                state = "STANDBY"
                load_pct = 0.0
                unit_lph = 0.0
                in_optimal = True
                note = "Hot standby readiness."

            total_fuel_lph += unit_lph
            dispatches.append(
                CHPDispatchRecommendation(
                    chp_index=chp_idx,
                    recommended_state=state,
                    recommended_load_kw=unit_kw,
                    load_factor_percent=load_pct,
                    fuel_flow_lph=unit_lph,
                    is_optimal_band=in_optimal,
                    efficiency_note=note,
                )
            )

        daily_burn_l = total_fuel_lph * 24.0

        # Estimate savings vs unoptimized status quo (e.g. running 2 units inefficiently at half load)
        unoptimized_burn_l = (2 * 3.5 + 0.28 * station_load) * 24.0
        fuel_savings_l = max(0.0, unoptimized_burn_l - daily_burn_l)

        # 2. Water Desalination Co-Generation Scheduling
        water_kpi = float(kpis.get("potable_tank_level_pct", 80.0))
        if water_kpi < 50.0 and active_units_count >= 1:
            ro_schedule = "SCHEDULED_CONTINUOUS: Potable storage < 50%; run RO unit co-generation."
            optimizations.append("Engage RO desalination with generator waste-heat recovery.")
        elif station_load < 50.0 and water_kpi < 85.0:
            ro_schedule = "VALLEY_FILLING: Run RO desalination during low-load period to boost CHP into optimal band."
            optimizations.append("Valley-filling: RO plant load elevates CHP above wet-stacking threshold.")
        else:
            ro_schedule = "STANDBY: Potable buffer adequate; defer RO power consumption."

        # 3. Peak-Shaving with UPS Battery Buffer
        battery_peak_shaving = station_load > 140.0
        if battery_peak_shaving:
            optimizations.append("Activate UPS battery buffer for transient peak-shaving (> 140 kW).")

        plan = ResourceOptimizationPlan(
            plan_id=f"OPT-{int(time.time())}",
            objective=objective,
            current_electrical_load_kw=station_load,
            recommended_generation_kw=station_load,
            chp_dispatches=dispatches,
            daily_fuel_burn_l=daily_burn_l,
            projected_fuel_savings_l_per_day=fuel_savings_l,
            fuel_autonomy_days=autonomy_days,
            ro_water_schedule=ro_schedule,
            battery_peak_shaving_active=battery_peak_shaving,
            optimizations_applied=optimizations,
        )

        self._latest_plan = plan
        return plan

    def critique_proposal(
        self, proposal: ActionProposal | dict[str, Any], session_id: str = ""
    ) -> dict[str, Any] | None:
        """Formulate a deliberation critique if a candidate proposal creates severe underload or fuel waste."""
        # Normalize proposal fields
        if isinstance(proposal, ActionProposal):
            title = proposal.title
            prop_id = proposal.proposal_id
            overrides = proposal.parameter_overrides
        else:
            title = proposal.get("title", "Unnamed Plan")
            prop_id = proposal.get("proposal_id", "ACT-UNKNOWN")
            overrides = proposal.get("parameter_overrides", [])

        # Track commanded generator loads across overrides
        commanded_chps: dict[int, float] = {}
        for item in overrides:
            path = (item.get("path") or item.get("target_path", "")).lower()
            val = item.get("value")
            for idx in range(3):
                if f"chps[{idx}].active_power_kw" in path and isinstance(val, (int, float)):
                    commanded_chps[idx + 1] = float(val)

        # Wet Stacking Critique: If 2 or more units are commanded to run at < 35 kW each
        underloaded_units = [idx for idx, kw in commanded_chps.items() if 0.0 < kw < self.WET_STACKING_LIMIT_KW]
        if len(underloaded_units) >= 2:
            total_kw = sum(commanded_chps[u] for u in underloaded_units)
            return {
                "proposal_id": prop_id,
                "plan_title": title,
                "critique_agent": self.role.value,
                "violates_constraint": "ENGINE_WET_STACKING_PREVENTION",
                "severity": "WARNING",
                "critique": (
                    f"OPTIMIZATION/CRITIQUE: Plan '{title}' allocates underloaded power to multiple generators "
                    f"(CHPs {underloaded_units} at < {self.WET_STACKING_LIMIT_KW} kW each, total {total_kw:.1f} kW). "
                    "Running diesel generators below 40% load causes severe engine wet stacking (unburnt fuel glazing, "
                    "carbon buildup in exhaust manifold, and elevated BSFC). "
                    f"Recommendation: Consolidate load onto a single generator at {total_kw:.1f} kW (sweet-spot band)."
                ),
                "recommended_action": "REGENERATE_OR_MODIFY",
            }

        # Excessive Fuel Waste Critique: If total commanded power exceeds station demand by > 50 kW
        kpis = self.engine.get_station_kpis()
        actual_load = float(kpis["station_electrical_load_kw"])
        total_commanded = sum(commanded_chps.values())
        if total_commanded >= actual_load + 55.0 and len(commanded_chps) >= 2:
            return {
                "proposal_id": prop_id,
                "plan_title": title,
                "critique_agent": self.role.value,
                "violates_constraint": "EXCESSIVE_FUEL_CONSUMPTION",
                "severity": "WARNING",
                "critique": (
                    f"OPTIMIZATION/CRITIQUE: Plan '{title}' commands {total_commanded:.1f} kW generation, which exceeds "
                    f"station demand ({actual_load:.1f} kW) by {total_commanded - actual_load:.1f} kW. "
                    "Excessive generation burns unrecoverable Jet A-1 fuel reserves during winter isolation. "
                    f"Recommendation: Throttle surplus generator capacity to match station load."
                ),
                "recommended_action": "REGENERATE_OR_MODIFY",
            }

        return None
