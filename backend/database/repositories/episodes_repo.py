"""Episodic Memory Repository for Cognitive Case-Based Reasoning.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Enables agents (Planning, Diagnostic, Friday Master Mind) to:
1. Store structured incident cases with environmental context and outcomes.
2. Query historical precedent cases (Case-Based Reasoning) to formulate optimal plans.
3. Track lessons learned and feed them into Groq LPU prompt context for engineering grounding.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import EpisodeRecord, SyncStatus, generate_utc_now

logger = logging.getLogger("friday.database.episodes")

COLLECTION_NAME = "station_episodes"


class EpisodesRepository:
    """Repository managing station crisis episodes and case-based memory."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def initialize_precedents(self) -> None:
        """Seed baseline historical expedition precedents if collection is empty."""
        count = await self.db.count_records(COLLECTION_NAME)
        if count > 0:
            return

        baseline_cases = [
            EpisodeRecord(
                episode_id="EP-HIST-2025-07-04",
                session_id="SES-HIST-042",
                station_id="bharati",
                incident_type="GENERATOR_TRIP",
                severity="CRITICAL",
                start_sim_time=0.0,
                end_sim_time=180.0,
                environmental_context={"ambient_temp_c": -32.5, "wind_speed_mps": 28.0, "katabatic_alert": True},
                initial_kpis={"total_generation_kw": 65.0, "load_kw": 140.0, "indoor_temp_c": 19.5, "composite_risk": 95.0},
                root_cause_diagnosis={
                    "isolated_component": "chp_1",
                    "confidence": 0.95,
                    "upstream_path": ["env_katabatic", "chp_1"],
                    "blast_radius_assets": 21,
                },
                deliberated_plan={
                    "tier": "TIER_1_AUTONOMOUS",
                    "actions": ["CRANK_STANDBY_CHP2", "ENGAGE_JACKET_PREHEAT", "SHED_NON_CRITICAL_LABS"],
                    "arbitrated_by": "FRIDAY_ORCHESTRATOR",
                },
                outcome={
                    "status": "RESOLVED_SUCCESSFULLY",
                    "recovery_duration_sec": 180,
                    "thermal_margin_c": 18.2,
                    "electrical_headroom_kw": 32.0,
                },
                lessons_learned=(
                    "Pre-heating jacket water for 60s prior to crank prevented cold-start torque trip at -32.5°C. "
                    "Standby CHP-2 stabilized 415V bus within 3 minutes."
                ),
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            EpisodeRecord(
                episode_id="EP-HIST-2025-08-19",
                session_id="SES-HIST-089",
                station_id="bharati",
                incident_type="UTILIDOR_PIPE_FREEZE_RISK",
                severity="CRITICAL",
                start_sim_time=0.0,
                end_sim_time=240.0,
                environmental_context={"ambient_temp_c": -38.0, "wind_speed_mps": 36.5, "katabatic_alert": True},
                initial_kpis={"total_generation_kw": 145.0, "load_kw": 138.0, "indoor_temp_c": 18.0, "composite_risk": 98.0},
                root_cause_diagnosis={
                    "isolated_component": "utilidor_water_line",
                    "confidence": 0.88,
                    "upstream_path": ["env_katabatic", "building_envelope", "utilidor_water_line"],
                    "blast_radius_assets": 18,
                },
                deliberated_plan={
                    "tier": "TIER_1_AUTONOMOUS",
                    "actions": ["ENGAGE_TRACE_HEATING_AUX", "ACTIVATE_RECIRCULATION_FLUSH"],
                    "arbitrated_by": "FRIDAY_ORCHESTRATOR",
                },
                outcome={
                    "status": "RESOLVED_SUCCESSFULLY",
                    "recovery_duration_sec": 240,
                    "thermal_margin_c": 12.5,
                    "electrical_headroom_kw": 25.0,
                },
                lessons_learned=(
                    "Trace heating alone is insufficient during >35 m/s katabatic gusts due to convective chill. "
                    "Thermal recirculation flush must be engaged concurrently to prevent ice crystallization."
                ),
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            EpisodeRecord(
                episode_id="EP-HIST-2025-09-11",
                session_id="SES-HIST-112",
                station_id="bharati",
                incident_type="BLIZZARD_STRIKE",
                severity="WARNING",
                start_sim_time=0.0,
                end_sim_time=300.0,
                environmental_context={"ambient_temp_c": -41.0, "wind_speed_mps": 42.0, "katabatic_alert": True},
                initial_kpis={"total_generation_kw": 148.0, "load_kw": 152.0, "indoor_temp_c": 17.2, "composite_risk": 85.0},
                root_cause_diagnosis={
                    "isolated_component": "building_envelope",
                    "confidence": 0.90,
                    "upstream_path": ["env_katabatic", "building_envelope"],
                    "blast_radius_assets": 28,
                },
                deliberated_plan={
                    "tier": "TIER_1_AUTONOMOUS",
                    "actions": ["RESTRICT_HVAC_FRESH_AIR_DAMPERS", "ENGAGE_HABITAT_SECONDARY_HEATING"],
                    "arbitrated_by": "FRIDAY_ORCHESTRATOR",
                },
                outcome={
                    "status": "RESOLVED_SUCCESSFULLY",
                    "recovery_duration_sec": 300,
                    "thermal_margin_c": 19.1,
                    "electrical_headroom_kw": 18.0,
                },
                lessons_learned=(
                    "Restricting HVAC fresh-air intake to 15% preserved 34 kWth of habitat warmth without compromising "
                    "CO2 air quality over a 6-hour blizzard peak."
                ),
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
        ]

        for ep in baseline_cases:
            await self.db.insert_record(COLLECTION_NAME, ep.to_dict())
        logger.info("Initialized %d historical episodic precedent cases.", len(baseline_cases))

    async def save_episode(self, episode: EpisodeRecord) -> str:
        """Save a new episode record into the local station database."""
        doc = episode.to_dict()
        doc_id = await self.db.insert_record(COLLECTION_NAME, doc)
        logger.info("Saved episode %s (Type: %s, Session: %s)", episode.episode_id, episode.incident_type, episode.session_id)
        return doc_id

    async def update_episode_outcome(
        self,
        session_id: str,
        outcome: dict[str, Any],
        lessons_learned: str,
        end_sim_time: float,
    ) -> bool:
        """Update an existing episode with its resolution outcome and lessons learned."""
        update_data = {
            "$set": {
                "outcome": outcome,
                "lessons_learned": lessons_learned,
                "end_sim_time": end_sim_time,
                "sync_status": SyncStatus.PENDING_HQ_SYNC.value,
            }
        }
        return await self.db.update_record(COLLECTION_NAME, {"session_id": session_id}, update_data)

    async def finalize_episode(
        self,
        session_id: str | None = None,
        episode_id: str | None = None,
        consensus_plan: dict[str, Any] | None = None,
        outcome: dict[str, Any] | None = None,
        lessons_learned: str = "",
        end_sim_time: float = 0.0,
    ) -> bool:
        """Finalize an episode with deliberated consensus plan, recovery outcome, and lessons learned."""
        filter_dict: dict[str, Any] = {}
        if episode_id:
            filter_dict["episode_id"] = episode_id
        elif session_id:
            filter_dict["session_id"] = session_id
        else:
            return False

        update_set: dict[str, Any] = {
            "sync_status": SyncStatus.PENDING_HQ_SYNC.value,
        }
        if consensus_plan:
            update_set["deliberated_plan"] = consensus_plan
        if outcome:
            update_set["outcome"] = outcome
        if lessons_learned:
            update_set["lessons_learned"] = lessons_learned
        if end_sim_time > 0:
            update_set["end_sim_time"] = end_sim_time

        return await self.db.update_record(COLLECTION_NAME, filter_dict, {"$set": update_set})

    async def find_similar_episodes(
        self,
        incident_type: str,
        ambient_temp_c: float | None = None,
        limit: int = 2,
    ) -> list[EpisodeRecord]:
        """Case-Based Reasoning: Query historical precedent episodes matching incident type.
        
        Ranks by environmental temperature proximity and resolution success.
        """
        filter_dict: dict[str, Any] = {"incident_type": incident_type}
        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="created_at_utc",
            sort_order=-1,
            limit=10,
        )

        episodes: list[EpisodeRecord] = []
        for d in raw_docs:
            try:
                episodes.append(EpisodeRecord(**d))
            except Exception as e:
                logger.debug("Failed parsing episode doc: %s", e)

        # Sort by temperature proximity if ambient_temp_c is provided
        if ambient_temp_c is not None and episodes:
            episodes.sort(
                key=lambda ep: abs(
                    ep.environmental_context.get("ambient_temp_c", 0.0) - ambient_temp_c
                )
            )

        return episodes[:limit]

    async def get_recent_episodes(
        self, station_id: str | None = None, limit: int = 15
    ) -> list[EpisodeRecord]:
        """Retrieve recent incident episodes."""
        filter_dict = {"station_id": station_id} if station_id else {}
        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="created_at_utc",
            sort_order=-1,
            limit=limit,
        )
        results: list[EpisodeRecord] = []
        for d in raw_docs:
            try:
                results.append(EpisodeRecord(**d))
            except Exception:
                pass
        return results

    # Defensive backward-compatible alias
    get_all = get_recent_episodes

    async def get_pending_sync_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve episodes awaiting satcom synchronization to Mainland HQ."""
        return await self.db.find_records(
            COLLECTION_NAME,
            filter_dict={"sync_status": SyncStatus.PENDING_HQ_SYNC.value},
            sort_by="sync_priority",
            sort_order=1,
            limit=limit,
        )

    async def mark_episode_synced(self, episode_id: str) -> bool:
        """Mark an episode as successfully synchronized to Mainland HQ."""
        update_data = {
            "$set": {
                "sync_status": SyncStatus.SYNCED_TO_HQ.value,
                "synced_at_utc": generate_utc_now(),
            }
        }
        return await self.db.update_record(COLLECTION_NAME, {"episode_id": episode_id}, update_data)
