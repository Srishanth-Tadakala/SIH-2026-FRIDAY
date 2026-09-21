"""Launch script for F.R.I.D.A.Y. Chief AI Digital Twin Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Run:
    python run_server.py
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  F.R.I.D.A.Y. CHIEF AI POLAR DIGITAL TWIN PLATFORM (SIH26060)")
    print("  Target Stations: Bharati Station & Maitri Station, East Antarctica")
    print("  Mainland Command: National Centre for Polar & Ocean Research (NCPOR), Goa")
    print("=" * 80)
    print("\n  -> Testing Cockpit UI:   http://127.0.0.1:8000/")
    print("  -> REST Health Probe:    http://127.0.0.1:8000/api/health")
    print("  -> Interactive API Docs: http://127.0.0.1:8000/docs")
    print("  -> Telemetry WebSocket:  ws://127.0.0.1:8000/ws/telemetry/bharati")
    print("=" * 80 + "\n")

    uvicorn.run(
        "backend.server.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info",
    )
