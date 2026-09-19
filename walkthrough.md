# Walkthrough: Phase 1, Phase 2 & Sub-Phase 3.1 Implementation

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Status**: 
- **Phase 1**: Digital Twin Core & Causal Graph Engine (Completed & Verified)  
- **Phase 2**: Multi-Agent Message Bus & Safety Interlocks (Completed & Verified)  
- **Sub-Phase 3.1**: Situation Awareness Agent (Completed & Verified)  
**Total Test Results**: **178 passed in 1.71s (0 failures, 0 errors, 100% green)**.

---

## 1. Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE COMPLETE ARCHITECTURE                                 │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  5. REACT FLOW DIGITAL TWIN FRONTEND (Future Phase)                                       │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  4. SATCOM SYNC & HEADLESS FASTAPI (Future Phase)                                         │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  3. F.R.I.D.A.Y. COGNITIVE AGENTS (10 Sub-Phases)                                         │
│  ├── [COMPLETED] Sub-Phase 3.1: Situation Awareness Agent ("What is happening now?")      │
│  ├── [PENDING APPROVAL] Sub-Phase 3.2: Diagnostic / Root-Cause Agent ("Why is it happening?") │
│  ├── [PENDING] Sub-Phase 3.3: Prediction Agent ("What is likely to happen next?")         │
│  ├── [PENDING] Sub-Phase 3.4: Risk & Impact Agent ("What could this affect?")             │
│  ├── [PENDING] Sub-Phase 3.5: Planning / Recommendation Agent ("What actions to consider?")│
│  ├── [PENDING] Sub-Phase 3.6: What-If / Simulation Agent ("What if we change something?") │
│  ├── [PENDING] Sub-Phase 3.7: Mission Operations Agent ("Can missions proceed safely?")  │
│  ├── [PENDING] Sub-Phase 3.8: Maintenance Agent ("What assets need spares / attention?")  │
│  ├── [PENDING] Sub-Phase 3.9: Resource Optimization Agent ("How to allocate fuel/water?") │
│  └── [PENDING] Sub-Phase 3.10: F.R.I.D.A.Y. Master Orchestrator ("Supervisory Control")   │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [PHASE 2 COMPLETED] MULTI-AGENT MESSAGE BUS & SAFETY INTERLOCKS                          │
│  • backend/agents/framework/models.py           • backend/agents/framework/bus.py         │
│  • backend/agents/framework/safety_interlock.py • backend/agents/framework/base_agent.py  │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [PHASE 1 COMPLETED] DIGITAL TWIN CORE & CAUSAL GRAPH ENGINE                              │
│  • backend/core/engine.py (Master Twin Engine)  • backend/core/causal_graph.py (Graph)    │
│  • backend/core/sandbox.py (In-Memory Forking)  • tests/core/test_twin_core.py            │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [FOUNDATION COMPLETED] 4-PILLAR PHYSICAL OBSERVATION LAYER (505 sensors, 146 tests)      │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Sub-Phase 3.1: Situation Awareness Agent

### Files Created / Modified:
1. `backend/agents/specialized/situation_awareness.py` (`SituationAwarenessAgent`, `AnomalyRecord`)
2. `backend/agents/specialized/__init__.py` (Package exports)
3. `backend/agents/framework/models.py` (Added `RESPONSE` and `ADVISORY` to `MessageType`)
4. `tests/agents/test_agent_situation_awareness.py` (7 specialized unit tests)

### Key Capabilities Implemented:
1. **Perception Pipeline (`scan_telemetry`)**:
   - Scans all 505 sensors across Energy, Infrastructure, Environment, and Logistics pillars on every tick.
   - Monitors physical limit boundaries (katabatic blizzard speeds, indoor thermal envelopes, fuel reserves, utilidor water line freeze thresholds, cold chain storage limits).
2. **Rate-of-Change (RoC) Tracking**:
   - Maintains sliding window deques (5-minute window) recording timestamps and physical readings for critical assets.
   - Computes derivatives $\frac{\Delta X}{\Delta t}$ to detect acute deterioration (such as indoor temperatures dropping faster than $0.02^\circ\text{C}/\text{s}$ or wind acceleration) before hard thresholds are crossed.
3. **Multi-Sensor Anomaly Correlation**:
   - Correlates environmental storm conditions with utilidor pipe cooling and building thermal loss.
   - Flags station-wide emergencies (e.g. Total Station Blackout when all 3 CHP units and the battery bus are unpowered).
4. **Deliberation Session Initiation & Broadcasting**:
   - Automatically initiates a `DeliberationSession` on the `AgentMessageBus` when a critical or emergency anomaly is detected.
   - Broadcasts structured `MessageType.ALERT` payloads containing primary sensor, observed value, threshold value, rate of change, and correlated sensor tags.
5. **Interactive Operational Status Queries**:
   - Handles `MessageType.QUERY` requests from F.R.I.D.A.Y. Orchestrator or human operators and returns a real-time station situation summary.

---

## 3. Test Verification & Code Correctness

### Regression & Sub-Phase 3.1 Test Suite Run:
```bash
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\siddu\OneDrive\Desktop\F.R.I.D.A.Y
collected 178 items

tests/core/test_twin_core.py::TestTwinCoreEngine::test_master_engine_initialization PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_master_clock_synchronization PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_cross_pillar_physical_ripple_blizzard PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_scenario_generator_trip PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_scenario_water_line_freeze PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_sub_millisecond_sensor_readings PASSED
tests/core/test_twin_core.py::TestTwinCoreEngine::test_kpi_computation PASSED
tests/core/test_twin_core.py::TestTwinCausalGraph::test_graph_initial_structure PASSED
tests/core/test_twin_core.py::TestTwinCausalGraph::test_upstream_root_cause_traversal PASSED
tests/core/test_twin_core.py::TestTwinCausalGraph::test_downstream_impact_traversal PASSED
tests/core/test_twin_core.py::TestTwinCausalGraph::test_blast_radius_computation PASSED
tests/core/test_twin_core.py::TestTwinCausalGraph::test_react_flow_topology_export PASSED
tests/core/test_twin_core.py::TestTwinSandbox::test_sandbox_state_isolation PASSED
tests/core/test_twin_core.py::TestTwinSandbox::test_sandbox_override_and_plan_evaluation PASSED
tests/agents/test_framework.py::TestAgentMessageBus::test_role_subscription_and_delivery PASSED
tests/agents/test_framework.py::TestAgentMessageBus::test_broadcast_delivery PASSED
tests/agents/test_framework.py::TestAgentMessageBus::test_type_subscription PASSED
tests/agents/test_framework.py::TestAgentMessageBus::test_deliberation_session_transcript PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_tier_1_autonomous_execution PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_thermal_life_support_guardrail_rejection PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_potable_water_guardrail_rejection PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_fire_damper_smoke_lockout PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_tier_3_commander_pin_authorization PASSED
tests/agents/test_framework.py::TestSafetyInterlockManager::test_tier_2_supervised_veto PASSED
tests/agents/test_framework.py::TestBaseSpecializedAgent::test_agent_lifecycle_and_helpers PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_initialization_and_steady_state PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_blizzard_wind_detection_and_alert_broadcast PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_indoor_thermal_decay_detection PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_total_station_blackout_emergency PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_utilidor_freeze_risk_detection PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_cold_chain_excursion_detection PASSED
tests/agents/test_agent_situation_awareness.py::TestSituationAwarenessAgent::test_interactive_query_response PASSED
... [146 original sensor tests across Energy, Infrastructure, Environment, Logistics] ...

============================= 178 passed in 1.71s =============================
```

---

## 4. Next Step: Awaiting Explicit Approval for Sub-Phase 3.2

In accordance with strict pairing instructions:
- **Sub-Phase 3.1 is 100% complete and tested.**
- **Awaiting Operator Approval before starting Sub-Phase 3.2 (Diagnostic / Root-Cause Agent: `diagnostic.py`).**
