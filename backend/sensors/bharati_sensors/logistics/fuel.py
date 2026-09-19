"""Fuel logistics observation sensors for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import CONFIG_BY_ID
from .models import LogisticsDomain, SensorKind, SensorValue
from .physics_state import BharatiLogisticsPhysicsState


def create_fuel_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 10 fuel logistics, vehicle dispensing, and line observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-FUEL-HELI-SUPPLY-LVL": lambda: state.fuel.heli_supply_level_l,
        "LOG-FUEL-HELI-SUPPLY-PCT": lambda: state.fuel.heli_supply_percent,
        "LOG-FUEL-VEH-TANK-LVL": lambda: state.fuel.vehicle_tank_level_l,
        "LOG-FUEL-VEH-TANK-PCT": lambda: state.fuel.vehicle_tank_percent,
        "LOG-FUEL-LINE-TEMP": lambda: state.fuel.line_temperature_c,
        "LOG-FUEL-LINE-PRESS": lambda: state.fuel.line_pressure_bar,
        "LOG-FUEL-TRANSFER-FLOW": lambda: state.fuel.transfer_flow_l_min,
        "LOG-FUEL-DISPENSED-DAILY": lambda: state.fuel.daily_dispensed_l,
        "LOG-FUEL-LEAK-MONITOR": lambda: state.fuel.leak_status,
        "LOG-FUEL-DISP-STATUS": lambda: state.fuel.dispenser_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.FUEL:
            raise KeyError(f"Configuration missing or invalid domain for fuel sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
