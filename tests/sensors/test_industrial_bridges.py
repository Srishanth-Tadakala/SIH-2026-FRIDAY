"""Test Suite for Industrial SCADA, PLC & Fieldbus Protocol Bridges.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies:
1. Modbus register map definitions and address integrity.
2. Virtual Modbus TCP Station Controller lifecycle.
3. Modbus Telemetry Bridge asynchronous polling and register reading.
4. Live injection of decoded float/int values into the Digital Twin Engine.
5. Discrete actuator coil writing (FC05).
6. Connection error handling, backoff resilience, and operational metrics.
"""

from __future__ import annotations

import asyncio
import pytest

from backend.core.engine import BharatiMasterTwinEngine
from backend.sensors.bridges.modbus_bridge import (
    ModbusBridgeConfig,
    ModbusTelemetryBridge,
)
from backend.sensors.bridges.modbus_map import (
    BHARATI_MODBUS_COIL_MAP,
    BHARATI_MODBUS_REGISTER_MAP,
    MODBUS_ADDRESS_TO_DEF,
    MODBUS_SENSOR_TO_DEF,
    ModbusDataType,
)
from tools.virtual_modbus_server import VirtualModbusStationController


def test_modbus_register_map_integrity() -> None:
    """Verify holding registers and coil mappings are well-formed and unique."""
    assert len(BHARATI_MODBUS_REGISTER_MAP) >= 15
    addresses = [r.address for r in BHARATI_MODBUS_REGISTER_MAP]
    assert len(addresses) == len(set(addresses)), "Duplicate Modbus register addresses detected"

    for r in BHARATI_MODBUS_REGISTER_MAP:
        assert r.address >= 0
        assert r.sensor_id.startswith("BHARATI")
        assert r.data_type in (ModbusDataType.FLOAT32, ModbusDataType.INT16, ModbusDataType.UINT16)

    # Verify lookups
    assert "BHARATI.CHP.01.ACTIVE_POWER" in MODBUS_SENSOR_TO_DEF
    assert 0 in MODBUS_ADDRESS_TO_DEF

    # Verify coils
    assert 0 in BHARATI_MODBUS_COIL_MAP
    assert 10 in BHARATI_MODBUS_COIL_MAP


def test_modbus_bridge_config_defaults() -> None:
    """Verify ModbusBridgeConfig sensible defaults."""
    cfg = ModbusBridgeConfig()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 5020
    assert cfg.station_id == "bharati"
    assert cfg.poll_interval_seconds == 1.0
    assert cfg.connect_timeout_seconds == 2.0
    assert cfg.enabled is True
    assert len(cfg.registers) == len(BHARATI_MODBUS_REGISTER_MAP)


@pytest.mark.asyncio
async def test_virtual_modbus_server_and_bridge_lifecycle() -> None:
    """Verify virtual Modbus TCP server startup, client connection, and graceful shutdown."""
    test_port = 15025
    server = VirtualModbusStationController(host="127.0.0.1", port=test_port)
    await server.start()

    config = ModbusBridgeConfig(
        host="127.0.0.1",
        port=test_port,
        poll_interval_seconds=0.1,
        connect_timeout_seconds=1.5,
    )
    bridge = ModbusTelemetryBridge(config=config)

    try:
        # Start bridge
        await bridge.start()
        await asyncio.sleep(0.3)

        status = bridge.get_status()
        assert status["is_running"] is True
        assert status["status"] == "CONNECTED"
        assert bridge.is_connected is True
        assert status["total_polls"] >= 1
    finally:
        await bridge.stop()
        await server.stop()

    assert bridge.is_connected is False
    assert bridge.is_running is False


@pytest.mark.asyncio
async def test_modbus_telemetry_reading_and_twin_injection() -> None:
    """Verify holding registers are polled, IEEE 754 floats decoded, and injected into Digital Twin."""
    test_port = 15026
    server = VirtualModbusStationController(host="127.0.0.1", port=test_port)
    # Set explicit non-default values on virtual controller
    server.set_float_register(0, 78.65)   # CHP-01 Active Power
    server.set_float_register(2, 401.5)   # Voltage
    server.set_float_register(6, 49.98)   # Frequency
    server.set_float_register(60, 3.25)   # Utilidor Water Line Temp
    await server.start()

    # Create digital twin engine
    engine = BharatiMasterTwinEngine(seed=42)
    engine.step(0.0)

    config = ModbusBridgeConfig(
        host="127.0.0.1",
        port=test_port,
        poll_interval_seconds=0.05,
    )
    bridge = ModbusTelemetryBridge(config=config, engine=engine)

    try:
        await bridge._ensure_connected()
        ingested = await bridge.poll_all_registers()
        assert ingested > 0

        # Verify values in twin engine cache
        readings = engine.get_all_readings()
        
        # Verify CHP-01 Power
        pwr_reading = readings.get("BHARATI.CHP.01.ACTIVE_POWER")
        pwr_val = pwr_reading.value if hasattr(pwr_reading, "value") else pwr_reading.get("value")
        assert abs(float(pwr_val) - 78.65) < 0.05

        # Verify Voltage
        v_reading = readings.get("BHARATI.CHP.01.VOLTAGE")
        v_val = v_reading.value if hasattr(v_reading, "value") else v_reading.get("value")
        assert abs(float(v_val) - 401.5) < 0.05

        # Verify Frequency
        f_reading = readings.get("BHARATI.CHP.01.FREQUENCY")
        f_val = f_reading.value if hasattr(f_reading, "value") else f_reading.get("value")
        assert abs(float(f_val) - 49.98) < 0.05

        # Verify Utilidor Water Temp
        pipe_reading = readings.get("BHARATI-PIPE-WATER01-TEMP")
        pipe_val = pipe_reading.value if hasattr(pipe_reading, "value") else pipe_reading.get("value")
        assert abs(float(pipe_val) - 3.25) < 0.05

    finally:
        await bridge.stop()
        await server.stop()


@pytest.mark.asyncio
async def test_modbus_actuator_coil_writing() -> None:
    """Verify writing discrete physical actuator coils via Modbus FC05."""
    test_port = 15027
    server = VirtualModbusStationController(host="127.0.0.1", port=test_port)
    await server.start()

    config = ModbusBridgeConfig(host="127.0.0.1", port=test_port)
    bridge = ModbusTelemetryBridge(config=config)

    try:
        await bridge._ensure_connected()

        # Coil 0: CHP-01 START_STOP
        assert server.get_coil(0) is True  # Default running
        success = await bridge.write_coil(address=0, value=False)
        assert success is True
        assert server.get_coil(0) is False  # Stopped

        # Coil 1: CHP-02 START_STOP
        assert server.get_coil(1) is False
        success = await bridge.write_coil(address=1, value=True)
        assert success is True
        assert server.get_coil(1) is True  # Started

        # Coil 10: Trace Heater 01
        success = await bridge.write_coil(address=10, value=True)
        assert success is True
        assert server.get_coil(10) is True

    finally:
        await bridge.stop()
        await server.stop()


@pytest.mark.asyncio
async def test_modbus_bridge_reconnection_resilience() -> None:
    """Verify bridge handles server being offline, records errors gracefully, and reconnects."""
    test_port = 15028
    config = ModbusBridgeConfig(
        host="127.0.0.1",
        port=test_port,
        connect_timeout_seconds=0.5,
    )
    bridge = ModbusTelemetryBridge(config=config)

    # 1. Server is offline: connect fails gracefully without uncaught exceptions
    connected = await bridge._ensure_connected()
    assert connected is False
    assert bridge.is_connected is False
    assert bridge.last_error is not None
    assert bridge.reconnect_count >= 1

    # 2. Server comes online: bridge reconnects cleanly
    server = VirtualModbusStationController(host="127.0.0.1", port=test_port)
    await server.start()

    try:
        connected = await bridge._ensure_connected()
        assert connected is True
        assert bridge.is_connected is True
        
        # Poll succeeds
        count = await bridge.poll_all_registers()
        assert count > 0
    finally:
        await bridge.stop()
        await server.stop()


def test_modbus_bridge_status_metrics() -> None:
    """Verify get_status returns complete telemetry dictionary."""
    config = ModbusBridgeConfig()
    bridge = ModbusTelemetryBridge(config=config)
    status = bridge.get_status()

    assert status["status"] == "DISCONNECTED"
    assert status["is_running"] is False
    assert status["target"] == "127.0.0.1:5020"
    assert status["station_id"] == "bharati"
    assert status["total_polls"] == 0
    assert status["total_points_ingested"] == 0
    assert status["registered_point_count"] == len(BHARATI_MODBUS_REGISTER_MAP)
