"""Data models, enums, and configuration structures for Bharati Infrastructure Sensors.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Union

# Typed union for all allowable sensor values
SensorValue = Union[float, int, str, bool, list[float], None]


class EvidenceLevel(str, Enum):
    """Authoritative classification of evidence basis for a sensor point."""
    DOCUMENTED = "DOCUMENTED"
    IMPLIED = "IMPLIED"
    NOT_PUBLICLY_CONFIRMED = "NOT_PUBLICLY_CONFIRMED"
    DERIVED = "DERIVED"


class SensorProvenance(str, Enum):
    """Sensor data origin/provenance.
    
    SIMULATED is the default for this phase.
    LIVE and WHAT_IF are defined for future adapters and scenarios.
    """
    LIVE = "LIVE"
    SIMULATED = "SIMULATED"
    WHAT_IF = "WHAT_IF"


class SensorKind(str, Enum):
    """Sensor role classification.
    
    INSTRUMENT: Direct physical measurement (e.g. flow meter, RTD, pressure transmitter).
    STATE: Discrete operational condition (e.g. pump running, damper open, alarm active).
    DERIVED: Mathematically calculated index or metric.
    """
    INSTRUMENT = "INSTRUMENT"
    STATE = "STATE"
    DERIVED = "DERIVED"


class SensorQuality(str, Enum):
    """Sensor data validity and quality state.
    
    Fully aligned with the Energy layer vocabulary.
    """
    GOOD = "GOOD"
    WARNING = "WARNING"
    BAD = "BAD"
    STALE = "STALE"
    FAILED = "FAILED"


class FailureType(str, Enum):
    """Types of simulated technical sensor faults.
    
    No 'NONE' enum: absence of failure is represented by failure = None.
    """
    DROPOUT = "DROPOUT"
    STALE = "STALE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    STUCK = "STUCK"


class PhysicalQuantity(str, Enum):
    """Physical quantity classification for strict unit and semantics validation."""
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    FLOW = "FLOW"
    VOLUME = "VOLUME"
    LEVEL_PERCENT = "LEVEL_PERCENT"
    CONCENTRATION = "CONCENTRATION"
    DISPLACEMENT = "DISPLACEMENT"
    STRAIN = "STRAIN"
    VIBRATION = "VIBRATION"
    POWER = "POWER"
    CURRENT = "CURRENT"
    VOLTAGE = "VOLTAGE"
    FREQUENCY = "FREQUENCY"
    STATUS = "STATUS"
    COUNT = "COUNT"
    DIMENSIONLESS = "DIMENSIONLESS"
    TIME = "TIME"


class InfrastructureDomain(str, Enum):
    """Subsystem domain classification within Infrastructure."""
    BUILDING = "BUILDING"
    HVAC = "HVAC"
    WATER = "WATER"
    WASTEWATER = "WASTEWATER"
    FIRE = "FIRE"
    REFRIGERATION = "REFRIGERATION"
    PIPELINES = "PIPELINES"
    EMERGENCY = "EMERGENCY"
    SECURITY = "SECURITY"
    BMS = "BMS"
    VIRTUAL = "VIRTUAL"


@dataclass(frozen=True)
class SensorConfig:
    """Configuration specification and spatial hierarchy for an infrastructure sensor."""
    sensor_id: str
    name: str
    asset_id: str
    domain: InfrastructureDomain
    subsystem: str
    kind: SensorKind
    evidence_level: EvidenceLevel
    physical_quantity: PhysicalQuantity
    unit: str
    sampling_interval_seconds: float
    station_id: str = "BHARATI"
    building_id: str = "MAIN_BUILDING"
    level_id: str = "LEVEL_1"
    zone_id: str = "COMMON"
    parent_asset_id: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    default_value: SensorValue = None
    stale_after_seconds: float = 60.0
    state_path: str = ""
    state_dependencies: list[str] = field(default_factory=list)
    description: str = ""
    simulation_assumption: bool = False
    failure_modes: list[FailureType] = field(
        default_factory=lambda: [
            FailureType.DROPOUT,
            FailureType.STALE,
            FailureType.OUT_OF_RANGE,
            FailureType.STUCK,
        ]
    )
    enabled: bool = True


@dataclass
class SensorReading:
    """Standardized sensor telemetry reading with full hierarchy and provenance."""
    sensor_id: str
    name: str
    asset_id: str
    domain: InfrastructureDomain
    subsystem: str
    kind: SensorKind
    physical_quantity: PhysicalQuantity
    value: SensorValue
    unit: str
    timestamp: str  # ISO-8601 UTC
    station_id: str = "BHARATI"
    building_id: str = "MAIN_BUILDING"
    level_id: str = "LEVEL_1"
    zone_id: str = "COMMON"
    simulation_time_seconds: float = 0.0
    event_time_seconds: float | None = None  # None unless reporting a discrete physical event
    provenance: SensorProvenance = SensorProvenance.SIMULATED
    source_reference: str = "bharati_infrastructure_physics_v1"
    quality: SensorQuality = SensorQuality.GOOD
    evidence_level: EvidenceLevel = EvidenceLevel.DOCUMENTED
    confidence: float = 1.0
    valid: bool = True
    min_valid: float | None = None
    max_valid: float | None = None
    stale_after_seconds: float = 60.0

    def to_dict(self) -> dict[str, Any]:
        """Convert reading to serialized dictionary."""
        data = asdict(self)
        data["domain"] = self.domain.value
        data["kind"] = self.kind.value
        data["physical_quantity"] = self.physical_quantity.value
        data["provenance"] = self.provenance.value
        data["quality"] = self.quality.value
        data["evidence_level"] = self.evidence_level.value
        return data
