"""Sensor representations for Bharati Station UPS Plants (UPS-1, UPS-2).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from .base import BaseSensor, StateBoundSensor
from .clock import SimulationClock
from .config import build_ups_sensor_configs
from .models import SensorValue
from .physics_state import UPSPhysicalState


def create_ups_sensors(
    ups_state: UPSPhysicalState,
    clock: SimulationClock,
) -> list[BaseSensor]:
    """Instantiate the complete sensor group for a single 60 kVA UPS plant.
    
    Includes 3-phase input/output, bypass, DC link, load, battery system,
    cell module voltages, and subsystem status indicators.
    """
    configs = build_ups_sensor_configs(ups_state.index)
    sensors: list[BaseSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "input_voltage_l1": lambda: ups_state.input_voltage_l1,
        "input_voltage_l2": lambda: ups_state.input_voltage_l2,
        "input_voltage_l3": lambda: ups_state.input_voltage_l3,
        "input_frequency_hz": lambda: ups_state.input_frequency_hz,
        "bypass_voltage": lambda: ups_state.bypass_voltage,
        "bypass_frequency_hz": lambda: ups_state.bypass_frequency_hz,
        "dc_link_voltage": lambda: ups_state.dc_link_voltage,
        "output_voltage_l1": lambda: ups_state.output_voltage_l1,
        "output_voltage_l2": lambda: ups_state.output_voltage_l2,
        "output_voltage_l3": lambda: ups_state.output_voltage_l3,
        "output_frequency_hz": lambda: ups_state.output_frequency_hz,
        "output_current_l1": lambda: ups_state.output_current_l1,
        "output_current_l2": lambda: ups_state.output_current_l2,
        "output_current_l3": lambda: ups_state.output_current_l3,
        "load_percent": lambda: ups_state.load_percent,
        "real_power_kw": lambda: ups_state.real_power_kw,
        "apparent_power_kva": lambda: ups_state.apparent_power_kva,
        "battery_voltage": lambda: ups_state.battery_voltage,
        "battery_current": lambda: ups_state.battery_current,
        "battery_temperature_c": lambda: ups_state.battery_temperature_c,
        "battery_capacity_percent": lambda: ups_state.battery_soc_percent,
        "backup_time_minutes": lambda: ups_state.backup_time_minutes,
        "individual_battery_voltages": lambda: list(ups_state.individual_battery_voltages),
        "rectifier_status": lambda: ups_state.rectifier_status,
        "boost_status": lambda: ups_state.boost_status,
        "battery_status": lambda: ups_state.battery_status,
        "charging_status": lambda: ups_state.charging_status,
        "inverter_status": lambda: ups_state.inverter_status,
        "bypass_status": lambda: ups_state.bypass_status,
        "load_status": lambda: ups_state.load_status,
        "fan_status": lambda: ups_state.fan_status,
    }

    for cfg in configs:
        getter = getters.get(cfg.parameter)
        if getter is None:
            raise KeyError(f"No getter defined for UPS parameter: {cfg.parameter}")
        sensors.append(StateBoundSensor(cfg, clock, getter))

    return sensors
