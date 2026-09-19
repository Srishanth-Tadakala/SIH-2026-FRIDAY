"""Data models, enums, and configuration structures for Bharati Logistics Observations.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Union

# Typed union for all allowable sensor values
SensorValue = Union[float, int, str, bool, list[float], None]


class EvidenceLevel(str, Enum):
    """Authoritative classification of evidence basis for a logistics observation point."""
    DOCUMENTED = "DOCUMENTED"
    IMPLIED = "IMPLIED"
    NOT_PUBLICLY_CONFIRMED = "NOT_PUBLICLY_CONFIRMED"
    DERIVED = "DERIVED"


class SensorProvenance(str, Enum):
    """Sensor data origin/provenance.
    
    SIMULATED is the mandatory default for v1.
    LIVE and WHAT_IF are defined for future adapters and twin core scenarios.
    """
    LIVE = "LIVE"
    SIMULATED = "SIMULATED"
    WHAT_IF = "WHAT_IF"


class SensorKind(str, Enum):
    """Sensor role classification.
    
    INSTRUMENT: Direct physical/IoT measurement (e.g. engine RPM, fuel flow, temperature).
    STATE: Discrete operational condition or record (e.g. status, location, inventory count).
    DERIVED: Mathematically calculated index, risk score, or composite indicator.
    """
    INSTRUMENT = "INSTRUMENT"
    STATE = "STATE"
    DERIVED = "DERIVED"


class SensorQuality(str, Enum):
    """Sensor data validity and quality state.
    
    Fully aligned with Energy, Infrastructure, and Environment layer vocabulary.
    """
    GOOD = "GOOD"
    WARNING = "WARNING"
    BAD = "BAD"
    STALE = "STALE"
    FAILED = "FAILED"


class FailureType(str, Enum):
    """Types of simulated technical sensor faults.
    
    Absence of failure is represented by failure = None.
    """
    DROPOUT = "DROPOUT"
    STALE = "STALE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    STUCK = "STUCK"


class PhysicalQuantity(str, Enum):
    """Physical quantity classification for strict unit and semantics validation."""
    SPEED = "SPEED"
    HEADING = "HEADING"
    ROTATIONAL_SPEED = "ROTATIONAL_SPEED"
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    VOLTAGE = "VOLTAGE"
    FLOW_RATE = "FLOW_RATE"
    VOLUME = "VOLUME"
    MASS = "MASS"
    ACCELERATION = "ACCELERATION"
    DISTANCE = "DISTANCE"
    ALTITUDE = "ALTITUDE"
    TIME = "TIME"
    PERCENT = "PERCENT"
    COUNT = "COUNT"
    STATUS = "STATUS"
    BOOLEAN = "BOOLEAN"
    SCORE = "SCORE"
    INDEX = "INDEX"
    DIMENSIONLESS = "DIMENSIONLESS"


class LogisticsDomain(str, Enum):
    """Subsystem domain classification within Bharati Logistics (11 domains)."""
    FLEET = "FLEET"
    CARGO = "CARGO"
    FUEL = "FUEL"
    COLD_CHAIN = "COLD_CHAIN"
    AVIATION = "AVIATION"
    MARINE = "MARINE"
    ROUTES = "ROUTES"
    MISSIONS = "MISSIONS"
    INVENTORY = "INVENTORY"
    WASTE = "WASTE"
    DERIVED = "DERIVED"


@dataclass
class LogisticsConditionState:
    """Explainable station logistics operating condition summary."""
    level: str  # "NORMAL", "CAUTION", "RESTRICTED", "LOCKDOWN"
    reasons: list[str] = field(default_factory=list)
    contributing_indicators: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        """Return formatted explainable summary string."""
        if not self.reasons:
            return self.level
        return f"{self.level} ({', '.join(self.reasons)})"


@dataclass(frozen=True)
class FleetAssetInfo:
    """Physical fleet asset metadata for Bharati station registry."""
    asset_id: str
    name: str
    asset_type: str  # "PISTEN_BULLY", "SNOW_SCOOTER", "TELEHANDLER", "EXCAVATOR", "BULLDOZER", "MANTIS_CRANE"
    capacity_description: str
    documented_model: str
    operational_role: str


@dataclass(frozen=True)
class SensorConfig:
    """Configuration specification and spatial context for a logistics observation point."""
    sensor_id: str
    name: str
    asset_id: str
    domain: LogisticsDomain
    subsystem: str
    kind: SensorKind
    evidence_level: EvidenceLevel
    physical_quantity: PhysicalQuantity
    unit: str
    sampling_interval_seconds: float
    station_id: str = "BHARATI"
    location_scope: str = "LOCAL_STATION"  # LOCAL_STATION, LOCAL_FLEET, STATION_STORAGE, STATION_FUEL_FARM, STATION_REEFER, AIR_OPERATION, MARINE_OPERATION, FIELD_ROUTE, REMOTE_FIELD_SITE, DERIVED_LOGISTICS_ENGINE
    measurement_zone: str = "STATION_PERIMETER"
    parent_asset_id: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    default_value: SensorValue = None  # Fallback/initialization only, not physics model
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
    """Standardized logistics observation telemetry reading with provenance and quality."""
    sensor_id: str
    name: str
    asset_id: str
    domain: LogisticsDomain
    subsystem: str
    kind: SensorKind
    physical_quantity: PhysicalQuantity
    value: SensorValue
    unit: str
    timestamp: str  # ISO-8601 UTC
    station_id: str = "BHARATI"
    location_scope: str = "LOCAL_STATION"
    measurement_zone: str = "STATION_PERIMETER"
    simulation_time_seconds: float = 0.0
    event_time_seconds: float | None = None
    provenance: SensorProvenance = SensorProvenance.SIMULATED
    source_reference: str = "bharati_logistics_physics_v1"
    quality: SensorQuality = SensorQuality.GOOD
    evidence_level: EvidenceLevel = EvidenceLevel.DOCUMENTED
    confidence: float = 1.0
    valid: bool = True
    min_valid: float | None = None
    max_valid: float | None = None
    stale_after_seconds: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)

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
