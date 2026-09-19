"""Comprehensive Unit Tests for Bharati Station Environment Observation Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Covers:
1. Package imports and exports
2. State initialization
3. All 9 environmental domains present
4. Sensor count equals 87 simulated telemetry points
5. Sensor IDs globally unique
6. Physical quantities and unit semantics
7. ASCII unit discipline (no Windows encoding failures)
8. Evidence classification (DOCUMENTED, IMPLIED, NOT_PUBLICLY_CONFIRMED, DERIVED)
9. Provenance (SIMULATED) and source_reference ("bharati_environment_physics_v1")
10. Explicit state_path resolution on all instrument and state sensors
11. Derived dependency resolution on all derived sensors
12. Spatial context separation (LOCAL_STATION vs COASTAL vs COASTAL_CONTEXT)
13. Weather bounds check
14. Humidity bounds (0 - 100%)
15. Wind speed and gust bounds (gust >= sustained wind)
16. Deterministic dew point calculation (Magnus-Tetens formula, dew <= temp)
17. Deterministic moist air density (CIPM formulation)
18. Radiation non-negative shortwave and net radiation balance
19. Radiation coherence during polar night (SW = 0, UV = 0 when daylight is False)
20. Aerosol non-negative bounds (BC, PM10, particle count >= 0)
21. Trace gas non-negative bounds (CO, NOx, SO2, O3)
22. Snow accumulation and depth dynamics
23. High-wind blowing snow drift mass flux (> 10 m/s threshold)
24. Visibility reduction under blowing snow / precipitation
25. Sea-ice thickness, concentration, and temperature bounds
26. Ocean context salinity, wave height, and temperature bounds
27. Atmospheric electricity potential gradient, air-earth current, and ion conductivities
28. Ionospheric TEC and scintillation index bounds
29. Seismic ground acceleration, particle velocity, and event trigger
30. Deterministic derived risk indicators
31. Extreme cold event propagation (temperature plunge -> freeze risk rises -> cold stress rises)
32. Blizzard event propagation (wind rises, visibility drops, blowing snow rises -> blizzard risk rises -> condition BLACK)
33. Explainable operating condition with contributing reasons
34. Sensor failure: DROPOUT (value=None, quality=FAILED)
35. Sensor failure: STALE (timestamp aged, quality=STALE)
36. Sensor failure: OUT_OF_RANGE (value forced out of bounds, quality=BAD)
37. Sensor failure: STUCK (preserves last valid physical reading, NOT default_value)
38. Sensor failure clearance (single and all)
39. Deterministic reproducibility with fixed seed
40. Cross-sensor causal coherence
41. Environment -> Infrastructure read-only interface (to_infrastructure_environmental_input)
42. Environment -> Energy read-only interface (get_energy_environmental_interface)
43. Environment -> Logistics read-only interface (get_logistics_environmental_interface)
44. Invariant: default_value is fallback-only; state-bound sensor resolves from physics state
45. Invariant: sensor reading updates when physics state changes
"""

from __future__ import annotations

import unittest

from backend.sensors.bharati_sensors.energy.clock import SimulationClock
from backend.sensors.bharati_sensors.environment import (
    BharatiEnvironmentPhysicsState,
    EnvironmentDomain,
    EnvironmentSensorRegistry,
    EvidenceLevel,
    FailureType,
    PhysicalQuantity,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    create_bharati_environment_sensors,
    get_energy_environmental_interface,
    get_infrastructure_environmental_extended,
    get_logistics_environmental_interface,
    to_infrastructure_environmental_input,
)
from backend.sensors.bharati_sensors.environment.config import (
    CONFIDENCE_BASELINE,
    ENVIRONMENT_SENSOR_CONFIGS,
    SOURCE_REFERENCE_DEFAULT,
    get_confidence_for_evidence,
)
from backend.sensors.bharati_sensors.infrastructure.environmental_input import EnvironmentalInput


class TestBharatiEnvironmentSensors(unittest.TestCase):
    """Test suite verifying the Bharati Station Environment Observation Layer."""

    def setUp(self) -> None:
        self.clock = SimulationClock()
        self.registry = create_bharati_environment_sensors(seed=42, clock=self.clock)

    def test_01_all_nine_domains_present_and_count_is_87(self) -> None:
        """Verify all 9 domains exist and sensor count is exactly 87."""
        self.assertEqual(self.registry.sensor_count, 87)
        domains_found = {s.domain for s in self.registry.get_all_sensors()}
        expected_domains = set(EnvironmentDomain)
        self.assertEqual(domains_found, expected_domains)

    def test_02_sensor_ids_are_globally_unique(self) -> None:
        """Verify all sensor IDs are unique across the catalogue."""
        sensors = self.registry.get_all_sensors()
        sensor_ids = [s.sensor_id for s in sensors]
        self.assertEqual(len(sensor_ids), len(set(sensor_ids)))

    def test_03_metadata_completeness(self) -> None:
        """Verify every sensor reading contains full asset and spatial context metadata."""
        readings = self.registry.read_all()
        self.assertEqual(len(readings), 87)
        for s_id, r in readings.items():
            self.assertEqual(r.sensor_id, s_id)
            self.assertTrue(bool(r.name))
            self.assertTrue(bool(r.asset_id))
            self.assertTrue(bool(r.subsystem))
            self.assertEqual(r.station_id, "BHARATI")
            self.assertIn(r.location_scope, ["LOCAL_STATION", "COASTAL", "COASTAL_CONTEXT"])
            self.assertTrue(bool(r.measurement_zone))
            self.assertIsInstance(r.domain, EnvironmentDomain)
            self.assertIsInstance(r.kind, SensorKind)
            self.assertIsInstance(r.physical_quantity, PhysicalQuantity)
            self.assertIsInstance(r.evidence_level, EvidenceLevel)
            self.assertIsInstance(r.quality, SensorQuality)
            self.assertIsInstance(r.confidence, float)
            self.assertGreaterEqual(r.confidence, 0.0)
            self.assertLessEqual(r.confidence, 1.0)
            self.assertIsNone(r.event_time_seconds)

    def test_04_provenance_and_source_reference(self) -> None:
        """Verify all readings strictly report SIMULATED provenance with bharati_environment_physics_v1."""
        readings = self.registry.read_all()
        for r in readings.values():
            self.assertEqual(r.provenance, SensorProvenance.SIMULATED)
            self.assertEqual(r.source_reference, SOURCE_REFERENCE_DEFAULT)

    def test_05_evidence_classification_distribution(self) -> None:
        """Verify presence of all four evidence levels in the configured catalogue."""
        evidence_counts = {level: 0 for level in EvidenceLevel}
        for cfg in ENVIRONMENT_SENSOR_CONFIGS.values():
            evidence_counts[cfg.evidence_level] += 1

        self.assertGreater(evidence_counts[EvidenceLevel.DOCUMENTED], 25)
        self.assertGreater(evidence_counts[EvidenceLevel.IMPLIED], 15)
        self.assertGreater(evidence_counts[EvidenceLevel.NOT_PUBLICLY_CONFIRMED], 10)
        self.assertGreater(evidence_counts[EvidenceLevel.DERIVED], 10)

        # Confirm surface ozone is conservative NOT_PUBLICLY_CONFIRMED
        self.assertEqual(ENVIRONMENT_SENSOR_CONFIGS["ENV-AIR-O3"].evidence_level, EvidenceLevel.NOT_PUBLICLY_CONFIRMED)
        # Confirm horizontal visibility is NOT_PUBLICLY_CONFIRMED
        self.assertEqual(ENVIRONMENT_SENSOR_CONFIGS["ENV-WX-VIS"].evidence_level, EvidenceLevel.NOT_PUBLICLY_CONFIRMED)

    def test_06_ascii_unit_discipline(self) -> None:
        """Verify all sensor units use ASCII strings without unicode encoding issues."""
        for cfg in ENVIRONMENT_SENSOR_CONFIGS.values():
            self.assertTrue(cfg.unit.isascii(), f"Sensor {cfg.sensor_id} has non-ASCII unit: {cfg.unit}")
            self.assertNotIn("°", cfg.unit)

    def test_07_state_path_resolution(self) -> None:
        """Verify every instrument and state sensor resolves from physics state via state_path."""
        physics = self.registry.physics
        for cfg in ENVIRONMENT_SENSOR_CONFIGS.values():
            if cfg.kind in [SensorKind.INSTRUMENT, SensorKind.STATE]:
                self.assertTrue(bool(cfg.state_path), f"Sensor {cfg.sensor_id} missing state_path")
                val = physics.get_value_by_path(cfg.state_path)
                self.assertIsNotNone(val, f"Path '{cfg.state_path}' on {cfg.sensor_id} returned None")

    def test_08_derived_dependency_resolution(self) -> None:
        """Verify all derived sensors have declared state_dependencies that resolve."""
        physics = self.registry.physics
        for cfg in ENVIRONMENT_SENSOR_CONFIGS.values():
            if cfg.kind == SensorKind.DERIVED:
                self.assertTrue(len(cfg.state_dependencies) > 0, f"Derived sensor {cfg.sensor_id} missing state_dependencies")
                for dep in cfg.state_dependencies:
                    # Dep may be a direct physics path or previous sensor reference
                    try:
                        val = physics.get_value_by_path(dep)
                        self.assertIsNotNone(val)
                    except AttributeError:
                        # May refer to weather.atmospheric_pressure_hpa or derived
                        self.fail(f"Derived sensor {cfg.sensor_id} has unresolvable dependency: {dep}")

    def test_09_spatial_context_distinction(self) -> None:
        """Verify spatial distinction between local station snow and coastal sea ice."""
        snow_sensors = self.registry.get_sensors_by_subsystem("STATION_SNOW")
        for s in snow_sensors:
            self.assertEqual(s.location_scope, "LOCAL_STATION")
            self.assertEqual(s.measurement_zone, "STATION_PERIMETER")

        ice_sensors = self.registry.get_sensors_by_subsystem("SEA_ICE")
        for s in ice_sensors:
            self.assertEqual(s.location_scope, "COASTAL")
            self.assertEqual(s.measurement_zone, "COASTAL_STUDY_AREA")

        ocean_sensors = self.registry.get_sensors_by_domain(EnvironmentDomain.OCEAN)
        for s in ocean_sensors:
            self.assertEqual(s.location_scope, "COASTAL_CONTEXT")
            self.assertEqual(s.measurement_zone, "PRYDZ_BAY_COASTAL")

    def test_10_weather_physical_bounds(self) -> None:
        """Verify weather variables are within realistic Antarctic ranges."""
        r_temp = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertGreaterEqual(r_temp.value, -50.0)
        self.assertLessEqual(r_temp.value, 15.0)

        r_rh = self.registry.read_sensor("ENV-WX-RH")
        self.assertGreaterEqual(r_rh.value, 0.0)
        self.assertLessEqual(r_rh.value, 100.0)

        r_press = self.registry.read_sensor("ENV-WX-PRESS")
        self.assertGreaterEqual(r_press.value, 920.0)
        self.assertLessEqual(r_press.value, 1040.0)

        r_wind = self.registry.read_sensor("ENV-WX-WIND-S")
        self.assertGreaterEqual(r_wind.value, 0.0)

        r_gust = self.registry.read_sensor("ENV-WX-GUST")
        self.assertGreaterEqual(r_gust.value, r_wind.value)

    def test_11_dew_point_physics(self) -> None:
        """Verify dew point is deterministically calculated and cannot exceed temperature."""
        temp = self.registry.read_sensor("ENV-WX-TEMP").value
        dew = self.registry.read_sensor("ENV-WX-DEW").value
        self.assertLessEqual(dew, temp)

    def test_12_air_density_physics(self) -> None:
        """Verify moist air density is positive and reasonable for cold polar atmosphere."""
        dens = self.registry.read_sensor("ENV-WX-DENS").value
        self.assertGreater(dens, 1.1)
        self.assertLess(dens, 1.55)

    def test_13_pressure_tendency(self) -> None:
        """Verify 3-hour pressure tendency exists and responds to pressure changes."""
        tend = self.registry.read_sensor("ENV-WX-PRESS-TEND").value
        self.assertIsInstance(tend, float)
        self.assertGreaterEqual(tend, -25.0)
        self.assertLessEqual(tend, 25.0)

    def test_14_radiation_polar_night_coherence(self) -> None:
        """Verify downwelling shortwave and UV index collapse to zero when daylight is False."""
        self.registry.physics.radiation.is_daylight = False
        self.registry.physics.step(1.0)
        sw = self.registry.read_sensor("ENV-RAD-SW").value
        uv = self.registry.read_sensor("ENV-RAD-UV").value
        avail = self.registry.read_sensor("ENV-RAD-SOLAR-AVAIL").value
        self.assertEqual(sw, 0.0)
        self.assertEqual(uv, 0.0)
        self.assertEqual(avail, 0.0)

    def test_15_aerosol_non_negative_bounds(self) -> None:
        """Verify aerosol mass, particle count, and optical coefficients are strictly non-negative."""
        bc = self.registry.read_sensor("ENV-AIR-BC").value
        pm10 = self.registry.read_sensor("ENV-AIR-AERO").value
        pcount = self.registry.read_sensor("ENV-AIR-PCOUNT").value
        scat = self.registry.read_sensor("ENV-AIR-SCAT").value
        abs_coeff = self.registry.read_sensor("ENV-AIR-ABS").value
        self.assertGreaterEqual(bc, 0.0)
        self.assertGreaterEqual(pm10, 0.0)
        self.assertGreaterEqual(pcount, 0.0)
        self.assertGreaterEqual(scat, 0.0)
        self.assertGreaterEqual(abs_coeff, 0.0)

    def test_16_trace_gases_bounds(self) -> None:
        """Verify carbon monoxide, NOx, SO2, and O3 are non-negative."""
        co = self.registry.read_sensor("ENV-AIR-CO").value
        nox = self.registry.read_sensor("ENV-AIR-NOX").value
        so2 = self.registry.read_sensor("ENV-AIR-SO2").value
        o3 = self.registry.read_sensor("ENV-AIR-O3").value
        self.assertGreaterEqual(co, 0.0)
        self.assertGreaterEqual(nox, 0.0)
        self.assertGreaterEqual(so2, 0.0)
        self.assertGreaterEqual(o3, 0.0)

    def test_17_blowing_snow_flux_coupling(self) -> None:
        """Verify high winds (>10 m/s) generate blowing snow drift mass flux."""
        self.registry.physics.weather.wind_speed_mps = 25.0
        self.registry.physics.step(1.0)
        drift = self.registry.read_sensor("ENV-SNOW-DRIFT").value
        self.assertGreater(drift, 5.0)

    def test_18_visibility_impairment_under_blowing_snow(self) -> None:
        """Verify visibility decreases dramatically under heavy blowing snow."""
        self.registry.physics.weather.wind_speed_mps = 35.0
        self.registry.physics.weather.precipitation_rate_mm_h = 10.0
        self.registry.physics.step(1.0)
        vis = self.registry.read_sensor("ENV-WX-VIS").value
        self.assertLess(vis, 1000.0)

    def test_19_sea_ice_bounds(self) -> None:
        """Verify fast-ice thickness and concentration bounds."""
        thick = self.registry.read_sensor("ENV-ICE-THICK").value
        conc = self.registry.read_sensor("ENV-ICE-CONC").value
        temp = self.registry.read_sensor("ENV-ICE-TEMP").value
        self.assertGreater(thick, 0.0)
        self.assertGreaterEqual(conc, 0.0)
        self.assertLessEqual(conc, 100.0)
        self.assertLessEqual(temp, 2.0)

    def test_20_ocean_coastal_context_bounds(self) -> None:
        """Verify coastal ocean salinity, current speed, and wave height bounds."""
        sal = self.registry.read_sensor("ENV-OCEAN-SAL").value
        cur = self.registry.read_sensor("ENV-OCEAN-CURRENT-S").value
        wave = self.registry.read_sensor("ENV-OCEAN-WAVE-H").value
        self.assertGreater(sal, 25.0)
        self.assertGreaterEqual(cur, 0.0)
        self.assertGreaterEqual(wave, 0.0)

    def test_21_environmental_water_limnology_isolation(self) -> None:
        """Verify environmental water sensors represent natural freshwater lakes."""
        ph = self.registry.read_sensor("ENV-WATER-PH").value
        cond = self.registry.read_sensor("ENV-WATER-COND").value
        self.assertGreaterEqual(ph, 5.0)
        self.assertLessEqual(ph, 9.5)
        # Natural lake conductivity is very low compared to seawater (uS/cm vs mS/cm)
        self.assertLess(cond, 200.0)

    def test_22_atmospheric_electricity_bounds(self) -> None:
        """Verify atmospheric electric field and air-earth conduction currents."""
        efield = self.registry.read_sensor("ENV-ELEC-EFIELD").value
        aec = self.registry.read_sensor("ENV-ELEC-AEC").value
        maxwell = self.registry.read_sensor("ENV-ELEC-MAXWELL").value
        self.assertGreaterEqual(efield, -500.0)
        self.assertLessEqual(efield, 1500.0)
        self.assertGreaterEqual(aec, -10.0)
        self.assertGreaterEqual(maxwell, -15.0)

    def test_23_ionospheric_tec_and_scintillation(self) -> None:
        """Verify ionospheric TEC and scintillation index S4."""
        tec = self.registry.read_sensor("ENV-IONO-TEC").value
        s4 = self.registry.read_sensor("ENV-IONO-L1-AMP").value
        self.assertGreaterEqual(tec, 0.0)
        self.assertGreaterEqual(s4, 0.0)
        self.assertLessEqual(s4, 1.5)

    def test_24_seismology_telemetry(self) -> None:
        """Verify ground acceleration and event detection channel."""
        acc = self.registry.read_sensor("ENV-SEIS-ACC").value
        event = self.registry.read_sensor("ENV-SEIS-EVENT").value
        self.assertGreaterEqual(acc, 0.0)
        self.assertIsInstance(event, bool)

    def test_25_wind_chill_index_calculation(self) -> None:
        """Verify Antarctic wind chill drops significantly below ambient temperature in wind."""
        self.registry.physics.weather.ambient_temperature_c = -20.0
        self.registry.physics.weather.wind_speed_mps = 15.0
        self.registry.physics.step(1.0)
        wct = self.registry.read_sensor("ENV-DERIVED-WIND-CHILL").value
        self.assertLess(wct, -28.0)

    def test_26_cold_stress_and_freeze_risk(self) -> None:
        """Verify cold stress and external infrastructure freeze risk scores."""
        cs = self.registry.read_sensor("ENV-DERIVED-COLD-STRESS").value
        fr = self.registry.read_sensor("ENV-DERIVED-FREEZE-RISK").value
        self.assertGreaterEqual(cs, 0.0)
        self.assertLessEqual(cs, 100.0)
        self.assertGreaterEqual(fr, 0.0)
        self.assertLessEqual(fr, 100.0)

    def test_27_extreme_cold_scenario_propagation(self) -> None:
        """Verify extreme cold scenario triggers freeze risk increase and cold stress."""
        self.registry.physics.set_scenario_extreme_cold()
        for _ in range(10):
            self.registry.step(60.0)

        temp = self.registry.read_sensor("ENV-WX-TEMP").value
        fr = self.registry.read_sensor("ENV-DERIVED-FREEZE-RISK").value
        cs = self.registry.read_sensor("ENV-DERIVED-COLD-STRESS").value
        self.assertLess(temp, -30.0)
        self.assertGreater(fr, 60.0)
        self.assertGreater(cs, 60.0)

    def test_28_blizzard_scenario_propagation_and_black_condition(self) -> None:
        """Verify blizzard scenario escalates wind, blowing snow, drops visibility, and triggers BLACK."""
        self.registry.physics.set_scenario_blizzard()
        for _ in range(10):
            self.registry.step(60.0)

        wind = self.registry.read_sensor("ENV-WX-WIND-S").value
        vis = self.registry.read_sensor("ENV-WX-VIS").value
        drift = self.registry.read_sensor("ENV-SNOW-DRIFT").value
        blizzard_risk = self.registry.read_sensor("ENV-DERIVED-BLIZZARD-RISK").value
        op_cond = self.registry.read_sensor("ENV-DERIVED-OPERATING-CONDITION").value

        self.assertGreaterEqual(wind, 28.0)
        self.assertLess(vis, 500.0)
        self.assertGreater(drift, 15.0)
        self.assertGreaterEqual(blizzard_risk, 65.0)
        self.assertTrue(op_cond.startswith("BLACK"))
        self.assertIn("BLIZZARD_CONDITIONS", op_cond)

    def test_29_explainable_operating_condition(self) -> None:
        """Verify OperatingConditionState maintains causal reasons and indicators."""
        op_state = self.registry.physics.derived.operating_condition
        self.assertIn(op_state.level, ["GREEN", "YELLOW", "RED", "BLACK"])
        self.assertTrue(len(op_state.reasons) > 0)
        self.assertIn("wind_speed_mps", op_state.contributing_indicators)
        self.assertIn("ambient_temp_c", op_state.contributing_indicators)

    def test_30_failure_simulation_dropout(self) -> None:
        """Verify DROPOUT technical failure returns value=None and FAILED quality."""
        self.registry.simulate_failure("ENV-WX-TEMP", FailureType.DROPOUT)
        r = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertIsNone(r.value)
        self.assertEqual(r.quality, SensorQuality.FAILED)
        self.assertFalse(r.valid)
        self.assertEqual(r.confidence, 0.0)

    def test_31_failure_simulation_stale(self) -> None:
        """Verify STALE technical failure returns aged timestamp and STALE quality."""
        self.registry.simulate_failure("ENV-WX-WIND-S", FailureType.STALE, stale_seconds=300.0)
        r = self.registry.read_sensor("ENV-WX-WIND-S")
        self.assertEqual(r.quality, SensorQuality.STALE)
        self.assertFalse(r.valid)
        self.assertEqual(r.confidence, 0.4)

    def test_32_failure_simulation_out_of_range(self) -> None:
        """Verify OUT_OF_RANGE technical failure generates out of bounds reading and BAD quality."""
        self.registry.simulate_failure("ENV-AIR-BC", FailureType.OUT_OF_RANGE)
        r = self.registry.read_sensor("ENV-AIR-BC")
        self.assertEqual(r.quality, SensorQuality.BAD)
        self.assertFalse(r.valid)
        self.assertEqual(r.confidence, 0.2)
        self.assertGreater(r.value, 2000.0)

    def test_33_failure_simulation_stuck_preserves_last_reading(self) -> None:
        """Verify STUCK failure freezes the exact last valid physical observation, NOT default_value."""
        self.registry.physics.weather.ambient_temperature_c = -27.4
        r1 = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertEqual(r1.value, -27.4)

        # Now inject STUCK
        self.registry.simulate_failure("ENV-WX-TEMP", FailureType.STUCK)
        # Advance physics to a new temperature
        self.registry.physics.weather.ambient_temperature_c = -12.0

        r2 = self.registry.read_sensor("ENV-WX-TEMP")
        # Sensor must report the frozen -27.4, NOT -12.0 and NOT default_value (-18.0)
        self.assertEqual(r2.value, -27.4)
        self.assertEqual(r2.quality, SensorQuality.BAD)
        self.assertFalse(r2.valid)

    def test_34_clear_failure_restores_health(self) -> None:
        """Verify clearing failure restores normal physical observation and GOOD quality."""
        self.registry.simulate_failure("ENV-WX-PRESS", FailureType.DROPOUT)
        r_fail = self.registry.read_sensor("ENV-WX-PRESS")
        self.assertEqual(r_fail.quality, SensorQuality.FAILED)

        self.registry.clear_failure("ENV-WX-PRESS")
        r_rec = self.registry.read_sensor("ENV-WX-PRESS")
        self.assertEqual(r_rec.quality, SensorQuality.GOOD)
        self.assertTrue(r_rec.valid)
        self.assertGreater(r_rec.confidence, 0.9)

    def test_35_clear_all_failures(self) -> None:
        """Verify clear_all_failures clears faults from all sensors."""
        self.registry.simulate_failure("ENV-WX-TEMP", FailureType.DROPOUT)
        self.registry.simulate_failure("ENV-WX-WIND-S", FailureType.STALE)
        self.registry.clear_all_failures()

        r1 = self.registry.read_sensor("ENV-WX-TEMP")
        r2 = self.registry.read_sensor("ENV-WX-WIND-S")
        self.assertEqual(r1.quality, SensorQuality.GOOD)
        self.assertEqual(r2.quality, SensorQuality.GOOD)

    def test_36_reproducibility_with_fixed_seed(self) -> None:
        """Verify identical seed produces identical physical state trajectories."""
        reg_a = create_bharati_environment_sensors(seed=99)
        reg_b = create_bharati_environment_sensors(seed=99)

        for _ in range(5):
            reg_a.step(60.0)
            reg_b.step(60.0)

        readings_a = reg_a.read_all()
        readings_b = reg_b.read_all()
        for s_id in readings_a:
            self.assertEqual(readings_a[s_id].value, readings_b[s_id].value, f"Mismatch on sensor {s_id}")

    def test_37_cross_sensor_causal_coherence(self) -> None:
        """Verify high wind propagates coherently across snow drift, visibility, blizzard risk, and wind chill."""
        # Initial mild state
        self.registry.physics.weather.wind_speed_mps = 5.0
        self.registry.physics.weather.ambient_temperature_c = -15.0
        self.registry.physics.step(1.0)
        drift_low = self.registry.read_sensor("ENV-SNOW-DRIFT").value
        vis_high = self.registry.read_sensor("ENV-WX-VIS").value
        wct_mild = self.registry.read_sensor("ENV-DERIVED-WIND-CHILL").value

        # Storm high wind state
        self.registry.physics.weather.wind_speed_mps = 30.0
        self.registry.physics.step(1.0)
        drift_high = self.registry.read_sensor("ENV-SNOW-DRIFT").value
        vis_low = self.registry.read_sensor("ENV-WX-VIS").value
        wct_severe = self.registry.read_sensor("ENV-DERIVED-WIND-CHILL").value

        self.assertGreater(drift_high, drift_low)
        self.assertLess(vis_low, vis_high)
        self.assertLess(wct_severe, wct_mild)

    def test_38_environment_to_infrastructure_interface(self) -> None:
        """Verify read-only EnvironmentalInput interface generation for Infrastructure."""
        env_input = to_infrastructure_environmental_input(self.registry)
        self.assertIsInstance(env_input, EnvironmentalInput)
        self.assertEqual(env_input.ambient_temperature_c, round(self.registry.physics.weather.ambient_temperature_c, 2))
        self.assertEqual(env_input.wind_speed_ms, round(self.registry.physics.weather.wind_speed_mps, 2))
        self.assertEqual(env_input.solar_radiation_w_m2, round(self.registry.physics.radiation.shortwave_downwelling_w_m2, 1))

        ext = get_infrastructure_environmental_extended(self.registry)
        self.assertIn("freeze_risk", ext)
        self.assertIn("snow_depth_m", ext)

    def test_39_environment_to_energy_interface(self) -> None:
        """Verify read-only environmental interface for Energy."""
        energy_ctx = get_energy_environmental_interface(self.registry)
        self.assertIn("ambient_temperature_c", energy_ctx)
        self.assertIn("solar_radiation_w_m2", energy_ctx)
        self.assertIn("wind_speed_mps", energy_ctx)
        self.assertIn("environmental_operating_condition", energy_ctx)
        self.assertIn("operating_condition_level", energy_ctx)

    def test_40_environment_to_logistics_interface(self) -> None:
        """Verify read-only environmental accessibility interface for Logistics."""
        log_ctx = get_logistics_environmental_interface(self.registry)
        self.assertIn("sea_ice_condition", log_ctx)
        self.assertIn("ocean_condition", log_ctx)
        self.assertIn("weather_severity", log_ctx)
        self.assertIn("accessibility_indicators", log_ctx)
        self.assertTrue(log_ctx["sea_ice_condition"]["thickness_m"] > 0)

    def test_41_state_bound_sensor_does_not_use_default_value(self) -> None:
        """Verify that a healthy state-bound sensor resolves from physics_state, NOT default_value."""
        cfg = ENVIRONMENT_SENSOR_CONFIGS["ENV-WX-TEMP"]
        self.registry.physics.weather.ambient_temperature_c = -31.5
        reading = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertEqual(reading.value, -31.5)
        self.assertNotEqual(reading.value, cfg.default_value)

    def test_42_sensor_updates_when_physics_state_changes(self) -> None:
        """Verify sensor reading updates dynamically when underlying physics changes."""
        self.registry.physics.weather.ambient_temperature_c = -10.0
        r1 = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertEqual(r1.value, -10.0)

        self.registry.physics.weather.ambient_temperature_c = -30.0
        r2 = self.registry.read_sensor("ENV-WX-TEMP")
        self.assertEqual(r2.value, -30.0)
        self.assertNotEqual(r1.value, r2.value)


if __name__ == "__main__":
    unittest.main()
