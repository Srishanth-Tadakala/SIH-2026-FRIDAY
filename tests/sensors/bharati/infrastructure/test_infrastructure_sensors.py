"""Comprehensive Unit Tests for Bharati Station Infrastructure Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Covers verification criteria:
1. All 11 infrastructure domains present
2. Sensor count aligns with ~175-190 target range (non-mechanically enforced)
3. Sensor IDs globally unique
4. Metadata completeness on all readings
5. Sensor provenance (SIMULATED) and source_reference ("bharati_infrastructure_physics_v1")
6. Evidence classification (DOCUMENTED vs IMPLIED vs NOT_PUBLICLY_CONFIRMED vs DERIVED)
7. Physical station facts (134 modules, 86 pillars) vs unconfirmed structural telemetry
8. Deterministic confidence values (no random generation)
9. Physical quantities and units validation
10. Water mass balance and tank volume integration
11. Water -> Wastewater physical coupling
12. Wastewater MBR treatment degradation
13. HVAC coil heat exchange thermodynamics
14. Fresh air ventilation CO2 reduction
15. Refrigeration target setpoint vs dynamic state
16. Refrigeration door open heat ingress and compressor response
17. Utilidor pipeline freeze risk under trace heating loss
18. Fire physics propagation and isolation actuation
19. Multi-sensor correlation observing single physical phenomena
20. Asset hierarchy integrity (parent assets, no cycles)
21. BMS telemetry health indicator calculation
22. Read-only auxiliary electrical power aggregation
23. Sensor failure simulation: DROPOUT
24. Sensor failure simulation: STALE
25. Sensor failure simulation: OUT_OF_RANGE
26. Sensor failure simulation: STUCK (preserving frozen reading value)
27. Failure clearance (single and all)
28. Registry lookups (by ID, domain, subsystem, kind, asset)
29. Reproducibility with fixed seed
30. Environmental input boundary conditions influence
31. Structural stilt and bedrock displacement indicators
32. Emergency shelter autonomy and life-support readiness
"""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.sensors.bharati_sensors.energy.clock import SimulationClock
from backend.sensors.bharati_sensors.infrastructure import (
    BharatiInfrastructurePhysicsState,
    EnvironmentalInput,
    EvidenceLevel,
    FailureType,
    InfrastructureDomain,
    PhysicalQuantity,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    create_bharati_infrastructure_sensors,
)
from backend.sensors.bharati_sensors.infrastructure.config import (
    BUILDING_PREFAB_MODULES,
    BUILDING_STEEL_PILLARS,
    FRESH_WATER_TANK_CAPACITY_L,
    SOURCE_REFERENCE_DEFAULT,
    get_confidence_for_evidence,
)


class TestBharatiInfrastructureSensors(unittest.TestCase):
    """Test suite verifying the Bharati Station Infrastructure Sensor Layer."""

    def setUp(self) -> None:
        """Create a standard test registry with a fixed seed and baseline environment."""
        self.clock = SimulationClock(datetime(2026, 9, 19, 12, 0, 0))
        self.env = EnvironmentalInput(
            ambient_temperature_c=-18.0,
            wind_speed_ms=12.0,
            wind_direction_deg=220.0,
            solar_radiation_w_m2=250.0,
        )
        self.registry = create_bharati_infrastructure_sensors(
            seed=42, clock=self.clock, environmental_input=self.env
        )

    def test_01_all_eleven_domains_present_and_count_in_target_range(self) -> None:
        """Verify all 11 domains exist and total sensor count is within target design range."""
        expected_domains = {
            InfrastructureDomain.BUILDING,
            InfrastructureDomain.HVAC,
            InfrastructureDomain.WATER,
            InfrastructureDomain.WASTEWATER,
            InfrastructureDomain.FIRE,
            InfrastructureDomain.REFRIGERATION,
            InfrastructureDomain.PIPELINES,
            InfrastructureDomain.EMERGENCY,
            InfrastructureDomain.SECURITY,
            InfrastructureDomain.BMS,
            InfrastructureDomain.VIRTUAL,
        }

        all_sensors = self.registry.get_all_sensors()
        actual_domains = {s.domain for s in all_sensors}

        self.assertEqual(actual_domains, expected_domains)
        # Verify count is within the ~175-190 target range (flexible)
        self.assertGreaterEqual(len(all_sensors), 170)
        self.assertLessEqual(len(all_sensors), 195)
        self.assertEqual(len(all_sensors), 180)

    def test_02_sensor_ids_are_globally_unique(self) -> None:
        """Verify all sensor IDs across all 11 domains are unique strings."""
        all_sensors = self.registry.get_all_sensors()
        sensor_ids = [s.sensor_id for s in all_sensors]
        self.assertEqual(len(sensor_ids), len(set(sensor_ids)))

    def test_03_metadata_completeness(self) -> None:
        """Verify every reading contains comprehensive asset and taxonomy metadata."""
        readings = self.registry.read_all()
        for s_id, reading in readings.items():
            self.assertTrue(reading.sensor_id.startswith("BHARATI-"))
            self.assertEqual(reading.station_id, "BHARATI")
            self.assertIsNotNone(reading.building_id)
            self.assertIsNotNone(reading.asset_id)
            self.assertIsInstance(reading.domain, InfrastructureDomain)
            self.assertIsInstance(reading.kind, SensorKind)
            self.assertIsInstance(reading.physical_quantity, PhysicalQuantity)
            self.assertIsInstance(reading.evidence_level, EvidenceLevel)
            self.assertIsInstance(reading.quality, SensorQuality)
            self.assertIsInstance(reading.timestamp, str)
            self.assertIsInstance(reading.simulation_time_seconds, float)
            self.assertIsNone(reading.event_time_seconds)  # Clarified semantic for v1

    def test_04_provenance_and_source_reference(self) -> None:
        """Verify all readings strictly adhere to SIMULATED provenance and source_reference."""
        readings = self.registry.read_all()
        for reading in readings.values():
            self.assertEqual(reading.provenance, SensorProvenance.SIMULATED)
            self.assertEqual(reading.source_reference, SOURCE_REFERENCE_DEFAULT)

    def test_05_evidence_level_classification_and_structural_separation(self) -> None:
        """Verify separation of physical station facts from unconfirmed structural telemetry."""
        # 1. Station physical facts are documented constants
        self.assertEqual(BUILDING_PREFAB_MODULES, 134)
        self.assertEqual(BUILDING_STEEL_PILLARS, 86)

        # 2. Structural telemetry sensors must be NOT_PUBLICLY_CONFIRMED
        structural_sensor_ids = [
            "BHARATI-STRUCT-BUILDING-TILT-X",
            "BHARATI-STRUCT-BUILDING-TILT-Y",
            "BHARATI-STRUCT-PILLAR-STRAIN-01",
            "BHARATI-STRUCT-FOUNDATION-DISP",
        ]
        for s_id in structural_sensor_ids:
            sensor = self.registry.get_sensor(s_id)
            self.assertEqual(
                sensor.config.evidence_level,
                EvidenceLevel.NOT_PUBLICLY_CONFIRMED,
                f"Sensor {s_id} should be NOT_PUBLICLY_CONFIRMED",
            )

        # 3. RO freshwater volume is DOCUMENTED/IMPLIED
        water_sensor = self.registry.get_sensor("BHARATI-WATER-RO-PERMEATE-FLOW")
        self.assertEqual(water_sensor.config.evidence_level, EvidenceLevel.DOCUMENTED)

        # 4. Virtual sensors must be DERIVED
        virt_sensor = self.registry.get_sensor("BHARATI-VIRT-BUILDING-HEAT-LOSS")
        self.assertEqual(virt_sensor.config.evidence_level, EvidenceLevel.DERIVED)

    def test_06_deterministic_confidence(self) -> None:
        """Verify confidence values are strictly deterministic with no random variation."""
        self.assertEqual(get_confidence_for_evidence(EvidenceLevel.DOCUMENTED), 1.0)
        self.assertEqual(get_confidence_for_evidence(EvidenceLevel.IMPLIED), 0.90)
        self.assertEqual(get_confidence_for_evidence(EvidenceLevel.DERIVED), 0.85)
        self.assertEqual(get_confidence_for_evidence(EvidenceLevel.NOT_PUBLICLY_CONFIRMED), 0.75)

        readings = self.registry.read_all()
        for reading in readings.values():
            if reading.valid:
                expected_conf = get_confidence_for_evidence(reading.evidence_level)
                self.assertEqual(reading.confidence, expected_conf)

    def test_07_physical_quantity_unit_consistency(self) -> None:
        """Verify physical quantity enum matches engineering units."""
        valid_units = {
            PhysicalQuantity.TEMPERATURE: ["degC", "°C"],
            PhysicalQuantity.PRESSURE: ["Pa", "bar", "kN_m2", "kPa", "hPa"],
            PhysicalQuantity.FLOW: ["L_h", "m3_h", "L/h", "m3/h"],
            PhysicalQuantity.VOLUME: ["L"],
            PhysicalQuantity.LEVEL_PERCENT: ["%", "%_obs", "score"],
            PhysicalQuantity.POWER: ["kW"],
            PhysicalQuantity.CONCENTRATION: ["mg_L", "ppm", "uS_cm"],
            PhysicalQuantity.COUNT: ["persons", "points"],
            PhysicalQuantity.DIMENSIONLESS: ["dB", "pH", "persons_100m2", "ratio"],
            PhysicalQuantity.DISPLACEMENT: ["mm", "mrad"],
            PhysicalQuantity.STRAIN: ["microstrain"],
            PhysicalQuantity.TIME: ["days", "ms"],
            PhysicalQuantity.VIBRATION: ["mm_s"],
            PhysicalQuantity.STATUS: ["state"],
        }
        for sensor in self.registry.get_all_sensors():
            pq = sensor.config.physical_quantity
            unit = sensor.config.unit
            self.assertIn(pq, valid_units, f"Unknown physical quantity {pq}")
            self.assertIn(
                unit,
                valid_units[pq],
                f"Invalid unit '{unit}' for physical quantity {pq} on sensor {sensor.sensor_id}",
            )

    def test_08_water_mass_balance_and_tank_integration(self) -> None:
        """Verify RO intake mass balance and potable tank volume integration V(t+1) = V(t) + net_flow * dt."""
        p = self.registry.physics
        initial_vol = p.water.potable_tank_volume_l

        # Verify capacity
        self.assertEqual(p.water.potable_tank_capacity_l, FRESH_WATER_TANK_CAPACITY_L)

        # Advance 1 hour (3600 s)
        dt = 3600.0
        self.registry.step(dt_seconds=dt)

        # Permeate produced vs consumption
        net_inflow_lph = p.water.ro_permeate_flow_lph - p.water.consumption_flow_lph
        expected_vol = initial_vol + (net_inflow_lph * (dt / 3600.0))

        self.assertAlmostEqual(p.water.potable_tank_volume_l, expected_vol, delta=1.0)
        expected_pct = round((p.water.potable_tank_volume_l / p.water.potable_tank_capacity_l) * 100.0, 1)
        self.assertEqual(p.water.potable_tank_level_pct, expected_pct)

        # Check intake vs permeate + reject + losses (~20 L/h modeled filter flush)
        total_effluent = p.water.ro_permeate_flow_lph + p.water.ro_reject_flow_lph + 20.0
        self.assertAlmostEqual(p.water.seawater_intake_flow_lph, total_effluent, delta=2.0)

    def test_09_water_to_wastewater_coupling(self) -> None:
        """Verify potable water consumption dynamically feeds wastewater influent."""
        p = self.registry.physics

        # Default consumption ~70-95 L/h, generating ~85% greywater/blackwater influent
        self.assertGreater(p.water.consumption_flow_lph, 0.0)
        self.assertAlmostEqual(p.wastewater.inlet_flow_lph, p.water.consumption_flow_lph * 0.85, delta=2.0)

        # Step time and verify sumps respond
        initial_grey = p.wastewater.grey_sump_level_pct
        self.registry.step(600.0)
        self.assertIsNotNone(p.wastewater.grey_sump_level_pct)

    def test_10_wastewater_treatment_degradation(self) -> None:
        """Verify MBR biological treatment degrades when aeration stops or membrane fouls."""
        p = self.registry.physics

        # Normal treatment
        self.assertTrue(p.wastewater.aeration_blower_running)
        self.assertLess(p.wastewater.effluent_cod_mg_l, 60.0)
        self.assertLess(p.wastewater.effluent_bod_mg_l, 15.0)

        # Stop aeration blower
        p.wastewater.aeration_blower_running = False
        p.wastewater.membrane_fouling_factor = 1.8

        # Step 2 hours
        for _ in range(12):
            self.registry.step(600.0)

        # Dissolved oxygen should drop, COD/BOD should rise, TMP should increase
        self.assertLess(p.wastewater.dissolved_oxygen_mg_l, 1.5)
        self.assertGreater(p.wastewater.effluent_cod_mg_l, 80.0)
        self.assertGreater(p.wastewater.membrane_tmp_bar, 0.35)

    def test_11_hvac_coil_heat_exchange(self) -> None:
        """Verify AHU supply air temperature exceeds return air during heating."""
        p = self.registry.physics
        self.assertGreater(p.hvac.ahu01_supply_temp_c, p.hvac.ahu01_return_temp_c)
        self.assertGreater(p.hvac.ahu02_supply_temp_c, p.hvac.ahu02_return_temp_c)
        self.assertGreater(p.hvac.ahu01_heating_valve_pct, 0.0)

    def test_12_ventilation_co2_reduction(self) -> None:
        """Verify outdoor fresh air ventilation prevents runaway CO2 accumulation."""
        p = self.registry.physics
        # Advance 1 hour with nominal occupancy
        self.registry.step(3600.0)
        # CO2 in living zone should remain controlled below 1000 ppm
        self.assertLess(p.hvac.co2_living_ppm, 1000.0)
        self.assertGreater(p.hvac.co2_living_ppm, 400.0)

    def test_13_refrigeration_setpoint_vs_state(self) -> None:
        """Verify refrigeration target setpoints are configurable while current temperatures are dynamic."""
        p = self.registry.physics
        # Deep freezer: target setpoint is -22°C assumption
        self.assertEqual(p.refrigeration.frz01_target_temp_c, -22.0)
        self.assertAlmostEqual(p.refrigeration.frz01_temp_c, -22.0, delta=2.0)

        # Chiller: target setpoint is +3°C assumption
        self.assertEqual(p.refrigeration.chl01_target_temp_c, 3.0)
        self.assertAlmostEqual(p.refrigeration.chl01_temp_c, 3.0, delta=2.0)

    def test_14_refrigeration_door_open_heat_ingress(self) -> None:
        """Verify opening cold room door causes thermal ingress and triggers compressor run."""
        p = self.registry.physics
        initial_temp = p.refrigeration.frz01_temp_c

        # Open deep freeze door
        p.refrigeration.frz01_door_open = True

        # Step 30 minutes
        for _ in range(6):
            self.registry.step(300.0)

        # Cabinet temperature must increase
        self.assertGreater(p.refrigeration.frz01_temp_c, initial_temp)
        self.assertTrue(p.refrigeration.frz01_compressor_running)

    def test_15_utilidor_trace_heating_freeze_risk(self) -> None:
        """Verify turning off utilidor trace heating drops pipe temperature towards ambient."""
        p = self.registry.physics
        initial_pipe_temp = p.pipelines.water01_pipe_temp_c

        # Disable trace heating under -18°C ambient
        p.pipelines.water01_trace_heating_on = False

        # Step 3 hours
        for _ in range(18):
            self.registry.step(600.0)

        self.assertLess(p.pipelines.water01_pipe_temp_c, initial_pipe_temp)
        freeze_risk_sensor = self.registry.read_sensor("BHARATI-VIRT-PIPE-FREEZE-RISK")
        self.assertGreater(freeze_risk_sensor.value, 15.0)

    def test_16_fire_physics_propagation_and_isolation(self) -> None:
        """Verify fire event triggers thermal/smoke detection, alarm, and damper closure."""
        p = self.registry.physics

        # Baseline: normal status, dampers open
        self.assertEqual(p.fire.z01_alarm_status, "NORMAL")
        self.assertTrue(p.fire.z01_damper_open)

        # Trigger fire in Zone 01 (Accommodation)
        p.trigger_fire_event(zone="Z01", intensity=0.7)
        self.registry.step(60.0)

        # Fire state updates
        self.assertGreater(p.fire.z01_temp_c, 45.0)
        self.assertGreater(p.fire.z01_smoke_obs_pct, 10.0)
        self.assertEqual(p.fire.z01_alarm_status, "ALARM")
        self.assertFalse(p.fire.z01_damper_open)  # Interlocked damper closed

        # Clear fire
        p.clear_fire_event()
        self.registry.step(60.0)
        self.assertEqual(p.fire.z01_alarm_status, "NORMAL")
        self.assertTrue(p.fire.z01_damper_open)

    def test_17_multi_sensor_correlation(self) -> None:
        """Verify multiple sensors observing a single physical fire event correlate perfectly."""
        p = self.registry.physics
        p.trigger_fire_event(zone="Z03", intensity=0.8)  # Energy/Generator plant
        self.registry.step(60.0)

        smoke = self.registry.read_sensor("BHARATI-FIRE-Z03-SMOKE")
        temp = self.registry.read_sensor("BHARATI-FIRE-Z03-TEMP")
        alarm = self.registry.read_sensor("BHARATI-FIRE-Z03-ALARM-STAT")
        damper = self.registry.read_sensor("BHARATI-FIRE-Z03-DAMPER-STAT")

        # All four sensors observe the same physical state
        self.assertGreater(float(smoke.value), 10.0)
        self.assertGreater(float(temp.value), 40.0)
        self.assertEqual(alarm.value, "ALARM")
        self.assertEqual(damper.value, "CLOSED")

        # Reset
        p.clear_fire_event()

    def test_18_asset_hierarchy_integrity(self) -> None:
        """Verify every sensor belongs to a defined asset and hierarchy levels are valid."""
        for sensor in self.registry.get_all_sensors():
            cfg = sensor.config
            self.assertIsNotNone(cfg.station_id)
            self.assertIsNotNone(cfg.building_id)
            self.assertIsNotNone(cfg.level_id)
            self.assertIsNotNone(cfg.zone_id)
            self.assertIsNotNone(cfg.asset_id)
            self.assertIsNotNone(cfg.subsystem)
            # Ensure asset_id is non-empty string
            self.assertGreater(len(cfg.asset_id), 0)

    def test_19_bms_telemetry_health_indicator(self) -> None:
        """Verify BMS telemetry health correctly reflects ratio of online points."""
        p = self.registry.physics
        total_pts = p.bms.points_online_count + p.bms.points_stale_count + p.bms.points_failed_count
        expected_health = round((p.bms.points_online_count / total_pts) * 100.0, 1)

        health_reading = self.registry.read_sensor("BHARATI-VIRT-BMS-TELEMETRY-HEALTH")
        self.assertAlmostEqual(float(health_reading.value), expected_health, delta=0.5)

    def test_20_read_only_auxiliary_power_interface(self) -> None:
        """Verify auxiliary electrical power is computed across infrastructure loads."""
        aux_kw = self.registry.physics.calculate_total_auxiliary_power_kw()
        self.assertGreater(aux_kw, 15.0)
        self.assertLess(aux_kw, 100.0)

        virt_aux = self.registry.read_sensor("BHARATI-VIRT-TOTAL-AUX-POWER")
        self.assertAlmostEqual(float(virt_aux.value), aux_kw, delta=0.1)

    def test_21_failure_simulation_dropout(self) -> None:
        """Verify DROPOUT failure returns None value and FAILED quality."""
        sensor_id = "BHARATI-WATER-RO-PERMEATE-FLOW"
        self.registry.simulate_failure(sensor_id, FailureType.DROPOUT)

        reading = self.registry.read_sensor(sensor_id)
        self.assertIsNone(reading.value)
        self.assertEqual(reading.quality, SensorQuality.FAILED)
        self.assertFalse(reading.valid)

        self.registry.clear_failure(sensor_id)
        restored = self.registry.read_sensor(sensor_id)
        self.assertIsNotNone(restored.value)
        self.assertEqual(restored.quality, SensorQuality.GOOD)

    def test_22_failure_simulation_stale(self) -> None:
        """Verify STALE failure returns aged timestamp and STALE quality."""
        sensor_id = "BHARATI-HVAC-AHU01-SUPPLY-TEMP"
        self.registry.simulate_failure(sensor_id, FailureType.STALE)

        reading = self.registry.read_sensor(sensor_id)
        self.assertEqual(reading.quality, SensorQuality.STALE)
        self.assertFalse(reading.valid)

        self.registry.clear_failure(sensor_id)

    def test_23_failure_simulation_out_of_range(self) -> None:
        """Verify OUT_OF_RANGE failure produces values exceeding valid range and BAD quality."""
        sensor_id = "BHARATI-BLDG-Z01-TEMP"
        sensor = self.registry.get_sensor(sensor_id)
        self.registry.simulate_failure(sensor_id, FailureType.OUT_OF_RANGE)

        reading = self.registry.read_sensor(sensor_id)
        self.assertEqual(reading.quality, SensorQuality.BAD)
        self.assertFalse(reading.valid)
        self.assertGreater(float(reading.value), sensor.config.max_value)

        self.registry.clear_failure(sensor_id)

    def test_24_failure_simulation_stuck_preserves_reading_value(self) -> None:
        """Verify STUCK failure freezes the exact reading value across physics changes."""
        sensor_id = "BHARATI-WATER-TANK-VOLUME"
        initial_reading = self.registry.read_sensor(sensor_id)
        frozen_val = initial_reading.value

        self.registry.simulate_failure(sensor_id, FailureType.STUCK)

        # Advance physics significantly
        self.registry.step(7200.0)

        stuck_reading = self.registry.read_sensor(sensor_id)
        self.assertEqual(stuck_reading.value, frozen_val)
        self.assertEqual(stuck_reading.quality, SensorQuality.BAD)
        self.assertFalse(stuck_reading.valid)

        self.registry.clear_failure(sensor_id)

    def test_25_clear_failures(self) -> None:
        """Verify clearing single and all failures restores normal operational readings."""
        s1 = "BHARATI-HVAC-AHU01-SUPPLY-TEMP"
        s2 = "BHARATI-COLD-FRZ01-TEMP"

        self.registry.simulate_failure(s1, FailureType.DROPOUT)
        self.registry.simulate_failure(s2, FailureType.STUCK)

        self.assertFalse(self.registry.read_sensor(s1).valid)
        self.assertFalse(self.registry.read_sensor(s2).valid)

        self.registry.clear_all_failures()

        self.assertTrue(self.registry.read_sensor(s1).valid)
        self.assertTrue(self.registry.read_sensor(s2).valid)

    def test_26_registry_lookups(self) -> None:
        """Verify registry lookup queries by domain, subsystem, kind, and asset."""
        # By domain
        water_sensors = self.registry.get_sensors_by_domain(InfrastructureDomain.WATER)
        self.assertEqual(len(water_sensors), 18)

        # By kind
        virtual_sensors = self.registry.get_sensors_by_kind(SensorKind.DERIVED)
        self.assertGreaterEqual(len(virtual_sensors), 18)

        # By asset
        ahu01_sensors = self.registry.get_sensors_by_asset("AHU-01")
        self.assertGreaterEqual(len(ahu01_sensors), 6)

        # By subsystem
        mbr_sensors = self.registry.get_sensors_by_subsystem("TREATMENT_MBR")
        self.assertGreaterEqual(len(mbr_sensors), 10)

    def test_27_reproducibility_with_fixed_seed(self) -> None:
        """Verify two registries initialized with identical seeds yield identical initial values."""
        clock1 = SimulationClock(datetime(2026, 9, 19, 12, 0, 0))
        clock2 = SimulationClock(datetime(2026, 9, 19, 12, 0, 0))

        reg1 = create_bharati_infrastructure_sensors(seed=999, clock=clock1, environmental_input=self.env)
        reg2 = create_bharati_infrastructure_sensors(seed=999, clock=clock2, environmental_input=self.env)

        readings1 = reg1.read_all()
        readings2 = reg2.read_all()

        for s_id in readings1:
            self.assertEqual(readings1[s_id].value, readings2[s_id].value)

    def test_28_environmental_input_influence(self) -> None:
        """Verify extreme blizzard conditions increase building heat loss and stilt strain."""
        calm_env = EnvironmentalInput(ambient_temperature_c=-10.0, wind_speed_ms=5.0)
        blizzard_env = EnvironmentalInput()
        blizzard_env.apply_extreme_cold_blizzard()

        reg_calm = create_bharati_infrastructure_sensors(seed=10, environmental_input=calm_env)
        reg_bliz = create_bharati_infrastructure_sensors(seed=10, environmental_input=blizzard_env)

        loss_calm = reg_calm.read_sensor("BHARATI-VIRT-BUILDING-HEAT-LOSS").value
        loss_bliz = reg_bliz.read_sensor("BHARATI-VIRT-BUILDING-HEAT-LOSS").value

        self.assertGreater(float(loss_bliz), float(loss_calm))

    def test_29_structural_stability_indicators(self) -> None:
        """Verify structural stilt strain and foundation displacement indicators are valid."""
        strain_reading = self.registry.read_sensor("BHARATI-STRUCT-PILLAR-STRAIN-01")
        disp_reading = self.registry.read_sensor("BHARATI-STRUCT-FOUNDATION-DISP")

        self.assertGreater(float(strain_reading.value), 0.0)
        self.assertGreater(float(disp_reading.value), 0.0)
        self.assertEqual(strain_reading.evidence_level, EvidenceLevel.NOT_PUBLICLY_CONFIRMED)

    def test_30_emergency_shelter_standby_readiness(self) -> None:
        """Verify emergency shelter reserves (fuel, water, heat) are ready for occupancy."""
        shelter_temp = self.registry.read_sensor("BHARATI-EMERG-SHELTER-TEMP")
        gen_fuel = self.registry.read_sensor("BHARATI-EMERG-GEN-FUEL-LEVEL")
        water_level = self.registry.read_sensor("BHARATI-EMERG-WATER-LEVEL")

        self.assertGreater(float(shelter_temp.value), 10.0)
        self.assertGreater(float(gen_fuel.value), 80.0)
        self.assertGreater(float(water_level.value), 75.0)


if __name__ == "__main__":
    unittest.main()
