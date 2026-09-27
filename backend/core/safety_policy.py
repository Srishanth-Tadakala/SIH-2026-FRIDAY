"""Centralized Life-Support and Station Safety Policies for Antarctic Stations.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class SafetyPolicy:
    """Explicit, typed, and auditable life-support thresholds for Antarctic station operations."""

    # Life Support & Habitability Guardrails
    min_indoor_temperature_c: float = 16.0
    max_indoor_temperature_c: float = 26.0
    min_potable_water_liters: float = 1500.0
    min_oxygen_pct: float = 19.5
    max_co2_ppm: float = 1200.0

    # Electrical Microgrid & Generation Guardrails
    min_voltage_v: float = 380.0
    max_voltage_v: float = 420.0
    min_frequency_hz: float = 48.0
    max_frequency_hz: float = 52.0
    max_generator_load_pct: float = 95.0
    min_battery_soc_pct: float = 20.0
    max_coolant_temp_c: float = 98.0

    # Environmental & Disaster Lockouts
    max_smoke_obscuration_pct: float = 1.5
    max_wind_speed_sortie_mps: float = 20.0
    min_ambient_temp_sortie_c: float = -30.0
    max_utilidor_freeze_risk_temp_c: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy parameters for telemetry & audits."""
        return {
            "min_indoor_temperature_c": self.min_indoor_temperature_c,
            "max_indoor_temperature_c": self.max_indoor_temperature_c,
            "min_potable_water_liters": self.min_potable_water_liters,
            "min_oxygen_pct": self.min_oxygen_pct,
            "max_co2_ppm": self.max_co2_ppm,
            "min_voltage_v": self.min_voltage_v,
            "max_voltage_v": self.max_voltage_v,
            "min_frequency_hz": self.min_frequency_hz,
            "max_frequency_hz": self.max_frequency_hz,
            "max_generator_load_pct": self.max_generator_load_pct,
            "min_battery_soc_pct": self.min_battery_soc_pct,
            "max_coolant_temp_c": self.max_coolant_temp_c,
            "max_smoke_obscuration_pct": self.max_smoke_obscuration_pct,
            "max_wind_speed_sortie_mps": self.max_wind_speed_sortie_mps,
            "min_ambient_temp_sortie_c": self.min_ambient_temp_sortie_c,
            "max_utilidor_freeze_risk_temp_c": self.max_utilidor_freeze_risk_temp_c,
        }


# Default immutable Antarctic Operational Safety Policy instance
DEFAULT_SAFETY_POLICY = SafetyPolicy()
