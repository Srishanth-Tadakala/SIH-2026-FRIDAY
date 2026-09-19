"""Inventory stores and supply autonomy observation sensors for Bharati Station.

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


def create_inventory_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 10 inventory, rations autonomy, and spares observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-INV-RATIONS-DAYS": lambda: state.inventory.rations_autonomy_days,
        "LOG-INV-RATIONS-STOCK": lambda: state.inventory.rations_stock_percent,
        "LOG-INV-MEDICAL-STATUS": lambda: state.inventory.medical_supplies_status,
        "LOG-INV-SPARES-GEN-PCT": lambda: state.inventory.generator_spares_percent,
        "LOG-INV-SPARES-VEH-PCT": lambda: state.inventory.vehicle_spares_percent,
        "LOG-INV-WATER-TREAT-PCT": lambda: state.inventory.water_treatment_spares_percent,
        "LOG-INV-BATTERY-STORES": lambda: state.inventory.emergency_batteries_count,
        "LOG-INV-SAFETY-PPE-PCT": lambda: state.inventory.ppe_gear_percent,
        "LOG-INV-CRITICAL-ALERTS": lambda: state.inventory.critical_stockout_alerts_count,
        "LOG-INV-STOCKOUT-RISK": lambda: state.inventory.stockout_risk_score,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.INVENTORY:
            raise KeyError(f"Configuration missing or invalid domain for inventory sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
