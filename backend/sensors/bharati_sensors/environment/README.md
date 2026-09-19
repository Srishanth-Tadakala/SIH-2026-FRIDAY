# Bharati Station Environment Observation Layer v1

Part of **SIH 2026 Project SIH26060: F.R.I.D.A.Y.**  
*Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations*

Target Station: **Bharati Station, Larsemann Hills, East Antarctica (69°24′29″S, 76°11′14″E)**

---

## 1. Executive Summary & Purpose

The **Bharati Environment Observation Layer v1** provides a scientifically grounded, physics-based, simulation-first telemetry layer capturing atmospheric, radiative, cryospheric, coastal, limnological, electrical, and scientific environmental phenomena surrounding Bharati Station.

It answers one core question:
> **“What is happening in the Antarctic environment around Bharati?”**

It does **NOT** answer:
> *“What should the operator do?”*

All diagnostic reasoning, optimization, forecasting, and automated control belong to future Agent and Digital Twin layers.

> [!IMPORTANT]
> **Strict Architectural Boundaries**:
> - Sensors are **NOT** the Digital Twin Core.
> - **Zero** Agents instantiated.
> - **Zero** REST/GraphQL APIs.
> - **Zero** Database persistence layers.
> - **Zero** UI / Dashboard components.
> - **Zero** LLM / AI reasoning calls.
> - **Zero** Message brokers / MQTT / Event buses.
> - **Zero** Forecasting models.

---

## 2. Core Architecture

```
                       BHARATI ENVIRONMENT
                  (Larsemann Hills, East Antarctica)
                                  │
                                  ▼
                  ENVIRONMENT PHYSICS STATE
             (BharatiEnvironmentPhysicsState: Ground Truth)
                                  │
         ┌──────────────┬─────────┴───┬─────────────┬──────────────┐
         ▼              ▼             ▼             ▼              ▼
      Weather       Radiation      Aerosol      Local Snow       Coastal
    Meteorology                 & Air Quality   (Station)        Sea Ice
         │              │             │             │              │
         ▼              ▼             ▼             ▼              ▼
    Coastal        Meltwater    Atm Electricity  Ionosphere      Sky &
    Context        Limnology       & Charges     Scintillation   Seismic
         │              │             │             │              │
         └──────────────┴─────────────┼─────────────┴──────────────┘
                                      ▼
                        ENVIRONMENT SENSOR LAYER
                (87 Simulated Telemetry Points Configured)
                        ├── Instrument Sensors
                        ├── State Sensors
                        └── Derived Sensors
                                      │
                                      ▼
                         ENVIRONMENT SENSOR REGISTRY
                   (EnvironmentSensorRegistry / Factory)
                                      │
                                      ▼
                           STANDARDIZED READINGS
                   (SensorReading: SIMULATED Provenance)
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼ (Read-Only)                ▼ (Read-Only)                ▼ (Read-Only)
   Infrastructure                Energy Sensor                   Logistics
  (EnvironmentalInput)             Interface                     Interface
         │                            │                            │
         ▼                            ▼                            ▼
  (Future Twin Core)           (Future Twin Core)           (Future Twin Core)
```

---

## 3. Simulation-First Principle & Provenance Discipline

Live telemetry to all Bharati scientific instrumentation is not publicly accessible. Therefore, this layer operates under strict provenance rules:

- Every reading emitted reports `provenance = SensorProvenance.SIMULATED`.
- Every reading emitted reports `source_reference = "bharati_environment_physics_v1"`.
- `event_time_seconds` defaults to `None` unless reporting a discrete physical event.
- **SIMULATED ≠ Random Fake Data**: Telemetry values are evaluated directly from a coupled, causal, multi-variable physics state (`BharatiEnvironmentPhysicsState`).
- **Future LIVE Adapter Compatibility**: The data contract (`SensorReading`) is designed so that a future physical telemetry adapter can inject real serial/Modbus/AWS readings without modifying downstream Digital Twin consumers.

---

## 4. Evidence Classification Discipline

To prevent engineering assumptions from being misrepresented as confirmed physical station hardware, every configured point carries an explicit `EvidenceLevel`:

| Evidence Level | Definition | Configured Points | Percentage |
| :--- | :--- | :---: | :---: |
| **`DOCUMENTED`** | Directly supported by NCPOR/Bharati public documentation or operational datasets (e.g. AWS met sensors, Aethalometer, Nephelometer, GNSS TEC, field mill). | 32 | 36.8 % |
| **`IMPLIED`** | Technically reasonable instrumentation associated with documented station observation programs, but exact telemetry addressing is not publicly confirmed. | 22 | 25.3 % |
| **`NOT_PUBLICLY_CONFIRMED`** | Useful Digital Twin parameter for which a physical Bharati sensor cannot be established from public evidence (e.g. coastal CTD moorings, wave radar). | 15 | 17.2 % |
| **`DERIVED`** | Mathematically calculated from underlying physical state variables (e.g. dew point, air density, wind chill, blizzard risk). | 18 | 20.7 % |
| **TOTAL** | **Simulated environmental telemetry points configured for the prototype** | **87** | **100.0 %** |

> [!WARNING]
> The project does **not** claim that every configured telemetry point corresponds to an installed physical sensor at Bharati Station.

---

## 5. Domain Breakdown & Sensor Catalogue (87 Points)

### Domain 1: WEATHER / METEOROLOGY (12 Points)
Station AWS mast observations:
- `ENV-WX-TEMP` (`degC`) [DOCUMENTED]: Ambient air temperature.
- `ENV-WX-RH` (`%`) [DOCUMENTED]: Ambient relative humidity.
- `ENV-WX-PRESS` (`hPa`) [DOCUMENTED]: Atmospheric barometric pressure.
- `ENV-WX-PRESS-TEND` (`hPa_3h`) [DERIVED]: 3-hour atmospheric barometric pressure tendency.
- `ENV-WX-WIND-S` (`m_s`) [DOCUMENTED]: 10m sustained wind speed.
- `ENV-WX-WIND-D` (`deg`) [DOCUMENTED]: Wind direction.
- `ENV-WX-GUST` (`m_s`) [IMPLIED]: Peak 3-second wind gust velocity.
- `ENV-WX-GUST-D` (`deg`) [IMPLIED]: Peak wind gust direction.
- `ENV-WX-VIS` (`m`) [NOT_PUBLICLY_CONFIRMED]: Horizontal atmospheric visibility.
- `ENV-WX-PRECIP-RATE` (`mm_h`) [IMPLIED]: Precipitation liquid-water-equivalent rate.
- `ENV-WX-DEW` (`degC`) [DERIVED]: Dew point temperature.
- `ENV-WX-DENS` (`kg_m3`) [DERIVED]: Moist air density.

### Domain 2: RADIATION & OPTICS (7 Points)
Radiation and atmospheric optical properties:
- `ENV-RAD-SW` (`W_m2`) [DOCUMENTED]: Downwelling shortwave global solar radiation.
- `ENV-RAD-LW` (`W_m2`) [IMPLIED]: Downwelling longwave atmospheric thermal radiation.
- `ENV-RAD-NET` (`W_m2`) [IMPLIED]: Net all-wave radiation balance.
- `ENV-RAD-UV` (`score`) [DOCUMENTED]: Solar ultraviolet index.
- `ENV-RAD-AOD` (`ratio`) [DOCUMENTED]: Aerosol optical depth at 500nm.
- `ENV-RAD-DAYLIGHT` (`bool`) [IMPLIED]: Astronomical daylight state.
- `ENV-RAD-SOLAR-AVAIL` (`%`) [DERIVED]: Solar energy generation availability factor.

### Domain 3: ATMOSPHERIC AEROSOL & AIR QUALITY (12 Points)
Aerosol laboratory and trace gas monitoring:
- `ENV-AIR-BC` (`ng_m3`) [DOCUMENTED]: Equivalent black carbon mass concentration (Aethalometer).
- `ENV-AIR-AERO` (`ug_m3`) [DOCUMENTED]: PM10 coarse particulate mass concentration.
- `ENV-AIR-PCOUNT` (`1_cm3`) [DOCUMENTED]: Total aerosol particle number density (CPC).
- `ENV-AIR-PSIZE` (`nm`) [IMPLIED]: Geometric mean particle diameter.
- `ENV-AIR-SCAT` (`1_Mm`) [DOCUMENTED]: Aerosol scattering coefficient at 550nm (Nephelometer).
- `ENV-AIR-ABS` (`1_Mm`) [DOCUMENTED]: Aerosol absorption coefficient at 880nm.
- `ENV-AIR-AOD` (`ratio`) [DOCUMENTED]: Total column aerosol optical depth.
- `ENV-AIR-CO` (`ppb`) [IMPLIED]: Carbon monoxide concentration.
- `ENV-AIR-NOX` (`ppb`) [IMPLIED]: Nitrogen oxides (NOx) concentration.
- `ENV-AIR-SO2` (`ppb`) [IMPLIED]: Sulfur dioxide concentration.
- `ENV-AIR-O3` (`ppb`) [NOT_PUBLICLY_CONFIRMED]: Surface tropospheric ozone.
- `ENV-AIR-QUALITY` (`%`) [DERIVED]: Clean air baseline purity index.

### Domain 4: SNOW & SEA ICE (11 Points)
Spatial distinction between local station snowpack and coastal sea ice:
- **Local Station Snowpack** (`location_scope="LOCAL_STATION"`, `measurement_zone="STATION_PERIMETER"`):
  - `ENV-SNOW-DEPTH` (`m`) [DOCUMENTED]: Local snow cover depth.
  - `ENV-SNOW-TEMP` (`degC`) [IMPLIED]: Snowpack temperature at 20cm depth.
  - `ENV-SNOW-DENS` (`kg_m3`) [IMPLIED]: Bulk snowpack density.
  - `ENV-SNOW-ACC` (`mm_h`) [IMPLIED]: Snow accumulation / ablation rate.
  - `ENV-SNOW-DRIFT` (`g_m2_s`) [IMPLIED]: Blowing snow horizontal mass transport flux.
- **Coastal Access Sea Ice** (`location_scope="COASTAL"`, `measurement_zone="COASTAL_STUDY_AREA"`):
  - `ENV-ICE-PRES` (`bool`) [DOCUMENTED]: Fast ice presence flag.
  - `ENV-ICE-THICK` (`m`) [IMPLIED]: Fast ice thickness.
  - `ENV-ICE-CONC` (`%`) [IMPLIED]: Coastal sea ice coverage fraction.
  - `ENV-ICE-TEMP` (`degC`) [IMPLIED]: Infrared radiometric ice surface temperature.
  - `ENV-ICE-DRIFT-S` (`m_s`) [NOT_PUBLICLY_CONFIRMED]: Pack ice drift speed.
  - `ENV-ICE-EDGE` (`km`) [NOT_PUBLICLY_CONFIRMED]: Distance to open water / ice lead edge.

### Domain 5: OCEAN & COASTAL CONTEXT (10 Points)
Coastal marine context (`location_scope="COASTAL_CONTEXT"`, `measurement_zone="PRYDZ_BAY_COASTAL"`):
- `ENV-OCEAN-TEMP` (`degC`) [NOT_PUBLICLY_CONFIRMED]: Surface seawater temperature.
- `ENV-OCEAN-SAL` (`PSU`) [NOT_PUBLICLY_CONFIRMED]: Practical seawater salinity.
- `ENV-OCEAN-COND` (`mS_cm`) [NOT_PUBLICLY_CONFIRMED]: Seawater electrical conductivity.
- `ENV-OCEAN-PRESS` (`dbar`) [NOT_PUBLICLY_CONFIRMED]: Hydrostatic subsurface pressure.
- `ENV-OCEAN-CURRENT-S` (`m_s`) [NOT_PUBLICLY_CONFIRMED]: Coastal current velocity.
- `ENV-OCEAN-CURRENT-D` (`deg`) [NOT_PUBLICLY_CONFIRMED]: Coastal current direction.
- `ENV-OCEAN-WAVE-H` (`m`) [NOT_PUBLICLY_CONFIRMED]: Significant wave height.
- `ENV-OCEAN-WAVE-P` (`s`) [NOT_PUBLICLY_CONFIRMED]: Peak wave spectral period.
- `ENV-OCEAN-LEVEL` (`m`) [NOT_PUBLICLY_CONFIRMED]: Tidal sea level anomaly.
- `ENV-OCEAN-TURB` (`NTU`) [NOT_PUBLICLY_CONFIRMED]: Seawater optical turbidity.

### Domain 6: ENVIRONMENTAL WATER / LIMNOLOGY (7 Points)
Natural proglacial/meltwater lakes (e.g. Lake Progress, Stepped Lake) — strictly separate from Infrastructure potable/RO systems:
- `ENV-WATER-TEMP` (`degC`) [DOCUMENTED]: Meltwater lake temperature.
- `ENV-WATER-PH` (`pH`) [DOCUMENTED]: Meltwater pH.
- `ENV-WATER-COND` (`uS_cm`) [DOCUMENTED]: Freshwater specific conductivity.
- `ENV-WATER-TURB` (`NTU`) [IMPLIED]: Meltwater stream turbidity.
- `ENV-WATER-DO` (`mg_L`) [IMPLIED]: Natural dissolved oxygen.
- `ENV-WATER-CONT` (`score`) [DERIVED]: Limnological contamination index.
- `ENV-WATER-HC` (`ppb`) [NOT_PUBLICLY_CONFIRMED]: Hydrocarbon trace fluorescence in runoff.

### Domain 7: ATMOSPHERIC ELECTRICITY (6 Points)
Atmospheric electricity laboratory observations:
- `ENV-ELEC-EFIELD` (`V_m`) [DOCUMENTED]: Atmospheric vertical electric field.
- `ENV-ELEC-AEC` (`pA_m2`) [DOCUMENTED]: Air-earth conduction current density.
- `ENV-ELEC-MAXWELL` (`pA_m2`) [IMPLIED]: Total Maxwell current density.
- `ENV-ELEC-POS` (`fS_m`) [IMPLIED]: Positive ion polar conductivity.
- `ENV-ELEC-NEG` (`fS_m`) [IMPLIED]: Negative ion polar conductivity.
- `ENV-ELEC-STATUS` (`status`) [DOCUMENTED]: System operational health state.

### Domain 8: SCIENTIFIC ENVIRONMENTAL CONTEXT (10 Points)
Ionospheric, optical sky, and seismological context:
- `ENV-IONO-TEC` (`TECU`) [DOCUMENTED]: Ionospheric Total Electron Content.
- `ENV-IONO-L1-AMP` (`ratio`) [DOCUMENTED]: L1 amplitude scintillation index S4.
- `ENV-IONO-L1-PHASE` (`rad`) [DOCUMENTED]: L1 phase scintillation sigma phi.
- `ENV-IONO-STATUS` (`status`) [DOCUMENTED]: Scintillation receiver lock state.
- `ENV-SKY-CLOUD` (`%`) [DOCUMENTED]: Cloud cover fraction.
- `ENV-SKY-AURORA` (`kR`) [DOCUMENTED]: 557.7nm auroral optical emission intensity.
- `ENV-SKY-IMAGE-STAT` (`status`) [DOCUMENTED]: All-sky camera dome/heating state.
- `ENV-SEIS-ACC` (`um_s2`) [DOCUMENTED]: Broadband ground acceleration.
- `ENV-SEIS-VEL` (`um_s`) [DOCUMENTED]: Ground particle velocity amplitude.
- `ENV-SEIS-EVENT` (`bool`) [DOCUMENTED]: Seismic event detected trigger.

### Domain 9: DERIVED ENVIRONMENTAL INDICATORS (12 Points)
All `kind = SensorKind.DERIVED`, `evidence_level = EvidenceLevel.DERIVED`:
- `ENV-DERIVED-DEWPOINT` (`degC`): Magnus dew point indicator.
- `ENV-DERIVED-AIR-DENSITY` (`kg_m3`): CIPM moist air density.
- `ENV-DERIVED-WIND-CHILL` (`degC`): JAG/TI wind chill index.
- `ENV-DERIVED-COLD-STRESS` (`score`): Outdoor cold stress index (0-100).
- `ENV-DERIVED-BLIZZARD-RISK` (`score`): Multi-factor blizzard severity index (0-100).
- `ENV-DERIVED-FREEZE-RISK` (`score`): External piping freeze threat index (0-100).
- `ENV-DERIVED-SNOW-ACCESS-RISK` (`score`): Ground access snow obstruction risk (0-100).
- `ENV-DERIVED-ICE-ACCESS-RISK` (`score`): Fast-ice trafficability risk (0-100).
- `ENV-DERIVED-SOLAR-AVAILABILITY` (`%`): Solar power generation potential factor.
- `ENV-DERIVED-VISIBILITY-RISK` (`score`): Whiteout disorientation risk (0-100).
- `ENV-DERIVED-ENVIRONMENTAL-RISK` (`score`): Composite threat index (0-100).
- `ENV-DERIVED-OPERATING-CONDITION` (`status`): Explainable operating severity category (`GREEN`, `YELLOW`, `RED`, `BLACK`).

---

## 6. Physical Coupling & Blizzard Formulation

### 1. Blowing Snow & Visibility Coupling
Blowing snow begins when wind exceeds ~10 m/s:
$$\text{Flux}_{drift} = \begin{cases} 0.045 \cdot (V - 10.0)^{2.2} \text{ g/m}^2/\text{s} & \text{if } V > 10.0 \text{ m/s} \\ 0.05 & \text{otherwise} \end{cases}$$

Visibility collapses under blowing snow and snowfall:
$$\text{Attenuation} = 1.0 + 0.75 \cdot \text{Flux}_{drift} + 2.2 \cdot \text{Rate}_{precip}$$
$$\text{Visibility} = \text{clamp}\left(\frac{18000.0}{\text{Attenuation}}, 25.0, 35000.0\right) \text{ m}$$

### 2. Multi-Factor Blizzard Risk Score
$$\text{Blizzard Risk} = \text{clamp}\left(100.0 \cdot \left(0.30 \cdot W_{sev} + 0.20 \cdot G_{sev} + 0.25 \cdot \text{Drift}_{sev} + 0.15 \cdot \text{Vis}_{sev} + 0.10 \cdot P_{sev}\right), 0, 100\right)$$

### 3. Explainable Operating Condition State
Preserves contributing causal reasons rather than behaving as an opaque string:
- `BLACK`: Blizzard Risk $\ge 70$, or Wind $\ge 30 \text{ m/s}$, or Visibility $< 300 \text{ m}$ (Reasons: `["BLIZZARD_CONDITIONS", "SEVERE_GALE_FORCE_WIND", "NEAR_ZERO_VISIBILITY"]`).
- `RED`: Wind $\ge 22 \text{ m/s}$, or Visibility $< 1000 \text{ m}$, or Temp $< -32 \text{ }^\circ\text{C}$ (Reasons: `["HIGH_WIND", "LOW_VISIBILITY", "EXTREME_COLD"]`).
- `YELLOW`: Wind $\ge 15 \text{ m/s}$, or Visibility $< 2000 \text{ m}$, or Temp $< -25 \text{ }^\circ\text{C}$ (Reasons: `["MODERATE_WIND", "REDUCED_VISIBILITY", "COLD_TEMPERATURE"]`).
- `GREEN`: Wind $< 15 \text{ m/s}$, Visibility $\ge 2000 \text{ m}$, Temp $\ge -25 \text{ }^\circ\text{C}$ (Reasons: `["NOMINAL_CONDITIONS"]`).

---

## 7. Technical Failure Simulation & Recovery

The layer models 4 canonical technical sensor faults without corrupting physical reality:
- `DROPOUT`: `value = None`, `quality = FAILED`, `valid = False`, `confidence = 0.0`.
- `STALE`: `timestamp` frozen in the past, `quality = STALE`, `valid = False`, `confidence = 0.4`.
- `OUT_OF_RANGE`: `value` forced outside `[min_value, max_value]`, `quality = BAD`, `valid = False`, `confidence = 0.2`.
- `STUCK`: `value` frozen at last known physical reading (not `default_value`), `quality = BAD`, `valid = False`, `confidence = 0.5`.
- `clear_failure()` / `clear_all_failures()`: restores normal reading and `GOOD` quality.

---

## 8. Cross-Pillar Read-Only Interfaces

- **`to_infrastructure_environmental_input()`**: Emits standard `EnvironmentalInput` instance (ambient temp, wind speed, wind direction, solar radiation, pressure, humidity, snowfall rate) to drive Infrastructure thermal dynamics.
- **`get_infrastructure_environmental_extended()`**: Exposes snow depth, freeze risk, and visibility.
- **`get_energy_environmental_interface()`**: Exposes ambient temperature, solar radiation, wind speed, solar availability, and operating severity level to drive Energy models.
- **`get_logistics_environmental_interface()`**: Exposes wind, visibility, snow depth, sea ice thickness/drift, wave height, ice access risk, and composite environmental risk for future logistical routing.

---

## 9. Verification & Regression Guarantee

The test suite contains **42 comprehensive unit tests** in `tests/sensors/bharati/environment/test_environment_sensors.py`.

Full project regression test run:
```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
Results:
- Energy Tests: 24 passed
- Infrastructure Tests: 30 passed
- Environment Tests: 42 passed
- **Total: 96 tests passed (0 failures, 0 errors)**
