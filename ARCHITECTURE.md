# F.R.I.D.A.Y. Technical Architecture & System Specification

**Project:** F.R.I.D.A.Y. (Fleet, Resource, Infrastructure, Diagnostics, Automation & Yield)  
**Initiative:** Smart India Hackathon (SIH 2026) — Problem Statement **SIH26060**  
**Sponsoring Client:** National Centre for Polar and Ocean Research (NCPOR), Ministry of Earth Sciences (MoES), Govt. of India  
**Operational Sites:** Bharati Station ($69^\circ 24'\text{ S}$), Maitri Station ($70^\circ 46'\text{ S}$), NCPOR Mainland HQ (Goa)

> 💡 **Notice**: For the modular, deep-dive architectural specifications, please refer to the [`docs/architecture/`](docs/architecture/) suite:
> - [System Overview](docs/architecture/overview.md)
> - [System Architecture & Topologies](docs/architecture/system-architecture.md)
> - [Frontend UI & Real-Time Visualization](docs/architecture/frontend.md)
> - [Backend API & Service Layer](docs/architecture/backend.md)
> - [Database & Persistence Subsystem](docs/architecture/database.md)
> - [505-Sensor Telemetry & Industrial Bridges](docs/architecture/telemetry.md)
> - [Deterministic Digital Twin & Causal Graph](docs/architecture/digital-twin.md)
> - [External Integrations & Satcom Protocol](docs/architecture/integrations.md)

---

## 1. High-Level System Architecture

F.R.I.D.A.Y. is designed as a distributed, edge-native, cognitive polar digital twin platform structured into distinct architectural layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER (UI)                           │
│  React 19 + TypeScript + Vite + TailwindCSS v4                              │
│  ├── Unified Station Cockpit (Telemetry, Alarms, Satcom, 3D Twin)          │
│  ├── React Flow Multi-Agent Deliberation DAG Visualization                  │
│  └── Three.js Interactive 3D Polar Habitat Modules                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / WebSocket (Multiplexed)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        API & OBSERVABILITY GATEWAY                          │
│  FastAPI + Uvicorn + JWT (HS256) + RBAC + Structured JSON Logging           │
│  ├── /api/auth/*       (Authentication, Token Issuance, Role Hierarchy)    │
│  ├── /api/stations/*   (Station Telemetry, 505 Sensors, Lifecycle)         │
│  ├── /api/actions/*    (Tiered Execution, Commander PIN, Safety Interlock) │
│  ├── /api/copilot/*    (Groq LPU Dialogue, Circuit Breaker, Offline Edge)   │
│  ├── /health/*         (Kubernetes Liveness, Readiness, Metrics)           │
│  └── /ws/telemetry/*   (Backpressure-Guarded WebSocket Multiplexer)        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Internal Event Bus (Isolated Callback Protection)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    SWARM INTELLIGENCE & REASONING CORE                      │
│  10-Agent Autonomous Deliberation Society                                   │
│  ├── Situation Awareness ───► Diagnostic Agent ───► Risk Impact Agent       │
│  ├── Prediction Agent    ───► Planning Agent   ───► Resource Optimizer      │
│  ├── Maintenance Agent   ───► Mission Ops      ───► What-If Simulation      │
│  └── Chief AI Governor: F.R.I.D.A.Y. Orchestrator                           │
│  ├── Groq LPU (Llama-3.3-70B) with 12s Timeout & 3-Failure Circuit Breaker  │
│  └── Local Deterministic Neural Synthesis (<1.4ms Edge Fallback)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Physics-Grounded State Evaluation
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                   DETERMINISTIC POLAR DIGITAL TWIN ENGINE                   │
│  Physical State Space across Bharati & Maitri Research Stations             │
│  ├── 505 Active Sensor Channels across 4 Critical Polar Life-Support Pillars:│
│  │   ├── Thermal & HVAC (CHP heat recovery, glycol loops, utilidors)        │
│  │   ├── Power & Microgrid (Diesel generators, battery bank, wind, solar)   │
│  │   ├── Water & Life Support (Snow melters, greywater, RO recycling)       │
│  │   └── Environmental & Weather (Katabatic wind, blizzard, solar radiation)│
│  ├── 35-Node Topological Causal Graph (Directed Acyclic Graph)              │
│  ├── Thermodynamic Differential Decay Equation Solver                       │
│  └── Counterfactual Sandboxing Engine (1000x Speed Acceleration)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Dual-Tier Persistence & Satcom Protocol
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                     STORAGE & POLAR SATCOM SUBSYSTEM                        │
│  Bandwidth-Constrained Antarctic Communications & Edge Storage              │
│  ├── EmbeddedDocumentStore: Atomic, zero-dependency JSON edge store        │
│  ├── MongoDB Atlas / Local MongoDB: Cloud sync with Dead-Letter Queue (DLQ)│
│  └── Polar SatCom Delta Protocol: 94.2% keyframe delta compression         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real Subsystems vs. Simulated Subsystems (Jury Disclosure)

To maintain absolute scientific and engineering integrity during evaluations and technical audits, the following distinction between physical hardware interfaces and simulated polar twin components is strictly documented:

| Subsystem | Operational Implementation | Fidelity & Verification Method |
| :--- | :--- | :--- |
| **Cognitive Swarm Agents (10)** | **100% Real Code & Real LLM** | Real Python async actors communicating over real event bus. Real Groq LPU inference via `llama-3.3-70b-versatile` API calls with circuit breaker protection. |
| **Safety Interlocks & Cryptography** | **100% Real Cryptographic Engine** | Real PBKDF2-HMAC-SHA256 (100k rounds) key derivation, real constant-time HMAC verification, real single-use token invalidation, real exponential lockout. |
| **API & WebSockets** | **100% Real Network Stack** | Real FastAPI ASGI server, real Uvicorn event loop, real JWT bearer token verification, real WebSocket streaming with backpressure protection. |
| **Polar SatCom Protocol** | **100% Real Protocol Implementation** | Real bit-level delta calculation, real keyframe compression, real packet prioritization, achieving 94.2% bandwidth reduction over mock satellite delay. |
| **Sensor Telemetry (505 Channels)** | **High-Fidelity Physics Simulation** | Real differential equations ($dT/dt = -k(T - T_{ext}) + Q_{in}$) simulating thermodynamic heat exchange, diesel generator fuel consumption, battery state of charge (SoC), and snow melter thermal mass. In production deployment, SCADA OPC-UA / Modbus TCP connectors bind directly to these 505 memory slots. |
| **Physical Actuators** | **Deterministic Digital Twin Virtualization** | Actuators mutate virtual digital twin state space with physical delay modeling, interlocking against safety violations before commanding physical PLCs. |

---

## 3. The 10-Agent Swarm Intelligence Society

F.R.I.D.A.Y. coordinates 10 specialized asynchronous agents governed by the Chief Orchestrator:

1. **Situation Awareness Agent**: Continuously aggregates 505 sensor channels, computing sliding Z-scores and rate-of-change ($dx/dt$) to detect anomalies within polar envelopes.
2. **Diagnostic Agent**: Traverses the 35-node topological causal DAG upstream in $<1.1\text{ ms}$ to isolate the true physical root cause from nuisance alarm floods.
3. **Risk Impact Agent**: Evaluates downstream hazards across human life support, structural integrity, and mission continuity.
4. **Prediction Agent**: Solves differential equations to calculate exact Time-to-Failure (TtF) (e.g., utilidor freeze countdown).
5. **Planning Agent**: Synthesizes tiered mitigation strategies using Case-Based Reasoning (CBR) and historical crisis episodes.
6. **Resource Optimizer**: Solves load-shedding and multi-commodity resource allocation (fuel, power, water) during severe polar constraints.
7. **Maintenance Agent**: Predicts machinery wear, fatigue cycles, and maintenance windows based on runtime hours and thermal cycling.
8. **Mission Ops Agent**: Coordinates scientific expeditions, outdoor sortie safety gates (wind $\le 45\text{ km/h}$), and runway conditions.
9. **What-If Simulation Agent**: Forks an in-memory digital twin sandbox at $1000\times$ speed ($<4.2\text{ ms}$) to counterfactually validate proposed actions before execution.
10. **Chief AI Governor (Orchestrator)**: Synthesizes agent recommendations, enforces the 3-Tier Autonomy Safety Interlock, and manages execution lifecycle.

---

## 4. Safety Interlock & Autonomy Tiers

Physical actuators cannot be toggled directly by an AI model. Every proposed intervention passes through the deterministic `SafetyInterlock`:

```
                    ┌────────────────────────────┐
                    │   Action Proposal from     │
                    │   Planning Agent / Copilot │
                    └─────────────┬──────────────┘
                                  │
                                  ▼
                    ┌────────────────────────────┐
                    │    Deterministic Safety    │ ──[Violates Life-Support]──► REJECTED (400)
                    │    Policy Validation       │
                    └─────────────┬──────────────┘
                                  │ [Passes Envelopes]
                                  ▼
               ┌──────────────────┴──────────────────┐
               ▼                                     ▼
        [ Tier 1: Autonomous ]             [ Tier 2: Supervised ]
        Reversible micro-trims             Operational state changes
        Executes immediately (<50ms)       Mandatory 60s countdown
                                           Real-time Operator Veto
                                                     │
                                                     ▼
                                          [ Tier 3: Commander ]
                                          High-risk / Life-support
                                          Requires Commander PIN
                                          + Single-use HMAC Token
```

---

## 5. Polar SatCom Differential Protocol

During solar storms or auroral geomagnetic disturbances, satellite communication bandwidth drops from 256 kbps to $<2.4\text{ kbps}$ or total blackout:
- **Baseline Payload**: Uncompressed 505-sensor JSON packet = $18.4\text{ KB}$ per tick.
- **SatCom Protocol**: Transmits full keyframes periodically; intermediate updates send only changed sensor indices with delta quantizations:
  $$\Delta = \text{quantize}(S_i(t) - S_i(t_{\text{key}}))$$
- **Bandwidth Reduction**: Yields an average payload of $1.07\text{ KB}$ (**$94.2\%$ bandwidth reduction**), ensuring telemetry flows continuously even over degraded polar satellite links.

---

## 6. Testing, Quality & Reliability Standards

- **355 Automated Backend Unit & Integration Tests (100% Passing)**:
  - Agent Society: 80 tests
  - Digital Twin Core & Sensors: 185 tests
  - SatCom Protocol: 8 tests
  - Database, Memory Persistence & Repositories: 16 tests
  - Security, RBAC & Failure Injection: 66 tests
- **16 Frontend Vitest Tests (100% Passing)**:
  - Token handling, session persistence, role decoding, telemetry stream ingestion, alerts lifecycle, memory queries, and honest unavailable state handling.
- **Production Build Validation**: Clean compilation via TypeScript (`tsc -b && vite build`) in $<600\text{ ms}$.

---

## 7. End-to-End Operational Data Flow Architecture

The F.R.I.D.A.Y. platform enforces a single authoritative source of truth across all tiers:

### A. Frontend Request & Control Flow (API)
```
[ User Interaction in React 19 UI ]
              │
              ▼
[ Authenticated API Client: api/client.ts ] ──(Injects Bearer Token / Handles ApiError)
              │
              ▼ HTTP (REST / OpenAPI Contract)
[ FastAPI Router: backend/server/routes/* ]
              │
              ▼
[ Domain Service Layer: StationService / SatcomService / MemoryRepo ]
              │
              ▼
[ Authoritative State: Digital Twin Engine / ACID Document Store ]
```

### B. Real-Time Telemetry & Event Streaming (WebSocket)
```
[ Digital Twin Physics Step / MessageBus Event ]
              │
              ▼
[ WebSocket Broadcast Multiplexer: ws_manager.py ]
  ├── Channel: kpis            (Station load, temperature, wind, risk index)
  ├── Channel: sensors         (505 individual physical telemetry channels)
  ├── Channel: alerts          (Operational & life-safety alerts)
  ├── Channel: deliberations   (Multi-agent consensus sessions)
  ├── Channel: satcom          (Polar mirror twin, delta frame stats)
  └── Channel: memory          (Agent retrieval events & new memory records)
              │
              ▼ WSS (Token Authenticated Query / Backpressure Buffer)
[ React Hook: useTelemetryStream.ts ]
              │ (Validates channels, handles reconnect, calculates stale-state)
              ▼
[ React Component Re-render: PolarCommandCanvas / StationCards / MemoryView ]
```

### C. Persistent Agent Memory & Context Injection Pipeline
```
[ Anomaly / Disturbance / Operational Event ]
              │
              ▼
[ Agent Reasoning Trigger: Planning / Diagnostic Agent ]
              │
              ▼ (Pre-Reasoning Memory Query)
[ Memory Repository: backend/database/repositories/memory_repo.py ]
  ├── 1. Partition Filter: (agent_role, station_id, memory_type)
  ├── 2. Vector Embedding & Keyword Relevance Scoring
  └── 3. Top-K Relevant Historical Memories Retrieved
              │
              ▼
[ Instrument Retrieval Telemetry Event: memory_retrieval_completed ]
  ├── Logged: query, memories_found, memory_ids, latency_ms, context_bytes
  └── Dispatched: MessageBus ──► WebSocket /ws/telemetry/* ──► MemoryView UI
              │
              ▼
[ Agent Context Construction ]
  ├── Injects: Relevant SOPs, historical incident resolutions, physical thresholds
  └── Passed To: Groq LPU (Llama-3.3-70B) / Edge Deterministic Neural Synthesis
              │
              ▼
[ Verified Safe Action Proposal / Outcome ]
              │
              ▼
[ New Memory Persisted: EmbeddedDocumentStore / PostgreSQL ]
```
