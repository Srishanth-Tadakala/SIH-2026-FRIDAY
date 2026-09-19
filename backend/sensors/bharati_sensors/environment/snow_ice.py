"""Cryosphere (local station snow and coastal sea ice) observations for Bharati.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.

SPATIAL DISTINCTION:
- Local Station Snowpack: location_scope="LOCAL_STATION", measurement_zone="STATION_PERIMETER"
- Coastal Access Fast Ice: location_scope="COASTAL", measurement_zone="COASTAL_STUDY_AREA"
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_snow_ice_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate station snowpack and coastal sea-ice sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        # Station local snow
        "ENV-SNOW-DEPTH": lambda: state.snow.snow_depth_m,
        "ENV-SNOW-TEMP": lambda: state.snow.snow_temperature_c,
        "ENV-SNOW-DENS": lambda: state.snow.snow_density_kg_m3,
        "ENV-SNOW-ACC": lambda: state.snow.accumulation_rate_mm_h,
        "ENV-SNOW-DRIFT": lambda: state.snow.drift_mass_flux_g_m2_s,
        # Coastal access sea ice
        "ENV-ICE-PRES": lambda: state.sea_ice.ice_present,
        "ENV-ICE-THICK": lambda: state.sea_ice.ice_thickness_m,
        "ENV-ICE-CONC": lambda: state.sea_ice.ice_concentration_percent,
        "ENV-ICE-TEMP": lambda: state.sea_ice.ice_surface_temperature_c,
        "ENV-ICE-DRIFT-S": lambda: state.sea_ice.ice_drift_speed_mps,
        "ENV-ICE-EDGE": lambda: state.sea_ice.distance_to_open_water_km,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.SNOW_ICE:
            raise KeyError(f"Configuration missing or invalid domain for snow/ice sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
