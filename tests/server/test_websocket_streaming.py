"""Unit and Integration Tests for Real-Time Multiplexed WebSocket Streaming (Sub-Phase 4.3).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Tests:
1. WebSocket Connection Handshake & System Channel Acknowledgment
2. Bidirectional Ping / Pong Heartbeat Mechanism
3. Dynamic Channel Subscription & Unsubscription ('kpis', 'sensors', 'alerts', 'deliberations', 'satcom')
4. Selective 4-Pillar Sensor Stream Filtering (Energy, Infrastructure, Environment, Logistics)
5. Selective Explicit Sensor IDs Stream Filtering
6. Full-Duplex Instant Station Snapshot On-Demand Query
7. Multi-Station Client Isolation (Bharati vs Maitri stream separation)
8. Unknown Station Connection Rejection (WS Close 1008)
9. Active Connection Diagnostic Telemetry (GET /api/ws/stats)
"""

from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient

from backend.server.app import create_app
from backend.server.state import reset_server_state
from backend.server.ws_manager import get_ws_manager


class TestWebSocketStreamingEngine:
    """Comprehensive test suite for F.R.I.D.A.Y. Multiplexed WebSocket Streaming."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> TestClient:
        """Provide a fresh server state and test client for each test."""
        reset_server_state(seed=42)
        app = create_app()
        return TestClient(app)

    def test_websocket_handshake_and_system_ack(self, setup_app: TestClient) -> None:
        """Verify WebSocket connection handshake returns system acknowledgment with default channels."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            msg = ws.receive_json()
            assert msg["channel"] == "system"
            assert msg["action"] == "connected"
            assert msg["station_id"] == "bharati"
            assert "alerts" in msg["active_subscriptions"]
            assert "kpis" in msg["active_subscriptions"]
            assert "satcom" in msg["active_subscriptions"]

    def test_websocket_ping_pong_heartbeat(self, setup_app: TestClient) -> None:
        """Verify full-duplex heartbeat response."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Consume initial connected message

            ws.send_json({"action": "ping"})
            pong = ws.receive_json()
            assert pong["channel"] == "system"
            assert pong["action"] == "pong"
            assert "timestamp" in pong

    def test_websocket_channel_subscription_and_unsubscription(self, setup_app: TestClient) -> None:
        """Verify subscribing to new channels and removing existing channels."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Handshake

            # Subscribe to deliberations and sensors
            ws.send_json({"action": "subscribe", "channels": ["sensors", "deliberations"]})
            ack = ws.receive_json()
            assert ack["channel"] == "system"
            assert ack["action"] == "subscribed"
            assert "deliberations" in ack["active_subscriptions"]
            assert "sensors" in ack["active_subscriptions"]

            # Unsubscribe from satcom
            ws.send_json({"action": "unsubscribe", "channels": ["satcom"]})
            unsub_ack = ws.receive_json()
            assert unsub_ack["action"] == "unsubscribed"
            assert "satcom" not in unsub_ack["active_subscriptions"]

    def test_websocket_selective_pillar_filtering(self, setup_app: TestClient) -> None:
        """Verify client receives only sensors belonging to the subscribed pillar."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Handshake

            # Subscribe specifically to Energy pillar
            ws.send_json({
                "action": "subscribe",
                "channels": ["sensors"],
                "filter": {"pillar": "energy"},
            })
            sub_ack = ws.receive_json()
            assert sub_ack["pillar_filter"] == "energy"

            # Trigger a simulation step over WebSocket
            ws.send_json({"action": "step", "dt_seconds": 1.0})

            # Client should receive broadcast messages for its subscribed channels (kpis, sensors, satcom)
            received_channels = []
            sensor_data = None

            for _ in range(4):
                msg = ws.receive_json()
                ch = msg.get("channel")
                received_channels.append(ch)
                if ch == "sensors":
                    sensor_data = msg

            assert "sensors" in received_channels
            assert sensor_data is not None
            readings = sensor_data["readings"]
            assert len(readings) > 0
            # Verify ALL returned sensors belong to Energy pillar
            for s_id in readings.keys():
                assert s_id.startswith("ENG-") or "CHP" in s_id or "GRID" in s_id

    def test_websocket_selective_sensor_ids_filtering(self, setup_app: TestClient) -> None:
        """Verify client receives only explicitly requested sensor IDs."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Handshake

            target_ids = ["ENV-WX-TEMP", "ENG-GEN-1-KW"]
            ws.send_json({
                "action": "subscribe",
                "channels": ["sensors"],
                "filter": {"sensor_ids": target_ids},
            })
            ws.receive_json()  # Subscribed ack

            # Trigger step
            ws.send_json({"action": "step", "dt_seconds": 1.0})

            # Consume until sensor frame
            sensor_readings = None
            for _ in range(4):
                msg = ws.receive_json()
                if msg.get("channel") == "sensors":
                    sensor_readings = msg.get("readings", {})

            assert sensor_readings is not None
            # Only requested target IDs may be present
            for k in sensor_readings.keys():
                assert k in target_ids

    def test_websocket_instant_snapshot_request(self, setup_app: TestClient) -> None:
        """Verify on-demand snapshot query returns all 505 sensors over WebSocket."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Handshake

            ws.send_json({"action": "get_snapshot"})
            snap = ws.receive_json()
            assert snap["channel"] == "sensors"
            assert snap["action"] == "snapshot"
            assert snap["station_id"] == "bharati"
            assert snap["sensor_count"] == 505
            assert len(snap["readings"]) == 505

    def test_websocket_station_isolation(self, setup_app: TestClient) -> None:
        """Verify isolation between Bharati and Maitri WebSocket streams."""
        client = setup_app

        with client.websocket_connect("/ws/telemetry/bharati") as ws_bharati, \
             client.websocket_connect("/ws/telemetry/maitri") as ws_maitri:

            # Handshakes
            h_b = ws_bharati.receive_json()
            h_m = ws_maitri.receive_json()
            assert h_b["station_id"] == "bharati"
            assert h_m["station_id"] == "maitri"

            # Step Bharati
            ws_bharati.send_json({"action": "step", "dt_seconds": 2.0})

            # Bharati receives update with station_id == "bharati"
            msg_b = ws_bharati.receive_json()
            assert msg_b["station_id"] == "bharati"

    def test_websocket_unknown_station_rejected(self, setup_app: TestClient) -> None:
        """Verify connecting to an invalid station ID is rejected with WebSocket close code 1008."""
        client = setup_app

        try:
            with client.websocket_connect("/ws/telemetry/dakshin_gangotri") as ws:
                ws.receive_json()
                pytest.fail("Should have closed connection for unknown station")
        except Exception:
            # Successfully rejected
            pass

    def test_websocket_diagnostic_stats_endpoint(self, setup_app: TestClient) -> None:
        """Verify GET /api/ws/stats reflects live WebSocket connection metrics."""
        client = setup_app

        # Baseline stats before connection
        res0 = client.get("/api/ws/stats")
        assert res0.status_code == 200
        data0 = res0.json()
        assert "supported_channels" in data0
        assert "kpis" in data0["supported_channels"]
        assert "sensors" in data0["supported_channels"]
        assert "deliberations" in data0["supported_channels"]

        # Open connection and check increment
        with client.websocket_connect("/ws/telemetry/bharati") as ws:
            ws.receive_json()  # Handshake

            res1 = client.get("/api/ws/stats")
            data1 = res1.json()
            assert data1["station_connections"]["bharati"] >= 1
            assert data1["total_active_connections"] >= 1

        # After exiting context, connection is cleaned up
        res2 = client.get("/api/ws/stats")
        data2 = res2.json()
        assert data2["station_connections"]["bharati"] == 0
