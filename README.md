# F.R.I.D.A.Y. — Antarctic Digital Twin & Multi-Agent Cognitive Platform

**SIH 2026 Problem Statement**: SIH26060  
**Title**: *Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations*  
**Target Stations**: 
- **Bharati Station** (Larsemann Hills, East Antarctica — $69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$)
- **Maitri Station** (Schirmacher Oasis, East Antarctica — $70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$)

---

## Executive Summary

**F.R.I.D.A.Y.** (*Fleet, Resource, Infrastructure, Diagnostics, Automation, & Yield*) is a mission-critical digital twin and autonomous multi-agent cognitive architecture developed for remote management of India's Antarctic research stations. Operating in the extreme polar environment of East Antarctica, F.R.I.D.A.Y. bridges physical telemetry, deterministic cross-pillar physics, in-memory what-if simulations, and an inter-agent deliberation protocol to deliver unprecedented operational resilience, life-support assurance, and fuel optimization under constrained satellite communications.

---

## Key Architecture Layers

```
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                          5. REACT FLOW DIGITAL TWIN FRONTEND                              │
│              (Topological Live Node-Edge Station Schematic + Agent Chat Stream)           │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                     4. SATCOM BANDWIDTH-AWARE DELTA PROTOCOL                              │
│          (<32 kbps Bandwidth, 850ms Simulated Polar Latency, Local Edge Autonomy)         │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│            3. F.R.I.D.A.Y. MASTER ORCHESTRATOR & 9 SPECIALIZED COGNITIVE AGENTS           │
│   (Situation Awareness, Diagnostic/RCA, Prediction, Risk, Planning, What-If, Mission Ops) │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                  2. AGENT MESSAGE BUS & TIERED SAFETY INTERLOCKS                          │
│          (Pub/Sub Broker, Shared Blackboard Session, Tier 1/2/3 Autonomy Guardrails)      │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│                       1. DIGITAL TWIN CORE & CAUSAL GRAPH ENGINE                          │
│        (Unified Master Engine, Topological Causal Graph, In-Memory Sandbox Forking)       │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│               [FOUNDATION COMPLETE] 4-PILLAR PHYSICAL OBSERVATION SENSORS                 │
│               • Energy (48 points)         • Infrastructure (180 points)                  │
│               • Environment (87 points)    • Logistics (98 points)                        │
│               ► Total: 413 Configured Points across 37 Domains (146 Tests Green)           │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4-Pillar Observation Layer (413 Points)

The foundation of F.R.I.D.A.Y. is built on deterministic, physics-bound telemetry representing the station's physical reality:

| Pillar | Sensors | Domains | Description |
| :--- | :---: | :---: | :--- |
| **Energy** | 48 | 6 | Three 100 kVA Scania CHPs, MLVD bus, Two 60 kVA UPS plants, 3-lakh L fuel farm, day tank, hydronic waste-heat recovery. |
| **Infrastructure** | 180 | 11 | Building structural stilts, HVAC air handlers, RO desalination plant, MBR wastewater, cold provisions, utilidor pipelines, fire safety. |
| **Environment** | 87 | 9 | AWS weather, surface radiation, katabatic winds, air quality, snow drift, ocean acoustics, atmospheric electricity, scientific instruments. |
| **Logistics** | 98 | 11 | PistenBully PB-01 to PB-06 fleet, heavy cranes, ISO containers, fuel logistics, cold chain reefers, aviation helipad, marine sea berths, Madrid Protocol waste. |
| **Total** | **413** | **37** | **146 unit tests passing with 100% code correctness in 1.12s.** |

---

## Deterministic Cross-Pillar Physical Propagation

F.R.I.D.A.Y. does not rely on random data mocks. Telemetry follows first-principles physical causality:
$$\text{Environment (Katabatic Blizzard)} \longrightarrow \text{Building Envelope (Conductive Heat Loss)} \longrightarrow \text{HVAC (Heating Demand Surge)}$$
$$\longrightarrow \text{Energy (CHP Electrical/Thermal Load Escalation)} \longrightarrow \text{Fuel Farm (Day-Tank Depletion)} \longrightarrow \text{Logistics (Helipad & Route Closure)}$$

---

## Multi-Agent Cognitive Architecture

Under the **F.R.I.D.A.Y. Core Orchestrator**, 9 specialized cognitive agents collaborate via an event-driven message bus:

1. **Situation Awareness Agent**: Scans 413 points every tick; detects rate-of-change anomalies and threshold breaches.
2. **Diagnostic / Root-Cause Agent**: Traverses the `TwinCausalGraph` upstream to eliminate symptom cascades and isolate fault origins.
3. **Prediction Agent**: Computes physical time-to-critical countdowns (time-to-freeze, hours of fuel runway, battery drain).
4. **Risk & Impact Agent**: Evaluates downstream blast radius across Life Support, Grid Power, Structural Health, and Mission Readiness.
5. **Planning / Recommendation Agent**: Formulates 2–3 operational mitigation options with clear parameter overrides.
6. **What-If / Simulation Agent**: Forks in-memory state sandboxes ($<5\,\text{ms}$) and fast-forwards physical simulation 4 hours into the future ($1000\times$ real-time).
7. **Mission Operations Agent**: Evaluates environmental accessibility, traction, and visibility to compute strict Go / Caution / No-Go status for field expeditions and flights.
8. **Maintenance Agent**: Tracks machine run hours, warehouse spare parts inventory, and Madrid Protocol waste return compliance.
9. **Resource Optimization Agent**: Optimizes global fuel burn against indoor thermal comfort, RO batch timing, and battery degradation.

---

## Safety Interlocks & Tiered Autonomy

To ensure absolute safety in extreme Antarctic conditions:
- **Tier 1 (Autonomous)**: Safe, reversible adjustments (e.g. damper throttling, self-diagnostics).
- **Tier 2 (Supervised)**: Moderate adjustments with a 60-second countdown veto window for station engineers.
- **Tier 3 (Commander Confirmation)**: Life-critical operations (load shedding, generator shutdown, traverse dispatch) strictly requiring human Commander authorization.

---

## Getting Started

### Prerequisites
- Python 3.12+ (Standard library only; zero external heavy dependencies for core engine)
- Pytest

### Running the Test Suite
```bash
# Run all 146 unit tests across the 4 pillars
python -m pytest tests/ -v
```

### Running Interactive Pillar Demos
```bash
# Energy Pillar Demo
python tools/demos/demo_energy_sensors.py

# Infrastructure Pillar Demo
python tools/demos/demo_infrastructure_sensors.py

# Environment Pillar Demo
python tools/demos/demo_environment_sensors.py

# Logistics Pillar Demo
python tools/demos/demo_logistics_sensors.py
```

---

## Project Status

- [x] **Pillar 1: Energy Observation Layer** (48 points, 24 unit tests)
- [x] **Pillar 2: Infrastructure Observation Layer** (180 points, 30 unit tests)
- [x] **Pillar 3: Environment Observation Layer** (87 points, 42 unit tests)
- [x] **Pillar 4: Logistics Observation Layer** (98 points, 50 unit tests)
- [x] **Regression Test Suite** (146 unit tests passing in ~1.1s)
- [x] **Phase 1 & 2 Industrial Architecture Specification**
- [ ] **Phase 1: Digital Twin Core & Causal Graph Engine** (*In Progress*)
- [ ] **Phase 2: Multi-Agent Framework & Safety Interlocks**
- [ ] **Phase 3: The 9 Cognitive Agents & Friday Orchestrator**
- [ ] **Phase 4: Satcom Delta Protocol & FastAPI Backend**
- [ ] **Phase 5: React Flow Digital Twin Frontend**

---

## License
MIT License. See [LICENSE](LICENSE) for details.
