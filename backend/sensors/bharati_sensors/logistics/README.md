# Bharati Station Logistics Observation Layer v1

Part of **SIH 2026 Project SIH26060: F.R.I.D.A.Y.**  
*Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations*

Target Station: **Bharati Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E)**

---

## 1. Executive Summary & Purpose

The **Bharati Logistics Observation Layer v1** (`backend.sensors.bharati_sensors.logistics`) provides a physically coherent, evidence-disciplined, deterministic, simulated telemetry and observation layer capturing the station's end-to-end logistics ecosystem:

- **Fleet / Vehicles & Heavy Equipment**: Pisten Bullies, snow scooters, telehandlers, excavators, bulldozers, and crawler cranes.
- **Cargo & ISO Containers**: Staging yards, gross weight records, internal temperature/humidity, shock accelerations, and door seals.
- **Fuel Logistics & Dispensing**: Station vehicle dispensing tanks, helicopter supply context, transfer line pressure/temp, and bund leak detection.
- **Cold Chain (Reefer Containers)**: Deep frozen (-22°C) rations, chilled stores, compressor status, grid/diesel power switching, and thermal excursion indicators.
- **Aviation Logistics**: Helicopter flight telemetry, cumulative airframe hours, and station helipad operational viability.
- **Marine & Coastal Logistics**: Ice-class expedition vessel distance/speed, offloading barge shuttling, voyage discharge progress, and coastal sea-berth safety.
- **Routes & Accessibility**: Station perimeter tracks, coastal links, fast-ice traverses, inter-station corridors, and surface traction index.
- **Missions & Field Personnel**: Anonymous operational groups (`TEAM-FIELD-01`, `TEAM-FIELD-02`), muster counts, comms checks, and return margins (zero personal PII).
- **Inventory & Essential Stores**: Food rations autonomy days, generator/vehicle spares, water treatment consumables, and stockout risk scores.
- **Waste & Return Logistics**: Compacted solid waste, hazardous drums, and backhaul staging governed under the **Protocol on Environmental Protection to the Antarctic Treaty (Madrid Protocol)**.
- **Derived Logistics Indicators**: Deterministic indices for fleet availability, cargo integrity, cold-chain risk, route accessibility, aviation access, marine access, and explainable condition summaries.

It answers one core question:
> **“What is the operational status, location, integrity, and safety margin of Bharati's logistics chain?”**

It does **NOT** answer:
> *“Which vehicle should be autonomously dispatched, or how should routes be optimized?”*

All dispatch optimization, autonomous route planning, predictive maintenance, and LLM reasoning belong to future Agent and Digital Twin layers.

> [!IMPORTANT]
> **Strict Architectural Boundaries**:
> - Sensors are **NOT** the Digital Twin Core.
> - **Zero** Agents instantiated.
> - **Zero** REST/GraphQL APIs.
> - **Zero** Database persistence layers.
> - **Zero** UI / Dashboard components.
> - **Zero** LLM / AI reasoning calls.
> - **Zero** Message brokers / MQTT / Event buses.
> - **Zero** Autonomous dispatch / route optimization engines.

---

## 2. Core Architecture

```
                       BHARATI LOGISTICS
              (Station, Field Routes, Coastal Berth)
                                │
                                ▼
                 LOGISTICS PHYSICS / SYSTEM STATE
           (BharatiLogisticsPhysicsState: Single Source of Truth)
                                │
     ┌───────────────┬──────────┼───────────┬───────────────┐
     ▼               ▼          ▼           ▼               ▼
   Fleet          Cargo &      Fuel      Cold Chain     Aviation &
 (Vehicles)     Containers  Logistics    (Reefers)      Marine
     │               │          │           │               │
     ▼               ▼          ▼           ▼               ▼
   Routes &      Missions &  Inventory   Waste Return    Derived
 Accessibility  Personnel   & Stores     (Madrid Prot)  Indicators
     │               │          │           │               │
     └───────────────┴──────────┼───────────┴───────────────┘
                                ▼
                    LOGISTICS OBSERVATION LAYER
            (98 Simulated Telemetry/State Points Configured)
                    ├── Instrument Sensors
                    ├── State Sensors
                    └── Derived Indicators
                                │
                                ▼
                    LOGISTICS SENSOR REGISTRY
               (LogisticsSensorRegistry / Factory)
                                │
                                ▼
                      STANDARDIZED READINGS
               (SensorReading: SIMULATED Provenance)
                                │
     ┌──────────────────────────┼──────────────────────────┐
     ▼ (Read-Only)              ▼ (Read-Only)              ▼ (Read-Only)
Environment Inputs         Infrastructure State         Energy State
  (Wind, Sea Ice,           (Storage, Loading)        (Fuel Context)
   Blizzard Risk)               │                          │
     │                          │                          │
     ▼                          ▼                          ▼
(Future Twin Core)         (Future Twin Core)         (Future Twin Core)
```

---

## 3. Formal Anti-Duplication Rule

> [!CAUTION]
> **Anti-Duplication Principle**:
> Logistics **MUST NOT** independently simulate ambient environmental observations already owned by the Environment pillar. Logistics consumes those observations through strictly read-only interfaces and derives logistics-specific operational states from them.

- Ambient wind and gusts $\rightarrow$ owned by **Environment** (`ENV-WX-WIND-S`, `ENV-WX-GUST`). Logistics observes wind and evaluates helipad operational status and sea-berth docking safety.
- Ambient optical visibility $\rightarrow$ owned by **Environment** (`ENV-WX-VIS`). Logistics observes visibility and evaluates route transit limitation status (`LOG-ROUTE-VIS-LIMIT`).
- Snow depth and accumulation $\rightarrow$ owned by **Environment** (`ENV-SNOW-DEPTH`). Logistics observes snow depth and evaluates ground surface traction index (`LOG-ROUTE-SURFACE-TRACTION`).
- Sea-ice thickness and concentration $\rightarrow$ owned by **Environment** (`ENV-ICE-THICK`, `ENV-ICE-CONC`). Logistics observes sea ice and evaluates fast-ice route safety and marine berth safety.

---

## 4. Complete 98-Point Sensor Catalogue (11 Domains)

### 1. Fleet & Vehicle Telemetry (16 Points)
*Scope: `LOCAL_FLEET` / `LOCAL_STATION`*
- `LOG-FLEET-PB01-SPEED` (`km_h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.speed_km_h`
- `LOG-FLEET-PB01-HEADING` (`deg`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.heading_deg`
- `LOG-FLEET-PB01-RPM` (`RPM`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.engine_rpm`
- `LOG-FLEET-PB01-ENG-TEMP` (`degC`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.engine_temp_c`
- `LOG-FLEET-PB01-FUEL-LVL` (`%`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.fuel_level_percent`
- `LOG-FLEET-PB01-FUEL-RATE` (`L_h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.fuel_rate_l_h`
- `LOG-FLEET-PB01-BATTERY` (`V`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.battery_voltage_v`
- `LOG-FLEET-PB01-ENG-HOURS` (`h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.pb01.engine_hours`
- `LOG-FLEET-PB01-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.pb01.status`
- `LOG-FLEET-PB02-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.pb02.status`
- `LOG-FLEET-SC01-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.sc01.status`
- `LOG-FLEET-SC01-FUEL` (`%`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.sc01.fuel_level_percent`
- `LOG-FLEET-TH01-HYD-PRESS` (`bar`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fleet.telehandler.hydraulic_pressure_bar`
- `LOG-FLEET-TH01-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.telehandler.status`
- `LOG-FLEET-EXC01-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.excavator.status`
- `LOG-FLEET-CRANE01-STATUS` (`status`) [DOCUMENTED, STATE] -> `fleet.mantis_crane.status`

### 2. Cargo & Containers (10 Points)
*Scope: `STATION_STORAGE`*
- `LOG-CARGO-TOTAL-COUNT` (`count`) [DOCUMENTED, STATE] -> `cargo.total_cargo_units`
- `LOG-CARGO-IN-TRANSIT` (`count`) [DOCUMENTED, STATE] -> `cargo.in_transit_units`
- `LOG-CARGO-C01-LOC` (`status`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `cargo.c01.location_zone`
- `LOG-CARGO-C01-WEIGHT` (`kg`) [DOCUMENTED, STATE] -> `cargo.c01.gross_weight_kg`
- `LOG-CARGO-C01-TEMP` (`degC`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cargo.c01.temperature_c`
- `LOG-CARGO-C01-HUM` (`%`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cargo.c01.relative_humidity_percent`
- `LOG-CARGO-C01-SHOCK` (`g`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cargo.c01.shock_g`
- `LOG-CARGO-C01-TILT` (`deg`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cargo.c01.tilt_deg`
- `LOG-CARGO-C01-DOOR` (`status`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `cargo.c01.door_status`
- `LOG-CARGO-HAZMAT-STATUS` (`status`) [DOCUMENTED, STATE] -> `cargo.hazmat_staging_status`

### 3. Fuel Logistics (10 Points)
*Scope: `STATION_FUEL_FARM` (Fleet dispensing and supply context, distinct from Energy generation)*
- `LOG-FUEL-HELI-SUPPLY-LVL` (`L`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fuel.heli_supply_level_l`
- `LOG-FUEL-HELI-SUPPLY-PCT` (`%`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fuel.heli_supply_percent`
- `LOG-FUEL-VEH-TANK-LVL` (`L`) [DOCUMENTED, INSTRUMENT] -> `fuel.vehicle_tank_level_l`
- `LOG-FUEL-VEH-TANK-PCT` (`%`) [DOCUMENTED, INSTRUMENT] -> `fuel.vehicle_tank_percent`
- `LOG-FUEL-LINE-TEMP` (`degC`) [IMPLIED, INSTRUMENT] -> `fuel.line_temperature_c`
- `LOG-FUEL-LINE-PRESS` (`bar`) [IMPLIED, INSTRUMENT] -> `fuel.line_pressure_bar`
- `LOG-FUEL-TRANSFER-FLOW` (`L_min`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `fuel.transfer_flow_l_min`
- `LOG-FUEL-DISPENSED-DAILY` (`L`) [DOCUMENTED, STATE] -> `fuel.daily_dispensed_l`
- `LOG-FUEL-LEAK-MONITOR` (`status`) [IMPLIED, STATE] -> `fuel.leak_status`
- `LOG-FUEL-DISP-STATUS` (`status`) [DOCUMENTED, STATE] -> `fuel.dispenser_status`

### 4. Cold Chain / Reefer Containers (8 Points)
*Scope: `STATION_REEFER`*
- `LOG-REEFER-01-TEMP` (`degC`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cold_chain.reefer01.core_temp_c`
- `LOG-REEFER-01-SETPOINT` (`degC`) [DOCUMENTED, STATE] -> `cold_chain.reefer01.setpoint_c`
- `LOG-REEFER-01-DOOR` (`status`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `cold_chain.reefer01.door_status`
- `LOG-REEFER-01-COMP-RUN` (`status`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `cold_chain.reefer01.compressor_status`
- `LOG-REEFER-01-PWR-STATE` (`status`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `cold_chain.reefer01.power_source`
- `LOG-REEFER-01-EXCURSION` (`bool`) [DERIVED, DERIVED] -> `cold_chain.reefer01.temperature_excursion`
- `LOG-REEFER-02-TEMP` (`degC`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `cold_chain.reefer02.core_temp_c`
- `LOG-REEFER-02-STATUS` (`status`) [DOCUMENTED, STATE] -> `cold_chain.reefer02.status`

### 5. Aviation Logistics (7 Points)
*Scope: `AIR_OPERATION` / `LOCAL_STATION`*
- `LOG-AV-HELI-STATUS` (`status`) [DOCUMENTED, STATE] -> `aviation.heli.status`
- `LOG-AV-HELI-AIRBORNE` (`bool`) [NOT_PUBLICLY_CONFIRMED, STATE] -> `aviation.heli.is_airborne`
- `LOG-AV-HELI-FUEL-PCT` (`%`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `aviation.heli.fuel_remaining_percent`
- `LOG-AV-HELI-ALTITUDE` (`m`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `aviation.heli.altitude_m`
- `LOG-AV-HELI-GROUND-SPEED` (`km_h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `aviation.heli.ground_speed_km_h`
- `LOG-AV-HELI-FLIGHT-HRS` (`h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `aviation.heli.cumulative_flight_hours`
- `LOG-AV-HELIPAD-STATUS` (`status`) [DOCUMENTED, STATE] -> `aviation.helipad.status`

### 6. Marine Logistics (7 Points)
*Scope: `MARINE_OPERATION`*
- `LOG-MAR-VESSEL-STATUS` (`status`) [DOCUMENTED, STATE] -> `marine.vessel.status`
- `LOG-MAR-VESSEL-DIST` (`km`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `marine.vessel.distance_to_station_km`
- `LOG-MAR-VESSEL-SPEED` (`knot`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `marine.vessel.speed_knots`
- `LOG-MAR-BARGE-STATUS` (`status`) [DOCUMENTED, STATE] -> `marine.barge.status`
- `LOG-MAR-DISCHARGE-PROGRESS` (`%`) [DOCUMENTED, STATE] -> `marine.discharge_progress_percent`
- `LOG-MAR-SEA-BERTH-SAFE` (`status`) [DERIVED, STATE] -> `marine.sea_berth_safety`
- `LOG-MAR-UNLOAD-RATE` (`tonne_h`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `marine.unloading_rate_tonne_h`

### 7. Routes & Accessibility (8 Points)
*Scope: `FIELD_ROUTE`*
- `LOG-ROUTE-STATION-STATUS` (`status`) [DOCUMENTED, STATE] -> `routes.station_ring.status`
- `LOG-ROUTE-HELIPAD-STATUS` (`status`) [DOCUMENTED, STATE] -> `routes.helipad_track.status`
- `LOG-ROUTE-COAST-STATUS` (`status`) [DOCUMENTED, STATE] -> `routes.coastal_link.status`
- `LOG-ROUTE-FASTICE-STATUS` (`status`) [DOCUMENTED, STATE] -> `routes.fast_ice_route.status`
- `LOG-ROUTE-LARSEMANN-STATUS` (`status`) [DOCUMENTED, STATE] -> `routes.larsemann_interstation.status`
- `LOG-ROUTE-VIS-LIMIT` (`status`) [DERIVED, STATE] -> `routes.visibility_condition`
- `LOG-ROUTE-CREVASSE-RISK` (`status`) [DERIVED, STATE] -> `routes.crevasse_risk`
- `LOG-ROUTE-SURFACE-TRACTION` (`%`) [DERIVED, DERIVED] -> `routes.surface_traction_index`

### 8. Missions & Personnel Logistics (9 Points)
*Scope: `REMOTE_FIELD_SITE` / `LOCAL_STATION` (Anonymous operational groups, zero PII)*
- `LOG-MISS-ACTIVE-COUNT` (`count`) [DOCUMENTED, STATE] -> `missions.active_missions_count`
- `LOG-MISS-STATION-PAX` (`count`) [DOCUMENTED, STATE] -> `missions.station_personnel_count`
- `LOG-MISS-FIELD-PAX` (`count`) [DOCUMENTED, STATE] -> `missions.field_personnel_count`
- `LOG-MISS-TEAM01-STATUS` (`status`) [DOCUMENTED, STATE] -> `missions.team01.status`
- `LOG-MISS-TEAM01-DIST` (`km`) [NOT_PUBLICLY_CONFIRMED, INSTRUMENT] -> `missions.team01.distance_km`
- `LOG-MISS-TEAM01-RADIO` (`status`) [DOCUMENTED, STATE] -> `missions.team01.radio_check_status`
- `LOG-MISS-TEAM01-RETURN-MARGIN` (`min`) [DERIVED, DERIVED] -> `missions.team01.return_margin_minutes`
- `LOG-MISS-TEAM02-STATUS` (`status`) [DOCUMENTED, STATE] -> `missions.team02.status`
- `LOG-MISS-READINESS-INDEX` (`status`) [DERIVED, STATE] -> `missions.readiness_status`

### 9. Inventory & Stores (10 Points)
*Scope: `STATION_STORAGE`*
- `LOG-INV-RATIONS-DAYS` (`day`) [DOCUMENTED, STATE] -> `inventory.rations_autonomy_days`
- `LOG-INV-RATIONS-STOCK` (`%`) [DOCUMENTED, STATE] -> `inventory.rations_stock_percent`
- `LOG-INV-MEDICAL-STATUS` (`status`) [DOCUMENTED, STATE] -> `inventory.medical_supplies_status`
- `LOG-INV-SPARES-GEN-PCT` (`%`) [DOCUMENTED, STATE] -> `inventory.generator_spares_percent`
- `LOG-INV-SPARES-VEH-PCT` (`%`) [DOCUMENTED, STATE] -> `inventory.vehicle_spares_percent`
- `LOG-INV-WATER-TREAT-PCT` (`%`) [DOCUMENTED, STATE] -> `inventory.water_treatment_spares_percent`
- `LOG-INV-BATTERY-STORES` (`count`) [DOCUMENTED, STATE] -> `inventory.emergency_batteries_count`
- `LOG-INV-SAFETY-PPE-PCT` (`%`) [DOCUMENTED, STATE] -> `inventory.ppe_gear_percent`
- `LOG-INV-CRITICAL-ALERTS` (`count`) [DERIVED, STATE] -> `inventory.critical_stockout_alerts_count`
- `LOG-INV-STOCKOUT-RISK` (`score`) [DERIVED, DERIVED] -> `inventory.stockout_risk_score`

### 10. Waste & Madrid Protocol Return (5 Points)
*Scope: `STATION_STORAGE`*
- `LOG-WASTE-SOLID-VOL` (`m3`) [DOCUMENTED, STATE] -> `waste.solid_waste_volume_m3`
- `LOG-WASTE-SOLID-PCT` (`%`) [DOCUMENTED, STATE] -> `waste.solid_storage_percent`
- `LOG-WASTE-HAZARD-VOL` (`L`) [DOCUMENTED, STATE] -> `waste.hazard_waste_volume_l`
- `LOG-WASTE-HAZARD-STATUS` (`status`) [DOCUMENTED, STATE] -> `waste.hazard_containment_status`
- `LOG-WASTE-RET-READY` (`%`) [DOCUMENTED, STATE] -> `waste.return_shipment_readiness_percent`

### 11. Derived Logistics Indicators (8 Points)
*Scope: `DERIVED_LOGISTICS_ENGINE`*
- `LOG-DERIVED-FLEET-AVAIL` (`%`) [DERIVED, DERIVED] -> `derived.fleet_availability_percent`
- `LOG-DERIVED-CARGO-INTEGRITY` (`%`) [DERIVED, DERIVED] -> `derived.cargo_integrity_index`
- `LOG-DERIVED-COLD-CHAIN-RISK` (`score`) [DERIVED, DERIVED] -> `derived.cold_chain_risk_score`
- `LOG-DERIVED-ROUTE-ACCESS` (`%`) [DERIVED, DERIVED] -> `derived.ground_route_accessibility_percent`
- `LOG-DERIVED-AIR-ACCESS` (`%`) [DERIVED, DERIVED] -> `derived.aviation_accessibility_percent`
- `LOG-DERIVED-MARINE-ACCESS` (`%`) [DERIVED, DERIVED] -> `derived.marine_accessibility_percent`
- `LOG-DERIVED-LOGISTICS-RISK` (`score`) [DERIVED, DERIVED] -> `derived.composite_logistics_risk`
- `LOG-DERIVED-LOGISTICS-CONDITION` (`status`) [DERIVED, STATE] -> `derived.logistics_condition_summary`

**Total Configured Points: EXACTLY 98 POINTS**  
Calculation: $16 + 10 + 10 + 8 + 7 + 7 + 8 + 9 + 10 + 5 + 8 = 98$.

---

## 5. Bharati Fleet Asset Registry

All 16 documented physical Bharati vehicles and machines are registered in `FLEET_ASSET_REGISTRY`:

| Asset ID | Asset Type | Documented Model | Operational Role |
| :--- | :--- | :--- | :--- |
| `PB-01` | `PISTEN_BULLY` | Kässbohrer PistenBully 300 Polar | Primary Lead Groomer / Hauler |
| `PB-02` | `PISTEN_BULLY` | Kässbohrer PistenBully 300 Polar | Heavy Sled Support Hauler |
| `PB-03` | `PISTEN_BULLY` | Kässbohrer PistenBully 100 | Personnel Transport Cabin |
| `PB-04` | `PISTEN_BULLY` | Kässbohrer PistenBully 100 | Utility Science Tracked Carrier |
| `PB-05` | `PISTEN_BULLY` | Kässbohrer PistenBully 300 Polar | Deep Field Standby Hauler |
| `PB-06` | `PISTEN_BULLY` | Kässbohrer PistenBully 300 Polar | Reserve Chassis & Winter Maintenance |
| `SC-01` | `SNOW_SCOOTER` | Yamaha / Ski-Doo Utility Snowmobile | Fast Route Reconnaissance 01 |
| `SC-02` | `SNOW_SCOOTER` | Yamaha / Ski-Doo Utility Snowmobile | Fast Route Reconnaissance 02 |
| `SC-03` | `SNOW_SCOOTER` | Yamaha / Ski-Doo Utility Snowmobile | Field Camp Safety Patrol 03 |
| `SC-04` | `SNOW_SCOOTER` | Yamaha / Ski-Doo Utility Snowmobile | Station Perimeter Standby 04 |
| `TELEHANDLER-01`| `TELEHANDLER` | Manitou / JCB Rough-Terrain Telehandler | Container Yard Material Handling |
| `EXCAVATOR-01` | `EXCAVATOR` | Komatsu / Caterpillar Heavy Excavator | Heavy Snow Clearing / Earthmoving 01 |
| `EXCAVATOR-02` | `EXCAVATOR` | Komatsu / Caterpillar Heavy Excavator | Coastal Loading Site Support 02 |
| `BULLDOZER-01` | `BULLDOZER` | Komatsu / Caterpillar Tracked Dozer | Snow Road Grading & Berm Clearing |
| `MANTIS-01` | `MANTIS_CRANE` | Tadano Mantis 15010 Crawler Crane | Rough-Terrain Container Discharge 01 |
| `MANTIS-02` | `MANTIS_CRANE` | Tadano Mantis 15010 Crawler Crane | Station Heavy Assembly Lift 02 |

---

## 6. Technical Sensor Failure Modes

Every sensor supports simulated technical failure injection aligned with standard industrial telemetry failure modes:

- `DROPOUT`: `value = None`, `quality = FAILED`, `confidence = 0.0`, `valid = False`.
- `STALE`: `timestamp` frozen in the past beyond stale threshold, `quality = STALE`, `valid = False`.
- `OUT_OF_RANGE`: `value` forced beyond physical engineering limits, `quality = BAD`, `valid = False`.
- `STUCK`: `value` frozen at last known valid physical observation across steps (never defaulting back to `default_value`), `quality = BAD`, `valid = False`.
- `clear_failure(sensor_id)` and `clear_all_failures()`: restores normal reading and `GOOD` quality.

---

## 7. Operational Scenarios

The coupled simulation supports instant scenario activation via `registry.set_scenario(name)`:

1. **`NORMAL`**: Standard polar baseline, PB-01 standby, routes open, helipad clear, cold-chain nominal, condition NORMAL.
2. **`VEHICLE_BREAKDOWN`**: PB-01 engine coolant temp 105°C, status FAULT, fleet availability drops to 81.25%, condition CAUTION.
3. **`FUEL_SHORTAGE`**: Vehicle tank drops to 14.5%, dispenser disabled, critical alert triggered, stockout risk > 0.5.
4. **`COLD_CHAIN_EXCURSION`**: Reefer 01 compressor fault, door open, core temp rises to -4.5°C, excursion True, cold-chain risk 1.0.
5. **`BLIZZARD_LOGISTICS_RESTRICTION`**: Coupled 32.5 m/s wind, 50m visibility, helipad closed, routes blocked, traction 20%, condition RESTRICTED.
6. **`HEAVY_CARGO_OPERATION`**: Barge active shuttle, discharge progress 62%, telehandler and crane active, in-transit units 8.
7. **`MISSION_FIELD_DEPLOYMENT`**: Team 01 and Team 02 active, field pax 7, station pax 20.
8. **`INVENTORY_SHORTAGE`**: Spares drop below 30%, critical alerts count 3, stockout risk 0.72.

---

## 8. Verification & Execution

### Run Standalone Demo
```powershell
python tools/demos/bharati_logistics_sensor_demo.py
```

### Run Unit Tests
```powershell
python -m unittest discover -s tests/sensors/bharati/logistics -p "test_*.py" -v
```

### Run Full 4-Pillar Project Regression
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

All 146 project tests pass (Energy: 24, Infrastructure: 30, Environment: 42, Logistics: 50) with 0 failures and 0 errors.
