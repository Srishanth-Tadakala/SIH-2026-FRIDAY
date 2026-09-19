"""Derived analytical, performance, and risk indicator sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, DerivedInfrastructureSensor
from .config import (
    BUILDING_HEAT_LOSS_COEFF_W_K,
    build_virtual_sensor_configs,
)
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_virtual_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate derived engineering calculations and digital-twin health indicators."""
    configs = build_virtual_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    calculators: dict[str, Callable[[], SensorValue]] = {
        # Thermal & Building
        "BHARATI-VIRT-BUILDING-HEAT-LOSS": lambda: round(
            BUILDING_HEAT_LOSS_COEFF_W_K
            * max(0.0, state.building.temp_living_c - state.env.ambient_temperature_c)
            / 1000.0,
            2,
        ),
        "BHARATI-VIRT-ZONE-TEMP-DEVIATION": lambda: round(
            abs(state.building.temp_living_c - state.building.temp_lab_c), 2
        ),
        "BHARATI-VIRT-OCCUPANCY-DENSITY": lambda: round(
            (state.building.occupancy_count / 2150.0) * 100.0, 2
        ),
        # HVAC & Indoor Air Quality
        "BHARATI-VIRT-HVAC-HEATING-LOAD": lambda: round(
            ((state.hvac.ahu01_heating_valve_pct + state.hvac.ahu02_heating_valve_pct) / 200.0) * 110.0,
            2,
        ),
        "BHARATI-VIRT-VENTILATION-EFFECTIVENESS": lambda: round(
            max(0.0, min(100.0, 100.0 - max(0.0, state.hvac.co2_living_ppm - 400.0) * 0.08)),
            1,
        ),
        "BHARATI-VIRT-AIR-QUALITY-INDEX": lambda: round(
            max(
                0.0,
                min(
                    100.0,
                    100.0
                    - max(0.0, state.hvac.co2_living_ppm - 400.0) * 0.05
                    - state.hvac.co_living_ppm * 5.0,
                ),
            ),
            1,
        ),
        # Water & Wastewater
        "BHARATI-VIRT-WATER-RESERVE-DAYS": lambda: round(
            state.water.potable_tank_volume_l / max(1.0, state.water.consumption_flow_lph * 24.0),
            2,
        ),
        "BHARATI-VIRT-RO-RECOVERY-RATIO": lambda: round(
            min(75.0, (state.water.ro_permeate_flow_lph / max(1.0, state.water.seawater_intake_flow_lph)) * 100.0),
            1,
        ),
        "BHARATI-VIRT-WWTP-EFFICIENCY": lambda: round(
            max(0.0, min(100.0, 100.0 - (state.wastewater.effluent_cod_mg_l / 350.0) * 100.0)),
            1,
        ),
        "BHARATI-VIRT-WWTP-BUFFER-CAPACITY": lambda: round(
            max(0.0, 100.0 - (state.wastewater.grey_sump_level_pct + state.wastewater.black_sump_level_pct) / 2.0),
            1,
        ),
        # Cold Storage & Refrigeration
        "BHARATI-VIRT-COLD-STORAGE-RISK": lambda: round(
            max(
                0.0,
                min(
                    100.0,
                    max(0.0, state.refrigeration.frz01_temp_c - (-18.0)) * 10.0
                    + max(0.0, state.refrigeration.chl01_temp_c - 5.0) * 10.0,
                ),
            ),
            1,
        ),
        "BHARATI-VIRT-REFRIG-COP": lambda: round(
            max(
                0.0,
                min(
                    8.0,
                    (state.refrigeration.frz01_evap_temp_c + 273.15)
                    / max(1.0, state.refrigeration.frz01_cond_temp_c - state.refrigeration.frz01_evap_temp_c)
                    * 0.45,
                ),
            ),
            2,
        ),
        # Pipelines & Utilidors
        "BHARATI-VIRT-PIPE-FREEZE-RISK": lambda: round(
            max(
                0.0,
                min(
                    100.0,
                    (10.0 - state.pipelines.water01_pipe_temp_c)
                    * (5.0 if not state.pipelines.water01_trace_heating_on else 0.5),
                ),
            ),
            1,
        ),
        "BHARATI-VIRT-PIPE-LEAK-RISK": lambda: 100.0
        if (
            state.pipelines.fuel01_leak_detected
            or state.pipelines.water01_leak_detected
            or state.pipelines.heat01_leak_detected
        )
        else 0.0,
        # Structural Condition
        "BHARATI-VIRT-STRUCT-CONDITION-INDICATOR": lambda: round(
            max(
                0.0,
                min(
                    100.0,
                    100.0
                    - (abs(state.structural.pillar_01_strain_ustrain) / 40.0)
                    - (abs(state.structural.building_tilt_x_mrad) * 15.0),
                ),
            ),
            1,
        ),
        "BHARATI-VIRT-FOUNDATION-DISP-INDICATOR": lambda: round(
            max(0.0, min(100.0, 100.0 - abs(state.structural.foundation_disp_mm) * 10.0)),
            1,
        ),
        # BMS & Auxiliary Power
        "BHARATI-VIRT-BMS-TELEMETRY-HEALTH": lambda: round(
            min(
                100.0,
                (
                    state.bms.points_online_count
                    / max(
                        1.0,
                        state.bms.points_online_count
                        + state.bms.points_stale_count
                        + state.bms.points_failed_count,
                    )
                )
                * 100.0,
            ),
            1,
        ),
        "BHARATI-VIRT-TOTAL-AUX-POWER": lambda: round(state.calculate_total_auxiliary_power_kw(), 2),
    }

    for cfg in configs:
        calc = calculators.get(cfg.sensor_id)
        if calc is None:
            raise KeyError(f"No calculator registered for virtual sensor: {cfg.sensor_id}")
        sensors.append(DerivedInfrastructureSensor(cfg, clock, calc))

    return sensors
