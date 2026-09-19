"""Factory functions and cross-pillar read-only state interfaces for Bharati Environment.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

ARCHITECTURAL PRINCIPLE:
Cross-pillar interfaces are STRICTLY READ-ONLY.
Environment does NOT modify Energy, Infrastructure, or Logistics state.
"""

from __future__ import annotations

from typing import Any

from ..energy.clock import SimulationClock
from ..infrastructure.environmental_input import EnvironmentalInput
from .air_quality import create_air_quality_sensors
from .atmospheric_electricity import create_atmospheric_electricity_sensors
from .environmental_water import create_environmental_water_sensors
from .ocean import create_ocean_sensors
from .physics_state import BharatiEnvironmentPhysicsState
from .radiation import create_radiation_sensors
from .registry import EnvironmentSensorRegistry
from .scientific import create_scientific_sensors
from .snow_ice import create_snow_ice_sensors
from .virtual import create_derived_sensors
from .weather import create_weather_sensors


def create_bharati_environment_sensors(
    seed: int | None = 42,
    clock: SimulationClock | None = None,
) -> EnvironmentSensorRegistry:
    """Instantiate and wire the complete Bharati Environment Observation Layer (87 points)."""
    physics = BharatiEnvironmentPhysicsState(seed=seed)
    sim_clock = clock or SimulationClock()
    registry = EnvironmentSensorRegistry(physics=physics, clock=sim_clock)

    domain_creators = [
        create_weather_sensors,
        create_radiation_sensors,
        create_air_quality_sensors,
        create_snow_ice_sensors,
        create_ocean_sensors,
        create_environmental_water_sensors,
        create_atmospheric_electricity_sensors,
        create_scientific_sensors,
        create_derived_sensors,
    ]

    for creator in domain_creators:
        sensors = creator(physics, sim_clock)
        for s in sensors:
            registry.register(s)

    # Initial read to populate latest readings cache
    registry.read_all()
    return registry


# =============================================================================
# CROSS-PILLAR READ-ONLY INTERFACES
# =============================================================================

def _extract_physics(
    source: BharatiEnvironmentPhysicsState | EnvironmentSensorRegistry,
) -> BharatiEnvironmentPhysicsState:
    """Extract BharatiEnvironmentPhysicsState from either state instance or registry."""
    if isinstance(source, EnvironmentSensorRegistry):
        return source.physics
    elif isinstance(source, BharatiEnvironmentPhysicsState):
        return source
    raise TypeError(f"Expected BharatiEnvironmentPhysicsState or EnvironmentSensorRegistry, got {type(source)}")


def to_infrastructure_environmental_input(
    source: BharatiEnvironmentPhysicsState | EnvironmentSensorRegistry,
) -> EnvironmentalInput:
    """Generate read-only EnvironmentalInput compatible with Infrastructure physics."""
    phy = _extract_physics(source)
    return EnvironmentalInput(
        ambient_temperature_c=round(phy.weather.ambient_temperature_c, 2),
        wind_speed_ms=round(phy.weather.wind_speed_mps, 2),
        wind_direction_deg=round(phy.weather.wind_direction_deg, 1),
        solar_radiation_w_m2=round(phy.radiation.shortwave_downwelling_w_m2, 1),
        atmospheric_pressure_hpa=round(phy.weather.atmospheric_pressure_hpa, 1),
        relative_humidity_percent=round(phy.weather.relative_humidity_percent, 1),
        snow_accumulation_rate_mm_h=round(phy.weather.precipitation_rate_mm_h, 2),
    )


def get_infrastructure_environmental_extended(
    source: BharatiEnvironmentPhysicsState | EnvironmentSensorRegistry,
) -> dict[str, Any]:
    """Extended read-only environmental context for Infrastructure digital twin."""
    phy = _extract_physics(source)
    return {
        "ambient_temperature_c": phy.weather.ambient_temperature_c,
        "wind_speed_mps": phy.weather.wind_speed_mps,
        "wind_direction_deg": phy.weather.wind_direction_deg,
        "humidity_percent": phy.weather.relative_humidity_percent,
        "solar_radiation_w_m2": phy.radiation.shortwave_downwelling_w_m2,
        "snow_depth_m": phy.snow.snow_depth_m,
        "freeze_risk": phy.derived.freeze_risk,
        "visibility_m": phy.weather.visibility_m,
    }


def get_energy_environmental_interface(
    source: BharatiEnvironmentPhysicsState | EnvironmentSensorRegistry,
) -> dict[str, Any]:
    """Read-only environmental boundary context driving station Energy dynamics."""
    phy = _extract_physics(source)
    return {
        "ambient_temperature_c": phy.weather.ambient_temperature_c,
        "solar_radiation_w_m2": phy.radiation.shortwave_downwelling_w_m2,
        "wind_speed_mps": phy.weather.wind_speed_mps,
        "solar_availability_percent": phy.derived.solar_availability_percent,
        "environmental_operating_condition": phy.derived.operating_condition.summary(),
        "operating_condition_level": phy.derived.operating_condition.level,
        "operating_condition_reasons": list(phy.derived.operating_condition.reasons),
    }


def get_logistics_environmental_interface(
    source: BharatiEnvironmentPhysicsState | EnvironmentSensorRegistry,
) -> dict[str, Any]:
    """Read-only environmental accessibility and route safety context for Logistics."""
    phy = _extract_physics(source)
    return {
        "wind_speed_mps": phy.weather.wind_speed_mps,
        "wind_gust_mps": phy.weather.wind_gust_mps,
        "visibility_m": phy.weather.visibility_m,
        "snow_depth_m": phy.snow.snow_depth_m,
        "sea_ice_condition": {
            "ice_present": phy.sea_ice.ice_present,
            "thickness_m": phy.sea_ice.ice_thickness_m,
            "concentration_percent": phy.sea_ice.ice_concentration_percent,
            "surface_temperature_c": phy.sea_ice.ice_surface_temperature_c,
            "drift_speed_mps": phy.sea_ice.ice_drift_speed_mps,
            "distance_to_open_water_km": phy.sea_ice.distance_to_open_water_km,
        },
        "ocean_condition": {
            "water_temperature_c": phy.ocean.water_temperature_c,
            "significant_wave_height_m": phy.ocean.significant_wave_height_m,
            "current_speed_mps": phy.ocean.current_speed_mps,
            "sea_level_anomaly_m": phy.ocean.sea_level_anomaly_m,
        },
        "weather_severity": {
            "blizzard_risk": phy.derived.blizzard_risk,
            "cold_stress_risk": phy.derived.cold_stress_risk,
            "operating_condition": phy.derived.operating_condition.summary(),
            "operating_condition_level": phy.derived.operating_condition.level,
        },
        "accessibility_indicators": {
            "snow_access_risk": phy.derived.snow_access_risk,
            "ice_access_risk": phy.derived.ice_access_risk,
            "visibility_risk": phy.derived.visibility_risk,
            "composite_risk": phy.derived.environmental_risk,
        },
    }
