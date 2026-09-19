"""Sensor representations for Bharati Station CHP Units (CHP-1, CHP-2, CHP-3).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from .base import BaseSensor, StateBoundSensor
from .clock import SimulationClock
from .config import build_chp_sensor_configs
from .models import SensorValue
from .physics_state import CHPPhysicalState


def create_chp_sensors(
    chp_state: CHPPhysicalState,
    clock: SimulationClock,
) -> list[BaseSensor]:
    """Instantiate the complete sensor group for a single 100 kVA CHP unit.
    
    Includes electrical, mechanical, thermal, pressure, fuel consumption,
    and operational status sensors.
    """
    configs = build_chp_sensor_configs(chp_state.index)
    sensors: list[BaseSensor] = []

    # Map parameter names to getter functions
    getters: dict[str, Callable[[], SensorValue]] = {
        "active_power_kw": lambda: chp_state.active_power_kw,
        "apparent_power_kva": lambda: chp_state.apparent_power_kva,
        "voltage": lambda: chp_state.voltage,
        "current": lambda: chp_state.current,
        "frequency_hz": lambda: chp_state.frequency_hz,
        "power_factor": lambda: chp_state.power_factor,
        "rpm": lambda: chp_state.rpm,
        "running_status": lambda: chp_state.running_status,
        "operating_state": lambda: chp_state.operating_state,
        "exhaust_temperature_c": lambda: chp_state.exhaust_temperature_c,
        "coolant_temperature_c": lambda: chp_state.coolant_temperature_c,
        "oil_pressure": lambda: chp_state.oil_pressure,
        "coolant_pressure": lambda: chp_state.coolant_pressure,
        "fuel_consumption_lph": lambda: chp_state.fuel_consumption_lph,
        "runtime_hours": lambda: chp_state.runtime_hours,
    }

    for cfg in configs:
        getter = getters.get(cfg.parameter)
        if getter is None:
            raise KeyError(f"No getter defined for CHP parameter: {cfg.parameter}")
        sensors.append(StateBoundSensor(cfg, clock, getter))

    return sensors
