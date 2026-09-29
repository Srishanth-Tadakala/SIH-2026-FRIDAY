"""Test Suite for Antarctic Mesoscale Prediction System (AMPS) Weather Engine.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies:
1. Antarctic Wind Chill Index calculation and polar climatology baseline.
2. Expedition safety condition classification (Condition 1, 2, and 3).
3. 24-hour polar numerical weather forecast generation.
4. Digital twin telemetry injection into Bharati master engine.
5. Simulated polar blizzard injection and station lockout alerting.
6. REST API endpoints for AMPS weather and forecasts.
"""

from __future__ import annotations

from typing import Any
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.bus import AgentMessageBus
from backend.core.engine import BharatiMasterTwinEngine
from backend.environmental.amps_weather import (
    AmpsWeatherEngine,
    PolarForecastHour,
    PolarSafetyCondition,
    PolarWeatherConfig,
    PolarWeatherObservation,
)
from backend.server.app import create_app
from backend.server.state import reset_server_state


def test_amps_weather_config_and_baseline() -> None:
    """Verify AMPS engine defaults and baseline observation."""
    config = PolarWeatherConfig(station_id="bharati", enable_live_poll=False)
    assert config.poll_interval_seconds == 300.0
    assert config.cond_1_wind_ms == 28.0

    engine = AmpsWeatherEngine(config=config)
    obs = engine.get_current_observation()
    assert obs.station_id == "bharati"
    assert -50.0 <= obs.temperature_c <= 10.0
    assert obs.wind_speed_ms >= 0.0
    assert obs.wind_chill_c <= obs.temperature_c
    assert obs.safety_condition in (
        PolarSafetyCondition.CONDITION_3_NORMAL,
        PolarSafetyCondition.CONDITION_2_WARNING,
        PolarSafetyCondition.CONDITION_1_LOCKOUT,
    )

    status = engine.get_status()
    assert status["status"] == "STOPPED"
    assert status["station_id"] == "bharati"
    assert "current_observation" in status


def test_polar_wind_chill_formula() -> None:
    """Verify Antarctic Wind Chill formula calculations."""
    engine = AmpsWeatherEngine()

    # At -20°C with 15 m/s (54 km/h) wind
    chill_1 = engine.calculate_wind_chill(temp_c=-20.0, wind_ms=15.0)
    assert chill_1 < -30.0

    # At -35°C with 30 m/s (108 km/h) wind
    chill_2 = engine.calculate_wind_chill(temp_c=-35.0, wind_ms=30.0)
    assert chill_2 < -55.0

    # Low wind shouldn't exceed air temp
    chill_calm = engine.calculate_wind_chill(temp_c=-10.0, wind_ms=0.5)
    assert chill_calm <= -10.0


def test_safety_condition_classification() -> None:
    """Verify Condition 1, 2, and 3 classifications based on wind, chill, and visibility."""
    engine = AmpsWeatherEngine()

    # Condition 3: Normal
    cond_norm = engine.evaluate_safety_condition(
        temp_c=-15.0, wind_ms=10.0, visibility_m=8000.0, wind_chill_c=-24.0
    )
    assert cond_norm == PolarSafetyCondition.CONDITION_3_NORMAL

    # Condition 2: Hazardous (Wind 22 m/s)
    cond_warn = engine.evaluate_safety_condition(
        temp_c=-22.0, wind_ms=22.0, visibility_m=400.0, wind_chill_c=-38.0
    )
    assert cond_warn == PolarSafetyCondition.CONDITION_2_WARNING

    # Condition 1: Lockout (Severe blizzard: wind 32 m/s, visibility 50m)
    cond_lock = engine.evaluate_safety_condition(
        temp_c=-35.0, wind_ms=32.0, visibility_m=50.0, wind_chill_c=-62.0
    )
    assert cond_lock == PolarSafetyCondition.CONDITION_1_LOCKOUT


def test_amps_forecast_generation() -> None:
    """Verify 24-hour hourly AMPS forecast series."""
    engine = AmpsWeatherEngine()
    forecast = engine.get_forecast()
    assert len(forecast) == 24

    for i, hour in enumerate(forecast, start=1):
        assert hour.hour_offset == i
        assert -60.0 <= hour.temperature_c <= 15.0
        assert hour.wind_speed_ms >= 0.0
        assert hour.wind_chill_c <= hour.temperature_c
        assert isinstance(hour.safety_condition, PolarSafetyCondition)


@pytest.mark.asyncio
async def test_amps_twin_telemetry_injection() -> None:
    """Verify poll_now injects polar weather readings into twin engine."""
    twin = BharatiMasterTwinEngine()
    engine = AmpsWeatherEngine(engine=twin)

    obs = await engine.poll_now()
    readings = twin.get_all_readings()

    assert "BHARATI.ENV.OUTSIDE_TEMP" in readings
    assert "BHARATI.ENV.WIND_SPEED" in readings
    assert "BHARATI.ENV.WIND_CHILL" in readings
    assert "BHARATI.ENV.PRESSURE_HPA" in readings

    temp_reading = readings["BHARATI.ENV.OUTSIDE_TEMP"]
    val = temp_reading.value if hasattr(temp_reading, "value") else temp_reading.get("value")
    assert abs(float(val) - obs.temperature_c) < 0.01


def test_polar_blizzard_simulation_and_alerting() -> None:
    """Verify blizzard drill simulation triggers Condition 1 Lockout alert on message bus."""
    bus = AgentMessageBus()
    alerts_received = []

    def on_alert(msg: Any) -> None:
        alerts_received.append(msg)

    from backend.agents.framework.models import MessageType
    bus.subscribe_type(MessageType.ALERT, on_alert)

    twin = BharatiMasterTwinEngine()
    engine = AmpsWeatherEngine(engine=twin, bus=bus)

    # Trigger Condition 1 Lockout Blizzard
    blizzard = engine.simulate_polar_blizzard(condition="CONDITION_1_LOCKOUT")
    assert blizzard.safety_condition == PolarSafetyCondition.CONDITION_1_LOCKOUT
    assert blizzard.wind_speed_ms > 30.0
    assert blizzard.visibility_meters < 100.0
    assert blizzard.blizzard_imminent is True

    # Verify high-priority alert broadcast
    assert len(alerts_received) >= 1
    alert = alerts_received[-1]
    assert "CONDITION_1_LOCKOUT" in alert.payload["title"]
    assert "LOCKOUT" in alert.payload["mandatory_action"]


def test_amps_weather_rest_api() -> None:
    """Verify /api/environmental/weather REST endpoints."""
    reset_server_state()
    app = create_app()
    client = TestClient(app)

    # 1. GET Current Weather
    resp_cur = client.get("/api/environmental/weather/current")
    assert resp_cur.status_code == 200
    cur_data = resp_cur.json()
    assert "temperature_c" in cur_data
    assert "wind_speed_ms" in cur_data
    assert "safety_condition" in cur_data

    # 2. GET 24-Hour Forecast
    resp_fc = client.get("/api/environmental/weather/forecast")
    assert resp_fc.status_code == 200
    fc_data = resp_fc.json()
    assert fc_data["hours_count"] == 24
    assert len(fc_data["forecast"]) == 24

    # 3. GET Weather Status
    resp_stat = client.get("/api/environmental/weather/status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert stat_data["station_id"] == "bharati"
    assert "current_observation" in stat_data

    # 4. POST Trigger Poll
    resp_poll = client.post("/api/environmental/weather/poll")
    assert resp_poll.status_code == 200
    poll_data = resp_poll.json()
    assert poll_data["status"] == "SUCCESS"
    assert "observation" in poll_data

    # 5. POST Simulate Blizzard (Valid Condition 1)
    resp_blizz = client.post(
        "/api/environmental/weather/simulate-blizzard",
        json={"condition": "CONDITION_1_LOCKOUT"},
    )
    assert resp_blizz.status_code == 200
    blizz_data = resp_blizz.json()
    assert blizz_data["status"] == "BLIZZARD_INJECTED"
    assert blizz_data["condition"] == "CONDITION_1_LOCKOUT"

    # 6. POST Simulate Blizzard (Invalid Condition -> 400 Bad Request)
    resp_bad = client.post(
        "/api/environmental/weather/simulate-blizzard",
        json={"condition": "SUNNY_DAY"},
    )
    assert resp_bad.status_code == 400
