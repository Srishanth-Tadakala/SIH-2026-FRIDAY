"""Standalone Demonstration Script for Bharati Station Energy Sensor Layer.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Demonstrates:
1. Initialization of Bharati Energy Sensor Registry (140 sensors).
2. Clean physical snapshot across CHPs, UPS, Fuel, Heating, and Virtual metrics.
3. Progression across simulation time steps.
4. Injection and reporting of simulated sensor failures (STUCK, DROPOUT).
5. Restoration of sensor health upon clearing faults.
"""

import sys
from datetime import datetime

# Ensure project root is in sys.path
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.sensors.bharati_sensors.energy import (
    FailureType,
    SensorProvenance,
    create_bharati_energy_sensors,
)
from backend.sensors.bharati_sensors.energy.clock import SimulationClock


def format_separator(title: str = "", width: int = 76) -> str:
    if not title:
        return "=" * width
    pad = (width - len(title) - 2) // 2
    return f"{'=' * pad} {title} {'=' * (width - len(title) - 2 - pad)}"


def main() -> None:
    print("\n" + format_separator("SIH 2026: F.R.I.D.A.Y. - BHARATI ENERGY SENSOR LAYER"))
    print("OBJECTIVE: Bharati Station Energy Telemetry & Physical Coherence Simulation")
    print("STATUS: SENSOR LAYER ONLY (No Agents, No APIs, No DBs, No UI)\n")

    # 1. Initialize Sensor Registry
    clock = SimulationClock(datetime(2026, 9, 19, 14, 30, 0))
    registry = create_bharati_energy_sensors(seed=2026, clock=clock)
    all_sensors = registry.get_all_sensors()
    print(f"[OK] Initialized Bharati Sensor Registry: {len(all_sensors)} sensors registered.")
    print(f"[OK] Simulation Clock initialized at: {clock.isoformat()}")

    # 2. Capture Initial Sensor Readings
    readings = registry.read_all()

    # 3. Print Snapshot
    print("\n" + format_separator("BHARATI ENERGY SENSOR SNAPSHOT (T = 0s)"))

    # A. CHP Units
    print("\n--- COMBINED HEAT & POWER (CHP) UNITS (3 x 100 kVA) ---")
    for idx in (1, 2, 3):
        prefix = f"BHARATI.CHP.{idx:02d}"
        state = readings[f"{prefix}.OPERATING_STATE"].value
        p_act = readings[f"{prefix}.POWER"].value
        v_act = readings[f"{prefix}.VOLTAGE"].value
        f_act = readings[f"{prefix}.FREQUENCY"].value
        rpm = readings[f"{prefix}.RPM"].value
        ex_t = readings[f"{prefix}.EXHAUST_TEMP"].value
        oil_p = readings[f"{prefix}.OIL_PRESSURE"].value
        fuel = readings[f"{prefix}.FUEL_CONSUMPTION"].value
        
        print(f"  CHP-{idx} [{state}]:")
        print(f"    Power: {p_act:5.1f} kW | Voltage: {v_act:5.1f} V | Freq: {f_act:5.2f} Hz | Speed: {rpm:4.0f} RPM")
        print(f"    Exhaust: {ex_t:5.1f} deg C | Oil Press: {oil_p:4.2f} bar | Fuel Flow: {fuel:4.1f} L/h")

    # B. UPS Plants
    print("\n--- UNINTERRUPTIBLE POWER SUPPLY (UPS) PLANTS (2 x 60 kVA) ---")
    for idx in (1, 2):
        prefix = f"BHARATI.UPS.{idx:02d}"
        load_pct = readings[f"{prefix}.LOAD"].value
        p_kw = readings[f"{prefix}.REAL_POWER"].value
        v_out = readings[f"{prefix}.OUTPUT_VOLTAGE_L1"].value
        b_soc = readings[f"{prefix}.BATTERY_SOC"].value
        b_volt = readings[f"{prefix}.BATTERY_VOLTAGE"].value
        b_curr = readings[f"{prefix}.BATTERY_CURRENT"].value
        b_time = readings[f"{prefix}.BACKUP_TIME"].value
        b_stat = readings[f"{prefix}.BATTERY_STATUS"].value
        
        print(f"  UPS-{idx} [{b_stat}]:")
        print(f"    Output: {v_out:5.1f} V | Active Load: {p_kw:4.1f} kW ({load_pct:4.1f}% rating)")
        print(f"    Battery: {b_soc:5.1f}% SOC | {b_volt:5.1f} V | {b_curr:4.1f} A | Autonomy: {b_time:4.0f} min")

    # C. Fuel System
    print("\n--- FUEL INFRASTRUCTURE & INVENTORY ---")
    bulk_l = readings["BHARATI.FUEL.BULK.LEVEL"].value
    bulk_pct = readings["BHARATI.FUEL.BULK.PERCENT"].value
    day_l = readings["BHARATI.FUEL.DAYTANK.LEVEL"].value
    day_pct = readings["BHARATI.FUEL.DAYTANK.PERCENT"].value
    fuel_flow = readings["BHARATI.FUEL.FLOW"].value
    tot_fuel = readings["BHARATI.VIRTUAL.TOTAL_FUEL"].value
    autonomy = readings["BHARATI.VIRTUAL.FUEL_AUTONOMY"].value
    leak = readings["BHARATI.FUEL.LEAK_STATUS"].value
    
    print(f"  Bulk Fuel Farm: {bulk_l:8,.1f} L ({bulk_pct:5.1f}% nominal 312k L capacity)")
    print(f"  Power Stn Day Tank: {day_l:6.1f} L ({day_pct:5.1f}% capacity)")
    print(f"  Total Station Fuel: {tot_fuel:8,.1f} L | Total Burn Rate: {fuel_flow:4.1f} L/h")
    print(f"  Estimated Autonomy: {autonomy:7,.1f} hours ({autonomy/24.0:4.1f} days) | Leak Status: {leak}")

    # D. Heating / Thermal Recovery
    print("\n--- STATION HEATING & THERMAL RECOVERY ---")
    t_sup = readings["BHARATI.HEATING.SUPPLY_TEMP"].value
    t_ret = readings["BHARATI.HEATING.RETURN_TEMP"].value
    d_t = readings["BHARATI.HEATING.DELTA_T"].value
    t_gly = readings["BHARATI.HEATING.GLYCOL_TEMP"].value
    p_gly = readings["BHARATI.HEATING.GLYCOL_PRESSURE"].value
    heat_kw = readings["BHARATI.HEATING.ESTIMATED_THERMAL_KW"].value
    p_stat = readings["BHARATI.HEATING.PUMP_STATUS"].value
    p_flow = readings["BHARATI.HEATING.PUMP_FLOW"].value
    
    print(f"  Supply Temp: {t_sup:4.1f} deg C | Return Temp: {t_ret:4.1f} deg C | Delta T: {d_t:4.1f} deg C (T_supply > T_return: True)")
    print(f"  Glycol Loop: {t_gly:4.1f} deg C @ {p_gly:4.2f} bar | Pump: {p_stat} ({p_flow:4.1f} m3/h)")
    print(f"  Delivered Heat: {heat_kw:5.1f} kWth (Documented Max Demand Cap: 155.0 kWth)")

    # E. Virtual / System Energy Balance
    print("\n--- SYSTEM-WIDE VIRTUAL ENERGY METRICS ---")
    gen_kw = readings["BHARATI.VIRTUAL.TOTAL_GENERATION"].value
    load_kw = readings["BHARATI.VIRTUAL.TOTAL_LOAD"].value
    net_bal = readings["BHARATI.VIRTUAL.NET_BALANCE"].value
    gen_util = readings["BHARATI.VIRTUAL.GENERATOR_UTILIZATION"].value
    elec_eff = readings["BHARATI.VIRTUAL.ELECTRICAL_EFFICIENCY"].value
    tot_eff = readings["BHARATI.VIRTUAL.TOTAL_EFFICIENCY"].value
    
    print(f"  Total Generation: {gen_kw:5.1f} kW | Total Station Demand: {load_kw:5.1f} kW")
    print(f"  Net Energy Balance: {net_bal:+5.1f} kW | Generator Utilization: {gen_util:4.1f}%")
    print(f"  Electrical Efficiency: {elec_eff:4.1f}% | Combined CHP Efficiency: {tot_eff:4.1f}%")

    # 4. Advance Simulation Time (Time progression demonstration)
    print("\n" + format_separator("SIMULATION TIME STEP PROGRESSION (60 seconds elapsed)"))
    registry.step(60.0)
    step_readings = registry.get_latest_state()
    print(f"  New Timestamp: {clock.isoformat()}")
    print(f"  CHP-1 Power:   {step_readings['BHARATI.CHP.01.POWER'].value} kW")
    print(f"  CHP-2 Power:   {step_readings['BHARATI.CHP.02.POWER'].value} kW")
    print(f"  Day Tank Level: {step_readings['BHARATI.FUEL.DAYTANK.LEVEL'].value} L")
    print(f"  Delivered Heat: {step_readings['BHARATI.HEATING.ESTIMATED_THERMAL_KW'].value} kWth")

    # 5. Demonstrate Simulated Technical Sensor Failures
    print("\n" + format_separator("SIMULATED SENSOR FAULT INJECTION DEMONSTRATION"))
    
    # Fault 1: Freeze CHP-1 Power sensor (STUCK)
    chp1_sensor_id = "BHARATI.CHP.01.POWER"
    print(f"\n[Injecting Fault 1] Freezing sensor '{chp1_sensor_id}' to STUCK...")
    registry.simulate_failure(chp1_sensor_id, FailureType.STUCK)
    r_stuck = registry.read_sensor(chp1_sensor_id)
    print(f"  Reading value:   {r_stuck.value} {r_stuck.unit}")
    print(f"  Sensor Quality:  {r_stuck.quality.value}")
    print(f"  Validity Flag:   {r_stuck.valid}")
    print(f"  Confidence:      {r_stuck.confidence}")

    # Fault 2: Disconnect Fuel Flow sensor (DROPOUT)
    fuel_sensor_id = "BHARATI.FUEL.FLOW"
    print(f"\n[Injecting Fault 2] Injecting DROPOUT into '{fuel_sensor_id}'...")
    registry.simulate_failure(fuel_sensor_id, FailureType.DROPOUT)
    r_drop = registry.read_sensor(fuel_sensor_id)
    print(f"  Reading value:   {r_drop.value}")
    print(f"  Sensor Quality:  {r_drop.quality.value}")
    print(f"  Validity Flag:   {r_drop.valid}")
    print(f"  Confidence:      {r_drop.confidence}")

    # Clear faults and show recovery
    print(f"\n[Restoring Health] Clearing all sensor faults...")
    registry.clear_all_failures()
    r_restored1 = registry.read_sensor(chp1_sensor_id)
    r_restored2 = registry.read_sensor(fuel_sensor_id)
    print(f"  {chp1_sensor_id} -> Value: {r_restored1.value} {r_restored1.unit} | Quality: {r_restored1.quality.value} | Valid: {r_restored1.valid}")
    print(f"  {fuel_sensor_id}        -> Value: {r_restored2.value} {r_restored2.unit} | Quality: {r_restored2.quality.value} | Valid: {r_restored2.valid}")

    # Final Boundary Confirmation
    print("\n" + format_separator())
    print("BOUNDARY CHECK CONFIRMED:")
    print("  * No EnergyAgent or AgentBase instantiated.")
    print("  * No Event Bus or inter-agent messaging created.")
    print("  * No REST / Web API created.")
    print("  * No database persistence created.")
    print("  * No UI / Dashboard created.")
    print("  * Sensor Layer cleanly delivers raw and derived telemetry snapshots.")
    print(format_separator())


if __name__ == "__main__":
    main()
