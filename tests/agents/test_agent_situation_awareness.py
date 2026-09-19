"""Unit and Integration Tests for Situation Awareness Agent (Sub-Phase 3.1).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Initialization & Zero False Alarms in Steady State
2. Severe Katabatic Blizzard Wind Detection & Alert Broadcasting
3. Indoor Thermal Life-Support Decay Detection & Rate-of-Change Tracking
4. Total Station Blackout Emergency Detection
5. Utilidor Fresh Water Line Freeze Threat Detection
6. Cold Chain Reefer Temperature Excursion Detection
7. Interactive Query-Response for Station Situational Overview
"""

import pytest

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.models import (
    AgentMessage,
    AgentRole,
    MessageType,
    SeverityLevel,
)
from backend.agents.specialized.situation_awareness import SituationAwarenessAgent
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine, MasterScenario


class TestSituationAwarenessAgent:
    """Test suite for SituationAwarenessAgent."""

    @pytest.fixture
    def setup_agent(self) -> tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]:
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()
        agent = SituationAwarenessAgent(bus, engine, graph)
        return agent, bus, engine

    def test_initialization_and_steady_state(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify agent initializes cleanly with zero active anomalies under nominal conditions."""
        agent, bus, engine = setup_agent
        assert agent.role == AgentRole.SITUATION_AWARENESS

        # Nominal snapshot
        snap = engine.get_snapshot()
        detected = agent.scan_telemetry(snap)

        assert len(detected) == 0
        summary = agent.get_situation_summary()
        assert summary["threat_level"] == "INFO"
        assert summary["active_anomaly_count"] == 0

    def test_blizzard_wind_detection_and_alert_broadcast(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify katabatic blizzard wind surge creates a session and broadcasts an ALERT."""
        agent, bus, engine = setup_agent

        # Listen for alerts on the bus
        received_alerts: list[AgentMessage] = []
        bus.subscribe_type(MessageType.ALERT, lambda m: received_alerts.append(m))

        # Inject blizzard strike
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)
        snap = engine.step(60.0)

        detected = agent.scan_telemetry(snap)
        assert len(detected) >= 1

        blizzard_anom = next((a for a in detected if a.anomaly_type == "KATABATIC_BLIZZARD_SURGE"), None)
        assert blizzard_anom is not None
        assert blizzard_anom.observed_value >= 30.0
        assert blizzard_anom.severity in (SeverityLevel.CRITICAL, SeverityLevel.EMERGENCY)

        # Verify broadcast on the bus
        assert len(received_alerts) >= 1
        alert_msg = received_alerts[0]
        assert alert_msg.message_type == MessageType.ALERT
        assert alert_msg.sender == AgentRole.SITUATION_AWARENESS
        assert alert_msg.recipient == "BROADCAST"
        assert alert_msg.payload["anomaly_type"] == "KATABATIC_BLIZZARD_SURGE"

        # Verify DeliberationSession created
        session = bus.get_session(alert_msg.session_id)
        assert session is not None
        assert session.trigger_alert["anomaly_type"] == "KATABATIC_BLIZZARD_SURGE"

    def test_indoor_thermal_decay_detection(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify indoor thermal decay below comfort levels is detected with RoC."""
        agent, bus, engine = setup_agent

        # Simulate living temperature drop
        engine.infra_registry.physics.building.temp_living_c = 15.5
        engine._refresh_all_readings()
        snap = engine.get_snapshot()

        detected = agent.scan_telemetry(snap)
        thermal_anom = next((a for a in detected if a.anomaly_type == "THERMAL_LIFE_SUPPORT_DECAY"), None)
        assert thermal_anom is not None
        assert thermal_anom.observed_value == 15.5
        assert thermal_anom.severity == SeverityLevel.CRITICAL

    def test_total_station_blackout_emergency(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify zero running CHPs triggers an immediate EMERGENCY blackout alert."""
        agent, bus, engine = setup_agent

        # Shut down all CHPs
        for chp in engine.energy_registry.physics.chps:
            chp.operating_state = "OFF"
            chp.running_status = False

        engine._refresh_all_readings()
        snap = engine.get_snapshot()

        detected = agent.scan_telemetry(snap)
        blackout_anom = next((a for a in detected if a.anomaly_type == "TOTAL_STATION_BLACKOUT"), None)
        assert blackout_anom is not None
        assert blackout_anom.severity == SeverityLevel.EMERGENCY

    def test_utilidor_freeze_risk_detection(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify fresh water pipe freezing triggers an anomaly alert."""
        agent, bus, engine = setup_agent

        # Inject water line freeze
        engine.inject_scenario(MasterScenario.WATER_LINE_FREEZE)
        snap = engine.step(10.0)

        detected = agent.scan_telemetry(snap)
        freeze_anom = next((a for a in detected if a.anomaly_type == "UTILIDOR_PIPE_FREEZE_RISK"), None)
        assert freeze_anom is not None
        assert freeze_anom.observed_value < 0.0

    def test_cold_chain_excursion_detection(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify reefer container temperature excursion is detected."""
        agent, bus, engine = setup_agent

        # Inject cold chain excursion
        engine.inject_scenario(MasterScenario.COLD_CHAIN_EXCURSION)
        snap = engine.step(10.0)

        detected = agent.scan_telemetry(snap)
        reefer_anom = next((a for a in detected if a.anomaly_type == "REEFER_TEMPERATURE_EXCURSION"), None)
        assert reefer_anom is not None
        assert reefer_anom.observed_value > -15.0

    def test_interactive_query_response(
        self, setup_agent: tuple[SituationAwarenessAgent, AgentMessageBus, BharatiMasterTwinEngine]
    ) -> None:
        """Verify agent responds to operational query messages with a situation summary."""
        agent, bus, engine = setup_agent

        responses: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.FRIDAY_ORCHESTRATOR, lambda m: responses.append(m))

        query_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient=AgentRole.SITUATION_AWARENESS,
            message_type=MessageType.QUERY,
            severity=SeverityLevel.INFO,
            payload={"request": "STATION_SITUATION_SUMMARY"},
            session_id="SES-QUERY-TEST",
        )
        bus.publish(query_msg)

        assert len(responses) == 1
        resp = responses[0]
        assert resp.message_type == MessageType.ADVISORY
        assert resp.payload["agent"] == "SITUATION_AWARENESS"
        assert "composite_risk_score" in resp.payload
        assert "indoor_avg_temp_c" in resp.payload
