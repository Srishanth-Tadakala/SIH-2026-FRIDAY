"""Radiation and atmospheric optical observations for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_radiation_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate radiation and optical solar sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-RAD-SW": lambda: state.radiation.shortwave_downwelling_w_m2,
        "ENV-RAD-LW": lambda: state.radiation.longwave_downwelling_w_m2,
        "ENV-RAD-NET": lambda: state.radiation.net_radiation_w_m2,
        "ENV-RAD-UV": lambda: state.radiation.uv_index,
        "ENV-RAD-AOD": lambda: state.radiation.aerosol_optical_depth_500nm,
        "ENV-RAD-DAYLIGHT": lambda: state.radiation.is_daylight,
        "ENV-RAD-SOLAR-AVAIL": lambda: state.radiation.solar_availability_percent,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.RADIATION:
            raise KeyError(f"Configuration missing or invalid domain for radiation sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
