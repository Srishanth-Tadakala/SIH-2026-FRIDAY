"""Cold chain and refrigerated container observation sensors for Bharati Station.

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


def create_cold_chain_sensors(
    state: BharatiLogisticsPhysicsState,
    clock: SimulationClock,
) -> list[BaseLogisticsSensor]:
    """Instantiate 8 cold-chain reefer telemetry and excursion observation points."""
    sensors: list[BaseLogisticsSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "LOG-REEFER-01-TEMP": lambda: state.cold_chain.reefer01.core_temp_c,
        "LOG-REEFER-01-SETPOINT": lambda: state.cold_chain.reefer01.setpoint_c,
        "LOG-REEFER-01-DOOR": lambda: state.cold_chain.reefer01.door_status,
        "LOG-REEFER-01-COMP-RUN": lambda: state.cold_chain.reefer01.compressor_status,
        "LOG-REEFER-01-PWR-STATE": lambda: state.cold_chain.reefer01.power_source,
        "LOG-REEFER-01-EXCURSION": lambda: state.cold_chain.reefer01.temperature_excursion,
        "LOG-REEFER-02-TEMP": lambda: state.cold_chain.reefer02_core_temp_c,
        "LOG-REEFER-02-STATUS": lambda: state.cold_chain.reefer02_status,
    }

    for sensor_id, getter in getters.items():
        cfg = CONFIG_BY_ID.get(sensor_id)
        if cfg is None or cfg.domain != LogisticsDomain.COLD_CHAIN:
            raise KeyError(f"Configuration missing or invalid domain for cold-chain sensor: {sensor_id}")

        if cfg.kind == SensorKind.DERIVED:
            sensors.append(DerivedLogisticsSensor(cfg, clock, getter))
        else:
            sensors.append(StateBoundLogisticsSensor(cfg, clock, getter))

    return sensors
