# Bharati Station Infrastructure Sensor Layer v1

Part of **SIH 2026 Project SIH26060**: *Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations (F.R.I.D.A.Y.)*.

---

## 1. Scope & Architectural Boundary

The **Bharati Infrastructure Sensor Layer** simulates physical telemetry for the 11 mission-critical sub-facilities of India's Bharati Station, Larsemann Hills, East Antarctica (69°24′29″ S, 76°11′14″ E).

```
  ┌────────────────────────────────────────────────────────┐
  │         ENVIRONMENT (External Boundary Inputs)         │
  │     (Ambient Temp, Wind Speed, Solar, Snowfall)        │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │     BHARATI INFRASTRUCTURE COUPLED PHYSICS STATE       │
  │   - Building Envelope Thermodynamics (UA=1850 W/K)     │
  │   - Structural Mechanics (86 Stilts, Bedrock Anchor)   │
  │   - HVAC Psychrometrics & Occupant CO2 Mass Balance    │
  │   - RO Desalination & Potable Water Mass Conservation  │
  │   - MBR Wastewater Biological & Hydraulic Treatment    │
  │   - Fire & Smoke Generation (4 Independent Zones)      │
  │   - Deep Freeze & Chiller Refrigeration Cycles         │
  │   - Trace-Heated External Utilidor Pipelines           │
  │   - Emergency Standby Shelter Life-Support Reserves    │
  │   - Access Control & Intrusion Detection Hardware      │
  │   - BMS Network Latency & Satellite Telecommunications │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │               SENSOR ABSTRACTION LAYER                 │
  │     (Instrument Sensors, State Sensors, Derived)       │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │             INFRASTRUCTURE SENSOR REGISTRY             │
  │     (Registry, Fault Injection, Telemetry Readout)     │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼
               Standardized Sensor Readings
              (Future Infrastructure Agent)
```

### Strict Non-Goals Enforced in v1:
- ❌ **NO Infrastructure Agent** (no automated diagnosis, planning, or dispatch).
- ❌ **NO Orchestrator / F.R.I.D.A.Y. Core**.
- ❌ **NO REST / GraphQL / WebSocket APIs**.
- ❌ **NO SQLite / Postgres / Time-Series DB persistence**.
- ❌ **NO MQTT / Kafka / Event Bus**.
- ❌ **NO UI / Web Dashboard / Visual Frontend**.
- ❌ **NO LLM / AI Reasoning / Predictive Optimization**.
- ❌ **NO Mutation of Energy Layer** (clean, read-only auxiliary power interface only).

---

## 2. NCPOR Factual Grounding vs. Simulation Assumptions

### Authoritative Documented Station Facts (NCPOR):
* **Main Building**: Elevated 3-tier aerodynamic intelligent superstructure composed of **134 prefabricated shipping-container sized modules**.
* **Elevated Foundation**: Supported on **86 heavy-duty structural steel pillars** to elevate the structure ~4–5 m above bedrock and mitigate snow drift accumulation.
* **BMS Architecture**: Over **1,000 configured data points** and ~180 field devices interconnected via high-reliability industrial automation networks.
* **Fire Safety**: Central addressable panel coordinating **~230 smoke detectors**, optical flame sensors, motorized dampers, and inert gas suppression.
* **Water & Sanitation**: Dedicated seawater intake feeding **Reverse Osmosis (RO)** desalination and biological **Membrane Bioreactor (MBR)** wastewater recycling.
* **External Utilidors**: Insulated and **electrically trace-heated utilidors** bridging the main station with fuel storage tanks and generator houses.

### Explicit Simulation Assumptions:
* Gross interior volume: $8,500\text{ m}^3$ with envelope UA factor of $1,850\text{ W/K}$.
* Potable water reservoir capacity: $25,000\text{ L}$ with rated RO permeate production of $600\text{ L/h}$.
* Deep freeze setpoint: $-22.0^\circ\text{C}$ (configurable target); provisions chiller: $+3.0^\circ\text{C}$ (configurable target).
* Nominal expedition headcount: $22$ winter/summer base personnel.
* Asset identifiers (`AHU-01`, `DDC-01`, etc.) are designated digital-twin modeling conventions.

---

## 3. Sensor Taxonomy & Domain Breakdown (180 Total Sensors)

| Domain | Sensors | Evidence Level | Primary Quantities Monitored |
| :--- | :---: | :--- | :--- |
| **1. Building & Structural** | 18 | `DOCUMENTED` / `NOT_PUBLICLY_CONFIRMED` | Indoor zone temps, envelope facade temps, aerodynamic snow load, inclinometer tilt, 86-pillar axial strain, foundation bedrock displacement. |
| **2. HVAC & Air Quality** | 26 | `IMPLIED` | AHU supply/return temps, static pressure, filter bank differential pressure, airflow, fan speed, heating valve, economizer dampers, indoor $\text{CO}_2$, $\text{CO}$. |
| **3. Water Intake & RO** | 18 | `DOCUMENTED` / `IMPLIED` | Seawater intake flow, pressure, temp, pump status, RO feed pressure, permeate flow, reject flow, conductivity, potable tank volume & level %, distribution flow. |
| **4. Wastewater (MBR)** | 18 | `IMPLIED` | Inlet sewage flow, grey/black/galley sump levels, aeration basin DO, blower status, membrane TMP, effluent COD, BOD, ammonia, pH, outfall valve. |
| **5. Fire & Safety** | 16 | `DOCUMENTED` / `IMPLIED` | Multi-zone smoke obscuration, thermal sensors, alarm status, motorized duct isolation dampers. |
| **6. Refrigeration** | 16 | `IMPLIED` | Deep freeze & cool room temperatures, evaporator/condenser temps, suction/discharge pressures, door contact switches, compressor run status, alarms. |
| **7. Utilidors & Pipelines**| 16 | `DOCUMENTED` / `IMPLIED` | Water, fuel, and hydronic heat loop pipe wall temperatures, pressures, flows, trace heating run status, leak detection alarms, main isolation valve. |
| **8. Emergency Shelter** | 11 | `DOCUMENTED` / `IMPLIED` | Refuge indoor temp, humidity, occupancy headcount, standalone backup generator status, fuel level, autonomous boiler temp, emergency water tank level. |
| **9. Security & Access** | 11 | `IMPLIED` | Main airlock door/lock status, powerhouse door/lock, fuel farm gate, CCTV operational status, emergency call station health, key vault security. |
| **10. BMS & Automation** | 12 | `DOCUMENTED` / `IMPLIED` | DDC-01/02 online status, fieldbus gateway, historian, online/stale/failed BMS point counters, fieldbus latency, satellite communications SNR & RTT latency. |
| **11. Virtual Indicators**| 18 | `DERIVED` | Building heat loss (kW), zone temp deviation, occupancy density, HVAC thermal load, ventilation effectiveness, air quality index, potable reserve days, RO recovery ratio, WWTP efficiency, cold storage risk, refrigeration COP, pipe freeze risk, pipe leak risk, structural condition score, foundation displacement score, BMS telemetry health (%), total auxiliary electrical power (kW). |

---

## 4. Evidence Hierarchy & Provenance

Every reading rigorously specifies its provenance and evidentiary grounding:

```python
class EvidenceLevel(str, Enum):
    DOCUMENTED = "DOCUMENTED"                    # Authoritative NCPOR specification / fact
    IMPLIED = "IMPLIED"                          # Standard Antarctic engineering practice
    NOT_PUBLICLY_CONFIRMED = "NOT_PUBLICLY_CONFIRMED" # Modeled structural telemetry
    DERIVED = "DERIVED"                          # Analytical calculation from other states
```

- **Physical Facts vs Sensor Evidence**: 134 modular containers and 86 steel stilts are documented physical facts. Sensors observing structural tilt, pillar axial strain, and foundation displacement are explicitly tagged `NOT_PUBLICLY_CONFIRMED`.
- **Deterministic Confidence**: Fixed non-random assignment:
  - `DOCUMENTED`: `1.0`
  - `IMPLIED`: `0.90`
  - `DERIVED`: `0.85`
  - `NOT_PUBLICLY_CONFIRMED`: `0.75`
- **Provenance Discipline**: Strictly `SensorProvenance.SIMULATED` with `source_reference = "bharati_infrastructure_physics_v1"`.

---

## 5. Coupled Physical Simulation Models

1. **Water Mass Balance Integration**:
   $$V(t+1) = V(t) + \left(Q_{\text{permeate}} - Q_{\text{consumption}}\right) \times \Delta t$$
   $$Q_{\text{intake}} = Q_{\text{permeate}} + Q_{\text{reject}} + Q_{\text{flush\_losses}}$$
   $$\text{Level } (\%) = \left(\frac{V(t)}{V_{\text{capacity}}}\right) \times 100$$
2. **Potable Water $\to$ Wastewater Coupling**:
   Station potable consumption dynamically feeds MBR sewage influent ($\approx 85\%$ grey/blackwater generation).
3. **Biological Treatment Degradation**:
   Aeration blower failure triggers rapid dissolved oxygen depletion ($1.2\text{ mg/L/h}$) and exponential effluent COD/BOD/ammonia degradation.
4. **Fire Combustion & Isolation**:
   Local heat and smoke generation trip optical detectors ($\text{smoke} > 15\%$, $T > 57^\circ\text{C}$), automatically actuating motorized fire dampers closed.
5. **Refrigeration Thermodynamics**:
   Configurable target setpoints ($-22^\circ\text{C}$, $+3^\circ\text{C}$) drive dynamic compressor cycling. Door openings induce convective warm air infiltration.
6. **Auxiliary Electrical Power Interface**:
   Read-only interface `calculate_total_auxiliary_power_kw()` aggregates HVAC, pumps, compressors, and trace heating loads ($\approx 35\text{--}80\text{ kW}$) without modifying Energy layer state.

---

## 6. Verification & Demonstration

### Run Comprehensive Unit Tests:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
*(All 54 tests pass across both Energy and Infrastructure).*

### Run Standalone Interactive Demo:
```powershell
python tools/demos/bharati_infrastructure_sensor_demo.py
```
Demonstrates baseline telemetry snapshot, Antarctic blizzard response, fault injection (`DROPOUT`, `STUCK`), fault recovery, and strict boundary isolation audit.
