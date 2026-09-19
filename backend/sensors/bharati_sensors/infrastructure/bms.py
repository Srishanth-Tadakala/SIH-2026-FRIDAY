"""Building Management System (BMS) supervisory and communications telemetry sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_bms_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_bms_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate BMS automation backbone, fieldbus, and station comms sensors."""
    configs = build_bms_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-BMS-DDC01-STATUS": lambda: state.bms.ddc01_online,
        "BHARATI-BMS-DDC02-STATUS": lambda: state.bms.ddc02_online,
        "BHARATI-BMS-GATEWAY-STATUS": lambda: state.bms.fieldbus_gateway_online,
        "BHARATI-BMS-HISTORIAN-STATUS": lambda: state.bms.historian_logging,
        "BHARATI-BMS-POINTS-ONLINE": lambda: state.bms.points_online_count,
        "BHARATI-BMS-POINTS-STALE": lambda: state.bms.points_stale_count,
        "BHARATI-BMS-POINTS-FAILED": lambda: state.bms.points_failed_count,
        "BHARATI-BMS-FIELDBUS-LATENCY": lambda: state.bms.fieldbus_latency_ms,
        "BHARATI-COMMS-SAT-LINK-STATUS": lambda: state.bms.sat_link_connected,
        "BHARATI-COMMS-SAT-SNR": lambda: state.bms.sat_snr_db,
        "BHARATI-COMMS-SAT-LATENCY": lambda: state.bms.sat_rtt_latency_ms,
        "BHARATI-COMMS-VHF-RADIO-HEALTH": lambda: state.bms.vhf_radio_healthy,
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for BMS sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
