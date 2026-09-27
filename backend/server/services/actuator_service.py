"""Actuator & Physical Plant Domain Service for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from typing import Any, Dict
from ...agents.framework.models import ActionProposal, AutonomyTier


class ActuatorService:
    """Coordinates physical equipment state queries and tiered command execution."""

    def __init__(self, server_state: Any) -> None:
        self.state = server_state

    def get_actuators_state(self, station_id: str) -> Dict[str, Any]:
        """Return comprehensive physical equipment states for the given station."""
        return self.state.get_actuator_state(station_id)

    def execute_action(
        self,
        proposal: ActionProposal,
        station_id: str = "bharati",
        commander_pin: str | None = None,
        execution_token: str | None = None,
    ) -> Any:
        """Execute or queue an action proposal subject to deterministic life-support safety interlocks."""
        engine = self.state.stations.get(station_id.lower(), self.state.get_engine())
        return self.state.safety_interlock.execute_action(
            proposal=proposal,
            engine=engine,
            commander_pin=commander_pin,
            execution_token=execution_token,
        )

    def get_pending_tier3_actions(self) -> list[Dict[str, Any]]:
        """List all actions pending Station Commander PIN authorization."""
        return self.state.safety_interlock.get_pending_tier3_actions()

    def authorize_tier3_action(
        self,
        action_id: str,
        pin: str,
        station_id: str = "bharati",
    ) -> Any:
        """Authorize and dispatch a pending Tier 3 life-critical action."""
        engine = self.state.stations.get(station_id.lower(), self.state.get_engine())
        return self.state.safety_interlock.authorize_and_execute_tier3(
            proposal_id=action_id,
            engine=engine,
            commander_pin=pin,
        )

    def cancel_tier3_action(self, action_id: str) -> bool:
        """Cancel and purge a pending Tier 3 action from the confirmation queue."""
        return self.state.safety_interlock.cancel_tier3_action(action_id)


def get_actuator_service() -> ActuatorService:
    """FastAPI Dependency Injection provider for ActuatorService."""
    from ..state import get_server_state
    state = get_server_state()
    return getattr(state, "actuator_service", ActuatorService(state))
