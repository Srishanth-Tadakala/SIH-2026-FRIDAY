"""Test Suite for NOAA Space Weather & Polar Ionospheric Ingestion Engine.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies:
1. Space Weather baseline metrics and G/S/R scale resolution.
2. Polar Cap Absorption (PCA) & 30MHz Riometer attenuation models.
3. Digital twin sensor override injection.
4. Geomagnetic storm drill simulation and message bus alerting.
5. REST API endpoints for environmental space weather.
"""

from __future__ import annotations

from typing import Any
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.bus import AgentMessageBus
from backend.core.engine import BharatiMasterTwinEngine
from backend.environmental.space_weather import (
    GeomagneticStormScale,
    RadioBlackoutScale,
    SolarRadiationScale,
    SpaceWeatherConfig,
    SpaceWeatherFeedEngine,
    SpaceWeatherMetrics,
)
from backend.server.app import create_app
from backend.server.state import reset_server_state


def test_space_weather_config_and_baseline() -> None:
    """Verify SpaceWeatherFeedEngine configuration defaults and baseline model."""
    config = SpaceWeatherConfig(station_id="bharati", enable_live_poll=False)
    assert config.poll_interval_seconds == 300.0
    assert config.storm_threshold_kp == 5.0

    engine = SpaceWeatherFeedEngine(config=config)
    metrics = engine.get_latest_metrics()
    assert 0.0 <= metrics.kp_index <= 9.0
    assert metrics.solar_wind_speed_kms > 300.0
    assert metrics.auroral_absorption_db >= 0.0
    assert metrics.is_synthetic is True

    status = engine.get_status()
    assert status["status"] == "STOPPED"
    assert status["station_id"] == "bharati"
    assert "current_metrics" in status


def test_space_weather_scale_mappings() -> None:
    """Verify conversion of Kp and NOAA levels to typed G/S/R scales."""
    engine = SpaceWeatherFeedEngine()

    # G-scale
    assert engine._map_g_scale("0", 2.0) == GeomagneticStormScale.G0_NONE
    assert engine._map_g_scale("1", 5.0) == GeomagneticStormScale.G1_MINOR
    assert engine._map_g_scale("2", 6.0) == GeomagneticStormScale.G2_MODERATE
    assert engine._map_g_scale("3", 7.0) == GeomagneticStormScale.G3_STRONG
    assert engine._map_g_scale("4", 8.0) == GeomagneticStormScale.G4_SEVERE
    assert engine._map_g_scale("5", 9.0) == GeomagneticStormScale.G5_EXTREME

    # S-scale
    assert engine._map_s_scale("0") == SolarRadiationScale.S0_NONE
    assert engine._map_s_scale("2") == SolarRadiationScale.S2_MODERATE
    assert engine._map_s_scale("5") == SolarRadiationScale.S5_EXTREME

    # R-scale
    assert engine._map_r_scale("0") == RadioBlackoutScale.R0_NONE
    assert engine._map_r_scale("3") == RadioBlackoutScale.R3_STRONG


@pytest.mark.asyncio
async def test_space_weather_twin_telemetry_injection() -> None:
    """Verify poll_now injects space weather points into Bharati twin engine."""
    twin = BharatiMasterTwinEngine()
    config = SpaceWeatherConfig(enable_live_poll=False)
    engine = SpaceWeatherFeedEngine(config=config, engine=twin)

    metrics = await engine.poll_now()
    assert metrics is not None

    readings = twin.get_all_readings()
    assert "BHARATI.ENV.KP_INDEX" in readings
    assert "BHARATI.ENV.SOLAR_WIND_SPEED" in readings
    assert "BHARATI.SATCOM.IONO_ATTENUATION_DB" in readings

    kp_reading = readings["BHARATI.ENV.KP_INDEX"]
    val = kp_reading.value if hasattr(kp_reading, "value") else kp_reading.get("value")
    assert abs(float(val) - metrics.kp_index) < 0.01


def test_geomagnetic_storm_simulation_and_alerting() -> None:
    """Verify storm simulation elevates metrics and publishes broadcast alert to bus."""
    bus = AgentMessageBus()
    alerts_received = []

    def on_alert(msg: Any) -> None:
        alerts_received.append(msg)

    from backend.agents.framework.models import MessageType
    bus.subscribe_type(MessageType.ALERT, on_alert)

    twin = BharatiMasterTwinEngine()
    engine = SpaceWeatherFeedEngine(engine=twin, bus=bus)

    # Trigger G4 Severe Storm
    storm = engine.simulate_geomagnetic_storm(g_level="G4")
    assert storm.geomagnetic_scale == GeomagneticStormScale.G4_SEVERE
    assert storm.kp_index == 8.0
    assert storm.satcom_hf_attenuation_risk in ("ELEVATED", "CRITICAL_BLACKOUT")
    assert storm.auroral_absorption_db > 5.0

    # Verify alert published to message bus
    assert len(alerts_received) >= 1
    last_alert = alerts_received[-1]
    assert "G4_SEVERE" in last_alert.payload["title"]
    assert last_alert.payload["kp_index"] == 8.0


def test_space_weather_rest_api() -> None:
    """Verify /api/environmental/space-weather REST endpoints."""
    reset_server_state()
    app = create_app()
    client = TestClient(app)

    # 1. GET Current Metrics
    resp_cur = client.get("/api/environmental/space-weather/current")
    assert resp_cur.status_code == 200
    cur_data = resp_cur.json()
    assert "kp_index" in cur_data
    assert "geomagnetic_scale" in cur_data
    assert "satcom_hf_attenuation_risk" in cur_data

    # 2. GET Engine Status
    resp_stat = client.get("/api/environmental/space-weather/status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert stat_data["station_id"] == "bharati"
    assert "total_polls" in stat_data

    # 3. POST Trigger Poll
    resp_poll = client.post("/api/environmental/space-weather/poll")
    assert resp_poll.status_code == 200
    poll_data = resp_poll.json()
    assert poll_data["status"] == "SUCCESS"
    assert "metrics" in poll_data

    # 4. POST Simulate Storm (Valid G5 Extreme)
    resp_storm = client.post(
        "/api/environmental/space-weather/simulate-storm",
        json={"g_level": "G5"},
    )
    assert resp_storm.status_code == 200
    storm_data = resp_storm.json()
    assert storm_data["status"] == "STORM_INJECTED"
    assert storm_data["scenario"] == "G5"
    assert storm_data["metrics"]["kp_index"] == 9.0

    # 5. POST Simulate Storm (Invalid Level -> 400 Bad Request)
    resp_bad = client.post(
        "/api/environmental/space-weather/simulate-storm",
        json={"g_level": "INVALID_STORM"},
    )
    assert resp_bad.status_code == 400
