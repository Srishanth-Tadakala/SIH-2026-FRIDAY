"""Sensor representations for Bharati Station Heating and Thermal Recovery Systems.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from .base import BaseSensor, DerivedSensor, StateBoundSensor
from .clock import SimulationClock
from .config import build_heating_sensor_configs
from .models import SensorKind, SensorValue
from .physics_state import HeatingPhysicalState


def create_heating_sensors(
    heating_state: HeatingPhysicalState,
    clock: SimulationClock,
) -> list[BaseSensor]:
    """Instantiate the heating loop and thermal energy recovery sensors.
    
    Observes supply, return, glycol loop, buffer tank, domestic hot water,
    pumps, and CHP thermal extraction.
    Provides derived heating Delta T and estimated useful thermal delivery.
    """
    configs = build_heating_sensor_configs()
    sensors: list[BaseSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "heating_supply_temperature_c": lambda: heating_state.heating_supply_temperature_c,
        "heating_return_temperature_c": lambda: heating_state.heating_return_temperature_c,
        "glycol_temperature_c": lambda: heating_state.glycol_temperature_c,
        "glycol_pressure_bar": lambda: heating_state.glycol_pressure_bar,
        "buffer_tank_temperature_c": lambda: heating_state.buffer_tank_temperature_c,
        "hot_water_temperature_c": lambda: heating_state.hot_water_temperature_c,
        "heating_pump_status": lambda: heating_state.heating_pump_status,
        "heating_pump_flow": lambda: heating_state.heating_pump_flow,
        "heating_pump_pressure": lambda: heating_state.heating_pump_pressure,
        "thermal_output_kw": lambda: heating_state.useful_thermal_output_kw,
    }

    def calc_delta_t() -> float:
        delta = heating_state.heating_supply_temperature_c - heating_state.heating_return_temperature_c
        return round(max(0.0, delta), 1)

    def calc_estimated_thermal() -> float:
        return round(heating_state.useful_thermal_output_kw, 2)

    derived_calcs: dict[str, Callable[[], SensorValue]] = {
        "heating_delta_t": calc_delta_t,
        "estimated_thermal_output_kw": calc_estimated_thermal,
    }

    for cfg in configs:
        if cfg.kind == SensorKind.DERIVED:
            calc = derived_calcs.get(cfg.parameter)
            if calc is None:
                raise KeyError(f"No derived calculator defined for heating parameter: {cfg.parameter}")
            sensors.append(DerivedSensor(cfg, clock, calc))
        else:
            getter = getters.get(cfg.parameter)
            if getter is None:
                raise KeyError(f"No getter defined for heating parameter: {cfg.parameter}")
            sensors.append(StateBoundSensor(cfg, clock, getter))

    return sensors
