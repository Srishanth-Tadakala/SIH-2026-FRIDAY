"""Sensor data models, enums, and configuration structures for Bharati Station Energy.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Union

# Typed union for all allowable sensor values
SensorValue = Union[float, int, str, bool, list[float], None]


class SensorQuality(str, Enum):
    """Allowed sensor quality states."""
    GOOD = "GOOD"
    WARNING = "WARNING"
    BAD = "BAD"
    STALE = "STALE"
    FAILED = "FAILED"


class SensorProvenance(str, Enum):
    """Sensor data origin/provenance.
    
    SIMULATED is the default for this phase.
    LIVE and WHAT_IF are defined for future adapters and scenarios.
    """
    LIVE = "LIVE"
    SIMULATED = "SIMULATED"
    WHAT_IF = "WHAT_IF"


class SensorCategory(str, Enum):
    """Energy domain subsystem category."""
    CHP = "CHP"
    UPS = "UPS"
    FUEL = "FUEL"
    HEATING = "HEATING"
    VIRTUAL = "VIRTUAL"


class SensorKind(str, Enum):
    """Sensor role classification.
    
    INSTRUMENT: Direct physical measurement (e.g. power meter, thermometer).
    STATE: Discrete operational state (e.g. RUNNING, OFF, LEAK).
    DERIVED: Calculated mathematically from other sensor readings.
    """
    INSTRUMENT = "INSTRUMENT"
    STATE = "STATE"
    DERIVED = "DERIVED"


class FailureType(str, Enum):
    """Types of simulated sensor failures."""
    NONE = "NONE"
    DROPOUT = "DROPOUT"
    STALE = "STALE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    STUCK = "STUCK"


@dataclass(frozen=True)
class SensorConfig:
    """Configuration specification for a sensor."""
    sensor_id: str
    asset: str
    category: SensorCategory
    kind: SensorKind
    parameter: str
    unit: str
    station: str = "BHARATI"
    domain: str = "ENERGY"
    sampling_interval_seconds: float = 1.0
    min_valid: float | None = None
    max_valid: float | None = None
    default_value: SensorValue = None
    stale_after_seconds: float = 60.0
    sensor_type: str = ""
    description: str = ""


@dataclass
class SensorReading:
    """Standardized sensor measurement reading."""
    sensor_id: str
    station: str
    domain: str
    asset: str
    category: SensorCategory
    kind: SensorKind
    parameter: str
    value: SensorValue
    unit: str
    timestamp: str
    source: SensorProvenance = SensorProvenance.SIMULATED
    source_reference: str = "bharati_energy_physics_v1"
    quality: SensorQuality = SensorQuality.GOOD
    confidence: float = 1.0
    valid: bool = True
    min_valid: float | None = None
    max_valid: float | None = None
    stale_after_seconds: float = 60.0
    sensor_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert reading to dictionary representation."""
        data = asdict(self)
        data["category"] = self.category.value
        data["kind"] = self.kind.value
        data["source"] = self.source.value
        data["quality"] = self.quality.value
        return data
