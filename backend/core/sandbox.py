"""In-Memory State-Forking and Accelerated Forward Simulation Sandbox.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Zero Mutation Contamination: Forks the entire master digital twin into isolated memory.
   Running forward projections never alters or degrades live station telemetry.
2. High-Speed Trajectory Evaluation: Simulates hours of coupled multi-pillar dynamics
   in sub-second execution times.
3. Candidate Plan Testing: Injects parameter overrides into the sandbox state and
   measures outcomes against baseline trajectories.
4. Quantitative Impact Scoring: Computes exact delta metrics (liters of fuel saved,
   thermal stability margins, battery SOC degradation, composite risk changes).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from .engine import BharatiMasterTwinEngine


@dataclass
class TrajectoryResult:
    """Time-series trajectory produced by accelerated forward simulation."""
    duration_seconds: float
    step_count: int
    time_points_hours: list[float] = field(default_factory=list)
    fuel_level_l: list[float] = field(default_factory=list)
    fuel_burn_lph: list[float] = field(default_factory=list)
    indoor_temp_c: list[float] = field(default_factory=list)
    station_load_kw: list[float] = field(default_factory=list)
    battery_soc_pct: list[float] = field(default_factory=list)
    risk_score: list[float] = field(default_factory=list)

    # Summary KPIs
    min_indoor_temp_c: float = 0.0
    max_indoor_temp_c: float = 0.0
    total_fuel_consumed_l: float = 0.0
    min_battery_soc_pct: float = 0.0
    final_autonomy_days: float = 0.0
    violations: list[str] = field(default_factory=list)


@dataclass
class PlanEvaluationDelta:
    """Quantitative comparison between an unmitigated baseline and a candidate plan."""
    plan_name: str
    duration_hours: float
    baseline_fuel_consumed_l: float
    candidate_fuel_consumed_l: float
    fuel_saved_l: float
    fuel_saved_percent: float
    baseline_min_temp_c: float
    candidate_min_temp_c: float
    temp_difference_c: float
    battery_margin_difference_pct: float
    risk_reduction_pct: float
    is_safe: bool
    safety_assessment: str


class TwinSandbox:
    """Isolated in-memory digital twin sandbox for predictive What-If simulation."""

    def __init__(self, engine: BharatiMasterTwinEngine) -> None:
        """Create an isolated sandbox containing a decoupled deepcopy of the engine."""
        self._engine: BharatiMasterTwinEngine = copy.deepcopy(engine)

    @classmethod
    def fork(cls, engine: BharatiMasterTwinEngine) -> TwinSandbox:
        """Fork the current master twin state into a new sandbox instance."""
        return cls(engine)

    @property
    def engine(self) -> BharatiMasterTwinEngine:
        """Access the isolated sandboxed twin engine."""
        return self._engine

    def apply_override(
        self,
        pillar: str,
        target_path: str,
        value: Any,
    ) -> None:
        """Inject a parameter override directly into the sandboxed physics state.
        
        Examples:
        - apply_override("energy", "chps[1].operating_state", "RUNNING")
        - apply_override("infrastructure", "hvac.ahu01_fresh_air_damper_pct", 15.0)
        - apply_override("infrastructure", "building.temp_living_c", 20.0)
        """
        pillar_lower = pillar.lower()
        if pillar_lower == "energy":
            root = self._engine.energy_registry.physics
        elif pillar_lower in ("infrastructure", "infra"):
            root = self._engine.infra_registry.physics
        elif pillar_lower in ("environment", "env"):
            root = self._engine.env_registry.physics
        elif pillar_lower in ("logistics", "log"):
            root = self._engine.logistics_registry.physics
        else:
            raise ValueError(f"Unknown pillar '{pillar}'. Must be energy, infra, env, or logistics.")

        parts = target_path.split(".")
        curr: Any = root
        for i, part in enumerate(parts[:-1]):
            # Handle indexed array lookups, e.g. chps[1]
            if "[" in part and part.endswith("]"):
                name, idx_str = part[:-1].split("[")
                curr = getattr(curr, name)[int(idx_str)]
            else:
                curr = getattr(curr, part)

        final_field = parts[-1]
        if "[" in final_field and final_field.endswith("]"):
            name, idx_str = final_field[:-1].split("[")
            getattr(curr, name)[int(idx_str)] = value
        else:
            setattr(curr, final_field, value)

    def apply_plan(self, plan_overrides: list[dict[str, Any]]) -> None:
        """Apply a batch of candidate plan overrides.
        
        Format of each override:
        {"pillar": "energy", "path": "chps[1].operating_state", "value": "RUNNING"}
        """
        for item in plan_overrides:
            self.apply_override(item["pillar"], item["path"], item["value"])

    def run_fast_forward(
        self,
        duration_seconds: float = 14400.0,  # 4 hours default
        dt_seconds: float = 60.0,
    ) -> TrajectoryResult:
        """Execute accelerated forward simulation and record the physical trajectory."""
        if duration_seconds <= 0 or dt_seconds <= 0:
            raise ValueError("Duration and dt must be positive values.")

        steps = int(duration_seconds / dt_seconds)
        traj = TrajectoryResult(duration_seconds=duration_seconds, step_count=steps)

        initial_fuel = (
            self._engine.energy_registry.physics.fuel.bulk_fuel_level_l
            + self._engine.energy_registry.physics.fuel.day_tank_level_l
        )

        min_temp = float("inf")
        max_temp = float("-inf")
        min_battery_soc = float("inf")

        for step_idx in range(steps):
            self._engine.step_physics_only(dt_seconds)
            kpis = self._engine.get_station_kpis()

            t_hours = round(((step_idx + 1) * dt_seconds) / 3600.0, 3)
            traj.time_points_hours.append(t_hours)
            traj.fuel_level_l.append(kpis["total_fuel_reserve_l"])
            traj.fuel_burn_lph.append(self._engine.energy_registry.physics.fuel.fuel_flow_lph)
            traj.indoor_temp_c.append(kpis["indoor_avg_temp_c"])
            traj.station_load_kw.append(kpis["station_electrical_load_kw"])

            # Battery SOC tracking across UPS
            ups_socs = [u.battery_soc_percent for u in self._engine.energy_registry.physics.ups]
            avg_soc = sum(ups_socs) / max(len(ups_socs), 1)
            traj.battery_soc_pct.append(round(avg_soc, 1))
            traj.risk_score.append(kpis["composite_risk_score"])

            # Track bounds
            if kpis["indoor_avg_temp_c"] < min_temp:
                min_temp = kpis["indoor_avg_temp_c"]
            if kpis["indoor_avg_temp_c"] > max_temp:
                max_temp = kpis["indoor_avg_temp_c"]
            if avg_soc < min_battery_soc:
                min_battery_soc = avg_soc

            # Life-safety threshold violations
            if kpis["indoor_avg_temp_c"] < 16.0:
                msg = f"T={t_hours}h: Indoor temp dropped below 16°C ({kpis['indoor_avg_temp_c']} °C)"
                if msg not in traj.violations:
                    traj.violations.append(msg)

            if kpis["station_electrical_load_kw"] > 190.0:
                msg = f"T={t_hours}h: Electrical load exceeded 95% continuous capacity ({kpis['station_electrical_load_kw']} kW)"
                if msg not in traj.violations:
                    traj.violations.append(msg)

        final_fuel = (
            self._engine.energy_registry.physics.fuel.bulk_fuel_level_l
            + self._engine.energy_registry.physics.fuel.day_tank_level_l
        )
        traj.total_fuel_consumed_l = round(max(0.0, initial_fuel - final_fuel), 1)
        traj.min_indoor_temp_c = round(min_temp, 2)
        traj.max_indoor_temp_c = round(max_temp, 2)
        traj.min_battery_soc_pct = round(min_battery_soc, 1)
        traj.final_autonomy_days = kpis["fuel_autonomy_days"]

        # Refresh cached readings once at simulation conclusion
        self._engine._refresh_all_readings()

        return traj

    @staticmethod
    def compare_trajectories(
        baseline: TrajectoryResult,
        candidate: TrajectoryResult,
        plan_name: str = "Candidate Plan",
    ) -> PlanEvaluationDelta:
        """Compute the quantitative delta between baseline and candidate trajectories."""
        duration_h = round(baseline.duration_seconds / 3600.0, 1)
        fuel_saved = round(baseline.total_fuel_consumed_l - candidate.total_fuel_consumed_l, 1)
        fuel_saved_pct = round(
            (fuel_saved / max(baseline.total_fuel_consumed_l, 1.0)) * 100.0, 2
        )

        temp_diff = round(candidate.min_indoor_temp_c - baseline.min_indoor_temp_c, 2)
        batt_diff = round(candidate.min_battery_soc_pct - baseline.min_battery_soc_pct, 1)

        base_avg_risk = sum(baseline.risk_score) / max(len(baseline.risk_score), 1)
        cand_avg_risk = sum(candidate.risk_score) / max(len(candidate.risk_score), 1)
        risk_reduction = round(((base_avg_risk - cand_avg_risk) / max(base_avg_risk, 1.0)) * 100.0, 1)

        is_safe = len(candidate.violations) == 0

        if is_safe:
            safety_assessment = (
                f"PASSED: Plan maintains life-support thresholds across {duration_h}h. "
                f"Fuel delta: {fuel_saved:+.1f} L ({fuel_saved_pct:+.1f}%). "
                f"Indoor temp margin: {temp_diff:+.1f} °C."
            )
        else:
            safety_assessment = (
                f"REJECTED: Plan causes {len(candidate.violations)} safety violation(s): "
                f"{'; '.join(candidate.violations[:2])}"
            )

        return PlanEvaluationDelta(
            plan_name=plan_name,
            duration_hours=duration_h,
            baseline_fuel_consumed_l=baseline.total_fuel_consumed_l,
            candidate_fuel_consumed_l=candidate.total_fuel_consumed_l,
            fuel_saved_l=fuel_saved,
            fuel_saved_percent=fuel_saved_pct,
            baseline_min_temp_c=baseline.min_indoor_temp_c,
            candidate_min_temp_c=candidate.min_indoor_temp_c,
            temp_difference_c=temp_diff,
            battery_margin_difference_pct=batt_diff,
            risk_reduction_pct=risk_reduction,
            is_safe=is_safe,
            safety_assessment=safety_assessment,
        )
