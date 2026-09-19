"""Physical coherence state model for Bharati Station Energy System.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

SOURCE OF TRUTH & TECHNICAL GROUNDING:
- Three 100 kVA diesel-operated CHP units (NCPOR documented).
- Centralized MLVD power distribution (NCPOR documented).
- Fuel farm (~3 lakh L, 13 x ~24k L tanks) + day tank (NCPOR documented).
- Heating system with waste-heat recovery (NCPOR documented, bounded by ~155 kWth max demand).
- Two 60 kVA UPS plants (NCPOR documented).

The physics state is the source of simulated reality. Sensors observe this state.
Values are deterministic and physically coupled.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Literal

from .config import (
    CHP_COUNT,
    CHP_NOMINAL_FREQUENCY_HZ,
    CHP_NOMINAL_RPM,
    CHP_NOMINAL_VOLTAGE_V,
    CHP_RATING_KVA,
    CHP_THERMAL_RECOVERY_RATIO,
    DAY_TANK_CAPACITY_L,
    DAY_TANK_REFILL_TARGET_L,
    DAY_TANK_REFILL_THRESHOLD_L,
    DIESEL_LHV_KWH_PER_L,
    FUEL_CONSUMPTION_FACTOR_L_PER_KWH,
    FUEL_FARM_CAPACITY_L,
    FUEL_IDLE_CONSUMPTION_LPH,
    FUEL_TRANSFER_PUMP_FLOW_LPH,
    GLYCOL_LOOP_PRESSURE_NOMINAL_BAR,
    MAX_STATION_HEATING_DEMAND_KW,
    UPS_BATTERY_NOMINAL_V,
    UPS_COUNT,
    UPS_DEFAULT_MODULE_COUNT,
    UPS_NOMINAL_VOLTAGE_V,
    UPS_RATING_KVA,
)


@dataclass
class CHPPhysicalState:
    """Coherent state of an individual 100 kVA CHP unit."""
    index: int  # 1, 2, or 3
    # Configurable operational state: RUNNING, STANDBY, OFF, MAINTENANCE
    operating_state: Literal["RUNNING", "STANDBY", "OFF", "MAINTENANCE"] = "STANDBY"
    
    # Electrical
    active_power_kw: float = 0.0
    apparent_power_kva: float = 0.0
    voltage: float = CHP_NOMINAL_VOLTAGE_V
    current: float = 0.0
    frequency_hz: float = CHP_NOMINAL_FREQUENCY_HZ
    power_factor: float = 0.88
    
    # Mechanical
    rpm: float = 0.0
    running_status: bool = False
    
    # Thermal
    exhaust_temperature_c: float = 25.0
    coolant_temperature_c: float = 25.0
    
    # Pressure
    oil_pressure: float = 0.0
    coolant_pressure: float = 0.0
    
    # Fuel
    fuel_consumption_lph: float = 0.0
    
    # Operational
    runtime_hours: float = 1240.0 + 350.0  # base initial hours


@dataclass
class UPSPhysicalState:
    """Coherent state of an individual 60 kVA UPS plant."""
    index: int  # 1 or 2
    # Configurable load sharing mode: PARALLEL_REDUNDANT, STANDBY, ISOLATED
    mode: str = "PARALLEL_REDUNDANT"  # SIMULATION ASSUMPTION
    
    # Input
    input_voltage_l1: float = 230.0
    input_voltage_l2: float = 230.0
    input_voltage_l3: float = 230.0
    input_frequency_hz: float = 50.0
    
    # Bypass
    bypass_voltage: float = 400.0
    bypass_frequency_hz: float = 50.0
    
    # DC Link
    dc_link_voltage: float = 400.0
    
    # Output
    output_voltage_l1: float = 230.0
    output_voltage_l2: float = 230.0
    output_voltage_l3: float = 230.0
    output_frequency_hz: float = 50.0
    output_current_l1: float = 0.0
    output_current_l2: float = 0.0
    output_current_l3: float = 0.0
    
    # Load
    load_percent: float = 0.0
    real_power_kw: float = 0.0
    apparent_power_kva: float = 0.0
    
    # Battery
    battery_module_count: int = UPS_DEFAULT_MODULE_COUNT  # Configurable module count
    battery_voltage: float = UPS_BATTERY_NOMINAL_V
    battery_current: float = -0.5  # Negative indicates charging/float current, positive indicates discharge
    battery_temperature_c: float = 22.0
    battery_soc_percent: float = 99.5
    backup_time_minutes: float = 65.0
    individual_battery_voltages: list[float] = field(default_factory=list)
    
    # Status flags
    rectifier_status: str = "NORMAL"
    boost_status: str = "INACTIVE"
    battery_status: str = "FLOAT"
    charging_status: str = "TRICKLE"
    inverter_status: str = "NORMAL"
    bypass_status: str = "AVAILABLE"
    load_status: str = "ON_INVERTER"
    fan_status: str = "NORMAL"


@dataclass
class FuelPhysicalState:
    """Coherent fuel storage, transfer, and consumption state."""
    # Bulk fuel farm inventory (excluding day tank)
    bulk_fuel_level_l: float = 275_000.0
    bulk_capacity_l: float = FUEL_FARM_CAPACITY_L
    
    # Day tank inventory (supplied from bulk farm)
    day_tank_level_l: float = 850.0
    day_tank_capacity_l: float = DAY_TANK_CAPACITY_L
    
    # Transfer system state
    transfer_pump_running: bool = False
    transfer_flow_lph: float = 0.0
    
    # Supply line & quality
    fuel_temperature_c: float = 8.5
    fuel_flow_lph: float = 0.0  # Total flow from day tank to active CHPs
    leak_status: str = "NORMAL"
    overfill_status: str = "NORMAL"
    
    # Cumulative consumed fuel for conservation accounting
    cumulative_fuel_consumed_l: float = 0.0


@dataclass
class HeatingPhysicalState:
    """Coherent thermal energy and hydronic heating loop state."""
    # Thermal production from CHPs
    chp_thermal_generation_kw: float = 0.0
    recoverable_thermal_kw: float = 0.0
    
    # Station heating demand (bounded by MAX_STATION_HEATING_DEMAND_KW = 155 kWth)
    station_heating_demand_kw: float = 95.0
    
    # Delivered useful heat
    useful_thermal_output_kw: float = 0.0
    
    # Temperatures
    heating_supply_temperature_c: float = 68.0
    heating_return_temperature_c: float = 52.0
    glycol_temperature_c: float = 65.0
    buffer_tank_temperature_c: float = 64.0
    hot_water_temperature_c: float = 58.0
    
    # Hydraulics
    glycol_pressure_bar: float = GLYCOL_LOOP_PRESSURE_NOMINAL_BAR
    heating_pump_status: str = "RUNNING"
    heating_pump_flow: float = 12.5  # m3/h
    heating_pump_pressure: float = 2.4  # bar


class BharatiEnergyPhysicsState:
    """Unified physical simulation state for Bharati Station Energy System.
    
    Provides deterministic stepping, realistic cross-subsystem coupling,
    and seed-based reproducibility.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._sim_time_seconds: float = 0.0
        
        # Initialize 3 CHPs
        # Initial simulation condition: CHP-1 RUNNING, CHP-2 RUNNING, CHP-3 STANDBY
        # (This is an initial simulation condition, NOT a permanent operational role)
        self.chps: list[CHPPhysicalState] = [
            CHPPhysicalState(index=1, operating_state="RUNNING", runtime_hours=4520.0),
            CHPPhysicalState(index=2, operating_state="RUNNING", runtime_hours=3810.0),
            CHPPhysicalState(index=3, operating_state="STANDBY", runtime_hours=2190.0),
        ]
        
        # Initialize 2 UPS plants
        self.ups: list[UPSPhysicalState] = [
            UPSPhysicalState(index=1, mode="PARALLEL_REDUNDANT"),
            UPSPhysicalState(index=2, mode="PARALLEL_REDUNDANT"),
        ]
        self._init_ups_cells()
        
        # Initialize Fuel and Heating subsystems
        self.fuel = FuelPhysicalState()
        self.heating = HeatingPhysicalState()
        
        # Station load parameters
        self.base_station_load_kw: float = 165.0
        self.total_station_load_kw: float = 165.0
        self.critical_load_fraction: float = 0.35  # ~35% critical load on UPS
        
        # Ambient temperature at Larsemann Hills (-35 to +5 C range)
        self.ambient_temperature_c: float = -18.0
        
        # Initial state calculation
        self._recalculate_physics(dt_seconds=0.0)

    def _init_ups_cells(self) -> None:
        """Initialize individual battery cell/module voltages."""
        for ups in self.ups:
            count = ups.battery_module_count
            nominal_per_module = ups.battery_voltage / count
            ups.individual_battery_voltages = [
                round(nominal_per_module + self._rng.uniform(-0.05, 0.05), 3)
                for _ in range(count)
            ]

    def set_seed(self, seed: int) -> None:
        """Reset the random number generator with a specific seed."""
        self._rng = random.Random(seed)

    def step(self, dt_seconds: float = 1.0) -> None:
        """Advance physical simulation state by dt_seconds."""
        if dt_seconds <= 0:
            return
            
        self._sim_time_seconds += dt_seconds
        self._recalculate_physics(dt_seconds)

    def _recalculate_physics(self, dt_seconds: float) -> None:
        """Perform deterministic physical updates across all coupled subsystems."""
        # 1. Station Load variation (smooth diurnal sinusoidal pattern + slight bounded noise)
        hour = (self._sim_time_seconds / 3600.0) % 24.0
        diurnal_factor = math.sin((hour - 8.0) * math.pi / 12.0)  # Peak around 14:00, trough around 02:00
        noise = self._rng.uniform(-1.5, 1.5)
        self.total_station_load_kw = max(80.0, min(240.0, self.base_station_load_kw + diurnal_factor * 18.0 + noise))
        
        critical_load_kw = self.total_station_load_kw * self.critical_load_fraction
        
        # 2. Dispatch load among active (RUNNING) CHPs
        running_chps = [chp for chp in self.chps if chp.operating_state == "RUNNING"]
        total_running = len(running_chps)
        
        if total_running > 0:
            load_per_chp = self.total_station_load_kw / total_running
        else:
            load_per_chp = 0.0
            
        total_fuel_consumption_lph = 0.0
        total_chp_thermal_generation_kw = 0.0
        
        for chp in self.chps:
            if chp.operating_state == "RUNNING":
                chp.running_status = True
                chp.active_power_kw = round(load_per_chp + self._rng.uniform(-0.4, 0.4), 2)
                chp.power_factor = round(0.88 + self._rng.uniform(-0.015, 0.015), 3)
                chp.apparent_power_kva = round(chp.active_power_kw / chp.power_factor, 2)
                
                # Voltage: 400V +/- small droop/noise
                voltage_noise = self._rng.uniform(-1.2, 1.2)
                chp.voltage = round(CHP_NOMINAL_VOLTAGE_V + voltage_noise, 1)
                
                # Frequency: 50.0 Hz with small governor droop based on loading
                freq_droop = (chp.active_power_kw / CHP_RATING_KVA) * 0.12
                freq_noise = self._rng.uniform(-0.02, 0.02)
                chp.frequency_hz = round(CHP_NOMINAL_FREQUENCY_HZ - freq_droop + freq_noise, 2)
                
                # Alternator current: P / (sqrt(3) * V * PF)
                denom = math.sqrt(3) * chp.voltage * chp.power_factor
                chp.current = round((chp.active_power_kw * 1000.0) / max(denom, 1.0), 1)
                
                # RPM: 1500 +/- minor governor hunting
                chp.rpm = round(CHP_NOMINAL_RPM * (chp.frequency_hz / CHP_NOMINAL_FREQUENCY_HZ) + self._rng.uniform(-2.0, 2.0), 1)
                
                # Thermal: Exhaust temp increases with load (320°C idle to ~480°C full load)
                chp.exhaust_temperature_c = round(320.0 + (chp.active_power_kw / CHP_RATING_KVA) * 160.0 + self._rng.uniform(-2.0, 2.0), 1)
                chp.coolant_temperature_c = round(78.0 + (chp.active_power_kw / CHP_RATING_KVA) * 9.0 + self._rng.uniform(-0.5, 0.5), 1)
                
                # Pressure
                chp.oil_pressure = round(4.2 + self._rng.uniform(-0.1, 0.1), 2)
                chp.coolant_pressure = round(1.8 + self._rng.uniform(-0.05, 0.05), 2)
                
                # Fuel consumption: idle + load slope (~0.25 L/kWh)
                chp.fuel_consumption_lph = round(
                    FUEL_IDLE_CONSUMPTION_LPH + (FUEL_CONSUMPTION_FACTOR_L_PER_KWH * chp.active_power_kw) + self._rng.uniform(-0.1, 0.1),
                    2
                )
                
                # Runtime accumulation
                chp.runtime_hours = round(chp.runtime_hours + (dt_seconds / 3600.0), 4)
                
                # Heat generation
                gross_heat = chp.active_power_kw * CHP_THERMAL_RECOVERY_RATIO
                total_chp_thermal_generation_kw += gross_heat
                total_fuel_consumption_lph += chp.fuel_consumption_lph
                
            else:
                # Standby / Off / Maintenance
                chp.running_status = False
                chp.active_power_kw = 0.0
                chp.apparent_power_kva = 0.0
                chp.current = 0.0
                chp.voltage = 0.0 if chp.operating_state in ("OFF", "MAINTENANCE") else CHP_NOMINAL_VOLTAGE_V
                chp.frequency_hz = 0.0 if chp.operating_state in ("OFF", "MAINTENANCE") else CHP_NOMINAL_FREQUENCY_HZ
                chp.rpm = 0.0
                chp.exhaust_temperature_c = max(20.0, chp.exhaust_temperature_c - (dt_seconds * 0.05))
                chp.coolant_temperature_c = max(20.0, chp.coolant_temperature_c - (dt_seconds * 0.02))
                chp.oil_pressure = 0.0
                chp.coolant_pressure = 0.0
                chp.fuel_consumption_lph = 0.0

        # 3. Fuel Inventory & Transfer System Update
        self.fuel.fuel_flow_lph = round(total_fuel_consumption_lph, 2)
        
        # Consumption from Day Tank
        liters_consumed = (total_fuel_consumption_lph * dt_seconds) / 3600.0
        self.fuel.day_tank_level_l = max(0.0, self.fuel.day_tank_level_l - liters_consumed)
        self.fuel.cumulative_fuel_consumed_l += liters_consumed
        
        # Day Tank automated refill logic from bulk fuel farm
        if self.fuel.day_tank_level_l <= DAY_TANK_REFILL_THRESHOLD_L:
            self.fuel.transfer_pump_running = True
        elif self.fuel.day_tank_level_l >= DAY_TANK_REFILL_TARGET_L:
            self.fuel.transfer_pump_running = False
            
        if self.fuel.transfer_pump_running and self.fuel.bulk_fuel_level_l > 0.0:
            transfer_flow = min(FUEL_TRANSFER_PUMP_FLOW_LPH, (self.fuel.day_tank_capacity_l - self.fuel.day_tank_level_l) * 3600.0 / max(dt_seconds, 1.0))
            transfer_liters = (transfer_flow * dt_seconds) / 3600.0
            actual_transfer = min(transfer_liters, self.fuel.bulk_fuel_level_l)
            
            self.fuel.bulk_fuel_level_l -= actual_transfer
            self.fuel.day_tank_level_l += actual_transfer
            self.fuel.transfer_flow_lph = round(transfer_flow, 1)
        else:
            self.fuel.transfer_flow_lph = 0.0
            
        # Fuel temperature with trace heating
        self.fuel.fuel_temperature_c = round(8.5 + self._rng.uniform(-0.2, 0.2), 1)

        # 4. UPS Subsystem Update (Two 60 kVA plants sharing critical load)
        # Default simulation assumption: parallel redundant load sharing
        ups_count = len(self.ups)
        ups_load_share_kw = (critical_load_kw / ups_count) if ups_count > 0 else 0.0
        
        for ups in self.ups:
            # Load
            ups.real_power_kw = round(ups_load_share_kw, 2)
            pf = 0.90
            ups.apparent_power_kva = round(ups.real_power_kw / pf, 2)
            ups.load_percent = round((ups.apparent_power_kva / UPS_RATING_KVA) * 100.0, 1)
            
            # Input from MLVD bus (reflecting running CHPs)
            if total_running > 0:
                grid_v = self.chps[0].voltage / math.sqrt(3)  # phase-neutral ~230V
                ups.input_voltage_l1 = round(grid_v + self._rng.uniform(-0.5, 0.5), 1)
                ups.input_voltage_l2 = round(grid_v + self._rng.uniform(-0.5, 0.5), 1)
                ups.input_voltage_l3 = round(grid_v + self._rng.uniform(-0.5, 0.5), 1)
                ups.input_frequency_hz = round(self.chps[0].frequency_hz, 2)
                ups.bypass_voltage = round(self.chps[0].voltage, 1)
                ups.bypass_frequency_hz = round(self.chps[0].frequency_hz, 2)
                
                # Normal operation: floating charge
                ups.rectifier_status = "NORMAL"
                ups.inverter_status = "NORMAL"
                ups.load_status = "ON_INVERTER"
                ups.battery_status = "FLOAT"
                ups.charging_status = "TRICKLE"
                ups.battery_current = -0.5  # Float charging ~0.5A
                
                # SOC maintains ~99.5 - 100%
                ups.battery_soc_percent = min(100.0, ups.battery_soc_percent + (0.01 * dt_seconds / 60.0))
                ups.battery_voltage = round(UPS_BATTERY_NOMINAL_V + 8.0 + (ups.battery_soc_percent - 100.0) * 0.5, 1)
                ups.backup_time_minutes = round(65.0 * (ups.battery_soc_percent / 100.0) * (30.0 / max(ups.real_power_kw, 5.0)), 1)
            else:
                # Discharging onto battery if no CHPs running
                ups.input_voltage_l1 = 0.0
                ups.input_voltage_l2 = 0.0
                ups.input_voltage_l3 = 0.0
                ups.input_frequency_hz = 0.0
                ups.rectifier_status = "OFF"
                ups.battery_status = "DISCHARGE"
                ups.charging_status = "NONE"
                ups.load_status = "ON_BATTERY"
                
                # Discharge current = Power / DC bus voltage
                discharge_a = (ups.real_power_kw * 1000.0) / max(ups.battery_voltage, 100.0)
                ups.battery_current = round(discharge_a, 1)
                
                # Decrease SOC
                # Assume 100 Ah capacity battery bank
                ah_consumed = (discharge_a * dt_seconds) / 3600.0
                ups.battery_soc_percent = max(0.0, ups.battery_soc_percent - (ah_consumed / 100.0) * 100.0)
                ups.battery_voltage = round(UPS_BATTERY_NOMINAL_V - 20.0 * (1.0 - ups.battery_soc_percent / 100.0), 1)
                ups.backup_time_minutes = round(60.0 * (ups.battery_soc_percent / 100.0), 1)
                
            # Output conditioning
            ups.output_voltage_l1 = 230.0 + round(self._rng.uniform(-0.3, 0.3), 1)
            ups.output_voltage_l2 = 230.0 + round(self._rng.uniform(-0.3, 0.3), 1)
            ups.output_voltage_l3 = 230.0 + round(self._rng.uniform(-0.3, 0.3), 1)
            ups.output_frequency_hz = 50.0 + round(self._rng.uniform(-0.01, 0.01), 2)
            
            # Phase currents
            i_phase = (ups.real_power_kw * 1000.0) / (3.0 * 230.0 * 0.9)
            ups.output_current_l1 = round(i_phase + self._rng.uniform(-0.2, 0.2), 1)
            ups.output_current_l2 = round(i_phase + self._rng.uniform(-0.2, 0.2), 1)
            ups.output_current_l3 = round(i_phase + self._rng.uniform(-0.2, 0.2), 1)
            
            # Update individual cell voltages
            count = ups.battery_module_count
            v_per_module = ups.battery_voltage / count
            ups.individual_battery_voltages = [
                round(v_per_module + self._rng.uniform(-0.04, 0.04), 3)
                for _ in range(count)
            ]

        # 5. Heating / Thermal Subsystem Update
        # Gross thermal generated by running CHPs
        self.heating.chp_thermal_generation_kw = round(total_chp_thermal_generation_kw, 2)
        self.heating.recoverable_thermal_kw = round(total_chp_thermal_generation_kw, 2)
        
        # Station heating demand: bounded by MAX_STATION_HEATING_DEMAND_KW = 155.0 kWth
        # Demand varies slightly with ambient temperature and occupancy
        temp_deficit = max(0.0, 18.0 - self.ambient_temperature_c)  # target indoor ~18°C
        demand_kw = min(MAX_STATION_HEATING_DEMAND_KW, 55.0 + (temp_deficit / 50.0) * 80.0 + self._rng.uniform(-2.0, 2.0))
        self.heating.station_heating_demand_kw = round(demand_kw, 2)
        
        # Useful thermal output: bounded by both recoverable heat and heating demand
        self.heating.useful_thermal_output_kw = round(min(self.heating.recoverable_thermal_kw, self.heating.station_heating_demand_kw), 2)
        
        # Supply and return temperatures:
        # Supply is strictly higher than return when useful heat is delivered
        if self.heating.useful_thermal_output_kw > 5.0:
            self.heating.heating_pump_status = "RUNNING"
            # Delta T correlated with useful thermal output / mass flow
            delta_t = 10.0 + (self.heating.useful_thermal_output_kw / MAX_STATION_HEATING_DEMAND_KW) * 12.0
            self.heating.heating_supply_temperature_c = round(68.0 + self._rng.uniform(-0.4, 0.4), 1)
            self.heating.heating_return_temperature_c = round(self.heating.heating_supply_temperature_c - delta_t, 1)
            self.heating.glycol_temperature_c = round(self.heating.heating_supply_temperature_c - 2.0, 1)
            self.heating.buffer_tank_temperature_c = round(self.heating.heating_supply_temperature_c - 3.5, 1)
            self.heating.hot_water_temperature_c = round(58.0 + self._rng.uniform(-0.3, 0.3), 1)
            self.heating.heating_pump_flow = round(12.5 + self._rng.uniform(-0.1, 0.1), 1)
            self.heating.heating_pump_pressure = round(2.4 + self._rng.uniform(-0.05, 0.05), 2)
        else:
            self.heating.heating_pump_status = "STANDBY"
            self.heating.heating_supply_temperature_c = round(35.0, 1)
            self.heating.heating_return_temperature_c = round(35.0, 1)
            self.heating.glycol_temperature_c = round(35.0, 1)
            self.heating.buffer_tank_temperature_c = round(35.0, 1)
            self.heating.hot_water_temperature_c = round(40.0, 1)
            self.heating.heating_pump_flow = 0.0
            self.heating.heating_pump_pressure = 0.5
            
        self.heating.glycol_pressure_bar = round(GLYCOL_LOOP_PRESSURE_NOMINAL_BAR + self._rng.uniform(-0.05, 0.05), 2)
