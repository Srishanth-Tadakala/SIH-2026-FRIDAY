"""Natural environmental water and limnological observations in Larsemann Hills.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.

CRITICAL DOMAIN SEPARATION:
This domain represents natural proglacial/meltwater lakes (e.g. Lake Progress, Stepped Lake)
and environmental runoff in Larsemann Hills.
It does NOT monitor or overlap with Infrastructure station water (RO seawater intake,
potable water storage, or wastewater MBR).
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_environmental_water_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate natural lake and proglacial meltwater limnological sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-WATER-TEMP": lambda: state.environmental_water.water_temperature_c,
        "ENV-WATER-PH": lambda: state.environmental_water.ph,
        "ENV-WATER-COND": lambda: state.environmental_water.conductivity_us_cm,
        "ENV-WATER-TURB": lambda: state.environmental_water.turbidity_ntu,
        "ENV-WATER-DO": lambda: state.environmental_water.dissolved_oxygen_mg_l,
        "ENV-WATER-CONT": lambda: state.environmental_water.contamination_index,
        "ENV-WATER-HC": lambda: state.environmental_water.hydrocarbon_trace_ppb,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.ENVIRONMENTAL_WATER:
            raise KeyError(f"Configuration missing or invalid domain for water sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
