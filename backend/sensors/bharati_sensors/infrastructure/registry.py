"""Infrastructure Sensor Registry for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

The registry is exclusively a sensor-management and telemetry readout mechanism.
It contains NO agent reasoning, NO diagnosis, and NO control decision logic.
"""

from __future__ import annotations

from typing import Any

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor
from .models import (
    FailureType,
    InfrastructureDomain,
    SensorKind,
    SensorReading,
)
from .physics_state import BharatiInfrastructurePhysicsState


class InfrastructureSensorRegistry:
    """Central registry and readout coordinator for Bharati Infrastructure sensors."""

    def __init__(
        self,
        physics: BharatiInfrastructurePhysicsState,
        clock: SimulationClock,
    ) -> None:
        self.physics = physics
        self.clock = clock
        self._sensors: dict[str, BaseInfrastructureSensor] = {}
        self._latest_readings: dict[str, SensorReading] = {}

    @property
    def sensor_count(self) -> int:
        """Return the total number of registered sensors."""
        return len(self._sensors)

    def register(self, sensor: BaseInfrastructureSensor) -> None:
        """Register a sensor in the infrastructure registry."""
        if sensor.sensor_id in self._sensors:
            raise ValueError(f"Sensor with ID '{sensor.sensor_id}' already registered.")
        self._sensors[sensor.sensor_id] = sensor

    def get_sensor(self, sensor_id: str) -> BaseInfrastructureSensor:
        """Retrieve a registered sensor by its unique sensor_id."""
        if sensor_id not in self._sensors:
            raise KeyError(f"Sensor '{sensor_id}' not found in registry.")
        return self._sensors[sensor_id]

    def get_all_sensors(self) -> list[BaseInfrastructureSensor]:
        """Return a list of all registered sensors."""
        return list(self._sensors.values())

    def get_sensors_by_domain(self, domain: InfrastructureDomain | str) -> list[BaseInfrastructureSensor]:
        """Retrieve all sensors belonging to a specific domain."""
        dom_val = domain.value if isinstance(domain, InfrastructureDomain) else str(domain)
        return [s for s in self._sensors.values() if s.domain.value == dom_val]

    def get_sensors_by_subsystem(self, subsystem: str) -> list[BaseInfrastructureSensor]:
        """Retrieve all sensors belonging to a specific subsystem."""
        return [s for s in self._sensors.values() if s.subsystem == subsystem]

    def get_sensors_by_asset(self, asset_id: str) -> list[BaseInfrastructureSensor]:
        """Retrieve all sensors monitoring a specific asset (e.g. 'AHU-01', 'RO-01')."""
        return [s for s in self._sensors.values() if s.asset_id == asset_id]

    def get_sensors_by_kind(self, kind: SensorKind | str) -> list[BaseInfrastructureSensor]:
        """Retrieve all sensors of a specific kind (INSTRUMENT, STATE, DERIVED)."""
        kind_val = kind.value if isinstance(kind, SensorKind) else str(kind)
        return [s for s in self._sensors.values() if s.kind.value == kind_val]

    def read_sensor(self, sensor_id: str, force: bool = False) -> SensorReading:
        """Read an individual sensor, returning a standard SensorReading."""
        sensor = self.get_sensor(sensor_id)
        reading = sensor.read(force=force)
        self._latest_readings[sensor_id] = reading
        return reading

    def read_all(self, force: bool = False) -> dict[str, SensorReading]:
        """Read all registered sensors and return a dictionary mapping sensor_id to SensorReading."""
        readings: dict[str, SensorReading] = {}
        for sensor_id, sensor in self._sensors.items():
            reading = sensor.read(force=force)
            readings[sensor_id] = reading
            self._latest_readings[sensor_id] = reading
        return readings

    def get_latest_state(self) -> dict[str, SensorReading]:
        """Get cached latest readings from the most recent read cycle."""
        if not self._latest_readings:
            return self.read_all()
        return dict(self._latest_readings)

    def step(self, dt_seconds: float = 60.0) -> None:
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
