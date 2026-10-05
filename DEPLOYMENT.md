# F.R.I.D.A.Y. Deployment & Operations Guide

**Platform:** F.R.I.D.A.Y. Polar Digital Twin Platform (SIH 2026 - SIH26060)  
**Target Environments:** Antarctic Station Edge (Bharati / Maitri) & NCPOR Mainland Cloud (Goa)

---

## 1. System Requirements

### 1.1 Polar Station Edge Node (Minimal Footprint)
- **OS**: Linux (Ubuntu 22.04 LTS / Debian 12 / Rocky Linux 9) or Windows Server / Windows 11
- **CPU**: 4 Cores (x86_64 or ARM64)
- **RAM**: 8 GB minimum (16 GB recommended)
- **Storage**: 20 GB SSD with atomic write support
- **Connectivity**: Resilient to 0 kbps complete satellite blackouts (embedded atomic persistence store activates automatically)

### 1.2 Mainland Mission Control Node (NCPOR Goa Cloud)
- **OS**: Linux (Ubuntu 22.04 LTS or Kubernetes cluster)
- **CPU**: 8+ Cores
- **RAM**: 16–32 GB
- **Database**: MongoDB Atlas or self-hosted Replica Set (v6.0+)
- **Reverse Proxy**: NGINX / Caddy / Traefik with TLS 1.3 termination

---

## 2. Containerized Deployment (Docker & Compose)

F.R.I.D.A.Y. includes a production-grade multi-stage container build and Docker Compose configuration.

### 2.1 Multi-Stage Dockerfile Architecture
The Docker build utilizes a 2-stage pipeline:
1. **Stage 1 (Frontend Builder)**: Node.js 20 Alpine compiles React 19 + TypeScript + Vite assets into `/dist`.
2. **Stage 2 (Production Runtime)**: Python 3.12 Slim runs FastAPI + Uvicorn serving both backend APIs and static frontend artifacts under a non-root security context (`friday:friday`).

### 2.2 Quickstart with Docker Compose

1. Clone repository and initialize environment:
   ```bash
   cp .env.example .env
   # Edit .env with your production credentials
   ```

2. Start the full stack (F.R.I.D.A.Y. Twin + Edge MongoDB):
   ```bash
   docker compose up -d --build
   ```

3. View live logs:
   ```bash
   docker compose logs -f friday-edge-bharati
   ```

4. Verify health endpoints:
   ```bash
   curl http://localhost:8000/health/liveness
   curl http://localhost:8000/health/readiness
   ```

---

## 3. Native Python + Vite Deployment

### 3.1 Backend Setup
```bash
# 1. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env   # On Windows
cp .env.example .env     # On Linux

# 4. Start the backend server
python run_server.py
```
Backend runs at `http://127.0.0.1:8000`.

### 3.2 Frontend Setup
```bash
cd frontend
npm install
npm run build   # Production bundle in frontend/dist
npm run dev     # Local development server at http://localhost:5173
```

---

## 4. Kubernetes & Container Health Probes

F.R.I.D.A.Y. exposes dedicated Kubernetes-compatible probes in `backend/server/routes/health.py`:

| Probe Path | Probe Type | Purpose | Healthy Response |
| :--- | :--- | :--- | :--- |
| `/health/liveness` | Liveness | Checks process health and process uptime. | `{"status": "alive", "uptime_seconds": 124.5}` (HTTP 200) |
| `/health/readiness` | Readiness | Checks digital twin state, message bus, persistence, and satcom link readiness. | `{"status": "ready", "components": {...}}` (HTTP 200) |
| `/api/health/metrics` | Monitoring | Exposes system metrics (CPU, RAM, active WS connections, pending actions). | `{"active_ws_connections": 3, "pending_supervised_actions": 0, ...}` |

### Kubernetes Pod Spec Example:
```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15
```

---

## 5. Offline Edge & Satcom Resilience Modes

When deploying to Bharati or Maitri Station:
- **Zero-Internet Fallback**: If `LOCAL_MONGO_URI` and `MONGODB_ATLAS_URI` are unreachable, the embedded atomic edge store (`data/edge_storage/*.json`) handles all state transitions, alarms, and CBR cases without loss.
- **LLM Cognitive Offline Fallback**: If the Groq LPU endpoint is unreachable (due to polar satcom blackout), the local neural synthesis engine generates rule-grounded, zero-latency mitigation strategies (<1.4ms).
- **Dead-Letter Queue (DLQ)**: Failed remote synchronization jobs are automatically shunted to the dead-letter queue after 5 exponential retry attempts, preventing head-of-line blocking.
