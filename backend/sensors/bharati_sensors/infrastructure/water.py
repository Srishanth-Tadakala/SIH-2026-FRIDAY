"""Water intake, RO desalination, and potable distribution sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_water_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_water_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate seawater intake, RO plant, and potable reservoir sensors."""
    configs = build_water_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-WATER-INTAKE-FLOW": lambda: state.water.seawater_intake_flow_lph,
        "BHARATI-WATER-INTAKE-PRESS": lambda: state.water.seawater_intake_pressure_bar,
        "BHARATI-WATER-INTAKE-TEMP": lambda: state.water.seawater_intake_temp_c,
        "BHARATI-WATER-INTAKE-PUMP-STAT": lambda: "RUNNING" if state.water.intake_pump_running else "STOPPED",
        "BHARATI-WATER-RO-FEED-PRESS": lambda: state.water.ro_feed_pressure_bar,
        "BHARATI-WATER-RO-PERMEATE-FLOW": lambda: state.water.ro_permeate_flow_lph,
        "BHARATI-WATER-RO-REJECT-FLOW": lambda: state.water.ro_reject_flow_lph,
        "BHARATI-WATER-RO-PERMEATE-COND": lambda: state.water.ro_permeate_conductivity_us_cm,
        "BHARATI-WATER-RO-MEMBRANE-STATUS": lambda: state.water.ro_system_status,
        "BHARATI-WATER-TANK-VOLUME": lambda: state.water.potable_tank_volume_l,
        "BHARATI-WATER-TANK-LEVEL-PCT": lambda: state.water.potable_tank_level_pct,
        "BHARATI-WATER-TANK-TEMP": lambda: state.water.potable_tank_temp_c,
        "BHARATI-WATER-DIST-PRESS": lambda: state.water.distribution_pressure_bar,
        "BHARATI-WATER-DIST-FLOW": lambda: state.water.consumption_flow_lph,
        "BHARATI-WATER-UV-STATUS": lambda: "ACTIVE" if state.water.uv_system_active else "INACTIVE",
        "BHARATI-WATER-CHLORINE-PPM": lambda: state.water.residual_chlorine_ppm,
        "BHARATI-WATER-HOT-WATER-SUPPLY-TEMP": lambda: state.water.domestic_hot_water_temp_c,
        "BHARATI-WATER-CALORIFIER-HEATER-STAT": lambda: "ACTIVE" if state.water.calorifier_backup_heater_on else "STANDBY",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for water sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
