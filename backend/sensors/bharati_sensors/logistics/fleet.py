"""Fleet and vehicle observation sensors for Bharati Station.

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


def create_fleet_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 16 fleet telemetry and operational status observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-FLEET-PB01-SPEED": lambda: state.fleet.pb01.speed_km_h,
        "LOG-FLEET-PB01-HEADING": lambda: state.fleet.pb01.heading_deg,
        "LOG-FLEET-PB01-RPM": lambda: state.fleet.pb01.engine_rpm,
        "LOG-FLEET-PB01-ENG-TEMP": lambda: state.fleet.pb01.engine_temp_c,
        "LOG-FLEET-PB01-FUEL-LVL": lambda: state.fleet.pb01.fuel_level_percent,
        "LOG-FLEET-PB01-FUEL-RATE": lambda: state.fleet.pb01.fuel_rate_l_h,
        "LOG-FLEET-PB01-BATTERY": lambda: state.fleet.pb01.battery_voltage_v,
        "LOG-FLEET-PB01-ENG-HOURS": lambda: state.fleet.pb01.engine_hours,
        "LOG-FLEET-PB01-STATUS": lambda: state.fleet.pb01.status,
        "LOG-FLEET-PB02-STATUS": lambda: state.fleet.pb02_status,
        "LOG-FLEET-SC01-STATUS": lambda: state.fleet.sc01_status,
        "LOG-FLEET-SC01-FUEL": lambda: state.fleet.sc01_fuel_percent,
        "LOG-FLEET-TH01-HYD-PRESS": lambda: state.fleet.telehandler_hydraulic_pressure_bar,
        "LOG-FLEET-TH01-STATUS": lambda: state.fleet.telehandler_status,
        "LOG-FLEET-EXC01-STATUS": lambda: state.fleet.excavator_status,
        "LOG-FLEET-CRANE01-STATUS": lambda: state.fleet.mantis_crane_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.FLEET:
            raise KeyError(f"Configuration missing or invalid domain for fleet sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
