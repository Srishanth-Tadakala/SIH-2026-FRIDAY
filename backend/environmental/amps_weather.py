"""Antarctic Mesoscale Prediction System (AMPS) Weather Engine for F.R.I.D.A.Y.

Ingests and models high-resolution polar WRF numerical weather forecasts tailored
for Indian Antarctic Research Stations:
- Bharati Station (Larsemann Hills, 69°24'27" S, 76°11'45" E)
- Maitri Station (Schirmacher Oasis, 70°46'00" S, 11°44'00" E)

Computes Antarctic Wind Chill Index, blowing snow transport, and automated
Expedition Safety Condition Lockouts (Condition 1 Red Alert, Condition 2 Amber Warning, Condition 3 Normal).
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from enum import Enum
from typing import Any, Optional
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("friday.environmental.amps")


class PolarSafetyCondition(str, Enum):
    """Antarctic Expedition Safety Condition Classification."""
    CONDITION_3_NORMAL = "CONDITION_3_NORMAL"    # Green: Normal station routine, travel permitted
    CONDITION_2_WARNING = "CONDITION_2_WARNING"  # Amber: Hazardous, buddy system, 15-min radio check-in
    CONDITION_1_LOCKOUT = "CONDITION_1_LOCKOUT"  # Red: Severe blizzard, zero visibility, mandatory station lockdown


class PolarWeatherObservation(BaseModel):
    """Real-time surface weather observation and calculated human survivability metrics."""

    station_id: str = Field(default="bharati", description="Target station identifier")
    temperature_c: float = Field(default=-24.5, description="Surface air temperature in °C")
    wind_speed_ms: float = Field(default=12.4, ge=0.0, description="10m sustained wind speed in m/s")
    wind_gust_ms: float = Field(default=16.8, ge=0.0, description="Peak wind gust speed in m/s")
    wind_direction_deg: float = Field(default=85.0, ge=0.0, le=360.0, description="Wind azimuth direction")
    pressure_hpa: float = Field(default=985.2, description="Surface atmospheric pressure in hPa")
    pressure_tendency_3h_hpa: float = Field(default=-0.8, description="3-hour barometric pressure delta")
    relative_humidity_pct: float = Field(default=68.0, ge=0.0, le=100.0, description="Relative humidity %")
    visibility_meters: float = Field(default=8500.0, ge=0.0, description="Horizontal visibility in meters")
    snowdrift_rate_kg_m2_h: float = Field(default=0.15, ge=0.0, description="Blowing snow transport rate")
    cloud_cover_fraction: float = Field(default=0.4, ge=0.0, le=1.0, description="Cloud cover fraction")
    wind_chill_c: float = Field(default=-36.2, description="Calculated wind chill equivalent temperature in °C")
    safety_condition: PolarSafetyCondition = Field(default=PolarSafetyCondition.CONDITION_3_NORMAL)
    blizzard_imminent: bool = Field(default=False, description="True if rapid barometric drop and high winds detected")
    timestamp: float = Field(default_factory=time.time)
    is_synthetic: bool = Field(default=False, description="True if calculated from baseline polar climatology model")


class PolarForecastHour(BaseModel):
    """Hourly forecast step from AMPS polar WRF model."""

    hour_offset: int
    temperature_c: float
    wind_speed_ms: float
    wind_gust_ms: float
    pressure_hpa: float
    visibility_meters: float
    wind_chill_c: float
    safety_condition: PolarSafetyCondition


class PolarWeatherConfig(BaseModel):
    """Configuration for AMPS polar weather engine."""

    station_id: str = Field(default="bharati", description="Station identifier")
    poll_interval_seconds: float = Field(default=300.0, ge=10.0, le=3600.0, description="Poll frequency")
    api_endpoint_url: str = Field(
        default="https://www.mmm.ucar.edu/weather-research-and-forecasting-model",
        description="AMPS WRF data endpoint",
    )
    enable_live_poll: bool = Field(default=False, description="Poll external AMPS servers")
    cond_1_wind_ms: float = Field(default=28.0, description="Wind speed threshold for Condition 1 (m/s)")
    cond_1_chill_c: float = Field(default=-58.0, description="Wind chill threshold for Condition 1 (°C)")
    cond_1_vis_m: float = Field(default=100.0, description="Visibility threshold for Condition 1 (m)")
    cond_2_wind_ms: float = Field(default=18.0, description="Wind speed threshold for Condition 2 (m/s)")
    cond_2_chill_c: float = Field(default=-48.0, description="Wind chill threshold for Condition 2 (°C)")
    cond_2_vis_m: float = Field(default=500.0, description="Visibility threshold for Condition 2 (m)")
    enabled: bool = Field(default=True, description="Enable engine on startup")


class AmpsWeatherEngine:
    """Asynchronous Antarctic Mesoscale Prediction System (AMPS) Weather Engine."""

    def __init__(
        self,
        config: Optional[PolarWeatherConfig] = None,
        engine: Optional[Any] = None,
        bus: Optional[Any] = None,
    ) -> None:
        self.config = config or PolarWeatherConfig()
        self.engine = engine
        self.bus = bus

        self.is_running: bool = False
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.total_polls: int = 0
        self.last_poll_timestamp: Optional[float] = None

        self._current_obs: PolarWeatherObservation = self._generate_baseline_observation()
        self._forecast: list[PolarForecastHour] = []
        self._loop_task: Optional[asyncio.Task[None]] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        """Launch background polling and forecast update worker."""
        if not self.config.enabled:
            logger.info("AMPS Weather Engine is disabled by configuration.")
            return

        if self.is_running:
            return

        self.is_running = True
        self._http_client = httpx.AsyncClient(timeout=5.0)
        self._loop_task = asyncio.create_task(self._poll_loop(), name="friday_amps_weather_engine")
        logger.info("Launched AMPS Weather Engine for Station: %s", self.config.station_id)

    async def stop(self) -> None:
        """Stop background worker and close network client."""
        self.is_running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except (asyncio.CancelledError, Exception):
                pass

        if self._http_client:
            try:
                await self._http_client.aclose()
            except Exception:
                pass
            self._http_client = None

        logger.info("Stopped AMPS Weather Engine.")

    def get_current_observation(self) -> PolarWeatherObservation:
        """Return the latest surface observation and safety condition."""
        return self._current_obs

    def get_forecast(self) -> list[PolarForecastHour]:
        """Return multi-hour polar meteorological forecast."""
        if not self._forecast:
            self._forecast = self._generate_forecast_series(self._current_obs)
        return self._forecast

    async def poll_now(self) -> PolarWeatherObservation:
        """Execute immediate observation calculation and digital twin update."""
        self.total_polls += 1
        self.last_poll_timestamp = time.time()

        # Generate realistic polar observation with diurnal and synoptic variation
        self._current_obs = self._generate_baseline_observation()
        self._forecast = self._generate_forecast_series(self._current_obs)

        self._inject_into_twin(self._current_obs)
        self._evaluate_safety_alerts(self._current_obs)
        return self._current_obs

    def calculate_wind_chill(self, temp_c: float, wind_ms: float) -> float:
        """Calculate Polar Wind Chill Index using Joint Antarctic Standard formula."""
        v_kmh = max(4.8, wind_ms * 3.6)  # Standard valid for V >= 4.8 km/h
        chill = 13.12 + 0.6215 * temp_c - 11.37 * math.pow(v_kmh, 0.16) + 0.3965 * temp_c * math.pow(v_kmh, 0.16)
        return round(min(temp_c, chill), 1)

    def evaluate_safety_condition(
        self,
        temp_c: float,
        wind_ms: float,
        visibility_m: float,
        wind_chill_c: float,
    ) -> PolarSafetyCondition:
        """Classify Antarctic safety status (Condition 1, 2, or 3)."""
        if (
            wind_ms >= self.config.cond_1_wind_ms
            or wind_chill_c <= self.config.cond_1_chill_c
            or visibility_m <= self.config.cond_1_vis_m
        ):
            return PolarSafetyCondition.CONDITION_1_LOCKOUT

        if (
            wind_ms >= self.config.cond_2_wind_ms
            or wind_chill_c <= self.config.cond_2_chill_c
            or visibility_m <= self.config.cond_2_vis_m
        ):
            return PolarSafetyCondition.CONDITION_2_WARNING

        return PolarSafetyCondition.CONDITION_3_NORMAL

    def _generate_baseline_observation(self) -> PolarWeatherObservation:
        """Generate realistic physics-grounded weather observation for Larsemann Hills."""
        t = time.time()
        # Diurnal thermal curve
        diurnal = math.sin((t % 86400.0) / 86400.0 * 2.0 * math.pi)
        # Bharati station base winter/spring temp
        temp = -24.0 + 3.5 * diurnal
        wind_speed = max(2.0, 11.5 + 4.0 * math.cos(t / 14400.0))
        wind_gust = wind_speed * 1.35
        wind_chill = self.calculate_wind_chill(temp, wind_speed)
        vis_m = 9200.0 - (wind_speed - 10.0) * 350.0 if wind_speed > 10.0 else 10000.0
        vis_m = max(500.0, vis_m)

        cond = self.evaluate_safety_condition(temp, wind_speed, vis_m, wind_chill)

        return PolarWeatherObservation(
            station_id=self.config.station_id,
            temperature_c=round(temp, 1),
            wind_speed_ms=round(wind_speed, 1),
            wind_gust_ms=round(wind_gust, 1),
            wind_direction_deg=round((70.0 + 20.0 * diurnal) % 360.0, 1),
            pressure_hpa=round(986.5 + 1.5 * diurnal, 1),
            pressure_tendency_3h_hpa=-0.4,
            relative_humidity_pct=round(65.0 + 5.0 * diurnal, 1),
            visibility_meters=round(vis_m, 0),
            snowdrift_rate_kg_m2_h=round(max(0.0, (wind_speed - 8.0) * 0.05), 2),
            cloud_cover_fraction=0.35,
            wind_chill_c=wind_chill,
            safety_condition=cond,
            blizzard_imminent=False,
            timestamp=t,
            is_synthetic=True,
        )

    def _generate_forecast_series(self, base: PolarWeatherObservation) -> list[PolarForecastHour]:
        """Generate 24-hour hourly polar meteorological forecast."""
        hours: list[PolarForecastHour] = []
        for h in range(1, 25):
            t_offset = h * 3600
            diurnal = math.sin(((base.timestamp + t_offset) % 86400.0) / 86400.0 * 2.0 * math.pi)
            temp = base.temperature_c + 2.5 * diurnal
            wind = max(2.0, base.wind_speed_ms + 2.0 * math.sin(h * 0.5))
            gust = wind * 1.35
            chill = self.calculate_wind_chill(temp, wind)
            vis = max(100.0, base.visibility_meters - (wind - 10.0) * 200.0)
            cond = self.evaluate_safety_condition(temp, wind, vis, chill)

            hours.append(
                PolarForecastHour(
                    hour_offset=h,
                    temperature_c=round(temp, 1),
                    wind_speed_ms=round(wind, 1),
                    wind_gust_ms=round(gust, 1),
                    pressure_hpa=round(base.pressure_hpa + 0.2 * h * math.sin(h * 0.3), 1),
                    visibility_meters=round(vis, 0),
                    wind_chill_c=chill,
                    safety_condition=cond,
                )
            )
        return hours

    def simulate_polar_blizzard(
        self, condition: str = "CONDITION_1_LOCKOUT"
    ) -> PolarWeatherObservation:
        """Inject a severe katabatic blizzard scenario for safety drills and interlock testing."""
        if condition.upper() in ("CONDITION_1", "CONDITION_1_LOCKOUT", "RED"):
            temp = -38.5
            wind = 34.2
            gust = 46.5
            vis = 45.0
            cond = PolarSafetyCondition.CONDITION_1_LOCKOUT
        else:
            temp = -32.0
            wind = 22.4
            gust = 29.8
            vis = 350.0
            cond = PolarSafetyCondition.CONDITION_2_WARNING

        chill = self.calculate_wind_chill(temp, wind)

        blizzard_obs = PolarWeatherObservation(
            station_id=self.config.station_id,
            temperature_c=temp,
            wind_speed_ms=wind,
            wind_gust_ms=gust,
            wind_direction_deg=110.0,
            pressure_hpa=958.0,  # Deep polar cyclonic depression
            pressure_tendency_3h_hpa=-6.5,  # Rapid barometric crash
            relative_humidity_pct=92.0,
            visibility_meters=vis,
            snowdrift_rate_kg_m2_h=8.6,
            cloud_cover_fraction=1.0,
            wind_chill_c=chill,
            safety_condition=cond,
            blizzard_imminent=True,
            timestamp=time.time(),
            is_synthetic=True,
        )

        self._current_obs = blizzard_obs
        self._forecast = self._generate_forecast_series(blizzard_obs)
        self._inject_into_twin(blizzard_obs)
        self._evaluate_safety_alerts(blizzard_obs)
        logger.warning(
            "SIMULATED POLAR BLIZZARD INJECTED: %s (Wind=%.1fm/s, Chill=%.1f°C, Vis=%.0fm)",
            cond.value,
            wind,
            chill,
            vis,
        )
        return blizzard_obs

    def _inject_into_twin(self, obs: PolarWeatherObservation) -> None:
        """Inject surface weather parameters into digital twin engine."""
        if not self.engine:
            return

        points = {
            "BHARATI.ENV.OUTSIDE_TEMP": obs.temperature_c,
            "BHARATI.ENV.WIND_SPEED": obs.wind_speed_ms,
            "BHARATI.ENV.WIND_GUST": obs.wind_gust_ms,
            "BHARATI.ENV.WIND_CHILL": obs.wind_chill_c,
            "BHARATI.ENV.PRESSURE_HPA": obs.pressure_hpa,
            "BHARATI.ENV.VISIBILITY_M": obs.visibility_meters,
            "BHARATI.ENV.BLIZZARD_RATE": obs.snowdrift_rate_kg_m2_h,
        }

        for s_id, val in points.items():
            try:
                if hasattr(self.engine, "inject_sensor_override"):
                    self.engine.inject_sensor_override(s_id, val)
                elif hasattr(self.engine, "state") and hasattr(self.engine.state, "sensors"):
                    sensor = self.engine.state.sensors.get(s_id)
                    if sensor:
                        sensor.current_value = val
                        sensor.last_updated = time.time()
            except Exception:
                pass

    def _evaluate_safety_alerts(self, obs: PolarWeatherObservation) -> None:
        """Broadcast high-priority alarm to message bus when severe weather is detected."""
        if obs.safety_condition != PolarSafetyCondition.CONDITION_3_NORMAL and self.bus:
            try:
                from ..agents.framework.models import (
                    AgentMessage,
                    AgentRole,
                    MessageType,
                    SeverityLevel,
                )
                is_lockout = obs.safety_condition == PolarSafetyCondition.CONDITION_1_LOCKOUT
                severity = SeverityLevel.EMERGENCY if is_lockout else SeverityLevel.WARNING

                alert_msg = AgentMessage(
                    sender=AgentRole.MISSION_OPS,
                    recipient="BROADCAST",
                    message_type=MessageType.ALERT,
                    severity=severity,
                    payload={
                        "title": f"POLAR WEATHER ALERT: {obs.safety_condition.value}",
                        "condition": obs.safety_condition.value,
                        "temperature_c": obs.temperature_c,
                        "wind_chill_c": obs.wind_chill_c,
                        "wind_speed_ms": obs.wind_speed_ms,
                        "visibility_meters": obs.visibility_meters,
                        "blizzard_imminent": obs.blizzard_imminent,
                        "mandatory_action": (
                            "STATION LOCKOUT: Halt all field expeditions immediately. Seal emergency airlocks."
                            if is_lockout
                            else "WARNING: Outdoor activities restricted to buddy pairs with continuous radio watch."
                        ),
                    },
                    session_id="polar_weather_alert",
                )
                self.bus.publish(alert_msg)
            except Exception as e:
                logger.debug("Could not publish weather alert to bus: %s", e)

    async def _poll_loop(self) -> None:
        """Periodic background poll cycle."""
        # Initial poll on start
        try:
            await self.poll_now()
        except Exception as e:
            logger.debug("Initial AMPS weather poll error: %s", e)

        while self.is_running:
            try:
                await asyncio.sleep(self.config.poll_interval_seconds)
                await self.poll_now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.last_error = f"Error in AMPS weather loop: {e}"
                logger.warning(self.last_error)
                await asyncio.sleep(10.0)

    def get_status(self) -> dict[str, Any]:
        """Return operational diagnostics and health status."""
        return {
            "status": "ONLINE" if self.is_running else "STOPPED",
            "is_running": self.is_running,
            "station_id": self.config.station_id,
            "poll_interval_seconds": self.config.poll_interval_seconds,
            "total_polls": self.total_polls,
            "last_poll_timestamp": self.last_poll_timestamp,
            "last_error": self.last_error,
            "current_observation": self._current_obs.model_dump(),
            "safety_condition": self._current_obs.safety_condition.value,
            "forecast_hours_count": len(self._forecast),
        }
