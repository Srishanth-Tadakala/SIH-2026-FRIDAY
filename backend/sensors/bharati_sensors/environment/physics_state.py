"""Single source of truth for simulated Bharati Station environmental physics.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

ARCHITECTURAL PRINCIPLE:
Sensors observe this state. They do NOT invent their own reality.
Healthy state-bound sensors resolve exclusively from this physical ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Any

from .models import OperatingConditionState


def _relaxation_factor(dt_seconds: float, tau_seconds: float) -> float:
    """Unconditionally stable first-order exponential relaxation factor."""
    if tau_seconds <= 0.0 or dt_seconds <= 0.0:
        return 1.0
    return 1.0 - math.exp(-dt_seconds / tau_seconds)


@dataclass
class WeatherState:
    """Atmospheric meteorological state at Bharati Station (AWS)."""
    ambient_temperature_c: float = -18.0
    relative_humidity_percent: float = 65.0
    atmospheric_pressure_hpa: float = 985.0
    pressure_tendency_hpa_3h: float = -0.2
    wind_speed_mps: float = 12.0
    wind_direction_deg: float = 85.0
    wind_gust_mps: float = 16.5
    wind_gust_direction_deg: float = 85.0
    visibility_m: float = 15000.0
    precipitation_rate_mm_h: float = 0.5
    dew_point_c: float = -22.5
    air_density_kg_m3: float = 1.34

    # Targets for smooth relaxation
    _target_temp_c: float = -18.0
    _target_rh_percent: float = 65.0
    _target_pressure_hpa: float = 985.0
    _target_wind_mps: float = 12.0
    _target_wind_deg: float = 85.0
    _target_precip_rate_mm_h: float = 0.5


@dataclass
class RadiationState:
    """Solar and thermal infrared radiation and atmospheric optics."""
    shortwave_downwelling_w_m2: float = 150.0
    longwave_downwelling_w_m2: float = 210.0
    net_radiation_w_m2: float = -25.0
    uv_index: float = 2.0
    aerosol_optical_depth_500nm: float = 0.035
    is_daylight: bool = True
    solar_availability_percent: float = 25.0

    _target_sw_w_m2: float = 150.0


@dataclass
class AerosolState:
    """Atmospheric particulate, optical scattering/absorption, and trace gases."""
    black_carbon_ng_m3: float = 15.0
    pm10_ug_m3: float = 3.5
    particle_number_cm3: float = 450.0
    mean_particle_size_nm: float = 65.0
    scattering_coeff_Mm_inv: float = 1.8
    absorption_coeff_Mm_inv: float = 0.12
    column_aod: float = 0.032
    carbon_monoxide_ppb: float = 45.0
    nitrogen_oxides_ppb: float = 1.2
    sulfur_dioxide_ppb: float = 0.3
    surface_ozone_ppb: float = 22.0
    air_quality_index: float = 98.0


@dataclass
class SnowState:
    """Local station perimeter snowpack state (location_scope="LOCAL_STATION")."""
    snow_depth_m: float = 0.85
    snow_temperature_c: float = -16.0
    snow_density_kg_m3: float = 380.0
    accumulation_rate_mm_h: float = 0.2
    drift_mass_flux_g_m2_s: float = 1.5


@dataclass
class SeaIceState:
    """Coastal study area fast ice and pack ice (location_scope="COASTAL")."""
    ice_present: bool = True
    ice_thickness_m: float = 1.65
    ice_concentration_percent: float = 85.0
    ice_surface_temperature_c: float = -14.5
    ice_drift_speed_mps: float = 0.25
    distance_to_open_water_km: float = 18.0


@dataclass
class OceanState:
    """Coastal Prydz Bay environmental context (location_scope="COASTAL_CONTEXT")."""
    water_temperature_c: float = -1.6
    salinity_psu: float = 34.2
    conductivity_ms_cm: float = 29.5
    pressure_dbar: float = 15.0
    current_speed_mps: float = 0.22
    current_direction_deg: float = 240.0
    significant_wave_height_m: float = 0.6
    wave_period_s: float = 6.5
    sea_level_anomaly_m: float = 0.15
    turbidity_ntu: float = 1.2


@dataclass
class EnvironmentalWaterState:
    """Natural proglacial meltwater lake limnology (e.g. Lake Progress)."""
    water_temperature_c: float = 3.2
    ph: float = 7.4
    conductivity_us_cm: float = 45.0
    turbidity_ntu: float = 0.8
    dissolved_oxygen_mg_l: float = 12.5
    contamination_index: float = 2.0
    hydrocarbon_trace_ppb: float = 0.05


@dataclass
class AtmosphericElectricityState:
    """Atmospheric potential gradient, air-earth current, and ion conductivities."""
    electric_field_v_m: float = 85.0
    air_earth_current_pa_m2: float = 2.1
    maxwell_current_pa_m2: float = 2.3
    positive_conductivity_fs_m: float = 11.5
    negative_conductivity_fs_m: float = 9.8
    system_status: str = "OPERATIONAL"


@dataclass
class IonosphereState:
    """Ionospheric TEC and scintillation observation context."""
    total_electron_content_tecu: float = 12.4
    scintillation_s4: float = 0.08
    phase_scintillation_rad: float = 0.12
    receiver_status: str = "LOCKED"


@dataclass
class SkyState:
    """All-sky camera optical observations, cloud cover, and auroral emissions."""
    cloud_cover_percent: float = 35.0
    auroral_intensity_kr: float = 2.5
    camera_status: str = "ACTIVE"


@dataclass
class SeismicState:
    """Broadband seismological observations at Bharati Geodetic Observatory."""
    ground_acceleration_um_s2: float = 0.8
    particle_velocity_um_s: float = 0.05
    event_detected: bool = False


@dataclass
class DerivedEnvironmentalState:
    """Deterministic derived indicators and explainable operating condition."""
    dew_point_c: float = -22.5
    air_density_kg_m3: float = 1.34
    wind_chill_c: float = -29.8
    cold_stress_risk: float = 35.0
    blizzard_risk: float = 12.0
    freeze_risk: float = 40.0
    snow_access_risk: float = 15.0
    ice_access_risk: float = 20.0
    solar_availability_percent: float = 25.0
    visibility_risk: float = 8.0
    environmental_risk: float = 24.0
    operating_condition: OperatingConditionState = field(
        default_factory=lambda: OperatingConditionState(
            level="GREEN",
            reasons=["NOMINAL_CONDITIONS"],
            contributing_indicators={"blizzard_risk": 12.0, "wind_speed": 12.0, "temperature": -18.0},
        )
    )

    @property
    def operating_condition_summary(self) -> str:
        return self.operating_condition.summary()


class BharatiEnvironmentPhysicsState:
    """Coupled physical simulation state for Bharati Station Environment."""

    def __init__(self, seed: int | None = 42) -> None:
        self.rng = random.Random(seed)
        self.simulation_time_seconds: float = 0.0
        self.active_scenario: str = "NORMAL"

        # Domain states
        self.weather = WeatherState()
        self.radiation = RadiationState()
        self.aerosol = AerosolState()
        self.snow = SnowState()
        self.sea_ice = SeaIceState()
        self.ocean = OceanState()
        self.environmental_water = EnvironmentalWaterState()
        self.atmospheric_electricity = AtmosphericElectricityState()
        self.ionosphere = IonosphereState()
        self.sky = SkyState()
        self.seismic = SeismicState()
        self.derived = DerivedEnvironmentalState()

        # Pressure tracking history for tendency
        self._pressure_history: list[tuple[float, float]] = [(0.0, self.weather.atmospheric_pressure_hpa)]

        # Initial evaluation of derived metrics
        self._recompute_all_derived()

    # =========================================================================
    # STATE RESOLUTION BY PATH
    # =========================================================================
    def get_value_by_path(self, path: str) -> Any:
        """Resolve a dotted state path directly into the physical state."""
        parts = path.split(".")
        current: Any = self
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise AttributeError(f"Path '{path}' could not be resolved on {type(current).__name__} (missing '{part}')")
        return current

    # =========================================================================
    # SCENARIOS
    # =========================================================================
    def set_scenario_normal(self) -> None:
        """Set nominal polar winter conditions."""
        self.active_scenario = "NORMAL"
        self.weather._target_temp_c = -18.0
        self.weather._target_rh_percent = 65.0
        self.weather._target_pressure_hpa = 985.0
        self.weather._target_wind_mps = 12.0
        self.weather._target_wind_deg = 85.0
        self.weather._target_precip_rate_mm_h = 0.5
        self.radiation._target_sw_w_m2 = 150.0
        self.radiation.is_daylight = True
        self.snow.accumulation_rate_mm_h = 0.2
        self.sky.cloud_cover_percent = 35.0
        self.seismic.event_detected = False

    def set_scenario_extreme_cold(self) -> None:
        """Set extreme Antarctic cold katabatic plunge."""
        self.active_scenario = "EXTREME_COLD"
        self.weather._target_temp_c = -38.5
        self.weather._target_rh_percent = 50.0
        self.weather._target_pressure_hpa = 998.0
        self.weather._target_wind_mps = 18.0
        self.weather._target_wind_deg = 110.0
        self.weather._target_precip_rate_mm_h = 0.0
        self.radiation._target_sw_w_m2 = 80.0
        self.radiation.is_daylight = True
        self.snow.accumulation_rate_mm_h = 0.0
        self.sky.cloud_cover_percent = 15.0
        self.seismic.event_detected = False

    def set_scenario_high_wind(self) -> None:
        """Set high katabatic storm wind condition."""
        self.active_scenario = "HIGH_WIND"
        self.weather._target_temp_c = -15.0
        self.weather._target_rh_percent = 70.0
        self.weather._target_pressure_hpa = 970.0
        self.weather._target_wind_mps = 24.5
        self.weather._target_wind_deg = 80.0
        self.weather._target_precip_rate_mm_h = 2.0
        self.radiation._target_sw_w_m2 = 50.0
        self.sky.cloud_cover_percent = 85.0
        self.seismic.event_detected = False

    def set_scenario_blizzard(self) -> None:
        """Set severe Antarctic blizzard conditions (wind >= 30 m/s, zero visibility)."""
        self.active_scenario = "BLIZZARD"
        self.weather._target_temp_c = -26.0
        self.weather._target_rh_percent = 92.0
        self.weather._target_pressure_hpa = 952.0  # Sharp pressure drop
        self.weather._target_wind_mps = 34.0       # Severe gale
        self.weather._target_wind_deg = 75.0
        self.weather._target_precip_rate_mm_h = 18.0
        self.radiation._target_sw_w_m2 = 10.0
        self.sky.cloud_cover_percent = 100.0
        self.seismic.event_detected = False

    def set_scenario_rapid_weather_change(self) -> None:
        """Set rapid coastal weather front transit."""
        self.active_scenario = "RAPID_WEATHER_CHANGE"
        self.weather._target_temp_c = -8.0
        self.weather._target_rh_percent = 85.0
        self.weather._target_pressure_hpa = 965.0
        self.weather._target_wind_mps = 20.0
        self.weather._target_wind_deg = 140.0
        self.weather._target_precip_rate_mm_h = 6.0
        self.radiation._target_sw_w_m2 = 30.0
        self.sky.cloud_cover_percent = 90.0
        self.seismic.event_detected = False

    def apply_scenario(self, scenario_name: str) -> None:
        """Apply scenario by name."""
        name = scenario_name.strip().upper()
        if name == "NORMAL":
            self.set_scenario_normal()
        elif name == "EXTREME_COLD":
            self.set_scenario_extreme_cold()
        elif name == "HIGH_WIND":
            self.set_scenario_high_wind()
        elif name == "BLIZZARD":
            self.set_scenario_blizzard()
        elif name == "RAPID_WEATHER_CHANGE":
            self.set_scenario_rapid_weather_change()
        else:
            raise ValueError(f"Unknown environmental scenario: {scenario_name}")

    # =========================================================================
    # SIMULATION STEPPING & COUPLING
    # =========================================================================
    def step(self, dt_seconds: float) -> None:
        """Advance physical simulation by dt_seconds."""
        if dt_seconds <= 0.0:
            return

        self.simulation_time_seconds += dt_seconds

        # 1. Weather relaxation toward active targets
        rf_fast = _relaxation_factor(dt_seconds, 60.0)
        rf_med = _relaxation_factor(dt_seconds, 180.0)
        rf_slow = _relaxation_factor(dt_seconds, 600.0)

        prev_pressure = self.weather.atmospheric_pressure_hpa

        self.weather.ambient_temperature_c += rf_med * (self.weather._target_temp_c - self.weather.ambient_temperature_c)
        self.weather.relative_humidity_percent += rf_med * (self.weather._target_rh_percent - self.weather.relative_humidity_percent)
        self.weather.atmospheric_pressure_hpa += rf_slow * (self.weather._target_pressure_hpa - self.weather.atmospheric_pressure_hpa)
        self.weather.wind_speed_mps += rf_fast * (self.weather._target_wind_mps - self.weather.wind_speed_mps)
        self.weather.wind_direction_deg += rf_med * (self.weather._target_wind_deg - self.weather.wind_direction_deg)
        self.weather.precipitation_rate_mm_h += rf_fast * (self.weather._target_precip_rate_mm_h - self.weather.precipitation_rate_mm_h)

        # Wind gust is physically coupled: peak gust >= sustained wind speed
        gust_mult = 1.35 + 0.05 * (self.rng.random() - 0.5)
        self.weather.wind_gust_mps = max(self.weather.wind_speed_mps, round(self.weather.wind_speed_mps * gust_mult, 2))
        self.weather.wind_gust_direction_deg = (self.weather.wind_direction_deg + (self.rng.random() - 0.5) * 10.0) % 360.0

        # Pressure tendency tracking (over simulated hours)
        self._pressure_history.append((self.simulation_time_seconds, self.weather.atmospheric_pressure_hpa))
        # Keep 3 hours of history (10800s)
        cutoff = self.simulation_time_seconds - 10800.0
        self._pressure_history = [(t, p) for t, p in self._pressure_history if t >= cutoff]
        if len(self._pressure_history) >= 2:
            oldest_t, oldest_p = self._pressure_history[0]
            dt_h = max(0.01, (self.simulation_time_seconds - oldest_t) / 3600.0)
            # Extrapolate or normalize to 3-hour tendency: dP/dt * 3h
            self.weather.pressure_tendency_hpa_3h = round((self.weather.atmospheric_pressure_hpa - oldest_p) * (3.0 / dt_h), 2)
        else:
            self.weather.pressure_tendency_hpa_3h = round((self.weather.atmospheric_pressure_hpa - prev_pressure) * 3.0, 2)

        # 2. Radiation relaxation and daylight coherence
        self.radiation.shortwave_downwelling_w_m2 += rf_fast * (self.radiation._target_sw_w_m2 - self.radiation.shortwave_downwelling_w_m2)
        if not self.radiation.is_daylight:
            self.radiation.shortwave_downwelling_w_m2 = 0.0
            self.radiation.uv_index = 0.0
        else:
            self.radiation.uv_index = round(max(0.0, self.radiation.shortwave_downwelling_w_m2 / 75.0), 1)

        # Longwave and net radiation balance
        t_kelvin = self.weather.ambient_temperature_c + 273.15
        sigma = 5.670374e-8
        blackbody_lw = sigma * (t_kelvin ** 4)
        emissivity = 0.72 + 0.002 * (self.weather.relative_humidity_percent - 50.0)
        self.radiation.longwave_downwelling_w_m2 = round(emissivity * blackbody_lw, 1)
        albedo = 0.82  # Antarctic snow cover albedo
        sw_net = (1.0 - albedo) * self.radiation.shortwave_downwelling_w_m2
        lw_net = self.radiation.longwave_downwelling_w_m2 - blackbody_lw
        self.radiation.net_radiation_w_m2 = round(sw_net + lw_net, 1)

        # 3. Snow and blowing snow flux physics
        # Blowing snow drift mass flux exponentially increases once wind exceeds ~10 m/s threshold
        if self.weather.wind_speed_mps > 10.0:
            excess_wind = self.weather.wind_speed_mps - 10.0
            self.snow.drift_mass_flux_g_m2_s = round(min(150.0, 0.045 * (excess_wind ** 2.2)), 2)
        else:
            self.snow.drift_mass_flux_g_m2_s = 0.05

        # Horizontal visibility is reduced by blowing snow and snowfall
        # Clean air visibility ~18,000m; blowing snow rapidly causes severe whiteout (< 300m)
        attenuation = 1.0 + (0.75 * self.snow.drift_mass_flux_g_m2_s) + (2.2 * self.weather.precipitation_rate_mm_h)
        self.weather.visibility_m = round(max(25.0, min(35000.0, 18000.0 / attenuation)), 1)

        # Snow accumulation and redistribution
        net_accum_rate_m_s = (self.weather.precipitation_rate_mm_h * 0.001) / 3600.0  # mm/h to m/s
        self.snow.snow_depth_m = max(0.0, round(self.snow.snow_depth_m + (net_accum_rate_m_s * dt_seconds), 4))
        self.snow.snow_temperature_c += rf_slow * (self.weather.ambient_temperature_c - self.snow.snow_temperature_c)

        # 4. Sea Ice & Ocean Coupling (slower thermal inertia)
        self.sea_ice.ice_surface_temperature_c += rf_slow * (self.weather.ambient_temperature_c - self.sea_ice.ice_surface_temperature_c)
        if self.active_scenario == "EXTREME_COLD":
            self.sea_ice.ice_thickness_m = min(4.5, round(self.sea_ice.ice_thickness_m + 0.00001 * dt_seconds, 4))
            self.sea_ice.ice_concentration_percent = min(100.0, round(self.sea_ice.ice_concentration_percent + 0.001 * dt_seconds, 1))
        elif self.active_scenario == "BLIZZARD":
            self.sea_ice.ice_drift_speed_mps = round(min(3.5, 0.04 * self.weather.wind_speed_mps), 2)
            self.ocean.significant_wave_height_m = round(min(6.5, 0.12 * self.weather.wind_speed_mps), 2)
            self.ocean.current_speed_mps = round(min(1.8, 0.025 * self.weather.wind_speed_mps), 2)
        else:
            self.sea_ice.ice_drift_speed_mps = 0.25
            self.ocean.significant_wave_height_m = 0.6
            self.ocean.current_speed_mps = 0.22

        # 5. Aerosol coupling with katabatic winds
        # High winds flush station perimeter, dispersing local plumes
        if self.weather.wind_speed_mps > 15.0:
            self.aerosol.black_carbon_ng_m3 = max(2.0, round(self.aerosol.black_carbon_ng_m3 * 0.95, 2))
            self.aerosol.carbon_monoxide_ppb = max(25.0, round(self.aerosol.carbon_monoxide_ppb * 0.98, 1))
            self.aerosol.nitrogen_oxides_ppb = max(0.3, round(self.aerosol.nitrogen_oxides_ppb * 0.95, 2))
        else:
            self.aerosol.black_carbon_ng_m3 = round(15.0 + 2.0 * math.sin(self.simulation_time_seconds / 300.0), 2)
            self.aerosol.carbon_monoxide_ppb = round(45.0 + 3.0 * math.sin(self.simulation_time_seconds / 500.0), 1)
            self.aerosol.nitrogen_oxides_ppb = round(1.2 + 0.2 * math.cos(self.simulation_time_seconds / 400.0), 2)

        # 6. Atmospheric Electricity
        # Fair weather field ~85 V/m; blizzard and blowing snow charges reverse and multiply electric field
        if self.snow.drift_mass_flux_g_m2_s > 10.0:
            self.atmospheric_electricity.electric_field_v_m = round(min(1200.0, 85.0 + (12.0 * self.snow.drift_mass_flux_g_m2_s)), 1)
            self.atmospheric_electricity.air_earth_current_pa_m2 = round(min(22.0, 2.1 + (0.25 * self.snow.drift_mass_flux_g_m2_s)), 2)
        else:
            self.atmospheric_electricity.electric_field_v_m = round(85.0 + 5.0 * math.sin(self.simulation_time_seconds / 200.0), 1)
            self.atmospheric_electricity.air_earth_current_pa_m2 = round(2.1 + 0.1 * math.sin(self.simulation_time_seconds / 150.0), 2)
        self.atmospheric_electricity.maxwell_current_pa_m2 = round(self.atmospheric_electricity.air_earth_current_pa_m2 * 1.08, 2)

        # Recompute all deterministic derived metrics
        self._recompute_all_derived()

    # =========================================================================
    # DETERMINISTIC DERIVED METRICS
    # =========================================================================
    def _recompute_all_derived(self) -> None:
        """Compute all derived indicators deterministically from the physical state."""
        t = self.weather.ambient_temperature_c
        rh = max(0.1, min(100.0, self.weather.relative_humidity_percent))
        p = self.weather.atmospheric_pressure_hpa
        v = max(0.0, self.weather.wind_speed_mps)

        # 1. Magnus-Tetens Dew Point
        # alpha = (17.27 * T) / (237.7 + T) + ln(RH / 100)
        # T_dew = (237.7 * alpha) / (17.27 - alpha)
        alpha = ((17.27 * t) / (237.7 + t)) + math.log(rh / 100.0)
        dew_point = (237.7 * alpha) / (17.27 - alpha)
        # Physical constraint: dew point cannot exceed ambient temperature
        dew_point = min(t, dew_point)
        self.weather.dew_point_c = round(dew_point, 2)
        self.derived.dew_point_c = self.weather.dew_point_c

        # 2. CIPM Moist Air Density
        # Saturation vapor pressure over liquid/ice approximation
        p_sat = 6.1121 * math.exp((17.502 * t) / (240.97 + t))  # hPa
        p_v = p_sat * (rh / 100.0)  # vapor pressure hPa
        p_d = max(100.0, p - p_v)    # dry air pressure hPa
        r_d = 287.058  # J / (kg * K)
        r_v = 461.495  # J / (kg * K)
        t_k = t + 273.15
        air_density = ((p_d * 100.0) / (r_d * t_k)) + ((p_v * 100.0) / (r_v * t_k))
        self.weather.air_density_kg_m3 = round(air_density, 3)
        self.derived.air_density_kg_m3 = self.weather.air_density_kg_m3

        # 3. Antarctic Wind Chill (JAG/TI standard formula)
        # WCT = 13.12 + 0.6215 * T - 11.37 * V_kmh^0.16 + 0.3965 * T * V_kmh^0.16
        v_kmh = v * 3.6
        if v_kmh > 4.8:
            v_pow = v_kmh ** 0.16
            wind_chill = 13.12 + (0.6215 * t) - (11.37 * v_pow) + (0.3965 * t * v_pow)
        else:
            wind_chill = t
        self.derived.wind_chill_c = round(wind_chill, 2)

        # 4. Cold Stress Risk (0 - 100)
        # Combines wind chill severity and ambient solar offset
        # Baseline: at WCT = 0°C -> 0, at WCT = -20°C -> 40, at WCT = -40°C -> 80, at WCT <= -55°C -> 100
        solar_warming = min(15.0, self.radiation.shortwave_downwelling_w_m2 / 40.0)
        effective_wct = wind_chill + (solar_warming * 0.5)
        if effective_wct >= 5.0:
            cold_stress = 0.0
        elif effective_wct <= -55.0:
            cold_stress = 100.0
        else:
            cold_stress = ((5.0 - effective_wct) / 60.0) * 100.0
        self.derived.cold_stress_risk = round(max(0.0, min(100.0, cold_stress)), 1)

        # 5. Blizzard Risk (0 - 100)
        # Physically incorporates wind, gust, blowing snow, visibility, and pressure tendency
        wind_sev = max(0.0, (v - 12.0) / 18.0)  # ramps up as wind exceeds 12 m/s
        gust_sev = max(0.0, (self.weather.wind_gust_mps - 18.0) / 18.0)
        drift_sev = min(1.0, self.snow.drift_mass_flux_g_m2_s / 20.0)
        vis_sev = max(0.0, (1500.0 - self.weather.visibility_m) / 1500.0)
        press_tend_sev = max(0.0, -self.weather.pressure_tendency_hpa_3h / 4.0)  # negative tendency (falling pressure)

        blizzard_score = 100.0 * (
            (0.30 * wind_sev) +
            (0.20 * gust_sev) +
            (0.25 * drift_sev) +
            (0.15 * vis_sev) +
            (0.10 * press_tend_sev)
        )
        self.derived.blizzard_risk = round(max(0.0, min(100.0, blizzard_score)), 1)

        # 6. External Infrastructure Freeze Risk (0 - 100)
        # Function of sub-zero temperature and convective wind velocity
        if t >= 0.0:
            freeze_score = 0.0
        else:
            subzero_mag = min(40.0, -t)
            wind_convection = 1.0 + min(2.0, v / 15.0)
            freeze_score = (subzero_mag / 40.0) * 60.0 * (wind_convection / 1.8)
        self.derived.freeze_risk = round(max(0.0, min(100.0, freeze_score)), 1)

        # 7. Snow Access Risk (0 - 100)
        # Ground snowpack depth + blowing snow drift accumulation obstruction
        depth_score = min(60.0, (self.snow.snow_depth_m / 2.5) * 60.0)
        drift_score = min(40.0, (self.snow.drift_mass_flux_g_m2_s / 25.0) * 40.0)
        self.derived.snow_access_risk = round(depth_score + drift_score, 1)

        # 8. Sea Ice Access Risk (0 - 100)
        # Evaluates fast-ice trafficability for heavy vehicles (safe when thick, cold, dense)
        if not self.sea_ice.ice_present:
            ice_risk = 100.0
        else:
            # Thickness < 1.0m is unsafe for heavy tracked vehicles; > 1.8m is safe
            thick_penalty = max(0.0, (1.8 - self.sea_ice.ice_thickness_m) / 1.8) * 50.0
            conc_penalty = max(0.0, (100.0 - self.sea_ice.ice_concentration_percent) / 100.0) * 30.0
            temp_penalty = max(0.0, (self.sea_ice.ice_surface_temperature_c + 5.0) / 7.0) * 20.0
            ice_risk = thick_penalty + conc_penalty + temp_penalty
        self.derived.ice_access_risk = round(max(0.0, min(100.0, ice_risk)), 1)

        # 9. Solar Generation Availability Factor (%)
        # Clear-sky potential factor (0% at night, up to 100% in bright sun)
        if not self.radiation.is_daylight or self.radiation.shortwave_downwelling_w_m2 <= 0.0:
            solar_avail = 0.0
        else:
            solar_avail = min(100.0, (self.radiation.shortwave_downwelling_w_m2 / 800.0) * 100.0)
        self.radiation.solar_availability_percent = round(solar_avail, 1)
        self.derived.solar_availability_percent = self.radiation.solar_availability_percent

        # 10. Visibility Risk (0 - 100)
        if self.weather.visibility_m >= 5000.0:
            vis_risk = 0.0
        else:
            vis_risk = ((5000.0 - self.weather.visibility_m) / 5000.0) * 100.0
        self.derived.visibility_risk = round(max(0.0, min(100.0, vis_risk)), 1)

        # 11. Clean Air Purity Index (%)
        # Evaluates black carbon, PM10, CO, and NOx against pristine Antarctic baseline
        bc_pen = min(40.0, (self.aerosol.black_carbon_ng_m3 / 100.0) * 40.0)
        pm_pen = min(30.0, (self.aerosol.pm10_ug_m3 / 25.0) * 30.0)
        gas_pen = min(30.0, ((self.aerosol.carbon_monoxide_ppb - 30.0) / 100.0) * 30.0) if self.aerosol.carbon_monoxide_ppb > 30.0 else 0.0
        air_quality = max(0.0, 100.0 - (bc_pen + pm_pen + gas_pen))
        self.aerosol.air_quality_index = round(air_quality, 1)

        # 12. Composite Station Environmental Threat Score (0 - 100)
        composite_risk = (
            (0.35 * self.derived.blizzard_risk) +
            (0.25 * self.derived.cold_stress_risk) +
            (0.25 * self.derived.freeze_risk) +
            (0.15 * self.derived.visibility_risk)
        )
        self.derived.environmental_risk = round(max(0.0, min(100.0, composite_risk)), 1)

        # 13. Explainable Operating Condition
        reasons: list[str] = []
        indicators: dict[str, float] = {
            "wind_speed_mps": round(v, 2),
            "wind_gust_mps": round(self.weather.wind_gust_mps, 2),
            "visibility_m": round(self.weather.visibility_m, 1),
            "ambient_temp_c": round(t, 2),
            "blizzard_risk": self.derived.blizzard_risk,
            "cold_stress_risk": self.derived.cold_stress_risk,
            "freeze_risk": self.derived.freeze_risk,
        }

        # Level determination with explicit causation
        if self.derived.blizzard_risk >= 70.0 or v >= 30.0 or self.weather.visibility_m < 300.0:
            level = "BLACK"
            if self.derived.blizzard_risk >= 70.0:
                reasons.append("BLIZZARD_CONDITIONS")
            if v >= 30.0:
                reasons.append("SEVERE_GALE_FORCE_WIND")
            if self.weather.visibility_m < 300.0:
                reasons.append("NEAR_ZERO_VISIBILITY")
        elif v >= 22.0 or self.weather.visibility_m < 1000.0 or t < -32.0 or self.derived.blizzard_risk >= 45.0:
            level = "RED"
            if v >= 22.0:
                reasons.append("HIGH_WIND")
            if self.weather.visibility_m < 1000.0:
                reasons.append("LOW_VISIBILITY")
            if t < -32.0:
                reasons.append("EXTREME_COLD")
            if self.derived.blizzard_risk >= 45.0:
                reasons.append("ELEVATED_BLIZZARD_RISK")
        elif v >= 15.0 or self.weather.visibility_m < 2000.0 or t < -25.0 or self.derived.blizzard_risk >= 25.0:
            level = "YELLOW"
            if v >= 15.0:
                reasons.append("MODERATE_WIND")
            if self.weather.visibility_m < 2000.0:
                reasons.append("REDUCED_VISIBILITY")
            if t < -25.0:
                reasons.append("COLD_TEMPERATURE")
            if self.derived.blizzard_risk >= 25.0:
                reasons.append("MODERATE_BLIZZARD_RISK")
        else:
            level = "GREEN"
            reasons.append("NOMINAL_CONDITIONS")

        self.derived.operating_condition = OperatingConditionState(
            level=level,
            reasons=reasons,
            contributing_indicators=indicators,
        )
