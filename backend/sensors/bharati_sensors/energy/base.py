"""Base sensor abstractions and failure simulation mechanisms.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Callable

from .clock import SimulationClock
from .config import SOURCE_REFERENCE_DEFAULT
from .models import (
    FailureType,
    SensorConfig,
    SensorProvenance,
    SensorQuality,
    SensorReading,
    SensorValue,
)


class BaseSensor(ABC):
    """Abstract base class for all Bharati Energy sensors.
    
    Manages reading generation, failure injection, staleness tracking,
    and quality validation.
    """

    def __init__(self, config: SensorConfig, clock: SimulationClock) -> None:
        self.config = config
        self.clock = clock
        
        # Failure injection state
        self._failure_type: FailureType = FailureType.NONE
        self._failure_params: dict[str, Any] = {}
        self._frozen_value: SensorValue = None
        self._frozen_timestamp: str | None = None
        
        # Last produced reading
        self._last_reading: SensorReading | None = None

    @property
    def sensor_id(self) -> str:
        return self.config.sensor_id

    @property
    def asset(self) -> str:
        return self.config.asset

    @property
    def category(self):
        return self.config.category

    @property
    def kind(self):
        return self.config.kind

    @property
    def parameter(self) -> str:
        return self.config.parameter

    def simulate_failure(self, failure_type: FailureType, **kwargs: Any) -> None:
        """Inject a simulated technical sensor fault.
        
        Supported faults:
        - DROPOUT: sensor returns None, quality FAILED
        - STALE: sensor returns old timestamp beyond stale threshold, quality STALE
        - OUT_OF_RANGE: sensor generates reading beyond min_valid/max_valid, quality BAD
        - STUCK: sensor preserves previous reading and freezes value, quality BAD
        """
        self._failure_type = failure_type
        self._failure_params = kwargs
        
        if failure_type == FailureType.STUCK:
            # Preserve the previous reading value if available, else default config value
            if self._last_reading is not None and self._last_reading.value is not None:
                self._frozen_value = self._last_reading.value
            else:
                self._frozen_value = self.config.default_value
        elif failure_type == FailureType.STALE:
            stale_delta = kwargs.get("stale_seconds", self.config.stale_after_seconds * 2.0)
            stale_dt = self.clock.now() - timedelta(seconds=stale_delta)
            self._frozen_timestamp = stale_dt.isoformat()

    def clear_failure(self) -> None:
        """Clear any injected simulated sensor fault."""
        self._failure_type = FailureType.NONE
        self._failure_params.clear()
        self._frozen_value = None
        self._frozen_timestamp = None

    @abstractmethod
    def _compute_raw_value(self) -> SensorValue:
        """Evaluate raw sensor value from physics state or calculation."""
        raise NotImplementedError

    def read(self) -> SensorReading:
        """Produce a standardized SensorReading with provenance and quality inspection."""
        current_iso = self.clock.isoformat()
        
        # 1. Handle active failure injection
        if self._failure_type == FailureType.DROPOUT:
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                station=self.config.station,
                domain=self.config.domain,
                asset=self.config.asset,
                category=self.config.category,
                kind=self.config.kind,
                parameter=self.config.parameter,
                value=None,
                unit=self.config.unit,
                timestamp=current_iso,
                source=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.FAILED,
                confidence=0.0,
                valid=False,
                min_valid=self.config.min_valid,
                max_valid=self.config.max_valid,
                stale_after_seconds=self.config.stale_after_seconds,
                sensor_type=self.config.sensor_type,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.STALE:
            timestamp = self._frozen_timestamp or (self.clock.now() - timedelta(seconds=self.config.stale_after_seconds * 2)).isoformat()
            raw_val = self._compute_raw_value()
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                station=self.config.station,
                domain=self.config.domain,
                asset=self.config.asset,
                category=self.config.category,
                kind=self.config.kind,
                parameter=self.config.parameter,
                value=raw_val,
                unit=self.config.unit,
                timestamp=timestamp,
                source=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.STALE,
                confidence=0.4,
                valid=False,
                min_valid=self.config.min_valid,
                max_valid=self.config.max_valid,
                stale_after_seconds=self.config.stale_after_seconds,
                sensor_type=self.config.sensor_type,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.OUT_OF_RANGE:
            # Force value outside valid thresholds
            if self.config.max_valid is not None:
                forced_val = round(self.config.max_valid * 1.6, 2)
            elif self.config.min_valid is not None:
                forced_val = round(self.config.min_valid - 50.0, 2)
            else:
                forced_val = 99999.0
                
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                station=self.config.station,
                domain=self.config.domain,
                asset=self.config.asset,
                category=self.config.category,
                kind=self.config.kind,
                parameter=self.config.parameter,
                value=forced_val,
                unit=self.config.unit,
                timestamp=current_iso,
                source=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.BAD,
                confidence=0.2,
                valid=False,
                min_valid=self.config.min_valid,
                max_valid=self.config.max_valid,
                stale_after_seconds=self.config.stale_after_seconds,
                sensor_type=self.config.sensor_type,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.STUCK:
            # Value frozen at previously observed value
            frozen_val = self._frozen_value if self._frozen_value is not None else self.config.default_value
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                station=self.config.station,
                domain=self.config.domain,
                asset=self.config.asset,
                category=self.config.category,
                kind=self.config.kind,
                parameter=self.config.parameter,
                value=frozen_val,
                unit=self.config.unit,
                timestamp=current_iso,
                source=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.BAD,
                confidence=0.5,
                valid=False,
                min_valid=self.config.min_valid,
                max_valid=self.config.max_valid,
                stale_after_seconds=self.config.stale_after_seconds,
                sensor_type=self.config.sensor_type,
            )
            self._last_reading = reading
            return reading

        # 2. Normal sensor read with automatic quality validation
        raw_val = self._compute_raw_value()
        quality, valid, confidence = self._evaluate_quality(raw_val)
        
        reading = SensorReading(
            sensor_id=self.config.sensor_id,
            station=self.config.station,
            domain=self.config.domain,
            asset=self.config.asset,
            category=self.config.category,
            kind=self.config.kind,
            parameter=self.config.parameter,
            value=raw_val,
            unit=self.config.unit,
            timestamp=current_iso,
            source=SensorProvenance.SIMULATED,
            source_reference=SOURCE_REFERENCE_DEFAULT,
            quality=quality,
            confidence=confidence,
            valid=valid,
            min_valid=self.config.min_valid,
            max_valid=self.config.max_valid,
            stale_after_seconds=self.config.stale_after_seconds,
            sensor_type=self.config.sensor_type,
        )
        self._last_reading = reading
        return reading

    def _evaluate_quality(self, val: SensorValue) -> tuple[SensorQuality, bool, float]:
        """Check technical range bounds and value integrity."""
        if val is None:
            return SensorQuality.FAILED, False, 0.0
            
        if isinstance(val, (int, float)):
            if self.config.min_valid is not None and val < self.config.min_valid:
                return SensorQuality.BAD, False, 0.3
            if self.config.max_valid is not None and val > self.config.max_valid:
                return SensorQuality.BAD, False, 0.3
                
        return SensorQuality.GOOD, True, 1.0


class StateBoundSensor(BaseSensor):
    """Sensor that observes a specific attribute or callable on a state object."""

    def __init__(
        self,
        config: SensorConfig,
        clock: SimulationClock,
        getter: Callable[[], SensorValue],
    ) -> None:
        super().__init__(config, clock)
        self._getter = getter

    def _compute_raw_value(self) -> SensorValue:
        return self._getter()


class DerivedSensor(BaseSensor):
    """Sensor that computes its value mathematically from other sensors or state values."""

    def __init__(
        self,
        config: SensorConfig,
        clock: SimulationClock,
        calculator: Callable[[], SensorValue],
    ) -> None:
        super().__init__(config, clock)
        self._calculator = calculator

    def _compute_raw_value(self) -> SensorValue:
        return self._calculator()
