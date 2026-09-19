"""Utilidor and external pipe bridge telemetry sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_pipeline_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_pipeline_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate utilidor water, fuel, and hydronic trace-heated pipeline sensors."""
    configs = build_pipeline_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        # Water Utilidor (Seawater / Potable)
        "BHARATI-PIPE-WATER01-TEMP": lambda: state.pipelines.water01_pipe_temp_c,
        "BHARATI-PIPE-WATER01-PRESS": lambda: state.pipelines.water01_pressure_bar,
        "BHARATI-PIPE-WATER01-FLOW": lambda: state.pipelines.water01_flow_lph,
        "BHARATI-PIPE-WATER01-TRACE-HEAT-STAT": lambda: "ACTIVE" if state.pipelines.water01_trace_heating_on else "INACTIVE",
        "BHARATI-PIPE-WATER01-LEAK-STAT": lambda: "ALARM" if state.pipelines.water01_leak_detected else "NORMAL",
        # Fuel Line (Fuel Farm to Generator House)
        "BHARATI-PIPE-FUEL01-TEMP": lambda: state.pipelines.fuel01_pipe_temp_c,
        "BHARATI-PIPE-FUEL01-PRESS": lambda: state.pipelines.fuel01_pressure_bar,
        "BHARATI-PIPE-FUEL01-FLOW": lambda: state.pipelines.fuel01_flow_lph,
        "BHARATI-PIPE-FUEL01-TRACE-HEAT-STAT": lambda: "ACTIVE" if state.pipelines.fuel01_trace_heating_on else "INACTIVE",
        "BHARATI-PIPE-FUEL01-LEAK-STAT": lambda: "ALARM" if state.pipelines.fuel01_leak_detected else "NORMAL",
        # Hydronic District Heating Loop
        "BHARATI-PIPE-HEAT01-TEMP": lambda: state.pipelines.heat01_pipe_temp_c,
        "BHARATI-PIPE-HEAT01-PRESS": lambda: state.pipelines.heat01_pressure_bar,
        "BHARATI-PIPE-HEAT01-FLOW": lambda: state.pipelines.heat01_flow_lph,
        "BHARATI-PIPE-HEAT01-TRACE-HEAT-STAT": lambda: "ACTIVE" if state.pipelines.heat01_trace_heating_on else "INACTIVE",
        "BHARATI-PIPE-HEAT01-LEAK-STAT": lambda: "ALARM" if state.pipelines.heat01_leak_detected else "NORMAL",
        # Isolation Valve
        "BHARATI-PIPE-MAIN-ISOLATION-VALVE": lambda: "OPEN" if state.pipelines.main_isolation_valve_open else "CLOSED",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for pipeline sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
