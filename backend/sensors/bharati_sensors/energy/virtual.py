"""Derived and virtual sensor representations for Bharati Station Energy.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Calculated mathematically from underlying sensor readings and physics state.
"""

from __future__ import annotations

from typing import Callable

from .base import BaseSensor, DerivedSensor
from .clock import SimulationClock
from .config import (
    CHP_RATING_KVA,
    DIESEL_LHV_KWH_PER_L,
    build_virtual_sensor_configs,
)
from .models import SensorValue
from .physics_state import BharatiEnergyPhysicsState


def create_virtual_sensors(
    physics: BharatiEnergyPhysicsState,
    clock: SimulationClock,
) -> list[BaseSensor]:
    """Instantiate virtual and derived station-level energy sensors.
    
    Provides:
    - total_generation_kw
    - total_station_load_kw
    - net_energy_balance_kw
    - total_fuel_l
    - estimated_fuel_autonomy_hours
    - generator_utilization_percent
    - total_thermal_output_kw
    - heating_delta_t
    - critical_load_percent
    - electrical_efficiency_percent
    - total_chp_efficiency_percent
    """
    configs = build_virtual_sensor_configs()
    sensors: list[BaseSensor] = []

    def get_total_generation() -> float:
        total = sum(
            chp.active_power_kw
            for chp in physics.chps
            if chp.operating_state == "RUNNING"
        )
        return round(total, 2)

    def get_total_load() -> float:
        return round(physics.total_station_load_kw, 2)

    def get_net_balance() -> float:
        gen = get_total_generation()
        load = get_total_load()
        return round(gen - load, 2)

    def get_total_fuel() -> float:
        return round(physics.fuel.bulk_fuel_level_l + physics.fuel.day_tank_level_l, 1)

    def get_fuel_autonomy() -> float:
        fuel = get_total_fuel()
        flow = physics.fuel.fuel_flow_lph
        if flow <= 0.01:
            return 99999.0
        return round(fuel / flow, 1)

    def get_generator_utilization() -> float:
        running_chps = [chp for chp in physics.chps if chp.operating_state == "RUNNING"]
        if not running_chps:
            return 0.0
        online_capacity_kw = len(running_chps) * CHP_RATING_KVA  # Nominal kVA ~ nominal kW limit
        gen = get_total_generation()
        return round((gen / online_capacity_kw) * 100.0, 1)

    def get_total_thermal_output() -> float:
        return round(physics.heating.useful_thermal_output_kw, 2)

    def get_heating_delta_t() -> float:
        delta = physics.heating.heating_supply_temperature_c - physics.heating.heating_return_temperature_c
        return round(max(0.0, delta), 1)

    def get_critical_load_percent() -> float:
        total_load = max(physics.total_station_load_kw, 1.0)
        ups_load = sum(u.real_power_kw for u in physics.ups)
        return round((ups_load / total_load) * 100.0, 1)

    def get_electrical_efficiency() -> float:
        flow = physics.fuel.fuel_flow_lph
        fuel_power_kw = flow * DIESEL_LHV_KWH_PER_L
        if fuel_power_kw <= 0.1:
            return 0.0
        gen = get_total_generation()
        return round((gen / fuel_power_kw) * 100.0, 1)

    def get_total_chp_efficiency() -> float:
        flow = physics.fuel.fuel_flow_lph
        fuel_power_kw = flow * DIESEL_LHV_KWH_PER_L
        if fuel_power_kw <= 0.1:
            return 0.0
        gen = get_total_generation()
        thermal = get_total_thermal_output()
        return round(((gen + thermal) / fuel_power_kw) * 100.0, 1)

    calcs: dict[str, Callable[[], SensorValue]] = {
        "total_generation_kw": get_total_generation,
        "total_station_load_kw": get_total_load,
        "net_energy_balance_kw": get_net_balance,
        "total_fuel_l": get_total_fuel,
        "estimated_fuel_autonomy_hours": get_fuel_autonomy,
        "generator_utilization_percent": get_generator_utilization,
        "total_thermal_output_kw": get_total_thermal_output,
        "heating_delta_t": get_heating_delta_t,
        "critical_load_percent": get_critical_load_percent,
        "electrical_efficiency_percent": get_electrical_efficiency,
        "total_chp_efficiency_percent": get_total_chp_efficiency,
    }

    for cfg in configs:
        calc = calcs.get(cfg.parameter)
        if calc is None:
            raise KeyError(f"No calculator defined for virtual parameter: {cfg.parameter}")
        sensors.append(DerivedSensor(cfg, clock, calc))

    return sensors
