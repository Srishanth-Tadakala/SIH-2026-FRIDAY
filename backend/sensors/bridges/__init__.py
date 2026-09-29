"""Industrial SCADA, Fieldbus and Hardware Protocol Bridges for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides native asynchronous bridges to physical and industrial protocol layers:
- Modbus TCP/RTU Master (Woodward/Cummins generator controllers, switchgear)
- OPC-UA Client/Server (Siemens S7-1500, Schneider M580 PLCs, SCADA gateways)
- MQTT v5 / Sparkplug B (Edge LoRaWAN, environmental micro-stations)
"""

from __future__ import annotations

from .modbus_bridge import ModbusTelemetryBridge, ModbusBridgeConfig
from .modbus_map import BHARATI_MODBUS_REGISTER_MAP, ModbusRegisterDef
from .opcua_bridge import OpcUaTelemetryBridge, OpcUaBridgeConfig
from .opcua_map import BHARATI_OPCUA_NODE_MAP, OpcUaNodeDef
from .mqtt_bridge import MqttTelemetryBridge, MqttBridgeConfig

__all__ = [
    "ModbusTelemetryBridge",
    "ModbusBridgeConfig",
    "BHARATI_MODBUS_REGISTER_MAP",
    "ModbusRegisterDef",
    "OpcUaTelemetryBridge",
    "OpcUaBridgeConfig",
    "BHARATI_OPCUA_NODE_MAP",
    "OpcUaNodeDef",
    "MqttTelemetryBridge",
    "MqttBridgeConfig",
]
