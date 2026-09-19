"""Factory for assembling the complete Bharati Station Infrastructure Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from ..energy.clock import SimulationClock
from .bms import create_bms_sensors
from .building import create_building_sensors
from .emergency import create_emergency_sensors
from .environmental_input import EnvironmentalInput
from .fire import create_fire_sensors
from .hvac import create_hvac_sensors
from .physics_state import BharatiInfrastructurePhysicsState
from .pipelines import create_pipeline_sensors
from .refrigeration import create_refrigeration_sensors
from .registry import InfrastructureSensorRegistry
from .security import create_security_sensors
from .virtual import create_virtual_sensors
from .wastewater import create_wastewater_sensors
from .water import create_water_sensors


def create_bharati_infrastructure_sensors(
    seed: int | None = None,
    clock: SimulationClock | None = None,
    environmental_input: EnvironmentalInput | None = None,
) -> InfrastructureSensorRegistry:
    """Create and return a fully assembled Bharati Infrastructure Sensor Registry.

    Instantiates all 11 infrastructure domains:
    1. Building & Structural
    2. HVAC & Indoor Air Quality
    3. Water Intake, RO & Distribution
    4. Wastewater Treatment (MBR)
    5. Fire & Safety
    6. Refrigeration & Cold Provisions
    7. Utilidor & External Pipelines
    8. Emergency Shelter
    9. Physical Access & Facility Security
    10. BMS & Station Communications
    11. Virtual & Derived Indicators

    All sensors observe a coherent underlying physical simulation state.
    """
    sim_clock = clock if clock is not None else SimulationClock()
    physics = BharatiInfrastructurePhysicsState(seed=seed, environmental_input=environmental_input)
    registry = InfrastructureSensorRegistry(physics=physics, clock=sim_clock)

    # 1. Building & Structural
    for sensor in create_building_sensors(physics, sim_clock):
        registry.register(sensor)

    # 2. HVAC & Indoor Air Quality
    for sensor in create_hvac_sensors(physics, sim_clock):
        registry.register(sensor)

    # 3. Water Intake, RO & Distribution
    for sensor in create_water_sensors(physics, sim_clock):
        registry.register(sensor)

    # 4. Wastewater Treatment (MBR)
    for sensor in create_wastewater_sensors(physics, sim_clock):
        registry.register(sensor)

    # 5. Fire & Safety
    for sensor in create_fire_sensors(physics, sim_clock):
        registry.register(sensor)

    # 6. Refrigeration & Cold Provisions
    for sensor in create_refrigeration_sensors(physics, sim_clock):
        registry.register(sensor)

    # 7. Utilidor & External Pipelines
    for sensor in create_pipeline_sensors(physics, sim_clock):
        registry.register(sensor)

    # 8. Emergency Shelter
    for sensor in create_emergency_sensors(physics, sim_clock):
        registry.register(sensor)

    # 9. Physical Access & Facility Security
    for sensor in create_security_sensors(physics, sim_clock):
        registry.register(sensor)

    # 10. BMS & Station Communications
    for sensor in create_bms_sensors(physics, sim_clock):
        registry.register(sensor)

    # 11. Virtual & Derived Indicators
    for sensor in create_virtual_sensors(physics, sim_clock):
        registry.register(sensor)

    # Prime registry with initial physical readings
    registry.read_all()

    return registry
