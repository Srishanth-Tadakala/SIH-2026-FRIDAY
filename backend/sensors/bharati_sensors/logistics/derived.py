"""Derived operational logistics indicators and explainable condition for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Deterministic in v1:
Calculated indicators representing fleet availability, cargo integrity, cold-chain risk,
accessibility scores, and explainable condition summaries.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import CONFIG_BY_ID
from .models import LogisticsDomain, SensorKind, SensorValue
from .physics_state import BharatiLogisticsPhysicsState


def create_derived_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 8 derived operational indicators and condition summary."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-DERIVED-FLEET-AVAIL": lambda: state.derived.fleet_availability_percent,
        "LOG-DERIVED-CARGO-INTEGRITY": lambda: state.derived.cargo_integrity_index,
        "LOG-DERIVED-COLD-CHAIN-RISK": lambda: state.derived.cold_chain_risk_score,
        "LOG-DERIVED-ROUTE-ACCESS": lambda: state.derived.ground_route_accessibility_percent,
        "LOG-DERIVED-AIR-ACCESS": lambda: state.derived.aviation_accessibility_percent,
        "LOG-DERIVED-MARINE-ACCESS": lambda: state.derived.marine_accessibility_percent,
        "LOG-DERIVED-LOGISTICS-RISK": lambda: state.derived.composite_logistics_risk,
        "LOG-DERIVED-LOGISTICS-CONDITION": lambda: state.derived.logistics_condition_summary,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.DERIVED:
            raise KeyError(f"Configuration missing or invalid domain for derived sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
