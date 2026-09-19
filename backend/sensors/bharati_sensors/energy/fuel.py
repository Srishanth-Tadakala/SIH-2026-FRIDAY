"""Sensor representations for Bharati Station Fuel Infrastructure.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from .base import BaseSensor, DerivedSensor, StateBoundSensor
from .clock import SimulationClock
from .config import build_fuel_sensor_configs
from .models import SensorKind, SensorValue
from .physics_state import FuelPhysicalState


def create_fuel_sensors(
    fuel_state: FuelPhysicalState,
    clock: SimulationClock,
) -> list[BaseSensor]:
    """Instantiate the fuel storage, transfer, and autonomy sensor suite.
    
    Observes bulk storage, day tank, flow, temperatures, and leak/overfill status.
    Provides derived total available fuel and autonomy calculations.
    """
    configs = build_fuel_sensor_configs()
    sensors: list[BaseSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "bulk_fuel_level_l": lambda: round(fuel_state.bulk_fuel_level_l, 1),
        "bulk_fuel_level_percent": lambda: round((fuel_state.bulk_fuel_level_l / fuel_state.bulk_capacity_l) * 100.0, 1),
        "day_tank_level_l": lambda: round(fuel_state.day_tank_level_l, 1),
        "day_tank_level_percent": lambda: round((fuel_state.day_tank_level_l / fuel_state.day_tank_capacity_l) * 100.0, 1),
        "fuel_temperature_c": lambda: fuel_state.fuel_temperature_c,
        "fuel_flow_lph": lambda: fuel_state.fuel_flow_lph,
        "leak_status": lambda: fuel_state.leak_status,
        "overfill_status": lambda: fuel_state.overfill_status,
    }

    def calc_total_available() -> float:
        return round(fuel_state.bulk_fuel_level_l + fuel_state.day_tank_level_l, 1)

    def calc_fuel_autonomy() -> float:
        total_fuel = fuel_state.bulk_fuel_level_l + fuel_state.day_tank_level_l
        flow = fuel_state.fuel_flow_lph
        if flow <= 0.01:
            return 99999.0  # Infinite autonomy when zero consumption
        return round(total_fuel / flow, 1)

    derived_calcs: dict[str, Callable[[], SensorValue]] = {
        "total_available_fuel_l": calc_total_available,
        "estimated_fuel_autonomy_hours": calc_fuel_autonomy,
    }

    for cfg in configs:
        if cfg.kind == SensorKind.DERIVED:
            calc = derived_calcs.get(cfg.parameter)
            if calc is None:
                raise KeyError(f"No derived calculator defined for fuel parameter: {cfg.parameter}")
            sensors.append(DerivedSensor(cfg, clock, calc))
        else:
            getter = getters.get(cfg.parameter)
            if getter is None:
                raise KeyError(f"No getter defined for fuel parameter: {cfg.parameter}")
            sensors.append(StateBoundSensor(cfg, clock, getter))

    return sensors
