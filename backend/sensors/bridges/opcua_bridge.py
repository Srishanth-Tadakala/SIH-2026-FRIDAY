"""Industrial OPC-UA Client/Server Gateway (IEC 62541) for F.R.I.D.A.Y.

Connects to Siemens S7-1500, Schneider M580, and Beckhoff IPC industrial PLCs
governing station life support, power generation, and cryogenic HVAC circuits.
Provides asynchronous subscription handling, deadband filtering, and rate-buffered
injection into the Bharati Digital Twin Engine.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from .opcua_map import BHARATI_OPCUA_NODE_MAP, OpcUaNodeDef

logger = logging.getLogger("friday.sensors.opcua")

try:
    from asyncua import Client, ua
    from asyncua.common.subscription import Subscription
    ASYNCUA_AVAILABLE = True
except ImportError:
    Client = None
    ua = None
    Subscription = None
    ASYNCUA_AVAILABLE = False
    logger.warning("asyncua library is not installed. OPC-UA Bridge will run in disabled/stub mode.")


class OpcUaBridgeConfig(BaseModel):
    """Configuration parameters for OPC-UA Gateway connection."""

    endpoint: str = Field(default="opc.tcp://127.0.0.1:4840/freeopcua/server/", description="OPC-UA server TCP endpoint URL")
    station_id: str = Field(default="bharati", description="Station identifier")
    poll_interval_seconds: float = Field(default=1.0, ge=0.05, le=60.0, description="Periodic poll / fallback interval")
    subscription_mode: bool = Field(default=True, description="Enable real-time data change notifications")
    batch_interval_seconds: float = Field(default=0.1, ge=0.01, le=1.0, description="Twin ingestion batch interval in seconds")
    queue_maxsize: int = Field(default=1000, description="Buffer queue size to prevent loop saturation during floods")
    connect_timeout_seconds: float = Field(default=3.0, ge=0.5, le=30.0, description="Socket connect timeout")
    max_reconnect_delay_seconds: float = Field(default=30.0, description="Maximum backoff reconnect delay")
    security_policy: str = Field(default="None", description="OPC-UA Security Policy URI")
    enabled: bool = Field(default=True, description="Enable or disable bridge on startup")


class _OpcUaSubHandler:
    """Internal subscription handler forwarding data changes to the bridge queue."""

    def __init__(self, bridge: "OpcUaTelemetryBridge") -> None:
        self.bridge = bridge

    def datachange_notification(self, node: Any, val: Any, data: Any) -> None:
        """Called by asyncua when a subscribed variable changes."""
        try:
            node_id_str = str(node.nodeid)
            self.bridge._enqueue_data_change(node_id_str, val)
        except Exception as e:
            logger.debug("Error processing datachange_notification: %s", e)


class OpcUaTelemetryBridge:
    """Asynchronous OPC-UA Client Bridge to Station PLCs and SCADA controllers."""

    def __init__(
        self,
        config: Optional[OpcUaBridgeConfig] = None,
        node_map: Optional[dict[str, OpcUaNodeDef]] = None,
        engine: Optional[Any] = None,
    ) -> None:
        self.config = config or OpcUaBridgeConfig()
        self.node_map = node_map or BHARATI_OPCUA_NODE_MAP
        self.engine = engine

        self.client: Optional[Any] = None
        self.subscription: Optional[Any] = None
        self.is_running: bool = False
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.reconnect_count: int = 0

        # Diagnostics & Metrics
        self.total_polls: int = 0
        self.total_events_received: int = 0
        self.total_points_ingested: int = 0
        self.last_poll_timestamp: Optional[float] = None
        self.last_ingest_timestamp: Optional[float] = None

        # Value cache for deadband calculations
        self._last_values: dict[str, float] = {}

        # Buffering queue and async task handles
        self._queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue(maxsize=self.config.queue_maxsize)
        self._poll_task: Optional[asyncio.Task[None]] = None
        self._batch_worker_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Launch background polling, subscription, and batch ingestion workers."""
        if not self.config.enabled:
            logger.info("OPC-UA Bridge is disabled by configuration.")
            return

        if not ASYNCUA_AVAILABLE:
            self.last_error = "asyncua library not installed"
            logger.warning("OPC-UA Bridge cannot start: asyncua library is not installed.")
            return

        if self.is_running:
            return

        self.is_running = True
        self._batch_worker_task = asyncio.create_task(
            self._batch_worker(), name="friday_opcua_batch_worker"
        )
        self._poll_task = asyncio.create_task(
            self._connection_and_poll_loop(), name="friday_opcua_bridge"
        )
        logger.info(
            "Launched OPC-UA Telemetry Bridge -> %s (SubMode: %s)",
            self.config.endpoint,
            self.config.subscription_mode,
        )

    async def stop(self) -> None:
        """Gracefully disconnect OPC-UA client and stop worker tasks."""
        self.is_running = False

        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except (asyncio.CancelledError, Exception):
                pass

        if self._batch_worker_task and not self._batch_worker_task.done():
            self._batch_worker_task.cancel()
            try:
                await self._batch_worker_task
            except (asyncio.CancelledError, Exception):
                pass

        await self._disconnect_client()
        logger.info("Stopped OPC-UA Telemetry Bridge.")

    async def _disconnect_client(self) -> None:
        """Close active OPC-UA session."""
        self.is_connected = False
        if self.subscription:
            try:
                await self.subscription.delete()
            except Exception:
                pass
            self.subscription = None

        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.client = None

    async def _ensure_connected(self) -> bool:
        """Establish session to OPC-UA server and setup subscriptions."""
        if not ASYNCUA_AVAILABLE:
            self.last_error = "asyncua library not available"
            return False

        if self.client and self.is_connected:
            return True

        self.is_connected = False
        try:
            self.client = Client(url=self.config.endpoint, timeout=self.config.connect_timeout_seconds)
            await asyncio.wait_for(
                self.client.connect(),
                timeout=self.config.connect_timeout_seconds,
            )
            self.is_connected = True
            logger.info("Connected to OPC-UA server at %s", self.config.endpoint)

            if self.config.subscription_mode:
                await self._setup_subscriptions()

            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            self.last_error = f"OPC-UA connection failed: {e}"
            self.reconnect_count += 1
            await self._disconnect_client()
            return False
        except Exception as e:
            self.last_error = f"OPC-UA connect error: {e}"
            self.reconnect_count += 1
            await self._disconnect_client()
            return False

    async def _setup_subscriptions(self) -> None:
        """Subscribe to all mapped Variable Nodes for real-time change events."""
        if not self.client or not self.is_connected:
            return

        try:
            handler = _OpcUaSubHandler(self)
            self.subscription = await self.client.create_subscription(100, handler)
            
            nodes_to_subscribe = []
            for node_id_str in self.node_map.keys():
                try:
                    node = self.client.get_node(node_id_str)
                    nodes_to_subscribe.append(node)
                except Exception as e:
                    logger.debug("Could not resolve OPC-UA node %s: %s", node_id_str, e)

            if nodes_to_subscribe:
                await self.subscription.subscribe_data_change(nodes_to_subscribe)
                logger.info(
                    "Subscribed to %d OPC-UA nodes on server %s",
                    len(nodes_to_subscribe),
                    self.config.endpoint,
                )
        except Exception as e:
            logger.warning("Failed to establish OPC-UA subscriptions: %s", e)

    def _enqueue_data_change(self, node_id: str, value: Any) -> None:
        """Thread-safe / non-blocking enqueue of data changes."""
        self.total_events_received += 1
        try:
            self._queue.put_nowait((node_id, value))
        except asyncio.QueueFull:
            # Drop oldest or skip if buffer full during major spike
            try:
                self._queue.get_nowait()
                self._queue.put_nowait((node_id, value))
            except Exception:
                pass

    async def _batch_worker(self) -> None:
        """Drain buffered changes and inject into Digital Twin with deadband filtering."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.batch_interval_seconds)
                if self._queue.empty():
                    continue

                batch: list[tuple[str, Any]] = []
                while not self._queue.empty() and len(batch) < 200:
                    try:
                        batch.append(self._queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                for node_id_str, val in batch:
                    node_def = self.node_map.get(node_id_str)
                    if not node_def:
                        continue

                    # Process deadband filtering
                    try:
                        numeric_val = float(val) if not isinstance(val, bool) else (1.0 if val else 0.0)
                    except (ValueError, TypeError):
                        numeric_val = 0.0

                    last_val = self._last_values.get(node_def.sensor_id)
                    if last_val is not None and abs(numeric_val - last_val) < node_def.deadband:
                        continue  # Below deadband threshold

                    self._last_values[node_def.sensor_id] = numeric_val
                    self._inject_into_twin(node_def.sensor_id, numeric_val)
                    self.total_points_ingested += 1

                self.last_ingest_timestamp = time.time()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in OPC-UA batch worker: %s", e)

    async def poll_all_nodes(self) -> int:
        """Explicitly poll all mapped nodes (used in fallback or non-subscription mode)."""
        if not await self._ensure_connected() or not self.client:
            return 0

        ingested_count = 0
        for node_id_str, node_def in self.node_map.items():
            try:
                node = self.client.get_node(node_id_str)
                val = await node.read_value()
                
                try:
                    num_val = float(val) if not isinstance(val, bool) else (1.0 if val else 0.0)
                except (ValueError, TypeError):
                    num_val = 0.0

                self._inject_into_twin(node_def.sensor_id, num_val)
                self._last_values[node_def.sensor_id] = num_val
                ingested_count += 1
            except Exception as e:
                logger.debug("Failed reading OPC-UA node %s: %s", node_id_str, e)

        self.total_polls += 1
        self.total_points_ingested += ingested_count
        self.last_poll_timestamp = time.time()
        return ingested_count

    async def write_node_value(self, node_id: str, value: Any, data_type: Optional[str] = None) -> bool:
        """Write setpoint or control command to an OPC-UA Variable Node."""
        if not await self._ensure_connected() or not self.client:
            return False

        try:
            node = self.client.get_node(node_id)
            
            # Format variant if specified
            if ua and data_type == "Boolean":
                variant = ua.DataValue(ua.Variant(bool(value), ua.VariantType.Boolean))
                await node.write_value(variant)
            elif ua and data_type == "Float":
                # Check current node data type or use Double/Float
                try:
                    variant = ua.DataValue(ua.Variant(float(value), ua.VariantType.Double))
                    await node.write_value(variant)
                except Exception:
                    variant = ua.DataValue(ua.Variant(float(value), ua.VariantType.Float))
                    await node.write_value(variant)
            elif ua and data_type == "Double":
                variant = ua.DataValue(ua.Variant(float(value), ua.VariantType.Double))
                await node.write_value(variant)
            else:
                await node.write_value(value)

            logger.info("Successfully wrote value %s to OPC-UA node %s", value, node_id)
            return True
        except Exception as e:
            self.last_error = f"Failed writing to node {node_id}: {e}"
            logger.error("OPC-UA write failure: %s", e)
            return False

    def _inject_into_twin(self, sensor_id: str, value: float) -> None:
        """Inject reading into Digital Twin engine."""
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
            logger.error("Error injecting OPC-UA point %s into twin: %s", sensor_id, e)

    async def _connection_and_poll_loop(self) -> None:
        """Continuous polling / heartbeat monitor with exponential backoff."""
        backoff = 1.0

        while self.is_running:
            try:
                connected = await self._ensure_connected()
                if not connected:
                    await asyncio.sleep(min(backoff, self.config.max_reconnect_delay_seconds))
                    backoff = min(backoff * 1.5, self.config.max_reconnect_delay_seconds)
                    continue

                backoff = 1.0
                if not self.config.subscription_mode:
                    await self.poll_all_nodes()

                await asyncio.sleep(self.config.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = f"OPC-UA loop exception: {e}"
                logger.warning("OPC-UA loop encountered error: %s", e)
                await asyncio.sleep(2.0)

    def get_status(self) -> dict[str, Any]:
        """Return operational telemetry and diagnostic metrics."""
        return {
            "status": "CONNECTED" if self.is_connected else "DISCONNECTED",
            "is_running": self.is_running,
            "library_available": ASYNCUA_AVAILABLE,
            "endpoint": self.config.endpoint,
            "station_id": self.config.station_id,
            "subscription_mode": self.config.subscription_mode,
            "registered_node_count": len(self.node_map),
            "total_polls": self.total_polls,
            "total_events_received": self.total_events_received,
            "total_points_ingested": self.total_points_ingested,
            "reconnect_count": self.reconnect_count,
            "last_error": self.last_error,
            "last_poll_timestamp": self.last_poll_timestamp,
            "last_ingest_timestamp": self.last_ingest_timestamp,
            "buffer_queue_size": self._queue.qsize(),
        }
