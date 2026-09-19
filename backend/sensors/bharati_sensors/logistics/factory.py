"""Factory for assembling the complete Bharati Station Logistics Observation Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Assembles:
- BharatiLogisticsPhysicsState
- SimulationClock
- 98 sensors across 11 domains:
    Fleet: 16
    Cargo: 10
    Fuel: 10
    Cold Chain: 8
    Aviation: 7
    Marine: 7
    Routes: 8
    Missions: 9
    Inventory: 10
    Waste: 5
    Derived: 8
- LogisticsSensorRegistry
"""

from __future__ import annotations

from ..energy.clock import SimulationClock
from .aviation import create_aviation_sensors
from .cargo import create_cargo_sensors
from .cold_chain import create_cold_chain_sensors
from .derived import create_derived_sensors
from .fleet import create_fleet_sensors
from .fuel import create_fuel_sensors
from .inventory import create_inventory_sensors
from .marine import create_marine_sensors
from .missions import create_missions_sensors
from .physics_state import BharatiLogisticsPhysicsState
from .registry import LogisticsSensorRegistry
from .routes import create_routes_sensors
from .waste import create_waste_sensors


def create_bharati_logistics_sensors(
    seed: int | None = None,
    clock: SimulationClock | None = None,
) -> tuple[LogisticsSensorRegistry, BharatiLogisticsPhysicsState, SimulationClock]:
    """Assemble and configure all 98 Bharati logistics observation points into a registry.
    
    Returns:
        (registry, physics_state, clock) tuple ready for observation.
    """
    if clock is None:
        clock = SimulationClock()

    physics = BharatiLogisticsPhysicsState(seed=seed)
    registry = LogisticsSensorRegistry(physics=physics, clock=clock)

    # 1. Fleet & Vehicle Telemetry (16 Points)
    for s in create_fleet_sensors(physics, clock):
        registry.register(s)

    # 2. Cargo & Containers (10 Points)
    for s in create_cargo_sensors(physics, clock):
        registry.register(s)

    # 3. Fuel Logistics (10 Points)
    for s in create_fuel_sensors(physics, clock):
        registry.register(s)

    # 4. Cold Chain / Reefers (8 Points)
    for s in create_cold_chain_sensors(physics, clock):
        registry.register(s)

    # 5. Aviation Logistics (7 Points)
    for s in create_aviation_sensors(physics, clock):
        registry.register(s)

    # 6. Marine Logistics (7 Points)
    for s in create_marine_sensors(physics, clock):
        registry.register(s)

    # 7. Routes & Accessibility (8 Points)
    for s in create_routes_sensors(physics, clock):
        registry.register(s)

    # 8. Missions & Personnel (9 Points)
    for s in create_missions_sensors(physics, clock):
        registry.register(s)

    # 9. Inventory & Stores (10 Points)
    for s in create_inventory_sensors(physics, clock):
        registry.register(s)

    # 10. Waste & Madrid Protocol (5 Points)
    for s in create_waste_sensors(physics, clock):
        registry.register(s)

    # 11. Derived Indicators & Condition (8 Points)
    for s in create_derived_sensors(physics, clock):
        registry.register(s)

    # Invariant: exactly 98 points assembled
    if registry.sensor_count != 98:
        raise RuntimeError(
            f"Factory assembly error: expected exactly 98 sensors, but registered {registry.sensor_count}"
        )

    # Pre-populate initial reading cache
    registry.read_all()

    return registry, physics, clock
