"""Station Domain Service for F.R.I.D.A.Y. Dual-Station Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import HTTPException


class StationService:
    """Manages dual Antarctic station lifecycle, active station contexts, and simulation stepping."""

    def __init__(self, server_state: Any) -> None:
        self.state = server_state

    def get_all_stations_summary(self) -> List[Dict[str, Any]]:
        """Return operational telemetry summaries for all managed Antarctic stations."""
        return self.state.get_all_stations_summary()

    def get_station_summary(self, station_id: str) -> Dict[str, Any]:
        """Retrieve real-time health and environmental summary for a specific station."""
        sid = station_id.lower()
        if sid not in self.state.stations:
            raise KeyError(f"Station '{station_id}' not found. Valid: {list(self.state.stations.keys())}")
        return self.state.get_station_summary(sid)

    def set_active_station(self, station_id: str) -> str:
        """Switch active operational station context."""
        sid = station_id.lower()
        if sid not in self.state.stations:
            raise KeyError(f"Unknown station '{station_id}'. Managed stations: {list(self.state.stations.keys())}")
        self.state.set_active_station(sid)
        return self.state.active_station_id

    def step(self, dt_seconds: float = 1.0) -> Dict[str, Any]:
        """Advance the digital twin simulation clock."""
        return self.state.step(dt_seconds=dt_seconds)


def get_station_service() -> StationService:
    """FastAPI Dependency Injection provider for StationService."""
    from ..state import get_server_state
    state = get_server_state()
    return getattr(state, "station_service", StationService(state))
