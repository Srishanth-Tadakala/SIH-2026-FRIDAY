"""Mission coordination and field personnel observation sensors for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Strict privacy discipline:
Uses anonymous operational team groups (TEAM-FIELD-01, TEAM-FIELD-02). Zero PII.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import CONFIG_BY_ID
from .models import LogisticsDomain, SensorKind, SensorValue
from .physics_state import BharatiLogisticsPhysicsState


def create_missions_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 9 mission coordination and operational party observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-MISS-ACTIVE-COUNT": lambda: state.missions.active_missions_count,
        "LOG-MISS-STATION-PAX": lambda: state.missions.station_personnel_count,
        "LOG-MISS-FIELD-PAX": lambda: state.missions.field_personnel_count,
        "LOG-MISS-TEAM01-STATUS": lambda: state.missions.team01.status,
        "LOG-MISS-TEAM01-DIST": lambda: state.missions.team01.distance_km,
        "LOG-MISS-TEAM01-RADIO": lambda: state.missions.team01.radio_check_status,
        "LOG-MISS-TEAM01-RETURN-MARGIN": lambda: state.missions.team01.return_margin_minutes,
        "LOG-MISS-TEAM02-STATUS": lambda: state.missions.team02_status,
        "LOG-MISS-READINESS-INDEX": lambda: state.missions.readiness_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.MISSIONS:
            raise KeyError(f"Configuration missing or invalid domain for mission sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
