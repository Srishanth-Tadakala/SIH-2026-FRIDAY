# Master Implementation Plan: Phase 3 — Multi-Agent Cognitive Platform (10 Sub-Phases)

**Project**: SIH 2026 Problem Statement SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Scope**: **Phase 3 (The 9 Specialized Cognitive Agents & F.R.I.D.A.Y. Core Orchestrator)**  
**Foundation Complete**:
- **Sensor Observation Layer**: 505 sensors across 4 pillars (Energy, Infra, Environment, Logistics).
- **Phase 1: Digital Twin Core**: `BharatiMasterTwinEngine`, `TwinCausalGraph`, `TwinSandbox`.
- **Phase 2: Agent Framework**: `AgentMessageBus`, `SafetyInterlockManager`, `BaseSpecializedAgent`, `models.py`.
- **Regression Test Baseline**: 171 automated unit tests passing 100% green in 4.03s.

---

## 1. Multi-Agent Cognitive Architecture (The OODA Deliberation Loop)

Rather than building all agents in a single monolithic step, Phase 3 is broken down into **10 discrete, self-contained sub-phases**. Each sub-phase implements **exactly one agent** with its own internal reasoning engine, typed bus contracts, and dedicated unit test suite.

```
                                      CRISIS TRIGGER
                          (e.g., Katabatic Blizzard / CHP Overheat)
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
   1. PERCEPTION    │ Sub-Phase 3.1: SITUATION AWARENESS AGENT      │
                    │ ("What is happening right now?")              │
                    └───────────────────────┬───────────────────────┘
                                            │ ALERT
                                            ▼
                    ┌───────────────────────────────────────────────┐
   2. DIAGNOSTICS   │ Sub-Phase 3.2: DIAGNOSTIC / ROOT-CAUSE AGENT  │
                    │ ("Why is it happening?" - Causal Traversal)   │
                    └───────────────────────┬───────────────────────┘
                                            │ DIAGNOSIS
                                            ▼
                    ┌───────────────────────────────────────────────┐
   3. PROJECTION    │ Sub-Phase 3.3: PREDICTION AGENT               │
                    │ ("What will happen next?" - Time-to-Critical) │
                    └───────────────────────┬───────────────────────┘
                                            │ PREDICTION_PROJECTION
                                            ▼
                    ┌───────────────────────────────────────────────┐
   4. RISK BLAST    │ Sub-Phase 3.4: RISK & IMPACT AGENT            │
                    │ ("What could this affect?" - Blast Radius)    │
                    └───────────────────────┬───────────────────────┘
                                            │ IMPACT_ASSESSMENT
                                            ▼
                    ┌───────────────────────────────────────────────┐
   5. STRATEGY      │ Sub-Phase 3.5: PLANNING & RECOMMENDATION AGENT│
                    │ ("What actions can solve this? - 2-3 Plans)   │
                    └───────┬───────────────────────────────┬───────┘
                            │ SIM_REQUEST                   │ PROPOSAL
                            ▼                               ▼
  ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
  │ Sub-Phase 3.6: WHAT-IF AGENT      │   │ Sub-Phase 3.9: RESOURCE OPTIMIZER │
  │ ("What if we change something?")  │   │ ("How to balance fuel vs thermal")│
  │ [Fast-forward 4h in TwinSandbox]  │   └─────────────────┬─────────────────┘
  └─────────────────┬─────────────────┘                     │
                    │ SIM_RESULT                            │ CRITIQUE
                    └───────────────────────┬───────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
   6. VALIDATION    │ Sub-Phase 3.7: MISSION OPERATIONS AGENT       │
   & DOMAIN CHECKS  │ ("Can missions / flights proceed? - Go/No-Go")│
                    ├───────────────────────────────────────────────┤
                    │ Sub-Phase 3.8: MAINTENANCE AGENT              │
                    │ ("What assets need spares / Madrid Protocol?")│
                    └───────────────────────┬───────────────────────┘
                                            │ DOMAIN_ADVISORIES
                                            ▼
                    ┌───────────────────────────────────────────────┐
   7. SYNTHESIS     │ Sub-Phase 3.10: F.R.I.D.A.Y. CHIEF AI         │
   & COMMAND        │ (Executive Action Card + Safety Interlock PIN)│
                    └───────────────────────────────────────────────┘
```

---

## 2. Detailed 10 Sub-Phase Implementation Breakdown

```
Target Directory: backend/agents/specialized/
Test Directory:   tests/agents/
```

### Sub-Phase 3.1: Situation Awareness Agent (`situation_awareness.py`)
- **Cognitive Question**: *"What is happening right now?"*
- **Role**: Continuous anomaly detector scanning all 505 sensors across Energy, Infrastructure, Environment, and Logistics.
- **Inputs**:
  - `engine.get_snapshot()` on each tick (`on_tick`).
  - Threshold envelopes (high/low limits, maximum rates of change $\Delta X / \Delta t$).
- **Internal Reasoning Engine**:
  - Multi-sensor correlation detector (e.g. ambient wind surge correlated with utilidor thermal drop).
  - Rate-of-change (RoC) tracker across sliding 5-minute windows.
  - Severity level evaluator (`INFO`, `WARNING`, `CRITICAL`, `EMERGENCY`).
- **Outputs**:
  - Creates a new `DeliberationSession` when an anomaly exceeds critical thresholds.
  - Broadcasts `MessageType.ALERT` to the bus with anomaly details, affected sensor IDs, observed values, and baseline limits.
- **Unit Test File**: `tests/agents/test_agent_situation_awareness.py`
  - Nominal steady-state scan (zero false alarms).
  - High-wind katabatic surge detection.
  - CHP power droop & over-temperature detection.
  - Session creation & broadcast verification.

---

### Sub-Phase 3.2: Diagnostic / Root-Cause Agent (`diagnostic.py`)
- **Cognitive Question**: *"Why is it happening?"*
- **Role**: Root-cause isolator that prevents alarm floods by distinguishing between primary faults and secondary symptom cascades.
- **Inputs**:
  - Subscribes to `MessageType.ALERT` on the message bus.
  - Queries `graph.get_upstream_causes(node_id, max_depth=5)` on `TwinCausalGraph`.
- **Internal Reasoning Engine**:
  - Upstream graph traversal isolating root physical assets.
  - Cross-references upstream equipment telemetry to eliminate healthy nodes.
  - Identifies single root cause (e.g. trace heating breaker trip vs freeze symptom).
- **Outputs**:
  - Publishes `MessageType.DIAGNOSIS` targeted to `AgentRole.PREDICTION` and `AgentRole.PLANNING`.
  - Payload contains `root_cause_asset`, `root_cause_name`, `confidence`, `causal_chain` (list of node IDs), and `explanation`.
- **Unit Test File**: `tests/agents/test_agent_diagnostic.py`
  - Isolates fuel delivery fault from day-tank low level.
  - Isolates utilidor freeze from RO plant failure.
  - Validates causal path length and attribution confidence.

---

### Sub-Phase 3.3: Prediction Agent (`prediction.py`)
- **Cognitive Question**: *"What will happen next if unmitigated?"*
- **Role**: Forward extrapolator computing physical time-to-critical countdowns.
- **Inputs**:
  - Subscribes to `MessageType.DIAGNOSIS`.
  - Queries active twin telemetry (current temperatures, tank levels, battery SOC).
- **Internal Reasoning Engine**:
  - First-order thermal decay equation:
    $$T(t) = T_{\text{ambient}} + (T_0 - T_{\text{ambient}}) \cdot e^{-t / \tau}$$
  - Fuel exhaustion runway:
    $$t_{\text{exhaustion}} = \frac{V_{\text{day\_tank}} + V_{\text{bulk}}}{\dot{V}_{\text{fuel\_burn}}}$$
  - Battery depletion countdown:
    $$t_{\text{battery}} = \frac{\text{Capacity}_{\text{Ah}} \times \text{SOC}}{I_{\text{critical\_discharge}}}$$
- **Outputs**:
  - Publishes `MessageType.PREDICTION_PROJECTION` targeted to `AgentRole.RISK_IMPACT` and `AgentRole.PLANNING`.
  - Payload contains `time_to_freeze_minutes`, `hours_to_blackout`, `hours_to_fuel_starvation`, and `projected_trajectory`.
- **Unit Test File**: `tests/agents/test_agent_prediction.py`
  - Predicts time until living module drops below $16^\circ\text{C}$ during heating loss.
  - Predicts fuel runway during high-demand blizzard run.
  - Verifies countdown bounds and mathematical stability.

---

### Sub-Phase 3.4: Risk & Impact Agent (`risk_impact.py`)
- **Cognitive Question**: *"What could this affect across the station?"*
- **Role**: Blast-radius evaluator calculating cascading failure spread across the 4 pillars.
- **Inputs**:
  - Subscribes to `MessageType.DIAGNOSIS` and `MessageType.PREDICTION_PROJECTION`.
  - Calls `graph.calculate_blast_radius(root_node_id)` on `TwinCausalGraph`.
- **Internal Reasoning Engine**:
  - Traverses downstream dependencies across 4 impact categories:
    1. **Life Support** (Human thermal comfort, breathable air, potable water, medical facility).
    2. **Grid Power** (MLVD 400V bus stability, UPS battery reserves, critical IT servers).
    3. **Structural Health** (Foundation stilt strain, utilidor pipe containment).
    4. **Mission Readiness** (Aviation helipad, field expedition teams, cargo integrity).
  - Computes weighted severity score ($0.0$ to $100.0$).
- **Outputs**:
  - Publishes `MessageType.IMPACT_ASSESSMENT` targeted to `AgentRole.PLANNING` and `AgentRole.FRIDAY_ORCHESTRATOR`.
  - Payload contains `severity_score`, `life_support_threat` (boolean), `affected_subsystems`, and `criticality_breakdown`.
- **Unit Test File**: `tests/agents/test_agent_risk_impact.py`
  - Evaluates blast radius of MLVD bus failure (threatens all life support).
  - Evaluates blast radius of localized Reefer compressor failure (logistics only).
  - Verifies severity scoring accuracy.

---

### Sub-Phase 3.5: Planning / Recommendation Agent (`planning.py`)
- **Cognitive Question**: *"What operational actions could solve this?"*
- **Role**: Strategy formulator synthesizing 2 to 3 distinct operational mitigation options.
- **Inputs**:
  - Subscribes to `MessageType.IMPACT_ASSESSMENT` and `MessageType.DIAGNOSIS`.
  - Reads station operating procedures and equipment configuration rules.
- **Internal Reasoning Engine**:
  - Formulates competing candidate plans:
    - **Plan A (Conservative / Resource Preserving)**: E.g., Trim fresh air ventilation by 15%, shed non-essential lab heating, keep single CHP online.
    - **Plan B (Aggressive / High Reliability)**: E.g., Crank standby CHP-2 immediately, bring hydronic flow to 100%, maintain all heating loops.
  - Assigns parameter overrides and provisional `AutonomyTier` to each plan.
- **Outputs**:
  - Publishes `MessageType.SIM_REQUEST` to `AgentRole.WHAT_IF` to test the candidate plans in the sandbox.
  - Publishes `MessageType.PROPOSAL` to `AgentRole.RESOURCE_OPTIMIZER` for efficiency critique.
- **Unit Test File**: `tests/agents/test_agent_planning.py`
  - Generates valid candidate proposals for a generator trip scenario.
  - Generates valid candidate proposals for a severe cold blizzard scenario.
  - Verifies parameter override structure and syntax.

---

### Sub-Phase 3.6: What-If / Simulation Agent (`what_if.py`)
- **Cognitive Question**: *"What happens if we execute this plan?"*
- **Role**: Predictive validator executing candidate action plans in `TwinSandbox`.
- **Inputs**:
  - Subscribes to `MessageType.SIM_REQUEST` containing candidate action proposals.
- **Internal Reasoning Engine**:
  - Forks `TwinSandbox.fork(engine)` into isolated memory.
  - Injects candidate parameter overrides into the sandbox state.
  - Executes accelerated forward simulation (4 hours physical time in $< 25\,\text{ms}$).
  - Compares candidate trajectory against unmitigated baseline:
    $$\Delta\text{Fuel} = \text{Fuel}_{\text{baseline}} - \text{Fuel}_{\text{candidate}}$$
    $$\Delta\text{Temp} = T_{\text{candidate\_min}} - T_{\text{baseline\_min}}$$
  - Checks for safety violations (e.g. indoor temp $< 16^\circ\text{C}$ or load $> 95\%$).
- **Outputs**:
  - Publishes `MessageType.SIM_RESULT` targeted to `AgentRole.PLANNING` and `AgentRole.FRIDAY_ORCHESTRATOR`.
  - Payload contains `simulation_delta`, `fuel_saved_l`, `temp_margin_c`, `is_safe`, and `safety_assessment`.
- **Unit Test File**: `tests/agents/test_agent_what_if.py`
  - Fast-forward simulation of Plan A vs Plan B.
  - Correctly detects safety violation if a plan causes indoor freezing.
  - Benchmarks execution time ($< 100\,\text{ms}$).

---

### Sub-Phase 3.7: Mission Operations Agent (`mission_ops.py`)
- **Cognitive Question**: *"Can outdoor missions, helicopter flights, or cargo operations proceed?"*
- **Role**: Field safety and logistics operational evaluator.
- **Inputs**:
  - Subscribes to environmental weather and logistics telemetry.
  - Tracks status of:
    - PistenBully PB-01 to PB-06 convoys.
    - Helicopter flight operations from helipad.
    - Quilty Bay ship offloading and barge operations.
    - Fast ice traverse routes.
- **Internal Reasoning Engine**:
  - Evaluates weather envelopes:
    - Helipad: Wind $\le 20\,\text{m/s}$, Visibility $\ge 800\,\text{m}$, Blizzard risk $< 0.6 \implies \text{GO}$.
    - Fast Ice Route: Ice thickness $\ge 1.5\,\text{m}$, Surface traction $\ge 60\% \implies \text{PASSABLE}$.
  - Computes operational decision: `GO`, `CAUTION`, `NO_GO`.
- **Outputs**:
  - Publishes `MessageType.ADVISORY` or `MessageType.ALERT` on mission safety.
  - Submits emergency traverse halt or recall proposals if weather deteriorates.
- **Unit Test File**: `tests/agents/test_agent_mission_ops.py`
  - Generates `NO_GO` when wind exceeds 25 m/s or whiteout conditions occur.
  - Generates `GO` under mild summer weather.
  - Verifies traction and sea-ice safety calculations.

---

### Sub-Phase 3.8: Maintenance Agent (`maintenance.py`)
- **Cognitive Question**: *"What assets need inspection, maintenance, or spare parts?"*
- **Role**: Equipment health monitor and Antarctic environmental treaty compliance officer.
- **Inputs**:
  - Tracks cumulative running hours across CHPs, vehicles, RO pumps, MBR blowers.
  - Reads warehouse stores inventory and spares stock levels.
  - Observes Madrid Protocol waste staging and wastewater discharge quality.
- **Internal Reasoning Engine**:
  - Maintenance interval tracking (e.g. Scania CHP 250h oil change, 1000h major overhaul; PB-01 track tension inspection).
  - Spares stockout risk evaluation.
  - Environmental discharge compliance verification (MBR effluent COD $< 100\,\text{mg/L}$, BOD $< 25\,\text{mg/L}$).
- **Outputs**:
  - Publishes `MessageType.ADVISORY` with maintenance schedules and spares warnings.
  - Critiques planning proposals that would push an asset past its critical maintenance window.
- **Unit Test File**: `tests/agents/test_agent_maintenance.py`
  - Flags overdue maintenance when CHP hours exceed service interval.
  - Verifies Madrid Protocol waste staging alerts.
  - Verifies warehouse inventory stockout alerts.

---

### Sub-Phase 3.9: Resource Optimization Agent (`resource_optimizer.py`)
- **Cognitive Question**: *"How should constrained station resources be balanced globally?"*
- **Role**: Multi-objective Pareto optimizer balancing competing station priorities:
  $$\min (\text{Fuel Burn Rate}) \quad \text{subject to} \quad T_{\text{indoor}} \ge 18^\circ\text{C}, \quad P_{\text{grid}} \le 95\%, \quad \text{Water} \ge 3\,\text{days}$$
- **Inputs**:
  - Subscribes to `MessageType.PROPOSAL` from Planning Agent.
  - Observes fuel reserve trajectories, electrical loads, and thermal recovery loops.
- **Internal Reasoning Engine**:
  - Evaluates global trade-offs (e.g., shifting RO desalination batch run to daytime when solar is high; peak-shaving battery duty cycles; night setback heating).
  - Critiques candidate plans that save fuel at the expense of life-support stability.
- **Outputs**:
  - Publishes `MessageType.CRITIQUE` on candidate proposals with recommended parameter tweaks.
  - Publishes `MessageType.CONSENSUS_PLAN` endorsing the optimal trade-off.
- **Unit Test File**: `tests/agents/test_agent_resource_optimizer.py`
  - Critiques plan with excessive fuel burn.
  - Recommends electrical load shifting for RO plant.
  - Verifies Pareto trade-off scoring.

---

### Sub-Phase 3.10: F.R.I.D.A.Y. Chief AI Orchestrator (`friday_orchestrator.py`)
- **Cognitive Question**: *"What is the final decision and operational plan for the station commander?"*
- **Role**: Executive Commander, dialogue manager, and multi-agent coordinator.
- **Inputs**:
  - Observes entire `DeliberationSession` blackboard across all agents.
  - Handles operator queries and commands (terminal or chat interface).
- **Internal Reasoning Engine**:
  - Initiates and manages multi-agent deliberation rounds during anomalies.
  - Synthesizes agent diagnoses, predictions, simulation results, and critiques into a unified **Executive Action Card**:
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │ F.R.I.D.A.Y. EXECUTIVE ACTION CARD: INCIDENT SES-91A04          │
    ├─────────────────────────────────────────────────────────────────┤
    │ Anomaly: Severe Katabatic Blizzard & Heating Demand Surge       │
    │ Root Cause: Ambient temp plunged to -32.5°C; wind gust 45 m/s   │
    │ Prediction: Indoor temp will drop to 15.2°C in 48 min           │
    │ Risk Score: 88.5 / 100 (CRITICAL: Life Support Threat)          │
    ├─────────────────────────────────────────────────────────────────┤
    │ Recommended Action: PLAN B (Dual CHP Dispatch & Damper Trim)    │
    │ • Start Standby CHP-2 to support 155 kWth heating surge         │
    │ • Trim AHU-01 fresh air damper to 15% to limit thermal loss     │
    │ • Halts Quilty Bay marine offload and closes helipad            │
    ├─────────────────────────────────────────────────────────────────┤
    │ Simulation Validation:                                          │
    │ • Indoor temp stabilizes at 20.4°C (Safe)                       │
    │ • Fuel burn increases by +12.4 L/h (Autonomy: 242 days)         │
    │ Autonomy Tier: TIER 3 (MANDATORY COMMANDER AUTHORIZATION)       │
    │ PIN Required: [ BHARATI-CMD-2026 ]                              │
    └─────────────────────────────────────────────────────────────────┘
    ```
  - Dispatches validated proposals through `SafetyInterlockManager`.
- **Outputs**:
  - Publishes `MessageType.CONSENSUS_PLAN` and dispatches execution.
  - Provides natural-language reasoning summary for operator explanation.
- **Unit Test File**: `tests/agents/test_friday_orchestrator.py`
  - Full end-to-end deliberation round on blizzard incident.
  - Executive Action Card generation.
  - Tier 3 Commander confirmation execution.

---

## 3. End-to-End Deliberation Integration Test (`tests/agents/test_deliberation_loop.py`)

Following the completion of sub-phases 3.1 through 3.10, an end-to-end multi-agent integration test will verify the complete cognitive chain:
1. Master engine injects `BLIZZARD_STRIKE`.
2. `SituationAwarenessAgent` fires `ALERT` and spawns session.
3. `DiagnosticRootCauseAgent` attributes root cause to katabatic weather surge.
4. `PredictionAgent` calculates thermal decay countdown.
5. `RiskImpactAgent` computes life-support blast radius (88/100).
6. `PlanningRecommendationAgent` formulates Plan A and Plan B.
7. `WhatIfSimulationAgent` forks sandbox, validates Plan B, and rejects Plan A for indoor freezing.
8. `MissionOperationsAgent` issues Helipad and Traverse `NO_GO`.
9. `ResourceOptimizationAgent` approves Plan B fuel-to-warmth ratio.
10. `FridayOrchestrator` compiles Executive Action Card, verifies Commander PIN, and executes on the live digital twin.

---

## 4. Verification Plan

### Test Strategy:
- Each of the 10 agents has its own dedicated test file (`test_agent_<name>.py`).
- 10 new test files + 1 end-to-end integration test file.
- Strict regression baseline: all 171 existing unit tests must remain 100% green after each sub-phase.

### Execution Plan:
- We will execute Sub-Phase 3.1 first, verify its unit tests, and then proceed sequentially through Sub-Phase 3.10.

---

## 5. User Review & Approval Gateway

> [!IMPORTANT]
> **Sub-Phase 3.1 Initiation**:
> We are ready to begin **Sub-Phase 3.1: Situation Awareness Agent** (`backend/agents/specialized/situation_awareness.py` and `tests/agents/test_agent_situation_awareness.py`).
>
> Please confirm if you approve proceeding with **Sub-Phase 3.1**!
