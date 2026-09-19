# Walkthrough: Phase 1, Phase 2, Sub-Phase 3.1 & Sub-Phase 3.2 Implementation

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Status**: 
- **Phase 1**: Digital Twin Core & Causal Graph Engine (Completed & Verified)  
- **Phase 2**: Multi-Agent Message Bus & Safety Interlocks (Completed & Verified)  
- **Sub-Phase 3.1**: Situation Awareness Agent (Completed & Verified)  
- **Sub-Phase 3.2**: Diagnostic / Root-Cause Agent (Completed & Verified)  
**Total Test Results**: **185 passed in 1.85s (0 failures, 0 errors, 100% green)**.

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
│  ├── [COMPLETED] Sub-Phase 3.2: Diagnostic / Root-Cause Agent ("Why is it happening?")    │
│  ├── [PENDING APPROVAL] Sub-Phase 3.3: Prediction Agent ("What is likely to happen next?") │
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

## 2. Sub-Phase 3.2: Diagnostic / Root-Cause Agent

### Files Created / Modified:
1. `backend/agents/specialized/diagnostic.py` (`DiagnosticAgent`, `DiagnosisResult`, `SENSOR_TO_NODE_MAP`)
2. `backend/agents/specialized/__init__.py` (Package exports)
3. `tests/agents/test_agent_diagnostic.py` (7 specialized unit tests)

### Key Capabilities Implemented:
1. **Upstream Topological Graph Traversal**:
   - Walks incoming causal dependency edges from any symptom node up to depth 6 in $O(V+E)$ time.
   - Traces multi-hop propagation chains (e.g. `day_tank` $\to$ `chp_1` $\to$ `mlvd_bus`).
2. **Telemetry Corroboration & Healthy Node Elimination**:
   - Inspects real-time digital twin sensor telemetry and physical state representations (`_evaluate_node_health`).
   - Safely extracts scalar and object telemetry using robust value unwrapping (`_extract_val`).
   - Distinguishes between originating primary equipment failures vs dependent cascading symptoms.
3. **Multi-Hop Root-Cause Isolation**:
   - Correctly prioritizes upstream originating faults over downstream symptoms (e.g. Day Tank fuel depletion vs tripping generators vs power bus alarms).
4. **Environmental External Disturbance Detection**:
   - Distinguishes external atmospheric stressors (e.g. Katabatic Blizzard storm winds $> 30\,\text{m/s}$) from internal mechanical failure, setting `is_environmental=True`.
5. **Deliberation Session Blackboard & Downstream Pub/Sub Dispatch**:
   - Listens to incoming `MessageType.ALERT` events from Situation Awareness.
   - Automatically updates `session.root_causes` on the shared blackboard.
   - Dispatches targeted `MessageType.DIAGNOSIS` messages to `AgentRole.PREDICTION` and `AgentRole.PLANNING`.
6. **Interactive Operational Diagnostic Inquiries**:
   - Responds to `MessageType.QUERY` requests from human operators or F.R.I.D.A.Y. Orchestrator with structured diagnostic narratives and causal chains.

---

## 3. Test Verification & Code Correctness

### Full Regression & Multi-Agent Test Suite Run:
```bash
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\siddu\OneDrive\Desktop\F.R.I.D.A.Y
collected 185 items

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
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_direct_generator_trip_root_cause_diagnosis PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_multi_hop_fuel_depletion_root_cause PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_katabatic_storm_environmental_root_cause PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_utilidor_water_freeze_root_cause PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_deliberation_session_integration_and_bus_dispatch PASSED
tests/agents/test_agent_diagnostic.py::TestDiagnosticAgent::test_interactive_query_response PASSED
... [146 original sensor tests across Energy, Infrastructure, Environment, Logistics] ...

============================= 185 passed in 1.85s =============================
```

---

## 4. Next Step: Awaiting Explicit Approval for Sub-Phase 3.3

In accordance with strict pairing instructions:
- **Sub-Phase 3.2 is 100% complete and tested.**
- **Awaiting Operator Approval before starting Sub-Phase 3.3 (Prediction Agent: `prediction.py`).**
