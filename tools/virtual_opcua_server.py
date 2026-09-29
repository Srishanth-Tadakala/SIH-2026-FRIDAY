"""Hardware-in-the-Loop (HIL) Virtual OPC-UA Station Automation Server.

Simulates Siemens S7-1500 and Schneider M580 PLCs running Bharati Station's
critical life-support systems, power generators, and utilidor heat tracing.
Used for automated CI/CD verification and end-to-end integration testing.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger("friday.tools.virtual_opcua")

try:
    from asyncua import Server, ua
    ASYNCUA_AVAILABLE = True
except ImportError:
    Server = None
    ua = None
    ASYNCUA_AVAILABLE = False


class VirtualOpcUaStationController:
    """In-process mock OPC-UA Server simulating Bharati Station Substation PLCs."""

    def __init__(self, host: str = "127.0.0.1", port: int = 4840) -> None:
        self.host = host
        self.port = port
        self.endpoint = f"opc.tcp://{host}:{port}/freeopcua/server/"
        self.server: Optional[Any] = None
        self.is_running: bool = False
        self._variables: dict[str, Any] = {}

    async def start(self) -> None:
        """Initialize address space, objects, variables, and start listening."""
        if not ASYNCUA_AVAILABLE:
            raise RuntimeError("asyncua library is not installed. Cannot start virtual OPC-UA server.")

        self.server = Server()
        await self.server.init()
        self.server.set_endpoint(self.endpoint)
        self.server.set_server_name("Bharati Polar Station Virtual Automation Gateway")

        # Set security policy to None for local HIL testing
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

        # Register Bharati Station namespace (idx=2)
        uri = "http://antarctica.friday/bharati/"
        idx = await self.server.register_namespace(uri)

        # Build Object Hierarchy
        objects = self.server.nodes.objects
        bharati_folder = await objects.add_folder(idx, "Bharati")

        # Subsystems
        chp1_folder = await bharati_folder.add_folder(idx, "CHP1")
        chp2_folder = await bharati_folder.add_folder(idx, "CHP2")
        grid_folder = await bharati_folder.add_folder(idx, "Grid")
        lifesupport_folder = await bharati_folder.add_folder(idx, "LifeSupport")
        fuelfarm_folder = await bharati_folder.add_folder(idx, "FuelFarm")
        env_folder = await bharati_folder.add_folder(idx, "Environmental")

        # 1. CHP-01 (Online)
        v = await chp1_folder.add_variable(ua.NodeId("Bharati.CHP1.ActivePower", idx), "ActivePower", 74.5)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP1.ActivePower"] = v

        v = await chp1_folder.add_variable(ua.NodeId("Bharati.CHP1.CoolantTemp", idx), "CoolantTemp", 82.3)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP1.CoolantTemp"] = v

        v = await chp1_folder.add_variable(ua.NodeId("Bharati.CHP1.OilPressure", idx), "OilPressure", 4.2)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP1.OilPressure"] = v

        v = await chp1_folder.add_variable(ua.NodeId("Bharati.CHP1.ExhaustGasTemp", idx), "ExhaustGasTemp", 445.0)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP1.ExhaustGasTemp"] = v

        # 2. CHP-02 (Cold Standby)
        v = await chp2_folder.add_variable(ua.NodeId("Bharati.CHP2.ActivePower", idx), "ActivePower", 0.0)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP2.ActivePower"] = v

        v = await chp2_folder.add_variable(ua.NodeId("Bharati.CHP2.CoolantTemp", idx), "CoolantTemp", 23.5)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.CHP2.CoolantTemp"] = v

        # 3. Grid
        v = await grid_folder.add_variable(ua.NodeId("Bharati.Grid.TotalPowerDemand", idx), "TotalPowerDemand", 63.8)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.Grid.TotalPowerDemand"] = v

        v = await grid_folder.add_variable(ua.NodeId("Bharati.Grid.BusVoltage", idx), "BusVoltage", 400.2)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.Grid.BusVoltage"] = v

        # 4. Life Support & Utilidor
        v = await lifesupport_folder.add_variable(ua.NodeId("Bharati.LifeSupport.UtilidorWaterTemp", idx), "UtilidorWaterTemp", 4.15)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.LifeSupport.UtilidorWaterTemp"] = v

        v = await lifesupport_folder.add_variable(ua.NodeId("Bharati.LifeSupport.UtilidorSewageTemp", idx), "UtilidorSewageTemp", 11.8)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.LifeSupport.UtilidorSewageTemp"] = v

        v = await lifesupport_folder.add_variable(ua.NodeId("Bharati.LifeSupport.TraceHeater01", idx), "TraceHeater01", True)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.LifeSupport.TraceHeater01"] = v

        # 5. Fuel Farm
        v = await fuelfarm_folder.add_variable(ua.NodeId("Bharati.FuelFarm.ReserveLiters", idx), "ReserveLiters", 284500.0)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.FuelFarm.ReserveLiters"] = v

        v = await fuelfarm_folder.add_variable(ua.NodeId("Bharati.FuelFarm.DayTankLevel", idx), "DayTankLevel", 79.2)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.FuelFarm.DayTankLevel"] = v

        # 6. Environmental
        v = await env_folder.add_variable(ua.NodeId("Bharati.Environmental.OutsideAirTemp", idx), "OutsideAirTemp", -28.4)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.Environmental.OutsideAirTemp"] = v

        v = await env_folder.add_variable(ua.NodeId("Bharati.Environmental.WindSpeed", idx), "WindSpeed", 14.8)
        await v.set_writable()
        self._variables["ns=2;s=Bharati.Environmental.WindSpeed"] = v

        await self.server.start()
        self.is_running = True
        logger.info("Virtual OPC-UA Station Server listening at %s", self.endpoint)

    async def stop(self) -> None:
        """Gracefully stop OPC-UA server."""
        if self.server:
            try:
                await self.server.stop()
            except Exception:
                pass
            self.server = None
        self.is_running = False
        logger.info("Virtual OPC-UA Station Server stopped.")

    async def set_variable_value(self, node_id: str, value: Any) -> None:
        """Set mock sensor value on the server (triggers subscriptions)."""
        var_node = self._variables.get(node_id)
        if not var_node:
            raise KeyError(f"Variable node {node_id} not registered in virtual server")
        await var_node.write_value(value)

    async def get_variable_value(self, node_id: str) -> Any:
        """Read raw value from server node."""
        var_node = self._variables.get(node_id)
        if not var_node:
            raise KeyError(f"Variable node {node_id} not registered in virtual server")
        return await var_node.read_value()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = VirtualOpcUaStationController(port=4840)

    async def main() -> None:
        await server.start()
        try:
            print("Virtual OPC-UA server running. Press Ctrl+C to terminate.")
            while True:
                await asyncio.sleep(1.0)
        except (KeyboardInterrupt, asyncio.CancelledError):
            await server.stop()

    asyncio.run(main())
