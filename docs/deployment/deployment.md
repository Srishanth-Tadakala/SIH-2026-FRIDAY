# Deployment & Operations Guide

## Deployment Topologies

F.R.I.D.A.Y. can be deployed across three operational topologies:
1. **Edge Deployment**: On-premise server located at Bharati or Maitri station connected directly to local SCADA networks.
2. **Cloud HQ Deployment**: Hosted on MongoDB Atlas and cloud Kubernetes / VM at NCPOR Goa headquarters.
3. **Dual-Node Mesh Topology**: Simultaneous edge and cloud deployment synchronized over the satcom bridge.

---

## 1. Containerized Deployment with Docker & Compose

The repository includes a hardened multi-stage `Dockerfile` and `docker-compose.yml`.

### Multi-Stage Dockerfile Architecture
```text
Stage 1: node:22-alpine       ---> Compiles React 19 / TypeScript into /app/frontend/dist
Stage 2: python:3.12-slim     ---> Installs requirements.txt, copies backend source,
                                   creates unprivileged 'friday' user, exposes port 8000
```

### Deploying Dual-Node Topology (Edge + Mainland HQ)
1. Initialize environment:
   ```bash
   cp .env.example .env
   ```
2. Build and launch services in background:
   ```bash
   docker compose up -d --build
   ```
3. Verify running containers:
   ```bash
   docker compose ps
   ```
   *Expected services:*
   - `friday-edge-bharati`: Antarctic Station Edge server (Port 8000).
   - `friday-mongo-edge`: Local MongoDB instance with healthcheck.
   - `friday-cloud-hq`: Mainland Command HQ server (Port 8001).
   - `friday-mongo-cloud`: Mainland HQ MongoDB instance.

4. Inspect logs:
   ```bash
   docker compose logs -f friday-edge-bharati
   ```

5. Check health:
   ```bash
   curl http://localhost:8000/health/liveness
   curl http://localhost:8000/health/readiness
   ```

---

## 2. Bare-Metal Linux / Edge Server Deployment

For dedicated industrial IPCs (Advantech, Moxa, Siemens IPC) at Antarctic stations:

### Systemd Service Configuration
Create `/etc/systemd/system/friday.service`:
```ini
[Unit]
Description=F.R.I.D.A.Y. Antarctic Digital Twin & Cognitive Operations Platform
After=network.target

[Service]
Type=simple
User=friday
WorkingDirectory=/opt/friday
EnvironmentFile=/opt/friday/.env
ExecStart=/opt/friday/.venv/bin/python run_server.py
Restart=always
RestartSec=5s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now friday.service
sudo systemctl status friday.service
```

---

## 3. Reverse Proxy & SSL/TLS Configuration (NGINX)

When deploying on public networks or Mainland HQ:

```nginx
server {
    listen 443 ssl http2;
    server_name antarctic-twin.ncpor.res.in;

    ssl_certificate /etc/letsencrypt/live/antarctic-twin.ncpor.res.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/antarctic-twin.ncpor.res.in/privkey.pem;

    # REST API & Static Frontend
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Telemetry Multiplexing
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

---

## 4. Disaster Recovery & Edge Storage Persistence

- In case of catastrophic power outages, local persistence data resides in `data/edge_storage/friday_embedded_edge.json`.
- Back up this directory regularly:
  ```bash
  tar -czvf friday_edge_backup_$(date +%F).tar.gz data/edge_storage/
  ```
