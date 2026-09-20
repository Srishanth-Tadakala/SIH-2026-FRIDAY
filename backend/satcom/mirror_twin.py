"""Mainland Mirror Digital Twin Replica Engine.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Mainland Headquarters (NCPOR Vasco da Gama, Goa / MoES New Delhi).

MAINLAND MIRROR TWIN:
Runs continuously at Mainland Command to mirror the Antarctic station twin state:
1. Consumes sparse, compressed satcom delta frames.
2. Reconstructs all 505 sensor channels in real-time.
3. Tracks sequence numbers, detects dropped packets, and triggers resync.
4. Computes SHA-256 state checksums to verify mathematical parity with the Antarctic twin.
5. Surfaces high-level KPIs, active alerts, and multi-agent deliberation briefings
   to mainland scientists, polar expedition directors, and engineers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Any

from .protocol import FrameType, SatcomFrame


@dataclass
class MirrorTwinMetrics:
    """Telemetry synchronization status of the Mainland Mirror Twin."""
    station_id: str
    sync_status: str                          # "SYNCHRONIZED", "AWAITING_KEYFRAME", "GAP_DETECTED"
    last_seq_num: int
    last_sim_time_seconds: float
    total_frames_received: int
    lost_frames_count: int
    resync_required: bool
    sensor_count: int
    state_checksum: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_id": self.station_id,
            "sync_status": self.sync_status,
            "last_seq_num": self.last_seq_num,
            "last_sim_time_seconds": round(self.last_sim_time_seconds, 2),
            "total_frames_received": self.total_frames_received,
            "lost_frames_count": self.lost_frames_count,
            "resync_required": self.resync_required,
            "sensor_count": self.sensor_count,
            "state_checksum": self.state_checksum,
        }


class MirrorTwinEngine:
    """Mainland digital twin replica maintaining synchronized station state over satcom."""

    def __init__(self, station_id: str = "bharati") -> None:
        self.station_id = station_id
        self._state: dict[str, Any] = {}
        self._kpis: dict[str, Any] = {}
        self._alerts: list[dict[str, Any]] = []
        self._deliberation_cards: list[dict[str, Any]] = []
        self._audit_trail: list[dict[str, Any]] = []

        self.last_seq_num: int = 0
        self.last_sim_time_seconds: float = 0.0
        self.last_timestamp_iso: str = ""
        self.sync_status: str = "AWAITING_KEYFRAME"
        self.resync_required: bool = True

        self.total_frames_received: int = 0
        self.lost_frames_count: int = 0

    def apply_frame(self, frame: SatcomFrame) -> tuple[bool, str]:
        """Process an incoming satcom frame and update the replica twin state.
        
        Returns:
            (accepted: bool, status_code: str)
        """
        if frame.station_id != self.station_id:
            return False, f"STATION_MISMATCH: Expected {self.station_id}, received {frame.station_id}"

        self.total_frames_received += 1

        # 1. Handle Full KEYFRAME
        if frame.frame_type == FrameType.KEYFRAME:
            self._state = dict(frame.payload)
            self.last_seq_num = frame.seq_num
            self.last_sim_time_seconds = frame.sim_time_seconds
            self.last_timestamp_iso = frame.timestamp_iso
            self._kpis = frame.kpis or {}
            self._alerts = frame.alerts or []
            self.sync_status = "SYNCHRONIZED"
            self.resync_required = False
            return True, "KEYFRAME_INITIALIZED"

        # 2. Handle Sparse DELTA
        if frame.frame_type == FrameType.DELTA:
            if self.sync_status == "AWAITING_KEYFRAME":
                self.resync_required = True
                return False, "REJECTED_AWAITING_KEYFRAME"

            # Check sequence continuity
            if frame.seq_num <= self.last_seq_num:
                # Duplicate or out-of-order frame
                return False, f"DUPLICATE_FRAME: Seq {frame.seq_num} <= {self.last_seq_num}"

            if frame.seq_num > (self.last_seq_num + 1):
                # Gap detected: frames were dropped by satcom channel
                lost = frame.seq_num - (self.last_seq_num + 1)
                self.lost_frames_count += lost
                self.sync_status = "GAP_DETECTED"
                self.resync_required = True

            # Apply delta channels to existing replica state
            self._state.update(frame.payload)
            self.last_seq_num = frame.seq_num
            self.last_sim_time_seconds = frame.sim_time_seconds
            self.last_timestamp_iso = frame.timestamp_iso
            if frame.kpis:
                self._kpis = frame.kpis
            if frame.alerts is not None:
                self._alerts = frame.alerts

            if not self.resync_required:
                self.sync_status = "SYNCHRONIZED"

            return True, "DELTA_APPLIED"

        # 3. Handle Urgent ALARM
        if frame.frame_type == FrameType.ALARM:
            alarm_data = frame.payload
            self._alerts.append(alarm_data)
            return True, "ALARM_REGISTERED"

        # 4. Handle Deliberation Briefing Card
        if frame.frame_type == FrameType.DELIBERATION_CARD:
            self._deliberation_cards.append(frame.payload)
            return True, "DELIBERATION_CARD_SAVED"

        # 5. Handle Commander Action / PIN Audit
        if frame.frame_type == FrameType.COMMAND_AUDIT:
            self._audit_trail.append(frame.payload)
            return True, "AUDIT_SAVED"

        # 6. Heartbeat Keepalive
        if frame.frame_type == FrameType.HEARTBEAT:
            self.last_timestamp_iso = frame.timestamp_iso
            return True, "HEARTBEAT_ACK"

        return False, f"UNKNOWN_FRAME_TYPE: {frame.frame_type}"

    def get_sensor_value(self, sensor_id: str) -> Any:
        """Lookup an individual sensor reading from the replica state in O(1) time."""
        if sensor_id not in self._state:
            raise KeyError(f"Sensor '{sensor_id}' not found in mainland mirror state for {self.station_id}")
        return self._state[sensor_id]

    def get_all_readings(self) -> dict[str, Any]:
        """Return the complete reconstructed state across all sensors."""
        return dict(self._state)

    def get_kpis(self) -> dict[str, Any]:
        """Return high-level KPIs."""
        return dict(self._kpis)

    def get_alerts(self) -> list[dict[str, Any]]:
        """Return active alerts."""
        return list(self._alerts)

    def get_deliberation_cards(self) -> list[dict[str, Any]]:
        """Return received multi-agent deliberation cards."""
        return list(self._deliberation_cards)

    def get_audit_trail(self) -> list[dict[str, Any]]:
        """Return received command audit trail."""
        return list(self._audit_trail)

    def is_synchronized(self) -> bool:
        """Check if replica twin is fully synchronized with no sequence gaps."""
        return self.sync_status == "SYNCHRONIZED" and not self.resync_required

    def get_state_checksum(self) -> str:
        """Compute deterministic SHA-256 hash of reconstructed state for parity verification."""
        if not self._state:
            return "0000000000000000000000000000000000000000000000000000000000000000"

        # Sort keys to ensure deterministic serialization
        normalized = {}
        for k in sorted(self._state.keys()):
            val = self._state[k]
            if isinstance(val, float):
                normalized[k] = round(val, 2)
            else:
                normalized[k] = val

        raw = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def create_resync_request(self) -> SatcomFrame:
        """Generate a RESYNC_REQUEST frame to demand a fresh KEYFRAME from Antarctica."""
        return SatcomFrame(
            frame_id=f"RESYNC-{self.station_id.upper()}-{int(time.time())}",
            station_id=self.station_id,
            frame_type=FrameType.RESYNC_REQUEST,
            seq_num=0,
            timestamp_iso="",
            sim_time_seconds=self.last_sim_time_seconds,
            payload={"last_known_seq": self.last_seq_num, "lost_frames": self.lost_frames_count},
            priority=0,  # Critical priority
        )

    def get_metrics(self) -> dict[str, Any]:
        """Return full mirror synchronization metrics."""
        m = MirrorTwinMetrics(
            station_id=self.station_id,
            sync_status=self.sync_status,
            last_seq_num=self.last_seq_num,
            last_sim_time_seconds=self.last_sim_time_seconds,
            total_frames_received=self.total_frames_received,
            lost_frames_count=self.lost_frames_count,
            resync_required=self.resync_required,
            sensor_count=len(self._state),
            state_checksum=self.get_state_checksum(),
        )
        return m.to_dict()
