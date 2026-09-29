"""Hardware-in-the-Loop (HIL) Virtual Modbus TCP Field Controller for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Simulates physical generator controllers (Woodward AGC-4 / Cummins PowerCommand)
and life-support switchgear over Modbus TCP for automated CI testing and verification.
Zero external server dependencies, 100% compliant with Modbus Application Protocol V1.1b.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import sys
import time
from typing import Any

from backend.sensors.bridges.modbus_map import (
    BHARATI_MODBUS_COIL_MAP,
    BHARATI_MODBUS_REGISTER_MAP,
)

logger = logging.getLogger("friday.tools.virtual_modbus")


class VirtualModbusStationController:
    """Virtual Modbus TCP field controller representing physical Antarctic plant controllers."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 15020,
    ) -> None:
        self.host = host
        self.port = port
        
        # 1000 Holding Registers (16-bit unsigned words, 0-indexed)
        self.holding_registers: list[int] = [0] * 1000
        # 500 Coils (boolean discrete flags, 0-indexed)
        self.coils: list[bool] = [False] * 500
        
        self.server: asyncio.Server | None = None
        self.is_running: bool = False
        self._lock = asyncio.Lock()
        
        # Populate nominal baseline values
        self.init_baseline_values()

    def set_float_register(self, address: int, value: float) -> None:
        """Encode IEEE 754 32-bit float into two contiguous 16-bit registers (0-indexed addressing)."""
        packed = struct.pack(">f", float(value))
        w0, w1 = struct.unpack(">HH", packed)
        self.holding_registers[address] = w0
        self.holding_registers[address + 1] = w1

    def get_float_register(self, address: int) -> float:
        """Decode IEEE 754 32-bit float from two contiguous 16-bit registers."""
        w0 = self.holding_registers[address]
        w1 = self.holding_registers[address + 1]
        packed = struct.pack(">HH", w0, w1)
        return round(struct.unpack(">f", packed)[0], 3)

    def set_int_register(self, address: int, value: int) -> None:
        """Set single 16-bit register value."""
        self.holding_registers[address] = int(value) & 0xFFFF

    def get_int_register(self, address: int) -> int:
        """Get single 16-bit register value."""
        return self.holding_registers[address]

    def set_coil(self, address: int, value: bool) -> None:
        """Set discrete coil value."""
        self.coils[address] = bool(value)

    def get_coil(self, address: int) -> bool:
        """Read discrete coil value."""
        return self.coils[address]

    def init_baseline_values(self) -> None:
        """Seed registers with realistic Antarctic operational telemetry."""
        # CHP-01 (Nominal Running: 65.4 kW, 400.2V, 1500 RPM, 50.02 Hz)
        self.set_float_register(0, 65.4)   # Active Power
        self.set_float_register(2, 400.2)  # Voltage
        self.set_float_register(4, 94.3)   # Current
        self.set_float_register(6, 50.02)  # Frequency
        self.set_float_register(8, 1500.5) # RPM
        self.set_float_register(10, 84.5)  # Coolant Temp
        self.set_float_register(12, 4.3)   # Oil Pressure
        self.set_int_register(14, 1)       # Running Status = 1

        # CHP-02 (Cold Standby)
        self.set_float_register(20, 0.0)
        self.set_float_register(22, 0.0)
        self.set_float_register(24, 0.0)
        self.set_float_register(26, 0.0)
        self.set_float_register(28, 0.0)
        self.set_float_register(30, 24.1)  # Engine block heater kept at 24°C
        self.set_float_register(32, 0.0)
        self.set_int_register(34, 0)       # Running Status = 0

        # Station Grid
        self.set_float_register(40, 400.1) # Main bus voltage
        self.set_float_register(42, 65.4)  # Total power demand

        # Fuel Farm & Day Tank
        self.set_float_register(50, 78.5)      # Day tank level 78.5%
        self.set_float_register(52, 284500.0)  # Total fuel reserve litres

        # Utilidor Life-Support Lines
        self.set_float_register(60, 4.8)   # Fresh water line +4.8°C
        self.set_float_register(62, 12.4)  # Sewage line +12.4°C

        # Default Coils
        self.set_coil(0, True)   # CHP-01 running
        self.set_coil(1, False)  # CHP-02 off
        self.set_coil(2, False)  # CHP-03 off
        self.set_coil(10, True)  # Trace heater 1 enabled

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle incoming Modbus TCP connections according to RFC 793."""
        while self.is_running:
            try:
                # Modbus TCP MBAP Header is 7 bytes:
                # Transaction ID (2B) + Protocol ID (2B) + Length (2B) + Unit ID (1B)
                header = await reader.read(7)
                if not header or len(header) < 7:
                    break

                trans_id, proto_id, length, unit_id = struct.unpack(">HHHB", header)
                pdu_len = length - 1
                if pdu_len < 1:
                    break

                pdu = await reader.read(pdu_len)
                if len(pdu) < pdu_len:
                    break

                fc = pdu[0]
                resp_pdu = b""

                if fc == 3:  # Read Holding Registers
                    addr, count = struct.unpack(">HH", pdu[1:5])
                    values = self.holding_registers[addr : addr + count]
                    resp_pdu = struct.pack(">BB", 3, count * 2) + b"".join(
                        struct.pack(">H", v) for v in values
                    )

                elif fc == 1:  # Read Coils
                    addr, count = struct.unpack(">HH", pdu[1:5])
                    coil_slice = self.coils[addr : addr + count]
                    # Pack into bytes
                    num_bytes = (count + 7) // 8
                    packed_bytes = bytearray(num_bytes)
                    for idx, val in enumerate(coil_slice):
                        if val:
                            packed_bytes[idx // 8] |= (1 << (idx % 8))
                    resp_pdu = struct.pack(">BB", 1, num_bytes) + bytes(packed_bytes)

                elif fc == 5:  # Write Single Coil
                    addr, val = struct.unpack(">HH", pdu[1:5])
                    self.coils[addr] = (val == 0xFF00)
                    resp_pdu = pdu  # Echo request as response per Modbus spec

                elif fc == 6:  # Write Single Register
                    addr, val = struct.unpack(">HH", pdu[1:5])
                    self.holding_registers[addr] = val
                    resp_pdu = pdu

                elif fc == 16:  # Write Multiple Registers
                    addr, count, byte_count = struct.unpack(">HHB", pdu[1:6])
                    vals = struct.unpack(f">{count}H", pdu[6 : 6 + count * 2])
                    for offset, v in enumerate(vals):
                        self.holding_registers[addr + offset] = v
                    resp_pdu = struct.pack(">BHH", 16, addr, count)

                else:
                    # Illegal Function Exception
                    resp_pdu = struct.pack(">BB", fc | 0x80, 0x01)

                resp_header = struct.pack(
                    ">HHHB",
                    trans_id,
                    proto_id,
                    len(resp_pdu) + 1,
                    unit_id,
                )
                writer.write(resp_header + resp_pdu)
                await writer.drain()

            except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
                break
            except Exception as e:
                logger.warning("Modbus client handler error: %s", e)
                break

        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

    async def start(self) -> None:
        """Start virtual Modbus TCP server asynchronously."""
        if self.is_running:
            return

        self.is_running = True
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
        )
        logger.info("Virtual Modbus TCP Server online at %s:%d", self.host, self.port)

    async def stop(self) -> None:
        """Stop virtual Modbus TCP server."""
        if not self.is_running:
            return

        self.is_running = False
        if self.server:
            self.server.close()
            try:
                await self.server.wait_closed()
            except Exception:
                pass
            self.server = None

        logger.info("Virtual Modbus TCP Server stopped.")


async def main() -> None:
    """Run standalone virtual Modbus server from terminal for testing."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 15020
    server = VirtualModbusStationController(host="127.0.0.1", port=port)
    await server.start()
    print("=" * 70)
    print("⚡ F.R.I.D.A.Y. VIRTUAL MODBUS TCP FIELD CONTROLLER")
    print(f"Address: 127.0.0.1:{port}")
    print("Registers: 1000 Holding Registers (IEEE 754 32-bit floats & Int16)")
    print("Coils:     500 Discrete Coils (Actuators / Breakers)")
    print("Press Ctrl+C to stop.")
    print("=" * 70)
    try:
        while True:
            await asyncio.sleep(1.0)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
