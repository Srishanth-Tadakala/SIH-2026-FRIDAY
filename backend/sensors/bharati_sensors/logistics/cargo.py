"""Cargo and container observation sensors for Bharati Station.

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


def create_cargo_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 10 cargo and container observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-CARGO-TOTAL-COUNT": lambda: state.cargo.total_cargo_units,
        "LOG-CARGO-IN-TRANSIT": lambda: state.cargo.in_transit_units,
        "LOG-CARGO-C01-LOC": lambda: state.cargo.c01.location_zone,
        "LOG-CARGO-C01-WEIGHT": lambda: state.cargo.c01.gross_weight_kg,
        "LOG-CARGO-C01-TEMP": lambda: state.cargo.c01.temperature_c,
        "LOG-CARGO-C01-HUM": lambda: state.cargo.c01.relative_humidity_percent,
        "LOG-CARGO-C01-SHOCK": lambda: state.cargo.c01.shock_g,
        "LOG-CARGO-C01-TILT": lambda: state.cargo.c01.tilt_deg,
        "LOG-CARGO-C01-DOOR": lambda: state.cargo.c01.door_status,
        "LOG-CARGO-HAZMAT-STATUS": lambda: state.cargo.hazmat_staging_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.CARGO:
            raise KeyError(f"Configuration missing or invalid domain for cargo sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
