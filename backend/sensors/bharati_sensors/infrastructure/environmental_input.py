"""External Environmental Input interface for Bharati Infrastructure.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

ARCHITECTURAL PRINCIPLE:
Infrastructure does NOT own or invent the weather sensor layer.
The Environment domain eventually provides these atmospheric observations.
Infrastructure Physics consumes this interface as external driving boundary conditions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnvironmentalInput:
    """External ambient environmental conditions driving station infrastructure physics."""
    ambient_temperature_c: float = -18.0  # Antarctic coastal ambient (-35 to +5 °C)
    wind_speed_ms: float = 12.0  # Wind speed in m/s (0 to 45 m/s)
    wind_direction_deg: float = 85.0  # Easterly / katabatic prevailing
    solar_radiation_w_m2: float = 150.0  # Global horizontal irradiance
    atmospheric_pressure_hpa: float = 985.0  # Antarctic sea-level barometric pressure
    relative_humidity_percent: float = 65.0  # Ambient relative humidity
    snow_accumulation_rate_mm_h: float = 0.5  # Snowfall / drift accumulation rate

    def apply_extreme_cold_blizzard(self) -> None:
        """Helper to simulate an extreme Antarctic cold blizzard event."""
        self.ambient_temperature_c = -32.5
        self.wind_speed_ms = 34.0
        self.solar_radiation_w_m2 = 10.0
        self.snow_accumulation_rate_mm_h = 15.0
        self.atmospheric_pressure_hpa = 960.0

    def apply_normal_summer_condition(self) -> None:
        """Helper to simulate mild polar summer conditions."""
        self.ambient_temperature_c = -2.0
        self.wind_speed_ms = 6.0
        self.solar_radiation_w_m2 = 450.0
        self.snow_accumulation_rate_mm_h = 0.0
        self.atmospheric_pressure_hpa = 995.0
