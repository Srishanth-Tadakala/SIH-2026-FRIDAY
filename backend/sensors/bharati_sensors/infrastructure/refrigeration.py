"""Cold storage and food provision refrigeration sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_refrigeration_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_refrigeration_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate deep freeze and chiller monitoring sensors."""
    configs = build_refrigeration_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        # Deep Freeze (FRZ-01, simulation setpoint -22°C)
        "BHARATI-COLD-FRZ01-TEMP": lambda: state.refrigeration.frz01_temp_c,
        "BHARATI-COLD-FRZ01-EVAP-TEMP": lambda: state.refrigeration.frz01_evap_temp_c,
        "BHARATI-COLD-FRZ01-COND-TEMP": lambda: state.refrigeration.frz01_cond_temp_c,
        "BHARATI-COLD-FRZ01-SUCTION-PRESS": lambda: state.refrigeration.frz01_suction_pressure_bar,
        "BHARATI-COLD-FRZ01-DISCHARGE-PRESS": lambda: state.refrigeration.frz01_discharge_pressure_bar,
        "BHARATI-COLD-FRZ01-DOOR-STATUS": lambda: "OPEN" if state.refrigeration.frz01_door_open else "CLOSED",
        "BHARATI-COLD-FRZ01-COMP-STATUS": lambda: "RUNNING" if state.refrigeration.frz01_compressor_running else "STOPPED",
        "BHARATI-COLD-FRZ01-TEMP-ALARM": lambda: state.refrigeration.frz01_temp_alarm,
        # Chiller / Cool Room (CHL-01, simulation setpoint +3°C)
        "BHARATI-COLD-CHL01-TEMP": lambda: state.refrigeration.chl01_temp_c,
        "BHARATI-COLD-CHL01-EVAP-TEMP": lambda: state.refrigeration.chl01_evap_temp_c,
        "BHARATI-COLD-CHL01-COND-TEMP": lambda: state.refrigeration.chl01_cond_temp_c,
        "BHARATI-COLD-CHL01-SUCTION-PRESS": lambda: state.refrigeration.chl01_suction_pressure_bar,
        "BHARATI-COLD-CHL01-DISCHARGE-PRESS": lambda: state.refrigeration.chl01_discharge_pressure_bar,
        "BHARATI-COLD-CHL01-DOOR-STATUS": lambda: "OPEN" if state.refrigeration.chl01_door_open else "CLOSED",
        "BHARATI-COLD-CHL01-COMP-STATUS": lambda: "RUNNING" if state.refrigeration.chl01_compressor_running else "STOPPED",
        "BHARATI-COLD-CHL01-TEMP-ALARM": lambda: state.refrigeration.chl01_temp_alarm,
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for refrigeration sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
