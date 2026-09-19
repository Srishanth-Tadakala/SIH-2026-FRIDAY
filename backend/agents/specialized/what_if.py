"""What-If / Simulation Specialized Cognitive Agent.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Zero Mutation Contamination: Forks the entire master digital twin into isolated memory.
   Running forward projections never alters or degrades live station telemetry.
2. Counterfactual Trajectory Evaluation: Injects proposed operational changes and compares
   trajectories against unmitigated baselines across multiple horizons (1h to 4h).
3. Quantitative KPI Delta Scoring: Computes exact delta metrics (liters of fuel saved,
   thermal stability margins, battery SOC degradation, composite risk changes).
4. Multi-Agent Deliberation Feedback: When candidate plans violate life-support guardrails
   or produce negative side-effects, formulates counterfactual critiques to force Planning
   re-deliberation rather than linear execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import Any, Literal

from ...core.causal_graph import TwinCausalGraph
from ...core.engine import BharatiMasterTwinEngine
from ...core.sandbox import PlanEvaluationDelta, TrajectoryResult, TwinSandbox
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

logger = logging.getLogger(__name__)


@dataclass
class PlanSimulationVerdict:
    """Quantitative outcome and safety evaluation of a simulated operational action proposal."""
    proposal_id: str
    plan_title: str
    is_safe: bool
    recommendation: Literal["APPROVE", "REJECT", "MODIFY"]
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
    violations: list[str] = field(default_factory=list)
    safety_assessment: str = ""
    counterfactual_critique: str | None = None
    simulation_timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize simulation verdict to dictionary for JSON streaming and bus messaging."""
        return {
            "proposal_id": self.proposal_id,
            "plan_title": self.plan_title,
            "is_safe": self.is_safe,
            "recommendation": self.recommendation,
            "duration_hours": self.duration_hours,
            "baseline_fuel_consumed_l": self.baseline_fuel_consumed_l,
            "candidate_fuel_consumed_l": self.candidate_fuel_consumed_l,
            "fuel_saved_l": self.fuel_saved_l,
            "fuel_saved_percent": self.fuel_saved_percent,
            "baseline_min_temp_c": self.baseline_min_temp_c,
            "candidate_min_temp_c": self.candidate_min_temp_c,
            "temp_difference_c": self.temp_difference_c,
            "battery_margin_difference_pct": self.battery_margin_difference_pct,
            "risk_reduction_pct": self.risk_reduction_pct,
            "violations": self.violations,
            "safety_assessment": self.safety_assessment,
            "counterfactual_critique": self.counterfactual_critique,
            "simulation_timestamp": self.simulation_timestamp,
        }


class WhatIfSimulationAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for counterfactual forward simulation of candidate action plans."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
        default_duration_seconds: float = 7200.0,  # 2 hours default
        default_dt_seconds: float = 60.0,          # 1 minute steps
    ) -> None:
        super().__init__(
            role=AgentRole.WHAT_IF,
            bus=bus,
            engine=engine,
            graph=graph,
            safety_interlock=safety_interlock,
        )

        self.default_duration_seconds = default_duration_seconds
        self.default_dt_seconds = default_dt_seconds

        # Cache of simulated plan verdicts: proposal_id -> PlanSimulationVerdict
        self._verdicts: dict[str, PlanSimulationVerdict] = {}
        self._sim_history: list[PlanSimulationVerdict] = []

    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming messages routed to WHAT_IF role."""
        if message.sender == self.role:
            return

        if message.message_type == MessageType.PROPOSAL:
            self.on_proposal_received(message)
        elif message.message_type == MessageType.SIM_REQUEST:
            self.on_sim_request_received(message)
        elif message.message_type == MessageType.QUERY:
            query_id = message.payload.get("proposal_id")
            if query_id and query_id in self._verdicts:
                resp_payload = {"verdict": self._verdicts[query_id].to_dict()}
            else:
                resp_payload = {
                    "total_simulations": len(self._sim_history),
                    "verdicts": [v.to_dict() for v in self._sim_history[-5:]],
                }
            self.publish_message(
                session_id=message.session_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                severity=SeverityLevel.INFO,
                payload=resp_payload,
                confidence=1.0,
            )

    def on_proposal_received(self, message: AgentMessage) -> None:
        """Evaluate candidate action proposals dispatched across the bus."""
        proposal_data = message.payload
        session_id = message.session_id
        session = self.bus.get_session(session_id) if session_id else None

        verdict = self.evaluate_proposal(
            proposal=proposal_data,
            session_id=session_id,
            session=session,
        )

        self._dispatch_verdict(verdict, session_id, session)

    def on_sim_request_received(self, message: AgentMessage) -> None:
        """Handle explicit simulation requests from Orchestrator, Planning, or Operator."""
        payload = message.payload
        duration_s = float(payload.get("duration_seconds", self.default_duration_seconds))
        dt_s = float(payload.get("dt_seconds", self.default_dt_seconds))

        proposal_data = payload.get("proposal", payload)
        session_id = message.session_id
        session = self.bus.get_session(session_id) if session_id else None

        verdict = self.evaluate_proposal(
            proposal=proposal_data,
            session_id=session_id,
            session=session,
            duration_seconds=duration_s,
            dt_seconds=dt_s,
        )

        self.publish_message(
            session_id=session_id,
            recipient=message.sender,
            message_type=MessageType.SIM_RESULT,
            severity=SeverityLevel.INFO if verdict.is_safe else SeverityLevel.WARNING,
            payload=verdict.to_dict(),
            confidence=1.0,
        )

    def _dispatch_verdict(
        self,
        verdict: PlanSimulationVerdict,
        session_id: str,
        session: DeliberationSession | None,
    ) -> None:
        """Publish simulation results and critiques back to Planning and Orchestrator."""
        verdict_dict = verdict.to_dict()
        severity = SeverityLevel.INFO if verdict.is_safe else SeverityLevel.CRITICAL

        # 1. Publish SIM_RESULT to Orchestrator and Planning
        self.publish_message(
            session_id=session_id,
            recipient=AgentRole.FRIDAY_ORCHESTRATOR,
            message_type=MessageType.SIM_RESULT,
            severity=severity,
            payload=verdict_dict,
            confidence=1.0,
        )

        self.publish_message(
            session_id=session_id,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.SIM_RESULT,
            severity=severity,
            payload=verdict_dict,
            confidence=1.0,
        )

        # 2. If plan is unsafe, publish explicit CRITIQUE to force Planning re-deliberation
        if not verdict.is_safe and verdict.counterfactual_critique:
            critique_payload = {
                "proposal_id": verdict.proposal_id,
                "plan_title": verdict.plan_title,
                "violations": verdict.violations,
                "critique": verdict.counterfactual_critique,
                "recommended_action": "REGENERATE_OR_MODIFY",
            }
            self.publish_message(
                session_id=session_id,
                recipient=AgentRole.PLANNING,
                message_type=MessageType.CRITIQUE,
                severity=SeverityLevel.WARNING,
                payload=critique_payload,
                confidence=1.0,
            )

            if session:
                session.critiques.append(critique_payload)

    def evaluate_proposal(
        self,
        proposal: ActionProposal | dict[str, Any],
        session_id: str = "",
        session: DeliberationSession | None = None,
        duration_seconds: float | None = None,
        dt_seconds: float | None = None,
    ) -> PlanSimulationVerdict:
        """Execute counterfactual forward simulation for an operational proposal against baseline."""
        duration_s = duration_seconds or self.default_duration_seconds
        dt_s = dt_seconds or self.default_dt_seconds

        # Normalize proposal fields
        if isinstance(proposal, ActionProposal):
            prop_id = proposal.proposal_id
            prop_title = proposal.title
            overrides = proposal.parameter_overrides
            prop_obj = proposal
        else:
            prop_id = proposal.get("proposal_id", "ACT-UNKNOWN")
            prop_title = proposal.get("title", "Unnamed Plan")
            overrides = proposal.get("parameter_overrides", [])
            prop_obj = None

        # 1. Baseline Simulation (Current state unmitigated forward trajectory)
        sandbox_baseline = self.fork_sandbox()
        baseline_traj: TrajectoryResult = sandbox_baseline.run_fast_forward(
            duration_seconds=duration_s,
            dt_seconds=dt_s,
        )

        # 2. Candidate Plan Simulation (Fork independent state, apply overrides, simulate)
        sandbox_cand = self.fork_sandbox()
        self._apply_overrides_safely(sandbox_cand, overrides)
        cand_traj: TrajectoryResult = sandbox_cand.run_fast_forward(
            duration_seconds=duration_s,
            dt_seconds=dt_s,
        )

        # 3. Trajectory Comparison
        delta: PlanEvaluationDelta = TwinSandbox.compare_trajectories(
            baseline=baseline_traj,
            candidate=cand_traj,
            plan_name=prop_title,
        )

        # 4. Domain & Life-Support Guardrail Checks
        violations = list(cand_traj.violations)

        # Check explicit parameter overrides against domain safety limits
        for item in overrides:
            path = item.get("path") or item.get("target_path", "")
            val = item.get("value")
            if "temp" in path and isinstance(val, (int, float)) and val < 16.0:
                violation_msg = (
                    f"Thermal Setpoint Breach: Commanded {path}={val}°C is below 16.0°C life-support floor."
                )
                if violation_msg not in violations:
                    violations.append(violation_msg)
            if "power" in path and isinstance(val, (int, float)) and val > 190.0:
                violation_msg = (
                    f"Electrical Overload: Commanded {path}={val} kW exceeds 190.0 kW capacity limit."
                )
                if violation_msg not in violations:
                    violations.append(violation_msg)

        # Check indoor temperature floor
        if cand_traj.min_indoor_temp_c < 16.0:
            violation_msg = f"Thermal Floor Breach: Indoor temp drops to {cand_traj.min_indoor_temp_c:.1f}°C (< 16.0°C life-support minimum)."
            if violation_msg not in violations:
                violations.append(violation_msg)

        # Check battery reserve floor
        if cand_traj.min_battery_soc_pct < 30.0:
            violation_msg = f"Battery Depletion: UPS reserve drops to {cand_traj.min_battery_soc_pct:.1f}% (< 30.0% critical buffer)."
            if violation_msg not in violations:
                violations.append(violation_msg)

        is_safe = len(violations) == 0

        # 5. Recommendation & Counterfactual Critique Formulation
        if not is_safe:
            recommendation: Literal["APPROVE", "REJECT", "MODIFY"] = "REJECT"
            counterfactual_critique = (
                f"CRITIQUE: Plan '{prop_title}' fails safety verification over {delta.duration_hours}h horizon. "
                f"Violations detected: {'; '.join(violations[:2])}. "
                f"Counterfactual finding: Candidate indoor temp min is {cand_traj.min_indoor_temp_c:.1f}°C vs baseline {baseline_traj.min_indoor_temp_c:.1f}°C. "
                "Recommendation: Invalidate or adjust load-shedding parameters to preserve life-support envelope."
            )
        elif delta.risk_reduction_pct < -5.0:
            recommendation = "MODIFY"
            counterfactual_critique = (
                f"ADVISORY: Plan '{prop_title}' is thermally safe but increases composite risk score by {-delta.risk_reduction_pct:.1f}%. "
                "Consider pairing with secondary auxiliary generator throttle."
            )
        else:
            recommendation = "APPROVE"
            counterfactual_critique = None

        verdict = PlanSimulationVerdict(
            proposal_id=prop_id,
            plan_title=prop_title,
            is_safe=is_safe,
            recommendation=recommendation,
            duration_hours=delta.duration_hours,
            baseline_fuel_consumed_l=delta.baseline_fuel_consumed_l,
            candidate_fuel_consumed_l=delta.candidate_fuel_consumed_l,
            fuel_saved_l=delta.fuel_saved_l,
            fuel_saved_percent=delta.fuel_saved_percent,
            baseline_min_temp_c=delta.baseline_min_temp_c,
            candidate_min_temp_c=delta.candidate_min_temp_c,
            temp_difference_c=delta.temp_difference_c,
            battery_margin_difference_pct=delta.battery_margin_difference_pct,
            risk_reduction_pct=delta.risk_reduction_pct,
            violations=violations,
            safety_assessment=delta.safety_assessment,
            counterfactual_critique=counterfactual_critique,
        )

        # Update proposal status and simulation delta on the proposal object
        if prop_obj:
            prop_obj.simulation_delta = verdict.to_dict()
            prop_obj.status = ProposalStatus.SIMULATED if is_safe else ProposalStatus.REJECTED

        self._verdicts[prop_id] = verdict
        self._sim_history.append(verdict)

        return verdict

    def compare_proposals(
        self,
        proposals: list[ActionProposal | dict[str, Any]],
        duration_seconds: float | None = None,
        dt_seconds: float | None = None,
    ) -> list[PlanSimulationVerdict]:
        """Simulate and rank multiple candidate proposals for multi-agent trade-off analysis."""
        verdicts: list[PlanSimulationVerdict] = []
        for prop in proposals:
            verdict = self.evaluate_proposal(
                proposal=prop,
                duration_seconds=duration_seconds,
                dt_seconds=dt_seconds,
            )
            verdicts.append(verdict)

        # Ranking logic:
        # 1. Safe plans before unsafe plans
        # 2. Higher risk reduction %
        # 3. Higher thermal difference margin (°C)
        # 4. More fuel saved (L)
        verdicts.sort(
            key=lambda v: (
                1 if v.is_safe else 0,
                v.risk_reduction_pct,
                v.temp_difference_c,
                v.fuel_saved_l,
            ),
            reverse=True,
        )

        return verdicts

    def _apply_overrides_safely(self, sandbox: TwinSandbox, overrides: list[dict[str, Any]]) -> None:
        """Apply plan overrides to sandbox handling key naming variations and field bounds."""
        for item in overrides:
            pillar = item.get("pillar", "energy")
            path = item.get("path") or item.get("target_path", "")
            value = item.get("value")

            if not path:
                continue

            try:
                sandbox.apply_override(pillar, path, value)
            except Exception as exc:
                logger.warning("Failed to apply sandbox override '%s.%s=%s': %s", pillar, path, value, exc)
