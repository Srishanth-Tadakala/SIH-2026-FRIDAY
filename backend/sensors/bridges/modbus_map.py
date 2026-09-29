"""Modbus Register Mapping Definitions for F.R.I.D.A.Y. Polar Twin.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Maps physical PLC Modbus holding registers (FC03), input registers (FC04),
and coils (FC01/FC05) to station digital twin sensor points.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ModbusDataType(str, Enum):
    """Data types supported in Modbus register mappings."""
    FLOAT32 = "FLOAT32"      # 2 registers (32-bit IEEE 754 float)
    INT16 = "INT16"          # 1 register (16-bit signed integer)
    UINT16 = "UINT16"        # 1 register (16-bit unsigned integer)
    BOOL = "BOOL"            # Single discrete bit / coil


class ModbusFunction(str, Enum):
    """Modbus operation functions."""
    HOLDING_REGISTER = "HOLDING_REGISTER"  # FC03 / FC16
    INPUT_REGISTER = "INPUT_REGISTER"      # FC04
    COIL = "COIL"                          # FC01 / FC05


@dataclass(frozen=True)
class ModbusRegisterDef:
    """Definition of a single Modbus telemetry register or actuator coil."""
    address: int
    sensor_id: str
    data_type: ModbusDataType
    function: ModbusFunction = ModbusFunction.HOLDING_REGISTER
    scale: float = 1.0
    unit: str = ""
    description: str = ""


# ==============================================================================
# BHARATI STATION MODBUS HOLDING REGISTER MAP (0-indexed addressing)
# ==============================================================================
BHARATI_MODBUS_REGISTER_MAP: list[ModbusRegisterDef] = [
    # --------------------------------------------------------------------------
    # CHP Generator 1 (Woodward AGC-4 Controller #1: Base Address 0)
    # --------------------------------------------------------------------------
    ModbusRegisterDef(
        address=0,
        sensor_id="BHARATI.CHP.01.ACTIVE_POWER",
        data_type=ModbusDataType.FLOAT32,
        unit="kW",
        description="CHP-01 Active Electrical Power",
    ),
    ModbusRegisterDef(
        address=2,
        sensor_id="BHARATI.CHP.01.VOLTAGE",
        data_type=ModbusDataType.FLOAT32,
        unit="V",
        description="CHP-01 Alternator AC Voltage L-L",
    ),
    ModbusRegisterDef(
        address=4,
        sensor_id="BHARATI.CHP.01.CURRENT",
        data_type=ModbusDataType.FLOAT32,
        unit="A",
        description="CHP-01 Alternator Output Current",
    ),
    ModbusRegisterDef(
        address=6,
        sensor_id="BHARATI.CHP.01.FREQUENCY",
        data_type=ModbusDataType.FLOAT32,
        unit="Hz",
        description="CHP-01 Alternator Frequency",
    ),
    ModbusRegisterDef(
        address=8,
        sensor_id="BHARATI.CHP.01.RPM",
        data_type=ModbusDataType.FLOAT32,
        unit="RPM",
        description="CHP-01 Engine Crankshaft Speed",
    ),
    ModbusRegisterDef(
        address=10,
        sensor_id="BHARATI.CHP.01.COOLANT_TEMP",
        data_type=ModbusDataType.FLOAT32,
        unit="°C",
        description="CHP-01 Engine Coolant Temperature",
    ),
    ModbusRegisterDef(
        address=12,
        sensor_id="BHARATI.CHP.01.OIL_PRESSURE",
        data_type=ModbusDataType.FLOAT32,
        unit="bar",
        description="CHP-01 Engine Lube Oil Pressure",
    ),
    ModbusRegisterDef(
        address=14,
        sensor_id="BHARATI.CHP.01.RUNNING_STATUS",
        data_type=ModbusDataType.INT16,
        description="CHP-01 Binary Run Status (1=Running, 0=Stopped)",
    ),

    # --------------------------------------------------------------------------
    # CHP Generator 2 (Woodward AGC-4 Controller #2: Base Address 20)
    # --------------------------------------------------------------------------
    ModbusRegisterDef(
        address=20,
        sensor_id="BHARATI.CHP.02.ACTIVE_POWER",
        data_type=ModbusDataType.FLOAT32,
        unit="kW",
        description="CHP-02 Active Electrical Power",
    ),
    ModbusRegisterDef(
        address=22,
        sensor_id="BHARATI.CHP.02.VOLTAGE",
        data_type=ModbusDataType.FLOAT32,
        unit="V",
        description="CHP-02 Alternator AC Voltage L-L",
    ),
    ModbusRegisterDef(
        address=24,
        sensor_id="BHARATI.CHP.02.CURRENT",
        data_type=ModbusDataType.FLOAT32,
        unit="A",
        description="CHP-02 Alternator Output Current",
    ),
    ModbusRegisterDef(
        address=26,
        sensor_id="BHARATI.CHP.02.FREQUENCY",
        data_type=ModbusDataType.FLOAT32,
        unit="Hz",
        description="CHP-02 Alternator Frequency",
    ),
    ModbusRegisterDef(
        address=28,
        sensor_id="BHARATI.CHP.02.RPM",
        data_type=ModbusDataType.FLOAT32,
        unit="RPM",
        description="CHP-02 Engine Crankshaft Speed",
    ),
    ModbusRegisterDef(
        address=30,
        sensor_id="BHARATI.CHP.02.COOLANT_TEMP",
        data_type=ModbusDataType.FLOAT32,
        unit="°C",
        description="CHP-02 Engine Coolant Temperature",
    ),
    ModbusRegisterDef(
        address=32,
        sensor_id="BHARATI.CHP.02.OIL_PRESSURE",
        data_type=ModbusDataType.FLOAT32,
        unit="bar",
        description="CHP-02 Engine Lube Oil Pressure",
    ),
    ModbusRegisterDef(
        address=34,
        sensor_id="BHARATI.CHP.02.RUNNING_STATUS",
        data_type=ModbusDataType.INT16,
        description="CHP-02 Binary Run Status (1=Running, 0=Stopped)",
    ),

    # --------------------------------------------------------------------------
    # Station Main Switchgear & Grid Bus (Base Address 40)
    # --------------------------------------------------------------------------
    ModbusRegisterDef(
        address=40,
        sensor_id="BHARATI.GRID.BUS_VOLTAGE",
        data_type=ModbusDataType.FLOAT32,
        unit="V",
        description="Station Main 400V Switchgear Bus Voltage",
    ),
    ModbusRegisterDef(
        address=42,
        sensor_id="BHARATI.GRID.TOTAL_POWER_KW",
        data_type=ModbusDataType.FLOAT32,
        unit="kW",
        description="Total Station Electrical Power Demand",
    ),

    # --------------------------------------------------------------------------
    # Fuel System & Day Tank (Base Address 50)
    # --------------------------------------------------------------------------
    ModbusRegisterDef(
        address=50,
        sensor_id="BHARATI.FUEL.DAY_TANK_LEVEL_PCT",
        data_type=ModbusDataType.FLOAT32,
        unit="%",
        description="Generator Day Tank Fuel Level Percentage",
    ),
    ModbusRegisterDef(
        address=52,
        sensor_id="BHARATI.FUEL.TOTAL_RESERVE_L",
        data_type=ModbusDataType.FLOAT32,
        unit="L",
        description="Total Usable Fuel Farm Reserve Litres",
    ),

    # --------------------------------------------------------------------------
    # Utilidor Life-Support Pipelines (Base Address 60)
    # --------------------------------------------------------------------------
    ModbusRegisterDef(
        address=60,
        sensor_id="BHARATI-PIPE-WATER01-TEMP",
        data_type=ModbusDataType.FLOAT32,
        unit="°C",
        description="Utilidor Potable Fresh Water Line Temperature",
    ),
    ModbusRegisterDef(
        address=62,
        sensor_id="BHARATI-PIPE-SEWAGE01-TEMP",
        data_type=ModbusDataType.FLOAT32,
        unit="°C",
        description="Utilidor Greywater/Sewage Line Temperature",
    ),
]

# Quick index by address
MODBUS_ADDRESS_TO_DEF: dict[int, ModbusRegisterDef] = {
    r.address: r for r in BHARATI_MODBUS_REGISTER_MAP
}

# Quick index by sensor_id
MODBUS_SENSOR_TO_DEF: dict[str, ModbusRegisterDef] = {
    r.sensor_id: r for r in BHARATI_MODBUS_REGISTER_MAP
}


# ==============================================================================
# ACTUATOR COIL MAP (Discrete read/write commands: 0-indexed)
# ==============================================================================
BHARATI_MODBUS_COIL_MAP: dict[int, str] = {
    0: "BHARATI.ACTUATOR.CHP01.START_STOP",       # True = Start, False = Stop
    1: "BHARATI.ACTUATOR.CHP02.START_STOP",       # True = Start, False = Stop
    2: "BHARATI.ACTUATOR.CHP03.START_STOP",       # True = Start, False = Stop
    10: "BHARATI.ACTUATOR.TRACE_HEAT_WATER01",    # True = Enable primary trace heater
    11: "BHARATI.ACTUATOR.TRACE_HEAT_WATER02",    # True = Enable secondary backup heater
    20: "BHARATI.ACTUATOR.FUEL_TRANSFER_PUMP",    # True = Bulk to day tank transfer run
    30: "BHARATI.ACTUATOR.LOAD_SHED_SCIENCE",     # True = Shed non-critical science labs
}
