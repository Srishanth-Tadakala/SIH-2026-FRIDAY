"""Ocean and coastal environmental context observations for Prydz Bay / Bharati coast.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.

SEMANTIC CLASSIFICATION:
Classified as Ocean / Coastal Environmental Context (location_scope="COASTAL_CONTEXT",
evidence_level=NOT_PUBLICLY_CONFIRMED), representing marine environmental conditions
rather than station-control hardware.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_ocean_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate coastal oceanographic and marine context sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-OCEAN-TEMP": lambda: state.ocean.water_temperature_c,
        "ENV-OCEAN-SAL": lambda: state.ocean.salinity_psu,
        "ENV-OCEAN-COND": lambda: state.ocean.conductivity_ms_cm,
        "ENV-OCEAN-PRESS": lambda: state.ocean.pressure_dbar,
        "ENV-OCEAN-CURRENT-S": lambda: state.ocean.current_speed_mps,
        "ENV-OCEAN-CURRENT-D": lambda: state.ocean.current_direction_deg,
        "ENV-OCEAN-WAVE-H": lambda: state.ocean.significant_wave_height_m,
        "ENV-OCEAN-WAVE-P": lambda: state.ocean.wave_period_s,
        "ENV-OCEAN-LEVEL": lambda: state.ocean.sea_level_anomaly_m,
        "ENV-OCEAN-TURB": lambda: state.ocean.turbidity_ntu,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.OCEAN:
            raise KeyError(f"Configuration missing or invalid domain for ocean sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
