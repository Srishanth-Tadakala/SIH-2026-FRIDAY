"""OPC-UA (IEC 62541) Node Mapping Definitions for Bharati Station.

Maps OPC-UA Server Node IDs (e.g., Siemens S7-1500, Schneider M580 PLCs)
to F.R.I.D.A.Y. Digital Twin sensor identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class OpcUaNodeDef:
    """Defines mapping between an OPC-UA Variable Node and a Twin Sensor."""

    node_id: str
    sensor_id: str
    description: str
    engineering_unit: str
    data_type: str = "Float"  # Float, Double, Boolean, Int32
    deadband: float = 0.01   # Minimum delta before triggering digital twin override


# Standard Namespace index 2 for Bharati Station Automation
BHARATI_OPCUA_NODE_MAP: dict[str, OpcUaNodeDef] = {
    # Combined Heat & Power - Generator 1 (Siemens S7 Substation PLC)
    "ns=2;s=Bharati.CHP1.ActivePower": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP1.ActivePower",
        sensor_id="BHARATI.CHP.01.ACTIVE_POWER",
        description="CHP-01 Active Electrical Power Output",
        engineering_unit="kW",
        data_type="Float",
        deadband=0.5,
    ),
    "ns=2;s=Bharati.CHP1.CoolantTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP1.CoolantTemp",
        sensor_id="BHARATI.CHP.01.COOLANT_TEMP",
        description="CHP-01 Engine Jacket Water Coolant Temp",
        engineering_unit="°C",
        data_type="Float",
        deadband=0.2,
    ),
    "ns=2;s=Bharati.CHP1.OilPressure": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP1.OilPressure",
        sensor_id="BHARATI.CHP.01.OIL_PRESSURE",
        description="CHP-01 Engine Lubricating Oil Pressure",
        engineering_unit="bar",
        data_type="Float",
        deadband=0.1,
    ),
    "ns=2;s=Bharati.CHP1.ExhaustGasTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP1.ExhaustGasTemp",
        sensor_id="BHARATI.CHP.01.EXHAUST_TEMP",
        description="CHP-01 Turbocharger Exhaust Gas Temperature",
        engineering_unit="°C",
        data_type="Float",
        deadband=1.0,
    ),
    # Combined Heat & Power - Generator 2 (Standby)
    "ns=2;s=Bharati.CHP2.ActivePower": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP2.ActivePower",
        sensor_id="BHARATI.CHP.02.ACTIVE_POWER",
        description="CHP-02 Active Electrical Power Output",
        engineering_unit="kW",
        data_type="Float",
        deadband=0.5,
    ),
    "ns=2;s=Bharati.CHP2.CoolantTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.CHP2.CoolantTemp",
        sensor_id="BHARATI.CHP.02.COOLANT_TEMP",
        description="CHP-02 Engine Block Heater Temperature",
        engineering_unit="°C",
        data_type="Float",
        deadband=0.2,
    ),
    # Station Grid & Microgrid Controller
    "ns=2;s=Bharati.Grid.TotalPowerDemand": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.Grid.TotalPowerDemand",
        sensor_id="BHARATI.STATION.TOTAL_POWER_DEMAND",
        description="Bharati Microgrid Total Electrical Demand",
        engineering_unit="kW",
        data_type="Float",
        deadband=0.5,
    ),
    "ns=2;s=Bharati.Grid.BusVoltage": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.Grid.BusVoltage",
        sensor_id="BHARATI.STATION.BUS_VOLTAGE",
        description="Main 400V Switchboard Busbar Voltage",
        engineering_unit="V",
        data_type="Float",
        deadband=0.5,
    ),
    # Life Support & Utilidor Thermal Enclosure
    "ns=2;s=Bharati.LifeSupport.UtilidorWaterTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.LifeSupport.UtilidorWaterTemp",
        sensor_id="BHARATI-PIPE-WATER01-TEMP",
        description="Potable Water Supply Utilidor Line Temperature",
        engineering_unit="°C",
        data_type="Float",
        deadband=0.05,
    ),
    "ns=2;s=Bharati.LifeSupport.UtilidorSewageTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.LifeSupport.UtilidorSewageTemp",
        sensor_id="BHARATI.UTILIDOR.SEWAGE_TEMP",
        description="Blackwater Sewage Discharge Trace Heated Line",
        engineering_unit="°C",
        data_type="Float",
        deadband=0.1,
    ),
    "ns=2;s=Bharati.LifeSupport.TraceHeater01": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.LifeSupport.TraceHeater01",
        sensor_id="BHARATI.TRACE_HEATER.01.STATUS",
        description="Water Utilidor Trace Heating Contactor Status",
        engineering_unit="bool",
        data_type="Boolean",
        deadband=0.0,
    ),
    # Fuel Farm Bulk Storage
    "ns=2;s=Bharati.FuelFarm.ReserveLiters": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.FuelFarm.ReserveLiters",
        sensor_id="BHARATI.FUEL.RESERVE_LITERS",
        description="Polar Diesel Bulk Storage Tanks Total Volume",
        engineering_unit="L",
        data_type="Float",
        deadband=10.0,
    ),
    "ns=2;s=Bharati.FuelFarm.DayTankLevel": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.FuelFarm.DayTankLevel",
        sensor_id="BHARATI.FUEL.DAY_TANK_LEVEL",
        description="Powerhouse Daily Service Tank Percentage",
        engineering_unit="%",
        data_type="Float",
        deadband=0.5,
    ),
    # Meteorological Mast
    "ns=2;s=Bharati.Environmental.OutsideAirTemp": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.Environmental.OutsideAirTemp",
        sensor_id="BHARATI.ENV.OUTSIDE_TEMP",
        description="External Ambient Air Temperature at Larsemann Hills",
        engineering_unit="°C",
        data_type="Float",
        deadband=0.1,
    ),
    "ns=2;s=Bharati.Environmental.WindSpeed": OpcUaNodeDef(
        node_id="ns=2;s=Bharati.Environmental.WindSpeed",
        sensor_id="BHARATI.ENV.WIND_SPEED",
        description="Ultrasonic Anemometer Wind Speed",
        engineering_unit="m/s",
        data_type="Float",
        deadband=0.2,
    ),
}
