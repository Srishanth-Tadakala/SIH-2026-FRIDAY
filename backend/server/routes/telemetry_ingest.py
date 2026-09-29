"""External SCADA / Field PLC Telemetry Ingestion Bridge for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Field PLCs, Modbus/OPC-UA Gateways, LoRaWAN Basestations -> Digital Twin Engine.
"""

from __future__ import annotations

import logging
import time
from typing import Any

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

    return {
        "status": "OPERATIONAL",
        "total_readings_ingested": _ingestion_stats["total_readings_ingested"],
        "total_batches_processed": _ingestion_stats["total_batches"],
        "active_sources": list(_ingestion_stats["known_sources"]),
        "last_source": _ingestion_stats["last_source"],
        "last_ingested_timestamp": _ingestion_stats["last_ingested_timestamp"],
        "total_twin_registered_sensors": total_twin_sensors,
        "supported_protocols": ["REST/JSON", "Modbus-TCP Bridge", "MQTT-Sparkplug B", "OPC-UA"],
        "modbus_bridge": modbus_status,
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

