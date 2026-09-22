"""Bharati Station Master Digital Twin Engine.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Unified Synchronized Clock: All 4 observation pillars (Energy, Infrastructure,
   Environment, Logistics) advance on a single master simulation clock.
2. Deterministic Physical Coupling: State propagation follows strict first-principles
   order: Environment -> Infrastructure -> Energy -> Logistics.
3. Master Scenario Injector: Station-wide physical scenarios (blizzards, generator
   trips, pipeline freezes, cold chain excursions) inject coherent multi-pillar disruptions.
4. Clean Read-Only Query API: Sub-millisecond sensor lookup across all registered points.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Literal

from ..sensors.bharati_sensors.energy.clock import SimulationClock
from ..sensors.bharati_sensors.energy.factory import create_bharati_energy_sensors
from ..sensors.bharati_sensors.energy.models import SensorReading as EnergySensorReading
from ..sensors.bharati_sensors.energy.registry import SensorRegistry as EnergyRegistry
from ..sensors.bharati_sensors.environment.factory import (
    create_bharati_environment_sensors,
    get_energy_environmental_interface,
    get_logistics_environmental_interface,
    to_infrastructure_environmental_input,
)
from ..sensors.bharati_sensors.environment.registry import EnvironmentSensorRegistry
from ..sensors.bharati_sensors.infrastructure.factory import create_bharati_infrastructure_sensors
from ..sensors.bharati_sensors.infrastructure.registry import InfrastructureSensorRegistry
from ..sensors.bharati_sensors.logistics.factory import create_bharati_logistics_sensors
from ..sensors.bharati_sensors.logistics.registry import LogisticsSensorRegistry


class MasterScenario(str, Enum):
    """Station-wide operational and environmental disturbance scenarios."""
    NORMAL = "NORMAL"
    BLIZZARD_STRIKE = "BLIZZARD_STRIKE"
    GENERATOR_TRIP = "GENERATOR_TRIP"
    WATER_LINE_FREEZE = "WATER_LINE_FREEZE"
    COLD_CHAIN_EXCURSION = "COLD_CHAIN_EXCURSION"
    FUEL_TRANSFER_LEAK = "FUEL_TRANSFER_LEAK"
    HEAVY_CARGO_OPERATION = "HEAVY_CARGO_OPERATION"
    MISSION_FIELD_DEPLOYMENT = "MISSION_FIELD_DEPLOYMENT"


@dataclass
class MasterTwinSnapshot:
    """Immutable station-wide telemetry and operational snapshot."""
    timestamp_iso: str
    sim_time_seconds: float
    active_scenario: str
    sensor_count: int
    readings: dict[str, Any]
    kpis: dict[str, Any]
    alerts: list[dict[str, Any]] = field(default_factory=list)
    station_id: str = "bharati"


class BharatiMasterTwinEngine:
    """Master Digital Twin simulation engine for Bharati Station."""

    def __init__(
        self,
        seed: int | None = 42,
        clock: SimulationClock | None = None,
    ) -> None:
        """Initialize all 4 observation pillars with a synchronized clock and shared seed."""
        self.station_id: str = "bharati"
        self.station_name: str = "Bharati Research Station"
        self.location: str = "Larsemann Hills, East Antarctica"
        self.coordinates: dict[str, Any] = {
            "latitude": -69.4078,
            "longitude": 76.1872,
            "latitude_dms": "69° 24' 28'' S",
            "longitude_dms": "76° 11' 14'' E",
            "elevation_m": 35.0,
        }
        self.clock = clock if clock is not None else SimulationClock()
        self.seed = seed
        self._active_scenario: MasterScenario = MasterScenario.NORMAL
        self._scenario_elapsed_seconds: float = 0.0

        # 1. Instantiate Environment Pillar
        self.env_registry: EnvironmentSensorRegistry = create_bharati_environment_sensors(
            seed=seed, clock=self.clock
        )

        # 2. Derive initial environmental input for Infrastructure
        initial_env_input = to_infrastructure_environmental_input(self.env_registry)

        # 3. Instantiate Infrastructure Pillar
        self.infra_registry: InfrastructureSensorRegistry = create_bharati_infrastructure_sensors(
            seed=seed, clock=self.clock, environmental_input=initial_env_input
        )

        # 4. Instantiate Energy Pillar
        self.energy_registry: EnergyRegistry = create_bharati_energy_sensors(
            seed=seed, clock=self.clock
        )

        # 5. Instantiate Logistics Pillar
        log_res = create_bharati_logistics_sensors(seed=seed, clock=self.clock)
        self.logistics_registry: LogisticsSensorRegistry = log_res[0]

        # Ensure initial physical coupling is applied
        self._couple_physics(dt_seconds=0.0)

        # Cache of all current readings
        self._cached_readings: dict[str, Any] = {}
        self._refresh_all_readings()

    @property
    def active_scenario(self) -> MasterScenario:
        """Return the currently active master scenario."""
        return self._active_scenario

    @property
    def sensor_count(self) -> int:
        """Total unique sensors instrumented across all 4 pillars."""
        return (
            len(self.env_registry.get_all_sensors())
            + len(self.infra_registry.get_all_sensors())
            + len(self.energy_registry.get_all_sensors())
            + len(self.logistics_registry.get_all_sensors())
        )

    def step(self, dt_seconds: float = 1.0) -> MasterTwinSnapshot:
        """Advance the master digital twin forward by dt_seconds in physical sequence.
        
        Sequential Propagation Loop:
        1. Advance shared simulation clock once.
        2. Step Environment physics -> observe external boundary conditions.
        3. Step Infrastructure physics -> calculate auxiliary kW & heating demand kWth.
        4. Step Energy physics -> dispatch CHPs, supply grid & thermal, burn fuel.
        5. Step Logistics physics -> observe wind/vis for routes & helipad, grid for reefers.
        6. Refresh telemetry cache and evaluate station KPIs & alerts.
        """
        if dt_seconds <= 0.0:
            return self.get_snapshot()

        # 1. Advance single master simulation clock
        self.clock.advance(dt_seconds)
        self._scenario_elapsed_seconds += dt_seconds

        # 2. Step Environment physics
        self.env_registry.physics.step(dt_seconds)

        # 3. Propagate physical cross-pillar boundaries
        self._couple_physics(dt_seconds)

        # 4. Step Infrastructure physics
        self.infra_registry.physics.step(dt_seconds)

        # 5. Extract Infrastructure demands for Energy
        aux_power_kw = self.infra_registry.physics.calculate_total_auxiliary_power_kw()
        base_station_kw = 120.0  # Base hotel load (living, computers, kitchen base)
        total_load_kw = max(80.0, min(240.0, base_station_kw + aux_power_kw))
        self.energy_registry.physics.total_station_load_kw = total_load_kw
        self.energy_registry.physics.ambient_temperature_c = (
            self.env_registry.physics.weather.ambient_temperature_c
        )

        # 6. Step Energy physics
        self.energy_registry.physics.step(dt_seconds)

        # 7. Feed Energy & Environment status into Logistics
        env_logistics = get_logistics_environmental_interface(self.env_registry)
        self.logistics_registry.physics.update_from_environment(env_logistics)

        # Derive energy grid status for cold chain
        chp_running = any(c.running_status for c in self.energy_registry.physics.chps)
        grid_status = "NORMAL" if chp_running else "BLACKOUT"
        self.logistics_registry.physics.update_from_energy({"grid_status": grid_status})

        # 8. Step Logistics physics
        self.logistics_registry.physics.step(dt_seconds)

        # 9. Refresh sensor readings
        self._refresh_all_readings()

        return self.get_snapshot()

    def _couple_physics(self, dt_seconds: float) -> None:
        """Synchronize physical cross-pillar boundary variables."""
        # Environment -> Infrastructure
        env_input = to_infrastructure_environmental_input(self.env_registry)
        self.infra_registry.physics.env.ambient_temperature_c = env_input.ambient_temperature_c
        self.infra_registry.physics.env.wind_speed_ms = env_input.wind_speed_ms
        self.infra_registry.physics.env.wind_direction_deg = env_input.wind_direction_deg
        self.infra_registry.physics.env.solar_radiation_w_m2 = env_input.solar_radiation_w_m2
        self.infra_registry.physics.env.atmospheric_pressure_hpa = env_input.atmospheric_pressure_hpa
        self.infra_registry.physics.env.relative_humidity_percent = env_input.relative_humidity_percent
        self.infra_registry.physics.env.snow_accumulation_rate_mm_h = env_input.snow_accumulation_rate_mm_h

    def _refresh_all_readings(self) -> None:
        """Update cached readings across all 4 registries."""
        readings: dict[str, Any] = {}
        readings.update(self.env_registry.read_all())
        readings.update(self.infra_registry.read_all())
        readings.update(self.energy_registry.read_all())
        readings.update(self.logistics_registry.read_all())
        self._cached_readings = readings

    def get_sensor_reading(self, sensor_id: str) -> Any:
        """Lookup an individual sensor reading across all 4 pillars in O(1) time."""
        if sensor_id in self._cached_readings:
            return self._cached_readings[sensor_id]
        if sensor_id in self.env_registry._sensors:
            return self.env_registry.read_sensor(sensor_id)
        if sensor_id in self.infra_registry._sensors:
            return self.infra_registry.read_sensor(sensor_id)
        if sensor_id in self.energy_registry._sensors:
            return self.energy_registry.read_sensor(sensor_id)
        if sensor_id in self.logistics_registry._sensors:
            return self.logistics_registry.read_sensor(sensor_id)
        raise KeyError(f"Sensor ID '{sensor_id}' not found in any Bharati observation pillar.")

    def get_all_readings(self) -> dict[str, Any]:
        """Return the complete dictionary of current readings for all 505 sensors."""
        return dict(self._cached_readings)

    def inject_sensor_override(self, sensor_id: str, value: Any, quality: str = "GOOD") -> bool:
        """Inject or override an external hardware SCADA/PLC reading into the twin cache."""
        if sensor_id in self._cached_readings:
            reading = self._cached_readings[sensor_id]
            if hasattr(reading, "value"):
                try:
                    reading.value = float(value) if isinstance(value, (int, float, str)) and str(value).replace(".", "", 1).replace("-", "", 1).isdigit() else value
                except Exception:
                    reading.value = value
            elif isinstance(reading, dict):
                reading["value"] = value
                reading["quality"] = quality
            else:
                self._cached_readings[sensor_id] = value
            return True
        else:
            self._cached_readings[sensor_id] = {
                "sensor_id": sensor_id,
                "value": value,
                "quality": quality,
                "timestamp_iso": self.clock.isoformat(),
            }
            return True

    def inject_scenario(self, scenario: MasterScenario | str, **params: Any) -> None:
        """Inject a station-wide physical disturbance scenario across all pillars."""
        sc = MasterScenario(scenario) if isinstance(scenario, str) else scenario
        self._active_scenario = sc
        self._scenario_elapsed_seconds = 0.0

        if sc == MasterScenario.NORMAL:
            self._apply_scenario_normal()
        elif sc == MasterScenario.BLIZZARD_STRIKE:
            self._apply_scenario_blizzard(**params)
        elif sc == MasterScenario.GENERATOR_TRIP:
            self._apply_scenario_generator_trip(**params)
        elif sc == MasterScenario.WATER_LINE_FREEZE:
            self._apply_scenario_water_line_freeze(**params)
        elif sc == MasterScenario.COLD_CHAIN_EXCURSION:
            self._apply_scenario_cold_chain_excursion(**params)
        elif sc == MasterScenario.FUEL_TRANSFER_LEAK:
            self._apply_scenario_fuel_transfer_leak(**params)
        elif sc == MasterScenario.HEAVY_CARGO_OPERATION:
            self._apply_scenario_heavy_cargo(**params)
        elif sc == MasterScenario.MISSION_FIELD_DEPLOYMENT:
            self._apply_scenario_field_mission(**params)

        # Propagate immediately through physics
        self._couple_physics(dt_seconds=0.0)
        self._refresh_all_readings()

    def clear_scenario(self) -> None:
        """Restore all pillars to nominal steady-state operation."""
        self.inject_scenario(MasterScenario.NORMAL)

    def _apply_scenario_normal(self) -> None:
        """Reset all systems to healthy baseline."""
        self.env_registry.physics.set_scenario_normal()
        self.env_registry.physics.weather.ambient_temperature_c = -18.0
        self.env_registry.physics.weather._target_temp_c = -18.0
        self.env_registry.physics.weather.wind_speed_mps = 12.0
        self.env_registry.physics.weather._target_wind_mps = 12.0
        self.env_registry.physics.weather.visibility_m = 25000.0
        self.env_registry.physics.derived.blizzard_risk = 0.05

        # Energy: CHPs healthy
        self.energy_registry.physics.chps[0].operating_state = "RUNNING"
        self.energy_registry.physics.chps[1].operating_state = "STANDBY"
        self.energy_registry.physics.chps[2].operating_state = "STANDBY"

        # Infra: HVAC and pipes healthy
        self.infra_registry.physics.pipelines.water01_trace_heating_on = True
        self.infra_registry.physics.pipelines.water01_pipe_temp_c = 14.5

        # Logistics: Nominal
        self.logistics_registry.set_scenario("NORMAL")

    def _apply_scenario_blizzard(self, wind_speed_mps: float = 34.0, temp_c: float = -32.5) -> None:
        """Simulate an extreme Antarctic katabatic blizzard."""
        self.env_registry.physics.set_scenario_blizzard()
        self.env_registry.physics.weather.wind_speed_mps = wind_speed_mps
        self.env_registry.physics.weather._target_wind_mps = wind_speed_mps
        self.env_registry.physics.weather.wind_gust_mps = wind_speed_mps * 1.35
        self.env_registry.physics.weather.ambient_temperature_c = temp_c
        self.env_registry.physics.weather._target_temp_c = temp_c
        self.env_registry.physics.weather.visibility_m = 250.0  # Whiteout
        self.env_registry.physics.weather.precipitation_rate_mm_h = 18.0
        self.env_registry.physics.snow.snow_depth_m += 0.35
        self.env_registry.physics.derived.blizzard_risk = 0.95

        # Logistics restrictions
        self.logistics_registry.set_scenario("BLIZZARD_LOGISTICS_RESTRICTION")

    def _apply_scenario_generator_trip(self, tripped_unit_index: int = 1) -> None:
        """Simulate an instantaneous generator mechanical/electrical fault."""
        chp_idx = max(0, min(tripped_unit_index - 1, 2))
        self.energy_registry.physics.chps[chp_idx].operating_state = "MAINTENANCE"
        self.energy_registry.physics.chps[chp_idx].running_status = False
        self.energy_registry.physics.chps[chp_idx].active_power_kw = 0.0

        # If lead tripped, start standby unit 2
        alt_idx = 1 if chp_idx == 0 else 0
        self.energy_registry.physics.chps[alt_idx].operating_state = "RUNNING"

    def _apply_scenario_water_line_freeze(self) -> None:
        """Simulate trace heating failure on utilidor fresh water supply line."""
        self.infra_registry.physics.pipelines.water01_trace_heating_on = False
        self.infra_registry.physics.pipelines.water01_pipe_temp_c = -2.5
        self.infra_registry.physics.water.ro_system_status = "FAULT_FREEZE"

    def _apply_scenario_cold_chain_excursion(self) -> None:
        """Simulate cold container Reefer-01 refrigeration compressor breakdown."""
        self.logistics_registry.set_scenario("COLD_CHAIN_EXCURSION")

    def _apply_scenario_fuel_transfer_leak(self) -> None:
        """Simulate fuel logistics shortage and bulk transfer pump fault."""
        self.logistics_registry.set_scenario("FUEL_SHORTAGE")
        self.energy_registry.physics.fuel.transfer_pump_running = False

    def _apply_scenario_heavy_cargo(self) -> None:
        """Simulate active Quilty Bay ship offloading with Mantis crane."""
        self.logistics_registry.set_scenario("HEAVY_CARGO_OPERATION")

    def _apply_scenario_field_mission(self) -> None:
        """Simulate long-range scientific traverse deployment to Polar Plateau."""
        self.logistics_registry.set_scenario("MISSION_FIELD_DEPLOYMENT")

    def get_station_kpis(self) -> dict[str, Any]:
        """Compute aggregated high-level operational performance indicators."""
        e_phy = self.energy_registry.physics
        i_phy = self.infra_registry.physics
        env_phy = self.env_registry.physics
        l_phy = self.logistics_registry.physics

        # Total generated electrical power
        running_chps = sum(1 for c in e_phy.chps if c.running_status)
        total_gen_kw = sum(c.active_power_kw for c in e_phy.chps if c.running_status)

        # Average indoor temperature across zones
        avg_indoor_temp = round(
            (i_phy.building.temp_living_c + i_phy.building.temp_lab_c + i_phy.building.temp_technical_c) / 3.0,
            2,
        )

        # Fuel burn rate & autonomy
        fuel_burn_lph = e_phy.fuel.fuel_flow_lph
        total_fuel_l = e_phy.fuel.bulk_fuel_level_l + e_phy.fuel.day_tank_level_l
        autonomy_days = round(total_fuel_l / max(fuel_burn_lph * 24.0, 1.0), 1)

        # Potable water autonomy
        water_autonomy_days = round(i_phy.water.potable_tank_volume_l / max(i_phy.water.consumption_flow_lph * 24.0, 1.0), 1)

        # Composite risk score (0 to 100)
        risk_score = round(
            (env_phy.derived.environmental_risk * 30.0)
            + (l_phy.derived.composite_logistics_risk * 35.0)
            + (100.0 - min(100.0, autonomy_days / 3.65)) * 0.15
            + (0.0 if avg_indoor_temp >= 18.0 else (18.0 - avg_indoor_temp) * 5.0),
            1,
        )

        return {
            "total_generation_kw": round(total_gen_kw, 1),
            "running_chp_count": running_chps,
            "station_electrical_load_kw": round(e_phy.total_station_load_kw, 1),
            "station_heating_demand_kw": round(e_phy.heating.station_heating_demand_kw, 1),
            "indoor_avg_temp_c": avg_indoor_temp,
            "ambient_temp_c": round(env_phy.weather.ambient_temperature_c, 1),
            "wind_speed_mps": round(env_phy.weather.wind_speed_mps, 1),
            "total_fuel_reserve_l": round(total_fuel_l, 0),
            "fuel_autonomy_days": autonomy_days,
            "water_autonomy_days": water_autonomy_days,
            "potable_tank_level_pct": round(i_phy.water.potable_tank_level_pct, 1),
            "fleet_availability_pct": round(l_phy.derived.fleet_availability_percent, 1),
            "ground_route_accessibility_pct": round(l_phy.derived.ground_route_accessibility_percent, 1),
            "composite_risk_score": min(100.0, max(0.0, risk_score)),
        }

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Identify critical operational alerts across all 4 pillars."""
        alerts: list[dict[str, Any]] = []
        kpis = self.get_station_kpis()

        if kpis["indoor_avg_temp_c"] < 16.0:
            alerts.append({
                "subsystem": "INFRASTRUCTURE_HVAC",
                "severity": "CRITICAL",
                "message": f"Indoor station temperature below life-safety threshold: {kpis['indoor_avg_temp_c']} °C",
            })

        if kpis["wind_speed_mps"] > 25.0:
            alerts.append({
                "subsystem": "ENVIRONMENT_WEATHER",
                "severity": "WARNING",
                "message": f"Severe katabatic blizzard winds: {kpis['wind_speed_mps']} m/s",
            })

        if kpis["running_chp_count"] == 0:
            alerts.append({
                "subsystem": "ENERGY_GENERATION",
                "severity": "EMERGENCY",
                "message": "TOTAL STATION BLACKOUT: Zero CHP generators active.",
            })

        if self.infra_registry.physics.pipelines.water01_pipe_temp_c < 1.0:
            alerts.append({
                "subsystem": "INFRASTRUCTURE_PIPELINES",
                "severity": "WARNING",
                "message": f"Utilidor fresh water line freeze warning: {self.infra_registry.physics.pipelines.water01_pipe_temp_c} °C",
            })

        if self.logistics_registry.physics.cold_chain.reefer01.temperature_excursion:
            alerts.append({
                "subsystem": "LOGISTICS_COLD_CHAIN",
                "severity": "CRITICAL",
                "message": f"Cold container Reefer-01 temperature excursion: {self.logistics_registry.physics.cold_chain.reefer01.core_temp_c} °C",
            })

        return alerts

    def get_snapshot(self) -> MasterTwinSnapshot:
        """Generate a complete serializable digital twin snapshot."""
        return MasterTwinSnapshot(
            timestamp_iso=self.clock.isoformat(),
            sim_time_seconds=self.clock.elapsed_seconds,
            active_scenario=self._active_scenario.value,
            sensor_count=self.sensor_count,
            readings=dict(self._cached_readings),
            kpis=self.get_station_kpis(),
            alerts=self.get_active_alerts(),
            station_id=self.station_id,
        )


class MaitriMasterTwinEngine(BharatiMasterTwinEngine):
    """Master Digital Twin simulation engine for Maitri Station.
    
    Target: Maitri Station, Schirmacher Oasis, Queen Maud Land, East Antarctica.
    - Coordinates: 70° 45' 58" S, 11° 43' 50" E, Elevation: 117m.
    - Primary fresh water line from Priyadarshini Lake with active trace heating.
    - 3x 100 kVA Cummins/Kirloskar Gensets.
    - Containerized modular architecture.
    """

    def __init__(
        self,
        seed: int | None = 101,
        clock: SimulationClock | None = None,
    ) -> None:
        super().__init__(seed=seed, clock=clock)
        self.station_id = "maitri"
        self.station_name = "Maitri Research Station"
        self.location = "Schirmacher Oasis, Queen Maud Land, East Antarctica"
        self.coordinates = {
            "latitude": -70.7661,
            "longitude": 11.7306,
            "latitude_dms": "70° 45' 58'' S",
            "longitude_dms": "11° 43' 50'' E",
            "elevation_m": 117.0,
        }

