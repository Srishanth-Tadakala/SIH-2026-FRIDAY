"""Persistent Agent and Station Cognitive Memory Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Manages persistent memory lifecycle:
1. Creation & Normalization
2. Persistence (Local Edge MongoDB / Atomic Document Store)
3. Semantic & Keyword Retrieval
4. Relevance Filtering & Context Construction
5. Telemetry Instrumentation for Memory Retrieval Events
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from ..connection import DatabaseManager
from ..models import MemoryRecord, MemoryRetrievalEvent, MemoryType, SyncStatus, generate_utc_now

logger = logging.getLogger("friday.database.memory")

COLLECTION_NAME = "agent_memories"
RETRIEVALS_COLLECTION_NAME = "memory_retrieval_events"


class MemoryRepository:
    """Repository managing persistent cognitive memories for agents and polar stations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
        self._records: list[MemoryRecord] = []
        self._cached_retrieval_events: list[dict[str, Any]] = []

    async def initialize_baseline_memories(self) -> None:
        """Seed baseline institutional knowledge if collection is currently empty, or load cache."""
        count = await self.db.count_records(COLLECTION_NAME)
        if count > 0:
            raw_docs = await self.db.find_records(COLLECTION_NAME, limit=500)
            self._records = []
            for d in raw_docs:
                try:
                    self._records.append(MemoryRecord(**d))
                except Exception:
                    pass
            logger.info("Loaded %d persistent memories into active runtime cache.", len(self._records))
            return

        baseline_memories = [
            # 1. PLANNING AGENT MEMORIES
            MemoryRecord(
                memory_id="MEM-PLN-001",
                memory_type=MemoryType.SOP,
                agent_role="PLANNING",
                station_id="bharati",
                title="CHP Generator Cold-Start Stabilization Protocol",
                summary="Pre-heat jacket water for 60s at temperatures below -30°C before cranking standby diesel.",
                content="During extreme Antarctic sub-zero excursions (-30°C to -45°C), cold-cranking standby CHP-02 diesel generators causes hydraulic resistance trips. Engaging auxiliary jacket pre-heaters for 60-90s reduces crank resistance and stabilizes the 415V bus in under 180 seconds.",
                importance=0.95,
                severity="CRITICAL",
                source="CBR_EPISODE",
                tags=["chp_1", "chp_2", "generator_trip", "cold_crank", "microgrid"],
                metadata={"recommended_tier": "TIER_1_AUTONOMOUS", "preheat_seconds": 60},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            MemoryRecord(
                memory_id="MEM-PLN-002",
                memory_type=MemoryType.SOP,
                agent_role="PLANNING",
                station_id="bharati",
                title="Katabatic Blizzard HVAC Thermal Retention SOP",
                summary="Throttle fresh air intake dampers to 15% when wind exceeds 35 m/s to prevent heat exchanger freezing.",
                content="Katabatic gravity winds down the ice sheet exceed 35 m/s with extreme convective chill. Throttling fresh air intake dampers to 15% and boosting primary glycol loop recirculating pump to 85% preserves 34 kWth of habitat warmth without exceeding 800 ppm CO2.",
                importance=0.92,
                severity="WARNING",
                source="CBR_EPISODE",
                tags=["hvac", "blizzard_strike", "damper", "glycol_loop", "katabatic"],
                metadata={"recommended_tier": "TIER_1_AUTONOMOUS", "min_fresh_air_pct": 15},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            # 2. DIAGNOSTIC AGENT MEMORIES
            MemoryRecord(
                memory_id="MEM-DIA-001",
                memory_type=MemoryType.AGENT,
                agent_role="DIAGNOSTIC",
                station_id="bharati",
                title="Causal Disambiguation: Katabatic Wind vs. Turbine Mechanical Failure",
                summary="Wind shear gusts above 28 m/s trigger pseudo-vibration on wind turbine towers without bearing damage.",
                content="Topological analysis shows that during katabatic onset, tower tilt-meters and bearing accelerometers report elevated RMS vibration. Cross-referencing anemometer dx/dt confirms aerodynamic buffeting rather than mechanical spalling, preventing false maintenance shutdowns.",
                importance=0.88,
                severity="INFO",
                source="AGENT_LEARNING",
                tags=["wind_turbine", "vibration", "katabatic", "causal_dag", "diagnostics"],
                metadata={"causal_root": "env_katabatic", "suppress_alarm": True},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            # 3. MAINTENANCE AGENT MEMORIES
            MemoryRecord(
                memory_id="MEM-MNT-001",
                memory_type=MemoryType.AGENT,
                agent_role="MAINTENANCE",
                station_id="bharati",
                title="Reverse Osmosis Membrane Desalination Flux Degradation Rate",
                summary="Maitri and Bharati RO membranes require citric acid descaling every 450 operating hours due to mineral brine salinity.",
                content="Quilty Bay seawater feed contains high silica and dissolved minerals. Differential pressure across Stage-1 membrane modules exceeding 2.4 bar indicates biofilm/mineral scaling. Scheduled chemical backwashes prevent irreversible membrane compaction.",
                importance=0.85,
                severity="INFO",
                source="AGENT_LEARNING",
                tags=["water", "reverse_osmosis", "membrane", "desalination", "maintenance"],
                metadata={"service_interval_hours": 450, "max_delta_p_bar": 2.4},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            # 4. SITUATION AWARENESS AGENT MEMORIES
            MemoryRecord(
                memory_id="MEM-SA-001",
                memory_type=MemoryType.STATION,
                agent_role="SITUATION_AWARENESS",
                station_id="bharati",
                title="Larsemann Hills Winter-Over Microclimate Baseline Profile",
                summary="Diurnal solar radiation drops to 0 W/m2 during polar night (May-August); base relies 100% on diesel CHP and BESS.",
                content="Between mid-May and late August, photovoltaic arrays produce 0 kW. Total station thermal load increases to 165 kWth with outdoor temperatures reaching -45°C. Microgrid load balancing requires minimum 2 operational CHP generators with 1 standby spinning reserve.",
                importance=0.90,
                severity="INFO",
                source="AGENT_LEARNING",
                tags=["solar_pv", "polar_night", "microgrid", "fuel_autonomy", "winter_over"],
                metadata={"solar_avail_kw": 0, "min_chp_online": 2},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            # 5. MAITRI STATION SPECIFIC MEMORIES
            MemoryRecord(
                memory_id="MEM-MT-001",
                memory_type=MemoryType.STATION,
                agent_role="PLANNING",
                station_id="maitri",
                title="Lake Priyadarshini Water Extraction Pump Ice Dam Mitigation",
                summary="Sub-surface intake pump at Lake Priyadarshini requires heated recirculation trace line to prevent anchor ice.",
                content="Maitri extracts potable water from Lake Priyadarshini via an insulated, heat-traced pipeline. Anchor ice formation at the intake strainer during June-July reduces flow rate by up to 70%. Activating the secondary 3 kW trace heater maintains a 4.5°C intake threshold.",
                importance=0.94,
                severity="CRITICAL",
                source="CBR_EPISODE",
                tags=["water", "lake_priyadarshini", "maitri", "trace_heating", "anchor_ice"],
                metadata={"station_id": "maitri", "heater_kw": 3.0},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
            # 6. GLOBAL SAFETY MEMORY
            MemoryRecord(
                memory_id="MEM-GLB-001",
                memory_type=MemoryType.GLOBAL,
                agent_role="ALL",
                station_id="all",
                title="Non-Bypassable Life-Support Envelope Thresholds",
                summary="Living module temperature must never be commanded below 16°C and potable reserves must exceed 1500 Liters.",
                content="Governed by NCPOR Polar Habitat Operations Guidelines and SafetyPolicy: indoor temperature < 16.0°C or potable water < 1500L automatically trigger safety interlock rejection and elevate incident to Tier 3 Commander PIN requirement.",
                importance=1.0,
                severity="CRITICAL",
                source="OPERATOR_OVERRIDE",
                tags=["safety_policy", "life_support", "tier_3", "hard_limits", "ncpor"],
                metadata={"min_temp_c": 16.0, "min_water_l": 1500.0},
                sync_status=SyncStatus.SYNCED_TO_HQ,
            ),
        ]

        for mem in baseline_memories:
            await self.db.insert_record(COLLECTION_NAME, mem.to_dict())
        self._records = list(baseline_memories)
        logger.info("Initialized %d baseline cognitive memory records.", len(baseline_memories))

    async def save_memory(self, memory: MemoryRecord) -> str:
        """Persist a new cognitive memory record."""
        doc = memory.to_dict()
        doc_id = await self.db.insert_record(COLLECTION_NAME, doc)
        self._records.append(memory)
        logger.info("Persisted memory [%s] for agent [%s] at station [%s]", memory.memory_id, memory.agent_role, memory.station_id)
        return doc_id

    def search_relevant_sync(
        self,
        agent_role: str,
        station_id: str = "bharati",
        query_text: str = "",
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> tuple[list[MemoryRecord], MemoryRetrievalEvent]:
        """Synchronous in-memory relevance search for agent reasoning cycles (<0.5ms)."""
        start_time = time.perf_counter()
        tags = tags or []
        tokens = set(re.findall(r"\w+", query_text.lower()))

        scored: list[tuple[float, MemoryRecord]] = []
        for mem in self._records:
            if mem.station_id.lower() not in (station_id.lower(), "all"):
                continue

            score = mem.importance * 2.0
            if mem.agent_role.upper() in (agent_role.upper(), "ALL"):
                score += 1.5

            matched_tags = set(t.lower() for t in mem.tags).intersection(set(t.lower() for t in tags))
            score += len(matched_tags) * 2.5

            doc_text = f"{mem.title} {mem.summary} {mem.content}".lower()
            token_matches = sum(1 for tok in tokens if tok in doc_text)
            score += token_matches * 0.8

            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_memories = [m for _, m in scored[:limit]]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        context_size = sum(len(m.content) for m in top_memories)

        event = MemoryRetrievalEvent(
            agent_role=agent_role,
            station_id=station_id,
            query=query_text or " ".join(tags),
            memories_found=len(top_memories),
            memory_ids=[m.memory_id for m in top_memories],
            retrieval_latency_ms=latency_ms,
            context_size_bytes=context_size,
            memory_injection_success=len(top_memories) > 0,
        )

        doc = event.to_dict()
        self._cached_retrieval_events.append(doc)
        if len(self._cached_retrieval_events) > 50:
            self._cached_retrieval_events.pop(0)

        return top_memories, event


    async def get_memory(self, memory_id: str) -> MemoryRecord | None:
        """Retrieve a specific memory by its unique ID."""
        doc = await self.db.find_one_record(COLLECTION_NAME, {"memory_id": memory_id})
        if not doc:
            return None
        return MemoryRecord(**doc)

    async def list_memories(
        self,
        agent_role: str | None = None,
        station_id: str | None = None,
        memory_type: str | None = None,
        severity: str | None = None,
        search_query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryRecord]:
        """List and filter persistent memories."""
        filter_dict: dict[str, Any] = {}
        if agent_role and agent_role.upper() != "ALL":
            filter_dict["agent_role"] = agent_role.upper()
        if station_id and station_id.lower() != "all":
            filter_dict["station_id"] = {"$in": [station_id.lower(), "all"]}
        if memory_type and memory_type.upper() != "ALL":
            filter_dict["memory_type"] = memory_type.upper()
        if severity and severity.upper() != "ALL":
            filter_dict["severity"] = severity.upper()

        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="importance",
            sort_order=-1,
            limit=limit + offset,
        )

        results: list[MemoryRecord] = []
        for d in raw_docs[offset : offset + limit]:
            try:
                results.append(MemoryRecord(**d))
            except Exception as e:
                logger.debug("Failed parsing memory doc: %s", e)

        # Keyword filtering if search_query is supplied
        if search_query and search_query.strip():
            q_lower = search_query.strip().lower()
            filtered: list[MemoryRecord] = []
            for m in results:
                if (
                    q_lower in m.title.lower()
                    or q_lower in m.summary.lower()
                    or q_lower in m.content.lower()
                    or any(q_lower in tag.lower() for tag in m.tags)
                ):
                    filtered.append(m)
            return filtered

        return results

    async def count_memories(
        self,
        agent_role: str | None = None,
        station_id: str | None = None,
        memory_type: str | None = None,
    ) -> int:
        """Count persistent memories matching specified filters."""
        filter_dict: dict[str, Any] = {}
        if agent_role and agent_role.upper() != "ALL":
            filter_dict["agent_role"] = agent_role.upper()
        if station_id and station_id.lower() != "all":
            filter_dict["station_id"] = {"$in": [station_id.lower(), "all"]}
        if memory_type and memory_type.upper() != "ALL":
            filter_dict["memory_type"] = memory_type.upper()

        return await self.db.count_records(COLLECTION_NAME, filter_dict=filter_dict)

    async def search_relevant_memories(
        self,
        agent_role: str,
        station_id: str = "bharati",
        query_text: str = "",
        tags: list[str] | None = None,
        limit: int = 3,
    ) -> tuple[list[MemoryRecord], MemoryRetrievalEvent]:
        """Perform semantic and keyword relevance search for agent reasoning context.
        
        Calculates relevance score based on:
        - Exact tag matching
        - Keyword hits in title/summary/content
        - Station scope matching
        - Base importance weighting
        """
        start_time = time.perf_counter()
        tags = tags or []
        tokens = set(re.findall(r"\w+", query_text.lower()))

        # Search candidates matching station or 'all'
        station_filter = {"$in": [station_id.lower(), "all"]}
        raw_candidates = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict={"station_id": station_filter},
            limit=50,
        )

        scored: list[tuple[float, MemoryRecord]] = []
        for doc in raw_candidates:
            try:
                mem = MemoryRecord(**doc)
            except Exception:
                continue

            score = mem.importance * 2.0  # Base weight

            # Role relevance: matching agent role or 'ALL' gets priority
            if mem.agent_role.upper() in (agent_role.upper(), "ALL"):
                score += 1.5

            # Tag matching
            matched_tags = set(t.lower() for t in mem.tags).intersection(set(t.lower() for t in tags))
            score += len(matched_tags) * 2.5

            # Token overlap in text
            doc_text = f"{mem.title} {mem.summary} {mem.content}".lower()
            token_matches = sum(1 for tok in tokens if tok in doc_text)
            score += token_matches * 0.8

            scored.append((score, mem))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top_memories = [m for _, m in scored[:limit]]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        context_size = sum(len(m.content) for m in top_memories)

        # Create instrumentation event
        event = MemoryRetrievalEvent(
            agent_role=agent_role,
            station_id=station_id,
            query=query_text or " ".join(tags),
            memories_found=len(top_memories),
            memory_ids=[m.memory_id for m in top_memories],
            retrieval_latency_ms=latency_ms,
            context_size_bytes=context_size,
            memory_injection_success=len(top_memories) > 0,
        )

        # Log event in DB and cache for real-time frontend stream
        await self.record_retrieval(event)

        return top_memories, event

    async def record_retrieval(self, event: MemoryRetrievalEvent) -> None:
        """Record a memory retrieval telemetry event."""
        doc = event.to_dict()
        try:
            await self.db.insert_record(RETRIEVALS_COLLECTION_NAME, doc)
        except Exception as e:
            logger.debug("Failed saving retrieval event: %s", e)

        # Keep sliding in-memory window of 50 recent events for live dashboard
        self._cached_retrieval_events.append(doc)
        if len(self._cached_retrieval_events) > 50:
            self._cached_retrieval_events.pop(0)

    async def get_recent_retrievals(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent agent memory retrieval operations."""
        if self._cached_retrieval_events:
            return self._cached_retrieval_events[-limit:]
        
        raw = await self.db.find_records(
            RETRIEVALS_COLLECTION_NAME,
            sort_by="timestamp_utc",
            sort_order=-1,
            limit=limit,
        )
        return raw

    async def get_memory_stats(self) -> dict[str, Any]:
        """Aggregate real statistical summary of the memory subsystem."""
        total_count = await self.db.count_records(COLLECTION_NAME)
        
        # Aggregate counts by agent role
        all_docs = await self.db.find_records(COLLECTION_NAME, limit=200)
        by_agent: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_station: dict[str, int] = {}
        
        for d in all_docs:
            role = d.get("agent_role", "UNKNOWN")
            m_type = d.get("memory_type", "UNKNOWN")
            st = d.get("station_id", "UNKNOWN")
            by_agent[role] = by_agent.get(role, 0) + 1
            by_type[m_type] = by_type.get(m_type, 0) + 1
            by_station[st] = by_station.get(st, 0) + 1

        recent_retrievals = await self.get_recent_retrievals(limit=10)
        avg_latency = (
            round(sum(r.get("retrieval_latency_ms", 0.0) for r in recent_retrievals) / len(recent_retrievals), 2)
            if recent_retrievals
            else 0.0
        )

        return {
            "total_memories": total_count,
            "counts_by_agent": by_agent,
            "counts_by_type": by_type,
            "counts_by_station": by_station,
            "total_retrieval_events": len(self._cached_retrieval_events),
            "average_retrieval_latency_ms": avg_latency,
            "recent_retrieval_events": recent_retrievals[-5:],
        }
