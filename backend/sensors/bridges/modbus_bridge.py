"""Asynchronous Modbus TCP Telemetry & Control Bridge for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Connects to physical or virtual generator controllers (Woodward AGC-4, Cummins PowerCommand)
and substation switchgear over Modbus TCP. Reads holding registers asynchronously, decodes
IEEE 754 floating-point values, and injects live readings into the Digital Twin Engine.
Also provides reverse coil writing for Tier 1-3 physical actuator commands.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import struct
import time
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .modbus_map import (
    BHARATI_MODBUS_COIL_MAP,
    BHARATI_MODBUS_REGISTER_MAP,
    ModbusDataType,
    ModbusRegisterDef,
)

logger = logging.getLogger("friday.sensors.bridges.modbus")


@dataclass
class ModbusBridgeConfig:
    """Configuration for Modbus TCP Telemetry Bridge."""
    host: str = "127.0.0.1"
    port: int = 5020
    station_id: str = "bharati"
    poll_interval_seconds: float = 1.0
    connect_timeout_seconds: float = 2.0
    max_reconnect_delay_seconds: float = 30.0
    enabled: bool = True
    registers: list[ModbusRegisterDef] = field(default_factory=lambda: list(BHARATI_MODBUS_REGISTER_MAP))


class ModbusTelemetryBridge:
    """Asynchronous Modbus TCP Master Bridge integrating field PLCs with the Digital Twin."""

    def __init__(
        self,
        config: ModbusBridgeConfig,
        engine: Any | None = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.client: AsyncModbusTcpClient | None = None
        
        # State & Concurrency
        self.is_running: bool = False
        self.is_connected: bool = False
        self._loop_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        
        # Operational Metrics
        self.total_polls: int = 0
        self.total_points_ingested: int = 0
        self.total_errors: int = 0
        self.reconnect_count: int = 0
        self.last_poll_timestamp: float = 0.0
        self.last_poll_latency_ms: float = 0.0
        self.last_error: str | None = None

    def set_engine(self, engine: Any) -> None:
        """Dynamically attach or swap target digital twin engine."""
        self.engine = engine

    async def start(self) -> None:
        """Launch background asynchronous polling loop."""
        if not self.config.enabled:
            logger.info("Modbus Bridge is disabled by configuration.")
            return

        if self.is_running:
            return

        self.is_running = True
        self._loop_task = asyncio.create_task(self._poll_loop(), name="friday_modbus_bridge")
        logger.info(
            "Launched Modbus TCP Telemetry Bridge -> %s:%d (Interval: %.1fs)",
            self.config.host,
            self.config.port,
            self.config.poll_interval_seconds,
        )

    async def stop(self) -> None:
        """Gracefully stop bridge and close TCP socket."""
        self.is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except (asyncio.CancelledError, Exception):
                pass

        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

        self.is_connected = False
        logger.info("Stopped Modbus TCP Telemetry Bridge.")

    async def _ensure_connected(self) -> bool:
        """Establish or verify socket connection with exponential backoff."""
        if self.client and self.client.connected:
            self.is_connected = True
            return True

        self.is_connected = False
        try:
            if not self.client:
                self.client = AsyncModbusTcpClient(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.connect_timeout_seconds,
                )

            connected = await asyncio.wait_for(
                self.client.connect(),
                timeout=self.config.connect_timeout_seconds,
            )
            self.is_connected = bool(connected)
            if self.is_connected:
                logger.info(
                    "Connected to Modbus field controller at %s:%d",
                    self.config.host,
                    self.config.port,
                )
            return self.is_connected
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
            self.last_error = f"Connection failed: {e}"
            self.reconnect_count += 1
            return False
        except Exception as e:
            self.last_error = f"Unexpected connect error: {e}"
            self.reconnect_count += 1
            return False

    async def _poll_loop(self) -> None:
        """Continuous polling loop with adaptive backoff."""
        backoff = 1.0

        while self.is_running:
            try:
                connected = await self._ensure_connected()
                if not connected:
                    await asyncio.sleep(min(backoff, self.config.max_reconnect_delay_seconds))
                    backoff = min(backoff * 1.5, self.config.max_reconnect_delay_seconds)
                    continue

                backoff = 1.0  # Reset backoff on successful connection
                t0 = time.perf_counter()
                points_ingested = await self.poll_all_registers()
                dt_ms = (time.perf_counter() - t0) * 1000.0

                self.total_polls += 1
                self.total_points_ingested += points_ingested
                self.last_poll_timestamp = time.time()
                self.last_poll_latency_ms = round(dt_ms, 2)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.total_errors += 1
                self.last_error = f"Poll loop error: {e}"
                logger.warning("Error in Modbus poll loop: %s", e)

            await asyncio.sleep(self.config.poll_interval_seconds)

    async def poll_all_registers(self) -> int:
        """Execute a single polling sweep across all configured holding registers."""
        if not self.client or not self.client.connected:
            return 0

        # Group registers by contiguous chunks to minimize TCP round-trips
        # Sort registers by address
        sorted_regs = sorted(self.config.registers, key=lambda r: r.address)
        if not sorted_regs:
            return 0

        ingested_count = 0
        now = time.time()

        # Batch reads into blocks (up to 32 registers per Modbus FC03 request)
        async with self._lock:
            # For simplicity and maximum compatibility, read each register block
            i = 0
            while i < len(sorted_regs):
                batch = [sorted_regs[i]]
                start_addr = sorted_regs[i].address
                # Span needed for first item (1 for INT16, 2 for FLOAT32)
                span = 2 if sorted_regs[i].data_type == ModbusDataType.FLOAT32 else 1
                end_addr = start_addr + span

                # Collect contiguous registers within 32 registers
                j = i + 1
                while j < len(sorted_regs):
                    next_reg = sorted_regs[j]
                    next_span = 2 if next_reg.data_type == ModbusDataType.FLOAT32 else 1
                    if next_reg.address == end_addr and (end_addr + next_span - start_addr) <= 32:
                        batch.append(next_reg)
                        end_addr += next_span
                        j += 1
                    else:
                        break

                count_to_read = end_addr - start_addr
                try:
                    result = await self.client.read_holding_registers(
                        address=start_addr,
                        count=count_to_read,
                    )

                    if not result.isError() and hasattr(result, "registers"):
                        raw_words = result.registers
                        offset = 0
                        for reg_def in batch:
                            if reg_def.data_type == ModbusDataType.FLOAT32:
                                if offset + 1 < len(raw_words):
                                    w0, w1 = raw_words[offset], raw_words[offset + 1]
                                    # Standard big-endian float decoding
                                    packed = struct.pack(">HH", w0, w1)
                                    val = struct.unpack(">f", packed)[0]
                                    val = round(val * reg_def.scale, 3)
                                    offset += 2
                                else:
                                    break
                            else:
                                if offset < len(raw_words):
                                    val = raw_words[offset] * reg_def.scale
                                    offset += 1
                                else:
                                    break

                            # Ingest into twin engine if attached
                            if self.engine and hasattr(self.engine, "inject_sensor_override"):
                                self.engine.inject_sensor_override(
                                    sensor_id=reg_def.sensor_id,
                                    value=val,
                                    quality="GOOD",
                                )
                            ingested_count += 1
                    else:
                        self.total_errors += 1
                        self.last_error = f"Modbus read error at addr {start_addr}: {result}"

                except ModbusException as me:
                    self.total_errors += 1
                    self.last_error = f"ModbusException: {me}"
                except Exception as ex:
                    self.total_errors += 1
                    self.last_error = f"Read error: {ex}"

                i = j if j > i else i + 1

        return ingested_count

    async def write_coil(self, address: int, value: bool) -> bool:
        """Write single discrete actuator coil (FC05) for physical control."""
        if not self.client or not self.client.connected:
            return False

        async with self._lock:
            try:
                res = await self.client.write_coil(address=address, value=value)
                success = not res.isError()
                if success:
                    coil_name = BHARATI_MODBUS_COIL_MAP.get(address, f"COIL_{address}")
                    logger.info("Successfully wrote Modbus coil %d (%s) = %s", address, coil_name, value)
                return success
            except Exception as e:
                self.last_error = f"Write coil {address} failed: {e}"
                logger.error("Modbus write coil %d failed: %s", address, e)
                return False

    def get_status(self) -> dict[str, Any]:
        """Return live health and performance metrics for Cockpit UI and Prometheus."""
        return {
            "status": "CONNECTED" if self.is_connected else "DISCONNECTED",
            "is_running": self.is_running,
            "target": f"{self.config.host}:{self.config.port}",
            "station_id": self.config.station_id,
            "total_polls": self.total_polls,
            "total_points_ingested": self.total_points_ingested,
            "total_errors": self.total_errors,
            "reconnect_count": self.reconnect_count,
            "last_poll_timestamp": self.last_poll_timestamp,
            "last_poll_latency_ms": self.last_poll_latency_ms,
            "last_error": self.last_error,
            "registered_point_count": len(self.config.registers),
        }
