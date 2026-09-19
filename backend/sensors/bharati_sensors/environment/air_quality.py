"""Atmospheric aerosol and air quality observations for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_air_quality_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate atmospheric particulate, optical, and trace gas sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-AIR-BC": lambda: state.aerosol.black_carbon_ng_m3,
        "ENV-AIR-AERO": lambda: state.aerosol.pm10_ug_m3,
        "ENV-AIR-PCOUNT": lambda: state.aerosol.particle_number_cm3,
        "ENV-AIR-PSIZE": lambda: state.aerosol.mean_particle_size_nm,
        "ENV-AIR-SCAT": lambda: state.aerosol.scattering_coeff_Mm_inv,
        "ENV-AIR-ABS": lambda: state.aerosol.absorption_coeff_Mm_inv,
        "ENV-AIR-AOD": lambda: state.aerosol.column_aod,
        "ENV-AIR-CO": lambda: state.aerosol.carbon_monoxide_ppb,
        "ENV-AIR-NOX": lambda: state.aerosol.nitrogen_oxides_ppb,
        "ENV-AIR-SO2": lambda: state.aerosol.sulfur_dioxide_ppb,
        "ENV-AIR-O3": lambda: state.aerosol.surface_ozone_ppb,
        "ENV-AIR-QUALITY": lambda: state.aerosol.air_quality_index,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.ATMOSPHERIC_AEROSOL:
            raise KeyError(f"Configuration missing or invalid domain for aerosol sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
