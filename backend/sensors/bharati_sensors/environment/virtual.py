"""Derived environmental indicators and operating condition sensors.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.

All sensors in this module are:
kind = SensorKind.DERIVED
evidence_level = EvidenceLevel.DERIVED
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_derived_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate derived environmental risk, comfort, and operational severity sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    calculators: dict[str, Callable[[], SensorValue]] = {
        "ENV-DERIVED-DEWPOINT": lambda: state.derived.dew_point_c,
        "ENV-DERIVED-AIR-DENSITY": lambda: state.derived.air_density_kg_m3,
        "ENV-DERIVED-WIND-CHILL": lambda: state.derived.wind_chill_c,
        "ENV-DERIVED-COLD-STRESS": lambda: state.derived.cold_stress_risk,
        "ENV-DERIVED-BLIZZARD-RISK": lambda: state.derived.blizzard_risk,
        "ENV-DERIVED-FREEZE-RISK": lambda: state.derived.freeze_risk,
        "ENV-DERIVED-SNOW-ACCESS-RISK": lambda: state.derived.snow_access_risk,
        "ENV-DERIVED-ICE-ACCESS-RISK": lambda: state.derived.ice_access_risk,
        "ENV-DERIVED-SOLAR-AVAILABILITY": lambda: state.derived.solar_availability_percent,
        "ENV-DERIVED-VISIBILITY-RISK": lambda: state.derived.visibility_risk,
        "ENV-DERIVED-ENVIRONMENTAL-RISK": lambda: state.derived.environmental_risk,
        "ENV-DERIVED-OPERATING-CONDITION": lambda: state.derived.operating_condition_summary,
    }

    for sensor_id, calc in calculators.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.DERIVED_INDICATORS:
            raise KeyError(f"Configuration missing or invalid domain for derived sensor: {sensor_id}")

        if cfg.kind != SensorKind.DERIVED:
            raise ValueError(f"Sensor {sensor_id} must have kind=DERIVED")

        sensors.append(DerivedEnvironmentSensor(cfg, clock, calc))

    return sensors
