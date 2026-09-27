"""Satcom & Polar Link Domain Service for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from typing import Any, Dict


class SatcomService:
    """Manages simulated satellite links, polar blackout transitions, and mirror twin states."""

    def __init__(self, server_state: Any) -> None:
        self.state = server_state

    def get_channel_status(self, station_id: str, channel_name: str = "telemetry") -> Dict[str, Any]:
        """Return operational profile and metrics for the specified satcom channel."""
        emulator = self.state.get_satcom_emulator(station_id, channel_name)
        if not emulator:
            raise KeyError(f"Satcom channel '{channel_name}' for station '{station_id}' not found.")
        return emulator.get_status()

    def set_channel_profile(self, station_id: str, profile_name: str, channel_name: str = "telemetry") -> Dict[str, Any]:
        """Update satcom connection profile (e.g. INMARSAT_BGAN, IRIDIUM_PILOT, BLACKOUT)."""
        return self.state.set_satcom_profile(station_id, profile_name, channel_name)

    def trigger_blackout(self, station_id: str, channel_name: str = "telemetry") -> Dict[str, Any]:
        """Simulate total satellite occlusion (0 kbps polar blackout)."""
        return self.set_channel_profile(station_id, "BLACKOUT", channel_name)

    def restore_nominal_link(self, station_id: str, channel_name: str = "telemetry") -> Dict[str, Any]:
        """Restore high-bandwidth satellite connection."""
        return self.set_channel_profile(station_id, "INMARSAT_BGAN_STANDARD", channel_name)

    def get_mirror_twin_status(self, station_id: str) -> Dict[str, Any]:
        """Return NCPOR Goa Mainland HQ mirror twin synchronization telemetry."""
        mirror = self.state.get_mirror_twin(station_id)
        if not mirror:
            raise KeyError(f"Mirror twin for station '{station_id}' not found.")
        return mirror.get_status()


def get_satcom_service() -> SatcomService:
    """FastAPI Dependency Injection provider for SatcomService."""
    from ..state import get_server_state
    state = get_server_state()
    return getattr(state, "satcom_service", SatcomService(state))
