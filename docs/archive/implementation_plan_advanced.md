# F.R.I.D.A.Y. — Advanced Master Implementation Plan: Industrial Protocols, Space Weather, Dual-Station Mesh & Cognitive Innovations

> **Project**: F.R.I.D.A.Y. (Futuristic Resource Intelligence & Digital Assistant for Yearly operations)  
> **Problem Statement**: SIH26060 — Smart India Hackathon 2026  
> **Target Deployments**:  
> - **Bharati Station** (Larsemann Hills, East Antarctica — $69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$)  
> - **Maitri Station** (Schirmacher Oasis, East Antarctica — $70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$)  
> - **Mainland Operations**: National Centre for Polar and Ocean Research (NCPOR), Goa & MoES, New Delhi  
> **Role**: Senior Python Developer, Integrations Manager & Principal Bug Fixer  
> **Current Test Baseline**: **355/355 Pytest Tests Green** | **16/16 Vitest Tests Green** | **GitHub Actions CI/CD Green**  

---

## Architectural Philosophy & Ground Rules

1. **Edge-First Invariant**: All physical digital twin simulations, cognitive agents, safety interlocks, and hardware bridges must run 100% locally on-station with zero reliance on cloud or external WAN availability.
2. **Zero Regressions**: The existing 355 backend pytest test suite and 16 frontend vitest tests must remain strictly green after every single incremental commit.
3. **Event-Loop Purity**: Hardware protocol drivers (Modbus, OPC-UA, MQTT) must never block the main `asyncio` event loop. All network I/O must either use native asynchronous drivers (`asyncua`, `pymodbus.client.AsyncModbusTcpClient`) or be isolated in dedicated thread/process executors.
4. **Memory & Resource Bounding**: Polar edge servers run continuously for 12+ months unattended. All queues, ring buffers, and caches must have strict upper bounds (`maxlen`, time-based eviction) to eliminate memory leaks.
5. **Deterministic Safety Guardrails**: No cognitive agent or external protocol input may bypass the [SafetyInterlockManager](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/agents/framework/safety_interlock.py) life-support invariants.

---

## Master Phase Map

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   F.R.I.D.A.Y. NEXT-GEN ADVANCED ROADMAP                               │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 6: INDUSTRIAL SCADA, PLC & FIELDBUS PROTOCOL BRIDGES                                             │
│  ├── 6.1: Native Asynchronous Modbus TCP/RTU Master Bridge (Cummins/Woodward Gensets)                  │
│  ├── 6.2: Industrial OPC-UA (IEC 62541) Client/Server Gateway (Siemens S7 / Schneider PLCs)            │
│  ├── 6.3: MQTT v5 & Sparkplug B Edge Connector (LoRaWAN & Environmental Mesh)                          │
│  ├── 6.4: BACnet/IP Bridge (Building Management System & Utilidor Heat-Tracing)                        │
│  └── 6.5: Hardware-in-the-Loop (HIL) Virtual Fieldbus Simulator & Test Harness                        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 7: LIVE SPACE WEATHER & POLAR CRYOSPHERIC SATELLITE FEEDS                                        │
│  ├── 7.1: NOAA Space Weather Prediction Center (SWPC) Live Feed Engine (Kp, Solar Proton Flux)         │
│  ├── 7.2: Space-Weather-Driven Satcom Link Degradation & Preemptive Spooling Automaton                │
│  ├── 7.3: AMPS & ECMWF Polar Meteorological Ingestion (Katabatic Wind Vector Forecasting)              │
│  └── 7.4: Automated Emergency Weather Advisory Pipeline (NCPOR / MoES Dispatch)                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 8: MAITRI STATION SPECIALIZATION & 3,000 KM INTER-STATION HF MESH RELAY                         │
│  ├── 8.1: Dedicated Maitri Sensor Pillar Suite (MAI.* Namespace, Lake Priyadarshini Water Line)        │
│  ├── 8.2: 3,000 km Inter-Station HF PACTOR-4 Store-and-Forward Mesh Proxy                             │
│  ├── 8.3: Dual-Station Fleet Topology & Independent Actuator Governance                                │
│  └── 8.4: Verification Tests for Station Isolation, Failover & Telemetry Parity                        │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 9: AUTONOMOUS COGNITIVE INNOVATIONS & FIELD OPERATIONS                                           │
│  ├── 9.1: Physics-Informed Neural Network (PINN) for Deep-Freeze Utilidor Water Line Dynamics         │
│  ├── 9.2: Contract-Net Protocol (CNP) Multi-Agent Resource Micro-Auctions (Generator Trip Shedding)    │
│  ├── 9.3: SGP4 Polar LEO Satellite Orbit Propagator & Opportunistic Bursted Satcom Scheduler          │
│  ├── 9.4: Offline Hands-Free Voice AI Copilot (Whisper/Vosk API & Piper TTS) for Sub-Zero Maintenance  │
│  ├── 9.5: Autonomous "Cryo-Sleep" Station Survival State Machine                                       │
│  └── 9.6: Prometheus Exporter (/metrics) & OpenTelemetry (OTel) Distributed Tracing                    │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Implementation Plan (One by One)

---

### PHASE 6: Industrial SCADA, PLC & Fieldbus Protocol Gateways

#### 6.1: Native Asynchronous Modbus TCP/RTU Master Bridge
- **Objective**: Replace mock HTTP ingestion with a native asynchronous Modbus master that connects to physical generator controllers (Woodward AGC-4, Cummins PowerCommand 3.3) and electrical switchgear (Schneider Masterpact).
- **Files to Create/Modify**:
  - `backend/sensors/bridges/__init__.py`
  - `backend/sensors/bridges/modbus_bridge.py`
  - `backend/sensors/bridges/modbus_map.py` (Register address mapping table)
  - [backend/server/app.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/app.py) (Register bridge in lifespan)
  - [requirements.txt](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/requirements.txt) (Add `pymodbus>=3.6.0`)
- **Component Design**:
  ```python
  class ModbusTelemetryBridge:
      def __init__(self, host: str, port: int, register_map: dict[int, str], poll_interval: float = 1.0):
          self.client = AsyncModbusTcpClient(host=host, port=port)
          self.register_map = register_map  # Address -> Sensor ID (e.g. 30001 -> "BHARATI.CHP.01.ACTIVE_POWER")
          self._running = False
          
      async def start(self) -> None: ...
      async def poll_cycle(self) -> list[SensorReading]: ...
      async def write_coil(self, address: int, value: bool) -> bool: ...
  ```
- **Bug-Fixer Hardening**:
  - *Connection Churn & Event Loop Deadlock*: If a generator PLC goes offline, unhandled socket reconnection can freeze or spam exceptions. Solution: Implement exponential backoff ($1\text{s} \to 30\text{s}$) with jitter, non-blocking connect timeouts ($2.0\text{s}$), and circuit breaker isolation.
  - *Byte/Word Endianness*: Industrial PLCs vary between Big-Endian, Little-Endian, and Mid-Little (word swapped). Use `BinaryPayloadDecoder` with explicit configurable endianness per register group.

#### 6.2: Industrial OPC-UA Client/Server Gateway (IEC 62541)
- **Objective**: Provide bi-directional connectivity to Siemens S7-1500 and Schneider M340/M580 PLCs running the station's primary life-support automation.
- **Files to Create/Modify**:
  - `backend/sensors/bridges/opcua_bridge.py`
  - `backend/sensors/bridges/opcua_client.py`
  - [backend/server/routes/telemetry_ingest.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/routes/telemetry_ingest.py) (Add OPC-UA bridge status and diagnostics)
  - [requirements.txt](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/requirements.txt) (Add `asyncua>=1.1.0`)
- **Component Design**:
  - `AsyncUAClientManager`: Manages secure OPC-UA endpoint connections (`opc.tcp://`) with SecurityPolicy `Basic256Sha256` and user/password or X.509 cert authentication.
  - `SubscriptionHandler`: Inherits from `asyncua.common.subscription.SubHandler` to receive `datachange_notification` events asynchronously. Employs deadband filtering before injecting into `engine.inject_sensor_override()`.
- **Bug-Fixer Hardening**:
  - *Notification Flood*: If 200 sensors update simultaneously at 50 Hz, it can saturate the asyncio loop. Solution: Incoming readings are queued in an internal `asyncio.Queue(maxsize=1000)` and batched every 100ms into the digital twin.

#### 6.3: MQTT v5 & Sparkplug B Edge Connector
- **Objective**: Standardized ingestion for low-power wireless sensors (LoRaWAN base stations, environmental micro-stations, meteorological poles) using lightweight Sparkplug B binary encoding.
- **Files to Create/Modify**:
  - `backend/sensors/bridges/mqtt_bridge.py`
  - `backend/sensors/bridges/sparkplug_parser.py`
  - [requirements.txt](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/requirements.txt) (Add `aiomqtt>=2.0.0`, `protobuf>=4.25.0`)
- **Component Design**:
  - Listens to MQTT topic: `spBv1.0/Antarctica/DDATA/bharati/+`
  - Parses Protobuf payload into typed sensor metrics.
  - Tracks `NBIRTH` (Node Birth) and `NDEATH` (Node Death) to automatically update sensor quality flags (`GOOD` vs `BAD/OFFLINE`) in the digital twin.

#### 6.4: BACnet/IP Bridge for HVAC & Utilidor Trace Heating
- **Objective**: Interface with building automation systems controlling HVAC dampers, airflow heat recovery ventilators, and utilidor heat-tracing resistance circuits.
- **Files to Create/Modify**:
  - `backend/sensors/bridges/bacnet_bridge.py`
- **Component Design**:
  - UDP-based BACnet/IP Foreign Device Registration (port 47808).
  - Periodic `ReadPropertyMultiple` for Analog Inputs and `WriteProperty` for heating setpoint adjustments.

#### 6.5: Hardware-in-the-Loop (HIL) Virtual Fieldbus Simulator & Test Harness
- **Objective**: Provide automated integration testing so CI/CD runs virtual Modbus and OPC-UA servers without physical hardware.
- **Files to Create**:
  - `tools/virtual_modbus_server.py`
  - `tools/virtual_opcua_server.py`
  - `tests/sensors/test_industrial_bridges.py`
- **Verification Command**:
  ```bash
  python -m pytest tests/sensors/test_industrial_bridges.py -v
  ```

---

### PHASE 7: Live Space Weather & Polar Cryospheric Satellite Feeds

#### 7.1: NOAA Space Weather Prediction Center (SWPC) Live Feed Engine
- **Objective**: Continuously poll NOAA SWPC REST endpoints to ingest planetary geomagnetic index ($K_p$) and solar proton flux.
- **Files to Create/Modify**:
  - `backend/satcom/space_weather.py`
  - [backend/satcom/channel_emulator.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/satcom/channel_emulator.py) (Bind link quality to space weather metrics)
  - [backend/server/routes/satcom.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/routes/satcom.py) (Add `/api/satcom/space-weather` endpoint)
  - `tests/satcom/test_space_weather.py`
- **Component Design**:
  ```python
  class SpaceWeatherMonitor:
      SWPC_KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
      SWPC_PROTON_URL = "https://services.swpc.noaa.gov/json/proton_flux.json"
      
      def __init__(self, cache_ttl: float = 300.0): ...
      async def fetch_latest_space_weather(self) -> SpaceWeatherMetrics: ...
  ```
- **Data Model**:
  ```python
  class SpaceWeatherMetrics(BaseModel):
      kp_index: float                # 0.0 to 9.0 (>= 5 is Geomagnetic Storm)
      geomagnetic_storm_level: str   # G0 (Quiet) to G5 (Extreme)
      proton_flux_pfu: float         # Solar proton event threshold >= 10 pfu (S1 to S5)
      auroral_absorption_db: float   # Polar Cap Absorption in dB
      hf_radio_status: str           # NORMAL, DEGRADED, BLACKOUT
      predicted_bgan_margin_db: float
  ```

#### 7.2: Space-Weather-Driven Satcom Link Degradation & Preemptive Spooling
- **Objective**: When $K_p \ge 6$ or Solar Radiation Storm $\ge \text{S2}$, automatically trigger preemptive cloud sync before link collapse, and warn the operator of imminent polar blackout.
- **Implementation**:
  - In [state.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/state.py), connect `SpaceWeatherMonitor` to `PolarSatcomChannelEmulator`.
  - When storm conditions trigger:
    1. Channel emulator adjusts packet loss from $2\%$ to $45\%-90\%$ and latency from $850\text{ms}$ to $3500\text{ms}$.
    2. `SatcomDatabaseSyncWorker` executes an immediate expedited sync of pending emergency audit records (`Priority 0`).
    3. UI displays an `AURORAL SUBSTORM DETECTED` banner in the satcom dock.

#### 7.3: AMPS & ECMWF Polar Meteorological Ingestion
- **Objective**: Ingest Antarctic Mesoscale Prediction System (AMPS) forecast vectors to give cognitive agents 48-hour forward situational awareness.
- **Files to Create**:
  - `backend/core/weather_ingest.py`
  - `tests/core/test_weather_ingest.py`
- **Logic**:
  - Ingests forecasts for Larsemann Hills ($69.4^\circ\text{S}, 76.2^\circ\text{E}$) and Schirmacher Oasis ($70.8^\circ\text{S}, 11.7^\circ\text{E}$).
  - When forecasted wind $> 35\text{ m/s}$ (70 knots):
    - `SituationAwarenessAgent` publishes an early advisory: `KATABATIC_BLIZZARD_APPROACHING`.
    - `PlanningAgent` automatically schedules fuel transfer to generator day-tanks and elevates living quarters thermal buffer to $+22^\circ\text{C}$ to store heat.

---

### PHASE 8: Maitri Station Specialization & 3,000 km Inter-Station HF Mesh Relay

#### 8.1: Dedicated Maitri Sensor Pillar Suite
- **Objective**: Decouple Maitri from Bharati's sensor classes and implement Maitri's actual physical infrastructure.
- **Files to Create/Modify**:
  - `backend/sensors/maitri_sensors/__init__.py`
  - `backend/sensors/maitri_sensors/energy/` (3x 100 kVA Cummins Gensets, local switchgear)
  - `backend/sensors/maitri_sensors/environment/` (Schirmacher Oasis rocky permafrost, container habitat)
  - `backend/sensors/maitri_sensors/infrastructure/` (Lake Priyadarshini water pump line, 3 kW trace heater)
  - `backend/sensors/maitri_sensors/logistics/` (Maitri fuel tank farm, PistenBully fleet)
  - [backend/core/engine.py:517](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/core/engine.py#L517) (Instantiate `MaitriSensorRegistry`)
- **Key Sensor Modeling**:
  - `MAI.INFRA.LAKE_PRIYADARSHINI_PUMP_FLOW_LPM`: Potable water intake rate.
  - `MAI.INFRA.TRACE_HEATER_LINE_TEMP_C`: Prevents anchor ice in the lake intake strainer.
  - `MAI.ENERGY.GENSET.01.POWER_KW` through `03`: 3-genset cyclic rotation.

#### 8.2: 3,000 km Inter-Station HF PACTOR-4 Store-and-Forward Mesh Proxy
- **Objective**: If Maitri's satellite dish is damaged by blizzard winds, route telemetry to Bharati over High-Frequency (HF) radio mesh.
- **Files to Create**:
  - `backend/satcom/mesh_relay.py`
  - `tests/satcom/test_mesh_relay.py`
- **Protocol Design**:
  - Low-bitrate packet protocol ($2.4\text{ kbps}$ PACTOR-4 simulation).
  - Frames encoded using base64-compressed delta frames.
  - Bharati station receives packets, verifies HMAC, and forwards them to NCPOR Goa via Bharati's functional BGAN link.

---

### PHASE 9: Autonomous Cognitive Innovations & Field Operations

#### 9.1: Physics-Informed Neural Network (PINN) for Deep-Freeze Dynamics
- **Objective**: Edge neural surrogate modeling 1D thermal dissipation in utilidor water pipes to predict exact minutes-to-burst during total blackout.
- **Files to Create**:
  - `backend/core/pinn_freeze_model.py`
  - `tests/core/test_pinn_freeze.py`
- **Algorithm**:
  - Resolves Fourier heat conduction with convective surface cooling:
    $$T(t + \Delta t) = T(t) - \frac{U \cdot A}{M \cdot C_p} (T(t) - T_{\text{ext}}) \Delta t$$
  - Augmented with latent neural correction factor $\mathcal{N}_\theta(T_{\text{in}}, T_{\text{out}}, v_{\text{wind}})$ calibrated against historical Antarctic telemetry.
  - Returns `minutes_to_ice_crystallization` and `minutes_to_structural_pipe_rupture`.

#### 9.2: Contract-Net Protocol (CNP) Multi-Agent Resource Micro-Auctions
- **Objective**: Replace hardcoded load-shedding tables with autonomous market-based multi-agent negotiation.
- **Files to Create**:
  - `backend/agents/framework/auction.py`
  - [backend/agents/specialized/resource_optimizer.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/agents/specialized/resource_optimizer.py) (Add auctioneer role)
  - `tests/agents/test_resource_auction.py`
- **Deliberation Protocol**:
  1. *Call for Bids (CFP)*: `ResourceOptimizerAgent` broadcasts available budget: $45.0\text{ kW}$ total power.
  2. *Bidding*:
     - `MissionOpsAgent` bids for Life Support: $22.0\text{ kW}$ (Priority 1.0, Bid value $\infty$).
     - `MaintenanceAgent` bids for Trace Heating: $12.0\text{ kW}$ (Priority 0.9).
     - `PlanningAgent` bids for Science Labs: $15.0\text{ kW}$ (Priority 0.2).
  3. *Clearance*: Auction clears in $45\text{ms}$; Science Lab heater shed to $0\text{ kW}$, living quarters maintained.

#### 9.3: SGP4 LEO Orbit Propagator & Opportunistic Bursted Satcom Scheduler
- **Objective**: Predict LEO polar constellation (OneWeb / Starlink Polar) elevation angles and schedule compressed burst transmissions during peak visibility.
- **Files to Create**:
  - `backend/satcom/orbit_predictor.py`
  - `tests/satcom/test_orbit_predictor.py`
  - [requirements.txt](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/requirements.txt) (Add `sgp4>=2.23`)
- **Calculations**:
  - Computes topocentric coordinates (Azimuth, Elevation, Range) from Bharati ($69.4^\circ\text{S}, 76.2^\circ\text{E}$).
  - Triggers burst transmission only when $\text{Elevation} \ge 25^\circ$.

#### 9.4: Offline Hands-Free Voice AI Copilot for Sub-Zero Maintenance
- **Objective**: Allow technicians wearing heavy thermal mittens in -35°C generator bays to query F.R.I.D.A.Y. hands-free.
- **Files to Create/Modify**:
  - `backend/server/services/voice_service.py`
  - [backend/server/routes/copilot.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/routes/copilot.py) (Add `/api/copilot/voice-query` audio upload endpoint)
- **Engine**:
  - Integrates with local offline speech transcription (Whisper.cpp or Vosk small model) returning text transcript -> routed directly into [CommanderCopilotAgent](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/routes/copilot.py) -> response converted to audio via offline Piper TTS.

#### 9.5: Autonomous "Cryo-Sleep" Station Survival Protocol
- **Objective**: Extreme fail-safe state machine protecting station integrity if crew is evacuated or incapacitated.
- **Files to Create**:
  - `backend/core/cryo_sleep.py`
  - `tests/core/test_cryo_sleep.py`
- **Execution Actions**:
  - Automatically commands actuators to drain exterior potable water pipes into insulated basement holding tanks.
  - Closes aerodynamic storm dampers on all unpopulated container modules.
  - Configures gensets into an ultra-lean cyclic run-mode (run 2 hours on, 4 hours off) to preserve fuel for up to 60 days.

#### 9.6: Prometheus Exporter & OpenTelemetry Tracing
- **Objective**: Enterprise metrics and distributed tracing.
- **Files to Create/Modify**:
  - `backend/server/metrics.py`
  - [backend/server/app.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/app.py) (Mount `/metrics` endpoint)
  - [requirements.txt](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/requirements.txt) (Add `prometheus-client>=0.20.0`, `opentelemetry-api>=1.23.0`)

---

## Step-by-Step Execution Sequence & Milestones

| Step # | Milestone | Scope | Deliverables | Verification Criterion |
| :---: | :--- | :--- | :--- | :--- |
| **Step 1** | Modbus TCP Master Bridge | Phase 6.1 | `modbus_bridge.py`, `modbus_map.py` | Virtual Modbus server integration test passing. |
| **Step 2** | OPC-UA Gateway & MQTT | Phase 6.2–6.3 | `opcua_bridge.py`, `mqtt_bridge.py` | Monitored item updates streaming into digital twin. |
| **Step 3** | Space Weather & Storm Degradation | Phase 7.1–7.2 | `space_weather.py`, satcom integration | $K_p \ge 6$ triggers automated BGAN degradation and preemptive sync. |
| **Step 4** | Polar AMPS Weather Ingestion | Phase 7.3 | `weather_ingest.py`, agent alerts | Simulated blizzard advisory triggers generator pre-heat. |
| **Step 5** | Maitri Sensor Pillar Specialization | Phase 8.1 | `backend/sensors/maitri_sensors/` | Full 505 Maitri sensors in `MAI.*` namespace verified. |
| **Step 6** | 3,000 km Inter-Station HF Mesh | Phase 8.2 | `mesh_relay.py` | Telemetry proxied across simulated HF link during dish failure. |
| **Step 7** | PINN Deep-Freeze Predictor | Phase 9.1 | `pinn_freeze_model.py` | Real-time minute countdown to pipe freeze calculated. |
| **Step 8** | Multi-Agent Resource Micro-Auctions | Phase 9.2 | `auction.py`, `resource_optimizer.py` | Generator trip triggers $<50\text{ms}$ market clearance and load-shed. |
| **Step 9** | SGP4 LEO Orbit Propagator | Phase 9.3 | `orbit_predictor.py` | Pass elevation calculation and burst scheduler verified. |
| **Step 10** | Offline Voice Copilot & Cryo-Sleep | Phase 9.4–9.5 | `voice_service.py`, `cryo_sleep.py` | Audio query processed; cryo-sleep state machine transitions. |
| **Step 11** | Prometheus Metrics & Final E2E Suite | Phase 9.6 | `metrics.py`, full regression suite | All existing 355 tests + 50 new tests green (400+ total). |

---

## Senior Bug-Fixer Checklist & Risk Mitigations

```
+----------------------------------------------------------------------------------------------------+
|                                    BUG FIXER RISK MITIGATION MATRIX                                 |
+----------------------------------------------------------------------------------------------------+
| Risk / Potential Bug                  Root Cause                     Bug-Fixer Hardening Mechanism |
| ----------------------------------    ----------------------------   ----------------------------- |
| 1. Modbus Socket Hang                 PLC ungracefully drops socket  Set strict 2.0s connect/read   |
|                                       under polar cold vibration     timeout; wrap in asyncio task |
|                                                                                                    |
| 2. OPC-UA Event Loop Saturation       100 PLC tags change at 50 Hz   Incoming buffer queue + 100ms |
|                                       saturating Uvicorn loop        batch coalesce into twin      |
|                                                                                                    |
| 3. SWPC API Rate Limit / Downtime     External NOAA network drops    Cache metrics with 300s TTL;  |
|                                       or returns HTTP 429            fallback to quiet sun model   |
|                                                                                                    |
| 4. Circular HF Mesh Routing           Bharati and Maitri echo        Monotonic packet hop-count    |
|                                       packets back and forth         limit (TTL=2) + deduplication |
|                                                                                                    |
| 5. Auction Deadlock in Multi-Agent    Two agents submit equal bids   Deterministic tie-breaking    |
|                                       for same remaining kW          by life-support criticality   |
|                                                                                                    |
| 6. SGP4 Epoch Drift                   TLE data becomes stale after   Alert operator if TLE data is |
|                                       30 days in polar blackout      older than 14 days; degrade   |
+----------------------------------------------------------------------------------------------------+
```
