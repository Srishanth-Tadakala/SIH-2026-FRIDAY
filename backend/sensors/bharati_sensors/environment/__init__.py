"""Bharati Station Environment Observation Layer (87 Points).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Exclusively implements environmental observation telemetry, physical state simulation,
and read-only cross-pillar interfaces for 9 environmental domains around Bharati Station.
"""

from __future__ import annotations

from .factory import (
    create_bharati_environment_sensors,
    get_energy_environmental_interface,
    get_infrastructure_environmental_extended,
    get_logistics_environmental_interface,
    to_infrastructure_environmental_input,
)
from .models import (
    EnvironmentDomain,
    EvidenceLevel,
    FailureType,
    OperatingConditionState,
    PhysicalQuantity,
    SensorConfig,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    SensorReading,
    SensorValue,
)
from .physics_state import (
    AerosolState,
    AtmosphericElectricityState,
    BharatiEnvironmentPhysicsState,
    DerivedEnvironmentalState,
    EnvironmentalWaterState,
    IonosphereState,
    OceanState,
    RadiationState,
    SeaIceState,
    SeismicState,
    SkyState,
    SnowState,
    WeatherState,
)
from .registry import EnvironmentSensorRegistry

__all__ = [
    "create_bharati_environment_sensors",
    "EnvironmentSensorRegistry",
    "BharatiEnvironmentPhysicsState",
    "OperatingConditionState",
    "to_infrastructure_environmental_input",
    "get_infrastructure_environmental_extended",
    "get_energy_environmental_interface",
    "get_logistics_environmental_interface",
    "EvidenceLevel",
    "SensorProvenance",
    "SensorKind",
    "SensorQuality",
    "FailureType",
    "PhysicalQuantity",
    "EnvironmentDomain",
    "SensorConfig",
    "SensorReading",
    "SensorValue",
    "WeatherState",
    "RadiationState",
    "AerosolState",
    "SnowState",
    "SeaIceState",
    "OceanState",
    "EnvironmentalWaterState",
    "AtmosphericElectricityState",
    "IonosphereState",
    "SkyState",
    "SeismicState",
    "DerivedEnvironmentalState",
]
