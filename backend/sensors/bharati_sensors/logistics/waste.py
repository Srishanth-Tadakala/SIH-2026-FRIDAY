"""Waste handling and return logistics observation sensors for Bharati Station.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Environmental treaty compliance:
Governed under the Protocol on Environmental Protection to the Antarctic Treaty (Madrid Protocol).
Strict total removal mandate for non-combustible and hazardous expedition wastes.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseLogisticsSensor, DerivedLogisticsSensor, StateBoundLogisticsSensor
from .config import CONFIG_BY_ID
from .models import LogisticsDomain, SensorKind, SensorValue
from .physics_state import BharatiLogisticsPhysicsState


def create_waste_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 5 waste containment and backhaul readiness observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-WASTE-SOLID-VOL": lambda: state.waste.solid_waste_volume_m3,
        "LOG-WASTE-SOLID-PCT": lambda: state.waste.solid_storage_percent,
        "LOG-WASTE-HAZARD-VOL": lambda: state.waste.hazard_waste_volume_l,
        "LOG-WASTE-HAZARD-STATUS": lambda: state.waste.hazard_containment_status,
        "LOG-WASTE-RET-READY": lambda: state.waste.return_shipment_readiness_percent,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.WASTE:
            raise KeyError(f"Configuration missing or invalid domain for waste sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
