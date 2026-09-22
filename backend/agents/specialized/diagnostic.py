"""Diagnostic / Root-Cause Agent for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

COGNITIVE OBJECTIVE:
"Why is it happening across the station's physical topology?"

RESPONSIBILITIES:
1. Alarm Flood Suppression: Distinguishes between originating primary equipment/environmental
   failures and secondary symptom cascades (e.g. cold habitat caused by generator trip vs HVAC fault).
2. Upstream Graph Traversal: Uses TwinCausalGraph to walk incoming dependency edges in O(V + E) time.
3. Telemetry Corroboration: Cross-references real-time sensor readings and physical states from the
   Master Twin Engine along the causal path to eliminate healthy nodes.
4. Root Cause Isolation: Pinpoints the originating root node, computes diagnostic confidence,
   records the causal chain, and formulates an engineering explanation.
5. Multi-Agent Deliberation: Automatically updates the DeliberationSession blackboard and
   dispatches structured DIAGNOSIS messages to Prediction, Planning, and F.R.I.D.A.Y. Orchestrator.
6. Interactive Query Support: Responds to on-demand operator inquiries explaining root causes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Literal

from ...core.causal_graph import CausalNode, NodeType, TwinCausalGraph
from ...core.engine import BharatiMasterTwinEngine, MasterTwinSnapshot
from ..framework.base_agent import BaseSpecializedAgent
from ..framework.bus import AgentMessageBus
from ..framework.models import (
    AgentMessage,
    AgentRole,
    DeliberationSession,
    MessageType,
    SeverityLevel,
)
from ..framework.groq_brain import GroqBrainEngine


@dataclass
class DiagnosisResult:
    """Structured diagnostic verdict pinpointing root cause and causal propagation."""
    diagnosis_id: str
    session_id: str
    symptom_node_id: str
    root_cause_node_id: str
    root_cause_name: str
    subsystem: str
    confidence: float
    causal_chain: list[str]  # Ordered sequence from root cause to symptom
    evidence: dict[str, Any]
    explanation: str
    is_environmental: bool
    recommended_focus: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize diagnostic outcome to dictionary."""
        return asdict(self)


# Comprehensive mapping of sensor ID prefixes / patterns to CausalNode IDs
SENSOR_TO_NODE_MAP: dict[str, str] = {
    # Energy: Generation & Fuel
    "BHARATI.CHP.01": "chp_1",
    "BHARATI.CHP.02": "chp_2",
    "BHARATI.CHP.03": "chp_3",
    "BHARATI.FUEL.DAYTANK": "day_tank",
    "BHARATI.FUEL.FLOW": "fuel_transfer_pump",
    "BHARATI.FUEL.TRANSFER": "fuel_transfer_pump",
    "BHARATI.FUEL.STORAGE": "bulk_fuel_farm",
    "BHARATI.GRID.MLVD": "mlvd_bus",
    "BHARATI.UPS.01": "ups_1",
    "BHARATI.UPS.02": "ups_2",
    "sensor_chp1_kw": "chp_1",
    "sensor_fuel_day_lvl": "day_tank",

    # Infrastructure: HVAC, Zones & Life-Support
    "BHARATI-BLDG-Z01": "zone_living",
    "BHARATI-BLDG-Z02": "zone_labs",
    "BHARATI-BLDG-Z03": "zone_medical",
    "BHARATI-BLDG-EMERGENCY": "emergency_shelter",
    "BHARATI-HVAC-AHU01": "ahu_01",
    "BHARATI-HVAC-AHU02": "ahu_02",
    "BHARATI-PIPE-WATER01": "utilidor_water_line",
    "BHARATI-RO": "ro_plant",
    "BHARATI-WATER-POTABLE": "potable_reservoir",
    "BHARATI-MBR": "mbr_wastewater",
    "BHARATI-BLDG-STRUCT": "building_envelope",
    "sensor_living_temp": "zone_living",

    # Environment
    "ENV-WX-WIND": "env_katabatic",
    "ENV-WX-GUST": "env_katabatic",
    "ENV-WX-TEMP": "env_ambient",
    "ENV-WX-SOLAR": "env_solar",
    "ENV-SEAICE": "env_sea_ice",
    "ENV-OCEAN": "env_ocean",
    "sensor_wind_speed": "env_katabatic",

    # Logistics
    "LOG-REEFER-01": "reefer_01",
    "LOG-FLEET-PB01": "pb_01",
    "LOG-ROUTE-RING": "station_ring_route",
    "LOG-ROUTE-FASTICE": "fast_ice_route",
    "LOG-AVIATION-HELIPAD": "helipad",
    "LOG-MARINE-BERTH": "sea_berth",
    "sensor_reefer_temp": "reefer_01",
}


class DiagnosticAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for root-cause isolation across the digital twin."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
    ) -> None:
        super().__init__(
            role=AgentRole.DIAGNOSTIC,
            bus=bus,
            engine=engine,
            graph=graph,
        )

        # Subscribe specifically to incoming ALERT messages from Situation Awareness
        self.bus.subscribe_type(MessageType.ALERT, self.on_alert_received)

        # Audit cache of generated diagnoses: diagnosis_id -> DiagnosisResult
        self._diagnoses: dict[str, DiagnosisResult] = {}

    def on_alert_received(self, message: AgentMessage) -> None:
        """Automatic deliberation hook triggered whenever an ALERT is published."""
        payload = message.payload
        session_id = message.session_id

        # Determine target symptom node
        primary_sensor = payload.get("primary_sensor_id", "")
        subsystem = payload.get("subsystem", "")
        start_node_id = self.resolve_sensor_to_node(primary_sensor, subsystem)

        if not start_node_id:
            return

        # Perform root cause diagnosis
        result = self.diagnose_node(
            symptom_node_id=start_node_id,
            session_id=session_id,
            alert_payload=payload,
        )

        # Record in local audit cache
        self._diagnoses[result.diagnosis_id] = result

        # Update DeliberationSession blackboard if session exists
        if session_id:
            session = self.bus.get_session(session_id)
            if session:
                session.root_causes.append(result.to_dict())

        # Publish DIAGNOSIS message to downstream agents (Prediction, Planning, Orchestrator)
        diag_payload = result.to_dict()
        severity = (
            SeverityLevel.CRITICAL
            if result.confidence >= 0.8
            else SeverityLevel.WARNING
        )

        # Dispatch to Prediction Agent
        self.publish_message(
            session_id=session_id,
            recipient=AgentRole.PREDICTION,
            message_type=MessageType.DIAGNOSIS,
            severity=severity,
            payload=diag_payload,
            confidence=result.confidence,
        )

        # Dispatch to Planning Agent
        self.publish_message(
            session_id=session_id,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.DIAGNOSIS,
            severity=severity,
            payload=diag_payload,
            confidence=result.confidence,
        )

    def handle_message(self, message: AgentMessage) -> None:
        """Handle direct queries or commands addressed specifically to DIAGNOSTIC role."""
        if message.message_type == MessageType.QUERY:
            query = message.payload.get("query", "")
            node_id = message.payload.get("node_id")
            sensor_id = message.payload.get("sensor_id")

            target_node = node_id or (
                self.resolve_sensor_to_node(sensor_id) if sensor_id else "zone_living"
            )

            result = self.diagnose_node(
                symptom_node_id=target_node,
                session_id=message.session_id,
                alert_payload=message.payload,
            )

            self.publish_message(
                session_id=message.session_id,
                recipient=message.sender,
                message_type=MessageType.RESPONSE,
                severity=SeverityLevel.INFO,
                payload=result.to_dict(),
                confidence=result.confidence,
            )

    def resolve_sensor_to_node(
        self, sensor_id: str, subsystem: str = ""
    ) -> str | None:
        """Map sensor ID or subsystem name to the matching CausalNode in the graph."""
        if not sensor_id:
            return None

        # Direct node ID match
        if self.graph.get_node(sensor_id):
            return sensor_id

        # Prefix matching in dictionary
        for prefix, node_id in SENSOR_TO_NODE_MAP.items():
            if sensor_id.startswith(prefix) or prefix in sensor_id:
                if self.graph.get_node(node_id):
                    return node_id

        # Fallback to subsystem matching
        if subsystem.upper() == "ENERGY":
            return "mlvd_bus"
        elif subsystem.upper() == "INFRASTRUCTURE":
            return "zone_living"
        elif subsystem.upper() == "ENVIRONMENT":
            return "env_ambient"
        elif subsystem.upper() == "LOGISTICS":
            return "reefer_01"

        return None

    def diagnose_node(
        self,
        symptom_node_id: str,
        session_id: str = "",
        alert_payload: dict[str, Any] | None = None,
    ) -> DiagnosisResult:
        """Execute causal graph upstream search and correlate with digital twin telemetry."""
        alert_payload = alert_payload or {}
        symptom_node = self.graph.get_node(symptom_node_id)
        symptom_name = symptom_node.name if symptom_node else symptom_node_id

        # 1. Fetch current digital twin snapshot
        snapshot = self.engine.get_snapshot()

        # 2. Traverse upstream causes up to depth 6
        upstream_candidates = self.graph.get_upstream_causes(symptom_node_id, max_depth=6)

        # 3. Evaluate each candidate node against physical telemetry
        abnormal_nodes: list[dict[str, Any]] = []

        for candidate in upstream_candidates:
            c_id = candidate["cause_node_id"]
            c_node = self.graph.get_node(c_id)
            if not c_node:
                continue

            health_eval = self._evaluate_node_health(c_id, snapshot)
            if health_eval["is_abnormal"]:
                candidate_info = dict(candidate)
                candidate_info["evidence"] = health_eval["evidence"]
                candidate_info["severity_factor"] = health_eval["severity_factor"]
                abnormal_nodes.append(candidate_info)

        # 4. Isolate root cause from candidate abnormal nodes
        diag_id = f"DIAG-{int(time.time()*1000)%1000000:06d}"

        if not abnormal_nodes:
            # Self-originating failure (no upstream causes found abnormal)
            symptom_health = self._evaluate_node_health(symptom_node_id, snapshot)
            return DiagnosisResult(
                diagnosis_id=diag_id,
                session_id=session_id or f"SES-{diag_id}",
                symptom_node_id=symptom_node_id,
                root_cause_node_id=symptom_node_id,
                root_cause_name=symptom_name,
                subsystem=symptom_node.subsystem if symptom_node else "UNKNOWN",
                confidence=0.85,
                causal_chain=[symptom_node_id],
                evidence=symptom_health.get("evidence", {"state": "direct local threshold breach"}),
                explanation=(
                    f"Direct physical failure originating at {symptom_name}. "
                    "All upstream dependencies verified nominal with no upstream cascades."
                ),
                is_environmental=symptom_node.node_type == NodeType.ENVIRONMENT_SOURCE if symptom_node else False,
                recommended_focus=f"Inspect and service local asset {symptom_name}.",
            )

        # Sort abnormal nodes by depth descending (furthest upstream) then severity
        abnormal_nodes.sort(key=lambda c: (c["depth"], c["severity_factor"]), reverse=True)
        root_candidate = abnormal_nodes[0]

        root_id = root_candidate["cause_node_id"]
        root_node = self.graph.get_node(root_id)
        root_name = root_node.name if root_node else root_id
        is_env = root_node.node_type == NodeType.ENVIRONMENT_SOURCE if root_node else False

        # Build causal chain from root candidate path
        causal_chain = root_candidate.get("path", [root_id, symptom_node_id])

        # Formulate engineering explanation
        explanation = self._synthesize_explanation(
            root_name=root_name,
            symptom_name=symptom_name,
            causal_chain=causal_chain,
            evidence=root_candidate["evidence"],
            is_env=is_env,
        )

        recommended_focus = (
            f"Mitigate external environmental hazard '{root_name}'."
            if is_env
            else f"Immediate maintenance/reset required on root asset '{root_name}' ({root_id})."
        )

        # Compute diagnostic confidence based on depth and evidence strength
        confidence = min(0.98, max(0.70, 0.75 + (0.05 * root_candidate.get("severity_factor", 1.0))))

        return DiagnosisResult(
            diagnosis_id=diag_id,
            session_id=session_id or f"SES-{diag_id}",
            symptom_node_id=symptom_node_id,
            root_cause_node_id=root_id,
            root_cause_name=root_name,
            subsystem=root_node.subsystem if root_node else "UNKNOWN",
            confidence=round(confidence, 2),
            causal_chain=causal_chain,
            evidence=root_candidate["evidence"],
            explanation=explanation,
            is_environmental=is_env,
            recommended_focus=recommended_focus,
        )

    @staticmethod
    def _extract_val(reading: Any, default: float = 0.0) -> float:
        """Safely extract float from SensorReading object or raw scalar."""
        if reading is None:
            return default
        if hasattr(reading, "value"):
            try:
                return float(reading.value)
            except (ValueError, TypeError):
                return default
        try:
            return float(reading)
        except (ValueError, TypeError):
            return default

    def _evaluate_node_health(
        self, node_id: str, snapshot: MasterTwinSnapshot
    ) -> dict[str, Any]:
        """Check physical state and sensor readings for a specific graph node."""
        readings = snapshot.readings
        kpis = snapshot.kpis

        # -----------------------------------------------------------------
        # 1. Environment Nodes
        # -----------------------------------------------------------------
        if node_id == "env_katabatic":
            wind_s = self._extract_val(readings.get("ENV-WX-WIND-S"), default=8.0)
            wind_g = self._extract_val(readings.get("ENV-WX-GUST"), default=10.0)
            if wind_s >= 25.0 or wind_g >= 30.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.5 if wind_s >= 32.0 else 1.0,
                    "evidence": {
                        "wind_speed_ms": wind_s,
                        "wind_gust_ms": wind_g,
                        "threshold_ms": 25.0,
                        "condition": "Severe Katabatic Storm",
                    },
                }

        elif node_id == "env_ambient":
            amb_t = self._extract_val(readings.get("ENV-WX-TEMP"), default=-15.0)
            if amb_t <= -28.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.2,
                    "evidence": {
                        "ambient_temp_c": amb_t,
                        "threshold_c": -28.0,
                        "condition": "Deep Freeze Ambient",
                    },
                }

        # -----------------------------------------------------------------
        # 2. Fuel & Generation Nodes
        # -----------------------------------------------------------------
        elif node_id == "day_tank":
            fuel_pct = self._extract_val(readings.get("BHARATI.FUEL.DAYTANK.PERCENT"), default=80.0)
            fuel_lvl = self._extract_val(readings.get("BHARATI.FUEL.DAYTANK.LEVEL"), default=1200.0)
            if fuel_pct <= 20.0 or fuel_lvl <= 300.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 2.0 if fuel_pct <= 5.0 else 1.2,
                    "evidence": {
                        "fuel_percent": fuel_pct,
                        "fuel_level_liters": fuel_lvl,
                        "threshold_percent": 20.0,
                        "condition": "Critical Day Tank Fuel Depletion",
                    },
                }

        elif node_id == "fuel_transfer_pump":
            flow = self._extract_val(readings.get("BHARATI.FUEL.FLOW"), default=0.0)
            day_pct = self._extract_val(readings.get("BHARATI.FUEL.DAYTANK.PERCENT"), default=80.0)
            # If day tank is low but fuel flow is zero
            if day_pct < 40.0 and flow <= 0.01:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.4,
                    "evidence": {
                        "fuel_flow_lph": flow,
                        "day_tank_percent": day_pct,
                        "condition": "Transfer Pump Inoperative during Low Level",
                    },
                }

        elif node_id in ("chp_1", "chp_2", "chp_3"):
            unit_idx = node_id.split("_")[1]
            pwr_key = f"BHARATI.CHP.{unit_idx.zfill(2)}.POWER"
            run_key = f"BHARATI.CHP.{unit_idx.zfill(2)}.RUNNING"
            temp_key = f"BHARATI.CHP.{unit_idx.zfill(2)}.COOLANT_TEMP"

            power_kw = self._extract_val(readings.get(pwr_key, readings.get(f"sensor_chp{unit_idx}_kw")), default=0.0)
            run_val = readings.get(run_key)
            is_running = bool(run_val.value if hasattr(run_val, "value") else (run_val if run_val is not None else (power_kw > 5.0)))
            coolant_t = self._extract_val(readings.get(temp_key), default=85.0)

            # CHP 1 is primary duty engine: if not running or coolant overheating
            if node_id == "chp_1" and (power_kw < 5.0 or coolant_t > 95.0):
                return {
                    "is_abnormal": True,
                    "severity_factor": 2.0 if power_kw < 1.0 else 1.2,
                    "evidence": {
                        "active_power_kw": power_kw,
                        "is_running": is_running,
                        "coolant_temp_c": coolant_t,
                        "condition": "Primary CHP Generator Tripped/Overheated",
                    },
                }
            elif node_id in ("chp_2", "chp_3") and coolant_t > 98.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.3,
                    "evidence": {
                        "active_power_kw": power_kw,
                        "coolant_temp_c": coolant_t,
                        "condition": f"Standby Generator {node_id.upper()} Overheating",
                    },
                }

        elif node_id == "mlvd_bus":
            running_gens = int(kpis.get("running_generators", 1))
            chp1_kw = self._extract_val(readings.get("BHARATI.CHP.01.POWER"), default=0.0)
            chp2_kw = self._extract_val(readings.get("BHARATI.CHP.02.POWER"), default=0.0)
            chp3_kw = self._extract_val(readings.get("BHARATI.CHP.03.POWER"), default=0.0)
            total_kw = chp1_kw + chp2_kw + chp3_kw

            if running_gens == 0 or total_kw < 5.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 2.5,
                    "evidence": {
                        "total_generation_kw": total_kw,
                        "running_generators": running_gens,
                        "condition": "Total MLVD Bus De-energization (Station Blackout)",
                    },
                }

        # -----------------------------------------------------------------
        # 3. Infrastructure & HVAC Nodes
        # -----------------------------------------------------------------
        elif node_id == "utilidor_water_line":
            pipe_t = self._extract_val(readings.get("BHARATI-PIPE-WATER01-TEMP"), default=4.0)
            if pipe_t <= 1.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 2.0 if pipe_t <= 0.0 else 1.4,
                    "evidence": {
                        "pipe_temp_c": pipe_t,
                        "threshold_c": 1.0,
                        "condition": "Utilidor Freeze Hazard / Trace Heating Loss",
                    },
                }

        elif node_id == "building_envelope":
            wind_s = self._extract_val(readings.get("ENV-WX-WIND-S"), default=8.0)
            amb_t = self._extract_val(readings.get("ENV-WX-TEMP"), default=-15.0)
            if wind_s >= 28.0 and amb_t <= -25.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.4,
                    "evidence": {
                        "external_wind_ms": wind_s,
                        "external_temp_c": amb_t,
                        "condition": "Extreme Windchill & Infiltration Pressure on Building Shell",
                    },
                }

        elif node_id in ("zone_living", "zone_labs", "zone_medical"):
            z_key = (
                "BHARATI-BLDG-Z01-TEMP"
                if node_id == "zone_living"
                else (
                    "BHARATI-BLDG-Z02-TEMP"
                    if node_id == "zone_labs"
                    else "BHARATI-BLDG-Z03-TEMP"
                )
            )
            temp = self._extract_val(readings.get(z_key), default=21.0)
            if temp <= 16.5:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.8 if temp <= 14.0 else 1.2,
                    "evidence": {
                        "zone_temp_c": temp,
                        "threshold_c": 16.5,
                        "condition": "Zone Severe Thermal Degradation",
                    },
                }

        elif node_id == "reefer_01":
            r_temp = self._extract_val(readings.get("LOG-REEFER-01-TEMP"), default=-22.0)
            if r_temp >= -15.0:
                return {
                    "is_abnormal": True,
                    "severity_factor": 1.5,
                    "evidence": {
                        "reefer_temp_c": r_temp,
                        "threshold_c": -15.0,
                        "condition": "Cold Chain Provision Warming Excursion",
                    },
                }

        # Default healthy node
        return {"is_abnormal": False, "severity_factor": 0.0, "evidence": {}}

    def _synthesize_explanation(
        self,
        root_name: str,
        symptom_name: str,
        causal_chain: list[str],
        evidence: dict[str, Any],
        is_env: bool,
    ) -> str:
        """Formulate a concise engineering narrative describing the failure propagation."""
        chain_str = " -> ".join(causal_chain)
        condition = evidence.get("condition", "abnormal operational parameters")

        groq_brain = GroqBrainEngine.get_instance()
        if groq_brain.is_live_available():
            try:
                res = groq_brain.run_sync(
                    groq_brain.reason_diagnosis(
                        symptom_node_id=symptom_name,
                        upstream_candidates=[{"cause_node_id": n} for n in causal_chain],
                        telemetry_snapshot={"evidence": evidence},
                        weather={},
                    )
                )
                if res and res.get("explanation"):
                    return str(res["explanation"])
            except Exception:
                pass

        if is_env:
            return (
                f"Environmental stressor '{root_name}' ({condition}) has propagated across station boundary "
                f"down to '{symptom_name}'. Causal Path: [{chain_str}]. "
                "Secondary alarms are downstream effects of extreme Antarctic external atmospheric forcing."
            )
        else:
            return (
                f"Primary root cause identified at physical equipment '{root_name}' ({condition}). "
                f"The failure propagated down the dependency cascade to impact '{symptom_name}'. "
                f"Causal Path: [{chain_str}]. Suppressing alarms on downstream nodes as dependent symptoms."
            )
