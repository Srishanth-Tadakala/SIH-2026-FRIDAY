"""Polar Satcom Channel Emulator.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica.

SIMULATES REAL-WORLD POLAR SATELLITE CHANNELS:
1. LAN Direct: Fast local link in Antarctic station control room.
2. Inmarsat BGAN: 64 kbps nominal satcom link with ~850ms GEO round-trip latency.
3. Iridium SBD: 9.6 kbps low-bandwidth polar orbit link with ~1500ms latency.
4. Polar Blackout: 0 kbps complete severed link during solar storms / antenna icing.

Automatically coordinates with PrioritizedSpoolQueue to spool telemetry during
blackouts and drains upon link recovery in strict priority order.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import random
import time
from typing import Any

from .protocol import CompressedSerializer, FrameType, SatcomFrame
from .store_and_forward import PrioritizedSpoolQueue


class SatcomChannelProfile(str, Enum):
    """Realistic polar communication channel profiles."""
    LAN_DIRECT = "LAN_DIRECT"                 # 100 Mbps, 0ms, 0% loss (Control Room LAN)
    INMARSAT_STANDARD = "INMARSAT_STANDARD"   # 64 kbps, 850ms RTT, 2% loss (Primary Inmarsat BGAN)
    IRIDIUM_LOW = "IRIDIUM_LOW"               # 9.6 kbps, 1500ms RTT, 8% loss (Backup Polar LEO)
    POLAR_BLACKOUT = "POLAR_BLACKOUT"         # 0 kbps, inf latency, 100% loss (Solar storm / icing)


@dataclass(frozen=True)
class ChannelParameters:
    """Physical characteristics of a polar satellite link."""
    name: str
    bandwidth_bps: int
    latency_ms: float
    packet_loss_rate: float
    description: str


CHANNEL_PROFILES: dict[SatcomChannelProfile, ChannelParameters] = {
    SatcomChannelProfile.LAN_DIRECT: ChannelParameters(
        name="Antarctic Local Station LAN",
        bandwidth_bps=100_000_000,
        latency_ms=0.0,
        packet_loss_rate=0.0,
        description="Local Ethernet inside Station Operations Center (0 latency, full speed)",
    ),
    SatcomChannelProfile.INMARSAT_STANDARD: ChannelParameters(
        name="Inmarsat BGAN Primary Uplink",
        bandwidth_bps=64_000,
        latency_ms=850.0,
        packet_loss_rate=0.02,
        description="Standard 64 kbps geostationary satellite link to Mainland India",
    ),
    SatcomChannelProfile.IRIDIUM_LOW: ChannelParameters(
        name="Iridium Polar LEO Backup Link",
        bandwidth_bps=9_600,
        latency_ms=1500.0,
        packet_loss_rate=0.08,
        description="Constrained 9.6 kbps polar LEO satellite link during high antenna motion",
    ),
    SatcomChannelProfile.POLAR_BLACKOUT: ChannelParameters(
        name="Polar Magnetic Storm Blackout",
        bandwidth_bps=0,
        latency_ms=float("inf"),
        packet_loss_rate=1.0,
        description="Total radio and satellite link severance (100% loss, local spooling only)",
    ),
}


class PolarSatcomChannelEmulator:
    """Emulates bandwidth, latency, packet loss, and blackout spooling for polar links."""

    def __init__(
        self,
        profile: SatcomChannelProfile | str = SatcomChannelProfile.INMARSAT_STANDARD,
        spool_queue: PrioritizedSpoolQueue | None = None,
        deterministic: bool = False,
    ) -> None:
        self.profile = (
            SatcomChannelProfile(profile) if isinstance(profile, str) else profile
        )
        self.spool_queue = spool_queue if spool_queue is not None else PrioritizedSpoolQueue()
        self.deterministic = deterministic
        self.force_drop_next = False

        # Live Metrics
        self.total_transmitted_bytes = 0
        self.total_raw_equivalent_bytes = 0
        self.packets_transmitted = 0
        self.packets_spooled = 0
        self.packets_lost = 0

    @property
    def params(self) -> ChannelParameters:
        return CHANNEL_PROFILES[self.profile]

    def set_profile(self, profile: SatcomChannelProfile | str) -> None:
        """Switch operational satellite link profile."""
        self.profile = SatcomChannelProfile(profile) if isinstance(profile, str) else profile

    def transmit(self, frame: SatcomFrame) -> tuple[bool, str, float, bytes]:
        """Attempt to transmit a SatcomFrame across the emulated satellite channel.
        
        Returns:
            (success: bool, status: str, transmission_delay_seconds: float, serialized_bytes: bytes)
        """
        serialized = CompressedSerializer.serialize(frame, compress=True)
        raw_eq_len = len(json.dumps(frame.to_dict()).encode("utf-8"))

        # 1. Check for complete blackout
        if self.profile == SatcomChannelProfile.POLAR_BLACKOUT:
            self.spool_queue.enqueue(frame)
            self.packets_spooled += 1
            return False, "SPOOLED_BLACKOUT", float("inf"), serialized

        # 2. Check for forced or statistical packet loss
        if self.force_drop_next or (
            not self.deterministic and random.random() < self.params.packet_loss_rate
        ):
            self.force_drop_next = False
            self.packets_lost += 1
            return False, "PACKET_LOSS_SATCOM", round(self.params.latency_ms / 1000.0, 3), serialized

        # 3. Successful transmission
        payload_bits = len(serialized) * 8
        serialization_delay = payload_bits / max(self.params.bandwidth_bps, 1)
        propagation_delay = self.params.latency_ms / 1000.0
        total_delay = serialization_delay + propagation_delay

        self.total_transmitted_bytes += len(serialized)
        self.total_raw_equivalent_bytes += raw_eq_len
        self.packets_transmitted += 1

        return True, "TRANSMITTED", round(total_delay, 4), serialized

    def recover_from_blackout(
        self,
        new_profile: SatcomChannelProfile | str = SatcomChannelProfile.INMARSAT_STANDARD,
        max_drain: int | None = None,
    ) -> list[tuple[SatcomFrame, bytes, float]]:
        """Restore satellite link and transmit spooled frames in strict priority order.
        
        Returns list of (frame, serialized_bytes, transmission_delay) for all drained frames.
        """
        self.set_profile(new_profile)
        drained_frames = self.spool_queue.drain(max_frames=max_drain)
        results: list[tuple[SatcomFrame, bytes, float]] = []

        for frame in drained_frames:
            success, status, delay, s_bytes = self.transmit(frame)
            if success:
                results.append((frame, s_bytes, delay))

        return results

    def get_channel_metrics(self) -> dict[str, Any]:
        """Aggregate satcom channel performance and bandwidth optimization telemetry."""
        raw_total = max(self.total_raw_equivalent_bytes, 1)
        saved_bytes = max(0, self.total_raw_equivalent_bytes - self.total_transmitted_bytes)
        ratio = self.total_transmitted_bytes / raw_total
        saved_pct = (1.0 - ratio) * 100.0

        return {
            "current_profile": self.profile.value,
            "profile_name": self.params.name,
            "bandwidth_bps": self.params.bandwidth_bps,
            "latency_ms": self.params.latency_ms,
            "packet_loss_rate": self.params.packet_loss_rate,
            "packets_transmitted": self.packets_transmitted,
            "packets_spooled": self.packets_spooled,
            "packets_lost": self.packets_lost,
            "spool_queue_depth": self.spool_queue.qsize(),
            "spool_queue_stats": self.spool_queue.get_stats(),
            "total_transmitted_bytes": self.total_transmitted_bytes,
            "raw_equivalent_bytes": self.total_raw_equivalent_bytes,
            "bandwidth_saved_bytes": saved_bytes,
            "compression_ratio": round(ratio, 4),
            "bandwidth_saved_pct": round(saved_pct, 2),
        }
