"""Server State Management for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Manages dual-station digital twins (Bharati & Maitri), causal graph, message bus,
safety interlock manager, and the 10 specialized cognitive agents.
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import json
import logging
import time
from typing import Any
import uuid

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.models import AgentMessage, AutonomyTier, MessageType, ProposalStatus
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.agents.orchestrator.friday_core import FridayMasterOrchestrator
from backend.agents.specialized.diagnostic import DiagnosticAgent
from backend.agents.specialized.maintenance import MaintenanceAgent
from backend.agents.specialized.mission_ops import MissionOpsAgent
from backend.agents.specialized.planning import PlanningAgent
from backend.agents.specialized.prediction import PredictionAgent
from backend.agents.specialized.resource_optimizer import ResourceOptimizerAgent
from backend.agents.specialized.risk_impact import RiskImpactAgent
from backend.agents.specialized.situation_awareness import SituationAwarenessAgent
from backend.agents.specialized.what_if import WhatIfSimulationAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import (
    BharatiMasterTwinEngine,
    MaitriMasterTwinEngine,
    MasterScenario,
    MasterTwinSnapshot,
)
from backend.database import (
    DatabaseManager,
    get_database_manager,
    CopilotChatRecord,
    DialogueRecord,
    EpisodeRecord,
    EquipmentLifecycleRecord,
    OperatorAuditRecord,
    StationStateSyncRecord,
    TelemetryTimeSeriesRecord,
    MemoryRecord,
    MemoryRetrievalEvent,
    MemoryType,
    SyncStatus,
)
from backend.database.repositories import (
    AuditRepository,
    CopilotRepository,
    DialogueRepository,
    EpisodesRepository,
    EquipmentRepository,
    MemoryRepository,
    StateSyncRepository,
    TelemetryRepository,
)
from backend.database.sync_worker import SatcomDatabaseSyncWorker

logger = logging.getLogger("friday.server.state")


class ServerState:
    """Central state container for the F.R.I.D.A.Y. backend service."""

    def __init__(self, seed: int = 42) -> None:
        logger.info("Initializing F.R.I.D.A.Y. Dual-Station Digital Twin & Agent Society...")

        # 1. Dual-Station Digital Twin Engines
        self.bharati_engine = BharatiMasterTwinEngine(seed=seed)
        self.maitri_engine = MaitriMasterTwinEngine(seed=seed + 59)
        self.stations: dict[str, BharatiMasterTwinEngine] = {
            "bharati": self.bharati_engine,
            "maitri": self.maitri_engine,
        }
        self.active_station_id: str = "bharati"

        # 2. Causal Dependency Graph
        self.graph = TwinCausalGraph()

        # 3. Message Bus & Safety Interlock Manager
        self.bus = AgentMessageBus()
        self.safety_interlock = SafetyInterlockManager()

        # 3b. 2-Step Distributed Database & Memory Subsystem
        self.db_manager = get_database_manager()
        self.episodes_repo = EpisodesRepository(self.db_manager)
        self.dialogue_repo = DialogueRepository(self.db_manager)
        self.equipment_repo = EquipmentRepository(self.db_manager)
        self.telemetry_repo = TelemetryRepository(self.db_manager)
        self.audit_repo = AuditRepository(self.db_manager)
        self.copilot_repo = CopilotRepository(self.db_manager)
        self.state_sync_repo = StateSyncRepository(self.db_manager)
        self.memory_repo = MemoryRepository(self.db_manager)
        self._current_episode_id: str | None = None
        self._current_episode_sim_start: float = 0.0

        # 4. Cognitive Agent Society (All 10 Agents)
        self.situation_awareness = SituationAwarenessAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
        )
        self.diagnostic = DiagnosticAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
        )
        self.prediction = PredictionAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
        )
        self.risk_impact = RiskImpactAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
        )
        self.planning = PlanningAgent(
            bus=self.bus,
            engine=self.bharati_engine,
            graph=self.graph,
            safety_interlock=self.safety_interlock,
            episodes_repo=self.episodes_repo,
            memory_repo=self.memory_repo,
        )
        self.what_if = WhatIfSimulationAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
        )
        self.mission_ops = MissionOpsAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph, safety_interlock=self.safety_interlock
        )
        self.maintenance = MaintenanceAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph, safety_interlock=self.safety_interlock
        )
        self.resource_optimizer = ResourceOptimizerAgent(
            bus=self.bus, engine=self.bharati_engine, graph=self.graph, safety_interlock=self.safety_interlock
        )
        self.orchestrator = FridayMasterOrchestrator(
            bus=self.bus,
            engine=self.bharati_engine,
            graph=self.graph,
            safety_interlock=self.safety_interlock,
        )

        # 5. Sliding historical buffer for time-series / charting (up to 120 points)
        self.history: dict[str, deque[dict[str, Any]]] = {
            "bharati": deque(maxlen=120),
            "maitri": deque(maxlen=120),
        }

        # Record initial historical snapshot for both stations
        for sid, eng in self.stations.items():
            snap = eng.get_snapshot()
            self._record_history(sid, snap)

        # 6. Polar Satcom Bandwidth-Aware Synchronization (Sub-Phase 4.2)
        from backend.satcom import (
            DeltaEncoder,
            MirrorTwinEngine,
            PolarSatcomChannelEmulator,
            SatcomChannelProfile,
        )

        self.satcom_encoders: dict[str, DeltaEncoder] = {
            "bharati": DeltaEncoder(),
            "maitri": DeltaEncoder(),
        }
        self.satcom_emulators: dict[str, PolarSatcomChannelEmulator] = {
            "bharati": PolarSatcomChannelEmulator(
                profile=SatcomChannelProfile.INMARSAT_STANDARD,
                deterministic=True,
            ),
            "maitri": PolarSatcomChannelEmulator(
                profile=SatcomChannelProfile.INMARSAT_STANDARD,
                deterministic=True,
            ),
        }
        self.mainland_mirrors: dict[str, MirrorTwinEngine] = {
            "bharati": MirrorTwinEngine("bharati"),
            "maitri": MirrorTwinEngine("maitri"),
        }

        # Initialize mainland mirror baseline keyframes
        for sid in self.stations.keys():
            self.sync_station_telemetry(sid, force_keyframe=True)

        # 6b. Bandwidth-Aware Satcom Store-and-Forward Database Sync Worker
        self.db_sync_worker = SatcomDatabaseSyncWorker(
            self.db_manager,
            is_link_connected_fn=lambda: not self.orchestrator.edge_blackout_mode,
        )

        # 6c. Modular Domain Services
        from .services.station_service import StationService
        from .services.satcom_service import SatcomService
        from .services.actuator_service import ActuatorService

        self.station_service = StationService(self)
        self.satcom_service = SatcomService(self)
        self.actuator_service = ActuatorService(self)

        # Server start timestamp
        self.server_start_time = time.time()

        # 7. Edge Autonomous Station Governor & Continuous Execution State
        self.autonomous_mode_enabled: bool = True
        self.is_continuous_loop_running: bool = False
        self.continuous_speed: float = 1.0
        self.autonomous_action_history: deque[dict[str, Any]] = deque(maxlen=200)
        self.cognitive_logs: deque[dict[str, Any]] = deque(maxlen=300)
        self._bg_task: asyncio.Task | None = None

        # Subscribe state to bus to capture all multi-agent cognitive events
        self.bus.subscribe_type(MessageType.ALERT, self._on_bus_alert)
        self.bus.subscribe_type(MessageType.DIAGNOSIS, self._on_bus_diagnosis)
        self.bus.subscribe_type(MessageType.PREDICTION_PROJECTION, self._on_bus_prediction)
        self.bus.subscribe_type(MessageType.PROPOSAL, self._on_bus_proposal)
        self.bus.subscribe_type(MessageType.SIM_RESULT, self._on_bus_sim_result)
        self.bus.subscribe_type(MessageType.CONSENSUS_PLAN, self._on_bus_consensus)
        self.bus.subscribe_broadcast(self._on_any_bus_message)

        # 8. Agent Society Runtime States & Deliberation Pipeline Tracker
        self.agent_runtime_states: dict[str, dict[str, Any]] = {
            "SITUATION_AWARENESS": {
                "role": "SITUATION_AWARENESS",
                "name": "Situation Awareness",
                "tag": "1. PERCEPTION",
                "icon": "👁️",
                "state": "SCANNING",
                "color": "#00f0ff",
                "objective": "Continuous scan of 505 physical sensors across Energy, Infra, Environment & Logistics.",
                "hypothesis": "All 505 telemetry points within nominal operational envelope.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "DIAGNOSTIC": {
                "role": "DIAGNOSTIC",
                "name": "Diagnostic Agent",
                "tag": "2. DIAGNOSTIC",
                "icon": "🔍",
                "state": "STANDBY",
                "color": "#a855f7",
                "objective": "Bayesian causal DAG traversal to isolate true root-cause equipment failures from cascade alarms.",
                "hypothesis": "Topological dependency paths nominal. No upstream faults.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "PREDICTION": {
                "role": "PREDICTION",
                "name": "Prediction Agent",
                "tag": "3. PREDICTION",
                "icon": "⏳",
                "state": "STANDBY",
                "color": "#f59e0b",
                "objective": "Physics lookahead extrapolation to compute Time-To-Failure (TTF) and thermal decay horizons.",
                "hypothesis": "Forward trajectory steady-state. System equilibrium stable.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "RISK_IMPACT": {
                "role": "RISK_IMPACT",
                "name": "Risk & Impact",
                "tag": "4. RISK IMPACT",
                "icon": "🛡️",
                "state": "STANDBY",
                "color": "#ef4444",
                "objective": "Blast radius quantification and criticality scoring across life-support and mission assets.",
                "hypothesis": "Station composite threat index nominal.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "PLANNING": {
                "role": "PLANNING",
                "name": "Planning Agent",
                "tag": "5. PLANNING",
                "icon": "📝",
                "state": "STANDBY",
                "color": "#38bdf8",
                "objective": "Formulates tiered mitigation plans balancing power dispatch, thermal stability, and life-safety.",
                "hypothesis": "Nominal dispatch schedule active. Standby assets pre-conditioned.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "WHAT_IF": {
                "role": "WHAT_IF",
                "name": "What-If Simulator",
                "tag": "6. WHAT-IF SIM",
                "icon": "🧪",
                "state": "STANDBY",
                "color": "#10b981",
                "objective": "Runs sandbox digital twin projections to mathematically verify proposal safety before physical execution.",
                "hypothesis": "Digital twin shadow sandbox synchronized with live physical state.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "MISSION_OPS": {
                "role": "MISSION_OPS",
                "name": "Mission Operations",
                "tag": "7. MISSION OPS",
                "icon": "🎯",
                "state": "STANDBY",
                "color": "#06b6d4",
                "objective": "Protects scientific payload continuity, clean lab power, and experimental sample integrity.",
                "hypothesis": "Atmospheric & seismic scientific experiments prioritized.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "MAINTENANCE": {
                "role": "MAINTENANCE",
                "name": "Maintenance Agent",
                "tag": "8. MAINTENANCE",
                "icon": "🔧",
                "state": "STANDBY",
                "color": "#eab308",
                "objective": "Monitors equipment running hours, spares inventory, filter dp, and lifecycle wear.",
                "hypothesis": "CHP runtime balanced. No maintenance interlocks active.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "RESOURCE_OPTIMIZER": {
                "role": "RESOURCE_OPTIMIZER",
                "name": "Resource Optimizer",
                "tag": "9. OPTIMIZER",
                "icon": "⚡",
                "state": "STANDBY",
                "color": "#c084fc",
                "objective": "Optimizes fuel consumption, heat recovery efficiency, and water desalination scheduling.",
                "hypothesis": "Cogeneration efficiency: 84.2%. Specific fuel: 0.28 L/kWh.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
            "FRIDAY_ORCHESTRATOR": {
                "role": "FRIDAY_ORCHESTRATOR",
                "name": "F.R.I.D.A.Y. Master Mind",
                "tag": "10. ORCHESTRATOR",
                "icon": "🧠",
                "state": "MONITORING",
                "color": "#00f0ff",
                "objective": "Multi-agent consensus arbitration, edge governance authority, and autonomous physical command execution.",
                "hypothesis": "Station governed under 100% autonomous edge stability invariant.",
                "confidence": 1.0,
                "messages_sent": 0,
                "messages_received": 0,
                "last_active_time": time.time(),
            },
        }

        self.active_deliberation_phase: dict[str, Any] = {
            "phase": 1,
            "phase_name": "PERCEPTION",
            "status": "NOMINAL",
            "session_id": None,
            "headline": "Station telemetry nominal across all 4 observation pillars.",
            "updated_at": time.time(),
        }

        # Initial cognitive startup log
        self.log_cognitive_event(
            category="EDGE_AUTHORITY",
            title="F.R.I.D.A.Y. Chief AI Polar Governor Online",
            details="Local AI governor online for Bharati and Maitri. Enforcing life-support guardrails and 100% local command authority during satcom blackout.",
            severity="INFO",
            station_id="bharati",
        )
        logger.info("F.R.I.D.A.Y. Dual-Station State, Agents & Satcom Sync Engines Online.")

    async def initialize_database(self) -> None:
        """Asynchronously probe databases, seed historical precedents and asset records, and start sync worker."""
        try:
            await self.db_manager.probe_connections()
            await self.episodes_repo.initialize_precedents()
            await self.memory_repo.initialize_baseline_memories()
            await self.equipment_repo.initialize_station_assets("bharati")
            await self.equipment_repo.initialize_station_assets("maitri")
            self.db_sync_worker.start()
            logger.info("F.R.I.D.A.Y. 2-Step Database & Memory Subsystem Initialized.")
        except Exception as e:
            logger.error("Error initializing database subsystem: %s", e)

    def get_engine(self, station_id: str | None = None) -> BharatiMasterTwinEngine:
        """Retrieve engine for the specified or active station."""
        sid = (station_id or self.active_station_id).lower()
        if sid not in self.stations:
            raise KeyError(f"Unknown station ID '{sid}'. Available stations: {list(self.stations.keys())}")
        return self.stations[sid]

    def set_active_station(self, station_id: str) -> None:
        """Switch the primary active station context."""
        sid = station_id.lower()
        if sid not in self.stations:
            raise KeyError(f"Unknown station ID '{sid}'. Available stations: {list(self.stations.keys())}")
        self.active_station_id = sid
        target_engine = self.stations[sid]
        # Re-link agents to current station engine
        self.situation_awareness.engine = target_engine
        self.diagnostic.engine = target_engine
        self.prediction.engine = target_engine
        self.risk_impact.engine = target_engine
        self.planning.engine = target_engine
        self.what_if.engine = target_engine
        self.mission_ops.engine = target_engine
        self.maintenance.engine = target_engine
        self.resource_optimizer.engine = target_engine
        self.orchestrator.engine = target_engine

    def step(self, station_id: str | None = None, dt_seconds: float = 1.0) -> MasterTwinSnapshot:
        """Advance simulation clock for the specified or active station."""
        engine = self.get_engine(station_id)
        snapshot = engine.step(dt_seconds)
        sid = engine.station_id

        # Record history
        self._record_history(sid, snapshot)

        # Synchronize telemetry delta to mainland mirror twin via satcom link
        self.sync_station_telemetry(sid, force_keyframe=False)

        # Trigger situation awareness on active station
        if sid == self.active_station_id:
            self.situation_awareness.on_tick(snapshot)

        # Broadcast update to connected WebSocket clients if asyncio loop is running
        try:
            import asyncio
            from .ws_manager import get_ws_manager
            loop = asyncio.get_running_loop()
            if loop.is_running():
                ws_manager = get_ws_manager()
                loop.create_task(ws_manager.broadcast_station_step(sid, snapshot, self))

                # Update equipment running hours in database
                if dt_seconds > 0:
                    chp1_active = snapshot.kpis.get("running_chp_count", 1) >= 1
                    chp2_active = snapshot.kpis.get("running_chp_count", 1) >= 2
                    loop.create_task(self.equipment_repo.accumulate_runtime("chp_1", sid, dt_seconds, is_running=chp1_active))
                    loop.create_task(self.equipment_repo.accumulate_runtime("chp_2", sid, dt_seconds, is_running=chp2_active))
                    loop.create_task(self.equipment_repo.accumulate_runtime("ahu_01", sid, dt_seconds, is_running=True))
                    loop.create_task(self.equipment_repo.accumulate_runtime("utilidor_water_line", sid, dt_seconds, is_running=True))
        except (RuntimeError, ImportError):
            pass

        return snapshot

    def sync_station_telemetry(
        self, station_id: str, force_keyframe: bool = False
    ) -> tuple[Any, dict[str, Any]]:
        """Encode, transmit over satcom link, and mirror station telemetry at mainland HQ."""
        sid = station_id.lower()
        engine = self.get_engine(sid)
        encoder = self.satcom_encoders[sid]
        emulator = self.satcom_emulators[sid]
        mirror = self.mainland_mirrors[sid]

        readings = engine.get_all_readings()
        kpis = engine.get_station_kpis()
        alerts = engine.get_active_alerts()
        sim_time = engine.clock.elapsed_seconds
        ts_iso = engine.clock.isoformat()

        if force_keyframe:
            frame = encoder.encode_keyframe(
                station_id=sid,
                readings=readings,
                sim_time_seconds=sim_time,
                timestamp_iso=ts_iso,
                kpis=kpis,
                alerts=alerts,
            )
        else:
            frame = encoder.encode_delta(
                station_id=sid,
                readings=readings,
                sim_time_seconds=sim_time,
                timestamp_iso=ts_iso,
                kpis=kpis,
                alerts=alerts,
            )

        success, status, delay, s_bytes = emulator.transmit(frame)
        if success:
            mirror.apply_frame(frame)

        tx_stats = {
            "success": success,
            "status": status,
            "delay_seconds": delay,
            "packet_bytes": len(s_bytes),
            "frame_type": frame.frame_type.value,
            "seq_num": frame.seq_num,
            "delta_count": frame.delta_count,
        }
        return frame, tx_stats

    def set_satcom_profile(self, profile: str, station_id: str | None = None) -> None:
        """Update satcom channel profile for specified or all stations."""
        targets = [station_id.lower()] if station_id else list(self.satcom_emulators.keys())
        p_upper = profile.upper()
        for sid in targets:
            if sid in self.satcom_emulators:
                prev_profile = self.satcom_emulators[sid].profile.name
                self.satcom_emulators[sid].set_profile(profile)
                is_blackout = (p_upper == "POLAR_BLACKOUT")
                self.orchestrator.edge_blackout_mode = is_blackout

                if is_blackout and prev_profile != "POLAR_BLACKOUT":
                    self.log_cognitive_event(
                        category="EDGE_AUTHORITY",
                        title="MAINLAND SATCOM SEVERED (POLAR BLACKOUT: 0 kbps)",
                        details="[EDGE AUTONOMY] Station completely severed from Mainland HQ. F.R.I.D.A.Y. assumed 100% full autonomous command authority. Telemetry deltas spooled locally.",
                        severity="EMERGENCY",
                        station_id=sid,
                    )
                elif not is_blackout and prev_profile == "POLAR_BLACKOUT":
                    self.log_cognitive_event(
                        category="EDGE_AUTHORITY",
                        title=f"MAINLAND SATCOM RESTORED ({p_upper})",
                        details=f"[HQ SYNC] Satellite communications re-established ({p_upper}). Ready to re-synchronize spooled telemetry queue with Mainland Mirror Twin.",
                        severity="INFO",
                        station_id=sid,
                    )

    def recover_satcom_blackout(
        self, station_id: str, new_profile: str = "INMARSAT_STANDARD"
    ) -> list[dict[str, Any]]:
        """Drain spooled blackout queue and apply frames to mainland mirror twin in priority order."""
        sid = station_id.lower()
        emulator = self.satcom_emulators[sid]
        mirror = self.mainland_mirrors[sid]
        self.orchestrator.edge_blackout_mode = False

        drained = emulator.recover_from_blackout(new_profile=new_profile)
        applied_summaries = []
        for frame, _, delay in drained:
            accepted, status_code = mirror.apply_frame(frame)
            applied_summaries.append({
                "frame_id": frame.frame_id,
                "frame_type": frame.frame_type.value,
                "seq_num": frame.seq_num,
                "priority": frame.priority,
                "accepted": accepted,
                "mirror_status": status_code,
                "tx_delay": delay,
            })

        self.log_cognitive_event(
            category="EDGE_AUTHORITY",
            title=f"Mainland Mirror Synchronized: {len(applied_summaries)} Packets Replayed",
            details=f"[HQ SYNC] Successfully replayed {len(applied_summaries)} spooled delta frames to Mainland Mirror Twin in priority sequence. Digital twin in full parity.",
            severity="INFO",
            station_id=sid,
        )
        return applied_summaries

    def get_satcom_summary(self, station_id: str) -> dict[str, Any]:
        """Aggregate satcom telemetry, channel metrics, and mainland mirror sync status."""
        sid = station_id.lower()
        emulator = self.satcom_emulators[sid]
        mirror = self.mainland_mirrors[sid]
        return {
            "station_id": sid,
            "channel_metrics": emulator.get_channel_metrics(),
            "mirror_twin": mirror.get_metrics(),
            "is_synchronized": mirror.is_synchronized(),
        }

    def inject_scenario(
        self, scenario: MasterScenario | str, station_id: str | None = None, **params: Any
    ) -> MasterTwinSnapshot:
        """Inject an operational or environmental crisis scenario into a station."""
        engine = self.get_engine(station_id)
        engine.inject_scenario(scenario, **params)
        # Advance 1 step to propagate physics
        snapshot = engine.step(dt_seconds=1.0)
        sid = engine.station_id
        self._record_history(sid, snapshot)

        sc_name = scenario.value if hasattr(scenario, "value") else str(scenario)
        self.log_cognitive_event(
            category="PERCEPTION",
            title=f"Crisis Injected: {sc_name}",
            details=f"[WHAT WAS NOTICED] Operational scenario '{sc_name}' initiated at {engine.station_name}. Disruption active across station sensors.",
            severity="CRITICAL",
            metadata={"scenario": sc_name, "params": params},
            station_id=sid,
        )

        # Record new crisis episode in database
        try:
            ep = EpisodeRecord(
                session_id=f"SES-{uuid.uuid4().hex[:8].upper()}",
                station_id=sid,
                incident_type=sc_name,
                severity="CRITICAL",
                start_sim_time=snapshot.sim_time_seconds,
                environmental_context={
                    "ambient_temp_c": snapshot.kpis.get("ambient_temp_c", -18.0),
                    "wind_speed_mps": snapshot.kpis.get("wind_speed_mps", 12.0),
                    "katabatic_alert": snapshot.kpis.get("wind_speed_mps", 12.0) > 25.0,
                },
                initial_kpis=snapshot.kpis,
                root_cause_diagnosis={"scenario": sc_name, "params": params},
            )
            self._current_episode_id = ep.episode_id
            self._current_episode_sim_start = snapshot.sim_time_seconds
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.episodes_repo.save_episode(ep))
        except Exception as e:
            logger.debug("Failed logging initial episode: %s", e)

        # Immediately trigger perception on active station
        if sid == self.active_station_id:
            self.situation_awareness.on_tick(snapshot)

        return snapshot

    def clear_scenario(self, station_id: str | None = None) -> MasterTwinSnapshot:
        """Reset specified or active station to nominal baseline."""
        engine = self.get_engine(station_id)
        engine.clear_scenario()
        snapshot = engine.step(dt_seconds=1.0)
        sid = engine.station_id
        self._record_history(sid, snapshot)

        self.reset_agent_society_states()

        if sid == self.active_station_id:
            self.situation_awareness.on_tick(snapshot)

        return snapshot

    def _record_history(self, station_id: str, snapshot: MasterTwinSnapshot) -> None:
        """Append state entry to sliding history."""
        entry = {
            "timestamp_iso": snapshot.timestamp_iso,
            "sim_time_seconds": snapshot.sim_time_seconds,
            "active_scenario": snapshot.active_scenario,
            "kpis": snapshot.kpis,
            "alert_count": len(snapshot.alerts),
        }
        self.history[station_id].append(entry)

    def get_station_summary(self, station_id: str) -> dict[str, Any]:
        """Generate high-level station health, location, and operational summary."""
        engine = self.get_engine(station_id)
        snapshot = engine.get_snapshot()
        return {
            "station_id": engine.station_id,
            "station_name": engine.station_name,
            "location": engine.location,
            "coordinates": engine.coordinates,
            "sensor_count": engine.sensor_count,
            "active_scenario": snapshot.active_scenario,
            "sim_time_seconds": snapshot.sim_time_seconds,
            "timestamp_iso": snapshot.timestamp_iso,
            "kpis": snapshot.kpis,
            "active_alert_count": len(snapshot.alerts),
            "is_active_context": engine.station_id == self.active_station_id,
        }

    def get_all_stations_summary(self) -> list[dict[str, Any]]:
        """List summaries for all managed polar stations."""
        return [self.get_station_summary(sid) for sid in self.stations.keys()]

    # -------------------------------------------------------------------------
    # Cognitive Event Bus Listeners & Structured Logger ("What Was Noticed & Done")
    # -------------------------------------------------------------------------

    def _on_any_bus_message(self, msg: AgentMessage) -> None:
        """Global bus listener to tally message activity for each agent."""
        s_role = msg.sender.value if hasattr(msg.sender, "value") else str(msg.sender)
        r_role = msg.recipient.value if hasattr(msg.recipient, "value") else str(msg.recipient)
        now = time.time()
        if s_role in self.agent_runtime_states:
            self.agent_runtime_states[s_role]["messages_sent"] += 1
            self.agent_runtime_states[s_role]["last_active_time"] = now
        if r_role in self.agent_runtime_states:
            self.agent_runtime_states[r_role]["messages_received"] += 1
            self.agent_runtime_states[r_role]["last_active_time"] = now

        # Log to persistent database dialogue repository
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                d_rec = DialogueRecord(
                    session_id=msg.session_id or "SES-BROADCAST",
                    station_id=self.active_station_id,
                    sim_time_seconds=self.get_engine().clock.elapsed_seconds,
                    sender=s_role,
                    recipient=r_role,
                    message_type=msg.message_type.value if hasattr(msg.message_type, "value") else str(msg.message_type),
                    severity=msg.severity.value if hasattr(msg.severity, "value") else str(msg.severity),
                    confidence=msg.confidence,
                    payload=msg.payload,
                )
                loop.create_task(self.dialogue_repo.log_message(d_rec))
        except (RuntimeError, ImportError):
            pass

    def _on_bus_alert(self, msg: AgentMessage) -> None:
        p = msg.payload
        if "SITUATION_AWARENESS" in self.agent_runtime_states:
            self.agent_runtime_states["SITUATION_AWARENESS"]["state"] = "PERCEIVING"
            self.agent_runtime_states["SITUATION_AWARENESS"]["hypothesis"] = f"Detected anomaly: {p.get('anomaly_type')} on {p.get('primary_sensor_id')}"
        if "DIAGNOSTIC" in self.agent_runtime_states:
            self.agent_runtime_states["DIAGNOSTIC"]["state"] = "ANALYZING"
        self.active_deliberation_phase = {
            "phase": 1,
            "phase_name": "PERCEPTION",
            "status": "ACTIVE_ANOMALY",
            "session_id": msg.session_id,
            "headline": f"Anomaly Noticed: {p.get('summary', p.get('anomaly_type'))}",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="PERCEPTION",
            title=f"Anomaly Detected: {p.get('anomaly_type', 'Telemetry Drift')}",
            details=f"[WHAT WAS NOTICED] Sensor {p.get('primary_sensor_id')}: {p.get('summary', '')} (Observed: {p.get('observed_value')}, Threshold: {p.get('threshold_value')}, RoC: {p.get('rate_of_change', 0.0):+.2f}/min).",
            severity=msg.severity.value,
            metadata=p,
            station_id=self.active_station_id,
        )

    def _on_bus_diagnosis(self, msg: AgentMessage) -> None:
        p = msg.payload
        chain_str = " -> ".join(p.get("causal_chain", []))
        if "DIAGNOSTIC" in self.agent_runtime_states:
            self.agent_runtime_states["DIAGNOSTIC"]["state"] = "DIAGNOSED"
            self.agent_runtime_states["DIAGNOSTIC"]["hypothesis"] = f"Root cause: {p.get('root_cause_name', p.get('root_cause_node_id'))} via [{chain_str}]"
            self.agent_runtime_states["DIAGNOSTIC"]["confidence"] = round(float(msg.confidence), 2)
        if "PREDICTION" in self.agent_runtime_states:
            self.agent_runtime_states["PREDICTION"]["state"] = "PROJECTING"
        if "RISK_IMPACT" in self.agent_runtime_states:
            self.agent_runtime_states["RISK_IMPACT"]["state"] = "EVALUATING"
            self.agent_runtime_states["RISK_IMPACT"]["hypothesis"] = f"Evaluating blast radius for {p.get('root_cause_name')}"

        self.active_deliberation_phase = {
            "phase": 2,
            "phase_name": "DIAGNOSIS",
            "status": "ROOT_CAUSE_ISOLATED",
            "session_id": msg.session_id,
            "headline": f"Root Cause Isolated: {p.get('root_cause_name')} (Confidence: {int(msg.confidence*100)}%)",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="DIAGNOSIS",
            title=f"Causal Root Cause: {p.get('root_cause_name', p.get('root_cause_node_id', 'unknown'))}",
            details=f"[WHAT WAS DIAGNOSED] {p.get('explanation', '')} Causal Path: [{chain_str}]. Recommended Focus: {p.get('recommended_focus', '')}.",
            severity=msg.severity.value,
            metadata=p,
            station_id=self.active_station_id,
        )

    def _on_bus_prediction(self, msg: AgentMessage) -> None:
        p = msg.payload
        min_ttf = p.get("min_time_to_failure_minutes")
        ttf_str = f"{min_ttf:.1f} min" if min_ttf is not None and min_ttf < 999.0 else "Stable"
        if "PREDICTION" in self.agent_runtime_states:
            self.agent_runtime_states["PREDICTION"]["state"] = "PROJECTED"
            self.agent_runtime_states["PREDICTION"]["hypothesis"] = f"Time-to-failure: {ttf_str}. Forward lookahead horizon computed."
        if "PLANNING" in self.agent_runtime_states:
            self.agent_runtime_states["PLANNING"]["state"] = "FORMULATING"

        self.active_deliberation_phase = {
            "phase": 3,
            "phase_name": "PREDICTION",
            "status": "TTF_COMPUTED",
            "session_id": msg.session_id,
            "headline": f"Predictive Horizon: TTF {ttf_str}",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="PREDICTION",
            title=f"Predictive Projection: TTF {ttf_str}",
            details=f"[WHAT WAS PROJECTED] Time-to-failure horizon: {ttf_str}. Forward lookahead trajectory evaluated against unmitigated baseline.",
            severity=msg.severity.value,
            metadata=p,
            station_id=self.active_station_id,
        )

    def _on_bus_proposal(self, msg: AgentMessage) -> None:
        p = msg.payload
        if "PLANNING" in self.agent_runtime_states:
            self.agent_runtime_states["PLANNING"]["state"] = "PROPOSED"
            self.agent_runtime_states["PLANNING"]["hypothesis"] = f"Proposed: {p.get('title')} ({p.get('tier', 'TIER_1')})"
        if "WHAT_IF" in self.agent_runtime_states:
            self.agent_runtime_states["WHAT_IF"]["state"] = "SIMULATING"

        self.active_deliberation_phase = {
            "phase": 4,
            "phase_name": "PROPOSALS",
            "status": "CANDIDATE_FORMULATED",
            "session_id": msg.session_id,
            "headline": f"Mitigation Formulated: {p.get('title')}",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="PLANNING",
            title=f"Operational Plan Formulated: {p.get('title', 'Action Plan')}",
            details=f"[WHAT WAS PLANNED] Strategy: {p.get('target_subsystem', 'STATION')}. Tier: {p.get('tier', 'TIER_1')}. Rationale: {p.get('rationale', '')}.",
            severity=msg.severity.value,
            metadata=p,
            station_id=self.active_station_id,
        )

    def _on_bus_sim_result(self, msg: AgentMessage) -> None:
        p = msg.payload
        status_txt = "VERIFIED SAFE" if p.get("is_safe") else "SAFETY VIOLATION"
        if "WHAT_IF" in self.agent_runtime_states:
            self.agent_runtime_states["WHAT_IF"]["state"] = "VERIFIED"
            self.agent_runtime_states["WHAT_IF"]["hypothesis"] = f"Sandbox Verdict: {status_txt}. Fuel: {p.get('fuel_saved_l', 0.0):+.1f}L, Temp: {p.get('temp_difference_c', 0.0):+.1f}°C"
        if "FRIDAY_ORCHESTRATOR" in self.agent_runtime_states:
            self.agent_runtime_states["FRIDAY_ORCHESTRATOR"]["state"] = "ARBITRATING"

        self.active_deliberation_phase = {
            "phase": 5,
            "phase_name": "SIMULATION",
            "status": "SANDBOX_VALIDATED",
            "session_id": msg.session_id,
            "headline": f"Digital Twin Sandbox: {status_txt}",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="PREDICTION",
            title=f"What-If Sandbox Simulation: {p.get('plan_title', 'Plan')} ({status_txt})",
            details=f"[WHAT WAS SIMULATED] Fuel delta: {p.get('fuel_saved_l', 0.0):+.1f}L, Temp delta: {p.get('temp_difference_c', 0.0):+.1f}°C, Risk reduction: {p.get('risk_reduction_pct', 0.0):+.1f}%. Verdict: {p.get('recommendation', 'APPROVE')}.",
            severity="INFO" if p.get("is_safe") else "CRITICAL",
            metadata=p,
            station_id=self.active_station_id,
        )

    def record_actuation(
        self,
        title: str,
        applied_overrides: list[dict[str, Any]],
        station_id: str | None = None,
        autonomy_tier: str = "TIER_1_AUTONOMOUS",
        dynamic_agent_chain: list[str] | None = None,
        verification: str = "Verified Safe: Microgrid 50.0 Hz nominal, life-support thermal boundary secured.",
        status: str = "EXECUTED_ON_DIGITAL_TWIN",
        action_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Record an executed physical actuation and parameter adjustment in the Black Box Flight Ledger."""
        sid = (station_id or self.active_station_id).lower()
        now_ts = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            sim_sec = self.get_engine(sid).clock.elapsed_seconds
        except Exception:
            sim_sec = 0.0

        act_record = {
            "action_id": action_id or f"ACT-{int(now_ts * 1000)}",
            "session_id": session_id or "SES-LOCAL-AUTONOMY",
            "title": title,
            "station_id": sid,
            "autonomy_tier": autonomy_tier,
            "dynamic_agent_chain": dynamic_agent_chain or [
                "SITUATION_AWARENESS",
                "DIAGNOSTIC",
                "PREDICTION",
                "PLANNING",
                "WHAT_IF",
                "FRIDAY_ORCHESTRATOR",
            ],
            "applied_overrides": applied_overrides,
            "physical_verification": verification,
            "status": status,
            "timestamp": now_ts,
            "timestamp_iso": now_iso,
            "sim_time_seconds": round(sim_sec, 2),
        }
        self.autonomous_action_history.append(act_record)
        return act_record

    def _on_bus_consensus(self, msg: AgentMessage) -> None:
        p = msg.payload
        overrides = p.get("applied_overrides", [])
        if "FRIDAY_ORCHESTRATOR" in self.agent_runtime_states:
            self.agent_runtime_states["FRIDAY_ORCHESTRATOR"]["state"] = "ACTUATED"
            self.agent_runtime_states["FRIDAY_ORCHESTRATOR"]["hypothesis"] = f"Consensus Plan Executed: {p.get('plan_title')}. Physical overrides applied."

        self.active_deliberation_phase = {
            "phase": 6,
            "phase_name": "CONSENSUS",
            "status": "ACTUATED",
            "session_id": msg.session_id,
            "headline": f"F.R.I.D.A.Y. Actuation Executed: {p.get('plan_title')}",
            "updated_at": time.time(),
        }

        self.log_cognitive_event(
            category="ACTUATION",
            title=f"Physical Actuation Executed: {p.get('plan_title', 'Consensus Plan')}",
            details=f"[WHAT WAS DONE] F.R.I.D.A.Y. executed physical overrides: {json.dumps(overrides)}. Status: {p.get('status')}. Station life-support and grid balance preserved.",
            severity="INFO",
            metadata=p,
            station_id=self.active_station_id,
        )
        tier_val = p.get("tier", "TIER_1_AUTONOMOUS")
        if hasattr(tier_val, "value"):
            tier_val = tier_val.value
        self.record_actuation(
            title=p.get("plan_title", "Consensus Plan"),
            applied_overrides=overrides,
            station_id=self.active_station_id,
            autonomy_tier=str(tier_val),
            dynamic_agent_chain=[
                "SITUATION_AWARENESS",
                "DIAGNOSTIC",
                "PREDICTION",
                "PLANNING",
                "WHAT_IF",
                "FRIDAY_ORCHESTRATOR",
            ],
            verification="Verified Safe in What-If Sandbox. Microgrid stable at 50.0 Hz, zero thermal violations.",
            status="EXECUTED_ON_DIGITAL_TWIN",
            action_id=p.get("proposal_id"),
            session_id=msg.session_id,
        )

        # Finalize active crisis episode in database
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                now_sim = self.get_engine().clock.elapsed_seconds
                start_sim = getattr(self, "_current_episode_sim_start", now_sim - 60.0)
                duration = max(1.0, now_sim - start_sim)
                rec_kpis = self.get_engine().get_station_kpis()
                lessons = (
                    f"Mitigation plan '{p.get('plan_title')}' successfully executed by {p.get('arbitrated_by', 'FRIDAY_ORCHESTRATOR')}. "
                    f"Overrides applied: {overrides}. Thermal margin and grid balance restored within {duration:.1f}s."
                )
                ep_id = getattr(self, "_current_episode_id", None)
                loop.create_task(
                    self.episodes_repo.finalize_episode(
                        session_id=msg.session_id,
                        episode_id=ep_id,
                        consensus_plan=p,
                        outcome={
                            "status": "RESOLVED_SUCCESSFULLY",
                            "recovery_duration_sec": duration,
                            "recovery_kpis": rec_kpis,
                        },
                        lessons_learned=lessons,
                        end_sim_time=now_sim,
                    )
                )
                self._current_episode_id = None
        except Exception as e:
            logger.debug("Failed finalizing episode in db: %s", e)

    def get_agent_society_status(self) -> dict[str, Any]:
        """Retrieve dynamic runtime operational status for all 10 cognitive agents."""
        return {
            "orchestrator_state": self.agent_runtime_states["FRIDAY_ORCHESTRATOR"]["state"],
            "total_agents": len(self.agent_runtime_states),
            "agents": self.agent_runtime_states,
            "active_deliberation_phase": self.active_deliberation_phase,
            "bus_total_messages": len(self.bus.get_history()),
            "active_sessions_count": len(self.bus.get_active_sessions()),
            "latest_session_id": self.active_deliberation_phase.get("session_id"),
        }

    def reset_agent_society_states(self) -> None:
        """Reset agent states to baseline nominal monitoring."""
        for role, data in self.agent_runtime_states.items():
            if role == "SITUATION_AWARENESS":
                data["state"] = "SCANNING"
                data["hypothesis"] = "All 505 telemetry points within nominal operational envelope."
            elif role == "FRIDAY_ORCHESTRATOR":
                data["state"] = "MONITORING"
                data["hypothesis"] = "Station governed under 100% autonomous edge stability invariant."
            else:
                data["state"] = "STANDBY"
                data["hypothesis"] = "Standing by for cognitive bus events."
            data["confidence"] = 1.0

        self.active_deliberation_phase = {
            "phase": 1,
            "phase_name": "PERCEPTION",
            "status": "NOMINAL",
            "session_id": None,
            "headline": "Station telemetry nominal across all 4 observation pillars.",
            "updated_at": time.time(),
        }

    def log_cognitive_event(
        self,
        category: str,
        title: str,
        details: str,
        severity: str = "INFO",
        metadata: dict[str, Any] | None = None,
        station_id: str | None = None,
    ) -> dict[str, Any]:
        """Record structured, explainable cognitive perception or actuation event."""
        entry = {
            "event_id": f"EVT-{int(time.time()*1000)%1000000:06d}-{uuid.uuid4().hex[:4]}",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "timestamp": time.time(),
            "station_id": (station_id or self.active_station_id).lower(),
            "category": category.upper(),
            "title": title,
            "details": details,
            "severity": severity.upper(),
            "metadata": metadata or {},
        }
        self.cognitive_logs.append(entry)
        return entry

    def get_cognitive_logs(
        self,
        station_id: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve historical cognitive perception and actuation logs."""
        sid = station_id.lower() if station_id else None
        cat = category.upper() if category and category.upper() != "ALL" else None

        filtered = []
        for log in reversed(self.cognitive_logs):
            if sid and log["station_id"] != sid:
                continue
            if cat and log["category"] != cat:
                continue
            filtered.append(log)
            if len(filtered) >= limit:
                break
        return filtered

    # -------------------------------------------------------------------------
    # Physical Actuators Subsystem
    # -------------------------------------------------------------------------

    def get_actuator_state(self, station_id: str | None = None) -> dict[str, Any]:
        """Expose current physical actuator states across Energy, Infrastructure, and Life-Support."""
        sid = (station_id or self.active_station_id).lower()
        engine = self.get_engine(sid)
        emulator = self.satcom_emulators[sid]
        is_blackout = emulator.profile.name == "POLAR_BLACKOUT"

        # 1. CHP Generators
        chps_data = []
        for idx, c in enumerate(engine.energy_registry.physics.chps):
            chps_data.append({
                "unit_id": idx + 1,
                "name": f"CHP-{idx + 1:02d}",
                "operating_state": c.operating_state,
                "power_kw": round(float(c.active_power_kw), 1),
                "running": bool(c.running_status),
                "coolant_temp_c": round(float(c.coolant_temperature_c), 1),
                "fuel_flow_lph": round(float(c.fuel_consumption_lph), 1),
                "runtime_hours": round(float(c.runtime_hours), 1),
            })

        # 2. Utilidor Trace Heating
        pipe_phys = engine.infra_registry.physics.pipelines
        trace_data = {
            "water01_trace_heating_on": bool(pipe_phys.water01_trace_heating_on),
            "water01_pipe_temp_c": round(float(pipe_phys.water01_pipe_temp_c), 1),
            "fuel01_trace_heating_on": bool(pipe_phys.fuel01_trace_heating_on),
            "heat01_trace_heating_on": bool(pipe_phys.heat01_trace_heating_on),
            "freeze_hazard": float(pipe_phys.water01_pipe_temp_c) < 1.0,
        }

        # 3. HVAC & Blizzard Dampers
        hvac_phys = engine.infra_registry.physics.hvac
        bldg_phys = engine.infra_registry.physics.building
        hvac_data = {
            "living_temp_c": round(float(bldg_phys.temp_living_c), 1),
            "lab_temp_c": round(float(bldg_phys.temp_lab_c), 1),
            "technical_temp_c": round(float(bldg_phys.temp_technical_c), 1),
            "ahu01_fan_running": bool(hvac_phys.ahu01_fan_running),
            "ahu01_heating_valve_pct": round(float(hvac_phys.ahu01_heating_valve_pct), 1),
            "ahu01_fresh_air_damper_pct": round(float(hvac_phys.ahu01_fresh_air_damper_pct), 1),
            "ahu02_fan_running": bool(hvac_phys.ahu02_fan_running),
            "ahu02_heating_valve_pct": round(float(hvac_phys.ahu02_heating_valve_pct), 1),
            "ahu02_fresh_air_damper_pct": round(float(hvac_phys.ahu02_fresh_air_damper_pct), 1),
            "blizzard_dampers_sealed": float(hvac_phys.ahu01_fresh_air_damper_pct) <= 5.0,
        }

        # 4. Science Load Shedding
        is_shed = getattr(engine, "_science_load_shed", False)
        load_shed_data = {
            "science_load_shed": is_shed,
            "conserved_kw": 15.0 if is_shed else 0.0,
        }

        # 5. Water / RO Desalination
        water_phys = engine.infra_registry.physics.water
        water_data = {
            "ro_system_status": water_phys.ro_system_status,
            "potable_tank_level_pct": round(float(water_phys.potable_tank_level_pct), 1),
            "potable_tank_volume_l": round(float(water_phys.potable_tank_volume_l), 1),
            "intake_pump_running": bool(water_phys.intake_pump_running),
        }

        # 6. Edge Command & Satcom Mode
        edge_data = {
            "station_id": sid,
            "autonomous_mode_enabled": self.autonomous_mode_enabled,
            "command_authority": "100% LOCAL EDGE AUTONOMY" if is_blackout else "MAINLAND HQ SUPERVISED",
            "satcom_profile": emulator.profile.name,
            "bandwidth_kbps": round(emulator.params.bandwidth_bps / 1000.0, 1),
            "is_blackout": is_blackout,
            "spooled_packets_count": len(emulator.spool_queue),
            "continuous_loop_running": self.is_continuous_loop_running,
            "continuous_speed": self.continuous_speed,
        }

        return {
            "station_id": sid,
            "generators": chps_data,
            "trace_heating": trace_data,
            "hvac": hvac_data,
            "load_shedding": load_shed_data,
            "water_system": water_data,
            "edge_status": edge_data,
        }

    def set_actuator_command(
        self,
        station_id: str,
        command: str,
        parameters: dict[str, Any],
        pin: str | None = None,
    ) -> dict[str, Any]:
        """Manually or programmatically command station actuators."""
        sid = station_id.lower()
        engine = self.get_engine(sid)
        cmd = command.upper()

        if cmd == "START_CHP":
            unit_id = int(parameters.get("unit_id", 1))
            kw = float(parameters.get("power_kw", 65.0))
            idx = max(0, min(unit_id - 1, 2))
            engine.energy_registry.physics.chps[idx].operating_state = "RUNNING"
            engine.energy_registry.physics.chps[idx].running_status = True
            engine.energy_registry.physics.chps[idx].active_power_kw = kw
            engine._couple_physics(0.0)
            engine._refresh_all_readings()
            self.log_cognitive_event(
                category="ACTUATION",
                title=f"Manual Operator Override: Started Generator CHP-{unit_id:02d}",
                details=f"[WHAT WAS DONE] Generator CHP-{unit_id:02d} commanded to RUNNING @ {kw} kW.",
                severity="INFO",
                station_id=sid,
            )
            self.record_actuation(
                title=f"Manual Dispatch: Started Generator CHP-{unit_id:02d}",
                applied_overrides=[
                    {"pillar": "energy", "path": f"chps[{idx}].operating_state", "value": "RUNNING"},
                    {"pillar": "energy", "path": f"chps[{idx}].active_power_kw", "value": kw},
                ],
                station_id=sid,
                autonomy_tier="MANUAL_COMMANDER_OVERRIDE",
                dynamic_agent_chain=["STATION_COMMANDER", "SAFETY_INTERLOCK", "DIGITAL_TWIN"],
                verification=f"Generator CHP-{unit_id:02d} synchronized to MLVD bus @ {kw} kW.",
            )
            return {"status": "SUCCESS", "message": f"CHP-{unit_id:02d} started successfully"}

        elif cmd == "STOP_CHP":
            unit_id = int(parameters.get("unit_id", 1))
            idx = max(0, min(unit_id - 1, 2))
            running_count = sum(
                1 for c in engine.energy_registry.physics.chps
                if c.operating_state == "RUNNING" or c.running_status
            )
            is_target_running = (
                engine.energy_registry.physics.chps[idx].operating_state == "RUNNING"
                or engine.energy_registry.physics.chps[idx].running_status
            )
            if is_target_running and running_count <= 1:
                if not pin or not self.safety_interlock.verify_commander_authorization("STOP_CHP", pin):
                    raise PermissionError("Stopping the last running generator requires Commander PIN verification.")
            engine.energy_registry.physics.chps[idx].operating_state = "STANDBY"
            engine.energy_registry.physics.chps[idx].running_status = False
            engine.energy_registry.physics.chps[idx].active_power_kw = 0.0
            engine._couple_physics(0.0)
            engine._refresh_all_readings()
            self.log_cognitive_event(
                category="ACTUATION",
                title=f"Manual Operator Override: Stopped Generator CHP-{unit_id:02d}",
                details=f"[WHAT WAS DONE] Generator CHP-{unit_id:02d} transitioned to STANDBY.",
                severity="WARNING",
                station_id=sid,
            )
            self.record_actuation(
                title=f"Commander Override: Stopped Generator CHP-{unit_id:02d}",
                applied_overrides=[
                    {"pillar": "energy", "path": f"chps[{idx}].operating_state", "value": "STANDBY"},
                    {"pillar": "energy", "path": f"chps[{idx}].active_power_kw", "value": 0.0},
                ],
                station_id=sid,
                autonomy_tier="TIER_3_COMMANDER_CONFIRMATION",
                dynamic_agent_chain=["STATION_COMMANDER", "PIN_GATEKEEPER", "SAFETY_INTERLOCK"],
                verification="Commander cryptographic PIN verified. Standby state confirmed.",
            )
            return {"status": "SUCCESS", "message": f"CHP-{unit_id:02d} stopped"}

        elif cmd == "SET_TRACE_HEATING":
            active = bool(parameters.get("active", True))
            pipe = engine.infra_registry.physics.pipelines
            pipe.water01_trace_heating_on = active
            if active:
                pipe.water01_pipe_temp_c = max(4.5, pipe.water01_pipe_temp_c)
            engine._couple_physics(0.0)
            engine._refresh_all_readings()
            self.log_cognitive_event(
                category="ACTUATION",
                title=f"Utilidor Trace Heating: {'ACTIVATED' if active else 'DEACTIVATED'}",
                details=f"[WHAT WAS DONE] Fresh water utilidor trace heating set to {active}. Pipe temp: {pipe.water01_pipe_temp_c:.1f}°C.",
                severity="INFO",
                station_id=sid,
            )
            self.record_actuation(
                title=f"Utilidor Trace Heating: {'ACTIVATED' if active else 'DEACTIVATED'}",
                applied_overrides=[
                    {"pillar": "infrastructure", "path": "pipelines.water01_trace_heating_on", "value": active},
                    {"pillar": "infrastructure", "path": "pipelines.water01_pipe_temp_c", "value": pipe.water01_pipe_temp_c},
                ],
                station_id=sid,
                autonomy_tier="MANUAL_COMMANDER_OVERRIDE",
                dynamic_agent_chain=["STATION_COMMANDER", "INFRASTRUCTURE_REGISTRY"],
                verification=f"Pipe temperature secured at {pipe.water01_pipe_temp_c:.1f}°C.",
            )
            return {"status": "SUCCESS", "message": f"Trace heating set to {active}"}

        elif cmd == "SET_BLIZZARD_DAMPERS":
            sealed = bool(parameters.get("sealed", True))
            hvac = engine.infra_registry.physics.hvac
            if sealed:
                hvac.ahu01_fresh_air_damper_pct = 0.0
                hvac.ahu02_fresh_air_damper_pct = 0.0
                hvac.ahu01_heating_valve_pct = 85.0
            else:
                hvac.ahu01_fresh_air_damper_pct = 25.0
                hvac.ahu02_fresh_air_damper_pct = 30.0
            engine._couple_physics(0.0)
            engine._refresh_all_readings()
            self.log_cognitive_event(
                category="ACTUATION",
                title=f"Blizzard Dampers: {'SEALED (0% Infiltration)' if sealed else 'OPEN (25% Fresh Air)'}",
                details=f"[WHAT WAS DONE] AHU fresh air dampers commanded to {'SEALED' if sealed else 'OPEN'}.",
                severity="INFO",
                station_id=sid,
            )
            self.record_actuation(
                title=f"Blizzard Dampers: {'SEALED (0% Infiltration)' if sealed else 'OPEN (25% Fresh Air)'}",
                applied_overrides=[
                    {"pillar": "infrastructure", "path": "hvac.ahu01_fresh_air_damper_pct", "value": 0.0 if sealed else 25.0},
                    {"pillar": "infrastructure", "path": "hvac.ahu02_fresh_air_damper_pct", "value": 0.0 if sealed else 30.0},
                ],
                station_id=sid,
                autonomy_tier="MANUAL_COMMANDER_OVERRIDE",
                dynamic_agent_chain=["STATION_COMMANDER", "INFRASTRUCTURE_REGISTRY"],
                verification=f"AHU fresh air dampers set to {'0% sealed' if sealed else '25% open'}.",
            )
            return {"status": "SUCCESS", "message": f"Dampers set to {'SEALED' if sealed else 'OPEN'}"}

        elif cmd == "TOGGLE_SCIENCE_LOAD_SHED":
            shed = bool(parameters.get("shed", True))
            engine._science_load_shed = shed
            if shed:
                engine.infra_registry.physics.building.temp_lab_c = 18.0
            else:
                engine.infra_registry.physics.building.temp_lab_c = 20.8
            engine._couple_physics(0.0)
            engine._refresh_all_readings()
            self.log_cognitive_event(
                category="ACTUATION",
                title=f"Non-Essential Science Load Shedding: {'ENGAGED (-15 kW)' if shed else 'RESTORED'}",
                details=f"[WHAT WAS DONE] Non-essential science electrical and heating loads {'shed' if shed else 'restored'} to balance station power.",
                severity="INFO",
                station_id=sid,
            )
            self.record_actuation(
                title=f"Science Load Shedding: {'ENGAGED (-15 kW)' if shed else 'RESTORED'}",
                applied_overrides=[
                    {"pillar": "energy", "path": "science_loads_shed", "value": shed},
                    {"pillar": "infrastructure", "path": "building.temp_lab_c", "value": 18.0 if shed else 20.8},
                ],
                station_id=sid,
                autonomy_tier="TIER_1_AUTONOMOUS",
                dynamic_agent_chain=["STATION_COMMANDER", "ENERGY_REGISTRY"],
                verification=f"Science electrical bus shed status: {shed}.",
            )
            return {"status": "SUCCESS", "message": f"Science load shed set to {shed}"}

        raise ValueError(f"Unknown actuator command '{command}'")

    # -------------------------------------------------------------------------
    # Autonomous Control Loop & Edge Governance Engine
    # -------------------------------------------------------------------------

    def run_autonomous_tick(self, station_id: str | None = None) -> MasterTwinSnapshot:
        """Advance station simulation, run autonomous AI perception, evaluate edge authority and actuators."""
        sid = (station_id or self.active_station_id).lower()
        engine = self.get_engine(sid)
        emulator = self.satcom_emulators[sid]
        is_blackout = emulator.profile.name == "POLAR_BLACKOUT"
        self.orchestrator.edge_blackout_mode = is_blackout

        # Advance digital twin physics 1 second
        snapshot = self.step(sid, dt_seconds=1.0)

        # If autonomous mode is enabled:
        if self.autonomous_mode_enabled:
            # If under Polar Blackout, check for pending Tier 2 actions held in supervision queue
            # and auto-execute them on the edge
            if is_blackout:
                pending = self.orchestrator.get_pending_supervised_actions()
                for item in pending:
                    act_id = item["action_id"]
                    res = self.orchestrator.bypass_supervised_action(act_id)
                    if res and res.success:
                        self.log_cognitive_event(
                            category="EDGE_AUTHORITY",
                            title=f"Edge Authority Override: {item['proposal']['title']}",
                            details=f"[WHAT WAS DONE] Mainland connection unavailable (0 kbps). Auto-executed supervised action immediately on local edge to protect station integrity: {res.message}",
                            severity="WARNING",
                            metadata=res.to_dict(),
                            station_id=sid,
                        )

            # Check if there is an active crisis scenario and auto-ensure physical stability
            sc = engine.active_scenario
            if sc == MasterScenario.GENERATOR_TRIP:
                chp1 = engine.energy_registry.physics.chps[0]
                chp2 = engine.energy_registry.physics.chps[1]
                if chp1.operating_state in ("MAINTENANCE", "OFF") and chp2.operating_state != "RUNNING":
                    chp2.operating_state = "RUNNING"
                    chp2.running_status = True
                    chp2.active_power_kw = 65.0
                    engine._couple_physics(0.0)
                    engine._refresh_all_readings()
                    self.log_cognitive_event(
                        category="ACTUATION",
                        title="Autonomous Generator Auto-Transfer: Started CHP-02",
                        details="[WHAT WAS DONE] Generator 1 tripped offline. F.R.I.D.A.Y. autonomously started standby Generator 2 @ 65 kW to prevent MLVD 400V bus collapse.",
                        severity="CRITICAL",
                        metadata={"generator": "CHP-02", "power_kw": 65.0},
                        station_id=sid,
                    )
                    self.record_actuation(
                        title="Autonomous Auto-Transfer: Started Standby CHP-02",
                        applied_overrides=[
                            {"pillar": "energy", "path": "chps[1].operating_state", "value": "RUNNING"},
                            {"pillar": "energy", "path": "chps[1].active_power_kw", "value": 65.0},
                        ],
                        station_id=sid,
                        autonomy_tier="TIER_1_AUTONOMOUS",
                        dynamic_agent_chain=["SITUATION_AWARENESS", "DIAGNOSTIC", "PLANNING", "WHAT_IF", "FRIDAY_ORCHESTRATOR"],
                        verification="Microgrid 400V bus stabilized (+65 kW), Frequency 50.0 Hz nominal.",
                    )

            elif sc == MasterScenario.BLIZZARD_STRIKE:
                hvac = engine.infra_registry.physics.hvac
                if hvac.ahu01_fresh_air_damper_pct > 5.0:
                    hvac.ahu01_fresh_air_damper_pct = 0.0
                    hvac.ahu02_fresh_air_damper_pct = 0.0
                    hvac.ahu01_heating_valve_pct = 85.0
                    hvac.ahu02_heating_valve_pct = 85.0
                    engine.infra_registry.physics.pipelines.water01_trace_heating_on = True
                    engine._couple_physics(0.0)
                    engine._refresh_all_readings()
                    self.log_cognitive_event(
                        category="ACTUATION",
                        title="Autonomous Blizzard Defense: Sealed Fresh Air Dampers",
                        details="[WHAT WAS DONE] Severe katabatic wind storm detected (>30 m/s). Sealed fresh air dampers to 0% to prevent whiteout infiltration, boosted heating valve to 85%, engaged pipeline trace heating.",
                        severity="WARNING",
                        metadata={"damper_pct": 0.0, "heating_valve_pct": 85.0},
                        station_id=sid,
                    )
                    self.record_actuation(
                        title="Autonomous Blizzard Defense: Sealed Fresh Air Dampers",
                        applied_overrides=[
                            {"pillar": "infrastructure", "path": "hvac.ahu01_fresh_air_damper_pct", "value": 0.0},
                            {"pillar": "infrastructure", "path": "hvac.ahu02_fresh_air_damper_pct", "value": 0.0},
                            {"pillar": "infrastructure", "path": "pipelines.water01_trace_heating_on", "value": True},
                        ],
                        station_id=sid,
                        autonomy_tier="TIER_1_AUTONOMOUS",
                        dynamic_agent_chain=["SITUATION_AWARENESS", "DIAGNOSTIC", "PLANNING", "WHAT_IF", "FRIDAY_ORCHESTRATOR"],
                        verification="Infiltration sealed (0%), Hydronic heating boosted to 85%, trace heating engaged.",
                    )

            elif sc == MasterScenario.WATER_LINE_FREEZE:
                pipe = engine.infra_registry.physics.pipelines
                if not pipe.water01_trace_heating_on or pipe.water01_pipe_temp_c < 1.0:
                    pipe.water01_trace_heating_on = True
                    pipe.water01_pipe_temp_c = 4.8
                    engine.infra_registry.physics.water.ro_system_status = "PRODUCING"
                    engine._couple_physics(0.0)
                    engine._refresh_all_readings()
                    self.log_cognitive_event(
                        category="ACTUATION",
                        title="Autonomous Freeze Protection: Energized Utilidor Trace Heating",
                        details="[WHAT WAS DONE] Potable water pipe temperature dropped towards freezing. F.R.I.D.A.Y. energized auxiliary heat tracing circuits, recovering pipe temp to +4.8°C.",
                        severity="CRITICAL",
                        metadata={"trace_heating": True, "pipe_temp_c": 4.8},
                        station_id=sid,
                    )
                    self.record_actuation(
                        title="Autonomous Freeze Protection: Energized Utilidor Trace Heating",
                        applied_overrides=[
                            {"pillar": "infrastructure", "path": "pipelines.water01_trace_heating_on", "value": True},
                            {"pillar": "infrastructure", "path": "pipelines.water01_pipe_temp_c", "value": 4.8},
                        ],
                        station_id=sid,
                        autonomy_tier="TIER_1_AUTONOMOUS",
                        dynamic_agent_chain=["SITUATION_AWARENESS", "DIAGNOSTIC", "PLANNING", "WHAT_IF", "FRIDAY_ORCHESTRATOR"],
                        verification="Potable water utilidor line recovered to +4.8°C. Freeze hazard cleared.",
                    )

        return snapshot

    async def run_continuous_loop(self) -> None:
        """Background coroutine advancing digital twin and running edge autonomy at 1 Hz."""
        logger.info("F.R.I.D.A.Y. Continuous Autonomous Station Governor loop started.")
        self.is_continuous_loop_running = True
        try:
            while self.is_continuous_loop_running:
                try:
                    self.run_autonomous_tick(self.active_station_id)
                except Exception as exc:
                    logger.error("Error in continuous autonomous loop: %s", exc)
                delay = 1.0 / max(0.1, self.continuous_speed)
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logger.info("F.R.I.D.A.Y. Continuous Autonomous Station Governor loop cancelled.")
        finally:
            self.is_continuous_loop_running = False

    def start_continuous_loop(self) -> None:
        """Start the background continuous 1 Hz simulation and autonomy loop."""
        if not self.is_continuous_loop_running:
            self.is_continuous_loop_running = True
            try:
                loop = asyncio.get_running_loop()
                self._bg_task = loop.create_task(self.run_continuous_loop())
            except RuntimeError:
                pass

    def stop_continuous_loop(self) -> None:
        """Stop the background continuous simulation loop."""
        self.is_continuous_loop_running = False
        if self._bg_task and not self._bg_task.done():
            self._bg_task.cancel()


# Global singleton instance for server runtime
_state_instance: ServerState | None = None


def get_server_state(seed: int = 42) -> ServerState:
    """Retrieve or create the global server state singleton."""
    global _state_instance
    if _state_instance is None:
        _state_instance = ServerState(seed=seed)
    return _state_instance


def reset_server_state(seed: int = 42) -> ServerState:
    """Reset the global server state (primarily for test fixtures)."""
    global _state_instance
    DatabaseManager.reset_instance()
    _state_instance = ServerState(seed=seed)
    return _state_instance
