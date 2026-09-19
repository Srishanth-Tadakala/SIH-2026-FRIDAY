"""Wastewater treatment (MBR) and effluent compliance sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_wastewater_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_wastewater_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate MBR wastewater treatment and effluent monitoring sensors."""
    configs = build_wastewater_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-WWTP-INLET-FLOW": lambda: state.wastewater.inlet_flow_lph,
        "BHARATI-WWTP-GREY-SUMP-LEVEL": lambda: state.wastewater.grey_sump_level_pct,
        "BHARATI-WWTP-BLACK-SUMP-LEVEL": lambda: state.wastewater.black_sump_level_pct,
        "BHARATI-WWTP-GALLEY-SUMP-LEVEL": lambda: state.wastewater.galley_sump_level_pct,
        "BHARATI-WWTP-AERATION-TANK-LEVEL": lambda: state.wastewater.aeration_basin_level_pct,
        "BHARATI-WWTP-AERATION-DO": lambda: state.wastewater.dissolved_oxygen_mg_l,
        "BHARATI-WWTP-BLOWER-STATUS": lambda: "RUNNING" if state.wastewater.aeration_blower_running else "STOPPED",
        "BHARATI-WWTP-MEMBRANE-TMP": lambda: state.wastewater.membrane_tmp_bar,
        "BHARATI-WWTP-OUTLET-FLOW": lambda: state.wastewater.effluent_discharge_flow_lph,
        "BHARATI-WWTP-EFFLUENT-COD": lambda: state.wastewater.effluent_cod_mg_l,
        "BHARATI-WWTP-EFFLUENT-BOD": lambda: state.wastewater.effluent_bod_mg_l,
        "BHARATI-WWTP-EFFLUENT-AMMONIA": lambda: state.wastewater.effluent_ammonia_mg_l,
        "BHARATI-WWTP-EFFLUENT-PH": lambda: state.wastewater.effluent_ph,
        "BHARATI-WWTP-EFFLUENT-TEMP": lambda: state.wastewater.effluent_temp_c,
        "BHARATI-WWTP-SLUDGE-LEVEL": lambda: state.wastewater.sludge_holding_level_pct,
        "BHARATI-WWTP-PERMEATE-PUMP-STAT": lambda: "RUNNING" if state.wastewater.permeate_pump_running else "STOPPED",
        "BHARATI-WWTP-TREATMENT-STATUS": lambda: state.wastewater.treatment_mode,
        "BHARATI-WWTP-DISCHARGE-VALVE-STAT": lambda: "OPEN" if state.wastewater.outfall_valve_open else "CLOSED",
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for wastewater sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
