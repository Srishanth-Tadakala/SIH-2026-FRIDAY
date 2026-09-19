"""Coupled simulation and physics state for Bharati Logistics Observation Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Maintains:
- Single Source of Truth: BharatiLogisticsPhysicsState
- 11 Domain sub-states coupled deterministically
- Scenarios: NORMAL, VEHICLE_BREAKDOWN, FUEL_SHORTAGE, COLD_CHAIN_EXCURSION,
  BLIZZARD_LOGISTICS_RESTRICTION, HEAVY_CARGO_OPERATION, MISSION_FIELD_DEPLOYMENT, INVENTORY_SHORTAGE
- Strictly Read-Only Cross-Pillar Interfaces:
  - update_from_environment(env_data)
  - update_from_infrastructure(infra_data)
  - update_from_energy(energy_data)
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import math
from typing import Any

from .models import LogisticsConditionState


@dataclass
class VehicleTelemetryState:
    """Lead vehicle dynamic CAN/GPS telemetry."""
    speed_km_h: float = 0.0
    heading_deg: float = 0.0
    engine_rpm: float = 0.0
    engine_temp_c: float = -10.0
    fuel_level_percent: float = 85.0
    fuel_rate_l_h: float = 0.0
    battery_voltage_v: float = 24.0
    engine_hours: float = 1240.0
    status: str = "STANDBY"  # READY, ACTIVE, STANDBY, MAINTENANCE, FAULT


@dataclass
class FleetState:
    """Bharati fleet tracking state for documented machines."""
    pb01: VehicleTelemetryState = field(default_factory=VehicleTelemetryState)
    pb02_status: str = "STANDBY"
    sc01_status: str = "READY"
    sc01_fuel_percent: float = 90.0
    telehandler_hydraulic_pressure_bar: float = 210.0
    telehandler_status: str = "READY"
    excavator_status: str = "STANDBY"
    mantis_crane_status: str = "READY"

    # Additional fleet asset statuses tracked in registry
    pb03_status: str = "STANDBY"
    pb04_status: str = "STANDBY"
    pb05_status: str = "STANDBY"
    pb06_status: str = "MAINTENANCE"  # Reserve chassis and winter maintenance
    sc02_status: str = "STANDBY"
    sc03_status: str = "STANDBY"
    sc04_status: str = "STANDBY"
    excavator02_status: str = "STANDBY"
    bulldozer_status: str = "STANDBY"
    crane02_status: str = "STANDBY"


@dataclass
class ContainerTelemetryState:
    """Tracked container dynamic sensors."""
    location_zone: str = "YARD_ZONE_A"
    gross_weight_kg: float = 12500.0
    temperature_c: float = -8.0
    relative_humidity_percent: float = 45.0
    shock_g: float = 0.05
    tilt_deg: float = 0.8
    door_status: str = "CLOSED_LOCKED"  # CLOSED_LOCKED, OPEN


@dataclass
class CargoState:
    """Cargo containers, staging, and hazardous materials state."""
    total_cargo_units: float = 64.0
    in_transit_units: float = 0.0
    c01: ContainerTelemetryState = field(default_factory=ContainerTelemetryState)
    hazmat_staging_status: str = "CONTAINED_SECURE"  # CONTAINED_SECURE, INSPECTION_REQUIRED, LEAK_ALERT


@dataclass
class FuelLogisticsState:
    """Fuel logistics, vehicle dispensing, and transfer manifolds."""
    heli_supply_level_l: float = 18500.0
    heli_supply_percent: float = 74.0
    vehicle_tank_level_l: float = 38500.0
    vehicle_tank_percent: float = 77.0
    line_temperature_c: float = -5.0
    line_pressure_bar: float = 4.2
    transfer_flow_l_min: float = 0.0
    daily_dispensed_l: float = 320.0
    leak_status: str = "NORMAL"  # NORMAL, ALARM
    dispenser_status: str = "READY"  # READY, DISPENSING, DISABLED, FAULT


@dataclass
class ReeferTelemetryState:
    """Refrigerated container state."""
    core_temp_c: float = -22.0
    setpoint_c: float = -22.0
    door_status: str = "CLOSED"
    compressor_status: str = "CYCLING"  # OFF, RUNNING, CYCLING, FAULT
    power_source: str = "STATION_GRID"  # STATION_GRID, DIESEL_GENSET, OFF
    temperature_excursion: bool = False


@dataclass
class ColdChainState:
    """Cold storage reefers preservation state."""
    reefer01: ReeferTelemetryState = field(default_factory=ReeferTelemetryState)
    reefer02_core_temp_c: float = 3.5
    reefer02_status: str = "NORMAL"


@dataclass
class HelicopterAvionicsState:
    """Aviation flight assets telemetry."""
    status: str = "GROUNDED_READY"  # GROUNDED_READY, IN_FLIGHT, VESSEL_DECK, MAINTENANCE
    is_airborne: bool = False
    fuel_remaining_percent: float = 92.0
    altitude_m: float = 0.0
    ground_speed_km_h: float = 0.0
    cumulative_flight_hours: float = 284.5


@dataclass
class AviationState:
    """Aviation and helipad logistics."""
    heli: HelicopterAvionicsState = field(default_factory=HelicopterAvionicsState)
    helipad_status: str = "CLEAR_OPEN"  # CLEAR_OPEN, SNOW_COVERED, CLOSED_WEATHER


@dataclass
class MarineVesselState:
    """Expedition ship AIS telemetry."""
    status: str = "AT_ANCHOR"  # EN_ROUTE, AT_ANCHOR, BERTHED, DEPARTED
    distance_to_station_km: float = 2.4
    speed_knots: float = 0.0


@dataclass
class MarineState:
    """Expedition vessel, barge, and sea-to-shore discharge."""
    vessel: MarineVesselState = field(default_factory=MarineVesselState)
    barge_status: str = "STANDBY"  # STANDBY, SHUTTLE, DOCKED, SECURED
    discharge_progress_percent: float = 45.0
    sea_berth_safety: str = "SAFE"  # SAFE, MARGINAL, UNSAFE
    unloading_rate_tonne_h: float = 8.5


@dataclass
class RoutesState:
    """Station ground tracks, sea ice corridors, and traverse accessibility."""
    station_ring_status: str = "OPEN"
    helipad_track_status: str = "OPEN"
    coastal_link_status: str = "OPEN"
    fast_ice_route_status: str = "PASSABLE"  # PASSABLE, CAUTION, CLOSED
    larsemann_interstation_status: str = "OPEN"
    visibility_condition: str = "UNRESTRICTED"  # UNRESTRICTED, MARGINAL, RESTRICTED, ZERO_VISIBILITY
    crevasse_risk: str = "LOW"  # LOW, MODERATE, HIGH
    surface_traction_index: float = 85.0


@dataclass
class MissionTeamState:
    """Simulated field team operations (anonymous groups, zero PII)."""
    status: str = "IN_PROGRESS"  # PREPARING, IN_PROGRESS, RETURNING, COMPLETED, STANDBY
    distance_km: float = 8.5
    radio_check_status: str = "ACKNOWLEDGED"  # ACKNOWLEDGED, OVERDUE, SILENCE
    return_margin_minutes: float = 180.0


@dataclass
class MissionsState:
    """Muster, field expeditions, and radio checks."""
    active_missions_count: float = 1.0
    station_personnel_count: float = 24.0
    field_personnel_count: float = 3.0
    team01: MissionTeamState = field(default_factory=MissionTeamState)
    team02_status: str = "STANDBY"
    readiness_status: str = "OPTIMAL"  # OPTIMAL, CAUTION, STANDBY_ONLY, SUSPENDED


@dataclass
class InventoryState:
    """Stock levels, spares, rations autonomy, and emergency supplies."""
    rations_autonomy_days: float = 420.0
    rations_stock_percent: float = 88.0
    medical_supplies_status: str = "STOCKED"  # STOCKED, ADEQUATE, LOW, CRITICAL
    generator_spares_percent: float = 82.0
    vehicle_spares_percent: float = 75.0
    water_treatment_spares_percent: float = 90.0
    emergency_batteries_count: float = 48.0
    ppe_gear_percent: float = 95.0
    critical_stockout_alerts_count: float = 0.0
    stockout_risk_score: float = 0.05


@dataclass
class WasteLogisticsState:
    """Solid and hazardous waste tracking under the Madrid Protocol."""
    solid_waste_volume_m3: float = 18.5
    solid_storage_percent: float = 32.0
    hazard_waste_volume_l: float = 850.0
    hazard_containment_status: str = "SECURED"  # SECURED, COMPROMISED
    return_shipment_readiness_percent: float = 85.0


@dataclass
class DerivedLogisticsState:
    """Calculated operational indicators and explainable condition."""
    fleet_availability_percent: float = 93.75
    cargo_integrity_index: float = 98.0
    cold_chain_risk_score: float = 0.0
    ground_route_accessibility_percent: float = 100.0
    aviation_accessibility_percent: float = 100.0
    marine_accessibility_percent: float = 85.0
    composite_logistics_risk: float = 0.05
    logistics_condition_summary: str = "NORMAL"


class BharatiLogisticsPhysicsState:
    """Coupled physical and operational simulation state for Bharati Logistics."""

    def __init__(self, seed: int | None = None) -> None:
        self.fleet = FleetState()
        self.cargo = CargoState()
        self.fuel = FuelLogisticsState()
        self.cold_chain = ColdChainState()
        self.aviation = AviationState()
        self.marine = MarineState()
        self.routes = RoutesState()
        self.missions = MissionsState()
        self.inventory = InventoryState()
        self.waste = WasteLogisticsState()
        self.derived = DerivedLogisticsState()

        self._active_scenario: str = "NORMAL"
        self._elapsed_seconds: float = 0.0

        # Environmental context inputs (read-only cache)
        self._env_wind_speed_mps: float = 8.5
        self._env_visibility_m: float = 25000.0
        self._env_snow_depth_m: float = 0.35
        self._env_sea_ice_conc_pct: float = 30.0
        self._env_blizzard_risk: float = 0.05

        self.recompute_derived_state()

    def set_scenario(self, scenario_name: str) -> None:
        """Switch simulation operational scenario and recompute coupled state."""
        self._active_scenario = scenario_name.upper()

        if self._active_scenario == "NORMAL":
            self.fleet.pb01.speed_km_h = 0.0
            self.fleet.pb01.heading_deg = 0.0
            self.fleet.pb01.engine_rpm = 0.0
            self.fleet.pb01.engine_temp_c = -10.0
            self.fleet.pb01.fuel_level_percent = 85.0
            self.fleet.pb01.fuel_rate_l_h = 0.0
            self.fleet.pb01.battery_voltage_v = 24.0
            self.fleet.pb01.status = "STANDBY"
            self.fleet.pb02_status = "STANDBY"
            self.fleet.sc01_status = "READY"
            self.fleet.sc01_fuel_percent = 90.0
            self.fleet.telehandler_status = "READY"
            self.fleet.telehandler_hydraulic_pressure_bar = 210.0
            self.fleet.pb06_status = "MAINTENANCE"

            self.cargo.c01.shock_g = 0.05
            self.cargo.c01.tilt_deg = 0.8
            self.cargo.c01.door_status = "CLOSED_LOCKED"
            self.cargo.c01.temperature_c = -8.0
            self.cargo.hazmat_staging_status = "CONTAINED_SECURE"

            self.fuel.vehicle_tank_percent = 77.0
            self.fuel.vehicle_tank_level_l = 38500.0
            self.fuel.dispenser_status = "READY"
            self.fuel.leak_status = "NORMAL"

            self.cold_chain.reefer01.core_temp_c = -22.0
            self.cold_chain.reefer01.compressor_status = "CYCLING"
            self.cold_chain.reefer01.power_source = "STATION_GRID"
            self.cold_chain.reefer01.temperature_excursion = False

            self.aviation.helipad_status = "CLEAR_OPEN"
            self.aviation.heli.status = "GROUNDED_READY"

            self.routes.station_ring_status = "OPEN"
            self.routes.helipad_track_status = "OPEN"
            self.routes.coastal_link_status = "OPEN"
            self.routes.fast_ice_route_status = "PASSABLE"
            self.routes.larsemann_interstation_status = "OPEN"
            self.routes.visibility_condition = "UNRESTRICTED"
            self.routes.crevasse_risk = "LOW"
            self.routes.surface_traction_index = 85.0

            self.missions.team01.status = "IN_PROGRESS"
            self.missions.team01.distance_km = 8.5
            self.missions.team01.radio_check_status = "ACKNOWLEDGED"
            self.missions.team01.return_margin_minutes = 180.0
            self.missions.readiness_status = "OPTIMAL"

        elif self._active_scenario == "VEHICLE_BREAKDOWN":
            self.fleet.pb01.status = "FAULT"
            self.fleet.pb01.engine_temp_c = 105.0
            self.fleet.pb01.engine_rpm = 0.0
            self.fleet.pb01.speed_km_h = 0.0
            self.fleet.pb01.fuel_rate_l_h = 0.0
            self.fleet.telehandler_status = "MAINTENANCE"
            self.fleet.telehandler_hydraulic_pressure_bar = 35.0

        elif self._active_scenario == "FUEL_SHORTAGE":
            self.fuel.vehicle_tank_percent = 14.5
            self.fuel.vehicle_tank_level_l = 7250.0
            self.fuel.heli_supply_percent = 20.0
            self.fuel.heli_supply_level_l = 5000.0
            self.fuel.dispenser_status = "DISABLED"
            self.inventory.stockout_risk_score = 0.65

        elif self._active_scenario == "COLD_CHAIN_EXCURSION":
            self.cold_chain.reefer01.power_source = "OFF"
            self.cold_chain.reefer01.compressor_status = "FAULT"
            self.cold_chain.reefer01.door_status = "OPEN"
            self.cold_chain.reefer01.core_temp_c = -4.5
            self.cold_chain.reefer01.temperature_excursion = True

        elif self._active_scenario == "BLIZZARD_LOGISTICS_RESTRICTION":
            self._env_wind_speed_mps = 32.5
            self._env_visibility_m = 50.0
            self._env_blizzard_risk = 0.95
            self.aviation.helipad_status = "CLOSED_WEATHER"
            self.routes.station_ring_status = "DRIFT_BLOCKED"
            self.routes.helipad_track_status = "DRIFT_BLOCKED"
            self.routes.coastal_link_status = "CLOSED"
            self.routes.fast_ice_route_status = "CLOSED"
            self.routes.larsemann_interstation_status = "CLOSED"
            self.routes.visibility_condition = "ZERO_VISIBILITY"
            self.routes.crevasse_risk = "HIGH"
            self.routes.surface_traction_index = 20.0
            self.marine.sea_berth_safety = "UNSAFE"
            self.marine.barge_status = "SECURED"
            self.missions.team01.return_margin_minutes = -15.0
            self.missions.readiness_status = "SUSPENDED"

        elif self._active_scenario == "HEAVY_CARGO_OPERATION":
            self.cargo.in_transit_units = 8.0
            self.marine.barge_status = "SHUTTLE"
            self.marine.discharge_progress_percent = 62.0
            self.marine.unloading_rate_tonne_h = 16.5
            self.fleet.telehandler_status = "ACTIVE"
            self.fleet.mantis_crane_status = "ACTIVE"
            self.fleet.pb01.status = "ACTIVE"
            self.fleet.pb01.engine_rpm = 1850.0
            self.fleet.pb01.speed_km_h = 12.5
            self.fleet.pb01.fuel_rate_l_h = 24.0

        elif self._active_scenario == "MISSION_FIELD_DEPLOYMENT":
            self.missions.active_missions_count = 2.0
            self.missions.station_personnel_count = 20.0
            self.missions.field_personnel_count = 7.0
            self.missions.team01.status = "IN_PROGRESS"
            self.missions.team01.distance_km = 14.2
            self.missions.team02_status = "DEPLOYED"

        elif self._active_scenario == "INVENTORY_SHORTAGE":
            self.inventory.generator_spares_percent = 22.0
            self.inventory.vehicle_spares_percent = 18.0
            self.inventory.critical_stockout_alerts_count = 3.0
            self.inventory.stockout_risk_score = 0.72

        self.recompute_derived_state()

    def update_from_environment(self, env_data: dict[str, Any]) -> None:
        """Strictly read-only consumer of external environmental observations.
        
        Logistics never mutates Environment. It observes ambient environmental
        context and updates logistics-owned route accessibility, helipad operations,
        and sea-berth safety.
        """
        wind_mps = float(env_data.get("wind_speed_mps", self._env_wind_speed_mps))
        vis_m = float(env_data.get("visibility_m", self._env_visibility_m))
        blizzard_risk = float(env_data.get("blizzard_risk", self._env_blizzard_risk))
        snow_depth_m = float(env_data.get("snow_depth_m", self._env_snow_depth_m))

        self._env_wind_speed_mps = wind_mps
        self._env_visibility_m = vis_m
        self._env_blizzard_risk = blizzard_risk
        self._env_snow_depth_m = snow_depth_m

        # 1. Update Helipad Operational Condition based on Wind and Visibility
        if wind_mps > 20.0 or vis_m < 800.0 or blizzard_risk > 0.6:
            self.aviation.helipad_status = "CLOSED_WEATHER"
        elif snow_depth_m > 0.8:
            self.aviation.helipad_status = "SNOW_COVERED"
        else:
            if self._active_scenario != "BLIZZARD_LOGISTICS_RESTRICTION":
                self.aviation.helipad_status = "CLEAR_OPEN"

        # 2. Update Route Visibility Condition
        if vis_m > 10000.0:
            self.routes.visibility_condition = "UNRESTRICTED"
        elif vis_m > 3000.0:
            self.routes.visibility_condition = "MARGINAL"
        elif vis_m > 500.0:
            self.routes.visibility_condition = "RESTRICTED"
        else:
            self.routes.visibility_condition = "ZERO_VISIBILITY"

        # 3. Update Surface Traction Index
        base_traction = 85.0
        if wind_mps > 15.0:
            base_traction -= min(40.0, (wind_mps - 15.0) * 2.5)
        if snow_depth_m > 0.5:
            base_traction -= min(25.0, (snow_depth_m - 0.5) * 20.0)
        if blizzard_risk > 0.5:
            base_traction -= 20.0
        self.routes.surface_traction_index = max(10.0, min(100.0, round(base_traction, 1)))

        # 4. Update Sea Berth Safety
        if wind_mps > 18.0 or blizzard_risk > 0.5:
            self.marine.sea_berth_safety = "UNSAFE"
        elif wind_mps > 12.0:
            self.marine.sea_berth_safety = "MARGINAL"
        else:
            if self._active_scenario != "BLIZZARD_LOGISTICS_RESTRICTION":
                self.marine.sea_berth_safety = "SAFE"

        self.recompute_derived_state()

    def update_from_infrastructure(self, infra_data: dict[str, Any]) -> None:
        """Strictly read-only consumer of station infrastructure storage states."""
        # Query infrastructure storage doors, HVAC, or structural integrity
        pass

    def update_from_energy(self, energy_data: dict[str, Any]) -> None:
        """Strictly read-only consumer of energy grid power status for reefers."""
        grid_status = energy_data.get("grid_status", "NORMAL")
        if grid_status == "BLACKOUT" and self._active_scenario != "NORMAL":
            self.cold_chain.reefer01.power_source = "DIESEL_GENSET"

    def recompute_derived_state(self) -> None:
        """Evaluate deterministic derived logistics indicators and condition summary."""
        # 1. Fleet Availability Percentage
        operational_assets = 0
        total_tracked_assets = 16
        statuses = [
            self.fleet.pb01.status,
            self.fleet.pb02_status,
            self.fleet.sc01_status,
            self.fleet.telehandler_status,
            self.fleet.excavator_status,
            self.fleet.mantis_crane_status,
            self.fleet.pb03_status,
            self.fleet.pb04_status,
            self.fleet.pb05_status,
            self.fleet.pb06_status,
            self.fleet.sc02_status,
            self.fleet.sc03_status,
            self.fleet.sc04_status,
            self.fleet.excavator02_status,
            self.fleet.bulldozer_status,
            self.fleet.crane02_status,
        ]
        for s in statuses:
            if s in ("READY", "ACTIVE", "STANDBY", "RESERVE"):
                operational_assets += 1
        self.derived.fleet_availability_percent = round(
            (operational_assets / total_tracked_assets) * 100.0, 2
        )

        # 2. Cargo Integrity Index
        c_score = 100.0
        if self.cargo.c01.shock_g > 2.0:
            c_score -= min(40.0, self.cargo.c01.shock_g * 10.0)
        if self.cargo.c01.tilt_deg > 5.0:
            c_score -= min(30.0, (self.cargo.c01.tilt_deg - 5.0) * 5.0)
        if self.cargo.c01.door_status != "CLOSED_LOCKED":
            c_score -= 15.0
        if self.cargo.hazmat_staging_status != "CONTAINED_SECURE":
            c_score -= 25.0
        self.derived.cargo_integrity_index = max(0.0, min(100.0, round(c_score, 1)))

        # 3. Cold Chain Risk Score
        r_risk = 0.0
        if self.cold_chain.reefer01.temperature_excursion:
            r_risk += 0.5
        temp_delta = self.cold_chain.reefer01.core_temp_c - self.cold_chain.reefer01.setpoint_c
        if temp_delta > 3.0:
            r_risk += min(0.4, temp_delta * 0.05)
        if self.cold_chain.reefer01.compressor_status == "FAULT":
            r_risk += 0.3
        self.derived.cold_chain_risk_score = min(1.0, round(r_risk, 2))

        # 4. Ground Route Accessibility Percentage
        routes = [
            self.routes.station_ring_status,
            self.routes.helipad_track_status,
            self.routes.coastal_link_status,
            self.routes.fast_ice_route_status,
            self.routes.larsemann_interstation_status,
        ]
        passable_count = 0
        for r in routes:
            if r in ("OPEN", "PASSABLE"):
                passable_count += 1
            elif r == "CAUTION":
                passable_count += 0.5
        self.derived.ground_route_accessibility_percent = round(
            (passable_count / len(routes)) * 100.0, 1
        )

        # 5. Aviation Accessibility Percentage
        air_access = 100.0
        if self.aviation.helipad_status == "CLOSED_WEATHER":
            air_access = 0.0
        elif self.aviation.helipad_status == "SNOW_COVERED":
            air_access = 40.0
        if self.aviation.heli.status == "MAINTENANCE":
            air_access = 0.0
        self.derived.aviation_accessibility_percent = air_access

        # 6. Marine Accessibility Percentage
        marine_access = 85.0
        if self.marine.sea_berth_safety == "UNSAFE":
            marine_access = 0.0
        elif self.marine.sea_berth_safety == "MARGINAL":
            marine_access = 40.0
        if self.marine.barge_status == "SECURED":
            marine_access = min(marine_access, 10.0)
        self.derived.marine_accessibility_percent = marine_access

        # 7. Composite Logistics Risk Score
        # Weighted combination of unavailabilities and risks across all modalities
        risk_components = [
            (1.0 - (self.derived.fleet_availability_percent / 100.0)) * 0.20,
            (1.0 - (self.derived.ground_route_accessibility_percent / 100.0)) * 0.25,
            (1.0 - (self.derived.aviation_accessibility_percent / 100.0)) * 0.15,
            self.derived.cold_chain_risk_score * 0.15,
            self.inventory.stockout_risk_score * 0.15,
            (1.0 - (self.derived.cargo_integrity_index / 100.0)) * 0.10,
        ]
        comp_risk = sum(risk_components)
        self.derived.composite_logistics_risk = max(0.0, min(1.0, round(comp_risk, 2)))

        # 8. Explainable Logistics Condition Summary
        reasons = []
        if self.derived.ground_route_accessibility_percent < 30.0:
            reasons.append("ROUTE_NETWORK_IMPASSABLE")
        if self.aviation.helipad_status == "CLOSED_WEATHER":
            reasons.append("AVIATION_WEATHER_CLOSURE")
        if self.derived.cold_chain_risk_score > 0.4:
            reasons.append("COLD_CHAIN_TEMPERATURE_EXCURSION")
        if self.fleet.pb01.status == "FAULT":
            reasons.append("LEAD_HAULER_MECHANICAL_FAULT")
        if self.fuel.dispenser_status == "DISABLED":
            reasons.append("FUEL_DISPENSING_RESTRICTED")
        if self.inventory.stockout_risk_score > 0.5:
            reasons.append("CRITICAL_SPARES_SHORTAGE")

        if "ROUTE_NETWORK_IMPASSABLE" in reasons and "AVIATION_WEATHER_CLOSURE" in reasons:
            cond_level = "RESTRICTED"
        elif self.derived.composite_logistics_risk > 0.5:
            cond_level = "RESTRICTED"
        elif self.derived.composite_logistics_risk > 0.20 or len(reasons) > 0:
            cond_level = "CAUTION"
        else:
            cond_level = "NORMAL"

        self.derived.logistics_condition_summary = cond_level

    def step(self, dt_seconds: float = 1.0) -> None:
        """Advance physical simulation state by dt_seconds."""
        self._elapsed_seconds += dt_seconds

        # Lead hauler dynamics if active
        if self.fleet.pb01.status == "ACTIVE":
            # Consume fuel
            consumed = (self.fleet.pb01.fuel_rate_l_h / 3600.0) * dt_seconds
            tank_capacity_l = 300.0
            fuel_pct_drop = (consumed / tank_capacity_l) * 100.0
            self.fleet.pb01.fuel_level_percent = max(
                0.0, round(self.fleet.pb01.fuel_level_percent - fuel_pct_drop, 3)
            )
            self.fleet.pb01.engine_hours = round(
                self.fleet.pb01.engine_hours + (dt_seconds / 3600.0), 3
            )

        # Helicopter dynamics if active
        if self.aviation.heli.status == "IN_FLIGHT":
            burn = (80.0 / 3600.0) * dt_seconds  # 80 L/h
            self.aviation.heli.fuel_remaining_percent = max(
                0.0, round(self.aviation.heli.fuel_remaining_percent - 0.02 * dt_seconds, 2)
            )
            self.aviation.heli.cumulative_flight_hours = round(
                self.aviation.heli.cumulative_flight_hours + (dt_seconds / 3600.0), 3
            )

        self.recompute_derived_state()

    def resolve_path(self, path: str) -> Any:
        """Resolve dotted state path directly to simulated physical value.
        
        Example paths:
        - fleet.pb01.speed_km_h
        - cargo.c01.gross_weight_kg
        - cold_chain.reefer01.core_temp_c
        - derived.fleet_availability_percent
        """
        parts = path.split(".")
        target: Any = self
        for part in parts:
            if hasattr(target, part):
                target = getattr(target, part)
            else:
                # Custom alias mappings for state paths
                if part == "pb02":
                    target = self.fleet.pb02_status
                elif part == "sc01":
                    target = self.fleet
                elif part == "telehandler":
                    target = self.fleet
                elif part == "excavator":
                    target = self.fleet.excavator_status
                elif part == "mantis_crane":
                    target = self.fleet.mantis_crane_status
                elif part == "heli":
                    target = self.aviation.heli
                elif part == "helipad":
                    target = self.aviation
                elif part == "vessel":
                    target = self.marine.vessel
                elif part == "barge":
                    target = self.marine
                elif part == "station_ring":
                    target = self.routes.station_ring_status
                elif part == "helipad_track":
                    target = self.routes.helipad_track_status
                elif part == "coastal_link":
                    target = self.routes.coastal_link_status
                elif part == "fast_ice_route":
                    target = self.routes.fast_ice_route_status
                elif part == "larsemann_interstation":
                    target = self.routes.larsemann_interstation_status
                elif part == "team01":
                    target = self.missions.team01
                elif part == "team02":
                    target = self.missions.team02_status
                elif part == "reefer01":
                    target = self.cold_chain.reefer01
                elif part == "reefer02":
                    target = self.cold_chain
                else:
                    raise AttributeError(f"Could not resolve subpath '{part}' in '{path}'")
        return target
