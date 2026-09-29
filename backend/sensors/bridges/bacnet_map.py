"""BACnet/IP (ANSI/ASHRAE Standard 135) Object Mapping Definitions for Bharati Station.

Maps BACnet/IP HVAC controllers, heat recovery ventilators (HRV), and utilidor
trace heating contactor circuits to F.R.I.D.A.Y. Digital Twin sensor identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BacnetObjectType(str, Enum):
    """Standard BACnet Object Types."""
    ANALOG_INPUT = "ANALOG_INPUT"      # 0
    ANALOG_OUTPUT = "ANALOG_OUTPUT"    # 1
    ANALOG_VALUE = "ANALOG_VALUE"      # 2
    BINARY_INPUT = "BINARY_INPUT"      # 3
    BINARY_OUTPUT = "BINARY_OUTPUT"    # 4
    BINARY_VALUE = "BINARY_VALUE"      # 5


@dataclass(frozen=True)
class BacnetObjectDef:
    """Defines mapping between a BACnet/IP Object and a Twin Sensor."""

    object_type: BacnetObjectType
    instance_id: int
    sensor_id: str
    description: str
    unit: str
    writable: bool = False
    default_value: float = 0.0


# Bharati Station Central HVAC & Utilidor Heat-Tracing Automation
BHARATI_BACNET_OBJECT_MAP: dict[tuple[BacnetObjectType, int], BacnetObjectDef] = {
    # 1. Analog Inputs (Sensors)
    (BacnetObjectType.ANALOG_INPUT, 101): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=101,
        sensor_id="BHARATI.HVAC.OUTSIDE_AIR_INTAKE_TEMP",
        description="HVAC Pre-Heated Fresh Air Intake Temperature",
        unit="°C",
        default_value=-22.4,
    ),
    (BacnetObjectType.ANALOG_INPUT, 102): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=102,
        sensor_id="BHARATI.HVAC.SUPPLY_AIR_TEMP",
        description="Main Station Habitation Module Supply Air Temperature",
        unit="°C",
        default_value=21.2,
    ),
    (BacnetObjectType.ANALOG_INPUT, 103): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=103,
        sensor_id="BHARATI.HVAC.RETURN_AIR_TEMP",
        description="Habitation Module Exhaust Air Return Temperature",
        unit="°C",
        default_value=19.8,
    ),
    (BacnetObjectType.ANALOG_INPUT, 104): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=104,
        sensor_id="BHARATI.HVAC.HEAT_EXCHANGER_EFFICIENCY",
        description="Plate Heat Exchanger Thermal Recovery Efficiency",
        unit="%",
        default_value=84.5,
    ),
    (BacnetObjectType.ANALOG_INPUT, 105): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=105,
        sensor_id="BHARATI.UTILIDOR.TRACE_CABLE_CURRENT_A",
        description="Utilidor Primary Trace Heating Circuit Current Draw",
        unit="A",
        default_value=18.4,
    ),
    (BacnetObjectType.ANALOG_INPUT, 106): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_INPUT,
        instance_id=106,
        sensor_id="BHARATI-PIPE-WATER01-TEMP",
        description="Potable Water Supply Utilidor Pipe Temperature",
        unit="°C",
        default_value=4.6,
    ),

    # 2. Analog Outputs & Setpoints (Writable)
    (BacnetObjectType.ANALOG_OUTPUT, 201): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_OUTPUT,
        instance_id=201,
        sensor_id="BHARATI.HVAC.HEATING_COIL_SETPOINT",
        description="HVAC Glycol Heating Loop Temperature Setpoint",
        unit="°C",
        writable=True,
        default_value=23.0,
    ),
    (BacnetObjectType.ANALOG_OUTPUT, 202): BacnetObjectDef(
        object_type=BacnetObjectType.ANALOG_OUTPUT,
        instance_id=202,
        sensor_id="BHARATI.HVAC.DAMPER_POSITION_PCT",
        description="Fresh Air Intake Modulating Damper Position",
        unit="%",
        writable=True,
        default_value=45.0,
    ),

    # 3. Binary Inputs (Alarm & Status)
    (BacnetObjectType.BINARY_INPUT, 301): BacnetObjectDef(
        object_type=BacnetObjectType.BINARY_INPUT,
        instance_id=301,
        sensor_id="BHARATI.HVAC.FILTER_DP_STATUS",
        description="Air Handling Unit HEPA Filter Differential Pressure (0=Clean, 1=Clogged)",
        unit="status",
        default_value=0.0,
    ),
    (BacnetObjectType.BINARY_INPUT, 302): BacnetObjectDef(
        object_type=BacnetObjectType.BINARY_INPUT,
        instance_id=302,
        sensor_id="BHARATI.HVAC.FIRE_SMOKE_DAMPER_STATUS",
        description="Life Support Fire & Smoke Damper Interlock (0=Open, 1=Tripped)",
        unit="status",
        default_value=0.0,
    ),

    # 4. Binary Outputs / Contactors (Writable)
    (BacnetObjectType.BINARY_OUTPUT, 401): BacnetObjectDef(
        object_type=BacnetObjectType.BINARY_OUTPUT,
        instance_id=401,
        sensor_id="BHARATI.TRACE_HEATER.01.STATUS",
        description="Utilidor Potable Water Trace Heater Solid-State Relay",
        unit="bool",
        writable=True,
        default_value=1.0,
    ),
    (BacnetObjectType.BINARY_OUTPUT, 402): BacnetObjectDef(
        object_type=BacnetObjectType.BINARY_OUTPUT,
        instance_id=402,
        sensor_id="BHARATI.TRACE_HEATER.02.STATUS",
        description="Utilidor Sewage Discharge Trace Heater Solid-State Relay",
        unit="bool",
        writable=True,
        default_value=1.0,
    ),
}
