# Walkthrough: Phase 1, Phase 2 & Sub-Phases 3.1–3.5 Implementation

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Status**: 
- **Phase 1**: Digital Twin Core & Causal Graph Engine (Completed & Verified)  
- **Phase 2**: Multi-Agent Message Bus & Safety Interlocks (Completed & Verified)  
- **Sub-Phase 3.1**: Situation Awareness Agent (Completed & Verified)  
- **Sub-Phase 3.2**: Diagnostic / Root-Cause Agent (Completed & Verified)  
- **Sub-Phase 3.3**: Prediction Agent (Completed & Verified)  
- **Sub-Phase 3.4**: Risk & Impact Agent (Completed & Verified)  
- **Sub-Phase 3.5**: Planning / Recommendation Agent (Completed & Verified)  
**Total Test Results**: **206 passed in 4.12s (0 failures, 0 errors, 100% green)**.

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
│  ├── [COMPLETED] Sub-Phase 3.3: Prediction Agent ("What is likely to happen next?")       │
│  ├── [COMPLETED] Sub-Phase 3.4: Risk & Impact Agent ("What could this affect?")           │
│  ├── [COMPLETED] Sub-Phase 3.5: Planning / Recommendation Agent ("What actions to take?") │
│  ├── [PENDING APPROVAL] Sub-Phase 3.6: What-If / Simulation Agent ("What if we change it?")│
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

## 2. Sub-Phase 3.5: Planning / Recommendation Agent

### Files Created / Modified:
1. `backend/agents/specialized/planning.py` (`PlanningAgent`)
2. `backend/agents/specialized/__init__.py` (Package exports)
3. `backend/agents/framework/models.py` (Added `to_dict()` serialization to `ActionProposal`)
4. `tests/agents/test_agent_planning.py` (7 specialized unit tests)

### Key Capabilities Implemented:
1. **Antarctic Operational SOP Playbook Formulation**:
   - Synthesizes incident diagnoses, lookahead trends, and blast radius constraints to formulate prioritized `ActionProposal`s:
     - **Generator Trip**: Automatically drafts proposals to sequence standby generator CHP-02 to active running status ($65\,\text{kW}$) and load-shed non-critical scientific research lab heating.
     - **Utilidor Freeze**: Drafts proposals to engage secondary electric trace heating tape and initiate warm thermal recirculation flush.
     - **Katabatic Blizzard**: Transitions HVAC AHU-01 and AHU-02 to 90% recirculation mode (sealing fresh air intake against snow ingress) and grounds outdoor field traverses.
     - **Cold Chain Excursion**: Re-routes Reefer-01 auxiliary electrical feed and cycles backup compressor.
     - **Day Tank Fuel Depletion**: Activates fuel transfer pump skid from Bulk Fuel Tank 01.
2. **Tiered Autonomy Pre-Screening**:
   - Categorizes each candidate proposal into:
     - `TIER_1_AUTONOMOUS`: Reversible, low-risk micro-adjustments and standby starts.
     - `TIER_2_SUPERVISED`: 60-second engineer countdown veto window.
     - `TIER_3_COMMANDER_CONFIRMATION`: High-consequence life-safety, bus de-energization, or shelter evacuation.
3. **Safety Interlock Guardrail Verification**:
   - Pre-screens every proposal against `SafetyInterlockManager`:
     - Blocks attempts to command living habitat below $16.0^\circ\text{C}$ (`ERR_THERMAL_LIFE_SUPPORT`).
     - Blocks attempts to deplete potable water below $1,500\,\text{L}$ (`ERR_POTABLE_WATER_MINIMUM`).
     - Rejects violating proposals with `ProposalStatus.REJECTED` and detailed rejection rationale.
4. **Deliberation Session Blackboard & Downstream Pub/Sub Dispatch**:
   - Automatically populates `session.candidate_proposals` on the shared `DeliberationSession` blackboard.
   - Dispatches `MessageType.PROPOSAL` messages to `AgentRole.WHAT_IF` (for accelerated forward sandbox verification) and `AgentRole.FRIDAY_ORCHESTRATOR`.
5. **Interactive Operational Planning Queries**:
   - Responds to `MessageType.QUERY` requests with formulated candidate proposal packages for any specified station asset.

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
collected 206 items

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
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_stable_forward_projection_nominal_conditions PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_thermal_decay_time_to_violation_in_blizzard PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_day_tank_fuel_exhaustion_time_to_failure PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_utilidor_pipe_freeze_time_to_failure PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_deliberation_session_integration_and_bus_dispatch PASSED
tests/agents/test_agent_prediction.py::TestPredictionAgent::test_interactive_query_response PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_generator_trip_blast_radius_assessment PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_katabatic_blizzard_mission_impact PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_utilidor_pipe_freeze_water_cycle_threat PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_urgency_multiplier_short_time_to_violation PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_deliberation_session_blackboard_and_bus_dispatch PASSED
tests/agents/test_agent_risk_impact.py::TestRiskImpactAgent::test_interactive_query_response PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_generator_trip_sop_proposal_formulation PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_utilidor_freeze_mitigation_proposal PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_katabatic_blizzard_hvac_recirculation_proposal PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_safety_interlock_guardrail_rejection_of_invalid_proposal PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_deliberation_session_blackboard_and_whatif_dispatch PASSED
tests/agents/test_agent_planning.py::TestPlanningAgent::test_interactive_query_response PASSED
... [146 original sensor tests across Energy, Infrastructure, Environment, Logistics] ...

============================= 206 passed in 4.12s =============================
```

---

## 4. Next Step: Awaiting Explicit Approval for Sub-Phase 3.6

In accordance with strict pairing instructions:
- **Sub-Phase 3.5 is 100% complete and tested.**
- **Awaiting Operator Approval before starting Sub-Phase 3.6 (What-If / Simulation Agent: `what_if.py`).**
