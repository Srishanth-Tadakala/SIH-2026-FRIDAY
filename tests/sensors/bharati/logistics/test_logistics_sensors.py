"""Comprehensive Unit Tests for Bharati Station Logistics Observation Layer v1.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E).

Covers:
1. Exact 98 configured points across 11 domains
2. Globally unique sensor IDs
3. Fleet asset registry completeness (16 documented physical machines)
4. Domain counts match specification (16, 10, 10, 8, 7, 7, 8, 9, 10, 5, 8)
5. Anti-duplication rule: zero duplicate environmental measurements
6. Strict taxonomy: SensorKind.DERIVED vs STATE vs INSTRUMENT
7. Evidence discipline: DOCUMENTED vs NOT_PUBLICLY_CONFIRMED vs IMPLIED vs DERIVED
8. Provenance discipline: 100% SIMULATED provenance and source_reference
9. State-bound resolution from BharatiLogisticsPhysicsState
10. Invariant: default_value is fallback-only, never primary reading source
11. Invariant: derived sensors compute dynamically from underlying state
12. Invariant: sensor reading updates when physics state changes
13. Lead hauler (PB-01) telemetry coherence
14. Cargo and containers coherence
15. Fuel logistics and dispensing coherence
16. Cold-chain reefer telemetry and excursion calculation
17. Aviation flight telemetry and helipad condition
18. Marine vessel AIS and discharge progress
19. Route network and surface traction index
20. Mission coordination, anonymous teams, and return margin semantics
21. Inventory stores, rations autonomy, and stockout risk
22. Waste backhaul readiness under Madrid Protocol
23. Derived indicators calculation and explainable condition summary
24. Technical failure: DROPOUT
25. Technical failure: STALE
26. Technical failure: OUT_OF_RANGE
27. Technical failure: STUCK (freezes last valid physical reading)
28. Fault clearance: single and all
29. Scenario: NORMAL
30. Scenario: VEHICLE_BREAKDOWN
31. Scenario: FUEL_SHORTAGE
32. Scenario: COLD_CHAIN_EXCURSION
33. Scenario: BLIZZARD_LOGISTICS_RESTRICTION
34. Scenario: HEAVY_CARGO_OPERATION
35. Scenario: MISSION_FIELD_DEPLOYMENT
36. Scenario: INVENTORY_SHORTAGE
37. Cross-pillar: update_from_environment high wind closure
38. Cross-pillar: update_from_environment low visibility impact
39. Cross-pillar: update_from_environment snow depth traction drop
40. Cross-pillar: update_from_energy reefer power transfer
41. Cross-pillar: read-only non-mutation invariance
42. Registry search: by domain
43. Registry search: by asset
44. Registry search: by kind
45. Registry search: by location scope
46. Registry execution: step advances simulation time
47. Serialization: SensorReading.to_dict() integrity
48. Madrid Protocol terminology verification
"""

from __future__ import annotations

import unittest

from backend.sensors.bharati_sensors.energy.clock import SimulationClock
from backend.sensors.bharati_sensors.logistics import (
    BHARATI_LOGISTICS_SENSORS,
    CONFIG_BY_ID,
    CONFIGS_BY_DOMAIN,
    FLEET_ASSET_REGISTRY,
    BharatiLogisticsPhysicsState,
    EvidenceLevel,
    FailureType,
    LogisticsDomain,
    LogisticsSensorRegistry,
    PhysicalQuantity,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    create_bharati_logistics_sensors,
)


class TestBharatiLogisticsSensors(unittest.TestCase):
    """Test suite for Bharati Logistics Observation Layer v1."""

    def setUp(self) -> None:
        self.clock = SimulationClock()
        self.registry, self.physics, _ = create_bharati_logistics_sensors(clock=self.clock)

    # ==========================================================================
    # 1. CATALOGUE, DOMAINS, AND ASSET REGISTRY
    # ==========================================================================

    def test_total_sensor_count_is_exactly_98(self) -> None:
        """Verify that exactly 98 sensors are configured and registered."""
        self.assertEqual(len(BHARATI_LOGISTICS_SENSORS), 98)
        self.assertEqual(self.registry.sensor_count, 98)

    def test_all_sensor_ids_are_unique(self) -> None:
        """Verify that every sensor ID is globally unique."""
        ids = [cfg.sensor_id for cfg in BHARATI_LOGISTICS_SENSORS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_eleven_distinct_domains_exist(self) -> None:
        """Verify that exactly 11 domains (10 operational + 1 derived) are defined."""
        self.assertEqual(len(LogisticsDomain), 11)
        expected_domains = {
            "FLEET", "CARGO", "FUEL", "COLD_CHAIN", "AVIATION",
            "MARINE", "ROUTES", "MISSIONS", "INVENTORY", "WASTE", "DERIVED"
        }
        actual_domains = {d.value for d in LogisticsDomain}
        self.assertEqual(actual_domains, expected_domains)

    def test_domain_counts_match_specification(self) -> None:
        """Verify exact sensor count per domain: 16+10+10+8+7+7+8+9+10+5+8 = 98."""
        expected = {
            LogisticsDomain.FLEET: 16,
            LogisticsDomain.CARGO: 10,
            LogisticsDomain.FUEL: 10,
            LogisticsDomain.COLD_CHAIN: 8,
            LogisticsDomain.AVIATION: 7,
            LogisticsDomain.MARINE: 7,
            LogisticsDomain.ROUTES: 8,
            LogisticsDomain.MISSIONS: 9,
            LogisticsDomain.INVENTORY: 10,
            LogisticsDomain.WASTE: 5,
            LogisticsDomain.DERIVED: 8,
        }
        for domain, count in expected.items():
            sensors = self.registry.get_sensors_by_domain(domain)
            self.assertEqual(
                len(sensors),
                count,
                f"Domain {domain.value} expected {count} sensors, got {len(sensors)}",
            )

    def test_fleet_asset_registry_has_16_physical_machines(self) -> None:
        """Verify all 16 documented Bharati fleet machines are registered."""
        self.assertEqual(len(FLEET_ASSET_REGISTRY), 16)
        expected_machines = [
            "PB-01", "PB-02", "PB-03", "PB-04", "PB-05", "PB-06",
            "SC-01", "SC-02", "SC-03", "SC-04",
            "TELEHANDLER-01", "EXCAVATOR-01", "EXCAVATOR-02",
            "BULLDOZER-01", "MANTIS-01", "MANTIS-02"
        ]
        for m in expected_machines:
            self.assertIn(m, FLEET_ASSET_REGISTRY)
            info = FLEET_ASSET_REGISTRY[m]
            self.assertEqual(info.asset_id, m)
            self.assertTrue(len(info.documented_model) > 0)
            self.assertTrue(len(info.operational_role) > 0)

    # ==========================================================================
    # 2. INVARIANTS, TAXONOMY, AND EVIDENCE DISCIPLINE
    # ==========================================================================

    def test_no_logistics_sensor_duplicates_environment_measurement(self) -> None:
        """Verify Logistics does NOT independently simulate ambient environment measurements.
        
        Logistics must NOT own independent sensors for ambient wind, sea ice concentration,
        snow depth, or ice thickness.
        """
        forbidden_sensor_ids = {
            "LOG-AV-HELIPAD-WIND",
            "LOG-MAR-ICE-CONC",
            "LOG-ROUTE-COAST-SNOW-DEPTH",
            "LOG-ROUTE-FASTICE-THICK",
        }
        for s_id in forbidden_sensor_ids:
            self.assertNotIn(
                s_id,
                CONFIG_BY_ID,
                f"Forbidden duplicate environmental observation {s_id} found in Logistics!",
            )

    def test_state_bound_sensor_reads_physics_state(self) -> None:
        """Verify state-bound sensors dynamically resolve from BharatiLogisticsPhysicsState."""
        self.physics.fleet.pb01.engine_temp_c = 68.5
        reading = self.registry.read_sensor("LOG-FLEET-PB01-ENG-TEMP")
        self.assertEqual(reading.value, 68.5)

        self.physics.cargo.c01.shock_g = 1.85
        reading_cargo = self.registry.read_sensor("LOG-CARGO-C01-SHOCK")
        self.assertEqual(reading_cargo.value, 1.85)

    def test_default_value_is_not_normal_reading(self) -> None:
        """Verify that healthy readings do NOT come from fallback default_value."""
        sensor = self.registry.get_sensor("LOG-FLEET-PB01-FUEL-LVL")
        cfg_default = sensor.config.default_value  # 85.0

        # Change physics state to a different value
        self.physics.fleet.pb01.fuel_level_percent = 52.4
        reading = sensor.read()
        self.assertEqual(reading.value, 52.4)
        self.assertNotEqual(reading.value, cfg_default)

    def test_derived_sensor_never_reads_default_as_primary_value(self) -> None:
        """Verify derived indicators calculate from underlying state rather than default_value."""
        sensor = self.registry.get_sensor("LOG-DERIVED-FLEET-AVAIL")
        # Under normal conditions: 15/16 assets operational -> 93.75%
        reading = sensor.read()
        self.assertEqual(reading.value, 93.75)

        # Break two vehicles
        self.physics.fleet.pb01.status = "FAULT"
        self.physics.fleet.pb02_status = "MAINTENANCE"
        self.physics.recompute_derived_state()
        new_reading = sensor.read()
        # 13/16 assets -> 81.25%
        self.assertEqual(new_reading.value, 81.25)

    def test_derived_kind_classification_discipline(self) -> None:
        """Verify all calculated quantities are typed SensorKind.DERIVED."""
        derived_ids = [
            "LOG-ROUTE-SURFACE-TRACTION",
            "LOG-MISS-TEAM01-RETURN-MARGIN",
            "LOG-INV-STOCKOUT-RISK",
            "LOG-DERIVED-FLEET-AVAIL",
            "LOG-DERIVED-CARGO-INTEGRITY",
            "LOG-DERIVED-COLD-CHAIN-RISK",
            "LOG-DERIVED-ROUTE-ACCESS",
            "LOG-DERIVED-AIR-ACCESS",
            "LOG-DERIVED-MARINE-ACCESS",
            "LOG-DERIVED-LOGISTICS-RISK",
        ]
        for sid in derived_ids:
            cfg = CONFIG_BY_ID[sid]
            self.assertEqual(
                cfg.kind,
                SensorKind.DERIVED,
                f"Sensor {sid} should be SensorKind.DERIVED, got {cfg.kind}",
            )

    def test_evidence_classification_discipline(self) -> None:
        """Verify evidence discipline: CAN/GPS & reefer temp are NOT_PUBLICLY_CONFIRMED; assets DOCUMENTED."""
        not_confirmed = [
            "LOG-FLEET-PB01-SPEED",
            "LOG-FLEET-PB01-RPM",
            "LOG-FLEET-PB01-ENG-HOURS",
            "LOG-REEFER-01-TEMP",
            "LOG-FUEL-HELI-SUPPLY-LVL",
            "LOG-AV-HELI-ALTITUDE",
        ]
        for sid in not_confirmed:
            cfg = CONFIG_BY_ID[sid]
            self.assertEqual(cfg.evidence_level, EvidenceLevel.NOT_PUBLICLY_CONFIRMED)

        documented_state = [
            "LOG-FLEET-PB01-STATUS",
            "LOG-CARGO-TOTAL-COUNT",
            "LOG-CARGO-C01-WEIGHT",
            "LOG-FUEL-VEH-TANK-LVL",
            "LOG-AV-HELIPAD-STATUS",
            "LOG-MAR-VESSEL-STATUS",
            "LOG-ROUTE-STATION-STATUS",
            "LOG-MISS-ACTIVE-COUNT",
            "LOG-INV-RATIONS-DAYS",
            "LOG-WASTE-SOLID-VOL",
        ]
        for sid in documented_state:
            cfg = CONFIG_BY_ID[sid]
            self.assertEqual(cfg.evidence_level, EvidenceLevel.DOCUMENTED)

    def test_all_sensor_readings_have_simulated_provenance(self) -> None:
        """Verify 100% of sensor readings report SIMULATED provenance and source reference."""
        readings = self.registry.read_all()
        for sid, r in readings.items():
            self.assertEqual(r.provenance, SensorProvenance.SIMULATED)
            self.assertEqual(r.source_reference, "bharati_logistics_physics_v1")
            self.assertEqual(r.station_id, "BHARATI")

    def test_madrid_protocol_terminology(self) -> None:
        """Verify Madrid Protocol terminology in waste configs and state."""
        cfg = CONFIG_BY_ID["LOG-WASTE-RET-READY"]
        self.assertIn("Madrid Protocol", cfg.description)

    def test_anonymous_field_teams_zero_pii(self) -> None:
        """Verify missions tracking uses anonymous operational markers with zero PII."""
        cfg1 = CONFIG_BY_ID["LOG-MISS-TEAM01-STATUS"]
        self.assertEqual(cfg1.asset_id, "TEAM-FIELD-01")
        cfg2 = CONFIG_BY_ID["LOG-MISS-TEAM02-STATUS"]
        self.assertEqual(cfg2.asset_id, "TEAM-FIELD-02")

    def test_mission_return_margin_semantics(self) -> None:
        """Verify return margin sensor semantics match return_margin_minutes."""
        cfg = CONFIG_BY_ID["LOG-MISS-TEAM01-RETURN-MARGIN"]
        self.assertEqual(cfg.state_path, "missions.team01.return_margin_minutes")
        self.assertEqual(cfg.unit, "min")

    # ==========================================================================
    # 3. DOMAIN SUBSYSTEMS & PHYSICAL COHERENCE
    # ==========================================================================

    def test_fleet_telemetry_coherence(self) -> None:
        """Verify PB-01 engine speed, temperature, and status read correctly."""
        r_speed = self.registry.read_sensor("LOG-FLEET-PB01-SPEED")
        r_rpm = self.registry.read_sensor("LOG-FLEET-PB01-RPM")
        r_temp = self.registry.read_sensor("LOG-FLEET-PB01-ENG-TEMP")
        r_status = self.registry.read_sensor("LOG-FLEET-PB01-STATUS")

        self.assertEqual(r_speed.value, 0.0)
        self.assertEqual(r_rpm.value, 0.0)
        self.assertEqual(r_temp.value, -10.0)
        self.assertEqual(r_status.value, "STANDBY")

    def test_cargo_sensors_coherence(self) -> None:
        """Verify container C01 weight, tilt, shock, and door status."""
        r_weight = self.registry.read_sensor("LOG-CARGO-C01-WEIGHT")
        r_shock = self.registry.read_sensor("LOG-CARGO-C01-SHOCK")
        r_door = self.registry.read_sensor("LOG-CARGO-C01-DOOR")
        r_haz = self.registry.read_sensor("LOG-CARGO-HAZMAT-STATUS")

        self.assertEqual(r_weight.value, 12500.0)
        self.assertEqual(r_shock.value, 0.05)
        self.assertEqual(r_door.value, "CLOSED_LOCKED")
        self.assertEqual(r_haz.value, "CONTAINED_SECURE")

    def test_fuel_logistics_coherence(self) -> None:
        """Verify helicopter fuel context, vehicle tank, and leak monitor."""
        r_heli = self.registry.read_sensor("LOG-FUEL-HELI-SUPPLY-LVL")
        r_veh = self.registry.read_sensor("LOG-FUEL-VEH-TANK-LVL")
        r_leak = self.registry.read_sensor("LOG-FUEL-LEAK-MONITOR")

        self.assertEqual(r_heli.value, 18500.0)
        self.assertEqual(r_veh.value, 38500.0)
        self.assertEqual(r_leak.value, "NORMAL")

    def test_cold_chain_coherence(self) -> None:
        """Verify reefer 01 temperature, setpoint, and excursion indicator."""
        r_temp = self.registry.read_sensor("LOG-REEFER-01-TEMP")
        r_set = self.registry.read_sensor("LOG-REEFER-01-SETPOINT")
        r_excursion = self.registry.read_sensor("LOG-REEFER-01-EXCURSION")

        self.assertEqual(r_temp.value, -22.0)
        self.assertEqual(r_set.value, -22.0)
        self.assertFalse(r_excursion.value)

    def test_aviation_logistics_coherence(self) -> None:
        """Verify helicopter status, fuel, altitude, and helipad status."""
        r_status = self.registry.read_sensor("LOG-AV-HELI-STATUS")
        r_pad = self.registry.read_sensor("LOG-AV-HELIPAD-STATUS")

        self.assertEqual(r_status.value, "GROUNDED_READY")
        self.assertEqual(r_pad.value, "CLEAR_OPEN")

    def test_marine_logistics_coherence(self) -> None:
        """Verify vessel AIS distance, barge status, and berth safety."""
        r_dist = self.registry.read_sensor("LOG-MAR-VESSEL-DIST")
        r_barge = self.registry.read_sensor("LOG-MAR-BARGE-STATUS")
        r_safe = self.registry.read_sensor("LOG-MAR-SEA-BERTH-SAFE")

        self.assertEqual(r_dist.value, 2.4)
        self.assertEqual(r_barge.value, "STANDBY")
        self.assertEqual(r_safe.value, "SAFE")

    def test_routes_accessibility_coherence(self) -> None:
        """Verify route statuses, traction index, and crevasse risk."""
        r_ring = self.registry.read_sensor("LOG-ROUTE-STATION-STATUS")
        r_traction = self.registry.read_sensor("LOG-ROUTE-SURFACE-TRACTION")
        r_crevasse = self.registry.read_sensor("LOG-ROUTE-CREVASSE-RISK")

        self.assertEqual(r_ring.value, "OPEN")
        self.assertEqual(r_traction.value, 85.0)
        self.assertEqual(r_crevasse.value, "LOW")

    def test_missions_coherence(self) -> None:
        """Verify active missions, pax distribution, and Team 01 return margin."""
        r_active = self.registry.read_sensor("LOG-MISS-ACTIVE-COUNT")
        r_stn = self.registry.read_sensor("LOG-MISS-STATION-PAX")
        r_fld = self.registry.read_sensor("LOG-MISS-FIELD-PAX")
        r_margin = self.registry.read_sensor("LOG-MISS-TEAM01-RETURN-MARGIN")

        self.assertEqual(r_active.value, 1.0)
        self.assertEqual(r_stn.value, 24.0)
        self.assertEqual(r_fld.value, 3.0)
        self.assertEqual(r_margin.value, 180.0)

    def test_inventory_coherence(self) -> None:
        """Verify rations days, spares percentages, and stockout risk."""
        r_days = self.registry.read_sensor("LOG-INV-RATIONS-DAYS")
        r_gen = self.registry.read_sensor("LOG-INV-SPARES-GEN-PCT")
        r_risk = self.registry.read_sensor("LOG-INV-STOCKOUT-RISK")

        self.assertEqual(r_days.value, 420.0)
        self.assertEqual(r_gen.value, 82.0)
        self.assertEqual(r_risk.value, 0.05)

    def test_waste_logistics_coherence(self) -> None:
        """Verify solid waste volume, hazard containment, and return readiness."""
        r_vol = self.registry.read_sensor("LOG-WASTE-SOLID-VOL")
        r_haz = self.registry.read_sensor("LOG-WASTE-HAZARD-STATUS")
        r_ret = self.registry.read_sensor("LOG-WASTE-RET-READY")

        self.assertEqual(r_vol.value, 18.5)
        self.assertEqual(r_haz.value, "SECURED")
        self.assertEqual(r_ret.value, 85.0)

    def test_derived_indicators_coherence(self) -> None:
        """Verify derived fleet availability, route access, and condition summary."""
        r_fleet = self.registry.read_sensor("LOG-DERIVED-FLEET-AVAIL")
        r_route = self.registry.read_sensor("LOG-DERIVED-ROUTE-ACCESS")
        r_cond = self.registry.read_sensor("LOG-DERIVED-LOGISTICS-CONDITION")

        self.assertEqual(r_fleet.value, 93.75)
        self.assertEqual(r_route.value, 100.0)
        self.assertEqual(r_cond.value, "NORMAL")

    # ==========================================================================
    # 4. TECHNICAL FAILURE MODES
    # ==========================================================================

    def test_dropout_failure_injection(self) -> None:
        """Verify DROPOUT causes value=None, quality=FAILED, valid=False, confidence=0.0."""
        sid = "LOG-FLEET-PB01-SPEED"
        self.registry.simulate_failure(sid, FailureType.DROPOUT)
        reading = self.registry.read_sensor(sid)

        self.assertIsNone(reading.value)
        self.assertEqual(reading.quality, SensorQuality.FAILED)
        self.assertFalse(reading.valid)
        self.assertEqual(reading.confidence, 0.0)

    def test_stale_failure_injection(self) -> None:
        """Verify STALE causes timestamp in past, quality=STALE, valid=False."""
        sid = "LOG-FUEL-VEH-TANK-LVL"
        self.registry.simulate_failure(sid, FailureType.STALE)
        reading = self.registry.read_sensor(sid)

        self.assertEqual(reading.quality, SensorQuality.STALE)
        self.assertFalse(reading.valid)
        self.assertEqual(reading.confidence, 0.4)

    def test_out_of_range_failure_injection(self) -> None:
        """Verify OUT_OF_RANGE forces value beyond limits and quality=BAD."""
        sid = "LOG-REEFER-01-TEMP"  # min -40, max 20
        self.registry.simulate_failure(sid, FailureType.OUT_OF_RANGE)
        reading = self.registry.read_sensor(sid)

        self.assertGreater(reading.value, 20.0)
        self.assertEqual(reading.quality, SensorQuality.BAD)
        self.assertFalse(reading.valid)

    def test_stuck_failure_injection_preserves_last_reading(self) -> None:
        """Verify STUCK preserves last valid physical reading rather than default_value."""
        sid = "LOG-ROUTE-SURFACE-TRACTION"
        self.physics.routes.surface_traction_index = 62.5
        first_read = self.registry.read_sensor(sid)
        self.assertEqual(first_read.value, 62.5)

        # Inject STUCK
        self.registry.simulate_failure(sid, FailureType.STUCK)
        # Advance physics state
        self.physics.routes.surface_traction_index = 25.0
        stuck_read = self.registry.read_sensor(sid)

        self.assertEqual(stuck_read.value, 62.5)  # Frozen at last valid observation
        self.assertEqual(stuck_read.quality, SensorQuality.BAD)
        self.assertFalse(stuck_read.valid)

    def test_clear_failure_restores_healthy_reading(self) -> None:
        """Verify clear_failure restores normal reading and GOOD quality."""
        sid = "LOG-FLEET-PB01-SPEED"
        self.registry.simulate_failure(sid, FailureType.DROPOUT)
        failed = self.registry.read_sensor(sid)
        self.assertEqual(failed.quality, SensorQuality.FAILED)

        self.registry.clear_failure(sid)
        restored = self.registry.read_sensor(sid)
        self.assertEqual(restored.quality, SensorQuality.GOOD)
        self.assertTrue(restored.valid)

    def test_clear_all_failures(self) -> None:
        """Verify clear_all_failures restores all faulted sensors."""
        self.registry.simulate_failure("LOG-FLEET-PB01-SPEED", FailureType.DROPOUT)
        self.registry.simulate_failure("LOG-REEFER-01-TEMP", FailureType.OUT_OF_RANGE)

        self.registry.clear_all_failures()
        r1 = self.registry.read_sensor("LOG-FLEET-PB01-SPEED")
        r2 = self.registry.read_sensor("LOG-REEFER-01-TEMP")
        self.assertEqual(r1.quality, SensorQuality.GOOD)
        self.assertEqual(r2.quality, SensorQuality.GOOD)

    # ==========================================================================
    # 5. OPERATIONAL SCENARIOS & PROPAGATION
    # ==========================================================================

    def test_scenario_normal(self) -> None:
        """Verify NORMAL scenario state."""
        self.registry.set_scenario("NORMAL")
        r_cond = self.registry.read_sensor("LOG-DERIVED-LOGISTICS-CONDITION")
        self.assertEqual(r_cond.value, "NORMAL")

    def test_scenario_vehicle_breakdown(self) -> None:
        """Verify VEHICLE_BREAKDOWN drops fleet availability and triggers CAUTION."""
        self.registry.set_scenario("VEHICLE_BREAKDOWN")
        r_status = self.registry.read_sensor("LOG-FLEET-PB01-STATUS")
        r_avail = self.registry.read_sensor("LOG-DERIVED-FLEET-AVAIL")
        r_cond = self.registry.read_sensor("LOG-DERIVED-LOGISTICS-CONDITION")

        self.assertEqual(r_status.value, "FAULT")
        self.assertLess(r_avail.value, 90.0)
        self.assertEqual(r_cond.value, "CAUTION")

    def test_scenario_fuel_shortage(self) -> None:
        """Verify FUEL_SHORTAGE disables dispenser and raises stockout risk."""
        self.registry.set_scenario("FUEL_SHORTAGE")
        r_disp = self.registry.read_sensor("LOG-FUEL-DISP-STATUS")
        r_pct = self.registry.read_sensor("LOG-FUEL-VEH-TANK-PCT")
        r_risk = self.registry.read_sensor("LOG-INV-STOCKOUT-RISK")

        self.assertEqual(r_disp.value, "DISABLED")
        self.assertEqual(r_pct.value, 14.5)
        self.assertGreater(r_risk.value, 0.5)

    def test_scenario_cold_chain_excursion(self) -> None:
        """Verify COLD_CHAIN_EXCURSION sets excursion True and raises cold-chain risk."""
        self.registry.set_scenario("COLD_CHAIN_EXCURSION")
        r_temp = self.registry.read_sensor("LOG-REEFER-01-TEMP")
        r_exc = self.registry.read_sensor("LOG-REEFER-01-EXCURSION")
        r_risk = self.registry.read_sensor("LOG-DERIVED-COLD-CHAIN-RISK")

        self.assertEqual(r_temp.value, -4.5)
        self.assertTrue(r_exc.value)
        self.assertGreater(r_risk.value, 0.4)

    def test_scenario_blizzard_restriction(self) -> None:
        """Verify BLIZZARD_LOGISTICS_RESTRICTION shuts aviation and locks down routes."""
        self.registry.set_scenario("BLIZZARD_LOGISTICS_RESTRICTION")
        r_pad = self.registry.read_sensor("LOG-AV-HELIPAD-STATUS")
        r_air = self.registry.read_sensor("LOG-DERIVED-AIR-ACCESS")
        r_ring = self.registry.read_sensor("LOG-ROUTE-STATION-STATUS")
        r_cond = self.registry.read_sensor("LOG-DERIVED-LOGISTICS-CONDITION")

        self.assertEqual(r_pad.value, "CLOSED_WEATHER")
        self.assertEqual(r_air.value, 0.0)
        self.assertEqual(r_ring.value, "DRIFT_BLOCKED")
        self.assertEqual(r_cond.value, "RESTRICTED")

    def test_scenario_heavy_cargo_operation(self) -> None:
        """Verify HEAVY_CARGO_OPERATION activates barge, crane, and telehandler."""
        self.registry.set_scenario("HEAVY_CARGO_OPERATION")
        r_transit = self.registry.read_sensor("LOG-CARGO-IN-TRANSIT")
        r_barge = self.registry.read_sensor("LOG-MAR-BARGE-STATUS")
        r_crane = self.registry.read_sensor("LOG-FLEET-CRANE01-STATUS")

        self.assertEqual(r_transit.value, 8.0)
        self.assertEqual(r_barge.value, "SHUTTLE")
        self.assertEqual(r_crane.value, "ACTIVE")

    def test_scenario_mission_field_deployment(self) -> None:
        """Verify MISSION_FIELD_DEPLOYMENT updates pax count and active teams."""
        self.registry.set_scenario("MISSION_FIELD_DEPLOYMENT")
        r_act = self.registry.read_sensor("LOG-MISS-ACTIVE-COUNT")
        r_fld = self.registry.read_sensor("LOG-MISS-FIELD-PAX")
        r_t2 = self.registry.read_sensor("LOG-MISS-TEAM02-STATUS")

        self.assertEqual(r_act.value, 2.0)
        self.assertEqual(r_fld.value, 7.0)
        self.assertEqual(r_t2.value, "DEPLOYED")

    def test_scenario_inventory_shortage(self) -> None:
        """Verify INVENTORY_SHORTAGE raises critical alerts and stockout score."""
        self.registry.set_scenario("INVENTORY_SHORTAGE")
        r_alerts = self.registry.read_sensor("LOG-INV-CRITICAL-ALERTS")
        r_risk = self.registry.read_sensor("LOG-INV-STOCKOUT-RISK")

        self.assertEqual(r_alerts.value, 3.0)
        self.assertEqual(r_risk.value, 0.72)

    # ==========================================================================
    # 6. READ-ONLY CROSS-PILLAR INTERFACES
    # ==========================================================================

    def test_update_from_environment_high_wind(self) -> None:
        """Verify external high wind closes helipad and degrades sea berth."""
        self.registry.update_from_environment({"wind_speed_mps": 24.5})
        r_pad = self.registry.read_sensor("LOG-AV-HELIPAD-STATUS")
        r_berth = self.registry.read_sensor("LOG-MAR-SEA-BERTH-SAFE")

        self.assertEqual(r_pad.value, "CLOSED_WEATHER")
        self.assertEqual(r_berth.value, "UNSAFE")

    def test_update_from_environment_low_visibility(self) -> None:
        """Verify external fog/blizzard visibility reduction updates route visibility."""
        self.registry.update_from_environment({"visibility_m": 1200.0})
        r_vis = self.registry.read_sensor("LOG-ROUTE-VIS-LIMIT")
        self.assertEqual(r_vis.value, "RESTRICTED")

        self.registry.update_from_environment({"visibility_m": 250.0})
        r_zero = self.registry.read_sensor("LOG-ROUTE-VIS-LIMIT")
        self.assertEqual(r_zero.value, "ZERO_VISIBILITY")

    def test_update_from_environment_snow_depth(self) -> None:
        """Verify deep snow reduces traction index and covers helipad."""
        self.registry.update_from_environment({"snow_depth_m": 1.2})
        r_trac = self.registry.read_sensor("LOG-ROUTE-SURFACE-TRACTION")
        r_pad = self.registry.read_sensor("LOG-AV-HELIPAD-STATUS")

        self.assertLess(r_trac.value, 75.0)
        self.assertEqual(r_pad.value, "SNOW_COVERED")

    def test_update_from_energy_grid_blackout(self) -> None:
        """Verify grid blackout transfers reefer power to backup diesel genset."""
        self.registry.update_from_energy({"grid_status": "BLACKOUT"})
        # When active scenario is non-normal, it transfers
        self.physics.set_scenario("VEHICLE_BREAKDOWN")
        self.registry.update_from_energy({"grid_status": "BLACKOUT"})
        r_pwr = self.registry.read_sensor("LOG-REEFER-01-PWR-STATE")
        self.assertEqual(r_pwr.value, "DIESEL_GENSET")

    def test_cross_pillar_read_only_invariance(self) -> None:
        """Verify Logistics does not modify input dicts passed via read-only interfaces."""
        env_input = {"wind_speed_mps": 14.0, "visibility_m": 12000.0}
        env_copy = dict(env_input)
        self.registry.update_from_environment(env_input)
        self.assertEqual(env_input, env_copy)

    # ==========================================================================
    # 7. REGISTRY QUERY METHODS & OPERATIONS
    # ==========================================================================

    def test_get_sensors_by_asset(self) -> None:
        """Verify sensor retrieval by asset ID."""
        pb01_sensors = self.registry.get_sensors_by_asset("PB-01")
        self.assertEqual(len(pb01_sensors), 9)

        reefer_sensors = self.registry.get_sensors_by_asset("REEFER-01")
        self.assertEqual(len(reefer_sensors), 6)

    def test_get_sensors_by_kind(self) -> None:
        """Verify sensor retrieval by kind (INSTRUMENT, STATE, DERIVED)."""
        instruments = self.registry.get_sensors_by_kind(SensorKind.INSTRUMENT)
        states = self.registry.get_sensors_by_kind(SensorKind.STATE)
        deriveds = self.registry.get_sensors_by_kind(SensorKind.DERIVED)

        self.assertEqual(len(instruments) + len(states) + len(deriveds), 98)

    def test_get_sensors_by_location_scope(self) -> None:
        """Verify retrieval by spatial scope."""
        fleet_sensors = self.registry.get_sensors_by_location_scope("LOCAL_FLEET")
        self.assertEqual(len(fleet_sensors), 16)

    def test_registry_step_advances_simulation_time(self) -> None:
        """Verify registry.step advances clock and elapsed seconds."""
        initial_time = self.clock.elapsed_seconds
        self.registry.step(120.0)
        self.assertEqual(self.clock.elapsed_seconds, initial_time + 120.0)

    def test_sensor_reading_to_dict_serialization(self) -> None:
        """Verify reading to_dict serialization contains expected string enum values."""
        reading = self.registry.read_sensor("LOG-FLEET-PB01-SPEED")
        d = reading.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d["sensor_id"], "LOG-FLEET-PB01-SPEED")
        self.assertEqual(d["domain"], "FLEET")
        self.assertEqual(d["provenance"], "SIMULATED")
        self.assertEqual(d["quality"], "GOOD")


if __name__ == "__main__":
    unittest.main()
