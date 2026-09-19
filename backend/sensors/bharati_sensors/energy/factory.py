"""Factory for assembling the complete Bharati Station Energy Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from .chp import create_chp_sensors
from .clock import SimulationClock
from .fuel import create_fuel_sensors
from .heating import create_heating_sensors
from .physics_state import BharatiEnergyPhysicsState
from .registry import SensorRegistry
from .ups import create_ups_sensors
from .virtual import create_virtual_sensors


def create_bharati_energy_sensors(
    seed: int | None = None,
    clock: SimulationClock | None = None,
) -> SensorRegistry:
    """Create and return a fully assembled Bharati Energy Sensor Registry.
    
    Instantiates:
    - 3 CHP unit sensor suites (CHP-1, CHP-2, CHP-3)
    - 2 UPS plant sensor suites (UPS-1, UPS-2)
    - Fuel storage, distribution, and autonomy sensors
    - Heating and thermal energy recovery sensors
    - Station-level virtual and derived energy sensors
    
    All sensors observe a coherent underlying physics state.
    """
    sim_clock = clock if clock is not None else SimulationClock()
    physics = BharatiEnergyPhysicsState(seed=seed)
    registry = SensorRegistry(physics=physics, clock=sim_clock)

    # 1. Register CHP-1, CHP-2, CHP-3 sensors
    for chp_state in physics.chps:
        for sensor in create_chp_sensors(chp_state, sim_clock):
            registry.register(sensor)

    # 2. Register UPS-1, UPS-2 sensors
    for ups_state in physics.ups:
        for sensor in create_ups_sensors(ups_state, sim_clock):
            registry.register(sensor)

    # 3. Register Fuel sensors
    for sensor in create_fuel_sensors(physics.fuel, sim_clock):
        registry.register(sensor)

    # 4. Register Heating sensors
    for sensor in create_heating_sensors(physics.heating, sim_clock):
        registry.register(sensor)

    # 5. Register Virtual / Derived sensors
    for sensor in create_virtual_sensors(physics, sim_clock):
        registry.register(sensor)

    # Prime registry with initial readings
    registry.read_all()

    return registry
