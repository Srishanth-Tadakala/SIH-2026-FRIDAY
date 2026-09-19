"""Fire detection, smoke monitoring, and damper status sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_fire_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_fire_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate fire, smoke, thermal detection, and damper status sensors."""
    configs = build_fire_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        # Zone 01 (Living & Accommodation)
        "BHARATI-FIRE-Z01-SMOKE": lambda: state.fire.z01_smoke_obs_pct,
        "BHARATI-FIRE-Z01-TEMP": lambda: state.fire.z01_temp_c,
        "BHARATI-FIRE-Z01-ALARM-STAT": lambda: state.fire.z01_alarm_status,
        "BHARATI-FIRE-Z01-DAMPER-STAT": lambda: "OPEN" if state.fire.z01_damper_open else "CLOSED",
        # Zone 02 (Laboratories & Medical)
        "BHARATI-FIRE-Z02-SMOKE": lambda: state.fire.z02_smoke_obs_pct,
        "BHARATI-FIRE-Z02-TEMP": lambda: state.fire.z02_temp_c,
        "BHARATI-FIRE-Z02-ALARM-STAT": lambda: state.fire.z02_alarm_status,
        "BHARATI-FIRE-Z02-DAMPER-STAT": lambda: "OPEN" if state.fire.z02_damper_open else "CLOSED",
        # Zone 03 (Energy & Mechanical Plant)
        "BHARATI-FIRE-Z03-SMOKE": lambda: state.fire.z03_smoke_obs_pct,
        "BHARATI-FIRE-Z03-TEMP": lambda: state.fire.z03_temp_c,
        "BHARATI-FIRE-Z03-ALARM-STAT": lambda: state.fire.z03_alarm_status,
        "BHARATI-FIRE-Z03-DAMPER-STAT": lambda: "OPEN" if state.fire.z03_damper_open else "CLOSED",
        # Zone 04 (Storage & Services)
        "BHARATI-FIRE-Z04-SMOKE": lambda: state.fire.z04_smoke_obs_pct,
        "BHARATI-FIRE-Z04-TEMP": lambda: state.fire.z04_temp_c,
        "BHARATI-FIRE-Z04-ALARM-STAT": lambda: state.fire.z04_alarm_status,
        "BHARATI-FIRE-Z04-DAMPER-STAT": lambda: "OPEN" if state.fire.z04_damper_open else "CLOSED",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for fire sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
