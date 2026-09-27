# ==============================================================================
# F.R.I.D.A.Y. Multi-Stage Production Container
# Antarctic Digital Twin Platform for Remote Management of Bharati & Maitri
# Part of Smart India Hackathon 2026 (SIH26060)
# ==============================================================================

# Stage 1: Build React/TypeScript Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Hardened Python Runtime
FROM python:3.12-slim AS runtime

LABEL maintainer="F.R.I.D.A.Y. Engineering Team <ncpor@moes.gov.in>"
LABEL description="Antarctic Digital Twin & Cognitive Operations Platform"

# Install curl for container health check probes
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ ./backend/
COPY assets/ ./assets/
COPY run_server.py ./

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create dedicated persistent directories and unprivileged runtime user
RUN mkdir -p /app/data/edge_storage && \
    useradd -u 10001 -m -s /bin/bash friday && \
    chown -R friday:friday /app

# Run as non-root user for security hardening
USER friday

# Expose FastAPI HTTP/WebSocket port
EXPOSE 8000

# Automated Docker Container Health Check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

# Launch production server
CMD ["python", "run_server.py"]
