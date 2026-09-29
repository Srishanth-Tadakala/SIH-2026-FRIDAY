"""MQTT v5 and Sparkplug B Edge Telemetry Bridge for F.R.I.D.A.Y.

Connects to station MQTT message brokers (Mosquitto/EMQX) to ingest real-time
metrics from low-power wireless LoRaWAN nodes, meteorological masts, and
edge IoT micro-controllers deployed across Larsemann Hills and Maitri.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("friday.sensors.mqtt")

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    mqtt = None
    PAHO_AVAILABLE = False
    logger.warning("paho-mqtt library is not installed. MQTT Bridge will run in disabled/stub mode.")


class MqttBridgeConfig(BaseModel):
    """Configuration for MQTT Broker connection."""

    host: str = Field(default="127.0.0.1", description="MQTT broker hostname or IP")
    port: int = Field(default=1883, ge=1, le=65535, description="MQTT broker TCP port")
    client_id: str = Field(default="friday-polar-twin-mqtt", description="MQTT client identifier")
    keepalive: int = Field(default=60, description="Keepalive interval in seconds")
    username: Optional[str] = Field(default=None, description="Optional authentication username")
    password: Optional[str] = Field(default=None, description="Optional authentication password")
    station_id: str = Field(default="bharati", description="Station identifier")
    topics: list[str] = Field(
        default_factory=lambda: [
            "antarctica/+/telemetry/#",
            "antarctica/+/sensors/#",
            "spBv1.0/Antarctica/+/+/#",
        ],
        description="MQTT topic patterns to subscribe to",
    )
    connect_timeout_seconds: float = Field(default=3.0, description="Connection timeout")
    enabled: bool = Field(default=True, description="Enable or disable bridge on startup")


class MqttTelemetryBridge:
    """Asynchronous MQTT Gateway for Edge Sensor Ingestion and Actuator Dispatch."""

    def __init__(
        self,
        config: Optional[MqttBridgeConfig] = None,
        engine: Optional[Any] = None,
    ) -> None:
        self.config = config or MqttBridgeConfig()
        self.engine = engine

        self.client: Optional[Any] = None
        self.is_running: bool = False
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.reconnect_count: int = 0

        # Diagnostics & Metrics
        self.total_messages_received: int = 0
        self.total_points_ingested: int = 0
        self.total_messages_published: int = 0
        self.last_message_timestamp: Optional[float] = None
        self.active_nodes: dict[str, dict[str, Any]] = {}  # Tracks Sparkplug B node states

        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def start(self) -> None:
        """Start asynchronous MQTT network loop."""
        if not self.config.enabled:
            logger.info("MQTT Bridge is disabled by configuration.")
            return

        if not PAHO_AVAILABLE:
            self.last_error = "paho-mqtt library not installed"
            logger.warning("MQTT Bridge cannot start: paho-mqtt library is not installed.")
            return

        if self.is_running:
            return

        self._loop = asyncio.get_running_loop()
        self.is_running = True

        try:
            # Try MQTT v5 with fallback to v3.1.1
            try:
                self.client = mqtt.Client(
                    client_id=self.config.client_id,
                    protocol=mqtt.MQTTv5,
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                )
            except (AttributeError, TypeError):
                self.client = mqtt.Client(client_id=self.config.client_id)

            if self.config.username:
                self.client.username_pw_set(self.config.username, self.config.password)

            # Assign callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Start non-blocking background network loop
            self.client.connect_async(
                self.config.host,
                self.config.port,
                self.config.keepalive,
            )
            self.client.loop_start()
            logger.info(
                "Launched MQTT Telemetry Bridge -> %s:%d (Client: %s)",
                self.config.host,
                self.config.port,
                self.config.client_id,
            )
        except Exception as e:
            self.last_error = f"MQTT start failed: {e}"
            self.is_connected = False
            logger.error("Failed to start MQTT client: %s", e)

    async def stop(self) -> None:
        """Gracefully disconnect MQTT client and terminate network loop."""
        self.is_running = False
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

        self.is_connected = False
        logger.info("Stopped MQTT Telemetry Bridge.")

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: Any, *args: Any) -> None:
        """Handle MQTT broker connection established."""
        # Handle both integer return code and ConnectFlags / ReasonCode
        code = getattr(rc, "value", rc) if hasattr(rc, "value") else rc
        if code == 0:
            self.is_connected = True
            self.last_error = None
            logger.info("Connected to MQTT Broker at %s:%d", self.config.host, self.config.port)
            # Subscribe to configured topics
            for topic in self.config.topics:
                client.subscribe(topic, qos=1)
                logger.info("Subscribed to MQTT topic: %s", topic)
        else:
            self.is_connected = False
            self.last_error = f"MQTT connection rejected with code: {code}"
            self.reconnect_count += 1
            logger.warning(self.last_error)

    def _on_disconnect(self, client: Any, userdata: Any, *args: Any) -> None:
        """Handle MQTT broker disconnection."""
        self.is_connected = False
        self.reconnect_count += 1
        logger.warning("Disconnected from MQTT Broker at %s:%d", self.config.host, self.config.port)

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        """Handle incoming telemetry message on subscribed topic."""
        self.total_messages_received += 1
        self.last_message_timestamp = time.time()

        try:
            topic = str(msg.topic)
            payload_str = msg.payload.decode("utf-8", errors="replace")
            
            # Check for Sparkplug B or standard JSON format
            if topic.startswith("spBv1.0/"):
                self._handle_sparkplug_message(topic, payload_str)
            else:
                self._handle_standard_telemetry(topic, payload_str)
        except Exception as e:
            logger.debug("Failed processing MQTT message on topic %s: %s", getattr(msg, "topic", "unknown"), e)

    def _handle_standard_telemetry(self, topic: str, payload_str: str) -> None:
        """Parse standard JSON telemetry payload."""
        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError:
            return

        # Case A: {"sensor_id": "...", "value": 12.3}
        if isinstance(data, dict) and "sensor_id" in data and "value" in data:
            self._inject_point(str(data["sensor_id"]), float(data["value"]))
            return

        # Case B: Multi-metric dict {"BHARATI.CHP.01.ACTIVE_POWER": 74.5, ...}
        if isinstance(data, dict):
            for k, v in data.items():
                try:
                    num_val = float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
                    self._inject_point(k, num_val)
                except (ValueError, TypeError):
                    continue

    def _handle_sparkplug_message(self, topic: str, payload_str: str) -> None:
        """Process Sparkplug B node lifecycle (NBIRTH, NDEATH, DDATA)."""
        # Format: spBv1.0/Group_ID/MessageType/Edge_Node_ID/[Device_ID]
        parts = topic.split("/")
        if len(parts) < 4:
            return

        msg_type = parts[2]
        edge_node_id = parts[3]
        device_id = parts[4] if len(parts) > 4 else None
        target_id = device_id or edge_node_id

        if msg_type in ("NBIRTH", "DBIRTH"):
            self.active_nodes[target_id] = {"status": "ONLINE", "birth_time": time.time()}
            logger.info("Sparkplug B Edge Node ONLINE: %s", target_id)
        elif msg_type in ("NDEATH", "DDEATH"):
            if target_id in self.active_nodes:
                self.active_nodes[target_id]["status"] = "OFFLINE"
                self.active_nodes[target_id]["death_time"] = time.time()
            logger.warning("Sparkplug B Edge Node OFFLINE (%s): %s", msg_type, target_id)
        elif msg_type in ("DDATA", "NDATA"):
            try:
                data = json.loads(payload_str)
                metrics = data.get("metrics", [])
                for metric in metrics:
                    name = metric.get("name")
                    val = metric.get("value")
                    if name and val is not None:
                        # Construct typed sensor ID
                        sensor_id = f"SPB.{target_id.upper()}.{name.upper()}"
                        try:
                            self._inject_point(sensor_id, float(val))
                        except (ValueError, TypeError):
                            pass
            except Exception:
                pass

    def _inject_point(self, sensor_id: str, value: float) -> None:
        """Dispatch reading into digital twin engine safely."""
        self.total_points_ingested += 1
        if not self.engine:
            return

        try:
            if hasattr(self.engine, "inject_sensor_override"):
                self.engine.inject_sensor_override(sensor_id, value)
            elif hasattr(self.engine, "state") and hasattr(self.engine.state, "sensors"):
                sensor = self.engine.state.sensors.get(sensor_id)
                if sensor:
                    sensor.current_value = value
                    sensor.last_updated = time.time()
        except Exception as e:
            logger.debug("Error injecting MQTT point %s: %s", sensor_id, e)

    async def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        """Publish command or telemetry to MQTT broker."""
        if not self.is_running or not self.client:
            self.last_error = "MQTT client not initialized or running"
            return False

        try:
            if isinstance(payload, (dict, list)):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)

            result = self.client.publish(topic, payload_str, qos=qos, retain=retain)
            # paho publish returns MQTTMessageInfo
            if hasattr(result, "rc"):
                code = getattr(result.rc, "value", result.rc)
                if code != 0:
                    self.last_error = f"Publish error code: {code}"
                    return False

            self.total_messages_published += 1
            return True
        except Exception as e:
            self.last_error = f"Publish failed: {e}"
            logger.error("Failed to publish to topic %s: %s", topic, e)
            return False

    def get_status(self) -> dict[str, Any]:
        """Return operational telemetry and diagnostic metrics."""
        return {
            "status": "CONNECTED" if self.is_connected else "DISCONNECTED",
            "is_running": self.is_running,
            "library_available": PAHO_AVAILABLE,
            "host": f"{self.config.host}:{self.config.port}",
            "client_id": self.config.client_id,
            "station_id": self.config.station_id,
            "subscribed_topics": self.config.topics,
            "total_messages_received": self.total_messages_received,
            "total_points_ingested": self.total_points_ingested,
            "total_messages_published": self.total_messages_published,
            "reconnect_count": self.reconnect_count,
            "last_error": self.last_error,
            "last_message_timestamp": self.last_message_timestamp,
            "active_sparkplug_nodes": len(self.active_nodes),
            "sparkplug_nodes": self.active_nodes,
        }
