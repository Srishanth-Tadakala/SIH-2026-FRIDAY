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


# ==============================================================================
# OPC-UA Industrial Gateway Tests (IEC 62541)
# ==============================================================================

from backend.sensors.bridges.opcua_map import BHARATI_OPCUA_NODE_MAP, OpcUaNodeDef
from backend.sensors.bridges.opcua_bridge import (
    OpcUaBridgeConfig,
    OpcUaTelemetryBridge,
    ASYNCUA_AVAILABLE,
)
from tools.virtual_opcua_server import VirtualOpcUaStationController


def test_opcua_node_map_integrity() -> None:
    """Verify OPC-UA node mappings are well-formed and unique."""
    assert len(BHARATI_OPCUA_NODE_MAP) >= 10
    node_ids = list(BHARATI_OPCUA_NODE_MAP.keys())
    assert len(node_ids) == len(set(node_ids))

    for node_id, node_def in BHARATI_OPCUA_NODE_MAP.items():
        assert node_id.startswith("ns=2;s=Bharati.")
        assert node_def.sensor_id.startswith("BHARATI")
        assert node_def.data_type in ("Float", "Double", "Boolean", "Int32")
        assert node_def.deadband >= 0.0


def test_opcua_bridge_config_and_status() -> None:
    """Verify OPC-UA configuration defaults and status structure."""
    config = OpcUaBridgeConfig(endpoint="opc.tcp://localhost:4840/freeopcua/server/")
    assert config.station_id == "bharati"
    assert config.subscription_mode is True

    bridge = OpcUaTelemetryBridge(config=config)
    status = bridge.get_status()
    assert status["status"] == "DISCONNECTED"
    assert status["is_running"] is False
    assert status["endpoint"] == "opc.tcp://localhost:4840/freeopcua/server/"
    assert status["registered_node_count"] == len(BHARATI_OPCUA_NODE_MAP)


@pytest.mark.asyncio
async def test_virtual_opcua_server_and_bridge_integration() -> None:
    """Test full HIL loop: Virtual OPC-UA Server -> OpcUaTelemetryBridge -> Twin."""
    if not ASYNCUA_AVAILABLE:
        pytest.skip("asyncua not available in this test environment")

    test_port = 14842
    server = VirtualOpcUaStationController(host="127.0.0.1", port=test_port)
    await server.start()

    engine = BharatiMasterTwinEngine()
    config = OpcUaBridgeConfig(
        endpoint=f"opc.tcp://127.0.0.1:{test_port}/freeopcua/server/",
        subscription_mode=False,
        connect_timeout_seconds=2.0,
    )
    bridge = OpcUaTelemetryBridge(config=config, engine=engine)

    try:
        connected = await bridge._ensure_connected()
        assert connected is True
        assert bridge.is_connected is True

        # Explicit poll of all nodes
        polled = await bridge.poll_all_nodes()
        assert polled > 0

        # Verify values in twin engine
        readings = engine.get_all_readings()
        pwr = readings.get("BHARATI.CHP.01.ACTIVE_POWER")
        val = pwr.value if hasattr(pwr, "value") else pwr.get("value")
        assert abs(float(val) - 74.5) < 0.1

        # Test writing variable through bridge
        success = await bridge.write_node_value(
            node_id="ns=2;s=Bharati.CHP1.ActivePower",
            value=88.2,
            data_type="Float",
        )
        assert success is True

        # Verify updated value on server
        updated = await server.get_variable_value("ns=2;s=Bharati.CHP1.ActivePower")
        assert abs(float(updated) - 88.2) < 0.1
    finally:
        await bridge.stop()
        await server.stop()


@pytest.mark.asyncio
async def test_opcua_bridge_offline_resilience() -> None:
    """Verify OPC-UA bridge handles offline server gracefully."""
    config = OpcUaBridgeConfig(
        endpoint="opc.tcp://127.0.0.1:14849/freeopcua/server/",
        connect_timeout_seconds=0.5,
    )
    bridge = OpcUaTelemetryBridge(config=config)

    connected = await bridge._ensure_connected()
    assert connected is False
    assert bridge.is_connected is False
    assert bridge.reconnect_count >= 1
    assert bridge.last_error is not None


# ==============================================================================
# MQTT v5 & Sparkplug B Tests
# ==============================================================================

from backend.sensors.bridges.mqtt_bridge import (
    MqttBridgeConfig,
    MqttTelemetryBridge,
    PAHO_AVAILABLE,
)


def test_mqtt_bridge_config_and_status() -> None:
    """Verify MQTT bridge configuration defaults and diagnostic status."""
    config = MqttBridgeConfig(host="127.0.0.1", port=1883)
    assert config.station_id == "bharati"
    assert len(config.topics) >= 2

    bridge = MqttTelemetryBridge(config=config)
    status = bridge.get_status()
    assert status["status"] == "DISCONNECTED"
    assert status["is_running"] is False
    assert status["client_id"] == "friday-polar-twin-mqtt"
    assert status["total_messages_received"] == 0


def test_mqtt_telemetry_and_sparkplug_message_handling() -> None:
    """Verify payload parsing for standard JSON and Sparkplug B frames."""
    engine = BharatiMasterTwinEngine()
    bridge = MqttTelemetryBridge(engine=engine)

    # 1. Standard Single Sensor JSON
    bridge._handle_standard_telemetry(
        topic="antarctica/bharati/telemetry/chp1",
        payload_str='{"sensor_id": "BHARATI.CHP.01.ACTIVE_POWER", "value": 76.8}',
    )
    readings = engine.get_all_readings()
    pwr = readings.get("BHARATI.CHP.01.ACTIVE_POWER")
    val = pwr.value if hasattr(pwr, "value") else pwr.get("value")
    assert abs(float(val) - 76.8) < 0.1

    # 2. Standard Multi-Metric Dictionary
    bridge._handle_standard_telemetry(
        topic="antarctica/bharati/telemetry/environment",
        payload_str='{"BHARATI.ENV.OUTSIDE_TEMP": -31.5, "BHARATI.ENV.WIND_SPEED": 18.2}',
    )
    readings = engine.get_all_readings()
    temp = readings.get("BHARATI.ENV.OUTSIDE_TEMP")
    val_temp = temp.value if hasattr(temp, "value") else temp.get("value")
    assert abs(float(val_temp) - (-31.5)) < 0.1

    # 3. Sparkplug B Node Birth (NBIRTH)
    bridge._handle_sparkplug_message(
        topic="spBv1.0/Antarctica/NBIRTH/bharati/meteo_mast_01",
        payload_str="{}",
    )
    assert "meteo_mast_01" in bridge.active_nodes
    assert bridge.active_nodes["meteo_mast_01"]["status"] == "ONLINE"

    # 4. Sparkplug B Device Data (DDATA)
    bridge._handle_sparkplug_message(
        topic="spBv1.0/Antarctica/DDATA/bharati/meteo_mast_01",
        payload_str='{"metrics": [{"name": "BarometricPressure", "value": 988.5, "type": "Float"}]}',
    )
    readings = engine.get_all_readings()
    assert "SPB.METEO_MAST_01.BAROMETRICPRESSURE" in readings

    # 5. Sparkplug B Node Death (NDEATH)
    bridge._handle_sparkplug_message(
        topic="spBv1.0/Antarctica/NDEATH/bharati/meteo_mast_01",
        payload_str="{}",
    )
    assert bridge.active_nodes["meteo_mast_01"]["status"] == "OFFLINE"

