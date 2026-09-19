# Detailed Industrial-Grade Implementation Plan: Phase 1 & Phase 2 Backend Core

**Project**: SIH 2026 Problem Statement SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: Bharati Research Station (Larsemann Hills) & Maitri Station (Schirmacher Oasis), East Antarctica  
**Scope**: **Phase 1 (Digital Twin Core & Causal Engine)** and **Phase 2 (Multi-Agent Framework & Safety Interlocks)**  
**Foundation**: 413 physical/virtual sensors across 4 pillars (Energy, Infrastructure, Environment, Logistics), 146 unit tests 100% green.  
**Objective**: Build an enterprise-grade, deterministic, low-latency, and safety-critical backend foundation that bridges raw sensor telemetry to autonomous multi-agent cognition.

---

## 1. Architectural Philosophy & Design Principles

To ensure this backend meets industry-grade mission-critical standards for Antarctic life-support infrastructure:

1. **Zero External Heavy Dependencies for Core Logic**:
   - The entire Digital Twin Core and Agent Framework will use Python 3.12+ standard library (`dataclasses`, `enum`, `typing`, `copy`, `time`, `collections`, `heapq`, `math`).
   - Ensures instantaneous startup, zero version rot, and guaranteed operation on air-gapped Antarctic edge servers.
2. **Deterministic Physics Coupling**:
   - No floating-point drift or asynchronous race conditions in physical simulation.
   - All 4 pillars advance along a single synchronized clock tick ($T_{\text{tick}}$).
3. **Strict Causal Discipline**:
   - Physical relationships between assets are modeled as an explicit directed graph with typed edges (e.g. thermal, electrical, hydraulic, environmental).
   - Upstream causes and downstream impact radiuses are computed via graph traversal algorithms ($O(V+E)$), eliminating brittle heuristic spaghetti.
4. **Isolated Fast-Forward Sandboxing**:
   - State-forking mechanism clones complete station memory in $< 5\,\text{ms}$, allowing accelerated forward simulation ($1000\times$ speed) of operational interventions without contaminating live station state.
5. **Fail-Safe Tiered Autonomy**:
   - Hardware-in-the-loop safety interlock strictly enforces Antarctic treaty (Madrid Protocol) and life-support guardrails before any action reaches execution.

---

## 2. Phase 1: Digital Twin Core & Causal Graph Engine

```
                                  MASTER TWIN ENGINE
                             (backend/core/engine.py)
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
   ENVIRONMENT PILLAR         INFRASTRUCTURE PILLAR            ENERGY PILLAR
  (87 sensors / 9 domains)    (180 sensors / 11 domains)   (48 sensors / 6 domains)
           │                            │                            │
           └──────────────┬─────────────┴─────────────┬──────────────┘
                          ▼                           ▼
                   LOGISTICS PILLAR           CAUSAL GRAPH
               (98 sensors / 11 domains)  (backend/core/causal_graph.py)
                          │                           │
                          └─────────────┬─────────────┘
                                        ▼
                                  TWIN SANDBOX
                            (backend/core/sandbox.py)
```

### Component 1.1: `backend/core/engine.py` (`BharatiMasterTwinEngine`)

The central simulation orchestrator that owns all four sensor pillar registries and their underlying physics models.

#### Key Responsibilities:
- **Synchronized Multi-Pillar Clock**: Drives a single master simulation clock advancing all pillars in deterministic physical sequence.
- **Physical Boundary Propagation**:
  1. $\text{Environment.step}(dt)$: Generates ambient temperature, katabatic wind velocity, barometric pressure, solar irradiance, and sea ice drift.
  2. $\text{Infrastructure.update\_from\_environment}(\text{env\_data})$: Applies ambient conditions to building thermal envelope, utilidor heat loss, and structural wind drag.
  3. $\text{Infrastructure.step}(dt)$: Computes zone temperatures, indoor air quality, water production, and derives:
     - Total Auxiliary Electrical Demand ($\text{kW}_{\text{aux}}$: HVAC fans, RO pumps, MBR blowers, trace heating).
     - Station Heating Demand ($\text{kW}_{\text{th}}$: AHU heating coils, domestic hot water, pipe freeze protection).
  4. $\text{Energy.update\_demands}(\text{load\_kw}, \text{heat\_kwth})$: Injects infrastructure load into the MLVD bus and hydronic loop.
  5. $\text{Energy.step}(dt)$: Dispatches active CHP generators (100 kVA Scania units), modulates waste-heat heat exchangers, regulates UPS battery floating, and drains the fuel day-tank with automated bulk-farm refill.
  6. $\text{Logistics.update\_cross\_pillar}(\text{env\_data}, \text{energy\_data})$: Feeds wind/visibility to helipad and vehicle routes; feeds grid status to reefer cold containers.
  7. $\text{Logistics.step}(dt)$: Updates vehicle telemetry, fuel levels, cargo integrity, route accessibility, and mission status.
- **Scenario Injection Framework**:
  - `inject_scenario(name: MasterScenario, **params)`: Clean deterministic API to inject station-wide crises:
    - `BLIZZARD_STRIKE`: Wind surges to 35 m/s, temp drops to $-35^\circ\text{C}$, helipad closes, thermal heat demand surges to 150 kWth.
    - `GENERATOR_TRIP`: Lead CHP-1 trips on overcurrent; grid droops, UPS-1 takes critical loads, standby CHP-2 auto-cranks.
    - `WATER_LINE_FREEZE`: Utilidor trace heating circuit trips; pipe temp drops below $0^\circ\text{C}$; RO production halts.
    - `COLD_CHAIN_EXCURSION`: Reefer compressor failure; vaccine/food core temperature rises above $-18^\circ\text{C}$.
    - `FUEL_TRANSFER_LEAK`: Bulk fuel transfer line valve fault; day-tank stops refilling.
- **Unified Query & Telemetry Export**:
  - `get_sensor_reading(sensor_id: str) -> SensorReading` (O(1) lookup across all 413 points).
  - `get_snapshot() -> MasterTwinSnapshot`: Comprehensive serializable telemetry snapshot.
  - `get_active_alerts() -> list[ActiveAlert]`: Scans all derived risk indices and threshold breaches.

---

### Component 1.2: `backend/core/causal_graph.py` (`TwinCausalGraph`)

A high-performance in-memory directed graph representing the physical topology, equipment dependencies, and sensor instrumentation of Bharati Station.

#### Data Models:
- `NodeType`: `ENVIRONMENT_SOURCE`, `EQUIPMENT_ASSET`, `DISTRIBUTION_BUS`, `ZONE_ENCLOSURE`, `STORAGE_RESERVOIR`, `PHYSICAL_SENSOR`, `MISSION_ENTITY`.
- `EdgeType`:
  - `THERMAL_TRANSFER` (e.g., CHP exhaust $\to$ Heat Exchanger $\to$ Glycol Loop $\to$ AHU Heating Coil).
  - `ELECTRICAL_FEED` (e.g., CHP-1 $\to$ MLVD Bus $\to$ UPS-1 $\to$ Critical Lab Bus $\to$ Medical Freezer).
  - `HYDRAULIC_FLOW` (e.g., Seawater Intake $\to$ RO Plant $\to$ Potable Water Reservoir $\to$ Galley).
  - `FUEL_SUPPLY` (e.g., Bulk Fuel Farm $\to$ Transfer Pump $\to$ Day Tank $\to$ CHP Fuel Injectors).
  - `ATMOSPHERIC_EXPOSURE` (e.g., Ambient Wind $\to$ Building Envelope $\to$ Helipad Status).
  - `SENSOR_OBSERVATION` (e.g., CHP-1 $\to$ `BH-ENG-CHP1-001` Active Power Sensor).
  - `LOGICAL_INTERLOCK` (e.g., Fire Damper Zone 1 $\to$ AHU-01 Fan Shutdown).
- `CausalNode`: `node_id`, `name`, `node_type`, `subsystem`, `criticality` (1 to 5), `metadata`.
- `CausalEdge`: `source_id`, `target_id`, `edge_type`, `weight`, `latency_seconds` (time delay for physical propagation).

#### Core Algorithms:
- `get_upstream_causes(node_id: str, max_depth: int = 5) -> list[CausalPath]`:
  - Reverse BFS/DFS traversal following incoming physical edges.
  - Returns ordered candidate root causes with cumulative physical latency.
  - *Used by*: **Diagnostic / Root-Cause Agent**.
- `get_downstream_impacts(node_id: str, max_depth: int = 5) -> list[ImpactPath]`:
  - Forward BFS/DFS traversal following outgoing physical edges.
  - Traverses to all downstream equipment, zones, and life-support systems.
  - *Used by*: **Risk & Impact Agent**.
- `calculate_blast_radius(node_id: str) -> BlastRadius`:
  - Aggregates affected assets by criticality, life-support impact, and mission readiness impact.
- `export_react_flow_topology() -> dict[str, Any]`:
  - Serializes nodes, coordinates, node categories, and edge styles formatted specifically for React Flow canvas.

---

### Component 1.3: `backend/core/sandbox.py` (`TwinSandbox`)

An ultra-fast in-memory state-forking and simulation engine that enables predictive what-if scenario exploration without corrupting active station telemetry.

#### Key Mechanics:
- `fork(engine: BharatiMasterTwinEngine) -> TwinSandbox`:
  - Clones the complete master twin state in memory ($< 5\,\text{ms}$).
  - Decoupled from live wall-clock timers.
- `apply_action_override(subsystem: str, parameter: str, value: Any)`:
  - Injects candidate operational changes into the sandbox state (e.g. `chps[1].operating_state = "RUNNING"`, `hvac.ahu01_fresh_air_damper_pct = 15.0`).
- `run_fast_forward(duration_seconds: float, dt: float = 1.0) -> TrajectoryResult`:
  - Executes accelerated forward simulation (e.g., 4 hours of physical time / 14,400 ticks computed in $< 25\,\text{ms}$).
  - Records continuous time-series metrics:
    - Fuel consumption rate and day-tank exhaustion runway.
    - Indoor zone temperatures (thermal decay or stabilization).
    - UPS battery SOC trajectory.
    - Water production balance.
    - Composite station risk index.
- `evaluate_plan_delta(baseline: TrajectoryResult, candidate: TrajectoryResult) -> PlanEvaluationDelta`:
  - Generates clear KPI comparison: $\Delta\text{Fuel}$, $\Delta\text{Temp}$, $\Delta\text{Autonomy}$, $\Delta\text{RiskScore}$.
  - *Used by*: **What-If Simulation Agent** and **Planning Agent**.

---

## 3. Phase 2: Multi-Agent Framework & Safety Interlock Layer

```
                        AGENT MESSAGE BUS (backend/agents/framework/bus.py)
                          [Pub/Sub Broker | Priority Queues | Audit Trail]
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  DELIBERATION SESSION          SAFETY INTERLOCK               BASE AGENT
 (Blackboard & Context)      (Tier 1 / 2 / 3 Guardrails)    (Standard ABC Interface)
```

### Component 2.1: `backend/agents/framework/models.py`

Strictly typed dataclasses and enums governing all inter-agent messages, operational plans, and safety tiers.

#### Enums:
- `AgentRole`: `SITUATION_AWARENESS`, `DIAGNOSTIC`, `PREDICTION`, `RISK_IMPACT`, `PLANNING`, `WHAT_IF`, `MISSION_OPS`, `MAINTENANCE`, `RESOURCE_OPTIMIZER`, `FRIDAY_ORCHESTRATOR`.
- `MessageType`: `ALERT`, `QUERY`, `DIAGNOSIS`, `PREDICTION_PROJECTION`, `IMPACT_ASSESSMENT`, `PROPOSAL`, `CRITIQUE`, `SIM_REQUEST`, `SIM_RESULT`, `CONSENSUS_PLAN`, `OPERATOR_COMMAND`.
- `SeverityLevel`: `INFO`, `ADVISORY`, `WARNING`, `CRITICAL`, `EMERGENCY`.
- `AutonomyTier`:
  - `TIER_1_AUTONOMOUS`: Safe, non-destructive, reversible micro-actions (e.g., damper micro-trim, automated logging, sensor self-test).
  - `TIER_2_SUPERVISED`: Operational load adjustments with a 60-second veto countdown (e.g., HVAC setpoint adjustment $\pm 1.5^\circ\text{C}$, non-critical pump switchover).
  - `TIER_3_COMMANDER_CONFIRMATION`: Life-safety or mission-critical actions requiring explicit human Commander sign-off (e.g., generator shutdown, power load shedding to living modules, field team recall).
- `ProposalStatus`: `DRAFT`, `SIMULATING`, `SIMULATED`, `APPROVED_PENDING_CONFIRMATION`, `EXECUTED`, `VETOED`, `REJECTED`.

#### Dataclasses:
- `AgentMessage`:
  - `message_id: str`, `session_id: str`, `sender: AgentRole`, `recipient: AgentRole | Literal["BROADCAST"]`, `message_type: MessageType`, `severity: SeverityLevel`, `payload: dict[str, Any]`, `confidence: float` (0.0 to 1.0), `timestamp: float`.
- `ActionProposal`:
  - `proposal_id: str`, `title: str`, `target_subsystem: str`, `parameter_overrides: dict[str, Any]`, `tier: AutonomyTier`, `rationale: str`, `projected_impact: dict[str, Any]`, `simulation_delta: dict[str, Any] | None`, `status: ProposalStatus`.
- `DeliberationSession`:
  - Blackboard shared among agents during an incident.
  - Contains `session_id`, `trigger_alert`, `root_causes`, `predictions`, `risk_assessment`, `candidate_proposals`, `critiques`, and chronological message transcript.

---

### Component 2.2: `backend/agents/framework/bus.py` (`AgentMessageBus`)

The high-performance in-memory pub/sub message broker connecting all agents.

#### Key Mechanics:
- **Role-Based & Topic Subscriptions**:
  - Agents subscribe to specific message types (e.g. `DiagnosticAgent` subscribes to `ALERT`, `WhatIfAgent` subscribes to `SIM_REQUEST`).
  - Broadcast support for station-wide situational updates.
- **Priority Queueing**:
  - `EMERGENCY` and `CRITICAL` messages jump the queue, ensuring instant response during life-support failures.
- **Dialogue Transcript & Audit Trail**:
  - Automatically records every message sent during a deliberation session.
  - Provides queryable history (`get_session_transcript(session_id)`) for UI streaming and post-incident investigation.
- **Synchronous & Asynchronous Dispatch**:
  - Supports deterministic sequential dispatch in test harnesses and non-blocking asynchronous dispatch for FastAPI WebSocket streaming.

---

### Component 2.3: `backend/agents/framework/safety_interlock.py` (`SafetyInterlockManager`)

The mission-critical gatekeeper enforcing physical station constraints and preventing hazardous autonomous operations.

#### Antarctic Life-Support Safety Guardrails:
1. **Thermal Guardrail**:
   - Living and sleeping zone temperature cannot be commanded below $16.0^\circ\text{C}$.
   - Emergency shelter minimum temperature must remain $\ge 12.0^\circ\text{C}$.
2. **Electrical Power Guardrail**:
   - Generator electrical loading must never exceed $95\%$ of continuous rating (80 kW on a 100 kVA Scania unit).
   - UPS battery state-of-charge must never be intentionally drained below $50\%$ unless total station blackout occurs.
3. **Potable Water & Hygiene Guardrail**:
   - Station potable storage must not be depleted below 3 days of autonomy (minimum 1,500 L).
4. **Fire & Smoke Containment Guardrail**:
   - Fire dampers cannot be overridden open when smoke obscuration is detected in the zone ($> 1.5\%$).
5. **Field Traverse & Aviation Guardrail**:
   - No outdoor traverse or helicopter departure can be cleared if wind speed $> 20\,\text{m/s}$ or visibility $< 800\,\text{m}$.
6. **Madrid Protocol Environmental Compliance Guardrail**:
   - Wastewater effluent COD must be $< 100\,\text{mg/L}$ and BOD $< 25\,\text{mg/L}$ before environmental discharge valve is permitted to open.

#### Execution Policy:
- `validate_proposal(proposal: ActionProposal, current_state: MasterTwinSnapshot) -> SafetyValidationResult`:
  - Evaluates proposal against all guardrails.
  - If violated: rejects proposal with explicit safety violation code and explanation.
  - If compliant: assigns required `AutonomyTier`.
- `execute_action(proposal: ActionProposal, engine: BharatiMasterTwinEngine, commander_auth: bool = False) -> ExecutionResult`:
  - Tier 1: Executes immediately on engine.
  - Tier 2: Queues action with 60-second timeout.
  - Tier 3: Requires `commander_auth == True`; otherwise rejects with `CONFIRMATION_REQUIRED`.

---

### Component 2.4: `backend/agents/framework/base_agent.py` (`BaseSpecializedAgent`)

The foundational abstract base class for all 9 cognitive agents and the Friday Orchestrator.

#### Core Interface:
```python
class BaseSpecializedAgent(ABC):
    def __init__(self, role: AgentRole, bus: AgentMessageBus, engine: BharatiMasterTwinEngine, graph: TwinCausalGraph):
        ...

    @abstractmethod
    def handle_message(self, message: AgentMessage, session: DeliberationSession) -> None:
        """Process incoming bus message and update the deliberation session."""
        pass

    def publish_message(self, session_id: str, recipient: AgentRole | str, msg_type: MessageType, severity: SeverityLevel, payload: dict[str, Any], confidence: float = 1.0) -> None:
        """Helper to construct and publish a typed message to the bus."""
        ...
```

---

## 4. Implementation Steps & File Structure

```
backend/
  core/
    __init__.py
    engine.py             # BharatiMasterTwinEngine (Unified multi-pillar simulation)
    causal_graph.py       # TwinCausalGraph (Topological causal dependencies)
    sandbox.py            # TwinSandbox (In-memory state forking & fast-forward)
  agents/
    __init__.py
    framework/
      __init__.py
      models.py           # Typed dataclasses, enums, message contracts
      bus.py              # AgentMessageBus (Pub/sub broker & audit trail)
      safety_interlock.py # SafetyInterlockManager (Tiered autonomy & safety bounds)
      base_agent.py       # BaseSpecializedAgent (Abstract base class)
tests/
  core/
    __init__.py
    test_twin_core.py     # Unified tick, causality, and sandbox tests
  agents/
    __init__.py
    test_framework.py     # Bus, safety interlock, and blackboard tests
```

---

## 5. Verification & Testing Plan

### Automated Test Suites:

1. **`tests/core/test_twin_core.py`**:
   - `test_master_engine_initialization()`: Verifies all 413 sensors registered and all 4 physics states initialized.
   - `test_master_clock_synchronization()`: Verifies stepping master engine advances time synchronously across all 4 pillars.
   - `test_cross_pillar_physical_ripple()`: Injects blizzard $\to$ verifies envelope heat loss $\to$ verifies HVAC valve opens $\to$ verifies CHP load increases $\to$ verifies fuel consumption accelerates.
   - `test_causal_graph_structure()`: Verifies node count, edge count, and presence of all 4 pillars in the graph.
   - `test_causal_graph_upstream_root_cause()`: Tests fault in `CHP-1` $\to$ verifies upstream trace locates fuel delivery / electrical governor.
   - `test_causal_graph_downstream_blast_radius()`: Tests loss of MLVD bus $\to$ verifies downstream impact on UPS, AHUs, RO plant, and Reefers.
   - `test_causal_graph_react_flow_export()`: Verifies export format contains valid nodes, coordinates, and edges.
   - `test_sandbox_state_isolation()`: Verifies mutating sandbox state does NOT alter the active master twin state.
   - `test_sandbox_fast_forward_performance()`: Benchmarks 4-hour forward simulation to ensure completion in $< 50\,\text{ms}$.

2. **`tests/agents/test_framework.py`**:
   - `test_bus_publish_and_subscribe()`: Verifies targeted message delivery and broadcast.
   - `test_bus_priority_queueing()`: Verifies `EMERGENCY` messages are delivered before `INFO` messages.
   - `test_deliberation_session_blackboard()`: Verifies multiple agents can read and append to a shared session.
   - `test_safety_interlock_tier_1_execution()`: Verifies safe minor adjustment executes autonomously.
   - `test_safety_interlock_tier_3_guardrail_rejection()`: Verifies attempt to shed medical zone or trip main breaker is blocked without Commander PIN.
   - `test_safety_interlock_thermal_minimum_enforcement()`: Verifies attempt to set indoor temp to $10^\circ\text{C}$ is rejected by life-support safety rule.

3. **Full Project Regression Run**:
   - `python -m pytest tests/` must execute all 146 existing sensor tests + all new core/framework tests, achieving 100% pass rate with 0 errors and 0 failures.

---

## 6. User Review & Approval Gateway

> [!IMPORTANT]
> **Next Action**:
> This implementation plan focuses **exclusively on Phase 1 and Phase 2**.
> Once approved, we will build:
> 1. `backend/core/` (`engine.py`, `causal_graph.py`, `sandbox.py`) and verify with `tests/core/test_twin_core.py`.
> 2. `backend/agents/framework/` (`models.py`, `bus.py`, `safety_interlock.py`, `base_agent.py`) and verify with `tests/agents/test_framework.py`.
>
> Please confirm if you approve starting implementation of **Phase 1**!
