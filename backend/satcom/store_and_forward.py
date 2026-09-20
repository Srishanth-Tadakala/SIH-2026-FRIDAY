"""Polar Satcom Store-and-Forward Prioritized Spooling Queue.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica.

POLAR BLACKOUT RESILIENCE:
High-latitude Antarctic satellite links suffer periodic disruptions:
1. Geomagnetic substorms / Solar coronal mass ejections (polar ionospheric absorption).
2. Katabatic blizzard icing / Snow drifts covering satellite radomes.
3. Satellite orbit transit gaps (low elevation look angles <10°).

During blackouts, stations must spool data into prioritized memory buffers:
- Priority 0 (CRITICAL / ALARM): Emergency trips, fire alarms, PIN authorizations. NEVER dropped.
- Priority 1 (DELIBERATION / SYNTHESIS): Multi-agent briefing cards, recovery plans. High retention.
- Priority 2 (TELEMETRY / METRICS): Routine sensor deltas. Bounded queue with oldest-frame eviction.

When link connectivity is restored, the buffer drains in strict priority order,
guaranteeing mainland operators at NCPOR Goa receive life-safety alerts before bulk telemetry.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Any

from .protocol import FrameType, SatcomFrame


# Standard Priority Class Constants
PRIORITY_CRITICAL = 0      # Emergency life-safety alarms, generator trips, PIN audits
PRIORITY_DELIBERATION = 1  # Multi-agent deliberation cards, action proposals
PRIORITY_TELEMETRY = 2     # Routine sensor delta frames, periodic snapshots


@dataclass
class QueueMetrics:
    """Live statistics for the store-and-forward spooler."""
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_dropped: int = 0
    critical_count: int = 0
    deliberation_count: int = 0
    telemetry_count: int = 0
    oldest_enqueued_timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_enqueued": self.total_enqueued,
            "total_dequeued": self.total_dequeued,
            "total_dropped": self.total_dropped,
            "current_queue_depth": self.critical_count + self.deliberation_count + self.telemetry_count,
            "priority_breakdown": {
                "critical": self.critical_count,
                "deliberation": self.deliberation_count,
                "telemetry": self.telemetry_count,
            },
            "oldest_timestamp": self.oldest_enqueued_timestamp,
        }


class PrioritizedSpoolQueue:
    """Multi-level prioritized ring buffer for Antarctic store-and-forward telemetry."""

    def __init__(
        self,
        max_critical_capacity: int = 1000,
        max_deliberation_capacity: int = 500,
        max_telemetry_capacity: int = 2000,
    ) -> None:
        self.max_critical = max_critical_capacity
        self.max_deliberation = max_deliberation_capacity
        self.max_telemetry = max_telemetry_capacity

        # Dedicated FIFO queues for each priority class to guarantee O(1) ops and perfect ordering
        self._critical_queue: deque[SatcomFrame] = deque()
        self._deliberation_queue: deque[SatcomFrame] = deque()
        self._telemetry_queue: deque[SatcomFrame] = deque()

        self._total_enqueued = 0
        self._total_dequeued = 0
        self._total_dropped = 0

    def enqueue(self, frame: SatcomFrame) -> bool:
        """Enqueue a frame based on its designated priority class."""
        priority = frame.priority

        if priority <= PRIORITY_CRITICAL:
            # Critical queue (Alarms, PIN audits): Never dropped unless hard capacity reached
            if len(self._critical_queue) >= self.max_critical:
                # Emergency overflow: drop oldest critical to avoid OOM
                self._critical_queue.popleft()
                self._total_dropped += 1
            self._critical_queue.append(frame)

        elif priority == PRIORITY_DELIBERATION:
            # Deliberation queue (Multi-agent briefings, proposals)
            if len(self._deliberation_queue) >= self.max_deliberation:
                self._deliberation_queue.popleft()
                self._total_dropped += 1
            self._deliberation_queue.append(frame)

        else:
            # Routine telemetry (Delta frames, periodic snapshots)
            if len(self._telemetry_queue) >= self.max_telemetry:
                # Evict oldest telemetry frame to preserve link capacity
                self._telemetry_queue.popleft()
                self._total_dropped += 1
            self._telemetry_queue.append(frame)

        self._total_enqueued += 1
        return True

    def dequeue(self) -> SatcomFrame | None:
        """Dequeue the highest-priority frame available in O(1) time."""
        # 1. Check Priority 0 (Critical)
        if self._critical_queue:
            self._total_dequeued += 1
            return self._critical_queue.popleft()

        # 2. Check Priority 1 (Deliberation)
        if self._deliberation_queue:
            self._total_dequeued += 1
            return self._deliberation_queue.popleft()

        # 3. Check Priority 2 (Telemetry)
        if self._telemetry_queue:
            self._total_dequeued += 1
            return self._telemetry_queue.popleft()

        return None

    def peek(self) -> SatcomFrame | None:
        """Inspect the next highest-priority frame without removing it."""
        if self._critical_queue:
            return self._critical_queue[0]
        if self._deliberation_queue:
            return self._deliberation_queue[0]
        if self._telemetry_queue:
            return self._telemetry_queue[0]
        return None

    def drain(self, max_frames: int | None = None) -> list[SatcomFrame]:
        """Drain up to max_frames in strict priority order (used upon link restoration)."""
        drained: list[SatcomFrame] = []
        limit = max_frames if max_frames is not None else (
            len(self._critical_queue) + len(self._deliberation_queue) + len(self._telemetry_queue)
        )

        while limit > 0:
            frame = self.dequeue()
            if frame is None:
                break
            drained.append(frame)
            limit -= 1

        return drained

    def qsize(self) -> int:
        """Total number of frames pending in the buffer."""
        return len(self._critical_queue) + len(self._deliberation_queue) + len(self._telemetry_queue)

    def qsize_by_priority(self) -> dict[int, int]:
        """Count of frames grouped by priority."""
        return {
            PRIORITY_CRITICAL: len(self._critical_queue),
            PRIORITY_DELIBERATION: len(self._deliberation_queue),
            PRIORITY_TELEMETRY: len(self._telemetry_queue),
        }

    def is_empty(self) -> bool:
        """Check if all priority queues are empty."""
        return self.qsize() == 0

    def get_stats(self) -> dict[str, Any]:
        """Return comprehensive buffer statistics."""
        oldest_ts = None
        for q in [self._critical_queue, self._deliberation_queue, self._telemetry_queue]:
            if q and (oldest_ts is None or q[0].sim_time_seconds < oldest_ts):
                oldest_ts = q[0].sim_time_seconds

        metrics = QueueMetrics(
            total_enqueued=self._total_enqueued,
            total_dequeued=self._total_dequeued,
            total_dropped=self._total_dropped,
            critical_count=len(self._critical_queue),
            deliberation_count=len(self._deliberation_queue),
            telemetry_count=len(self._telemetry_queue),
            oldest_enqueued_timestamp=oldest_ts,
        )
        return metrics.to_dict()

    def clear(self) -> None:
        """Flush all pending buffers."""
        self._critical_queue.clear()
        self._deliberation_queue.clear()
        self._telemetry_queue.clear()
