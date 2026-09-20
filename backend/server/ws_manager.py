"""Real-Time Multiplexed WebSocket Streaming Manager for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

ARCHITECTURE:
Enables low-latency, full-duplex multiplexed streaming over a single WebSocket connection:
1. Channel Multiplexing:
   - 'kpis': High-level vital signs (Power, Thermal, Fuel/Water Autonomy, Risk Score) at 1 Hz.
   - 'sensors': Granular 505-sensor telemetry deltas with optional pillar/sensor filtering.
   - 'alerts': Immediate push of operational and life-safety alarms.
   - 'deliberations': Real-time streaming of multi-agent cognitive events and briefing cards.
   - 'satcom': Satellite link status, profile, bandwidth savings, and mirror sync status.
2. Selective Subscription:
   - Clients filter sensor streams by pillar ('energy', 'infrastructure', 'environment', 'logistics')
     or specific sensor IDs to eliminate client-side over-fetching.
3. Full-Duplex Control:
   - Clients can trigger simulation steps, ping heartbeats, request instant snapshots, and alter subscriptions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import time
from typing import Any
import uuid

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("friday.server.ws")


class WebSocketChannel(str, Enum):
    """Multiplexed streaming channels over a single WebSocket connection."""
    KPIS = "kpis"                   # High-level vital signs (1 Hz)
    SENSORS = "sensors"             # 505-sensor granular telemetry deltas
    ALERTS = "alerts"               # Immediate operational and life-safety alarms
    DELIBERATIONS = "deliberations" # Multi-agent blackboard deliberations & briefing cards
    SATCOM = "satcom"               # Satcom channel profile, bandwidth, and mirror sync status
    SYSTEM = "system"               # Handshake, subscription acks, heartbeats, ping/pong


@dataclass
class ClientSubscription:
    """Subscription preferences and filtering criteria for an individual WebSocket client."""
    channels: set[str] = field(default_factory=lambda: {"kpis", "alerts", "satcom"})
    pillar_filter: str | None = None          # 'energy', 'infrastructure', 'environment', 'logistics'
    sensor_ids_filter: set[str] | None = None # Explicit sensor IDs
    rate_hz: float = 1.0                      # Telemetry update frequency limit
    last_broadcast_time: float = 0.0


@dataclass
class WebSocketClientSession:
    """Represents an active WebSocket client session."""
    client_id: str
    station_id: str
    websocket: WebSocket
    subscription: ClientSubscription
    connected_at: float = field(default_factory=time.time)
    messages_sent: int = 0
    messages_received: int = 0

    async def send_json_safe(self, data: dict[str, Any]) -> bool:
        """Send JSON payload safely across the WebSocket."""
        try:
            await self.websocket.send_json(data)
            self.messages_sent += 1
            return True
        except Exception as e:
            logger.debug(f"Failed sending WebSocket message to {self.client_id}: {e}")
            return False


class TelemetryWebSocketManager:
    """Manages multi-station multiplexed WebSocket connections, subscriptions, and broadcasts."""

    def __init__(self) -> None:
        # Station ID -> {Client ID: Session}
        self._clients: dict[str, dict[str, WebSocketClientSession]] = {
            "bharati": {},
            "maitri": {},
        }
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        station_id: str,
        client_id: str | None = None,
    ) -> WebSocketClientSession:
        """Accept incoming WebSocket connection and register client session."""
        await websocket.accept()
        sid = station_id.lower()
        cid = client_id or f"client-{uuid.uuid4().hex[:8]}"

        session = WebSocketClientSession(
            client_id=cid,
            station_id=sid,
            websocket=websocket,
            subscription=ClientSubscription(),
        )

        async with self._lock:
            if sid not in self._clients:
                self._clients[sid] = {}
            self._clients[sid][cid] = session

        # Send initial connection handshake acknowledgment
        await session.send_json_safe({
            "channel": WebSocketChannel.SYSTEM.value,
            "action": "connected",
            "client_id": cid,
            "station_id": sid,
            "active_subscriptions": sorted(list(session.subscription.channels)),
            "timestamp": time.time(),
        })

        logger.info(f"WebSocket client {cid} connected to station {sid}.")
        return session

    async def disconnect(self, session: WebSocketClientSession) -> None:
        """Unregister a disconnected WebSocket client."""
        async with self._lock:
            sid = session.station_id
            cid = session.client_id
            if sid in self._clients and cid in self._clients[sid]:
                del self._clients[sid][cid]
                logger.info(f"WebSocket client {cid} disconnected from station {sid}.")

    @staticmethod
    def _serialize_val(reading: Any) -> Any:
        """Extract JSON-serializable scalar value from SensorReading or dict."""
        if hasattr(reading, "value"):
            v = reading.value
        elif isinstance(reading, dict) and "value" in reading:
            v = reading["value"]
        else:
            v = reading

        if isinstance(v, float):
            return round(v, 3)
        return v

    async def handle_client_message(
        self,
        session: WebSocketClientSession,
        message: dict[str, Any],
        server_state: Any,
    ) -> None:
        """Process control messages from client (subscribe, ping, step, snapshot)."""
        session.messages_received += 1
        action = message.get("action", "").lower()

        # 1. PING -> PONG
        if action == "ping":
            await session.send_json_safe({
                "channel": WebSocketChannel.SYSTEM.value,
                "action": "pong",
                "client_id": session.client_id,
                "timestamp": time.time(),
            })
            return

        # 2. SUBSCRIBE
        if action == "subscribe":
            channels = message.get("channels", [])
            if isinstance(channels, list):
                session.subscription.channels.update(channels)
            elif isinstance(message.get("channel"), str):
                session.subscription.channels.add(message["channel"])

            # Filters
            flt = message.get("filter", {})
            if "pillar" in flt:
                session.subscription.pillar_filter = flt["pillar"].lower() if flt["pillar"] else None
            if "sensor_ids" in flt and isinstance(flt["sensor_ids"], list):
                session.subscription.sensor_ids_filter = set(flt["sensor_ids"])

            if "rate_hz" in message and isinstance(message["rate_hz"], (int, float)):
                session.subscription.rate_hz = max(0.1, min(10.0, float(message["rate_hz"])))

            await session.send_json_safe({
                "channel": WebSocketChannel.SYSTEM.value,
                "action": "subscribed",
                "active_subscriptions": sorted(list(session.subscription.channels)),
                "pillar_filter": session.subscription.pillar_filter,
                "sensor_ids_filter": list(session.subscription.sensor_ids_filter) if session.subscription.sensor_ids_filter else None,
                "rate_hz": session.subscription.rate_hz,
            })
            return

        # 3. UNSUBSCRIBE
        if action == "unsubscribe":
            channels = message.get("channels", [])
            if isinstance(channels, list):
                session.subscription.channels.difference_update(channels)
            elif isinstance(message.get("channel"), str):
                session.subscription.channels.discard(message["channel"])

            await session.send_json_safe({
                "channel": WebSocketChannel.SYSTEM.value,
                "action": "unsubscribed",
                "active_subscriptions": sorted(list(session.subscription.channels)),
            })
            return

        # 4. STEP SIMULATION CLOCK
        if action == "step":
            dt = float(message.get("dt_seconds", 1.0))
            snap = server_state.step(session.station_id, dt_seconds=dt)
            await session.send_json_safe({
                "channel": WebSocketChannel.SYSTEM.value,
                "action": "stepped",
                "station_id": session.station_id,
                "sim_time_seconds": snap.sim_time_seconds,
                "dt_seconds": dt,
            })
            return

        # 5. GET INSTANT SNAPSHOT
        if action == "get_snapshot":
            engine = server_state.get_engine(session.station_id)
            snap = engine.get_snapshot()
            clean_readings = {k: self._serialize_val(v) for k, v in snap.readings.items()}
            await session.send_json_safe({
                "channel": WebSocketChannel.SENSORS.value,
                "action": "snapshot",
                "station_id": session.station_id,
                "sim_time_seconds": snap.sim_time_seconds,
                "timestamp_iso": snap.timestamp_iso,
                "sensor_count": snap.sensor_count,
                "readings": clean_readings,
            })
            return

        # Unknown action
        await session.send_json_safe({
            "channel": WebSocketChannel.SYSTEM.value,
            "action": "error",
            "message": f"Unknown action: '{action}'",
        })

    def _filter_readings_for_client(
        self,
        session: WebSocketClientSession,
        readings: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply pillar and sensor ID filters to outgoing telemetry."""
        sub = session.subscription
        if not sub.pillar_filter and not sub.sensor_ids_filter:
            return {k: self._serialize_val(v) for k, v in readings.items()}

        filtered: dict[str, Any] = {}
        for s_id, val in readings.items():
            scalar = self._serialize_val(val)
            # Check sensor ID filter
            if sub.sensor_ids_filter and s_id not in sub.sensor_ids_filter:
                continue
            # Check pillar filter
            if sub.pillar_filter:
                p = sub.pillar_filter.upper()
                if p == "ENERGY" and not (s_id.startswith("ENG-") or "CHP" in s_id or "GRID" in s_id):
                    continue
                if p == "INFRASTRUCTURE" and not (s_id.startswith("INFRA-") or "HVAC" in s_id or "WATER" in s_id):
                    continue
                if p == "ENVIRONMENT" and not (s_id.startswith("ENV-") or "WX" in s_id or "MET" in s_id):
                    continue
                if p == "LOGISTICS" and not (s_id.startswith("LOG-") or "REEFER" in s_id or "VEH" in s_id):
                    continue
            filtered[s_id] = scalar

        return filtered

    async def broadcast_station_step(
        self,
        station_id: str,
        snapshot: Any,
        server_state: Any,
    ) -> None:
        """Broadcast multiplexed telemetry to all connected clients on a station."""
        sid = station_id.lower()
        if sid not in self._clients:
            return

        sessions = list(self._clients[sid].values())
        if not sessions:
            return

        # Extract delta frame from satcom encoder
        satcom_summary = server_state.get_satcom_summary(sid) if hasattr(server_state, "get_satcom_summary") else {}
        kpis = snapshot.kpis if hasattr(snapshot, "kpis") else {}
        alerts = snapshot.alerts if hasattr(snapshot, "alerts") else []
        readings = snapshot.readings if hasattr(snapshot, "readings") else {}
        sim_time = snapshot.sim_time_seconds if hasattr(snapshot, "sim_time_seconds") else 0.0

        for session in sessions:
            sub = session.subscription

            # 1. Broadcast KPIs Channel
            if WebSocketChannel.KPIS.value in sub.channels:
                await session.send_json_safe({
                    "channel": WebSocketChannel.KPIS.value,
                    "station_id": sid,
                    "sim_time_seconds": sim_time,
                    "kpis": kpis,
                })

            # 2. Broadcast Sensors Channel
            if WebSocketChannel.SENSORS.value in sub.channels:
                filtered_readings = self._filter_readings_for_client(session, readings)
                await session.send_json_safe({
                    "channel": WebSocketChannel.SENSORS.value,
                    "station_id": sid,
                    "sim_time_seconds": sim_time,
                    "channel_count": len(filtered_readings),
                    "readings": filtered_readings,
                })

            # 3. Broadcast Alerts Channel
            if WebSocketChannel.ALERTS.value in sub.channels and alerts:
                await session.send_json_safe({
                    "channel": WebSocketChannel.ALERTS.value,
                    "station_id": sid,
                    "alert_count": len(alerts),
                    "alerts": alerts,
                })

            # 4. Broadcast Satcom Channel
            if WebSocketChannel.SATCOM.value in sub.channels and satcom_summary:
                await session.send_json_safe({
                    "channel": WebSocketChannel.SATCOM.value,
                    "station_id": sid,
                    "satcom": satcom_summary,
                })

    async def broadcast_deliberation_event(
        self,
        station_id: str,
        event_data: dict[str, Any],
    ) -> None:
        """Broadcast live cognitive deliberation event to clients subscribed to deliberations."""
        sid = station_id.lower()
        if sid not in self._clients:
            return

        for session in list(self._clients[sid].values()):
            if WebSocketChannel.DELIBERATIONS.value in session.subscription.channels:
                await session.send_json_safe({
                    "channel": WebSocketChannel.DELIBERATIONS.value,
                    "station_id": sid,
                    "timestamp": time.time(),
                    "event": event_data,
                })

    async def broadcast_alarm(
        self,
        station_id: str,
        alarm: dict[str, Any],
    ) -> None:
        """Broadcast high-priority alarm immediately to all subscribed clients."""
        sid = station_id.lower()
        if sid not in self._clients:
            return

        for session in list(self._clients[sid].values()):
            if WebSocketChannel.ALERTS.value in session.subscription.channels:
                await session.send_json_safe({
                    "channel": WebSocketChannel.ALERTS.value,
                    "station_id": sid,
                    "alarm": alarm,
                })

    def get_stats(self) -> dict[str, Any]:
        """Aggregate active WebSocket streaming connection telemetry."""
        total_clients = sum(len(c) for c in self._clients.values())
        station_breakdown = {sid: len(c) for sid, c in self._clients.items()}
        return {
            "total_active_connections": total_clients,
            "station_connections": station_breakdown,
            "supported_channels": [c.value for c in WebSocketChannel],
        }


# Global WebSocket Manager Singleton
_ws_manager_instance: TelemetryWebSocketManager | None = None


def get_ws_manager() -> TelemetryWebSocketManager:
    """Retrieve or create the global WebSocket manager singleton."""
    global _ws_manager_instance
    if _ws_manager_instance is None:
        _ws_manager_instance = TelemetryWebSocketManager()
    return _ws_manager_instance
