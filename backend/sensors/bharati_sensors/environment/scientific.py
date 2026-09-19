"""Scientific environmental context (ionosphere, all-sky, seismology) observations.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.

SEMANTIC ROLE:
These sensors provide scientific environmental context rather than station equipment control.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_scientific_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate ionospheric, all-sky optical, and broadband seismology sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-IONO-TEC": lambda: state.ionosphere.total_electron_content_tecu,
        "ENV-IONO-L1-AMP": lambda: state.ionosphere.scintillation_s4,
        "ENV-IONO-L1-PHASE": lambda: state.ionosphere.phase_scintillation_rad,
        "ENV-IONO-STATUS": lambda: state.ionosphere.receiver_status,
        "ENV-SKY-CLOUD": lambda: state.sky.cloud_cover_percent,
        "ENV-SKY-AURORA": lambda: state.sky.auroral_intensity_kr,
        "ENV-SKY-IMAGE-STAT": lambda: state.sky.camera_status,
        "ENV-SEIS-ACC": lambda: state.seismic.ground_acceleration_um_s2,
        "ENV-SEIS-VEL": lambda: state.seismic.particle_velocity_um_s,
        "ENV-SEIS-EVENT": lambda: state.seismic.event_detected,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.SCIENTIFIC_CONTEXT:
            raise KeyError(f"Configuration missing or invalid domain for scientific sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
