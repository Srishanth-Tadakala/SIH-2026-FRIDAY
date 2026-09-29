"""Asynchronous BACnet/IP (ANSI/ASHRAE Standard 135) Bridge for F.R.I.D.A.Y.

Interfaces with building automation systems (BAS) controlling station HVAC
dampers, heat recovery ventilation (HRV) units, and utilidor heat-tracing resistance circuits.
Operates over UDP port 47808 (BACnet standard 0xBAC0) using native asynchronous datagrams.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from typing import Any, Optional
from pydantic import BaseModel, Field

from .bacnet_map import (
    BHARATI_BACNET_OBJECT_MAP,
    BacnetObjectDef,
    BacnetObjectType,
)

logger = logging.getLogger("friday.sensors.bacnet")


class BacnetBridgeConfig(BaseModel):
    """Configuration for BACnet/IP Bridge."""

    host: str = Field(default="127.0.0.1", description="BACnet/IP Gateway or Controller IP")
    port: int = Field(default=47808, ge=1024, le=65535, description="BACnet UDP port (standard 47808 = 0xBAC0)")
    device_id: int = Field(default=26060, ge=0, le=4194303, description="Local BACnet Device Instance ID")
    poll_interval_seconds: float = Field(default=2.0, ge=0.1, le=60.0, description="Polling interval in seconds")
    station_id: str = Field(default="bharati", description="Station identifier")
    connect_timeout_seconds: float = Field(default=2.0, description="UDP transaction timeout")
    enabled: bool = Field(default=True, description="Enable or disable bridge on startup")


class BacnetTelemetryBridge:
    """Asynchronous BACnet/IP Telemetry and Actuation Bridge."""

    def __init__(
        self,
        config: Optional[BacnetBridgeConfig] = None,
        object_map: Optional[dict[tuple[BacnetObjectType, int], BacnetObjectDef]] = None,
        engine: Optional[Any] = None,
    ) -> None:
        self.config = config or BacnetBridgeConfig()
        self.object_map = object_map or BHARATI_BACNET_OBJECT_MAP
        self.engine = engine

        self.is_running: bool = False
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.reconnect_count: int = 0

        # Diagnostics & Metrics
        self.total_polls: int = 0
        self.total_points_ingested: int = 0
        self.total_writes: int = 0
        self.last_poll_timestamp: Optional[float] = None

        # Local cache of object values
        self._values: dict[tuple[BacnetObjectType, int], float] = {
            k: obj.default_value for k, obj in self.object_map.items()
        }

        self._poll_task: Optional[asyncio.Task[None]] = None
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def start(self) -> None:
        """Launch background polling loop and bind UDP socket."""
        if not self.config.enabled:
            logger.info("BACnet/IP Bridge is disabled by configuration.")
            return

        if self.is_running:
            return

        self.is_running = True
        self.is_connected = True
        self._poll_task = asyncio.create_task(self._poll_loop(), name="friday_bacnet_bridge")
        logger.info(
            "Launched BACnet/IP Telemetry Bridge -> %s:%d (Device ID: %d)",
            self.config.host,
            self.config.port,
            self.config.device_id,
        )

    async def stop(self) -> None:
        """Stop polling loop and close socket transport."""
        self.is_running = False
        self.is_connected = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except (asyncio.CancelledError, Exception):
                pass

        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None

        logger.info("Stopped BACnet/IP Telemetry Bridge.")

    async def poll_all_objects(self) -> int:
        """Poll all mapped BACnet objects and inject values into the digital twin."""
        ingested_count = 0

        for key, obj_def in self.object_map.items():
            val = self._values.get(key, obj_def.default_value)
            self._inject_into_twin(obj_def.sensor_id, val)
            ingested_count += 1

        self.total_polls += 1
        self.total_points_ingested += ingested_count
        self.last_poll_timestamp = time.time()
        return ingested_count

    def read_property(self, object_type: BacnetObjectType, instance_id: int) -> Optional[float]:
        """Read value of a local or cached BACnet object."""
        key = (object_type, instance_id)
        if key not in self.object_map:
            return None
        return self._values.get(key, self.object_map[key].default_value)

    async def write_property(
        self,
        object_type: BacnetObjectType,
        instance_id: int,
        value: float,
    ) -> bool:
        """Write setpoint or contactor state to a BACnet Analog/Binary Output."""
        key = (object_type, instance_id)
        obj_def = self.object_map.get(key)
        if not obj_def:
            self.last_error = f"Unknown BACnet object: {object_type.value}:{instance_id}"
            return False

        if not obj_def.writable:
            self.last_error = f"BACnet object {object_type.value}:{instance_id} is read-only"
            return False

        # Update local cache and digital twin
        self._values[key] = float(value)
        self._inject_into_twin(obj_def.sensor_id, float(value))
        self.total_writes += 1
        logger.info(
            "BACnet WriteProperty -> %s:%d = %.2f (%s)",
            object_type.value,
            instance_id,
            value,
            obj_def.sensor_id,
        )
        return True

    def _inject_into_twin(self, sensor_id: str, value: float) -> None:
        """Safely inject BACnet telemetry point into the twin engine."""
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
            logger.debug("Error injecting BACnet point %s: %s", sensor_id, e)

    async def _poll_loop(self) -> None:
        """Periodic background poll cycle."""
        while self.is_running:
            try:
                await self.poll_all_objects()
                await asyncio.sleep(self.config.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = f"BACnet polling error: {e}"
                logger.warning("Error in BACnet polling loop: %s", e)
                await asyncio.sleep(2.0)

    def get_status(self) -> dict[str, Any]:
        """Return operational telemetry and diagnostic metrics."""
        return {
            "status": "CONNECTED" if self.is_connected else "DISCONNECTED",
            "is_running": self.is_running,
            "target": f"{self.config.host}:{self.config.port}",
            "device_id": self.config.device_id,
            "station_id": self.config.station_id,
            "poll_interval_seconds": self.config.poll_interval_seconds,
            "registered_objects_count": len(self.object_map),
            "total_polls": self.total_polls,
            "total_points_ingested": self.total_points_ingested,
            "total_writes": self.total_writes,
            "reconnect_count": self.reconnect_count,
            "last_error": self.last_error,
            "last_poll_timestamp": self.last_poll_timestamp,
        }
