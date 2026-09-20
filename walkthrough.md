# Walkthrough: Sub-Phase 4.2 Implementation (Polar Satcom Bandwidth-Aware Sync Protocol & Mainland Mirror Twin)

**Project**: SIH 2026 SIH26060 — *F.R.I.D.A.Y. (Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations)*  
**Target Stations**: 
- **Bharati Station** (Larsemann Hills, East Antarctica — $69^\circ 24' 28''\text{ S}, 76^\circ 11' 14''\text{ E}$)
- **Maitri Station** (Schirmacher Oasis, East Antarctica — $70^\circ 45' 58''\text{ S}, 11^\circ 43' 50''\text{ E}$)
- **Mainland Command**: National Centre for Polar and Ocean Research (NCPOR), Vasco da Gama, Goa & MoES, New Delhi  

**Status**: 
- **Phase 1**: Digital Twin Core & Causal Graph Engine (Completed & Verified — 14 tests)  
- **Phase 2**: Multi-Agent Message Bus & Safety Interlocks (Completed & Verified — 11 tests)  
- **Phase 3**: All 10 Specialized Cognitive Agents (Completed & Verified — 72 tests)  
- **Phase 4 (In Progress)**:
  - **Sub-Phase 4.1**: FastAPI Engine Core & Dual-Station REST Endpoints (**Completed & Verified — 10 tests**)  
  - **Sub-Phase 4.2**: Polar Satcom Delta-Sync Protocol & Mainland Mirror Twin (**Completed & Verified — 8 tests**)  
  - **Sub-Phase 4.3**: Real-Time Multiplexed WebSocket Streaming Engine (Next up)  
- **Phase 5**: Tactical Polar Digital Twin & Remote Cockpit (Vite + React + React Flow + Animated Subsystem Schematic)  
**Total Test Results**: **261 passed (0 failures, 0 errors, 100% green in 44.81s)**.

---

## 1. Polar Satcom Architectural Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       POLAR SATELLITE TELEMETRY SYNCHRONIZATION PIPELINE                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
      ANTARCTIC RESEARCH STATIONS                                              MAINLAND HEADQUARTERS
   (Bharati Station / Maitri Station)                                     (NCPOR Goa / MoES New Delhi)

  ┌─────────────────────────────────┐                                    ┌───────────────────────────────────┐
  │   Station Digital Twin Engine   │                                    │    Mainland Mirror Twin Engine    │
  │   • 505 Physical Sensor Points  │                                    │    • Full 505 Reconstructed Twin │
  │   • 4 Pillars / 37 Subsystems   │                                    │    • O(1) Real-Time Sensor Lookup │
  │   • Active Crisis Scenarios     │                                    │    • SHA-256 State Checksum Parity│
  └────────────────┬────────────────┘                                    └─────────────────▲─────────────────┘
                   │                                                                       │
  ┌────────────────▼────────────────┐                                    ┌─────────────────┴─────────────────┐
  │        Deadband Filter          │                                    │      Satcom Deserializer &        │
  │  • Temp: ±0.20°C                │                                    │      Frame Sequence Validator     │
  │  • Power/Load: ±0.50 kW         │                                    │  • Validates Monotonic Sequence   │
  │  • Tank/SOC: ±0.50%             │                                    │  • Detects Dropped Packet Gaps    │
  │  • Discrete Flags: Immediate    │                                    │  • Triggers Keyframe Resync       │
  └────────────────┬────────────────┘                                    └─────────────────▲─────────────────┘
                   │ Filtered Channels                                                     │
  ┌────────────────▼────────────────┐                                                      │
  │      Sparse Delta Encoder       │                                                      │
  │  • Frame 1: Full Baseline KEY   │                                                      │
  │  • Frame 2+: Sparse DELTA (N<20)│                                                      │
  │  • Sequence Number Counter      │                                                      │
  └────────────────┬────────────────┘                                                      │
                   │ SatcomFrame                                                           │
  ┌────────────────▼────────────────┐                                                      │
  │  Compressed Binary Serializer   │                                                      │
  │  • Header: b"FRDY\x01" (Magic)  │                                                      │
  │  • Zlib Level 9 Deflate Packing │                                                      │
  │  • >90% Bandwidth Reduction     │                                                      │
  └────────────────┬────────────────┘                                                      │
                   │ Binary Packet                                                         │
  ┌────────────────▼───────────────────────────────────────────────────────────────────────┴─────────────────┐
  │                                    POLAR SATCOM CHANNEL EMULATOR                                        │
  │  Profiles:                                                                                              │
  │  • LAN_DIRECT: 100 Mbps, 0ms latency, 0% packet loss (Control Room)                                     │
  │  • INMARSAT_STANDARD: 64 kbps, 850ms latency, 2% packet loss (Primary GEO BGAN)                           │
  │  • IRIDIUM_LOW: 9.6 kbps, 1500ms latency, 8% packet loss (Backup Polar LEO)                             │
  │  • POLAR_BLACKOUT: 0 kbps, inf latency, 100% loss (Solar storms / Radome icing)                        │
  │                                                                                                         │
  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────────┐  │
  │  │                            PRIORITIZED STORE-AND-FORWARD SPOOL QUEUE                              │  │
  │  │  • Priority 0 (CRITICAL): Alarms, Generator Trips, PIN Audits (Never dropped)                    │  │
  │  │  • Priority 1 (DELIBERATION): Multi-Agent Briefing Cards, Action Proposals                       │  │
  │  │  • Priority 2 (TELEMETRY): Routine Deltas (Bounded buffer, oldest evicted during multi-day blackout│  │
  │  │  ► Upon Link Restoration: Drains in strict priority order (0 -> 1 -> 2)                          │  │
  │  └───────────────────────────────────────────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Sub-Phase 4.2: Delivered Components

### 1. Polar Satcom Telemetry Protocol & Compression Engine
- [protocol.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/satcom/protocol.py):
  - **`DeadbandRule` & `DeadbandFilter`**:
    - Suppresses sensor telemetry jitter across steady-state operations.
    - Tailored physical deadbands: Temperatures ($\pm0.20\,^\circ\text{C}$), Electrical Loads ($\pm0.50\,\text{kW}$), Tank Levels ($\pm0.50\,\%$), Pressures ($\pm0.50\,\text{hPa}$), Flow Rates ($\pm0.50\,\text{L/h}$), Wind Speeds ($\pm0.30\,\text{m/s}$).
    - Discrete states, trips, alarms, and boolean flags have threshold $0.0$, guaranteeing immediate transmission upon state transitions.
    - Configurable `max_silence_seconds` ($60.0\,\text{s}$) heartbeat prevents channels from going stale.
  - **`FrameType` & `SatcomFrame`**:
    - Defines frame classifications: `KEYFRAME` (505 sensors baseline), `DELTA` (sparse channel diffs), `ALARM` (urgent warnings), `COMMAND_AUDIT` (PIN authorizations), `DELIBERATION_CARD` (multi-agent consensus), `HEARTBEAT`, and `RESYNC_REQUEST`.
    - Standardized metadata with sequence numbering, simulation timestamps, KPIs, active alarms, and delta counts.
  - **`DeltaEncoder`**:
    - Monotonically sequence-tracked differential frame encoding per station.
    - Initial frame is always an authoritative baseline `KEYFRAME`. Subsequent frames transmit sparse deltas containing only modified channels ($N < 20$ vs $505$).
  - **`CompressedSerializer`**:
    - Packs frames into compact binary payloads with magic header `b"FRDY\x01"` and zlib Level 9 compression.
    - Yields $>90\%$ payload reduction on full keyframes and compresses sparse deltas down to $< 300$ bytes.

### 2. Prioritized Store-and-Forward Spool Queue
- [store_and_forward.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/satcom/store_and_forward.py):
  - Multi-level prioritized ring buffer designed for polar blackouts:
    - **`PRIORITY_CRITICAL` ($0$)**: Emergency alarms, generator blackouts, PIN authorizations, commander overrides. Never dropped unless hard safety threshold is exceeded.
    - **`PRIORITY_DELIBERATION` ($1$)**: Explainable multi-agent briefing cards, proposed action plans, diagnostic root causes.
    - **`PRIORITY_TELEMETRY` ($2$)**: Routine sensor deltas and periodic snapshots. Bounded capacity with oldest-frame eviction to preserve satcom bandwidth.
  - Guarantees $O(1)$ enqueue and dequeue operations.
  - Drains in strict priority order upon link restoration ($0 \to 1 \to 2$).

### 3. Polar Satcom Channel Emulator
- [channel_emulator.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/satcom/channel_emulator.py):
  - Emulates physical characteristics of polar satellite constellations:
    - `LAN_DIRECT`: $100\,\text{Mbps}$, $0\,\text{ms}$, $0\%$ packet loss (Antarctic station control room LAN).
    - `INMARSAT_STANDARD`: $64\,\text{kbps}$, $850\,\text{ms}$ RTT latency, $2\%$ packet loss (Primary Inmarsat BGAN).
    - `IRIDIUM_LOW`: $9.6\,\text{kbps}$, $1500\,\text{ms}$ RTT latency, $8\%$ packet loss (Backup polar orbit LEO link).
    - `POLAR_BLACKOUT`: $0\,\text{kbps}$, $\infty\,\text{ms}$, $100\%$ packet loss (Solar coronal mass ejections, radome snow icing).
  - Automatically redirects frames to `PrioritizedSpoolQueue` during blackout conditions (`SPOOLED_BLACKOUT`).
  - Provides `recover_from_blackout()` to drain spooled frames in priority order when link connectivity is re-established.
  - Tracks cumulative transmitted bytes, raw uncompressed equivalent bytes, and total bandwidth savings.

### 4. Mainland Mirror Digital Twin Replica Engine
- [mirror_twin.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/satcom/mirror_twin.py):
  - Runs at Mainland Command (NCPOR Goa / MoES New Delhi).
  - Maintains a synchronized, reconstructed digital twin of Bharati and Maitri stations.
  - Validates frame sequence numbers: detects packet drops (`GAP_DETECTED`), flags `resync_required`, and generates `RESYNC_REQUEST` frames.
  - Computes deterministic SHA-256 state checksums to verify mathematical parity between remote Antarctic station engines and the mainland replica.
  - Provides $O(1)$ sensor lookup, active alerts, and cached deliberation briefing cards.

### 5. FastAPI REST API Integration
- [satcom.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/routes/satcom.py):
  - `GET /api/satcom/status`: Aggregated channel metrics, compression savings, and sync status for both stations.
  - `GET /api/satcom/{station_id}/summary`: Granular channel telemetry and mirror twin status for a specific station.
  - `GET /api/satcom/{station_id}/mirror`: Reconstructed mainland twin readings (all 505 sensors), KPIs, active alerts, and SHA-256 checksum.
  - `POST /api/satcom/profile`: Dynamically switch channel profiles (`LAN_DIRECT`, `INMARSAT_STANDARD`, `IRIDIUM_LOW`, `POLAR_BLACKOUT`).
  - `POST /api/satcom/{station_id}/sync`: Trigger manual satcom delta or keyframe transmission.
  - `POST /api/satcom/{station_id}/recover`: Restore satellite connection from blackout and drain the prioritized spool queue.
  - `POST /api/satcom/{station_id}/resync`: Force full keyframe resynchronization to heal sequence gaps.
- [state.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/state.py):
  - Embedded satcom encoders, emulators, and mainland mirror engines into `ServerState`.
  - Automatic background delta transmission on simulation clock steps.
- [app.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/backend/server/app.py):
  - Registered `satcom_router` in FastAPI application and exposed `satcom_sync_active: True` in `/api/health`.

---

## 3. Test Verification & Zero Regressions

A dedicated test suite was implemented in [test_satcom_protocol.py](file:///c:/Users/siddu/OneDrive/Desktop/F.R.I.D.A.Y/tests/satcom/test_satcom_protocol.py) covering all Sub-Phase 4.2 capabilities:
1. `test_deadband_filtering_dampens_jitter`: Verified steady-state jitter suppression, deadband thresholds, and discrete flag triggers.
2. `test_delta_encoder_keyframe_and_sparse_delta`: Verified 505-sensor baseline keyframe generation and sparse delta frames.
3. `test_compressed_serializer_binary_efficiency`: Verified binary header `b"FRDY\x01"`, zlib Level 9 deflation, and $>90\%$ bandwidth savings.
4. `test_prioritized_spool_queue_ordering_and_eviction`: Verified strict priority draining ($0 > 1 > 2$) and bounded telemetry eviction.
5. `test_polar_channel_emulator_profiles_and_blackout`: Verified profile switching, latency simulation, blackout spooling, and priority recovery.
6. `test_mainland_mirror_twin_state_reconstruction_and_checksum`: Verified exact state reconstruction, $O(1)$ lookup, and SHA-256 checksum parity.
7. `test_mainland_mirror_twin_gap_detection_and_resync`: Verified sequence gap detection (`GAP_DETECTED`) and keyframe healing.
8. `test_satcom_rest_api_endpoints`: Verified FastAPI REST endpoints for satcom status, mirror twin, profile switching, spool recovery, and resync.

### Full Regression Suite Run:
```bash
python -m pytest
============================ 261 passed in 44.81s =============================
```
- **Total Tests**: 261 / 261 passed (100% green).
- **Test Breakdown**:
  - Sensors (Energy, Environment, Infrastructure, Logistics): **146 tests**
  - Digital Twin Core & Causal Graph: **14 tests**
  - Multi-Agent Message Bus & Safety Interlocks: **11 tests**
  - 10 Specialized Cognitive Agents & Orchestrator: **72 tests**
  - FastAPI Server REST Endpoints (Sub-Phase 4.1): **10 tests**
  - Polar Satcom Bandwidth-Aware Telemetry & Mirror Twin (Sub-Phase 4.2): **8 tests**
- **Git Commit**: `5675d43` pushed to `origin/main`.

---

## 4. Next Step: Sub-Phase 4.3 Implementation Plan

With Sub-Phase 4.1 and Sub-Phase 4.2 fully implemented, tested, and pushed, the next logical step in Phase 4 is:

### **Sub-Phase 4.3: Real-Time Multiplexed WebSocket Streaming Engine**
1. **WebSocket Protocol & Multiplexing**:
   - Create `backend/server/routes/ws.py` providing `/ws/telemetry/{station_id}`.
   - Channel multiplexing over a single connection:
     - `channel: "kpis"` (1 Hz high-level overview).
     - `channel: "sensors"` (selective subscription by sensor ID or pillar).
     - `channel: "alerts"` (immediate broadcast of new alarms).
     - `channel: "deliberations"` (live agent blackboard messages and briefing cards).
     - `channel: "satcom"` (satcom profile, bandwidth stats, blackout alerts).
2. **Client-Side Throttling & Backpressure**:
   - Dynamic rate-limiting based on connection profile (LAN: 10 Hz, Satcom: 0.1-1 Hz).
   - Heartbeat ping/pong and auto-reconnect handling.
3. **Unit & Integration Tests**:
   - WebSocket subscription testing using FastAPI TestClient with WebSocket transport.
   - Verifying selective channel subscriptions and delta broadcasting.
