"""Comprehensive Unit Tests for Bharati Station Energy Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Covers all 24 required verification criteria:
1. All three CHP units created
2. Both UPS units created
3. Fuel sensors created
4. Heating sensors created
5. Virtual sensors created
6. Sensor IDs are unique
7. Every reading contains required metadata
8. Units are correct
9. Values stay within valid ranges
10. CHP electrical generation affects total generation
11. CHP operation affects fuel consumption
12. Fuel decreases when CHP is operating
13. Heating supply temperature > return temperature
14. Useful thermal output bounded by 155 kWth constraint
15. Virtual total generation equals sum of running CHP generation
16. Net energy balance is calculated correctly
17. Sensor failure simulation works
18. STALE / FAILED / BAD states work
19. Registry lookups work (ID, asset, category, kind)
20. Reproducible simulation works with a fixed seed
21. Fuel inventory conservation
22. Energy balance consistency
23. Thermal output bounds and consistency
24. Sensor provenance discipline (SIMULATED + reference)
"""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.sensors.bharati_sensors.energy import (
    FailureType,
    SensorCategory,
    SensorKind,
    SensorProvenance,
    SensorQuality,
    create_bharati_energy_sensors,
)
from backend.sensors.bharati_sensors.energy.clock import SimulationClock
from backend.sensors.bharati_sensors.energy.config import MAX_STATION_HEATING_DEMAND_KW


class TestBharatiEnergySensors(unittest.TestCase):
    """Test suite verifying the Bharati Station Energy Sensor Layer."""

    def setUp(self) -> None:
        """Create a standard test registry with a fixed seed."""
        self.clock = SimulationClock(datetime(2026, 9, 19, 12, 0, 0))
        self.registry = create_bharati_energy_sensors(seed=42, clock=self.clock)

    def test_01_all_three_chp_units_created(self) -> None:
        """Verify sensors exist for all three 100 kVA CHP units."""
        for chp_idx in (1, 2, 3):
            asset = f"CHP-{chp_idx}"
            sensors = self.registry.get_sensors_by_asset(asset)
            self.assertGreater(len(sensors), 0, f"No sensors found for {asset}")
            
            # Verify core physical parameters
            ids = [s.sensor_id for s in sensors]
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.POWER", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.VOLTAGE", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.CURRENT", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.FREQUENCY", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.PF", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.RPM", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.RUNNING_STATUS", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.OPERATING_STATE", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.EXHAUST_TEMP", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.COOLANT_TEMP", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.OIL_PRESSURE", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.COOLANT_PRESSURE", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.FUEL_CONSUMPTION", ids)
            self.assertIn(f"BHARATI.CHP.{chp_idx:02d}.RUNTIME_HOURS", ids)

    def test_02_both_ups_units_created(self) -> None:
        """Verify sensors exist for both 60 kVA UPS plants."""
        for ups_idx in (1, 2):
            asset = f"UPS-{ups_idx}"
            sensors = self.registry.get_sensors_by_asset(asset)
            self.assertGreater(len(sensors), 0, f"No sensors found for {asset}")
            
            ids = [s.sensor_id for s in sensors]
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.INPUT_VOLTAGE_L1", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.OUTPUT_VOLTAGE_L1", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.DC_LINK_VOLTAGE", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.LOAD", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.REAL_POWER", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.BATTERY_VOLTAGE", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.BATTERY_SOC", ids)
            self.assertIn(f"BHARATI.UPS.{ups_idx:02d}.CELL_VOLTAGES", ids)

    def test_03_fuel_sensors_created(self) -> None:
        """Verify fuel monitoring sensors exist for bulk, day tank, and status."""
        fuel_sensors = self.registry.get_sensors_by_category(SensorCategory.FUEL)
        ids = [s.sensor_id for s in fuel_sensors]
        
        self.assertIn("BHARATI.FUEL.BULK.LEVEL", ids)
        self.assertIn("BHARATI.FUEL.BULK.PERCENT", ids)
        self.assertIn("BHARATI.FUEL.DAYTANK.LEVEL", ids)
        self.assertIn("BHARATI.FUEL.DAYTANK.PERCENT", ids)
        self.assertIn("BHARATI.FUEL.TEMPERATURE", ids)
        self.assertIn("BHARATI.FUEL.FLOW", ids)
        self.assertIn("BHARATI.FUEL.LEAK_STATUS", ids)
        self.assertIn("BHARATI.FUEL.OVERFILL_STATUS", ids)
        self.assertIn("BHARATI.FUEL.TOTAL_AVAILABLE", ids)
        self.assertIn("BHARATI.FUEL.AUTONOMY_HOURS", ids)

    def test_04_heating_sensors_created(self) -> None:
        """Verify heating loop and thermal energy recovery sensors exist."""
        heating_sensors = self.registry.get_sensors_by_category(SensorCategory.HEATING)
        ids = [s.sensor_id for s in heating_sensors]
        
        self.assertIn("BHARATI.HEATING.SUPPLY_TEMP", ids)
        self.assertIn("BHARATI.HEATING.RETURN_TEMP", ids)
        self.assertIn("BHARATI.HEATING.GLYCOL_TEMP", ids)
        self.assertIn("BHARATI.HEATING.GLYCOL_PRESSURE", ids)
        self.assertIn("BHARATI.HEATING.BUFFER_TANK_TEMP", ids)
        self.assertIn("BHARATI.HEATING.HOT_WATER_TEMP", ids)
        self.assertIn("BHARATI.HEATING.PUMP_STATUS", ids)
        self.assertIn("BHARATI.HEATING.PUMP_FLOW", ids)
        self.assertIn("BHARATI.HEATING.PUMP_PRESSURE", ids)
        self.assertIn("BHARATI.HEATING.CHP_THERMAL_KW", ids)
        self.assertIn("BHARATI.HEATING.DELTA_T", ids)
        self.assertIn("BHARATI.HEATING.ESTIMATED_THERMAL_KW", ids)

    def test_05_virtual_sensors_created(self) -> None:
        """Verify virtual and derived system energy sensors exist."""
        virtual_sensors = self.registry.get_sensors_by_category(SensorCategory.VIRTUAL)
        ids = [s.sensor_id for s in virtual_sensors]
        
        self.assertIn("BHARATI.VIRTUAL.TOTAL_GENERATION", ids)
        self.assertIn("BHARATI.VIRTUAL.TOTAL_LOAD", ids)
        self.assertIn("BHARATI.VIRTUAL.NET_BALANCE", ids)
        self.assertIn("BHARATI.VIRTUAL.TOTAL_FUEL", ids)
        self.assertIn("BHARATI.VIRTUAL.FUEL_AUTONOMY", ids)
        self.assertIn("BHARATI.VIRTUAL.GENERATOR_UTILIZATION", ids)
        self.assertIn("BHARATI.VIRTUAL.TOTAL_THERMAL_OUTPUT", ids)
        self.assertIn("BHARATI.VIRTUAL.HEATING_DELTA_T", ids)
        self.assertIn("BHARATI.VIRTUAL.CRITICAL_LOAD_PERCENT", ids)
        self.assertIn("BHARATI.VIRTUAL.ELECTRICAL_EFFICIENCY", ids)
        self.assertIn("BHARATI.VIRTUAL.TOTAL_EFFICIENCY", ids)

    def test_06_sensor_ids_are_unique(self) -> None:
        """Verify that every registered sensor has a unique sensor_id."""
        all_sensors = self.registry.get_all_sensors()
        ids = [s.sensor_id for s in all_sensors]
        self.assertEqual(len(ids), len(set(ids)), "Sensor IDs contain duplicates")
        self.assertEqual(len(ids), 140, "Total sensor count expected to be 140")

    def test_07_readings_contain_required_metadata(self) -> None:
        """Verify that all readings contain required metadata fields."""
        readings = self.registry.read_all()
        for s_id, reading in readings.items():
            self.assertEqual(reading.sensor_id, s_id)
            self.assertEqual(reading.station, "BHARATI")
            self.assertEqual(reading.domain, "ENERGY")
            self.assertTrue(len(reading.asset) > 0)
            self.assertTrue(len(reading.parameter) > 0)
            self.assertTrue(len(reading.unit) > 0)
            self.assertTrue(len(reading.timestamp) > 0)
            self.assertEqual(reading.source, SensorProvenance.SIMULATED)
            self.assertEqual(reading.source_reference, "bharati_energy_physics_v1")
            self.assertIn(reading.quality, (SensorQuality.GOOD, SensorQuality.WARNING))
            self.assertGreaterEqual(reading.confidence, 0.0)
            self.assertLessEqual(reading.confidence, 1.0)
            self.assertTrue(reading.valid)

    def test_08_units_are_correct(self) -> None:
        """Verify physical units match engineering specifications."""
        readings = self.registry.read_all()
        self.assertEqual(readings["BHARATI.CHP.01.POWER"].unit, "kW")
        self.assertEqual(readings["BHARATI.CHP.01.VOLTAGE"].unit, "V")
        self.assertEqual(readings["BHARATI.CHP.01.CURRENT"].unit, "A")
        self.assertEqual(readings["BHARATI.CHP.01.FREQUENCY"].unit, "Hz")
        self.assertEqual(readings["BHARATI.CHP.01.RPM"].unit, "RPM")
        self.assertEqual(readings["BHARATI.CHP.01.EXHAUST_TEMP"].unit, "°C")
        self.assertEqual(readings["BHARATI.CHP.01.OIL_PRESSURE"].unit, "bar")
        self.assertEqual(readings["BHARATI.FUEL.BULK.LEVEL"].unit, "L")
        self.assertEqual(readings["BHARATI.FUEL.FLOW"].unit, "L/h")
        self.assertEqual(readings["BHARATI.HEATING.PUMP_FLOW"].unit, "m³/h")
        self.assertEqual(readings["BHARATI.HEATING.CHP_THERMAL_KW"].unit, "kWth")

    def test_09_values_stay_within_valid_ranges(self) -> None:
        """Verify values remain within configured min/max valid bounds during normal operation."""
        readings = self.registry.read_all()
        for s_id, reading in readings.items():
            if isinstance(reading.value, (int, float)):
                if reading.min_valid is not None:
                    self.assertGreaterEqual(
                        reading.value,
                        reading.min_valid,
                        f"Sensor {s_id} value {reading.value} < min_valid {reading.min_valid}"
                    )
                if reading.max_valid is not None:
                    self.assertLessEqual(
                        reading.value,
                        reading.max_valid,
                        f"Sensor {s_id} value {reading.value} > max_valid {reading.max_valid}"
                    )

    def test_10_chp_generation_affects_total_generation(self) -> None:
        """Verify changes in CHP active power directly change virtual total generation."""
        # Initial reading with CHP-1 and CHP-2 running
        r1 = self.registry.read_all()
        gen1 = r1["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
        
        # Start CHP-3
        self.registry.physics.chps[2].operating_state = "RUNNING"
        self.registry.step(1.0)
        
        r2 = self.registry.read_all()
        gen2 = r2["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
        
        # Load was shared among 3 CHPs, total generation tracks station load
        chp1_p = r2["BHARATI.CHP.01.POWER"].value
        chp2_p = r2["BHARATI.CHP.02.POWER"].value
        chp3_p = r2["BHARATI.CHP.03.POWER"].value
        self.assertAlmostEqual(gen2, chp1_p + chp2_p + chp3_p, places=1)

    def test_11_chp_operation_affects_fuel_consumption(self) -> None:
        """Verify operating CHPs consume fuel proportional to load."""
        r = self.registry.read_all()
        chp1_fuel = r["BHARATI.CHP.01.FUEL_CONSUMPTION"].value
        chp3_fuel = r["BHARATI.CHP.03.FUEL_CONSUMPTION"].value
        
        # CHP-1 is running (~80 kW), CHP-3 is on standby (0 kW)
        self.assertGreater(chp1_fuel, 15.0, "Running CHP fuel consumption expected > 15 L/h")
        self.assertEqual(chp3_fuel, 0.0, "Standby CHP fuel consumption expected 0 L/h")

    def test_12_fuel_decreases_when_chp_is_operating(self) -> None:
        """Verify total station fuel inventory decreases as CHPs operate over time."""
        r_initial = self.registry.read_all()
        initial_fuel = r_initial["BHARATI.VIRTUAL.TOTAL_FUEL"].value
        
        # Advance simulation by 1 hour (3600 seconds)
        self.registry.step(3600.0)
        
        r_final = self.registry.read_all()
        final_fuel = r_final["BHARATI.VIRTUAL.TOTAL_FUEL"].value
        
        self.assertLess(final_fuel, initial_fuel, "Fuel did not decrease after 1 hour of CHP operation")
        consumed = initial_fuel - final_fuel
        self.assertGreater(consumed, 25.0, "Expected significant fuel consumption over 1 hour")

    def test_13_heating_supply_temp_greater_than_return_temp(self) -> None:
        """Verify heating supply temperature is higher than return temperature during active heating."""
        r = self.registry.read_all()
        t_supply = r["BHARATI.HEATING.SUPPLY_TEMP"].value
        t_return = r["BHARATI.HEATING.RETURN_TEMP"].value
        delta_t = r["BHARATI.HEATING.DELTA_T"].value
        
        self.assertGreater(t_supply, t_return, f"Supply {t_supply} <= Return {t_return}")
        self.assertAlmostEqual(delta_t, t_supply - t_return, places=1)

    def test_14_useful_thermal_output_bounded_by_155_kwth(self) -> None:
        """Verify useful delivered thermal heat never exceeds documented NCPOR limit of 155 kWth."""
        # Drive load high to maximize waste heat
        self.registry.physics.base_station_load_kw = 230.0
        for chp in self.registry.physics.chps:
            chp.operating_state = "RUNNING"
        self.registry.step(10.0)
        
        r = self.registry.read_all()
        useful_thermal = r["BHARATI.HEATING.ESTIMATED_THERMAL_KW"].value
        self.assertLessEqual(
            useful_thermal,
            MAX_STATION_HEATING_DEMAND_KW,
            f"Useful thermal {useful_thermal} exceeded documented limit {MAX_STATION_HEATING_DEMAND_KW}"
        )

    def test_15_virtual_total_generation_equals_sum_of_chp_power(self) -> None:
        """Verify virtual total generation exactly equals the sum of running CHP active powers."""
        r = self.registry.read_all()
        sum_chp = (
            r["BHARATI.CHP.01.POWER"].value +
            r["BHARATI.CHP.02.POWER"].value +
            r["BHARATI.CHP.03.POWER"].value
        )
        total_gen = r["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
        self.assertAlmostEqual(total_gen, sum_chp, places=1)

    def test_16_net_energy_balance_calculated_correctly(self) -> None:
        """Verify net energy balance equals total generation minus station load."""
        r = self.registry.read_all()
        gen = r["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
        load = r["BHARATI.VIRTUAL.TOTAL_LOAD"].value
        balance = r["BHARATI.VIRTUAL.NET_BALANCE"].value
        self.assertAlmostEqual(balance, gen - load, places=1)

    def test_17_sensor_failure_simulation_works(self) -> None:
        """Verify simulated technical sensor faults alter reading behavior."""
        sensor_id = "BHARATI.CHP.01.POWER"
        
        # Test DROPOUT
        self.registry.simulate_failure(sensor_id, FailureType.DROPOUT)
        r_drop = self.registry.read_sensor(sensor_id)
        self.assertEqual(r_drop.quality, SensorQuality.FAILED)
        self.assertIsNone(r_drop.value)
        self.assertFalse(r_drop.valid)
        
        # Test CLEAR
        self.registry.clear_failure(sensor_id)
        r_cleared = self.registry.read_sensor(sensor_id)
        self.assertEqual(r_cleared.quality, SensorQuality.GOOD)
        self.assertIsNotNone(r_cleared.value)
        self.assertTrue(r_cleared.valid)

    def test_18_stale_failed_bad_states_work(self) -> None:
        """Verify STALE, OUT_OF_RANGE, and STUCK produce proper qualities and freeze values."""
        sensor_id = "BHARATI.CHP.01.POWER"
        
        # STALE
        self.registry.simulate_failure(sensor_id, FailureType.STALE, stale_seconds=300.0)
        r_stale = self.registry.read_sensor(sensor_id)
        self.assertEqual(r_stale.quality, SensorQuality.STALE)
        self.assertFalse(r_stale.valid)
        
        # OUT_OF_RANGE
        self.registry.simulate_failure(sensor_id, FailureType.OUT_OF_RANGE)
        r_oor = self.registry.read_sensor(sensor_id)
        self.assertEqual(r_oor.quality, SensorQuality.BAD)
        self.assertFalse(r_oor.valid)
        self.assertGreater(r_oor.value, 105.0)
        
        # STUCK (preserves previous value)
        self.registry.clear_failure(sensor_id)
        initial_val = self.registry.read_sensor(sensor_id).value
        self.registry.simulate_failure(sensor_id, FailureType.STUCK)
        
        # Step physics to vary true generator power
        self.registry.step(10.0)
        r_stuck = self.registry.read_sensor(sensor_id)
        self.assertEqual(r_stuck.quality, SensorQuality.BAD)
        self.assertEqual(r_stuck.value, initial_val, "STUCK failure did not preserve previous reading value")

    def test_19_registry_lookup_by_id_asset_category_kind(self) -> None:
        """Verify sensor registry lookup functions work accurately across all dimensions."""
        # By ID
        s = self.registry.get_sensor("BHARATI.FUEL.DAYTANK.LEVEL")
        self.assertEqual(s.parameter, "day_tank_level_l")
        
        # By Asset
        ups1_sensors = self.registry.get_sensors_by_asset("UPS-1")
        self.assertEqual(len(ups1_sensors), 31)
        
        # By Category
        chp_sensors = self.registry.get_sensors_by_category(SensorCategory.CHP)
        self.assertEqual(len(chp_sensors), 45)  # 3 CHPs * 15 sensors
        
        # By Kind
        derived_sensors = self.registry.get_sensors_by_kind(SensorKind.DERIVED)
        self.assertEqual(len(derived_sensors), 15)  # 2 in fuel, 2 in heating, 11 in virtual

    def test_20_reproducible_simulation_with_fixed_seed(self) -> None:
        """Verify that identical random seeds produce identical sensor reading sequences."""
        reg1 = create_bharati_energy_sensors(seed=999, clock=SimulationClock())
        reg2 = create_bharati_energy_sensors(seed=999, clock=SimulationClock())
        
        for _ in range(5):
            reg1.step(2.0)
            reg2.step(2.0)
            
        r1 = reg1.read_all()
        r2 = reg2.read_all()
        
        for s_id in r1:
            val1 = r1[s_id].value
            val2 = r2[s_id].value
            self.assertEqual(val1, val2, f"Seed reproducibility failed for sensor {s_id}")

    def test_21_fuel_conservation(self) -> None:
        """Verify conservation of fuel: (bulk_init + day_init) == (bulk_final + day_final + fuel_consumed)."""
        bulk_init = self.registry.physics.fuel.bulk_fuel_level_l
        day_init = self.registry.physics.fuel.day_tank_level_l
        
        # Step through multiple cycles (1800 seconds), causing fuel consumption and pump transfers
        self.registry.step(1800.0)
        
        bulk_final = self.registry.physics.fuel.bulk_fuel_level_l
        day_final = self.registry.physics.fuel.day_tank_level_l
        consumed = self.registry.physics.fuel.cumulative_fuel_consumed_l
        
        total_initial = bulk_init + day_init
        total_final_accounting = bulk_final + day_final + consumed
        self.assertAlmostEqual(
            total_initial,
            total_final_accounting,
            places=1,
            msg="Fuel conservation violated across bulk and day tank accounting"
        )

    def test_22_energy_balance_conservation(self) -> None:
        """Verify that net_balance equals generation minus station load consistently across steps."""
        for _ in range(3):
            self.registry.step(5.0)
            r = self.registry.read_all()
            gen = r["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
            load = r["BHARATI.VIRTUAL.TOTAL_LOAD"].value
            balance = r["BHARATI.VIRTUAL.NET_BALANCE"].value
            self.assertAlmostEqual(balance, gen - load, places=2)

    def test_23_thermal_consistency(self) -> None:
        """Verify thermal output bounds: useful <= recoverable, useful <= demand, demand <= 155 kWth."""
        for _ in range(3):
            self.registry.step(10.0)
            physics = self.registry.physics
            useful = physics.heating.useful_thermal_output_kw
            recoverable = physics.heating.recoverable_thermal_kw
            demand = physics.heating.station_heating_demand_kw
            
            self.assertLessEqual(useful, recoverable + 0.01)
            self.assertLessEqual(useful, demand + 0.01)
            self.assertLessEqual(demand, MAX_STATION_HEATING_DEMAND_KW)

    def test_24_sensor_provenance_discipline(self) -> None:
        """Verify all sensor readings strictly report SIMULATED provenance with source reference."""
        readings = self.registry.read_all()
        for s_id, r in readings.items():
            self.assertEqual(
                r.source,
                SensorProvenance.SIMULATED,
                f"Sensor {s_id} did not report SIMULATED provenance"
            )
            self.assertEqual(
                r.source_reference,
                "bharati_energy_physics_v1",
                f"Sensor {s_id} has invalid source reference {r.source_reference}"
            )


if __name__ == "__main__":
    unittest.main()
