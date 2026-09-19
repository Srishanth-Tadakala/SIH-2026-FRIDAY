"""Marine and coastal vessel observation sensors for Bharati Station.

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


def create_marine_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 7 marine expedition vessel, barge, and discharge observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-MAR-VESSEL-STATUS": lambda: state.marine.vessel.status,
        "LOG-MAR-VESSEL-DIST": lambda: state.marine.vessel.distance_to_station_km,
        "LOG-MAR-VESSEL-SPEED": lambda: state.marine.vessel.speed_knots,
        "LOG-MAR-BARGE-STATUS": lambda: state.marine.barge_status,
        "LOG-MAR-DISCHARGE-PROGRESS": lambda: state.marine.discharge_progress_percent,
        "LOG-MAR-SEA-BERTH-SAFE": lambda: state.marine.sea_berth_safety,
        "LOG-MAR-UNLOAD-RATE": lambda: state.marine.unloading_rate_tonne_h,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.MARINE:
            raise KeyError(f"Configuration missing or invalid domain for marine sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
