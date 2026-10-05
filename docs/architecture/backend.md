# Backend Architecture & Service Layer

## Technology Stack

The F.R.I.D.A.Y. backend is an asynchronous, high-throughput service layer engineered in **Python 3.12+ / 3.14**:
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) with asynchronous ASGI request processing
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) with multi-worker support
- **Data Validation & Settings**: [Pydantic v2](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Industrial Protocols**: [pymodbus](https://pymodbus.readthedocs.io/), [asyncua](https://github.com/FreeOpcUa/opcua-asyncio), [paho-mqtt](https://eclipse.dev/paho/index.php?page=clients/python/index.php)
- **Database Driver**: [Motor](https://motor.readthedocs.io/) (async MongoDB) with zero-dependency embedded JSON fallback
- **Authentication**: Cryptographic JWT ([PyJWT](https://pyjwt.readthedocs.io/)) with salted PBKDF2-HMAC-SHA256 password hashing
- **Testing**: [pytest](https://docs.pytest.org/) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

---

## Directory Structure

```text
backend/
├── app.py                      # FastAPI application factory & router registration
├── config.py                   # Strongly-typed settings layer with AliasChoices support
├── auth.py                     # RBAC definitions, JWT token encoding, PBKDF2 hashing
├── state.py                    # Master server state container (dual twins, agents, bus)
├── ws_manager.py               # WebSocket client connection & subscription manager
├── agents/                     # Multi-Agent Swarm Intelligence System
│   ├── framework/              # Base agent class, pub/sub bus, Groq LLM brain, schemas
│   ├── orchestrator/           # FridayMasterOrchestrator coordination logic
│   └── specialized/            # 9 domain-specialized cognitive agents
├── core/                       # Digital Twin physics engine, causal graph & safety rules
│   ├── engine.py               # Master twin state space & differential solver
│   ├── causal_graph.py         # 35-node topological DAG for root-cause fault isolation
│   ├── safety_policy.py        # Autonomous execution limits & safety invariants
│   └── sandbox.py              # Counterfactual predictive execution sandbox
├── database/                   # Dual-tier database connection, repositories & sync worker
├── environmental/              # AMPS polar weather & NOAA SWPC space weather integration
├── satcom/                     # Iridium satellite channel emulator, delta protocol & DTN
├── sensors/                    # 505 sensor definitions & industrial fieldbus bridges
│   ├── bharati_sensors/        # Sensor definitions across 4 operational pillars
│   └── bridges/                # Modbus TCP, OPC UA, BACnet, and MQTT async bridges
└── server/                     # API routing modules & controllers
    └── routes/                 # 18 domain-specific API routers
```

---

## 18 Registered API Routers

All endpoints are organized cleanly by domain in `backend/server/routes/`:

| Router Module | Base Path | Core Responsibilities |
| :--- | :--- | :--- |
| `auth.py` | `/api/v1/auth` | Login, JWT token generation, session verification, current user lookup (`/me`). |
| `health.py` | `/health`, `/api/health` | Container liveness probe, subsystem readiness probe, runtime metrics. |
| `stations.py` | `/api/stations` | Station metadata, operational active station selector, manual stepping. |
| `telemetry.py` | `/api/telemetry` | Snapshots, KPIs, alerts, sensor history, 4-pillar readings (`energy`, `infrastructure`, `environment`, `logistics`). |
| `telemetry_ingest.py` | `/api/v1/telemetry/ingest`| External telemetry ingestion gateway for SCADA bridges and field PLCs. |
| `actions.py` | `/api/actions` | Physical actuator status, pending execution queue, Station Commander PIN authorization. |
| `agents.py` | `/api/agents` | Status of all 10 cognitive agents, causal graph inspection, Groq status, dynamic call history. |
| `deliberations.py` | `/api/deliberations` | Consensus deliberation sessions, agent votes, executive briefing cards. |
| `scenarios.py` | `/api/scenarios` | Injection of simulated crises (generator trip, blizzard, water line freeze) and resets. |
| `satcom.py` | `/api/satcom` | Satellite link profile selection, channel metrics, store-and-forward spool, resync triggers. |
| `database.py` | `/api/database` | Database connection status, historical crisis episodes, equipment lifecycle, audit trails. |
| `copilot.py` | `/api/copilot` | Natural language operational copilot chat, suggested queries, conversation history. |
| `sync.py` | `/api/sync` | Station state synchronization and offline/online reconciliation. |
| `alerts.py` | `/api/alerts` | Station alert querying and operator acknowledgment. |
| `alerts_sovereign.py` | `/api/alerts/sovereign`| Sovereign agency CAP alerts (IMD, INCOIS, Disaster Management) with HMAC validation. |
| `memory.py` | `/api/memory` | Case-based reasoning (CBR) episode store, semantic tag search, retrieval tracking. |
| `environmental.py` | `/api/environmental` | AMPS polar weather forecasts, wind chill calculations, NOAA SWPC space weather. |
| `ws.py` | `/ws/telemetry` | Multiplexed WebSocket streaming with station scoping and client queue bounds. |

---

## State Lifecycle & 1 Hz Autonomy Loop

At server launch via the FastAPI lifespan context manager (`backend/server/app.py`):
1. **Calibration**: Master twin state is initialized with baseline physics calibration values.
2. **Database Initialization**: The `DatabaseManager` probes local MongoDB and cloud Atlas; if offline, it automatically engages the embedded atomic store.
3. **Continuous Autonomy Loop (1 Hz)**: A background asyncio task executes once per second:
   - Advances station physical clock and solves differential decay equations.
   - Computes real-time KPIs (electrical balance, indoor temperature, water reserve).
   - Scans 505 sensors for threshold violations and generates alerts.
   - Evaluates active cognitive agent hypotheses and safety interlock timers.
   - Dispatches telemetry broadcasts to active WebSocket subscribers.
4. **Graceful Shutdown**: On process termination, the loop safely drains pending queues, flushes the persistence buffer to disk, and cleanly disconnects active client sessions.
