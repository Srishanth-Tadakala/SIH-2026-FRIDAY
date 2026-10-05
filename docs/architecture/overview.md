# F.R.I.D.A.Y. Architectural Overview

## Executive Summary

**F.R.I.D.A.Y.** (*Fleet, Resource, Infrastructure, Diagnostics, Automation & Yield*) is a mission-grade, edge-native digital twin and multi-agent cognitive operations platform designed for remote management and autonomous life-support preservation of Indian Antarctic Research Stations:
- **Bharati Station** (Larsemann Hills, East Antarctica — $69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$)
- **Maitri Station** (Schirmacher Oasis, East Antarctica — $70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$)
- **Mainland Mission Control**: National Centre for Polar and Ocean Research (NCPOR), Ministry of Earth Sciences (MoES), Goa, India.

The platform was originally architected under **Smart India Hackathon 2026** (Problem Statement **SIH26060**).

---

## The Operational Challenge

Operating scientific stations in Antarctica presents extreme conditions:
1. **Severe Sub-Zero Thermodynamics**: Ambient temperatures fall to $-55^\circ\text{C}$ with katabatic blizzard wind gusts exceeding $160\text{ km/h}$.
2. **Utilidor Freeze Vulnerability**: utilidor utility conduits (carrying potable water, fire suppression water, and sewage) freeze solid within **18 minutes** of a combined heat and power (CHP) microgrid failure.
3. **Severe Satellite Constrained Uplink**: Station communication relies on polar satellite links (Iridium / Inmarsat) with bandwidths constrained to $2.4\text{ kbps}$, latency of $600\text{–}1800\text{ ms}$, packet jitter, and frequent multi-hour solar or geomagnetic blackout periods.
4. **Isolated Human Crew**: Station crews are completely cut off from physical evacuation for 8 to 9 months during the austral winter polar night.

---

## Architectural Principles

F.R.I.D.A.Y. addresses these operational realities through five foundational design invariants:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE DESIGN INVARIANTS                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. 100% Offline Polar Autonomy: Never depend on cloud connectivity.    │
│ 2. Deterministic Physics Grounding: 505 physical sensor channels/base. │
│ 3. 3-Tier Safety Interlock: AI proposes, but strict rules govern.      │
│ 4. Bandwidth-Aware Satcom Sync: >90% telemetry data reduction.         │
│ 5. Dual-Mode Zero-Breakage Storage: Auto-fallback to embedded atomic.  │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. 100% Offline Edge Autonomy
The station edge node must function fully autonomously even when disconnected from mainland headquarters. Cloud LLM inferences (via Groq LPU) are non-blocking enhancements with sub-millisecond local deterministic fallback engines.

### 2. Deterministic Physics Grounding
Sensors and actuators are not treated as abstract key-value pairs. They are governed by thermodynamic differential decay equations, electrical load balance constraints, and fluid dynamic pipe networks calibrated to Bharati and Maitri equipment specifications.

### 3. Three-Tier Safety Interlock Architecture
AI models (LLMs and cognitive agents) are strictly prevented from executing physical commands directly. All action proposals must traverse the safety policy engine:
- **Tier 1 (Autonomous Micro-Adjustment)**: Low-risk, reversible setpoint adjustments (e.g., radiator valve $\pm 2\%$) execute in $<1.2\text{s}$.
- **Tier 2 (Supervised Operational Transfer)**: Significant adjustments (e.g., HVAC air circulation mode shift) trigger a 60-second supervised countdown with human operator veto capability.
- **Tier 3 (Station Commander Emergency Interlock)**: High-consequence actions (diesel generator cutover, load shedding, blast seal lockdown) require physical Station Commander PIN authorization and single-use HMAC-SHA256 tokens.

### 4. Bandwidth-Aware Polar Satcom Delta Protocol
Rather than streaming raw JSON over satellite transponders, F.R.I.D.A.Y. uses deadband filtering, differential state delta encoding, and RFC 5050/9171 Delay-Tolerant Networking (DTN) bundle protocols, reducing satcom uplink bandwidth consumption by **90.2%**.

### 5. Dual-Mode Storage Resilience
The platform operates on MongoDB (local edge and Atlas cloud). If MongoDB is offline, uninstalled, or restarting, F.R.I.D.A.Y. seamlessly falls back to an embedded, atomic, file-backed JSON document store without dropping telemetry samples or interrupting the 1 Hz autonomous loop.
