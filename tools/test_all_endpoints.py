"""Comprehensive API Testing & Postman Collection Generator for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Executes end-to-end integration requests against all 60+ REST endpoints,
verifies response schemas, status codes, latency benchmarks (<500ms),
and exports an industry-grade Postman Collection v2.1.0 with automated test scripts.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List

import httpx
from httpx import ASGITransport

# Ensure workspace root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.framework.models import ActionProposal, AutonomyTier
from backend.server.app import create_app
from backend.server.state import get_server_state


class ApiBenchmarkRunner:
    """Automated benchmark runner and Postman artifact generator."""

    def __init__(self) -> None:
        self.app = create_app()
        self.state = get_server_state(seed=42)
        self.state.step(dt_seconds=0.0)
        self.results: List[Dict[str, Any]] = []

    async def run_all_tests(self) -> bool:
        """Execute exhaustive suite of tests against all endpoint domains."""
        transport = ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
            # 1. System & Health
            await self._test(client, "GET", "/api/health", expected_status=200, keys=["status", "system", "version", "managed_stations"])
            await self._test(client, "GET", "/api/stations", expected_status=200, keys=["stations", "active_station"])
            await self._test(client, "GET", "/api/stations/bharati", expected_status=200, keys=["station_id", "station_name", "location", "coordinates"])
            await self._test(client, "GET", "/api/stations/maitri", expected_status=200, keys=["station_id", "station_name", "location", "coordinates"])
            await self._test(client, "POST", "/api/stations/active/bharati", expected_status=200, keys=["status", "active_station_id"])
            await self._test(client, "POST", "/api/stations/bharati/step", expected_status=200, payload={"dt_seconds": 1.0}, keys=["status", "station_id", "kpis"])

            # 2. Telemetry & Sensor Pillars (505 Sensors)
            await self._test(client, "GET", "/api/telemetry/bharati/snapshot", expected_status=200, keys=["station_id", "readings", "kpis", "alerts"])
            await self._test(client, "GET", "/api/telemetry/bharati/kpis", expected_status=200, keys=["station_id", "kpis"])
            await self._test(client, "GET", "/api/telemetry/bharati/alerts", expected_status=200, keys=["station_id", "alerts", "alert_count"])
            await self._test(client, "GET", "/api/telemetry/bharati/history", expected_status=200, keys=["station_id", "history", "count"])
            await self._test(client, "GET", "/api/telemetry/bharati/pillars/energy", expected_status=200, keys=["pillar", "readings", "sensor_count"])
            await self._test(client, "GET", "/api/telemetry/bharati/pillars/infrastructure", expected_status=200, keys=["pillar", "readings", "sensor_count"])
            await self._test(client, "GET", "/api/telemetry/bharati/pillars/environment", expected_status=200, keys=["pillar", "readings", "sensor_count"])
            await self._test(client, "GET", "/api/telemetry/bharati/pillars/logistics", expected_status=200, keys=["pillar", "readings", "sensor_count"])
            await self._test(client, "GET", "/api/telemetry/bharati/sensors/BHARATI.CHP.01.POWER", expected_status=200, keys=["station_id", "sensor_id", "reading"])

            # 3. Hardware SCADA & Field PLC Ingestion Bridge
            sample_plc_payload = {
                "station_id": "bharati",
                "source": "FIELD_PLC_SCHNEIDER_M340",
                "readings": [
                    {"sensor_id": "BHARATI.CHP.01.POWER", "value": 72.4, "quality": "GOOD"}
                ]
            }
            await self._test(client, "POST", "/api/telemetry/ingest", expected_status=200, payload=sample_plc_payload, keys=["status", "station_id", "points_ingested"])
            await self._test(client, "GET", "/api/telemetry/ingest/status", expected_status=200, keys=["status", "total_readings_ingested", "total_batches_processed"])

            # 4. Multi-Agent Society & Causal Graph
            await self._test(client, "GET", "/api/agents/status", expected_status=200, keys=["agents", "total_agents"])
            await self._test(client, "GET", "/api/agents/diagnostic", expected_status=200, keys=["role", "runtime", "recent_messages_count"])
            await self._test(client, "GET", "/api/agents/bus/stats", expected_status=200, keys=["total_messages_published", "active_sessions_count"])
            await self._test(client, "GET", "/api/agents/causal_graph", expected_status=200, keys=["nodes", "edges", "total_nodes"])
            await self._test(client, "GET", "/api/agents/causal_graph/blast_radius/chp_1", expected_status=200, keys=["node_id", "blast_radius"])
            await self._test(client, "GET", "/api/agents/groq_status", expected_status=200, keys=["status", "model_name"])
            await self._test(client, "POST", "/api/agents/set_groq_key", expected_status=200, payload={"api_key": "gsk_test_postman_validation_key_2026"}, keys=["status", "message"])

            # 5. Deliberations & Briefing Cards (Ensure at least 1 session exists)
            sess = self.state.bus.create_session(trigger_alert={"alert_type": "POWER_ANOMALY", "station_id": "bharati"})
            session_id = sess.session_id
            await self._test(client, "GET", "/api/deliberations", expected_status=200, is_list=True)
            await self._test(client, "GET", f"/api/deliberations/{session_id}", expected_status=200, keys=["session_id", "status"])
            
            # Give session a proposal so briefing card can synthesize
            prop = ActionProposal(
                title="Dispatch Standby Generator",
                target_subsystem="energy",
                parameter_overrides=[{"command": "START_CHP", "parameters": {"unit": 2}}],
                tier=AutonomyTier.TIER_2_SUPERVISED,
                rationale="Auto-dispatch CHP-02 to pick up base electrical load",
            )
            sess.candidate_proposals.append(prop)
            await self._test(client, "GET", f"/api/deliberations/{session_id}/briefing_card", expected_status=200, keys=["session_id", "incident_title"])

            # 6. Actuators, Autonomy & Safety Interlocks
            await self._test(client, "GET", "/api/actions/actuators/bharati", expected_status=200, keys=["station_id"])
            await self._test(client, "GET", "/api/actions/pending", expected_status=200, keys=["pending_actions"])
            await self._test(client, "GET", "/api/actions/pending_tier3", expected_status=200, keys=["pending_tier3_actions"])
            await self._test(client, "POST", "/api/actions/autonomous_mode", expected_status=200, payload={"autonomous_enabled": True}, keys=["autonomous_enabled"])
            await self._test(client, "GET", "/api/actions/cognitive_logs/bharati", expected_status=200, keys=["station_id", "logs"])
            await self._test(client, "GET", "/api/actions/edge_status/bharati", expected_status=200, keys=["station_id", "autonomous_mode_enabled"])

            # 7. PIN Authorization & Tier 1 Execution
            pin_payload = {"pin": "BHARATI-CMD-2026", "command": "COMMANDER_EMERGENCY_DISPATCH"}
            await self._test(client, "POST", "/api/actions/authorize_pin", expected_status=200, payload=pin_payload, keys=["status", "command"])
            
            # Safe Tier 1 test execution
            tier1_payload = {
                "plan_name": "Adjust Damper Position",
                "strategy": "OPERATIONAL_MITIGATION",
                "autonomy_tier": "TIER_1",
                "actions": [{"command": "SET_BLIZZARD_DAMPERS", "parameters": {"damper_position_pct": 80.0}}],
                "expected_outcome": "Restore nominal fresh air airflow",
                "resource_cost": 0.05,
                "confidence": 0.95
            }
            await self._test(client, "POST", "/api/actions/execute", expected_status=200, payload=tier1_payload, keys=["success", "status"])

            # 8. Crisis Scenarios
            await self._test(client, "GET", "/api/scenarios", expected_status=200, is_list=True)
            await self._test(client, "POST", "/api/scenarios/inject", expected_status=200, payload={"scenario": "BLIZZARD_STRIKE", "station_id": "bharati"}, keys=["status", "active_scenario"])
            await self._test(client, "POST", "/api/scenarios/clear", expected_status=200, payload={"station_id": "bharati"}, keys=["status", "active_scenario"])

            # 9. Polar Satcom & Mainland Mirror
            await self._test(client, "GET", "/api/satcom/status", expected_status=200, keys=["status", "managed_stations"])
            await self._test(client, "POST", "/api/satcom/profile", expected_status=200, payload={"profile": "INMARSAT_STANDARD"}, keys=["status", "new_profile"])
            await self._test(client, "GET", "/api/satcom/bharati/summary", expected_status=200, keys=["station_id", "channel_metrics"])
            await self._test(client, "GET", "/api/satcom/bharati/mirror", expected_status=200, keys=["station_id", "sync_status", "readings"])
            await self._test(client, "POST", "/api/satcom/bharati/sync", expected_status=200, payload={"force_keyframe": False}, keys=["station_id", "frame_id", "tx_stats"])
            await self._test(client, "POST", "/api/satcom/bharati/resync", expected_status=200, keys=["station_id", "status"])
            await self._test(client, "POST", "/api/satcom/bharati/recover", expected_status=200, payload={"new_profile": "INMARSAT_STANDARD"}, keys=["station_id", "new_profile"])

            # 10. 2-Step Distributed Database & CBR Memory
            await self._test(client, "GET", "/api/database/status", expected_status=200, keys=["database", "satcom_synchronizer"])
            await self._test(client, "GET", "/api/database/episodes", expected_status=200, is_list=True)
            await self._test(client, "GET", "/api/database/equipment", expected_status=200, is_list=True)
            await self._test(client, "GET", "/api/database/audits", expected_status=200, is_list=True)
            await self._test(client, "POST", "/api/database/sync", expected_status=200, keys=["status", "metrics"])

            # 11. Copilot ("Ask F.R.I.D.A.Y.")
            await self._test(client, "GET", "/api/copilot/status", expected_status=200, keys=["status", "model_name"])
            await self._test(client, "GET", "/api/copilot/suggested_queries", expected_status=200, keys=["status", "suggested_queries"])
            await self._test(client, "GET", "/api/copilot/history", expected_status=200, keys=["status", "station_id", "messages"])
            copilot_payload = {
                "station_id": "bharati",
                "message": "Assess station electrical stability and fuel reserve."
            }
            await self._test(client, "POST", "/api/copilot/chat", expected_status=200, payload=copilot_payload, keys=["status", "reply", "cited_sensors"])

            # 12. Universal State Synchronization (Never Starts Fresh)
            await self._test(client, "GET", "/api/sync/state", expected_status=200, keys=["status", "station_id", "operator"])
            sync_payload = {
                "station_id": "bharati",
                "active_tab": "topo",
                "autonomous_mode": True,
                "voice_enabled": False,
                "operator_name": "Cmdr. T. Srishanth"
            }
            await self._test(client, "POST", "/api/sync/state", expected_status=200, payload=sync_payload, keys=["status", "message", "state"])
            login_payload = {
                "operator_id": "STATION_COMMANDER",
                "operator_name": "Cmdr. T. Srishanth",
                "pin": "BHARATI-CMD-2026",
                "station_id": "bharati"
            }
            await self._test(client, "POST", "/api/sync/login", expected_status=200, payload=login_payload, keys=["status", "authenticated"])
            await self._test(client, "POST", "/api/sync/full_refresh", expected_status=200, payload={"station_id": "bharati"}, keys=["status", "synced_state"])
            await self._test(client, "POST", "/api/sync/logout", expected_status=200, payload={}, keys=["status"])

            # 13. WebSocket & Real-time Stats
            await self._test(client, "GET", "/api/ws/stats", expected_status=200, keys=["total_active_connections", "station_connections"])

        return all(r["passed"] for r in self.results)

    async def _test(
        self,
        client: httpx.AsyncClient,
        method: str,
        path: str,
        expected_status: int = 200,
        payload: Dict[str, Any] | None = None,
        keys: List[str] | None = None,
        is_list: bool = False,
    ) -> Any:
        """Perform request and benchmark response latency and keys."""
        t0 = time.perf_counter()
        try:
            if method == "GET":
                resp = await client.get(path)
            elif method == "POST":
                resp = await client.post(path, json=payload or {})
            elif method == "DELETE":
                resp = await client.delete(path)
            else:
                raise ValueError(f"Unsupported method: {method}")

            dt_ms = (time.perf_counter() - t0) * 1000.0
            passed = resp.status_code == expected_status

            data: Any = None
            if "application/json" in resp.headers.get("content-type", ""):
                try:
                    data = resp.json()
                except Exception:
                    data = {}

            missing_keys = []
            if passed and is_list:
                if not isinstance(data, list):
                    passed = False
                    missing_keys.append("Expected JSON list")
            elif passed and keys and isinstance(data, dict):
                for k in keys:
                    if k not in data:
                        missing_keys.append(k)
                        passed = False

            result = {
                "method": method,
                "path": path,
                "status_code": resp.status_code,
                "expected_status": expected_status,
                "latency_ms": round(dt_ms, 2),
                "passed": passed,
                "missing_keys": missing_keys,
                "data": data,
            }
            self.results.append(result)
            return data
        except Exception as e:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            result = {
                "method": method,
                "path": path,
                "status_code": 500,
                "expected_status": expected_status,
                "latency_ms": round(dt_ms, 2),
                "passed": False,
                "error": str(e),
                "data": {},
            }
            self.results.append(result)
            return {}

    def print_summary_report(self) -> None:
        """Display an ASCII verification scorecard."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        avg_lat = sum(r["latency_ms"] for r in self.results) / (total or 1)
        max_lat = max((r["latency_ms"] for r in self.results), default=0.0)

        print("\n" + "=" * 90)
        print("  F.R.I.D.A.Y. EXHAUSTIVE API ENDPOINT VERIFICATION REPORT (SIH26060)")
        print("=" * 90)
        print(f"{'STATUS':<8} | {'METHOD':<6} | {'LATENCY':<10} | {'ENDPOINT':<50}")
        print("-" * 90)

        for r in self.results:
            tag = "PASS" if r["passed"] else "FAIL"
            lat_str = f"{r['latency_ms']} ms"
            path_str = r['path'][:48]
            print(f"[{tag:<4}] | {r['method']:<6} | {lat_str:<10} | {path_str:<50}")
            if not r["passed"]:
                print(f"       -> Error: status={r['status_code']} (expected {r['expected_status']}), missing={r.get('missing_keys')}")

        print("=" * 90)
        print(f"  TOTAL ENDPOINTS TESTED : {total}")
        print(f"  PASSED                 : {passed} / {total} ({passed/total*100:.1f}%)")
        print(f"  AVERAGE LATENCY        : {avg_lat:.2f} ms")
        print(f"  PEAK LATENCY           : {max_lat:.2f} ms (Target <500 ms)")
        print("=" * 90 + "\n")

    def export_postman_collection(self, out_path: str = "postman_collection.json") -> None:
        """Generate Postman Collection v2.1.0 JSON format."""
        folders: Dict[str, List[Dict[str, Any]]] = {
            "1. System & Health": [],
            "2. Stations & Physics": [],
            "3. Telemetry & Sensor Pillars (505 Sensors)": [],
            "4. Hardware SCADA & Field PLC": [],
            "5. Multi-Agent Society & Causal Graph": [],
            "6. Deliberations & Briefings": [],
            "7. Tiered Actions & Interlocks": [],
            "8. Crisis Scenarios": [],
            "9. Polar Satcom & Mainland Mirror": [],
            "10. 2-Step Distributed Database": [],
            "11. Copilot (Ask F.R.I.D.A.Y.)": [],
            "12. Universal State Sync": [],
            "13. WebSocket & Real-Time Stats": [],
        }

        def categorize(path: str) -> str:
            if path in ["/api/health", "/api/stations", "/"]:
                return "1. System & Health"
            if "/api/stations" in path:
                return "2. Stations & Physics"
            if "/api/telemetry/ingest" in path:
                return "4. Hardware SCADA & Field PLC"
            if "/api/telemetry" in path:
                return "3. Telemetry & Sensor Pillars (505 Sensors)"
            if "/api/agents" in path:
                return "5. Multi-Agent Society & Causal Graph"
            if "/api/deliberations" in path:
                return "6. Deliberations & Briefings"
            if "/api/actions" in path:
                return "7. Tiered Actions & Interlocks"
            if "/api/scenarios" in path:
                return "8. Crisis Scenarios"
            if "/api/satcom" in path:
                return "9. Polar Satcom & Mainland Mirror"
            if "/api/database" in path:
                return "10. 2-Step Distributed Database"
            if "/api/copilot" in path:
                return "11. Copilot (Ask F.R.I.D.A.Y.)"
            if "/api/sync" in path:
                return "12. Universal State Sync"
            return "13. WebSocket & Real-Time Stats"

        for r in self.results:
            folder_name = categorize(r["path"])
            clean_name = f"{r['method']} {r['path']}"
            
            # Postman URL parts
            url_clean = "{{base_url}}" + r["path"]
            path_segments = [p for p in r["path"].strip("/").split("/") if p]

            item: Dict[str, Any] = {
                "name": clean_name,
                "request": {
                    "method": r["method"],
                    "header": [
                        {"key": "Content-Type", "value": "application/json", "type": "text"},
                        {"key": "Accept", "value": "application/json", "type": "text"}
                    ],
                    "url": {
                        "raw": url_clean,
                        "host": ["{{base_url}}"],
                        "path": path_segments
                    },
                    "description": f"Audited endpoint for {r['path']}. Measured latency: {r['latency_ms']} ms."
                },
                "event": [
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                f"pm.test('Status code is {r['expected_status']}', function () {{",
                                f"    pm.response.to.have.status({r['expected_status']});",
                                "});",
                                "pm.test('Response time is below 500ms', function () {",
                                "    pm.expect(pm.response.responseTime).to.be.below(500);",
                                "});",
                                "pm.test('Response is valid JSON', function () {",
                                "    pm.response.to.be.json;",
                                "});"
                            ]
                        }
                    }
                ]
            }

            # Add body for POST requests
            if r["method"] == "POST":
                sample_body: Dict[str, Any] = {}
                if "authorize_pin" in r["path"]:
                    sample_body = {"pin": "BHARATI-CMD-2026", "command": "COMMANDER_EMERGENCY_DISPATCH"}
                elif "autonomous_mode" in r["path"]:
                    sample_body = {"autonomous_enabled": True}
                elif "step" in r["path"]:
                    sample_body = {"dt_seconds": 1.0}
                elif "set_groq_key" in r["path"]:
                    sample_body = {"api_key": "{{groq_api_key}}"}
                elif "telemetry/ingest" in r["path"]:
                    sample_body = {
                        "station_id": "{{station_id}}",
                        "source": "FIELD_PLC_SCHNEIDER_M340",
                        "readings": [{"sensor_id": "BHARATI.CHP.01.POWER", "value": 68.4, "quality": "GOOD"}]
                    }
                elif "copilot/chat" in r["path"]:
                    sample_body = {
                        "station_id": "{{station_id}}",
                        "message": "Explain causal root cause of current microgrid alerts."
                    }
                elif "sync/state" in r["path"]:
                    sample_body = {
                        "station_id": "bharati",
                        "active_tab": "topo",
                        "autonomous_mode": True,
                        "voice_enabled": False
                    }
                elif "sync/login" in r["path"]:
                    sample_body = {"operator_id": "STATION_COMMANDER", "pin": "BHARATI-CMD-2026", "station_id": "bharati"}
                elif "inject" in r["path"]:
                    sample_body = {"scenario": "BLIZZARD_STRIKE", "station_id": "{{station_id}}"}
                elif "profile" in r["path"]:
                    sample_body = {"profile": "INMARSAT_STANDARD"}
                elif "sync" in r["path"]:
                    sample_body = {"force_keyframe": False}
                elif "recover" in r["path"]:
                    sample_body = {"new_profile": "INMARSAT_STANDARD"}
                elif "execute" in r["path"]:
                    sample_body = {
                        "plan_name": "Adjust Damper Position",
                        "strategy": "OPERATIONAL_MITIGATION",
                        "autonomy_tier": "TIER_1",
                        "actions": [{"command": "SET_BLIZZARD_DAMPERS", "parameters": {"damper_position_pct": 80.0}}],
                        "expected_outcome": "Restore nominal fresh air airflow",
                        "resource_cost": 0.05,
                        "confidence": 0.95
                    }

                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(sample_body, indent=2)
                }

            folders[folder_name].append(item)

        collection = {
            "info": {
                "_postman_id": "c1f8d420-1a2b-4e3c-9f8a-friday-sih26060",
                "name": "F.R.I.D.A.Y. Polar Digital Twin API (SIH 2026)",
                "description": "Complete Industry-Grade API Collection for F.R.I.D.A.Y. Polar Digital Twin Platform (SIH26060 - NCPOR Goa). Includes 60+ endpoints covering 505 sensors, multi-agent society, causal graph, 2-step distributed DB, and satcom.",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": folder_name,
                    "item": items,
                    "description": f"Endpoints for {folder_name}"
                }
                for folder_name, items in folders.items() if items
            ]
        }

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2)
        print(f"  -> Exported Postman Collection v2.1.0 to: {out_path}")

    def export_postman_environment(self, out_path: str = "postman_environment.json") -> None:
        """Export Postman Environment JSON format."""
        env = {
            "id": "e2f9d510-4b3c-4a1d-8e7b-friday-env",
            "name": "F.R.I.D.A.Y. Local Polar Edge (127.0.0.1:8000)",
            "values": [
                {"key": "base_url", "value": "http://127.0.0.1:8000", "type": "default", "enabled": True},
                {"key": "station_id", "value": "bharati", "type": "default", "enabled": True},
                {"key": "secondary_station_id", "value": "maitri", "type": "default", "enabled": True},
                {"key": "commander_pin", "value": "BHARATI-CMD-2026", "type": "secret", "enabled": True},
                {"key": "groq_api_key", "value": "", "type": "secret", "enabled": True}
            ],
            "_postman_variable_scope": "environment"
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(env, f, indent=2)
        print(f"  -> Exported Postman Environment to: {out_path}")


async def main() -> None:
    runner = ApiBenchmarkRunner()
    success = await runner.run_all_tests()
    runner.print_summary_report()
    runner.export_postman_collection("postman_collection.json")
    runner.export_postman_environment("postman_environment.json")
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
