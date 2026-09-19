"""Physical access control and facility security sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_security_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_security_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate access control, intrusion, camera, and facility security sensors."""
    configs = build_security_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-SEC-MAIN-AIRLOCK-LOCK": lambda: "LOCKED" if state.security.main_airlock_locked else "UNLOCKED",
        "BHARATI-SEC-POWER-HOUSE-DOOR": lambda: "OPEN" if state.security.powerhouse_door_open else "CLOSED",
        "BHARATI-SEC-POWER-HOUSE-LOCK": lambda: "LOCKED" if state.security.powerhouse_locked else "UNLOCKED",
        "BHARATI-SEC-FUEL-FARM-GATE": lambda: "OPEN" if state.security.fuel_farm_gate_open else "CLOSED",
        "BHARATI-SEC-UNAUTHORIZED-ACCESS": lambda: state.security.unauthorized_access_detected,
        "BHARATI-SEC-CAM-01-STATUS": lambda: "ONLINE" if state.security.cam_01_online else "OFFLINE",
        "BHARATI-SEC-CAM-02-STATUS": lambda: "ONLINE" if state.security.cam_02_online else "OFFLINE",
        "BHARATI-SEC-CAM-03-STATUS": lambda: "ONLINE" if state.security.cam_03_online else "OFFLINE",
        "BHARATI-SEC-EMERGENCY-CALL-STAT": lambda: state.security.emergency_call_active,
        "BHARATI-SEC-PA-SYSTEM-HEALTH": lambda: state.security.pa_system_healthy,
        "BHARATI-SEC-KEY-VAULT-STATUS": lambda: state.security.key_vault_secure,
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for security sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
