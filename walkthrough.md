# Walkthrough: Phase 1, Phase 2 & Sub-Phases 3.1–3.8 Implementation

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
- **Sub-Phase 3.6**: What-If / Simulation Agent (Completed & Verified)  
- **Sub-Phase 3.7**: Mission Operations Agent (Completed & Verified)  
- **Sub-Phase 3.8**: Maintenance Agent (Completed & Verified)  
**Total Test Results**: **227 passed in 5.44s (0 failures, 0 errors, 100% green)**.

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
│  ├── [COMPLETED] Sub-Phase 3.6: What-If / Simulation Agent ("What if we change it?")      │
│  ├── [COMPLETED] Sub-Phase 3.7: Mission Operations Agent ("Can missions proceed safely?") │
│  ├── [COMPLETED] Sub-Phase 3.8: Maintenance Agent ("What assets need spares / attention?")│
│  ├── [PENDING APPROVAL] Sub-Phase 3.9: Resource Optimization Agent ("Allocate fuel/water")│
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

## 2. Sub-Phase 3.8: Maintenance Agent

### Files Created / Modified:
1. `backend/agents/specialized/maintenance.py` (`MaintenanceAgent`, `MaintenanceHealthReport`, `AssetMaintenanceProfile`, `MaintenanceUrgency`)
2. `backend/agents/specialized/__init__.py` (Package exports)
3. `tests/agents/test_agent_maintenance.py` (7 specialized unit tests)

### Key Capabilities Implemented:
1. **Equipment Wear & MTBF Margin Tracking**:
   - Monitors rotating machinery runtime hours against factory service intervals:
     - Cummins QSK19 CHP generators ($2,000\,\text{h}$ interval)
     - PistenBully 300 polar tracked snowcats ($500\,\text{h}$ track/hydraulic interval)
     - Polar helicopter airframe cumulative flight hours ($100\,\text{h}$ inspection interval)
   - Computes exact hours until service and physical wear degradation percentage ($0\%$ to $100\%$).
2. **Spares Inventory Defense (Madrid Protocol Alignment)**:
   - Tracks generator, vehicle, and water treatment spare part stock levels from `InventoryState`.
   - Flags stockout hazards under Antarctic winter logistics isolation ($9$ months without resupply).
3. **Cyclic Deliberation Critique & Overdue Machinery Start Veto**:
   - **Overdue Machinery Veto**: When the Planning Agent proposes activating a generator (e.g. CHP-03 with $2,190\,\text{h}$ runtime on a $2,000\,\text{h}$ interval), Maintenance **vetoes** the startup command (`OVERDUE_MACHINERY_START_RESTRICTION`).
   - Prevents catastrophic fuel injector seizure or turbocharger breakdown during sub-zero operations.
   - **Alternative Machine Recommendation**: Automatically identifies and recommends the healthiest alternative unit (e.g. *"Switch to Combined Heat & Power Unit 1 with 1,480.0h service margin remaining"*).
   - Publishes `MessageType.CRITIQUE` back to `AgentRole.PLANNING` and registers the critique on `session.critiques` on the shared blackboard.
4. **Interactive Equipment Health Queries**:
   - Responds to `MessageType.QUERY` requests with comprehensive station equipment status reports (`MaintenanceHealthReport`).

---

## 3. Test Verification & Code Correctness

### Full Regression & Multi-Agent Test Suite Run:
```powershell
python -m pytest tests/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\siddu\OneDrive\Desktop\F.R.I.D.A.Y
collected 227 items

tests/core/test_twin_core.py::TestTwinCoreEngine::test_master_engine_initialization PASSED
...
tests/agents/test_agent_mission_ops.py::TestMissionOpsAgent::test_pubsub_deliberation_session_critique_dispatch PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_generate_maintenance_report_chp_and_fleet PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_overdue_asset_flagging PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_cyclic_critique_overdue_generator_start_veto PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_safe_generator_proposal_no_critique PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_pubsub_deliberation_session_critique_recording PASSED
tests/agents/test_agent_maintenance.py::TestMaintenanceAgent::test_interactive_query_response PASSED

============================= 227 passed in 5.44s =============================
```

---

## 4. Next Step: Sub-Phase 3.9
Awaiting user explicit approval before beginning **Sub-Phase 3.9: Resource Optimization Agent (`backend/agents/specialized/resource_optimizer.py`)**.
