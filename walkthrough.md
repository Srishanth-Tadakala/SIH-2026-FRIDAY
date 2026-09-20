# Walkthrough: Sub-Phase 4.1 Implementation (FastAPI Engine Core & Dual-Station REST Endpoints)

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: 
- **Bharati Station** (Larsemann Hills, East Antarctica — $69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$)
- **Maitri Station** (Schirmacher Oasis, East Antarctica — $70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$)
- **Mainland Command**: National Centre for Polar and Ocean Research (NCPOR), Goa & MoES, New Delhi  

**Status**: 
- **Phase 1**: Digital Twin Core & Causal Graph Engine (Completed & Verified — 14 tests)  
- **Phase 2**: Multi-Agent Message Bus & Safety Interlocks (Completed & Verified — 11 tests)  
- **Phase 3**: All 10 Specialized Cognitive Agents (Completed & Verified — 72 tests)  
- **Phase 4 (In Progress)**:
  - **Sub-Phase 4.1**: FastAPI Engine Core & Dual-Station REST Endpoints (**Completed & Verified — 10 tests**)  
  - **Sub-Phase 4.2**: Polar Satcom Delta-Sync Protocol (Pending Approval)  
  - **Sub-Phase 4.3**: Multiplexed WebSocket Streaming Engine (Pending Approval)  
**Total Test Results**: **253 passed (0 failures, 0 errors, 100% green)**.

---

## 1. Complete Multi-Tiered Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       F.R.I.D.A.Y. CHIEF AI PLATFORM                                    │
│                                           (100% Offline Polar AI)                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. REACT FLOW DIGITAL TWIN FRONTEND (Future Phase)                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. HEADLESS SERVER & SATCOM BANDWIDTH-AWARE DELTA SYNC ENGINE                                           │
│  ├── [COMPLETED] Sub-Phase 4.1: FastAPI Engine Core & Dual-Station REST API                             │
│  │   • /api/health           • /api/stations       • /api/telemetry/{sid}                              │
│  │   • /api/agents           • /api/deliberations  • /api/actions            • /api/scenarios           │
│  ├── [NEXT] Sub-Phase 4.2: Polar Satcom Bandwidth-Aware Protocol (Deadband + Compression + Spool)       │
│  └── [NEXT] Sub-Phase 4.3: Real-Time Multiplexed WebSocket Streaming Engine                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. F.R.I.D.A.Y. MULTI-AGENT COGNITIVE ARCHITECTURE (ALL 10 AGENTS COMPLETE — 72 Tests)                   │
│    [10] Orchestrator  [1] Perception  [2] Diagnostic  [3] Prediction  [4] Risk  [5] Planning            │
│    [6] What-If Sim    [7] Mission Ops [8] Maintenance [9] Resource Optimizer                            │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. AGENT COMMUNICATION & SAFETY GOVERNANCE (Phase 2 — 11 Tests)                                         │
│    • MessageBus (Async Pub/Sub Blackboard)  • SafetyInterlockManager (Tier 1/2/3 Hard Safety Invariants)│
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. DIGITAL TWIN CORE & CAUSAL GRAPH (Phase 1 — 14 Tests)                                                │
│    • BharatiMasterTwinEngine  • MaitriMasterTwinEngine  • TwinCausalGraph  • TwinSandbox Forking        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ FOUNDATION: 4-PILLAR PHYSICAL SENSOR LAYER (146 Tests)                                                  │
│    • Energy & Microgrid (140)  • Life Support & HVAC (180)  • Environment (87)  • Logistics (98)        │
│    ► Total: 505 Deterministic Physical Points Across 37 Subsystem Domains                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Sub-Phase 4.1: Delivered Components

### 1. Dual-Station Digital Twin Support:
- [MaitriMasterTwinEngine](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/core/engine.py): Dedicated simulation twin for Maitri Station in Schirmacher Oasis ($70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$), with Priyadarshini Lake fresh water pipeline, 3x Kirloskar gensets, and containerized habitat telemetry.
- [BharatiMasterTwinEngine](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/core/engine.py): Updated with station metadata, location, and coordinates in Larsemann Hills ($69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$).

### 2. Central Server State Manager:
- [ServerState](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/state.py): Singleton holding dual twin engines (`bharati`, `maitri`), causal graph, message bus, safety interlock manager, and all 10 specialized cognitive agents.
- Provides thread-safe simulation stepping, crisis injection, active station context switching, and sliding time-series historical buffers (up to 120 points).

### 3. Comprehensive REST API Endpoints:
- **System Health**: `GET /api/health` — Probe reporting system readiness, managed stations, clock, and agent society status.
- **Dual-Station Management**:
  - `GET /api/stations`: Listing all stations with live health indices and coordinates.
  - `GET /api/stations/{station_id}`: Granular metadata and environmental overview.
  - `POST /api/stations/active/{station_id}`: Switch default active station context.
  - `POST /api/stations/{station_id}/step`: Manual simulation clock advancement.
- **Subsystem Telemetry**:
  - `GET /api/telemetry/{station_id}/snapshot`: Complete 505-sensor snapshot.
  - `GET /api/telemetry/{station_id}/kpis`: Aggregated power, thermal, fuel, water, and risk metrics.
  - `GET /api/telemetry/{station_id}/alerts`: Active operational and life-safety alerts.
  - `GET /api/telemetry/{station_id}/pillars/{pillar}`: Filtered readings for Energy, Infrastructure, Environment, or Logistics.
  - `GET /api/telemetry/{station_id}/sensors/{sensor_id}`: Instant $O(1)$ single-sensor lookup.
  - `GET /api/telemetry/{station_id}/history`: Time-series sliding buffer for dashboard charts.
- **Cognitive Agent Society**:
  - `GET /api/agents/status`: Status of all 10 cognitive agents and bus message statistics.
  - `GET /api/agents/{agent_role}`: Detail and recent messages for a specific agent.
  - `GET /api/agents/bus/stats`: Bus message throughput and session counts.
- **Deliberation Sessions & Commander Briefing Cards**:
  - `GET /api/deliberations`: List of active and resolved multi-agent deliberations.
  - `GET /api/deliberations/{session_id}`: Complete session blackboard (proposals, simulations, critiques).
  - `GET /api/deliberations/{session_id}/briefing_card`: Synthesizes or retrieves explainable Commander Briefing Card.
- **Tiered Autonomy Action Pipeline**:
  - `POST /api/actions/execute`: Tier 1 auto-execute, Tier 2 supervised countdown queue.
  - `GET /api/actions/pending`: List pending Tier 2 supervised countdown actions.
  - `POST /api/actions/supervised/{action_id}/bypass`: Supervisor bypass for immediate execution.
  - `POST /api/actions/supervised/{action_id}/cancel`: Operator cancellation / veto.
  - `POST /api/actions/authorize_pin`: Mandatory Station Commander PIN verification (`BHARATI-CMD-2026` / `MAITRI-CMD-2026`).
- **Crisis Scenario Injection**:
  - `GET /api/scenarios`: List 8 physical crisis scenarios.
  - `POST /api/scenarios/inject`: Inject blizzard, generator trip, utilidor freeze, etc.
  - `POST /api/scenarios/clear`: Restore station to nominal baseline.

---

## 3. Test Verification & Code Correctness

### Server Endpoint Tests (`tests/server/test_api_endpoints.py`):
```powershell
python -m pytest tests/server/test_api_endpoints.py -v
```
```
============================= test session starts =============================
collected 10 items

tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_system_health_check PASSED [ 10%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_dual_stations_listing_and_detail PASSED [ 20%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_active_station_switching_and_clock_step PASSED [ 30%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_telemetry_snapshot_kpis_and_alerts PASSED [ 40%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_telemetry_pillar_filtering_and_single_sensor_lookup PASSED [ 50%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_agents_status_and_bus_statistics PASSED [ 60%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_crisis_scenario_injection_and_deliberation_trigger PASSED [ 70%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_deliberation_session_detail_and_briefing_card PASSED [ 80%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_tiered_action_execution_pipeline PASSED [ 90%]
tests/server/test_api_endpoints.py::TestFastAPIServerEndpoints::test_tier_3_commander_pin_gatekeeping PASSED [100%]

======================== 10 passed in 94.47s ========================
```

### Full Repository Regression Test Suite:
```powershell
python -m pytest tests/ -q
```
```
253 passed in 95.93s (100% green, 0 regressions)
```

---

## 4. Next Step: Sub-Phase 4.2
Awaiting user approval before proceeding to **Sub-Phase 4.2: Polar Satcom Bandwidth-Aware Sync Protocol** (`backend/satcom/`):
- Deadband filtering (thermal ±0.2°C, electrical ±1 kW, levels ±0.5%).
- Sparse delta encoding ($S_t - S_{t-1}$).
- High-ratio zlib/delta compression (>95% bandwidth reduction).
- Store-and-forward offline buffer for polar blackout resilience.
- Mainland mirror twin synchronization engine.
