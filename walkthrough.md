# Walkthrough - Bharati Station Sensor Pillars (Energy, Infrastructure, Environment, Logistics)

**Project**: SIH 2026 SIH26060: F.R.I.D.A.Y. (“Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations”)  
**Target Station**: Bharati Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E)

---

## 4-Pillar Observation Layer Status Overview

All four operational observation pillars of the Bharati Station digital twin are now fully implemented, verified, and passing regression testing:

| Pillar | Subsystem / Package | Configured Points | Domains | Unit Tests | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Pillar 1: Energy** | `backend.sensors.bharati_sensors.energy` | 48 | 6 | 24 | ✅ Complete |
| **Pillar 2: Infrastructure** | `backend.sensors.bharati_sensors.infrastructure` | 180 | 11 | 30 | ✅ Complete |
| **Pillar 3: Environment** | `backend.sensors.bharati_sensors.environment` | 87 | 9 | 42 | ✅ Complete |
| **Pillar 4: Logistics** | `backend.sensors.bharati_sensors.logistics` | 98 | 11 | 50 | ✅ Complete |
| **TOTALS** | **4 Operational Pillars** | **413** | **37** | **146** | **100% Green** |

---

## Pillar 4 Implementation: Bharati Station Logistics Observation Layer v1

### Architecture Summary

The **Logistics Observation Layer** completes the four observation pillars of the platform, strictly maintaining the sensor-only boundary:

```
                       BHARATI LOGISTICS
              (Station, Field Routes, Coastal Berth)
                                │
                                ▼
                 LOGISTICS PHYSICS / SYSTEM STATE
           (BharatiLogisticsPhysicsState: Ground Truth)
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

## 1. Files Created for Logistics Layer

| File | Description |
| :--- | :--- |
| [`models.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/models.py) | Data classes and enums: `LogisticsDomain` (11 domains), `EvidenceLevel`, `SensorProvenance`, `SensorKind`, `SensorQuality`, `FailureType`, `PhysicalQuantity`, `LogisticsConditionState`, `FleetAssetInfo`, `SensorConfig`, `SensorReading`. |
| [`config.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/config.py) | Declarative configuration table for all 98 observation points, 16 physical fleet assets (`FLEET_ASSET_REGISTRY`), ASCII units, state paths, and catalogue validator. |
| [`physics_state.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/physics_state.py) | `BharatiLogisticsPhysicsState` coupled simulation ground truth with 11 domain sub-states, scenarios (`NORMAL`, `VEHICLE_BREAKDOWN`, `FUEL_SHORTAGE`, `COLD_CHAIN_EXCURSION`, `BLIZZARD_LOGISTICS_RESTRICTION`, `HEAVY_CARGO_OPERATION`, `MISSION_FIELD_DEPLOYMENT`, `INVENTORY_SHORTAGE`), and strictly read-only cross-pillar interfaces. |
| [`base.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/base.py) | Base classes (`BaseLogisticsSensor`, `StateBoundLogisticsSensor`, `DerivedLogisticsSensor`) and technical fault injection (`DROPOUT`, `STALE`, `OUT_OF_RANGE`, `STUCK` with last known reading preserved). |
| [`fleet.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/fleet.py) | Builder for 16 fleet telemetry and operational status points (lead hauler PB-01 speed, heading, rpm, temp, fuel level, fuel rate, battery, engine hours, status, plus support vehicle statuses). |
| [`cargo.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/cargo.py) | Builder for 10 cargo and container observation points (total count, in-transit, C01 location, weight record, internal temp/hum, shock, tilt, door seal, hazmat staging). |
| [`fuel.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/fuel.py) | Builder for 10 fuel logistics points (helicopter supply context, vehicle bulk tank, line temp/pressure, transfer flow rate, daily dispensed, bund leak monitor, dispenser status). |
| [`cold_chain.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/cold_chain.py) | Builder for 8 cold-chain reefer points (Reefer 01 core temp, setpoint, door, compressor run, power source, thermal excursion indicator, Reefer 02 chilled stores). |
| [`aviation.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/aviation.py) | Builder for 7 aviation logistics points (helicopter status, airborne state, fuel %, altitude, ground speed, cumulative flight hours, station helipad status). |
| [`marine.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/marine.py) | Builder for 7 marine logistics points (expedition ship status, distance to station, AIS speed, offloading barge status, discharge progress %, coastal sea-berth safety, unloading rate). |
| [`routes.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/routes.py) | Builder for 8 route accessibility points (station ring, helipad track, coastal link, fast-ice route, Larsemann inter-station corridor, visibility limitation, crevasse hazard, surface traction index). |
| [`missions.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/missions.py) | Builder for 9 mission coordination points (active missions, muster counts on-station and in field, anonymous teams `TEAM-FIELD-01` and `TEAM-FIELD-02`, return margin minutes, radio checks, readiness index). |
| [`inventory.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/inventory.py) | Builder for 10 inventory stores points (rations autonomy days, rations stock %, medical stock status, generator spares %, vehicle spares %, water treatment spares %, battery reserves, PPE gear %, critical alerts, stockout risk). |
| [`waste.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/waste.py) | Builder for 5 waste containment points under the **Madrid Protocol** (solid volume, solid storage %, hazard volume, hazard containment status, Madrid Protocol return shipment readiness %). |
| [`derived.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/derived.py) | Builder for 8 derived operational indicators (fleet availability %, cargo integrity %, cold-chain risk, ground route access %, aviation access %, marine access %, composite logistics risk, explainable condition summary). |
| [`registry.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/registry.py) | Central `LogisticsSensorRegistry` for sensor lookup, readouts, stepping, scenario switching, and failure management. |
| [`factory.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/factory.py) | Layer assembly (`create_bharati_logistics_sensors`). |
| [`__init__.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/__init__.py) | Clean package exports. |
| [`README.md`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/sensors/bharati_sensors/logistics/README.md) | Authoritative technical documentation, catalogue breakdown, and usage. |
| [`test_logistics_sensors.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/tests/sensors/bharati/logistics/test_logistics_sensors.py) | 50 comprehensive unit tests covering all verification criteria. |
| [`bharati_logistics_sensor_demo.py`](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/tools/demos/bharati_logistics_sensor_demo.py) | Standalone interactive demonstration and boundary audit script. |

---

## 2. Sensor Summary (98 Points Across 11 Domains)

| Domain | Observation Points | Key Sensors |
| :--- | :---: | :--- |
| **FLEET & VEHICLES** | 16 | PB-01 Speed, Heading, RPM, Coolant Temp, Fuel Level, Fuel Rate, Battery, Hours, Status; PB-02 Status; SC-01 Status & Fuel; Telehandler Pressure & Status; Excavator Status; Mantis Crane Status. |
| **CARGO & CONTAINERS** | 10 | Total Units, In-Transit Units, C01 Location Zone, Weight Record, Temp, Humidity, Shock Accelerometer, Tilt Inclinometer, Door Seal, Hazmat Compliance. |
| **FUEL LOGISTICS** | 10 | Heli Supply Level & %, Vehicle Tank Level & %, Line Temp, Line Pressure, Transfer Flow Rate, Daily Dispensed Log, Sump Leak Monitor, Dispenser Status. |
| **COLD CHAIN (REEFERS)** | 8 | Reefer 01 Core Temp, Setpoint, Door Status, Compressor Run, Power Source (Grid/Genset), Thermal Excursion Boolean, Reefer 02 Temp & Status. |
| **AVIATION LOGISTICS** | 7 | Helicopter Flight Status, Airborne State, Fuel %, Altitude, Ground Speed, Cumulative Flight Hours, Station Helipad Status. |
| **MARINE LOGISTICS** | 7 | Expedition Vessel Status, Distance to Station, AIS Speed, Offloading Barge Status, Voyage Discharge %, Coastal Sea Berth Safety, Unloading Rate. |
| **ROUTES & ACCESSIBILITY** | 8 | Station Ring Road, Helipad Track, Coastal Link, Fast-Ice Heavy Traverse, Larsemann Inter-Station Route, Visibility Limitation, Crevasse Hazard, Surface Traction Index. |
| **MISSIONS & PERSONNEL** | 9 | Active Missions Count, Station Muster, Field Pax, Team 01 Status, Distance, Radio Check, Return Margin Minutes, Team 02 Status, Readiness Index. |
| **INVENTORY & STORES** | 10 | Rations Autonomy Days, Rations Stock %, Medical Supplies Status, Generator Spares %, Vehicle Spares %, Water Treatment Consumables %, Battery Reserves, PPE Gear %, Stockout Alerts Count, Stockout Risk Score. |
| **WASTE RETURN (MADRID)**| 5 | Compacted Solid Waste Volume & %, Drummed Hazardous Waste Volume & Containment Status, Madrid Protocol Return Shipment Readiness %. |
| **DERIVED INDICATORS** | 8 | Fleet Availability %, Cargo Integrity Index, Cold-Chain Risk Score, Ground Route Access %, Aviation Access %, Marine Access %, Composite Logistics Risk, Explainable Condition Summary. |
| **TOTAL** | **98** | **Exact Count Configured & Verified** |

---

## 3. Key Technical Corrections Incorporated

1. **Exact 98 vs 108 Count Inconsistency Resolved**:
   - Reclassified 10 low-value or duplicative environmental observations out of the Logistics sensor catalogue.
   - Exact count locked at **98 configured points** across **11 domains** (10 operational domains + 1 derived domain).
2. **Formal Anti-Duplication Rule**:
   - Logistics **MUST NOT** independently simulate ambient environmental observations (wind, snow depth, sea ice concentration, ice thickness).
   - Logistics consumes those observations strictly via read-only interfaces from Environment and evaluates route trafficability, helipad operating status, and sea berth safety.
3. **Fleet Asset Registry Separation**:
   - All 16 documented Bharati fleet machines tracked in `FLEET_ASSET_REGISTRY` (`PB-01` to `PB-06`, `SC-01` to `SC-04`, `TELEHANDLER-01`, `EXCAVATOR-01`, `EXCAVATOR-02`, `BULLDOZER-01`, `MANTIS-01`, `MANTIS-02`).
   - Standardized telemetry profiles for the lead machine with status observation points for support machines.
4. **Sensor Taxonomy & Evidence Discipline**:
   - Derived indices (`stockout_risk`, `surface_traction`, `return_margin`, `excursion`) are typed `SensorKind.DERIVED`.
   - Inventory records and cargo weights are typed `SensorKind.STATE`.
   - Live CAN-bus/GPS, reefer temperature telemetry, and helicopter fuel levels are classified as `NOT_PUBLICLY_CONFIRMED`; physical assets and capabilities are `DOCUMENTED`.
5. **Helicopter Fuel Supply Context**:
   - Replaced assumptions of a dedicated physical station heli-tank with `fuel.heli_supply_level_l` / `fuel.heli_supply_percent` representing aviation supply context.
6. **Madrid Protocol Terminology**:
   - Accurately named the **Protocol on Environmental Protection to the Antarctic Treaty (Madrid Protocol)**.
7. **Privacy Discipline**:
   - Anonymous operational groups (`TEAM-FIELD-01`, `TEAM-FIELD-02`) with explicit return margin semantics (`return_margin_minutes`), with zero personal PII.
8. **State-Bound vs Default Value Invariant**:
   - Verified that healthy state-bound sensors resolve exclusively from `BharatiLogisticsPhysicsState`; `default_value` is fallback-only.

---

## 4. Verification Results

### Unit Test Execution
```powershell
python -m unittest discover -s tests/sensors/bharati/logistics -p "test_*.py" -v
```
- **Result**: 50/50 tests PASS in 0.053s.

### Full 4-Pillar Regression Test Execution
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
- **Result**: 146/146 tests PASS in 0.229s across all 4 pillars:
  - Energy: 24 tests PASS
  - Infrastructure: 30 tests PASS
  - Environment: 42 tests PASS
  - Logistics: 50 tests PASS
  - Total: 146 tests, 0 failures, 0 errors.

### Standalone Demonstration Execution
```powershell
python tools/demos/bharati_logistics_sensor_demo.py
```
- Output verified:
  - Exact 98 points across 11 domains.
  - 16 documented fleet machines listed from registry.
  - 100% `SIMULATED` provenance and source reference.
  - Baseline snapshot across fleet, cargo, fuel, reefers, aviation, marine, routes, missions, inventory, waste, and derived indicators.
  - Successful scenario transitions: `VEHICLE_BREAKDOWN`, `COLD_CHAIN_EXCURSION`, `BLIZZARD_LOGISTICS_RESTRICTION`.
  - Injected fault handling: `DROPOUT`, `STUCK`, `STALE`, `OUT_OF_RANGE` and recovery.
  - Read-only environmental integration demonstrated.
  - 16-point boundary audit confirmed with zero non-sensor components.
