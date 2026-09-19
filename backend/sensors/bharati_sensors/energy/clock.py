"""Simulation clock abstraction for reproducible time progression.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta


class SimulationClock:
    """Lightweight simulation clock providing deterministic ISO-8601 timestamps.
    
    Allows sensor readings and physics state to advance predictably in simulated time.
    """

    def __init__(self, initial_time: datetime | None = None) -> None:
        if initial_time is None:
            self._current_time = datetime(2026, 9, 19, 0, 0, 0, tzinfo=timezone.utc)
        else:
            if initial_time.tzinfo is None:
                self._current_time = initial_time.replace(tzinfo=timezone.utc)
            else:
                self._current_time = initial_time
        self._initial_time = self._current_time

    def now(self) -> datetime:
        """Get current simulation datetime."""
        return self._current_time

    def isoformat(self) -> str:
        """Get current timestamp in ISO-8601 UTC format."""
        return self._current_time.isoformat()

    def advance(self, seconds: float) -> datetime:
        """Advance the simulation clock by the given number of seconds."""
        if seconds < 0:
            raise ValueError(f"Cannot advance clock by negative seconds: {seconds}")
        self._current_time += timedelta(seconds=seconds)
        return self._current_time

    def set_time(self, dt: datetime) -> None:
        """Explicitly set the simulation time."""
        if dt.tzinfo is None:
            self._current_time = dt.replace(tzinfo=timezone.utc)
        else:
            self._current_time = dt

    @property
    def elapsed_seconds(self) -> float:
        """Total elapsed seconds since simulation start."""
        return (self._current_time - self._initial_time).total_seconds()
