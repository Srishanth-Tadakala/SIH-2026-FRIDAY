"""Physical coherence state model for Bharati Station Infrastructure Systems.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

CAUSAL STRUCTURE & SOURCE OF TRUTH:
All infrastructure sensors observe this unified deterministic physical reality.
Values are coupled through thermodynamic, hydraulic, biological, and aerodynamic relationships.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .config import (
    BUILDING_HEAT_LOSS_COEFF_W_K,
    BUILDING_TARGET_TEMP_C,
    COLD_ROOM_TARGET_TEMP_C,
    DEEP_FREEZER_TARGET_TEMP_C,
    FRESH_WATER_TANK_CAPACITY_L,
    NOMINAL_STATION_OCCUPANCY,
    PER_CAPITA_WATER_CONSUMPTION_L_DAY,
    RO_DESIGN_PERMEATE_FLOW_LPH,
    SEAWATER_INTAKE_NOMINAL_FLOW_LPH,
    WASTEWATER_AERATION_TANK_CAPACITY_L,
)
from .environmental_input import EnvironmentalInput


@dataclass
class BuildingPhysicalState:
    """Thermal envelope, zones, and human occupancy state."""
    temp_living_c: float = 21.2
    humidity_living_pct: float = 44.5
    temp_lab_c: float = 20.8
    humidity_lab_pct: float = 42.0
    temp_technical_c: float = 18.5
    occupancy_count: int = NOMINAL_STATION_OCCUPANCY
    envelope_temp_north_c: float = -12.5
    envelope_temp_south_c: float = -16.0
    roof_snow_load_kpa: float = 1.2
    main_airlock_door_open: bool = False


@dataclass
class StructuralPhysicalState:
    """Superstructure, elevated pillar stilts, and bedrock foundation displacement."""
    building_tilt_x_mrad: float = 0.22  # East-West tilt
    building_tilt_y_mrad: float = -0.15  # North-South tilt
    pillar_01_strain_ustrain: float = 145.0  # Outer stilt strain
    pillar_43_strain_ustrain: float = 162.0  # Center core stilt strain
    pillar_86_strain_ustrain: float = 138.0  # Perimeter stilt strain
    foundation_disp_mm: float = 0.42  # Bedrock anchor displacement
    vibration_rms_mm_s: float = 1.15  # Wind-induced vibration velocity
    joint_disp_mm: float = 1.85  # Prefab module thermal dilation


@dataclass
class HVACPhysicalState:
    """Air handling units, mechanical ventilation, and indoor air quality."""
    # AHU-01 (Residential & Common)
    ahu01_supply_temp_c: float = 22.4
    ahu01_return_temp_c: float = 20.2
    ahu01_supply_pressure_pa: float = 320.0
    ahu01_return_pressure_pa: float = -80.0
    ahu01_filter_dp_pa: float = 125.0
    ahu01_airflow_m3_h: float = 3850.0
    ahu01_fan_running: bool = True
    ahu01_fan_speed_pct: float = 75.0
    ahu01_heating_valve_pct: float = 45.0
    ahu01_fresh_air_damper_pct: float = 25.0
    
    # AHU-02 (Laboratories & Technical)
    ahu02_supply_temp_c: float = 21.8
    ahu02_return_temp_c: float = 19.8
    ahu02_supply_pressure_pa: float = 340.0
    ahu02_return_pressure_pa: float = -95.0
    ahu02_filter_dp_pa: float = 110.0
    ahu02_airflow_m3_h: float = 4200.0
    ahu02_fan_running: bool = True
    ahu02_fan_speed_pct: float = 80.0
    ahu02_heating_valve_pct: float = 48.0
    ahu02_fresh_air_damper_pct: float = 30.0
    
    # Gas concentrations (NDIR CO2 & Electrochemical CO)
    co2_living_ppm: float = 580.0
    co_living_ppm: float = 1.2
    co2_lab_ppm: float = 510.0
    co_lab_ppm: float = 0.8
    
    # Auxiliary fans
    exhaust_fan_running: bool = True
    humidifier_active: bool = True


@dataclass
class WaterPhysicalState:
    """Reverse Osmosis seawater desalination, storage reservoir, and distribution."""
    # Seawater Intake
    seawater_intake_flow_lph: float = SEAWATER_INTAKE_NOMINAL_FLOW_LPH
    seawater_intake_pressure_bar: float = 3.2
    seawater_intake_temp_c: float = 1.8
    intake_pump_running: bool = True
    
    # RO Desalination (Mass conservation: Feed ~ Permeate + Reject + Loss)
    ro_feed_pressure_bar: float = 55.0
    ro_permeate_flow_lph: float = RO_DESIGN_PERMEATE_FLOW_LPH
    ro_reject_flow_lph: float = 880.0
    ro_permeate_conductivity_us_cm: float = 240.0
    ro_system_status: str = "PRODUCING"
    
    # Storage Reservoir (Volume & Derived Level %)
    potable_tank_capacity_l: float = FRESH_WATER_TANK_CAPACITY_L
    potable_tank_volume_l: float = 20500.0
    potable_tank_level_pct: float = 82.0
    potable_tank_temp_c: float = 14.2
    
    # Distribution & Domestic Service
    distribution_pressure_bar: float = 3.8
    consumption_flow_lph: float = (NOMINAL_STATION_OCCUPANCY * PER_CAPITA_WATER_CONSUMPTION_L_DAY) / 24.0  # ~110 L/h
    uv_system_active: bool = True
    residual_chlorine_ppm: float = 0.65
    domestic_hot_water_temp_c: float = 58.5
    calorifier_backup_heater_on: bool = False


@dataclass
class WastewaterPhysicalState:
    """Collection sumps, MBR ultrafiltration treatment, and discharge quality."""
    # Influent sumps (coupled directly to station water consumption)
    inlet_flow_lph: float = 95.0
    grey_sump_level_pct: float = 48.0
    black_sump_level_pct: float = 35.0
    galley_sump_level_pct: float = 40.0
    
    # Biological aeration basin
    aeration_basin_capacity_l: float = WASTEWATER_AERATION_TANK_CAPACITY_L
    aeration_basin_level_pct: float = 72.0
    dissolved_oxygen_mg_l: float = 2.8
    aeration_blower_running: bool = True
    
    # Membrane Bio-Reactor (MBR) Ultrafiltration
    membrane_tmp_bar: float = 0.25  # Trans-membrane pressure (0.1 to 1.2 bar)
    membrane_fouling_factor: float = 1.0  # 1.0 clean, >1.5 fouled
    effluent_discharge_flow_lph: float = 92.0
    permeate_pump_running: bool = True
    treatment_mode: str = "TREATING"
    
    # Effluent Chemical Quality (Dynamically driven by aeration and membrane condition)
    effluent_cod_mg_l: float = 42.0
    effluent_bod_mg_l: float = 8.5
    effluent_ammonia_mg_l: float = 3.2
    effluent_ph: float = 7.4
    effluent_temp_c: float = 16.0
    
    # Residuals & Discharge
    sludge_holding_level_pct: float = 28.0
    outfall_valve_open: bool = True


@dataclass
class FirePhysicalState:
    """Combustion physics, thermal rise, optical smoke density, and damper interlocks."""
    # Zone 1 (Residential)
    z01_smoke_obs_pct: float = 0.0
    z01_temp_c: float = 21.2
    z01_alarm_status: str = "NORMAL"
    z01_damper_open: bool = True
    
    # Zone 2 (Laboratories)
    z02_smoke_obs_pct: float = 0.0
    z02_temp_c: float = 20.8
    z02_alarm_status: str = "NORMAL"
    z02_damper_open: bool = True
    
    # Zone 3 (Power House)
    z03_smoke_obs_pct: float = 0.0
    z03_temp_c: float = 28.5
    z03_alarm_status: str = "NORMAL"
    z03_damper_open: bool = True
    
    # Zone 4 (Fuel Handling Room)
    z04_smoke_obs_pct: float = 0.0
    z04_temp_c: float = 15.0
    z04_alarm_status: str = "NORMAL"
    z04_damper_open: bool = True
    
    # Physical combustion event flags
    active_fire_zone: str | None = None
    fire_intensity: float = 0.0  # 0.0 to 1.0


@dataclass
class RefrigerationPhysicalState:
    """Cold storage freezers, provisions chillers, and thermodynamic cooling cycles."""
    # Deep Freeze Room (Simulation Target Setpoint -22.0°C)
    frz01_target_temp_c: float = DEEP_FREEZER_TARGET_TEMP_C
    frz01_temp_c: float = DEEP_FREEZER_TARGET_TEMP_C
    frz01_evap_temp_c: float = -28.0
    frz01_cond_temp_c: float = 38.0
    frz01_suction_pressure_bar: float = 1.6
    frz01_discharge_pressure_bar: float = 14.5
    frz01_door_open: bool = False
    frz01_compressor_running: bool = True
    frz01_temp_alarm: str = "NORMAL"
    
    # Cold Provisions Chiller (Simulation Target Setpoint +3.0°C)
    chl01_target_temp_c: float = COLD_ROOM_TARGET_TEMP_C
    chl01_temp_c: float = COLD_ROOM_TARGET_TEMP_C
    chl01_evap_temp_c: float = -3.0
    chl01_cond_temp_c: float = 36.0
    chl01_suction_pressure_bar: float = 3.2
    chl01_discharge_pressure_bar: float = 13.8
    chl01_door_open: bool = False
    chl01_compressor_running: bool = False  # Cycling thermostat
    chl01_temp_alarm: str = "NORMAL"


@dataclass
class PipelinePhysicalState:
    """External utilidors, freeze protection, and containment monitoring."""
    # Potable Water Intake Pipeline
    water01_pipe_temp_c: float = 8.5
    water01_pressure_bar: float = 3.5
    water01_flow_lph: float = 600.0
    water01_trace_heating_on: bool = True
    water01_leak_detected: bool = False
    
    # Bulk Fuel Transfer Pipeline
    fuel01_pipe_temp_c: float = 6.2
    fuel01_pressure_bar: float = 2.8
    fuel01_flow_lph: float = 0.0  # Intermittent transfer
    fuel01_trace_heating_on: bool = True
    fuel01_leak_detected: bool = False
    
    # Hydronic Heating External Return Pipeline
    heat01_pipe_temp_c: float = 48.0
    heat01_pressure_bar: float = 2.4
    heat01_flow_lph: float = 4500.0
    heat01_trace_heating_on: bool = True
    heat01_leak_detected: bool = False
    
    main_isolation_valve_open: bool = True


@dataclass
class EmergencyShelterPhysicalState:
    """Autonomous emergency refuge facility life support state."""
    shelter_temp_c: float = 16.5
    shelter_humidity_pct: float = 40.0
    occupancy_count: int = 0
    generator_status: str = "STANDBY"
    generator_fuel_pct: float = 94.0
    boiler_temp_c: float = 62.0
    water_tank_level_pct: float = 88.0
    smoke_obs_pct: float = 0.0
    co2_ppm: float = 430.0
    co_ppm: float = 0.2
    door_open: bool = False


@dataclass
class SecurityPhysicalState:
    """Access portals, electronic latches, and surveillance integrity."""
    main_airlock_locked: bool = True
    powerhouse_door_open: bool = False
    powerhouse_locked: bool = True
    fuel_farm_gate_open: bool = False
    unauthorized_access_detected: str = "NORMAL"
    cam_01_online: bool = True
    cam_02_online: bool = True
    cam_03_online: bool = True
    emergency_call_active: str = "STANDBY"
    pa_system_healthy: str = "NORMAL"
    key_vault_secure: str = "SECURE"


@dataclass
class BMSPhysicalState:
    """Building Management System automation hardware and satellite backhaul."""
    ddc01_online: str = "ONLINE"
    ddc02_online: str = "ONLINE"
    fieldbus_gateway_online: str = "ONLINE"
    historian_logging: str = "LOGGING"
    points_online_count: float = 982.0
    points_stale_count: float = 12.0
    points_failed_count: float = 6.0
    fieldbus_latency_ms: float = 45.0
    sat_link_connected: str = "CONNECTED"
    sat_snr_db: float = 14.2
    sat_rtt_latency_ms: float = 640.0
    vhf_radio_healthy: str = "READY"


class BharatiInfrastructurePhysicsState:
    """Unified physical simulation state for all Bharati Infrastructure domains.
    
    Maintains causal coupling, conservation laws, and deterministic progression.
    """

    def __init__(
        self,
        seed: int | None = None,
        environmental_input: EnvironmentalInput | None = None,
    ) -> None:
        self._rng = random.Random(seed)
        self.sim_time_seconds: float = 0.0
        
        # Shared external environmental boundary input
        self.env = environmental_input if environmental_input is not None else EnvironmentalInput()
        
        # Domain subsystem physical states
        self.building = BuildingPhysicalState()
        self.structural = StructuralPhysicalState()
        self.hvac = HVACPhysicalState()
        self.water = WaterPhysicalState()
        self.wastewater = WastewaterPhysicalState()
        self.fire = FirePhysicalState()
        self.refrigeration = RefrigerationPhysicalState()
        self.pipelines = PipelinePhysicalState()
        self.emergency = EmergencyShelterPhysicalState()
        self.security = SecurityPhysicalState()
        self.bms = BMSPhysicalState()

    def set_seed(self, seed: int) -> None:
        """Reset the random number generator seed for deterministic reproducibility."""
        self._rng = random.Random(seed)

    def trigger_fire_event(self, zone_code: str = "Z01", intensity: float = 0.8, zone: str | None = None) -> None:
        """Trigger an authentic physical fire event in a specific zone.
        
        Physical consequence: local temperature rises, smoke obscuration surges.
        Sensors observe these states; detectors trip alarms and actuate fire dampers.
        """
        target_zone = (zone if zone is not None else zone_code).upper()
        self.fire.active_fire_zone = target_zone
        self.fire.fire_intensity = max(0.1, min(1.0, intensity))
        self._recalculate_fire_physics(dt_seconds=1.0)

    def clear_fire_event(self) -> None:
        """Extinguish and clear physical fire state."""
        self.fire.active_fire_zone = None
        self.fire.fire_intensity = 0.0
        # Reset zone fire parameters to ambient baseline
        self.fire.z01_smoke_obs_pct = 0.0
        self.fire.z01_temp_c = 21.2
        self.fire.z01_alarm_status = "NORMAL"
        self.fire.z01_damper_open = True
        
        self.fire.z02_smoke_obs_pct = 0.0
        self.fire.z02_temp_c = 20.8
        self.fire.z02_alarm_status = "NORMAL"
        self.fire.z02_damper_open = True
        
        self.fire.z03_smoke_obs_pct = 0.0
        self.fire.z03_temp_c = 28.5
        self.fire.z03_alarm_status = "NORMAL"
        self.fire.z03_damper_open = True
        
        self.fire.z04_smoke_obs_pct = 0.0
        self.fire.z04_temp_c = 15.0
        self.fire.z04_alarm_status = "NORMAL"
        self.fire.z04_damper_open = True

    def calculate_total_auxiliary_power_kw(self) -> float:
        """Compute the total electrical load drawn by station infrastructure equipment.
        
        Read-only interface consumable by future Energy models without modifying Energy state:
        - HVAC supply/exhaust fans and humidifier
        - Desalination RO high-pressure pumps & seawater intake
        - Wastewater treatment air blower and permeate pumps
        - Cold storage refrigeration condensing compressors
        - Pipeline electrical trace heating circuits
        """
        # HVAC fan power (~12-18 kW)
        hvac_kw = 0.0
        if self.hvac.ahu01_fan_running:
            hvac_kw += 5.5 * (self.hvac.ahu01_fan_speed_pct / 100.0) ** 2.5
        if self.hvac.ahu02_fan_running:
            hvac_kw += 7.5 * (self.hvac.ahu02_fan_speed_pct / 100.0) ** 2.5
        if self.hvac.humidifier_active:
            hvac_kw += 4.0
            
        # Water & RO pumps (~10-15 kW)
        water_kw = 0.0
        if self.water.intake_pump_running:
            water_kw += 2.2
        if self.water.ro_system_status == "PRODUCING":
            water_kw += 8.5  # High-pressure plunger pump
            
        # Wastewater pumps & blowers (~4-6 kW)
        ww_kw = 0.0
        if self.wastewater.aeration_blower_running:
            ww_kw += 3.0
        if self.wastewater.permeate_pump_running:
            ww_kw += 1.5
            
        # Refrigeration compressors (~5-10 kW)
        refrig_kw = 0.0
        if self.refrigeration.frz01_compressor_running:
            refrig_kw += 4.2
        if self.refrigeration.chl01_compressor_running:
            refrig_kw += 2.8
            
        # Pipeline trace heating circuits (~6-12 kW)
        pipe_kw = 0.0
        if self.pipelines.water01_trace_heating_on:
            pipe_kw += 2.5
        if self.pipelines.fuel01_trace_heating_on:
            pipe_kw += 2.0
        if self.pipelines.heat01_trace_heating_on:
            pipe_kw += 1.8
            
        return round(hvac_kw + water_kw + ww_kw + refrig_kw + pipe_kw, 1)

    def step(self, dt_seconds: float = 1.0) -> None:
        """Advance the physical simulation state forward by dt_seconds."""
        if dt_seconds <= 0:
            return
            
        self.sim_time_seconds += dt_seconds
        
        # Recalculate coupled physics across all domains
        self._recalculate_building_thermal(dt_seconds)
        self._recalculate_structural(dt_seconds)
        self._recalculate_hvac(dt_seconds)
        self._recalculate_water(dt_seconds)
        self._recalculate_wastewater(dt_seconds)
        self._recalculate_fire_physics(dt_seconds)
        self._recalculate_refrigeration(dt_seconds)
        self._recalculate_pipelines(dt_seconds)
        self._recalculate_emergency(dt_seconds)
        self._recalculate_bms(dt_seconds)

    @staticmethod
    def _relaxation_factor(dt_seconds: float, tau_seconds: float) -> float:
        """Unconditionally stable exponential relaxation factor (1 - exp(-dt/tau))."""
        if tau_seconds <= 0.0 or dt_seconds <= 0.0:
            return 1.0
        return 1.0 - math.exp(-dt_seconds / tau_seconds)

    # --------------------------------------------------------------------------
    # Subsystem Physical Equations
    # --------------------------------------------------------------------------
    def _recalculate_building_thermal(self, dt_seconds: float) -> None:
        """Building envelope heat loss and zone temperature response."""
        t_amb = self.env.ambient_temperature_c
        
        # Conduction through cladding facades
        self.building.envelope_temp_north_c = round(t_amb + (self.building.temp_living_c - t_amb) * 0.25, 1)
        self.building.envelope_temp_south_c = round(t_amb + (self.building.temp_lab_c - t_amb) * 0.20, 1)
        
        # Roof aerodynamic snow load increases with wind and snowfall rate
        snow_target = 1.0 + (self.env.snow_accumulation_rate_mm_h * 0.15) + (self.env.wind_speed_ms * 0.02)
        alpha_snow = self._relaxation_factor(dt_seconds, 3600.0)
        self.building.roof_snow_load_kpa = round(
            self.building.roof_snow_load_kpa + (snow_target - self.building.roof_snow_load_kpa) * alpha_snow,
            2
        )
        
        # Zone indoor temperatures: heating coil supply vs conduction heat loss
        # Delta T driven by AHU heating valve and ambient deficit
        heating_drive_living = (self.hvac.ahu01_heating_valve_pct / 100.0) * 1.5 - ((21.0 - t_amb) / 40.0) * 0.8
        alpha_t = self._relaxation_factor(dt_seconds, 600.0)
        self.building.temp_living_c = round(
            max(15.0, min(25.0, self.building.temp_living_c + heating_drive_living * alpha_t + self._rng.uniform(-0.02, 0.02))),
            1
        )
        
        heating_drive_lab = (self.hvac.ahu02_heating_valve_pct / 100.0) * 1.5 - ((20.5 - t_amb) / 40.0) * 0.8
        self.building.temp_lab_c = round(
            max(15.0, min(25.0, self.building.temp_lab_c + heating_drive_lab * alpha_t + self._rng.uniform(-0.02, 0.02))),
            1
        )

    def _recalculate_structural(self, dt_seconds: float) -> None:
        """Wind-induced tilt, vibration, and thermal dilation on elevated pillars."""
        wind = self.env.wind_speed_ms
        t_amb = self.env.ambient_temperature_c
        
        # Wind force induces lateral tilt and vibration
        self.structural.building_tilt_x_mrad = round(0.15 + (wind / 45.0) * 0.40 + self._rng.uniform(-0.02, 0.02), 2)
        self.structural.building_tilt_y_mrad = round(-0.10 + (wind / 45.0) * 0.25 + self._rng.uniform(-0.02, 0.02), 2)
        self.structural.vibration_rms_mm_s = round(0.4 + (wind / 45.0) ** 1.8 * 4.5 + self._rng.uniform(-0.05, 0.05), 2)
        
        # Axial strain on 86 steel stilts under snow & wind loading
        base_strain = 140.0 + (self.building.roof_snow_load_kpa * 8.0)
        self.structural.pillar_01_strain_ustrain = round(base_strain + (wind * 0.5) + self._rng.uniform(-1.0, 1.0), 1)
        self.structural.pillar_43_strain_ustrain = round(base_strain * 1.1 + self._rng.uniform(-1.0, 1.0), 1)
        self.structural.pillar_86_strain_ustrain = round(base_strain * 0.95 + self._rng.uniform(-1.0, 1.0), 1)
        
        # Thermal contraction across 134 modular joint shells
        thermal_shrink_mm = (0.0 - t_amb) * 0.08
        self.structural.joint_disp_mm = round(1.2 + thermal_shrink_mm + self._rng.uniform(-0.05, 0.05), 2)

    def _recalculate_hvac(self, dt_seconds: float) -> None:
        """AHU coil heat transfer, fan airflow, and occupant CO2 balance."""
        t_amb = self.env.ambient_temperature_c
        
        # AHU-01 Heating coil thermodynamics: supply air temp responds to valve position
        ahu01_target_supply = self.hvac.ahu01_return_temp_c + (self.hvac.ahu01_heating_valve_pct / 100.0) * 8.0
        alpha_ahu = self._relaxation_factor(dt_seconds, 60.0)
        self.hvac.ahu01_supply_temp_c = round(
            self.hvac.ahu01_supply_temp_c + (ahu01_target_supply - self.hvac.ahu01_supply_temp_c) * alpha_ahu,
            1
        )
        self.hvac.ahu01_return_temp_c = round(self.building.temp_living_c - 0.8, 1)
        
        # AHU-02
        ahu02_target_supply = self.hvac.ahu02_return_temp_c + (self.hvac.ahu02_heating_valve_pct / 100.0) * 8.0
        self.hvac.ahu02_supply_temp_c = round(
            self.hvac.ahu02_supply_temp_c + (ahu02_target_supply - self.hvac.ahu02_supply_temp_c) * alpha_ahu,
            1
        )
        self.hvac.ahu02_return_temp_c = round(self.building.temp_lab_c - 0.8, 1)
        
        # CO2 Mass Balance: Occupant metabolic generation vs fresh air ventilation dilution
        occupants = self.building.occupancy_count
        fresh_air_m3_h = (self.hvac.ahu01_airflow_m3_h * (self.hvac.ahu01_fresh_air_damper_pct / 100.0))
        
        # Target steady-state CO2 concentration
        if fresh_air_m3_h > 100.0:
            co2_living_target = 420.0 + (occupants * 18.0 * 1000.0) / fresh_air_m3_h
        else:
            co2_living_target = 1800.0
            
        alpha_co2 = self._relaxation_factor(dt_seconds, 300.0)
        self.hvac.co2_living_ppm = round(
            self.hvac.co2_living_ppm + (co2_living_target - self.hvac.co2_living_ppm) * alpha_co2 + self._rng.uniform(-1.0, 1.0),
            1
        )

    def _recalculate_water(self, dt_seconds: float) -> None:
        """Seawater intake, RO mass conservation, and reservoir volume integration."""
        # Seawater intake flow
        if self.water.intake_pump_running:
            self.water.seawater_intake_flow_lph = round(SEAWATER_INTAKE_NOMINAL_FLOW_LPH + self._rng.uniform(-20.0, 20.0), 1)
            self.water.seawater_intake_pressure_bar = round(3.2 + self._rng.uniform(-0.1, 0.1), 2)
        else:
            self.water.seawater_intake_flow_lph = 0.0
            self.water.seawater_intake_pressure_bar = 0.0
            
        # Reverse Osmosis Mass Conservation: Feed = Permeate + Reject + Loss
        if self.water.ro_system_status == "PRODUCING" and self.water.intake_pump_running:
            self.water.ro_permeate_flow_lph = round(RO_DESIGN_PERMEATE_FLOW_LPH + self._rng.uniform(-10.0, 10.0), 1)
            # Brine reject is the remaining fraction minus ~20 L/h modeled filter flush loss
            self.water.ro_reject_flow_lph = round(self.water.seawater_intake_flow_lph - self.water.ro_permeate_flow_lph - 20.0, 1)
            self.water.ro_feed_pressure_bar = round(55.0 + self._rng.uniform(-0.5, 0.5), 1)
            self.water.ro_permeate_conductivity_us_cm = round(240.0 + self._rng.uniform(-5.0, 5.0), 1)
        else:
            self.water.ro_permeate_flow_lph = 0.0
            self.water.ro_reject_flow_lph = 0.0
            self.water.ro_feed_pressure_bar = 0.0
            
        # Station water consumption based on live headcount
        hourly_rate = (self.building.occupancy_count * PER_CAPITA_WATER_CONSUMPTION_L_DAY) / 24.0
        self.water.consumption_flow_lph = round(hourly_rate + self._rng.uniform(-5.0, 5.0), 1)
        
        # Potable Storage Tank Mass Balance Integration:
        # V(t+1) = V(t) + (Q_permeate - Q_consumption) * dt
        dt_hours = dt_seconds / 3600.0
        net_water_litres = (self.water.ro_permeate_flow_lph - self.water.consumption_flow_lph) * dt_hours
        self.water.potable_tank_volume_l = max(
            0.0,
            min(self.water.potable_tank_capacity_l, self.water.potable_tank_volume_l + net_water_litres)
        )
        self.water.potable_tank_level_pct = round(
            (self.water.potable_tank_volume_l / self.water.potable_tank_capacity_l) * 100.0,
            1
        )

    def _recalculate_wastewater(self, dt_seconds: float) -> None:
        """Coupled influent from potable consumption and dynamic MBR treatment degradation."""
        # Influent sewage generation directly tracks station water consumption (~85% of consumed water)
        self.wastewater.inlet_flow_lph = round(self.water.consumption_flow_lph * 0.85, 1)
        
        # Sump accumulation
        dt_hours = dt_seconds / 3600.0
        self.wastewater.grey_sump_level_pct = round(
            max(10.0, min(95.0, self.wastewater.grey_sump_level_pct + (self.wastewater.inlet_flow_lph * 0.7 - 70.0) * dt_hours * 0.2)),
            1
        )
        
        # Treatment Process Dynamics:
        # If aeration blower is OFF, dissolved oxygen crashes, bio-digestion fails, and COD/ammonia escalate!
        if self.wastewater.aeration_blower_running:
            self.wastewater.dissolved_oxygen_mg_l = round(2.8 + self._rng.uniform(-0.1, 0.1), 1)
            target_cod = 42.0 * self.wastewater.membrane_fouling_factor
            target_bod = 8.5 * self.wastewater.membrane_fouling_factor
            target_ammonia = 3.2
        else:
            # Anaerobic degradation: bacterial respiration consumes DO rapidly (~1.2 mg/L per hour)
            self.wastewater.dissolved_oxygen_mg_l = max(0.1, round(self.wastewater.dissolved_oxygen_mg_l - (1.2 * dt_hours), 2))
            target_cod = 180.0  # Fails standard
            target_bod = 45.0   # Fails standard
            target_ammonia = 22.0
            
        alpha_ww = self._relaxation_factor(dt_seconds, 600.0)
        self.wastewater.effluent_cod_mg_l = round(
            self.wastewater.effluent_cod_mg_l + (target_cod - self.wastewater.effluent_cod_mg_l) * alpha_ww,
            1
        )
        self.wastewater.effluent_bod_mg_l = round(
            self.wastewater.effluent_bod_mg_l + (target_bod - self.wastewater.effluent_bod_mg_l) * alpha_ww,
            1
        )
        self.wastewater.effluent_ammonia_mg_l = round(
            self.wastewater.effluent_ammonia_mg_l + (target_ammonia - self.wastewater.effluent_ammonia_mg_l) * alpha_ww,
            1
        )
        
        # MBR Trans-Membrane Pressure (TMP)
        self.wastewater.membrane_tmp_bar = round(0.25 * self.wastewater.membrane_fouling_factor + self._rng.uniform(-0.01, 0.01), 2)
        if self.wastewater.permeate_pump_running:
            self.wastewater.effluent_discharge_flow_lph = round(92.0 + self._rng.uniform(-3.0, 3.0), 1)
        else:
            self.wastewater.effluent_discharge_flow_lph = 0.0

    def _recalculate_fire_physics(self, dt_seconds: float) -> None:
        """Physical combustion heat and smoke generation, causing detector activation and damper trips."""
        if self.fire.active_fire_zone is not None and self.fire.fire_intensity > 0.0:
            zone = self.fire.active_fire_zone
            intensity = self.fire.fire_intensity
            
            # Rate of smoke generation and thermal spike in affected zone
            if zone == "Z01":
                self.fire.z01_smoke_obs_pct = min(100.0, round(self.fire.z01_smoke_obs_pct + (intensity * 40.0 * dt_seconds), 1))
                self.fire.z01_temp_c = min(150.0, round(self.fire.z01_temp_c + (intensity * 15.0 * dt_seconds), 1))
                # Detectors trip when smoke > 15% or temp > 57°C
                if self.fire.z01_smoke_obs_pct > 15.0 or self.fire.z01_temp_c > 57.0:
                    self.fire.z01_alarm_status = "ALARM"
                    self.fire.z01_damper_open = False  # Damper auto-trips closed to isolate duct
            elif zone == "Z02":
                self.fire.z02_smoke_obs_pct = min(100.0, round(self.fire.z02_smoke_obs_pct + (intensity * 40.0 * dt_seconds), 1))
                self.fire.z02_temp_c = min(150.0, round(self.fire.z02_temp_c + (intensity * 15.0 * dt_seconds), 1))
                if self.fire.z02_smoke_obs_pct > 15.0 or self.fire.z02_temp_c > 57.0:
                    self.fire.z02_alarm_status = "ALARM"
                    self.fire.z02_damper_open = False
            elif zone == "Z03":
                self.fire.z03_smoke_obs_pct = min(100.0, round(self.fire.z03_smoke_obs_pct + (intensity * 40.0 * dt_seconds), 1))
                self.fire.z03_temp_c = min(150.0, round(self.fire.z03_temp_c + (intensity * 15.0 * dt_seconds), 1))
                if self.fire.z03_smoke_obs_pct > 15.0 or self.fire.z03_temp_c > 57.0:
                    self.fire.z03_alarm_status = "ALARM"
                    self.fire.z03_damper_open = False
            elif zone == "Z04":
                self.fire.z04_smoke_obs_pct = min(100.0, round(self.fire.z04_smoke_obs_pct + (intensity * 40.0 * dt_seconds), 1))
                self.fire.z04_temp_c = min(150.0, round(self.fire.z04_temp_c + (intensity * 15.0 * dt_seconds), 1))
                if self.fire.z04_smoke_obs_pct > 15.0 or self.fire.z04_temp_c > 57.0:
                    self.fire.z04_alarm_status = "ALARM"
                    self.fire.z04_damper_open = False

    def _recalculate_refrigeration(self, dt_seconds: float) -> None:
        """Deep freeze and chiller thermodynamics: compressor cooling vs convective door heat ingress."""
        # Deep Freeze Room
        frz_target = self.refrigeration.frz01_target_temp_c
        if self.refrigeration.frz01_door_open:
            # Door open causes rapid warm air ingress (+1.5°C per minute)
            self.refrigeration.frz01_temp_c = round(self.refrigeration.frz01_temp_c + (1.5 * dt_seconds / 60.0), 2)
            self.refrigeration.frz01_compressor_running = True  # Forced continuous run
        else:
            # Compressor pulls temp down towards configurable target
            if self.refrigeration.frz01_compressor_running:
                alpha_frz = self._relaxation_factor(dt_seconds, 300.0)
                pull_down = (self.refrigeration.frz01_temp_c - frz_target) * alpha_frz
                self.refrigeration.frz01_temp_c = round(self.refrigeration.frz01_temp_c - pull_down, 2)
                if self.refrigeration.frz01_temp_c <= frz_target - 0.5:
                    self.refrigeration.frz01_compressor_running = False
            else:
                # Slight passive insulation heat leak
                alpha_leak = self._relaxation_factor(dt_seconds, 300.0)
                self.refrigeration.frz01_temp_c = round(self.refrigeration.frz01_temp_c + (0.1 * alpha_leak), 2)
                if self.refrigeration.frz01_temp_c >= frz_target + 1.0:
                    self.refrigeration.frz01_compressor_running = True
                    
        # Spoilage alarm if freezer exceeds -15°C
        if self.refrigeration.frz01_temp_c > -15.0:
            self.refrigeration.frz01_temp_alarm = "ALARM_HIGH_TEMP"
        else:
            self.refrigeration.frz01_temp_alarm = "NORMAL"
            
        # Cold Provisions Chiller
        chl_target = self.refrigeration.chl01_target_temp_c
        if self.refrigeration.chl01_door_open:
            self.refrigeration.chl01_temp_c = round(self.refrigeration.chl01_temp_c + (2.0 * dt_seconds / 60.0), 2)
            self.refrigeration.chl01_compressor_running = True
        else:
            if self.refrigeration.chl01_compressor_running:
                alpha_chl = self._relaxation_factor(dt_seconds, 200.0)
                pull_down = (self.refrigeration.chl01_temp_c - chl_target) * alpha_chl
                self.refrigeration.chl01_temp_c = round(self.refrigeration.chl01_temp_c - pull_down, 2)
                if self.refrigeration.chl01_temp_c <= chl_target - 0.5:
                    self.refrigeration.chl01_compressor_running = False
            else:
                alpha_leak_chl = self._relaxation_factor(dt_seconds, 200.0)
                self.refrigeration.chl01_temp_c = round(self.refrigeration.chl01_temp_c + (0.15 * alpha_leak_chl), 2)
                if self.refrigeration.chl01_temp_c >= chl_target + 1.0:
                    self.refrigeration.chl01_compressor_running = True
                    
        if self.refrigeration.chl01_temp_c > 8.0:
            self.refrigeration.chl01_temp_alarm = "ALARM_HIGH_TEMP"
        else:
            self.refrigeration.chl01_temp_alarm = "NORMAL"

    def _recalculate_pipelines(self, dt_seconds: float) -> None:
        """Utilidor pipeline freeze protection based on ambient temp, flow, and trace heating."""
        t_amb = self.env.ambient_temperature_c
        
        # Potable water pipe:
        # If trace heating is ON, pipe stays protected (~8.5°C)
        # If trace heating is OFF and flow is 0, pipe rapidly cools towards ambient!
        if self.pipelines.water01_trace_heating_on:
            target_t = 8.5
        else:
            target_t = t_amb  # Plunges to sub-zero!
            
        alpha_pipe = self._relaxation_factor(dt_seconds, 600.0)
        self.pipelines.water01_pipe_temp_c = round(
            self.pipelines.water01_pipe_temp_c + (target_t - self.pipelines.water01_pipe_temp_c) * alpha_pipe,
            1
        )
        
        # Fuel pipe
        if self.pipelines.fuel01_trace_heating_on:
            target_fuel_t = 6.0
        else:
            target_fuel_t = t_amb
        self.pipelines.fuel01_pipe_temp_c = round(
            self.pipelines.fuel01_pipe_temp_c + (target_fuel_t - self.pipelines.fuel01_pipe_temp_c) * alpha_pipe,
            1
        )

    def _recalculate_emergency(self, dt_seconds: float) -> None:
        """Emergency shelter environmental stability."""
        # Stable refuge temperature maintained by independent boiler
        self.emergency.shelter_temp_c = round(16.5 + self._rng.uniform(-0.1, 0.1), 1)
        self.emergency.boiler_temp_c = round(62.0 + self._rng.uniform(-0.2, 0.2), 1)

    def _recalculate_bms(self, dt_seconds: float) -> None:
        """BMS point status counters and satellite communication latency."""
        # Points online fluctuate very slightly with normal field polling
        self.bms.fieldbus_latency_ms = round(45.0 + self._rng.uniform(-2.0, 2.0), 1)
        self.bms.sat_rtt_latency_ms = round(640.0 + self._rng.uniform(-10.0, 10.0), 1)
        self.bms.sat_snr_db = round(14.2 + self._rng.uniform(-0.2, 0.2), 1)
