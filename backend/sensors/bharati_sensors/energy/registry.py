"""Sensor Registry for Bharati Station Energy System.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

The registry is exclusively a sensor-management and telemetry readout mechanism.
It contains NO agent reasoning, NO diagnosis, and NO control decision logic.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSensor
from .clock import SimulationClock
from .models import (
    FailureType,
    SensorCategory,
    SensorKind,
    SensorReading,
)
from .physics_state import BharatiEnergyPhysicsState


class SensorRegistry:
    """Central registry and readout coordinator for Bharati Energy sensors."""

    def __init__(
        self,
        physics: BharatiEnergyPhysicsState,
        clock: SimulationClock,
    ) -> None:
        self.physics = physics
        self.clock = clock
        self._sensors: dict[str, BaseSensor] = {}
        self._latest_readings: dict[str, SensorReading] = {}

    def register(self, sensor: BaseSensor) -> None:
        """Register a sensor in the registry."""
        if sensor.sensor_id in self._sensors:
            raise ValueError(f"Sensor with ID '{sensor.sensor_id}' already registered.")
        self._sensors[sensor.sensor_id] = sensor

    def get_sensor(self, sensor_id: str) -> BaseSensor:
        """Retrieve a registered sensor by its unique sensor_id."""
        if sensor_id not in self._sensors:
            raise KeyError(f"Sensor '{sensor_id}' not found in registry.")
        return self._sensors[sensor_id]

    def get_all_sensors(self) -> list[BaseSensor]:
        """Return a list of all registered sensors."""
        return list(self._sensors.values())

    def get_sensors_by_asset(self, asset: str) -> list[BaseSensor]:
        """Retrieve all sensors monitoring a specific asset (e.g. 'CHP-1', 'UPS-2')."""
        return [s for s in self._sensors.values() if s.asset == asset]

    def get_sensors_by_category(self, category: SensorCategory | str) -> list[BaseSensor]:
        """Retrieve all sensors belonging to a specific category (e.g. CHP, UPS, FUEL)."""
        cat_val = category.value if isinstance(category, SensorCategory) else str(category)
        return [s for s in self._sensors.values() if s.category.value == cat_val]

    def get_sensors_by_kind(self, kind: SensorKind | str) -> list[BaseSensor]:
        """Retrieve all sensors of a specific kind (INSTRUMENT, STATE, DERIVED)."""
        kind_val = kind.value if isinstance(kind, SensorKind) else str(kind)
        return [s for s in self._sensors.values() if s.kind.value == kind_val]

    def read_sensor(self, sensor_id: str) -> SensorReading:
        """Read an individual sensor, returning a standard SensorReading."""
        sensor = self.get_sensor(sensor_id)
        reading = sensor.read()
        self._latest_readings[sensor_id] = reading
        return reading

    def read_all(self) -> dict[str, SensorReading]:
        """Read all registered sensors and return a dictionary mapping sensor_id to SensorReading."""
        readings: dict[str, SensorReading] = {}
        for sensor_id, sensor in self._sensors.items():
            reading = sensor.read()
            readings[sensor_id] = reading
            self._latest_readings[sensor_id] = reading
        return readings

    def get_latest_state(self) -> dict[str, SensorReading]:
        """Get the cached latest readings from the most recent read cycle."""
        if not self._latest_readings:
            return self.read_all()
        return dict(self._latest_readings)

    def step(self, dt_seconds: float = 1.0) -> None:
        """Advance the underlying physics simulation state and clock."""
        self.clock.advance(dt_seconds)
        self.physics.step(dt_seconds)
        # Update latest readings after physical state progression
        self.read_all()

    def simulate_failure(
        self,
        sensor_id: str,
        failure_type: FailureType | str,
        **kwargs: Any,
    ) -> None:
        """Inject a simulated sensor fault into a specific sensor."""
        sensor = self.get_sensor(sensor_id)
        ft = FailureType(failure_type) if isinstance(failure_type, str) else failure_type
        sensor.simulate_failure(ft, **kwargs)

    def clear_failure(self, sensor_id: str) -> None:
        """Clear simulated faults from a specific sensor."""
        sensor = self.get_sensor(sensor_id)
        sensor.clear_failure()

    def clear_all_failures(self) -> None:
        """Clear simulated faults from all registered sensors."""
        for sensor in self._sensors.values():
            sensor.clear_failure()
