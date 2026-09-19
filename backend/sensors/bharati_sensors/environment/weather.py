"""Weather and surface meteorological observations for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseEnvironmentSensor, DerivedEnvironmentSensor, StateBoundEnvironmentSensor
from .config import ENVIRONMENT_SENSOR_CONFIGS
from .models import EnvironmentDomain, SensorKind, SensorValue
from .physics_state import BharatiEnvironmentPhysicsState


def create_weather_sensors(
    state: BharatiEnvironmentPhysicsState,
    clock: SimulationClock,
) -> list[BaseEnvironmentSensor]:
    """Instantiate surface weather and meteorological sensors."""
    sensors: list[BaseEnvironmentSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "ENV-WX-TEMP": lambda: state.weather.ambient_temperature_c,
        "ENV-WX-RH": lambda: state.weather.relative_humidity_percent,
        "ENV-WX-PRESS": lambda: state.weather.atmospheric_pressure_hpa,
        "ENV-WX-PRESS-TEND": lambda: state.weather.pressure_tendency_hpa_3h,
        "ENV-WX-WIND-S": lambda: state.weather.wind_speed_mps,
        "ENV-WX-WIND-D": lambda: state.weather.wind_direction_deg,
        "ENV-WX-GUST": lambda: state.weather.wind_gust_mps,
        "ENV-WX-GUST-D": lambda: state.weather.wind_gust_direction_deg,
        "ENV-WX-VIS": lambda: state.weather.visibility_m,
        "ENV-WX-PRECIP-RATE": lambda: state.weather.precipitation_rate_mm_h,
        "ENV-WX-DEW": lambda: state.weather.dew_point_c,
        "ENV-WX-DENS": lambda: state.weather.air_density_kg_m3,
    }

    for sensor_id, getter in getters.items():
        cfg = ENVIRONMENT_SENSOR_CONFIGS.get(sensor_id)
        if cfg is None or cfg.domain != EnvironmentDomain.WEATHER:
            raise KeyError(f"Configuration missing or invalid domain for weather sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedEnvironmentSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundEnvironmentSensor(cfg, clock, getter))

    return sensors
