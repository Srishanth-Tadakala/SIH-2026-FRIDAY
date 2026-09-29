"""FastAPI Application Factory for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides RESTful endpoints for dual-station digital twin monitoring, telemetry streaming,
cognitive agent inspection, crisis scenario injection, and tiered command execution.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import secrets
import time
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .routes.actions import router as actions_router
from .routes.agents import router as agents_router
from .routes.alerts import router as alerts_router
from .routes.auth import router as auth_router
from .routes.copilot import router as copilot_router
from .routes.database import router as database_router
from .routes.deliberations import router as deliberations_router
from .routes.environmental import router as environmental_router
from .routes.health import router as health_router
from .routes.memory import router as memory_router
from .routes.satcom import router as satcom_router
from .routes.scenarios import router as scenarios_router
from .routes.stations import router as stations_router
from .routes.sync import router as sync_router
from .routes.telemetry import router as telemetry_router
from .routes.telemetry_ingest import router as telemetry_ingest_router
from .routes.ws import router as ws_router
from .state import get_server_state

logger = logging.getLogger("friday.server")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager initializing digital twin state and continuous autonomy loop."""
    state = get_server_state(seed=42)
    # Perform initial calibration step
    state.step(dt_seconds=0.0)
    # Initialize 2-step distributed database subsystem and satcom sync worker
    await state.initialize_database()
    # Start continuous autonomous station governor loop (1 Hz)
    loop_task = asyncio.create_task(state.run_continuous_loop())
    yield
    # Graceful shutdown
    state.is_continuous_loop_running = False
    state.db_sync_worker.stop()
    loop_task.cancel()
    try:
        await loop_task
    except (asyncio.CancelledError, Exception):
        pass


def create_app() -> FastAPI:
    """Create and configure the master F.R.I.D.A.Y. FastAPI application."""
    app = FastAPI(
        title="F.R.I.D.A.Y. Antarctic Digital Twin Platform",
        description=(
            "Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations "
            "(Bharati Station & Maitri Station). Developed for Smart India Hackathon 2026 (SIH26060)."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    settings = get_settings()

    # Enable CORS for validated local and remote frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # Register API Routers
    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(stations_router)
    app.include_router(telemetry_router)
    app.include_router(telemetry_ingest_router)
    app.include_router(satcom_router)
    app.include_router(ws_router)
    app.include_router(agents_router)
    app.include_router(deliberations_router)
    app.include_router(actions_router)
    app.include_router(scenarios_router)
    app.include_router(database_router)
    app.include_router(copilot_router)
    app.include_router(sync_router)
    app.include_router(alerts_router)
    app.include_router(memory_router)
    app.include_router(environmental_router)

    # Luminous Scandi-Tech React Frontend Mount
    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    
    if os.path.exists(frontend_dist) and os.path.exists(os.path.join(frontend_dist, "index.html")):
        assets_dir = os.path.join(frontend_dist, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse, tags=["Homepage UI"])
    @app.get("/ui", response_class=HTMLResponse, tags=["Homepage UI"])
    def serve_homepage_ui() -> Any:
        """Serve the modern Luminous Scandi-Tech React Homepage."""
        react_index = os.path.join(frontend_dist, "index.html")
        if os.path.exists(react_index):
            return FileResponse(react_index)
        legacy_index = os.path.join(static_dir, "index.html")
        if os.path.exists(legacy_index):
            return FileResponse(legacy_index)
        return HTMLResponse("<h1>F.R.I.D.A.Y. Homepage UI</h1><p>index.html not found</p>")

    @app.get("/legacy-ui", response_class=HTMLResponse, tags=["Testing Cockpit"])
    def serve_legacy_ui() -> Any:
        """Serve the standalone tactical testing cockpit."""
        legacy_index = os.path.join(static_dir, "index.html")
        if os.path.exists(legacy_index):
            return FileResponse(legacy_index)
        return HTMLResponse("<h1>Cockpit UI not found</h1>")

    @app.get("/api/health", tags=["System"])
    def health_check() -> dict[str, Any]:
        """System health and operational readiness probe."""
        state = get_server_state()
        uptime_seconds = round(time.time() - state.server_start_time, 2)
        active_engine = state.get_engine()
        return {
            "status": "ONLINE",
            "system": "F.R.I.D.A.Y. Antarctic Digital Twin & Cognitive Operations Platform",
            "version": "1.0.0",
            "uptime_seconds": uptime_seconds,
            "managed_stations": list(state.stations.keys()),
            "active_station": state.active_station_id,
            "station_clock_iso": active_engine.clock.isoformat(),
            "sensor_count": active_engine.sensor_count,
            "cognitive_agents_count": 10,
            "interlocks_active": True,
            "satcom_sync_active": True,
            "websocket_streaming_active": True,
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global fallback exception handler ensuring no internal stack or exception details leak."""
        req_id = secrets.token_hex(6)
        logger.error(f"[REQ-{req_id}] Internal server exception at {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred while processing the operational command.",
                    "request_id": req_id,
                }
            },
        )

    return app


# Default app instance for uvicorn runtime: uvicorn backend.server.app:app
app = create_app()
