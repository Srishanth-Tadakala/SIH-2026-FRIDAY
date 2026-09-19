"""Building envelope and structural health sensor group.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
"""

from __future__ import annotations

from typing import Callable

from ..energy.clock import SimulationClock
from .base import BaseInfrastructureSensor, StateBoundInfrastructureSensor
from .config import build_building_sensor_configs
from .models import SensorValue
from .physics_state import BharatiInfrastructurePhysicsState


def create_building_sensors(
    state: BharatiInfrastructurePhysicsState,
    clock: SimulationClock,
) -> list[BaseInfrastructureSensor]:
    """Instantiate building thermal, environmental, and structural sensors."""
    configs = build_building_sensor_configs()
    sensors: list[BaseInfrastructureSensor] = []

    getters: dict[str, Callable[[], SensorValue]] = {
        "BHARATI-BLDG-Z01-TEMP": lambda: state.building.temp_living_c,
        "BHARATI-BLDG-Z01-HUM": lambda: state.building.humidity_living_pct,
        "BHARATI-BLDG-Z02-TEMP": lambda: state.building.temp_lab_c,
        "BHARATI-BLDG-Z02-HUM": lambda: state.building.humidity_lab_pct,
        "BHARATI-BLDG-Z03-TEMP": lambda: state.building.temp_technical_c,
        "BHARATI-BLDG-OCCUPANCY": lambda: state.building.occupancy_count,
        "BHARATI-BLDG-ENV-TEMP-NORTH": lambda: state.building.envelope_temp_north_c,
        "BHARATI-BLDG-ENV-TEMP-SOUTH": lambda: state.building.envelope_temp_south_c,
        "BHARATI-BLDG-ROOF-SNOW-LOAD": lambda: state.building.roof_snow_load_kpa,
        "BHARATI-BLDG-MAIN-DOOR-STATUS": lambda: "OPEN" if state.building.main_airlock_door_open else "CLOSED",
        "BHARATI-STRUCT-BUILDING-TILT-X": lambda: state.structural.building_tilt_x_mrad,
        "BHARATI-STRUCT-BUILDING-TILT-Y": lambda: state.structural.building_tilt_y_mrad,
        "BHARATI-STRUCT-PILLAR-STRAIN-01": lambda: state.structural.pillar_01_strain_ustrain,
        "BHARATI-STRUCT-PILLAR-STRAIN-43": lambda: state.structural.pillar_43_strain_ustrain,
        "BHARATI-STRUCT-PILLAR-STRAIN-86": lambda: state.structural.pillar_86_strain_ustrain,
        "BHARATI-STRUCT-FOUNDATION-DISP": lambda: state.structural.foundation_disp_mm,
        "BHARATI-STRUCT-VIBRATION-RMS": lambda: state.structural.vibration_rms_mm_s,
        "BHARATI-STRUCT-JOINT-DISP": lambda: state.structural.joint_disp_mm,
    }

    for cfg in configs:
        getter = getters.get(cfg.sensor_id)
        if getter is None:
            raise KeyError(f"No getter registered for building sensor: {cfg.sensor_id}")
        sensors.append(StateBoundInfrastructureSensor(cfg, clock, getter))

    return sensors
