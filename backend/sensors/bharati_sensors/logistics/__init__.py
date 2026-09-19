"""Bharati Research Station Logistics Observation Layer v1.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E).

The Logistics Observation Layer provides 98 simulated observation and telemetry points
across 11 domains (Fleet, Cargo, Fuel, Cold Chain, Aviation, Marine, Routes, Missions,
Inventory, Waste, Derived).
"""

from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import (
    BHARATI_LOGISTICS_SENSORS,
    CONFIG_BY_ID,
    CONFIGS_BY_DOMAIN,
    FLEET_ASSET_REGISTRY,
    get_confidence_for_evidence,
    validate_catalogue,
)
from .factory import create_bharati_logistics_sensors
from .models import (
    EvidenceLevel,
    FailureType,
    FleetAssetInfo,
    LogisticsConditionState,
    LogisticsDomain,
    PhysicalQuantity,
    SensorConfig,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    SensorReading,
    SensorValue,
)
from .physics_state import (
    AviationState,
    BharatiLogisticsPhysicsState,
    CargoState,
    ColdChainState,
    DerivedLogisticsState,
    FleetState,
    FuelLogisticsState,
    InventoryState,
    MarineState,
    MissionsState,
    RoutesState,
    WasteLogisticsState,
)
from .registry import LogisticsSensorRegistry

__all__ = [
    # Factory & Registry
    "create_bharati_logistics_sensors",
    "LogisticsSensorRegistry",
    # Base Sensor Classes
    "BaseLogisticsSensor",
    "StateBoundLogisticsSensor",
    "DerivedLogisticsSensor",
    # Physics & Simulation State
    "BharatiLogisticsPhysicsState",
    "FleetState",
    "CargoState",
    "FuelLogisticsState",
    "ColdChainState",
    "AviationState",
    "MarineState",
    "RoutesState",
    "MissionsState",
    "InventoryState",
    "WasteLogisticsState",
    "DerivedLogisticsState",
    # Enums & Data Structures
    "LogisticsDomain",
    "EvidenceLevel",
    "SensorProvenance",
    "SensorKind",
    "SensorQuality",
    "FailureType",
    "PhysicalQuantity",
    "LogisticsConditionState",
    "FleetAssetInfo",
    "SensorConfig",
    "SensorReading",
    "SensorValue",
    # Configs & Registries
    "BHARATI_LOGISTICS_SENSORS",
    "FLEET_ASSET_REGISTRY",
    "CONFIG_BY_ID",
    "CONFIGS_BY_DOMAIN",
    "get_confidence_for_evidence",
    "validate_catalogue",
]
