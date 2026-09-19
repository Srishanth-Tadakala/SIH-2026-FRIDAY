"""Data models, enums, and configuration structures for Bharati Environment Observations.

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
    """Authoritative classification of evidence basis for an environmental point."""
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
    
    INSTRUMENT: Direct physical measurement (e.g. anemometer, barometer, aethalometer).
    STATE: Discrete operational condition (e.g. daylight active, fast-ice present).
    DERIVED: Mathematically calculated index or indicator.
    """
    INSTRUMENT = "INSTRUMENT"
    STATE = "STATE"
    DERIVED = "DERIVED"


class SensorQuality(str, Enum):
    """Sensor data validity and quality state.
    
    Fully aligned with Energy and Infrastructure layer vocabulary.
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
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    PRESSURE_TENDENCY = "PRESSURE_TENDENCY"
    WIND_SPEED = "WIND_SPEED"
    DIRECTION = "DIRECTION"
    RELATIVE_HUMIDITY = "RELATIVE_HUMIDITY"
    SOLAR_IRRADIANCE = "SOLAR_IRRADIANCE"
    MASS_CONCENTRATION = "MASS_CONCENTRATION"
    PARTICLE_COUNT = "PARTICLE_COUNT"
    SCATTERING_COEFFICIENT = "SCATTERING_COEFFICIENT"
    ABSORPTION_COEFFICIENT = "ABSORPTION_COEFFICIENT"
    OPTICAL_DEPTH = "OPTICAL_DEPTH"
    DEPTH = "DEPTH"
    THICKNESS = "THICKNESS"
    VELOCITY = "VELOCITY"
    ACCELERATION = "ACCELERATION"
    MASS_FLUX = "MASS_FLUX"
    DISTANCE = "DISTANCE"
    VOLTAGE = "VOLTAGE"
    CURRENT_DENSITY = "CURRENT_DENSITY"
    CONDUCTIVITY = "CONDUCTIVITY"
    ELECTRON_CONTENT = "ELECTRON_CONTENT"
    OPTICAL_INTENSITY = "OPTICAL_INTENSITY"
    PH = "PH"
    TURBIDITY = "TURBIDITY"
    SALINITY = "SALINITY"
    PERCENT = "PERCENT"
    INDEX = "INDEX"
    RATE = "RATE"
    STATUS = "STATUS"
    DIMENSIONLESS = "DIMENSIONLESS"
    COUNT = "COUNT"
    TIME = "TIME"
    PRESENCE = "PRESENCE"


class EnvironmentDomain(str, Enum):
    """Subsystem domain classification within Environment."""
    WEATHER = "WEATHER"
    RADIATION = "RADIATION"
    ATMOSPHERIC_AEROSOL = "ATMOSPHERIC_AEROSOL"
    SNOW_ICE = "SNOW_ICE"
    OCEAN = "OCEAN"
    ENVIRONMENTAL_WATER = "ENVIRONMENTAL_WATER"
    ATMOSPHERIC_ELECTRICITY = "ATMOSPHERIC_ELECTRICITY"
    SCIENTIFIC_CONTEXT = "SCIENTIFIC_CONTEXT"
    DERIVED_INDICATORS = "DERIVED_INDICATORS"


@dataclass
class OperatingConditionState:
    """Explainable station environmental operating condition."""
    level: str  # "GREEN", "YELLOW", "RED", "BLACK"
    reasons: list[str] = field(default_factory=list)
    contributing_indicators: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        """Return formatted explainable summary string."""
        if not self.reasons:
            return self.level
        return f"{self.level} ({', '.join(self.reasons)})"


@dataclass(frozen=True)
class SensorConfig:
    """Configuration specification and spatial context for an environmental observation."""
    sensor_id: str
    name: str
    asset_id: str
    domain: EnvironmentDomain
    subsystem: str
    kind: SensorKind
    evidence_level: EvidenceLevel
    physical_quantity: PhysicalQuantity
    unit: str
    sampling_interval_seconds: float
    station_id: str = "BHARATI"
    location_scope: str = "LOCAL_STATION"  # LOCAL_STATION, COASTAL, COASTAL_CONTEXT
    measurement_zone: str = "STATION_PERIMETER"
    parent_asset_id: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    default_value: SensorValue = None  # Initialization/fallback only, not physics model
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
    """Standardized environmental sensor telemetry reading with hierarchy and provenance."""
    sensor_id: str
    name: str
    asset_id: str
    domain: EnvironmentDomain
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
    event_time_seconds: float | None = None  # None unless reporting a discrete physical event
    provenance: SensorProvenance = SensorProvenance.SIMULATED
    source_reference: str = "bharati_environment_physics_v1"
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
