"""Emergency shelter and life-support sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_emergency_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_emergency_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate emergency shelter life support and self-sufficiency sensors."""
    configs = build_emergency_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-EMERG-SHELTER-TEMP": lambda: state.emergency.shelter_temp_c,
        "BHARATI-EMERG-SHELTER-HUM": lambda: state.emergency.shelter_humidity_pct,
        "BHARATI-EMERG-OCCUPANCY": lambda: state.emergency.occupancy_count,
        "BHARATI-EMERG-GEN-STATUS": lambda: state.emergency.generator_status,
        "BHARATI-EMERG-GEN-FUEL-LEVEL": lambda: state.emergency.generator_fuel_pct,
        "BHARATI-EMERG-BOILER-TEMP": lambda: state.emergency.boiler_temp_c,
        "BHARATI-EMERG-WATER-LEVEL": lambda: state.emergency.water_tank_level_pct,
        "BHARATI-EMERG-SMOKE-DETECT": lambda: state.emergency.smoke_obs_pct,
        "BHARATI-EMERG-CO2": lambda: state.emergency.co2_ppm,
        "BHARATI-EMERG-CO": lambda: state.emergency.co_ppm,
        "BHARATI-EMERG-DOOR-STATUS": lambda: "OPEN" if state.emergency.door_open else "CLOSED",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for emergency sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
