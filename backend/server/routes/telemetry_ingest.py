"""External SCADA / Field PLC Telemetry Ingestion Bridge for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Field PLCs, Modbus/OPC-UA Gateways, LoRaWAN Basestations -> Digital Twin Engine.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..state import get_server_state

logger = logging.getLogger("friday.server.routes.telemetry_ingest")

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry Ingestion"])

# Global Ingestion Telemetry Stats
_ingestion_stats: dict[str, Any] = {
    "total_readings_ingested": 0,
    "total_batches": 0,
    "known_sources": set(),
    "last_source": "NONE",
    "last_ingested_timestamp": 0.0,
}


class SingleReading(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor ID or Modbus address")
    value: Any = Field(..., description="Sensor numerical or boolean telemetry value")
    quality: str = Field(default="GOOD", description="OPC/SCADA Quality: GOOD, UNCERTAIN, BAD")
    timestamp: float | None = Field(default=None, description="Field PLC epoch timestamp")


class BatchIngestRequest(BaseModel):
    station_id: str = Field(default="bharati", description="Antarctic station ID (bharati/maitri)")
    source: str = Field(default="FIELD_SCADA_GATEWAY", description="Originating PLC / RTU identifier")
    readings: list[SingleReading] = Field(default_factory=list, description="Array of telemetry readings")
    # Also allow single inline reading
    sensor_id: str | None = Field(default=None, description="Optional single sensor ID")
    value: Any | None = Field(default=None, description="Optional single sensor value")
    quality: str = Field(default="GOOD", description="Quality flag")


@router.post("/ingest")
def ingest_field_telemetry(payload: BatchIngestRequest) -> dict[str, Any]:
    """Ingest live hardware PLC / SCADA sensor telemetry into the F.R.I.D.A.Y. digital twin."""
    server_state = get_server_state()
    engine = server_state.get_engine(payload.station_id)
    if not engine:
        raise HTTPException(status_code=404, detail=f"Target station '{payload.station_id}' not found.")

    readings_to_process: list[SingleReading] = list(payload.readings)
    if payload.sensor_id is not None and payload.value is not None:
        readings_to_process.append(
            SingleReading(
                sensor_id=payload.sensor_id,
                value=payload.value,
                quality=payload.quality,
                timestamp=time.time(),
            )
        )

    if not readings_to_process:
        raise HTTPException(status_code=400, detail="No sensor readings provided in ingestion request.")

    ingested_count = 0
    now = time.time()

    for item in readings_to_process:
        if hasattr(engine, "inject_sensor_override"):
            success = engine.inject_sensor_override(
                sensor_id=item.sensor_id,
                value=item.value,
                quality=item.quality,
            )
            if success:
                ingested_count += 1

    # Update global metrics
    _ingestion_stats["total_readings_ingested"] += ingested_count
    _ingestion_stats["total_batches"] += 1
    _ingestion_stats["known_sources"].add(payload.source)
    _ingestion_stats["last_source"] = payload.source
    _ingestion_stats["last_ingested_timestamp"] = now

    logger.info(
        "Ingested %d sensor points from %s into %s digital twin.",
        ingested_count,
        payload.source,
        payload.station_id,
    )

    return {
        "status": "INGESTED",
        "station_id": payload.station_id,
        "source": payload.source,
        "points_ingested": ingested_count,
        "timestamp": now,
    }


@router.get("/ingest/status")
def get_ingestion_status() -> dict[str, Any]:
    """Return hardware ingestion bridge metrics and gateway health."""
    server_state = get_server_state()
    active_engine = server_state.get_engine()
    total_twin_sensors = active_engine.sensor_count if active_engine else 0
    modbus_status = server_state.modbus_bridge.get_status() if hasattr(server_state, "modbus_bridge") else {}
    opcua_status = server_state.opcua_bridge.get_status() if hasattr(server_state, "opcua_bridge") else {}
    mqtt_status = server_state.mqtt_bridge.get_status() if hasattr(server_state, "mqtt_bridge") else {}
    bacnet_status = server_state.bacnet_bridge.get_status() if hasattr(server_state, "bacnet_bridge") else {}

    return {
        "status": "OPERATIONAL",
        "total_readings_ingested": _ingestion_stats["total_readings_ingested"],
        "total_batches_processed": _ingestion_stats["total_batches"],
        "active_sources": list(_ingestion_stats["known_sources"]),
        "last_source": _ingestion_stats["last_source"],
        "last_ingested_timestamp": _ingestion_stats["last_ingested_timestamp"],
        "total_twin_registered_sensors": total_twin_sensors,
        "supported_protocols": ["REST/JSON", "Modbus-TCP Bridge", "MQTT-Sparkplug B", "OPC-UA", "BACnet/IP"],
        "modbus_bridge": modbus_status,
        "opcua_bridge": opcua_status,
        "mqtt_bridge": mqtt_status,
        "bacnet_bridge": bacnet_status,
    }


class ModbusCoilRequest(BaseModel):
    address: int = Field(..., ge=0, description="Coil address (0-indexed)")
    value: bool = Field(..., description="Coil state (True=ON/Start, False=OFF/Stop)")
    station_id: str = Field(default="bharati", description="Station ID")


@router.get("/modbus/status")
def get_modbus_status() -> dict[str, Any]:
    """Return real-time operational status of the native Modbus TCP bridge."""
    server_state = get_server_state()
    if not hasattr(server_state, "modbus_bridge"):
        raise HTTPException(status_code=503, detail="Modbus bridge not initialized.")
    return server_state.modbus_bridge.get_status()


@router.get("/modbus/registers")
def get_modbus_register_catalog() -> dict[str, Any]:
    """Return configured Modbus register map catalog and coil definitions."""
    from ...sensors.bridges.modbus_map import (
        BHARATI_MODBUS_COIL_MAP,
        BHARATI_MODBUS_REGISTER_MAP,
    )
    return {
        "holding_registers": [
            {
                "address": r.address,
                "sensor_id": r.sensor_id,
                "data_type": r.data_type.value,
                "unit": r.unit,
                "description": r.description,
            }
            for r in BHARATI_MODBUS_REGISTER_MAP
        ],
        "coils": [
            {"address": addr, "actuator_id": name}
            for addr, name in sorted(BHARATI_MODBUS_COIL_MAP.items())
        ],
    }


@router.post("/modbus/coil")
async def write_modbus_coil(payload: ModbusCoilRequest) -> dict[str, Any]:
    """Write discrete actuator coil via Modbus FC05 (e.g. generator start/stop, trace heat)."""
    server_state = get_server_state()
    if not hasattr(server_state, "modbus_bridge"):
        raise HTTPException(status_code=503, detail="Modbus bridge not initialized.")

    success = await server_state.modbus_bridge.write_coil(payload.address, payload.value)
    if not success:
        last_err = server_state.modbus_bridge.last_error or "Coil write failed or bridge not connected."
        raise HTTPException(status_code=502, detail=f"Modbus write coil error: {last_err}")

    from ...sensors.bridges.modbus_map import BHARATI_MODBUS_COIL_MAP
    coil_name = BHARATI_MODBUS_COIL_MAP.get(payload.address, f"COIL_{payload.address}")

    return {
        "status": "COMMAND_DISPATCHED",
        "address": payload.address,
        "actuator_id": coil_name,
        "value": payload.value,
        "station_id": payload.station_id,
        "timestamp": time.time(),
    }


# ==============================================================================
# OPC-UA Industrial Gateway Endpoints (IEC 62541)
# ==============================================================================

class OpcUaWriteRequest(BaseModel):
    node_id: str = Field(..., description="OPC-UA NodeId string (e.g. ns=2;s=Bharati.CHP1.ActivePower)")
    value: Any = Field(..., description="Value to write to PLC variable")
    data_type: Optional[str] = Field(default=None, description="Optional type hint: Boolean, Float, Int32")


@router.get("/opcua/status")
def get_opcua_status() -> dict[str, Any]:
    """Return real-time operational status of the OPC-UA industrial gateway."""
    server_state = get_server_state()
    if not hasattr(server_state, "opcua_bridge"):
        raise HTTPException(status_code=503, detail="OPC-UA bridge not initialized.")
    return server_state.opcua_bridge.get_status()


@router.get("/opcua/nodes")
def get_opcua_node_catalog() -> dict[str, Any]:
    """Return registered OPC-UA node mappings for station PLC subsystems."""
    from ...sensors.bridges.opcua_map import BHARATI_OPCUA_NODE_MAP
    return {
        "total_nodes": len(BHARATI_OPCUA_NODE_MAP),
        "nodes": [
            {
                "node_id": node.node_id,
                "sensor_id": node.sensor_id,
                "description": node.description,
                "unit": node.engineering_unit,
                "data_type": node.data_type,
                "deadband": node.deadband,
            }
            for node in BHARATI_OPCUA_NODE_MAP.values()
        ],
    }


@router.post("/opcua/write")
async def write_opcua_variable(payload: OpcUaWriteRequest) -> dict[str, Any]:
    """Write setpoint or control command to an OPC-UA PLC Variable Node."""
    server_state = get_server_state()
    if not hasattr(server_state, "opcua_bridge"):
        raise HTTPException(status_code=503, detail="OPC-UA bridge not initialized.")

    success = await server_state.opcua_bridge.write_node_value(
        payload.node_id, payload.value, payload.data_type
    )
    if not success:
        last_err = server_state.opcua_bridge.last_error or "OPC-UA write failed or bridge not connected."
        raise HTTPException(status_code=502, detail=f"OPC-UA write error: {last_err}")

    return {
        "status": "COMMAND_DISPATCHED",
        "node_id": payload.node_id,
        "value": payload.value,
        "timestamp": time.time(),
    }


# ==============================================================================
# MQTT v5 & Sparkplug B Edge Connector Endpoints
# ==============================================================================

class MqttPublishRequest(BaseModel):
    topic: str = Field(..., description="Target MQTT topic")
    payload: Any = Field(..., description="Payload data (dict, list, or string)")
    qos: int = Field(default=1, ge=0, le=2, description="MQTT QoS level")
    retain: bool = Field(default=False, description="MQTT Retain flag")


@router.get("/mqtt/status")
def get_mqtt_status() -> dict[str, Any]:
    """Return operational status and metrics for the MQTT / Sparkplug B edge connector."""
    server_state = get_server_state()
    if not hasattr(server_state, "mqtt_bridge"):
        raise HTTPException(status_code=503, detail="MQTT bridge not initialized.")
    return server_state.mqtt_bridge.get_status()


@router.post("/mqtt/publish")
async def publish_mqtt_message(payload: MqttPublishRequest) -> dict[str, Any]:
    """Publish control command or telemetry frame to an edge MQTT topic."""
    server_state = get_server_state()
    if not hasattr(server_state, "mqtt_bridge"):
        raise HTTPException(status_code=503, detail="MQTT bridge not initialized.")

    success = await server_state.mqtt_bridge.publish(
        topic=payload.topic,
        payload=payload.payload,
        qos=payload.qos,
        retain=payload.retain,
    )
    if not success:
        last_err = server_state.mqtt_bridge.last_error or "MQTT publish failed or client disconnected."
        raise HTTPException(status_code=502, detail=f"MQTT publish error: {last_err}")

    return {
        "status": "MESSAGE_PUBLISHED",
        "topic": payload.topic,
        "timestamp": time.time(),
    }


# ==============================================================================
# BACnet/IP HVAC & Utilidor Heat-Tracing Endpoints (ANSI/ASHRAE 135)
# ==============================================================================

class BacnetWriteRequest(BaseModel):
    object_type: str = Field(..., description="BACnet Object Type: ANALOG_OUTPUT, BINARY_OUTPUT")
    instance_id: int = Field(..., ge=0, description="BACnet Object Instance ID")
    value: float = Field(..., description="Numeric setpoint or contactor state (0.0 or 1.0)")


@router.get("/bacnet/status")
def get_bacnet_status() -> dict[str, Any]:
    """Return operational telemetry and health metrics for the BACnet/IP bridge."""
    server_state = get_server_state()
    if not hasattr(server_state, "bacnet_bridge"):
        raise HTTPException(status_code=503, detail="BACnet bridge not initialized.")
    return server_state.bacnet_bridge.get_status()


@router.get("/bacnet/objects")
def get_bacnet_object_catalog() -> dict[str, Any]:
    """Return configured BACnet object catalog for station HVAC and utilidor lines."""
    from ...sensors.bridges.bacnet_map import BHARATI_BACNET_OBJECT_MAP
    return {
        "total_objects": len(BHARATI_BACNET_OBJECT_MAP),
        "objects": [
            {
                "object_type": obj.object_type.value,
                "instance_id": obj.instance_id,
                "sensor_id": obj.sensor_id,
                "description": obj.description,
                "unit": obj.unit,
                "writable": obj.writable,
                "default_value": obj.default_value,
            }
            for obj in BHARATI_BACNET_OBJECT_MAP.values()
        ],
    }


@router.post("/bacnet/write")
async def write_bacnet_property(payload: BacnetWriteRequest) -> dict[str, Any]:
    """Write setpoint or contactor state to a BACnet Analog/Binary Output."""
    server_state = get_server_state()
    if not hasattr(server_state, "bacnet_bridge"):
        raise HTTPException(status_code=503, detail="BACnet bridge not initialized.")

    from ...sensors.bridges.bacnet_map import BacnetObjectType

    try:
        obj_type = BacnetObjectType(payload.object_type)
    except ValueError:
        valid_types = [t.value for t in BacnetObjectType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid BACnet object type: {payload.object_type}. Valid: {valid_types}",
        )

    success = await server_state.bacnet_bridge.write_property(
        object_type=obj_type,
        instance_id=payload.instance_id,
        value=payload.value,
    )
    if not success:
        last_err = server_state.bacnet_bridge.last_error or "BACnet write failed."
        raise HTTPException(status_code=502, detail=f"BACnet write error: {last_err}")

    return {
        "status": "COMMAND_DISPATCHED",
        "object_type": payload.object_type,
        "instance_id": payload.instance_id,
        "value": payload.value,
        "timestamp": time.time(),
    }



