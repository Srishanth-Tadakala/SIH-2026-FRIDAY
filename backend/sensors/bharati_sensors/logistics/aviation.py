"""Aviation logistics observation sensors for Bharati Station.

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


def create_aviation_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 7 aviation telemetry and helipad observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-AV-HELI-STATUS": lambda: state.aviation.heli.status,
        "LOG-AV-HELI-AIRBORNE": lambda: state.aviation.heli.is_airborne,
        "LOG-AV-HELI-FUEL-PCT": lambda: state.aviation.heli.fuel_remaining_percent,
        "LOG-AV-HELI-ALTITUDE": lambda: state.aviation.heli.altitude_m,
        "LOG-AV-HELI-GROUND-SPEED": lambda: state.aviation.heli.ground_speed_km_h,
        "LOG-AV-HELI-FLIGHT-HRS": lambda: state.aviation.heli.cumulative_flight_hours,
        "LOG-AV-HELIPAD-STATUS": lambda: state.aviation.helipad_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.AVIATION:
            raise KeyError(f"Configuration missing or invalid domain for aviation sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
