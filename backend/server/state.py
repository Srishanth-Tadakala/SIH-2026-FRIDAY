"""Server State Management for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Manages dual-station digital twins (Bharati & Maitri), causal graph, message bus,
safety interlock manager, and the 10 specialized cognitive agents.
"""

from __future__ import annotations

from collections import deque
import logging
import time
from typing import Any

from backend.agents.framework.bus import AgentMessageBus
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
            bus=self.bus, engine=self.bharati_engine, graph=self.graph
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

        # Server start timestamp
        self.server_start_time = time.time()
        logger.info("F.R.I.D.A.Y. Dual-Station State, Agents & Satcom Sync Engines Online.")

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
        for sid in targets:
            if sid in self.satcom_emulators:
                self.satcom_emulators[sid].set_profile(profile)

    def recover_satcom_blackout(
        self, station_id: str, new_profile: str = "INMARSAT_STANDARD"
    ) -> list[dict[str, Any]]:
        """Drain spooled blackout queue and apply frames to mainland mirror twin in priority order."""
        sid = station_id.lower()
        emulator = self.satcom_emulators[sid]
        mirror = self.mainland_mirrors[sid]

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
    _state_instance = ServerState(seed=seed)
    return _state_instance
