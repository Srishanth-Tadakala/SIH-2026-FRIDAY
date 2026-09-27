"""WebSocket Telemetry Streaming Route for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Provides:
- WebSocket endpoint: `/ws/telemetry/{station_id}`
- Diagnostic REST endpoint: `GET /api/ws/stats`
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..auth import decode_access_token
from ..config import get_settings
from ..state import get_server_state
from ..ws_manager import get_ws_manager

logger = logging.getLogger("friday.server.routes.ws")

router = APIRouter(tags=["WebSocket Streaming"])


@router.websocket("/ws/telemetry/{station_id}")
async def telemetry_websocket_endpoint(
    websocket: WebSocket,
    station_id: str,
) -> None:
    """Persistent bidirectional WebSocket connection for multiplexed telemetry streaming."""
    state = get_server_state()
    settings = get_settings()
    sid = station_id.lower()

    if sid not in state.stations:
        await websocket.close(code=1008, reason=f"Unknown station ID: {sid}")
        return

    # 1. Security & Handshake Authentication
    token = websocket.query_params.get("token")
    if token:
        try:
            payload = decode_access_token(token)
            user_station = payload.get("station_id")
            if user_station and user_station.lower() != sid:
                await websocket.close(code=1008, reason=f"Unauthorized for station: {sid}")
                return
        except Exception:
            await websocket.close(code=1008, reason="Invalid or expired authentication token")
            return
    elif settings.ENVIRONMENT == "production":
        await websocket.close(code=1008, reason="Production mode requires Bearer authentication token")
        return

    # 2. Connection Limit Defense
    manager = get_ws_manager()
    total_clients = sum(len(c) for c in manager._clients.values())
    if total_clients >= settings.WS_MAX_CONNECTIONS:
        await websocket.close(code=1013, reason="Maximum concurrent WebSocket connections reached")
        return

    session = await manager.connect(websocket, sid)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
            except json.JSONDecodeError:
                await session.send_json_safe({
                    "channel": "system",
                    "action": "error",
                    "message": "Malformed JSON payload.",
                })
                continue

            await manager.handle_client_message(session, msg, state)

    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        logger.debug(f"WebSocket streaming connection cancelled ({session.client_id}).")
        raise
    except Exception as e:
        logger.debug(f"WebSocket connection terminated ({session.client_id}): {e}")
    finally:
        await manager.disconnect(session)


@router.get("/api/ws/stats", tags=["System"])
def get_websocket_connection_stats() -> dict[str, Any]:
    """Retrieve active WebSocket streaming connection counts and supported multiplex channels."""
    manager = get_ws_manager()
    return manager.get_stats()
