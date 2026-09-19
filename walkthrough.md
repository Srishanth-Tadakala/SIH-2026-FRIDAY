# Walkthrough: Phase 1 & Phase 2 Backend Implementation

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Status**: **Phase 1 (Digital Twin Core & Causal Graph)** and **Phase 2 (Multi-Agent Framework & Safety Interlocks)** Completed & Verified.  
**Test Results**: **171 passed in 4.03s (0 failures, 0 errors, 100% green)**.

---

## 1. What Was Built

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE COMPLETE ARCHITECTURE                                 │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  5. REACT FLOW DIGITAL TWIN FRONTEND (Next Phase)                                         │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  4. SATCOM SYNC & HEADLESS FASTAPI (Next Phase)                                           │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  3. F.R.I.D.A.Y. MASTER ORCHESTRATOR & 9 SPECIALIZED COGNITIVE AGENTS (Ready to Build)    │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [PHASE 2 COMPLETED] MULTI-AGENT MESSAGE BUS & SAFETY INTERLOCKS                          │
│  • backend/agents/framework/models.py           • backend/agents/framework/bus.py         │
│  • backend/agents/framework/safety_interlock.py • backend/agents/framework/base_agent.py  │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [PHASE 1 COMPLETED] DIGITAL TWIN CORE & CAUSAL GRAPH ENGINE                              │
│  • backend/core/engine.py (Master Twin Engine)  • backend/core/causal_graph.py (Graph)    │
│  • backend/core/sandbox.py (In-Memory Forking)  • tests/core/test_twin_core.py            │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  [FOUNDATION COMPLETE] 4-PILLAR PHYSICAL OBSERVATION LAYER (505 sensors, 146 tests)       │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: Digital Twin Core & Causal Graph Engine

### 1. `backend/core/engine.py` (`BharatiMasterTwinEngine`)
- **Single Synchronized Clock**: Advances all 4 observation pillars (Energy, Infrastructure, Environment, Logistics) along a single deterministic timeline.
- **Physical Sequential Coupling**:
  $$\text{Environment } \xrightarrow{\text{boundary conditions}} \text{ Infrastructure } \xrightarrow{\text{kW \& heat demands}} \text{ Energy } \xrightarrow{\text{grid \& fuel status}} \text{ Logistics}$$
- **Master Scenario Injector**:
  - `BLIZZARD_STRIKE`: Katabatic winds surge to 34 m/s, temp drops to $-32.5^\circ\text{C}$, helipad closes, routes restricted, blizzard alerts raised.
  - `GENERATOR_TRIP`: Mechanical/electrical fault trips lead CHP-1; standby CHP-2 auto-starts; UPS buffers critical bus.
  - `WATER_LINE_FREEZE`: Trace heating loss on utilidor pipe drops temperature below $0^\circ\text{C}$; RO plant trips on freeze fault.
  - `COLD_CHAIN_EXCURSION`, `FUEL_TRANSFER_LEAK`, `HEAVY_CARGO_OPERATION`, `MISSION_FIELD_DEPLOYMENT`.
- **Sub-Millisecond Readout**: O(1) sensor lookup across all 505 points.
- **Station KPIs & Alerts**: Computes real-time fuel autonomy days, water autonomy days, indoor average temperature, running CHP counts, and composite risk score.

### 2. `backend/core/causal_graph.py` (`TwinCausalGraph`)
- Explicit directed graph representing station physical topology, equipment dependencies, and instrumentation:
  - **41 nodes & 48 edges** mapping energy generation, distribution buses, thermal loops, HVAC air handlers, living zones, utilidors, water cycle, and logistics.
- **Upstream Root-Cause Traversal** (`get_upstream_causes()`):
  - Traverses incoming edges backwards in $O(V+E)$ time to identify originating physical faults (used by Diagnostic Agent).
- **Downstream Blast Radius & Severity** (`calculate_blast_radius()`):
  - Traverses outgoing edges to determine cascading impact across life-support systems, assigning a 0–100 severity score.
- **React Flow Serialization** (`export_react_flow_topology()`):
  - Exports nodes, coordinates, labels, and animated SVG edges ready for frontend visualization.

### 3. `backend/core/sandbox.py` (`TwinSandbox`)
- **In-Memory State Forking** (`TwinSandbox.fork(engine)`):
  - Clones entire digital twin state in $< 19\,\text{ms}$, completely isolating the sandbox from live station telemetry.
- **Accelerated Forward Simulation** (`run_fast_forward()`):
  - Simulates 4 hours of physical time in $< 850\,\text{ms}$ (or 30 minutes in $< 100\,\text{ms}$).
  - Records time-series trajectories of fuel reserves, indoor temperature, battery SOC, and risk scores.
- **Quantitative Plan Delta Evaluation** (`compare_trajectories()`):
  - Evaluates candidate operational plans against unmitigated baselines, computing liters of fuel saved, temperature margins, and safety compliance.

---

## 3. Phase 2: Multi-Agent Communication Framework & Safety Interlocks

### 1. `backend/agents/framework/models.py`
- Typed enums and dataclasses:
  - `AgentRole`: The 9 specialized cognitive roles + `FRIDAY_ORCHESTRATOR`.
  - `MessageType`: `ALERT`, `QUERY`, `DIAGNOSIS`, `PREDICTION_PROJECTION`, `IMPACT_ASSESSMENT`, `PROPOSAL`, `CRITIQUE`, `SIM_REQUEST`, `SIM_RESULT`, `CONSENSUS_PLAN`, `OPERATOR_COMMAND`.
  - `AutonomyTier`: `TIER_1_AUTONOMOUS`, `TIER_2_SUPERVISED`, `TIER_3_COMMANDER_CONFIRMATION`.
  - `AgentMessage`: Standard envelope for pub/sub message routing.
  - `ActionProposal`: Structured intervention plan with target subsystem, parameter overrides, autonomy tier, and rationale.
  - `DeliberationSession`: Shared blackboard holding active alerts, root causes, predictions, candidate plans, and chronological dialogue transcripts.

### 2. `backend/agents/framework/bus.py` (`AgentMessageBus`)
- In-memory event broker supporting:
  - Role-targeted messaging (`subscribe_role()`).
  - Semantic message-type filtering (`subscribe_type()`).
  - Platform-wide broadcast (`subscribe_broadcast()`).
  - Deliberation session blackboard recording and audit log retrieval.

### 3. `backend/agents/framework/safety_interlock.py` (`SafetyInterlockManager`)
- Enforces non-negotiable Antarctic life-support safety guardrails:
  - **Thermal Life-Support**: Living quarters cannot be commanded below $16.0^\circ\text{C}$ (`ERR_THERMAL_LIFE_SUPPORT`).
  - **Potable Water Reserve**: Water cannot be drained below 3 days of autonomy (minimum 1,500 L) (`ERR_POTABLE_WATER_MINIMUM`).
  - **Fire Containment**: Dampers locked closed when smoke $> 1.5\%$ (`ERR_FIRE_DAMPER_SMOKE_LOCKOUT`).
  - **Severe Weather Lockout**: Outgoing traverses blocked in extreme katabatic winds (`ERR_TRAVERSE_WEATHER_LOCKOUT`).
  - **Tiered Autonomy Gatekeeping**:
    - Tier 1: Executes autonomously.
    - Tier 2: Enters 60-second engineer veto window.
    - Tier 3: Strictly requires human Commander PIN confirmation (`BHARATI-CMD-2026`).

### 4. `backend/agents/framework/base_agent.py` (`BaseSpecializedAgent`)
- Standard abstract base class with lifecycle hooks, bus subscription, causal graph queries, sandbox forking, and safety interlock integration.

---

## 4. Test Verification & Code Correctness

### Complete Test Suite Execution:
```bash
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
collected 171 items

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
... [146 original sensor tests across Energy, Infrastructure, Environment, Logistics] ...

============================= 171 passed in 4.03s =============================
```

---

## 5. Next Steps
With Phase 1 and Phase 2 fully built, tested, and validated, we are ready to implement:
- **Phase 3: The 9 Specialized Cognitive Agents** (built and tested one by one under `backend/agents/specialized/`):
  1. `SituationAwarenessAgent`
  2. `DiagnosticRootCauseAgent`
  3. `PredictionAgent`
  4. `RiskImpactAgent`
  5. `PlanningRecommendationAgent`
  6. `WhatIfSimulationAgent`
  7. `MissionOperationsAgent`
  8. `MaintenanceAgent`
  9. `ResourceOptimizationAgent`
  10. `FridayOrchestrator`
