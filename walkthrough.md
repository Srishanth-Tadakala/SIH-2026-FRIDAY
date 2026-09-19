# Walkthrough: Phase 1, Phase 2 & Sub-Phases 3.1–3.6 Implementation

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
**Total Test Results**: **213 passed in 5.25s (0 failures, 0 errors, 100% green)**.

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
│  ├── [PENDING APPROVAL] Sub-Phase 3.7: Mission Operations Agent ("Can missions proceed?") │
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

## 2. Sub-Phase 3.6: What-If / Simulation Agent

### Files Created / Modified:
1. `backend/agents/specialized/what_if.py` (`WhatIfSimulationAgent`, `PlanSimulationVerdict`)
2. `backend/agents/specialized/__init__.py` (Package exports)
3. `tests/agents/test_agent_what_if.py` (7 specialized unit tests)

### Key Capabilities Implemented:
1. **Counterfactual Forward Simulation via In-Memory Sandboxes**:
   - For every candidate `ActionProposal`, forks an unmitigated baseline sandbox and a candidate plan sandbox (`TwinSandbox.fork(engine)`).
   - Fast-forwards coupled station dynamics across configurable horizons ($1\,\text{h}$, $2\,\text{h}$, $4\,\text{h}$) at accelerated rates ($>1000\times$).
   - Evaluates quantitative trajectory delta metrics via `TwinSandbox.compare_trajectories()`:
     - Fuel consumed delta ($\Delta L$) and percentage saved
     - Minimum indoor temperature margin ($\Delta^\circ\text{C}$)
     - Battery reserve margin ($\Delta\%$)
     - Composite risk reduction score ($\%$)
2. **Antarctic Life-Support Floor & Safety Enforcement**:
   - Checks trajectory outcomes and parameter overrides against mandatory life-support floors:
     - Indoor living temperature must not breach $16.0^\circ\text{C}$ minimum
     - Critical UPS battery buffer must not breach $30.0\%$ reserve
     - Electrical capacity must not exceed continuous rating ($190.0\,\text{kW}$)
   - Rejects unsafe plans with `is_safe=False` and status `ProposalStatus.REJECTED`.
3. **Cyclic Deliberation Feedback & Counterfactual Critiques**:
   - Rather than acting as a passive linear pipeline, when an unsafe plan is detected, publishes an explicit `MessageType.CRITIQUE` back to `AgentRole.PLANNING`.
   - Populates `DeliberationSession.critiques` on the shared blackboard, forcing the Planning Agent to re-deliberate and generate safer alternatives.
4. **Multi-Proposal Comparative Ranking**:
   - Implements `compare_proposals()` to evaluate and rank multiple competing operational strategies.
   - Orders proposals: Safe plans first, followed by highest risk reduction, highest thermal stability margin, and fuel savings.
5. **Zero Mutation Guarantee**:
   - Verified that extreme forward simulations operate in complete memory decoupling without altering master twin state, simulation clock, or telemetry readings.

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
collected 213 items

tests/core/test_twin_core.py::TestTwinCoreEngine::test_master_engine_initialization PASSED
...
tests/agents/test_agent_planning.py::TestPlanningAgent::test_interactive_query_response PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_initialization_and_clean_state PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_counterfactual_simulation_baseline_vs_candidate PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_unsafe_plan_rejection_and_counterfactual_critique PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_pubsub_proposal_evaluation_and_feedback_dispatch PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_multi_proposal_comparative_ranking PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_explicit_sim_request_handling PASSED
tests/agents/test_agent_what_if.py::TestWhatIfSimulationAgent::test_zero_mutation_contamination PASSED

============================= 213 passed in 5.25s =============================
```

---

## 4. Next Step: Sub-Phase 3.7
Awaiting user explicit approval before beginning **Sub-Phase 3.7: Mission Operations Agent (`backend/agents/specialized/mission_ops.py`)**.
