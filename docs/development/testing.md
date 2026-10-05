# Testing & Automated Verification Guide

F.R.I.D.A.Y. enforces strict verification standards to guarantee that life-support systems and safety interlocks never regress.

---

## 1. Test Architecture Overview

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        F.R.I.D.A.Y. TEST SUITE                         │
├──────────────────────────────────┬─────────────────────────────────────┤
│ Backend Tests (pytest)           │ 397 Tests Across 7 Test Domains     │
│ Frontend Tests (Vitest)          │ 16 Unit & Integration Tests         │
│ API Verification Benchmark       │ 60 of 60 Endpoints Verified (100%)  │
│ CI/CD Workflow (GitHub Actions)  │ Multi-Python (3.11, 3.12) & Node 22 │
└──────────────────────────────────┴─────────────────────────────────────┘
```

---

## 2. Running Backend Tests

The backend test suite is executed using `pytest`.

### Run Complete Test Suite
```bash
python -m pytest
```
*Expected: 397 passed in ~120s.*

### Run Tests by Subsystem Domain
```bash
# Multi-Agent Swarm Intelligence & Deliberation Tests (72 tests)
python -m pytest tests/agents/

# Physics Digital Twin Core & Differential Equations (14 tests)
python -m pytest tests/core/

# Satcom Protocol, Delta Compression & DTN Bundles (13 tests)
python -m pytest tests/satcom/

# 505 Sensor Points across Energy, HVAC, Environment, Logistics (146 tests)
python -m pytest tests/sensors/

# Industrial Fieldbus Bridges (Modbus, OPC UA, BACnet, MQTT) (17 tests)
python -m pytest tests/sensors/test_industrial_bridges.py

# FastAPI Endpoints, Security, WebSockets & Safety Interlocks (130+ tests)
python -m pytest tests/server/

# Database Fallback & CBR Memory (9 tests)
python -m pytest tests/database/
```

### Run Failure Injection Tests
Simulates sudden generator cutoffs, communication blackouts, corrupted tokens, and invalid PIN entries:
```bash
python -m pytest tests/server/test_failure_injection.py tests/server/test_security_and_auth.py
```

---

## 3. Running Frontend Tests

Frontend unit and integration tests are powered by Vitest and JSDOM:

```bash
cd frontend

# Run all tests once
npm test

# Run tests in interactive watch mode
npm run test:watch
```

---

## 4. End-to-End API Benchmarking

The automated benchmarking tool `tools/test_all_endpoints.py` tests all 60 REST endpoints against response schemas, latency thresholds ($<500\text{ms}$), and exports an updated Postman collection:

```bash
python tools/test_all_endpoints.py
```
*Generates:*
- `postman_collection.json` (Postman Collection v2.1.0)
- `postman_environment.json` (Local environment variables)

---

## 5. Continuous Integration (GitHub Actions)

Every pull request and push to `main` triggers `.github/workflows/ci.yml`:
1. **Backend Matrix Job**: Tests Python 3.11 and 3.12 with Ruff lint checks and Pytest suite.
2. **Frontend Job**: Tests Node.js 22 with `oxlint`, Vitest, and TypeScript production build.
3. **Container Job**: Validates the multi-stage `Dockerfile` build.
