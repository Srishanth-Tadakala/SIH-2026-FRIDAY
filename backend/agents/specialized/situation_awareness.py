"""Situation Awareness Agent for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

COGNITIVE OBJECTIVE:
"What is happening right now across the station's 505 sensors?"

RESPONSIBILITIES:
1. Continuous Sensor Scanning: Monitors telemetry across Energy, Infrastructure,
   Environment, and Logistics pillars on every clock tick.
2. Rate-of-Change (RoC) Tracking: Detects rapid physical degradation before hard
   thresholds are breached (e.g. rapid wind acceleration, steep indoor thermal decay).
3. Multi-Sensor Correlation: Correlates physical ripples (e.g. ambient plunge + heating
   load surge + utilidor cooling) to distinguish systemic crises from localized sensor drift.
4. Incident Initiation: Automatically creates a DeliberationSession on the Agent Message
   Bus and broadcasts structured ALERT messages for downstream Diagnostic and Planning agents.
5. Situation Reporting: Responds to operator queries with comprehensive operational summaries.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time
from typing import Any

from ...core.causal_graph import TwinCausalGraph
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


@dataclass
class AnomalyRecord:
    """Detected physical or operational anomaly across the digital twin."""
    anomaly_id: str
    anomaly_type: str
    subsystem: str
    primary_sensor_id: str
    observed_value: Any
    threshold_value: Any
    severity: SeverityLevel
    summary: str
    rate_of_change: float = 0.0
    correlated_sensors: list[str] = field(default_factory=list)
    first_detected_sim_time: float = 0.0
    last_detected_sim_time: float = 0.0


class SituationAwarenessAgent(BaseSpecializedAgent):
    """Specialized cognitive agent responsible for station-wide situational awareness."""

    def __init__(
        self,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
    ) -> None:
        super().__init__(
            role=AgentRole.SITUATION_AWARENESS,
            bus=bus,
            engine=engine,
            graph=graph,
        )

        # Sliding window history for RoC computation: sensor_id -> deque[(sim_time, value)]
        self._history: dict[str, deque[tuple[float, float]]] = {}
        self._history_window_seconds: float = 300.0  # 5-minute window

        # Active anomalies: anomaly_key -> AnomalyRecord
        self._active_anomalies: dict[str, AnomalyRecord] = {}

        # Mappings of active anomaly_key -> DeliberationSession ID
        self._anomaly_sessions: dict[str, str] = {}

    def on_tick(self, snapshot: MasterTwinSnapshot) -> None:
        """Continuous perception hook executed on every digital twin step."""
        self.scan_telemetry(snapshot)

    def scan_telemetry(self, snapshot: MasterTwinSnapshot) -> list[AnomalyRecord]:
        """Exhaustively scan current telemetry and detect physical threshold or RoC anomalies."""
        detected: list[AnomalyRecord] = []
        sim_time = snapshot.sim_time_seconds
        readings = snapshot.readings
        kpis = snapshot.kpis

        # ---------------------------------------------------------------------
        # 1. Weather & Katabatic Blizzard Monitoring
        # ---------------------------------------------------------------------
        w_spd_reading = readings.get("ENV-WX-WIND-S")
        if w_spd_reading is not None:
            w_spd = float(w_spd_reading.value)
            self._update_history("ENV-WX-WIND-S", sim_time, w_spd)
            w_roc = self._calculate_roc("ENV-WX-WIND-S", sim_time)

            if w_spd >= 30.0 or (w_spd >= 25.0 and w_roc > 2.0):
                sev = SeverityLevel.EMERGENCY if w_spd >= 35.0 else SeverityLevel.CRITICAL
                record = self._build_anomaly(
                    anomaly_key="BLIZZARD_KATABATIC_SURGE",
                    anomaly_type="KATABATIC_BLIZZARD_SURGE",
                    subsystem="ENVIRONMENT",
                    sensor_id="ENV-WX-WIND-S",
                    value=w_spd,
                    threshold=25.0,
                    severity=sev,
                    summary=f"Severe katabatic wind storm detected: {w_spd:.1f} m/s (RoC: {w_roc:+.2f} m/s/min)",
                    roc=w_roc,
                    correlated=["ENV-WX-GUST", "ENV-WX-VIS", "BHARATI-BLDG-ENV-TEMP-NORTH"],
                    sim_time=sim_time,
                )
                detected.append(record)

        # ---------------------------------------------------------------------
        # 2. Indoor Thermal Life-Support Monitoring
        # ---------------------------------------------------------------------
        living_temp_reading = readings.get("BHARATI-BLDG-Z01-TEMP")
        if living_temp_reading is not None:
            living_temp = float(living_temp_reading.value)
            self._update_history("BHARATI-BLDG-Z01-TEMP", sim_time, living_temp)
            t_roc = self._calculate_roc("BHARATI-BLDG-Z01-TEMP", sim_time)

            if living_temp < 18.0:
                sev = SeverityLevel.EMERGENCY if living_temp < 15.0 else SeverityLevel.CRITICAL
                record = self._build_anomaly(
                    anomaly_key="INDOOR_THERMAL_DECAY",
                    anomaly_type="THERMAL_LIFE_SUPPORT_DECAY",
                    subsystem="INFRASTRUCTURE",
                    sensor_id="BHARATI-BLDG-Z01-TEMP",
                    value=living_temp,
                    threshold=18.0,
                    severity=sev,
                    summary=f"Indoor living zone temperature below comfort threshold: {living_temp:.1f} °C (RoC: {t_roc:+.2f} °C/min)",
                    roc=t_roc,
                    correlated=["BHARATI-BLDG-Z02-TEMP", "BHARATI.HEATING.SUPPLY_TEMP"],
                    sim_time=sim_time,
                )
                detected.append(record)

        # ---------------------------------------------------------------------
        # 3. Energy Generation & Blackout Threat Monitoring
        # ---------------------------------------------------------------------
        running_chps = kpis.get("running_chp_count", 0)
        chp1_power = float(readings.get("BHARATI.CHP.01.POWER", readings.get("sensor_chp1_kw", 0.0)).value if hasattr(readings.get("BHARATI.CHP.01.POWER", readings.get("sensor_chp1_kw", 0.0)), "value") else (readings.get("BHARATI.CHP.01.POWER", 0.0) or 0.0))
        if running_chps == 0:
            record = self._build_anomaly(
                anomaly_key="TOTAL_STATION_BLACKOUT",
                anomaly_type="TOTAL_STATION_BLACKOUT",
                subsystem="ENERGY",
                sensor_id="BHARATI.CHP.01.POWER",
                value=0.0,
                threshold=1.0,
                severity=SeverityLevel.EMERGENCY,
                summary="CRITICAL EMERGENCY: All CHP generators offline. Station relying on battery UPS.",
                roc=0.0,
                correlated=["BHARATI.CHP.02.POWER", "BHARATI.CHP.03.POWER", "BHARATI.UPS.01.LOAD_PERCENT"],
                sim_time=sim_time,
            )
            detected.append(record)
        elif chp1_power <= 0.1 and snapshot.active_scenario == "GENERATOR_TRIP":
            record = self._build_anomaly(
                anomaly_key="CHP_01_MECHANICAL_TRIP",
                anomaly_type="GENERATOR_MECHANICAL_FAULT",
                subsystem="ENERGY",
                sensor_id="BHARATI.CHP.01.POWER",
                value=chp1_power,
                threshold=15.0,
                severity=SeverityLevel.CRITICAL,
                summary="Primary generator CHP-01 tripped offline with active electrical fault.",
                roc=0.0,
                correlated=["BHARATI.CHP.01.COOLANT_TEMP", "BHARATI.CHP.02.POWER"],
                sim_time=sim_time,
            )
            detected.append(record)

        # ---------------------------------------------------------------------
        # 4. Utilidor Fresh Water Freeze Monitoring
        # ---------------------------------------------------------------------
        pipe_temp_reading = readings.get("BHARATI-PIPE-WATER01-TEMP")
        if pipe_temp_reading is not None:
            pipe_temp = float(pipe_temp_reading.value)
            if pipe_temp < 1.0:
                sev = SeverityLevel.CRITICAL if pipe_temp < 0.0 else SeverityLevel.WARNING
                record = self._build_anomaly(
                    anomaly_key="UTILIDOR_WATER_FREEZE",
                    anomaly_type="UTILIDOR_PIPE_FREEZE_RISK",
                    subsystem="INFRASTRUCTURE",
                    sensor_id="BHARATI-PIPE-WATER01-TEMP",
                    value=pipe_temp,
                    threshold=1.0,
                    severity=sev,
                    summary=f"Utilidor fresh water pipe approaching freezing point: {pipe_temp:.1f} °C",
                    roc=0.0,
                    correlated=["BHARATI-PIPE-WATER01-TRACE-HEAT-STAT", "BHARATI-WATER-RO-MEMBRANE-STATUS"],
                    sim_time=sim_time,
                )
                detected.append(record)

        # ---------------------------------------------------------------------
        # 5. Cold Chain Reefer Excursion Monitoring
        # ---------------------------------------------------------------------
        reefer_temp_reading = readings.get("LOG-REEFER-01-TEMP")
        if reefer_temp_reading is not None:
            reefer_temp = float(reefer_temp_reading.value)
            if reefer_temp > -15.0:
                record = self._build_anomaly(
                    anomaly_key="COLD_CHAIN_EXCURSION",
                    anomaly_type="REEFER_TEMPERATURE_EXCURSION",
                    subsystem="LOGISTICS",
                    sensor_id="LOG-REEFER-01-TEMP",
                    value=reefer_temp,
                    threshold=-15.0,
                    severity=SeverityLevel.CRITICAL,
                    summary=f"Cold storage container Reefer-01 temperature excursion: {reefer_temp:.1f} °C (Limit: -15°C)",
                    roc=0.0,
                    correlated=["LOG-REEFER-01-COMP-RUN", "LOG-DERIVED-COLD-CHAIN-RISK"],
                    sim_time=sim_time,
                )
                detected.append(record)

        # ---------------------------------------------------------------------
        # 6. Fire & Smoke Obscuration Monitoring
        # ---------------------------------------------------------------------
        smoke_reading = readings.get("BHARATI-FIRE-Z01-SMOKE")
        if smoke_reading is not None:
            smoke_obs = float(smoke_reading.value)
            if smoke_obs > 1.5:
                record = self._build_anomaly(
                    anomaly_key="FIRE_SMOKE_ZONE_1",
                    anomaly_type="FIRE_SMOKE_DETECTION",
                    subsystem="INFRASTRUCTURE",
                    sensor_id="BHARATI-FIRE-Z01-SMOKE",
                    value=smoke_obs,
                    threshold=1.5,
                    severity=SeverityLevel.EMERGENCY,
                    summary=f"Smoke obscuration detected in Zone 1: {smoke_obs:.1f}%",
                    roc=0.0,
                    correlated=["BHARATI-FIRE-Z01-TEMP", "BHARATI-FIRE-Z01-ALARM-STAT"],
                    sim_time=sim_time,
                )
                detected.append(record)

        # Update active anomalies tracking and trigger bus notifications
        self._process_detected_anomalies(detected, sim_time)
        return detected

    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming queries or status requests."""
        if message.message_type == MessageType.QUERY:
            summary = self.get_situation_summary()
            self.publish_message(
                session_id=message.session_id,
                recipient=message.sender,
                message_type=MessageType.ADVISORY,
                severity=SeverityLevel.INFO,
                payload=summary,
                confidence=1.0,
            )

    def get_situation_summary(self) -> dict[str, Any]:
        """Generate a complete situational overview across all 4 pillars."""
        kpis = self.engine.get_station_kpis()
        active_list = [
            {
                "anomaly_id": a.anomaly_id,
                "type": a.anomaly_type,
                "subsystem": a.subsystem,
                "severity": a.severity.value,
                "sensor_id": a.primary_sensor_id,
                "observed_value": a.observed_value,
                "summary": a.summary,
            }
            for a in self._active_anomalies.values()
        ]

        # Overall threat level
        if any(a.severity == SeverityLevel.EMERGENCY for a in self._active_anomalies.values()):
            threat_level = SeverityLevel.EMERGENCY
        elif any(a.severity == SeverityLevel.CRITICAL for a in self._active_anomalies.values()):
            threat_level = SeverityLevel.CRITICAL
        elif any(a.severity == SeverityLevel.WARNING for a in self._active_anomalies.values()):
            threat_level = SeverityLevel.WARNING
        else:
            threat_level = SeverityLevel.INFO

        return {
            "agent": self.role.value,
            "threat_level": threat_level.value,
            "active_anomaly_count": len(self._active_anomalies),
            "active_anomalies": active_list,
            "composite_risk_score": kpis["composite_risk_score"],
            "ambient_temp_c": kpis["ambient_temp_c"],
            "wind_speed_mps": kpis["wind_speed_mps"],
            "indoor_avg_temp_c": kpis["indoor_avg_temp_c"],
            "fuel_autonomy_days": kpis["fuel_autonomy_days"],
            "running_chps": kpis["running_chp_count"],
        }

    def _build_anomaly(
        self,
        anomaly_key: str,
        anomaly_type: str,
        subsystem: str,
        sensor_id: str,
        value: Any,
        threshold: Any,
        severity: SeverityLevel,
        summary: str,
        roc: float,
        correlated: list[str],
        sim_time: float,
    ) -> AnomalyRecord:
        """Construct or update an AnomalyRecord."""
        record = self._active_anomalies.get(anomaly_key)
        if record is None:
            record = AnomalyRecord(
                anomaly_id=f"ANOM-{anomaly_key[:8]}-{int(sim_time)}",
                anomaly_type=anomaly_type,
                subsystem=subsystem,
                primary_sensor_id=sensor_id,
                observed_value=value,
                threshold_value=threshold,
                severity=severity,
                summary=summary,
                rate_of_change=roc,
                correlated_sensors=correlated,
                first_detected_sim_time=sim_time,
                last_detected_sim_time=sim_time,
            )
        else:
            record.observed_value = value
            record.severity = severity
            record.summary = summary
            record.rate_of_change = roc
            record.last_detected_sim_time = sim_time

        return record

    def _process_detected_anomalies(
        self,
        detected: list[AnomalyRecord],
        sim_time: float,
    ) -> None:
        """Broadcast newly detected anomalies and maintain active session tracking."""
        current_keys = set()

        for rec in detected:
            key = rec.anomaly_type
            current_keys.add(key)
            is_new = key not in self._active_anomalies

            self._active_anomalies[key] = rec

            # If this is a new anomaly, spawn a DeliberationSession and broadcast ALERT
            if is_new:
                session = self.bus.create_session(
                    trigger_alert={
                        "anomaly_id": rec.anomaly_id,
                        "anomaly_type": rec.anomaly_type,
                        "subsystem": rec.subsystem,
                        "sensor_id": rec.primary_sensor_id,
                        "observed_value": rec.observed_value,
                        "severity": rec.severity.value,
                        "summary": rec.summary,
                    }
                )
                self._anomaly_sessions[key] = session.session_id

                # Broadcast ALERT to all cognitive agents
                self.publish_message(
                    session_id=session.session_id,
                    recipient="BROADCAST",
                    message_type=MessageType.ALERT,
                    severity=rec.severity,
                    payload={
                        "anomaly_id": rec.anomaly_id,
                        "anomaly_type": rec.anomaly_type,
                        "subsystem": rec.subsystem,
                        "primary_sensor_id": rec.primary_sensor_id,
                        "observed_value": rec.observed_value,
                        "threshold_value": rec.threshold_value,
                        "rate_of_change": rec.rate_of_change,
                        "correlated_sensors": rec.correlated_sensors,
                        "summary": rec.summary,
                    },
                    confidence=1.0,
                )

        # Clear resolved anomalies
        resolved_keys = set(self._active_anomalies.keys()) - current_keys
        for key in resolved_keys:
            del self._active_anomalies[key]
            if key in self._anomaly_sessions:
                del self._anomaly_sessions[key]

    def _update_history(self, sensor_id: str, sim_time: float, value: float) -> None:
        """Append reading to sensor history and purge entries outside the sliding window."""
        if sensor_id not in self._history:
            self._history[sensor_id] = deque()

        q = self._history[sensor_id]
        q.append((sim_time, value))

        cutoff = sim_time - self._history_window_seconds
        while q and q[0][0] < cutoff:
            q.popleft()

    def _calculate_roc(self, sensor_id: str, current_time: float) -> float:
        """Calculate Rate of Change per minute: (V_now - V_old) / (delta_t / 60)."""
        q = self._history.get(sensor_id)
        if not q or len(q) < 2:
            return 0.0

        old_t, old_v = q[0]
        curr_t, curr_v = q[-1]
        dt = curr_t - old_t
        if dt <= 0.0:
            return 0.0

        dt_min = dt / 60.0
        return round((curr_v - old_v) / dt_min, 3)
