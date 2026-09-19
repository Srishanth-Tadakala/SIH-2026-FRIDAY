"""Bharati Station Energy Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides physical coherence simulation, sensor telemetry representations,
quality inspection, and failure injection for the Bharati Energy domain.
"""

from .clock import SimulationClock
from .factory import create_bharati_energy_sensors
from .models import (
    FailureType,
    SensorCategory,
    SensorConfig,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    SensorReading,
    SensorValue,
)
from .physics_state import (
    BharatiEnergyPhysicsState,
    CHPPhysicalState,
    FuelPhysicalState,
    HeatingPhysicalState,
    UPSPhysicalState,
)
from .registry import SensorRegistry

__all__ = [
    "create_bharati_energy_sensors",
    "SensorRegistry",
    "SimulationClock",
    "BharatiEnergyPhysicsState",
    "CHPPhysicalState",
    "UPSPhysicalState",
    "FuelPhysicalState",
    "HeatingPhysicalState",
    "SensorReading",
    "SensorConfig",
    "SensorQuality",
    "SensorProvenance",
    "SensorCategory",
    "SensorKind",
    "FailureType",
    "SensorValue",
]
