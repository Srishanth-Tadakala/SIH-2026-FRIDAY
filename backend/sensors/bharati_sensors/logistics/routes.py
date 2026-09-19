"""Route network and transit accessibility observation sensors for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Strict anti-duplication boundary:
Does not duplicate environmental observations (snow depth, ice thickness, wind).
Observes route viability, trafficability, and traverse risk.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import CONFIG_BY_ID
from .models import LogisticsDomain, SensorKind, SensorValue
from .physics_state import BharatiLogisticsPhysicsState


def create_routes_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 8 route and accessibility observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-ROUTE-STATION-STATUS": lambda: state.routes.station_ring_status,
        "LOG-ROUTE-HELIPAD-STATUS": lambda: state.routes.helipad_track_status,
        "LOG-ROUTE-COAST-STATUS": lambda: state.routes.coastal_link_status,
        "LOG-ROUTE-FASTICE-STATUS": lambda: state.routes.fast_ice_route_status,
        "LOG-ROUTE-LARSEMANN-STATUS": lambda: state.routes.larsemann_interstation_status,
        "LOG-ROUTE-VIS-LIMIT": lambda: state.routes.visibility_condition,
        "LOG-ROUTE-CREVASSE-RISK": lambda: state.routes.crevasse_risk,
        "LOG-ROUTE-SURFACE-TRACTION": lambda: state.routes.surface_traction_index,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.ROUTES:
            raise KeyError(f"Configuration missing or invalid domain for route sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
