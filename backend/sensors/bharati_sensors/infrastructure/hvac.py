"""HVAC, mechanical ventilation, and air quality sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_hvac_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_hvac_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate AHU, duct pressure, ventilation fan, and air quality sensors."""
    configs = build_hvac_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        # AHU-01
        "BHARATI-HVAC-AHU01-SUPPLY-TEMP": lambda: state.hvac.ahu01_supply_temp_c,
        "BHARATI-HVAC-AHU01-RETURN-TEMP": lambda: state.hvac.ahu01_return_temp_c,
        "BHARATI-HVAC-AHU01-SUPPLY-PRESS": lambda: state.hvac.ahu01_supply_pressure_pa,
        "BHARATI-HVAC-AHU01-RETURN-PRESS": lambda: state.hvac.ahu01_return_pressure_pa,
        "BHARATI-HVAC-AHU01-DIFF-PRESS": lambda: state.hvac.ahu01_filter_dp_pa,
        "BHARATI-HVAC-AHU01-AIRFLOW": lambda: state.hvac.ahu01_airflow_m3_h,
        "BHARATI-HVAC-AHU01-FAN-STATUS": lambda: "RUNNING" if state.hvac.ahu01_fan_running else "STOPPED",
        "BHARATI-HVAC-AHU01-FAN-SPEED": lambda: state.hvac.ahu01_fan_speed_pct,
        "BHARATI-HVAC-AHU01-HEAT-VALVE": lambda: state.hvac.ahu01_heating_valve_pct,
        "BHARATI-HVAC-AHU01-DAMPER-POS": lambda: state.hvac.ahu01_fresh_air_damper_pct,
        
        # AHU-02
        "BHARATI-HVAC-AHU02-SUPPLY-TEMP": lambda: state.hvac.ahu02_supply_temp_c,
        "BHARATI-HVAC-AHU02-RETURN-TEMP": lambda: state.hvac.ahu02_return_temp_c,
        "BHARATI-HVAC-AHU02-SUPPLY-PRESS": lambda: state.hvac.ahu02_supply_pressure_pa,
        "BHARATI-HVAC-AHU02-RETURN-PRESS": lambda: state.hvac.ahu02_return_pressure_pa,
        "BHARATI-HVAC-AHU02-DIFF-PRESS": lambda: state.hvac.ahu02_filter_dp_pa,
        "BHARATI-HVAC-AHU02-AIRFLOW": lambda: state.hvac.ahu02_airflow_m3_h,
        "BHARATI-HVAC-AHU02-FAN-STATUS": lambda: "RUNNING" if state.hvac.ahu02_fan_running else "STOPPED",
        "BHARATI-HVAC-AHU02-FAN-SPEED": lambda: state.hvac.ahu02_fan_speed_pct,
        "BHARATI-HVAC-AHU02-HEAT-VALVE": lambda: state.hvac.ahu02_heating_valve_pct,
        "BHARATI-HVAC-AHU02-DAMPER-POS": lambda: state.hvac.ahu02_fresh_air_damper_pct,
        
        # IAQ & Auxiliary
        "BHARATI-HVAC-Z01-CO2": lambda: state.hvac.co2_living_ppm,
        "BHARATI-HVAC-Z01-CO": lambda: state.hvac.co_living_ppm,
        "BHARATI-HVAC-Z02-CO2": lambda: state.hvac.co2_lab_ppm,
        "BHARATI-HVAC-Z02-CO": lambda: state.hvac.co_lab_ppm,
        "BHARATI-HVAC-EXHAUST-FAN-STATUS": lambda: "RUNNING" if state.hvac.exhaust_fan_running else "STOPPED",
        "BHARATI-HVAC-HUMIDIFIER-STATUS": lambda: "ACTIVE" if state.hvac.humidifier_active else "STANDBY",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for HVAC sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
