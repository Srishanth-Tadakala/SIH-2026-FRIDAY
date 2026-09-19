"""Base sensor classes and technical failure injection for Bharati Infrastructure.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Callable

from ..energy.clock import SimulationClock
from .config import SOURCE_REFERENCE_DEFAULT, get_confidence_for_evidence
from .models import (
    FailureType,
    SensorConfig,
    SensorProvenance,
    SensorQuality,
    SensorReading,
    SensorValue,
)


class BaseInfrastructureSensor(ABC):
    """Abstract base class for all Bharati Infrastructure sensors."""

    def __init__(self, config: SensorConfig, clock: SimulationClock) -> None:
        self.config = config
        self.clock = clock
        
        # Failure injection state
        self._failure_type: FailureType | None = None
        self._failure_params: dict[str, Any] = {}
        self._frozen_value: SensorValue = None
        self._frozen_timestamp: str | None = None
        
        # Last produced reading
        self._last_reading: SensorReading | None = None

    @property
    def sensor_id(self) -> str:
        return self.config.sensor_id

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def asset_id(self) -> str:
        return self.config.asset_id

    @property
    def domain(self):
        return self.config.domain

    @property
    def kind(self):
        return self.config.kind

    @property
    def physical_quantity(self):
        return self.config.physical_quantity

    @property
    def subsystem(self) -> str:
        return self.config.subsystem

    @property
    def building_id(self) -> str:
        return self.config.building_id

    @property
    def zone_id(self) -> str:
        return self.config.zone_id

    def simulate_failure(self, failure_type: FailureType, **kwargs: Any) -> None:
        """Inject a simulated technical sensor fault.
        
        Supported fault modes:
        - DROPOUT: sensor value drops to None, quality = FAILED
        - STALE: sensor timestamp freezes beyond stale threshold, quality = STALE
        - OUT_OF_RANGE: sensor generates reading beyond min_value/max_value, quality = BAD
        - STUCK: sensor preserves its previous reading across steps, quality = BAD
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
        self._failure_type = None
        self._failure_params.clear()
        self._frozen_value = None
        self._frozen_timestamp = None

    @abstractmethod
    def _compute_raw_value(self) -> SensorValue:
        """Evaluate raw sensor value from physical state or mathematical derivation."""
        raise NotImplementedError

    def read(self, force: bool = False) -> SensorReading:
        """Produce a standardized SensorReading with hierarchy, provenance, and quality check."""
        current_iso = self.clock.isoformat()
        current_sim_time = self.clock.elapsed_seconds
        
        # 1. Handle Active Failure Injections
        if self._failure_type == FailureType.DROPOUT:
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                name=self.config.name,
                station_id=self.config.station_id,
                building_id=self.config.building_id,
                level_id=self.config.level_id,
                zone_id=self.config.zone_id,
                asset_id=self.config.asset_id,
                domain=self.config.domain,
                subsystem=self.config.subsystem,
                kind=self.config.kind,
                physical_quantity=self.config.physical_quantity,
                value=None,
                unit=self.config.unit,
                timestamp=current_iso,
                simulation_time_seconds=current_sim_time,
                event_time_seconds=None,
                provenance=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.FAILED,
                evidence_level=self.config.evidence_level,
                confidence=0.0,
                valid=False,
                min_valid=self.config.min_value,
                max_valid=self.config.max_value,
                stale_after_seconds=self.config.stale_after_seconds,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.STALE:
            timestamp = self._frozen_timestamp or (self.clock.now() - timedelta(seconds=self.config.stale_after_seconds * 2)).isoformat()
            raw_val = self._compute_raw_value()
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                name=self.config.name,
                station_id=self.config.station_id,
                building_id=self.config.building_id,
                level_id=self.config.level_id,
                zone_id=self.config.zone_id,
                asset_id=self.config.asset_id,
                domain=self.config.domain,
                subsystem=self.config.subsystem,
                kind=self.config.kind,
                physical_quantity=self.config.physical_quantity,
                value=raw_val,
                unit=self.config.unit,
                timestamp=timestamp,
                simulation_time_seconds=current_sim_time,
                event_time_seconds=None,
                provenance=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.STALE,
                evidence_level=self.config.evidence_level,
                confidence=0.4,
                valid=False,
                min_valid=self.config.min_value,
                max_valid=self.config.max_value,
                stale_after_seconds=self.config.stale_after_seconds,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.OUT_OF_RANGE:
            if self.config.max_value is not None:
                forced_val = round(self.config.max_value * 1.5, 2)
            elif self.config.min_value is not None:
                forced_val = round(self.config.min_value - 50.0, 2)
            else:
                forced_val = 99999.0
                
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                name=self.config.name,
                station_id=self.config.station_id,
                building_id=self.config.building_id,
                level_id=self.config.level_id,
                zone_id=self.config.zone_id,
                asset_id=self.config.asset_id,
                domain=self.config.domain,
                subsystem=self.config.subsystem,
                kind=self.config.kind,
                physical_quantity=self.config.physical_quantity,
                value=forced_val,
                unit=self.config.unit,
                timestamp=current_iso,
                simulation_time_seconds=current_sim_time,
                event_time_seconds=None,
                provenance=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.BAD,
                evidence_level=self.config.evidence_level,
                confidence=0.2,
                valid=False,
                min_valid=self.config.min_value,
                max_valid=self.config.max_value,
                stale_after_seconds=self.config.stale_after_seconds,
            )
            self._last_reading = reading
            return reading

        elif self._failure_type == FailureType.STUCK:
            frozen_val = self._frozen_value if self._frozen_value is not None else self.config.default_value
            reading = SensorReading(
                sensor_id=self.config.sensor_id,
                name=self.config.name,
                station_id=self.config.station_id,
                building_id=self.config.building_id,
                level_id=self.config.level_id,
                zone_id=self.config.zone_id,
                asset_id=self.config.asset_id,
                domain=self.config.domain,
                subsystem=self.config.subsystem,
                kind=self.config.kind,
                physical_quantity=self.config.physical_quantity,
                value=frozen_val,
                unit=self.config.unit,
                timestamp=current_iso,
                simulation_time_seconds=current_sim_time,
                event_time_seconds=None,
                provenance=SensorProvenance.SIMULATED,
                source_reference=SOURCE_REFERENCE_DEFAULT,
                quality=SensorQuality.BAD,
                evidence_level=self.config.evidence_level,
                confidence=0.5,
                valid=False,
                min_valid=self.config.min_value,
                max_valid=self.config.max_value,
                stale_after_seconds=self.config.stale_after_seconds,
            )
            self._last_reading = reading
            return reading

        # 2. Normal Read with Validation
        raw_val = self._compute_raw_value()
        quality, valid = self._validate_quality(raw_val)
        confidence = get_confidence_for_evidence(self.config.evidence_level) if valid else 0.3
        
        reading = SensorReading(
            sensor_id=self.config.sensor_id,
            name=self.config.name,
            station_id=self.config.station_id,
            building_id=self.config.building_id,
            level_id=self.config.level_id,
            zone_id=self.config.zone_id,
            asset_id=self.config.asset_id,
            domain=self.config.domain,
            subsystem=self.config.subsystem,
            kind=self.config.kind,
            physical_quantity=self.config.physical_quantity,
            value=raw_val,
            unit=self.config.unit,
            timestamp=current_iso,
            simulation_time_seconds=current_sim_time,
            event_time_seconds=None,
            provenance=SensorProvenance.SIMULATED,
            source_reference=SOURCE_REFERENCE_DEFAULT,
            quality=quality,
            evidence_level=self.config.evidence_level,
            confidence=confidence,
            valid=valid,
            min_valid=self.config.min_value,
            max_valid=self.config.max_value,
            stale_after_seconds=self.config.stale_after_seconds,
        )
        self._last_reading = reading
        return reading

    def _validate_quality(self, val: SensorValue) -> tuple[SensorQuality, bool]:
        """Perform boundary inspection against configured physical limits."""
        if val is None:
            return SensorQuality.FAILED, False
            
        if isinstance(val, (int, float)):
            if self.config.min_value is not None and val < self.config.min_value:
                return SensorQuality.BAD, False
            if self.config.max_value is not None and val > self.config.max_value:
                return SensorQuality.BAD, False
                
        return SensorQuality.GOOD, True


class StateBoundInfrastructureSensor(BaseInfrastructureSensor):
    """Sensor that observes a specific attribute or callable from physical state."""

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


class DerivedInfrastructureSensor(BaseInfrastructureSensor):
    """Sensor that evaluates a mathematical calculation from other states/sensors."""

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
