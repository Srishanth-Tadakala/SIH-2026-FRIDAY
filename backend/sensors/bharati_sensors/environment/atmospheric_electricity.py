"""Atmospheric electricity and global electric circuit observations at Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_atmospheric_electricity_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate atmospheric potential gradient, air-earth current, and ion sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-ELEC-EFIELD": lambda: state.atmospheric_electricity.electric_field_v_m,
        "ENV-ELEC-AEC": lambda: state.atmospheric_electricity.air_earth_current_pa_m2,
        "ENV-ELEC-MAXWELL": lambda: state.atmospheric_electricity.maxwell_current_pa_m2,
        "ENV-ELEC-POS": lambda: state.atmospheric_electricity.positive_conductivity_fs_m,
        "ENV-ELEC-NEG": lambda: state.atmospheric_electricity.negative_conductivity_fs_m,
        "ENV-ELEC-STATUS": lambda: state.atmospheric_electricity.system_status,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.ATMOSPHERIC_ELECTRICITY:
            raise KeyError(f"Configuration missing or invalid domain for electricity sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
