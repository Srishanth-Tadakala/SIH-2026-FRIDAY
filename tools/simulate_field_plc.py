"""Hardware SCADA / PLC Field Telemetry Simulator for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Demonstrates external hardware telemetry ingestion over HTTP/REST into F.R.I.D.A.Y. digital twin.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
import urllib.request
import urllib.error


def run_plc_simulator(
    base_url: str = "http://127.0.0.1:8000",
    station_id: str = "bharati",
    duration_seconds: float = 30.0,
    interval_seconds: float = 1.0,
    burst_fault: bool = False,
) -> None:
    """Stream simulated field PLC telemetry packets into F.R.I.D.A.Y. gateway."""
    print("=" * 70)
    print("📡 F.R.I.D.A.Y. EXTERNAL FIELD SCADA / PLC TELEMETRY INGESTOR")
    print(f"Target Gateway: {base_url}/api/telemetry/ingest")
    print(f"Station ID:     {station_id.upper()}")
    print(f"Simulation Mode: {'BURST FAULT INJECTION' if burst_fault else 'NOMINAL CONTINUOUS'}")
    print("=" * 70)

    endpoint = f"{base_url.rstrip('/')}/api/telemetry/ingest"
    start_time = time.time()
    packet_count = 0

    while time.time() - start_time < duration_seconds:
        t = time.time() - start_time
        packet_count += 1

        # Synthesize realistic field sensor points
        if burst_fault and t > 5.0 and t < 15.0:
            # Inject acute generator frequency and power dip
            chp_kw = 12.0 + random.uniform(-2.0, 2.0)
            chp_freq = 47.2 + random.uniform(-0.4, 0.4)
            pipe_temp = -1.5 + random.uniform(-0.2, 0.2)
            quality = "BAD"
        else:
            chp_kw = 65.0 + 3.0 * math.sin(t * 0.2) + random.uniform(-1.0, 1.0)
            chp_freq = 50.0 + 0.05 * math.cos(t * 0.1)
            pipe_temp = 4.5 + 0.3 * math.sin(t * 0.05)
            quality = "GOOD"

        payload = {
            "station_id": station_id,
            "source": "FIELD_PLC_SCHNEIDER_M340_BAY1",
            "readings": [
                {
                    "sensor_id": "BHARATI.CHP.01.ACTIVE_POWER",
                    "value": round(chp_kw, 2),
                    "quality": quality,
                    "timestamp": time.time(),
                },
                {
                    "sensor_id": "BHARATI.CHP.01.FREQUENCY",
                    "value": round(chp_freq, 3),
                    "quality": quality,
                    "timestamp": time.time(),
                },
                {
                    "sensor_id": "BHARATI-PIPE-WATER01-TEMP",
                    "value": round(pipe_temp, 2),
                    "quality": quality,
                    "timestamp": time.time(),
                },
            ],
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                status_code = resp.status
                res_body = json.loads(resp.read().decode("utf-8"))
            dt_ms = (time.perf_counter() - t0) * 1000.0

            print(
                f"[{time.strftime('%H:%M:%S')}] Packet #{packet_count:03d} -> "
                f"HTTP {status_code} ({dt_ms:.1f}ms) | CHP: {chp_kw:.1f} kW | Pipe: {pipe_temp:.1f}°C | Status: {res_body.get('status')}"
            )
        except urllib.error.URLError as e:
            print(f"[{time.strftime('%H:%M:%S')}] Packet #{packet_count:03d} FAILED: {e.reason}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Packet #{packet_count:03d} ERROR: {e}")

        time.sleep(interval_seconds)

    print("=" * 70)
    print(f"Ingestion completed. Sent {packet_count} packets in {duration_seconds:.1f}s.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="External PLC Field Telemetry Simulator")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of F.R.I.D.A.Y. server")
    parser.add_argument("--station", default="bharati", help="Target station ID")
    parser.add_argument("--duration", type=float, default=10.0, help="Run duration in seconds")
    parser.add_argument("--interval", type=float, default=1.0, help="Packet interval in seconds")
    parser.add_argument("--fault", action="store_true", help="Inject acute hardware fault telemetry")
    args = parser.parse_args()

    run_plc_simulator(
        base_url=args.url,
        station_id=args.station,
        duration_seconds=args.duration,
        interval_seconds=args.interval,
        burst_fault=args.fault,
    )
