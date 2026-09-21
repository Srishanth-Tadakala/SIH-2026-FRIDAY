"""High-Density Telemetry Time-Series Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Stores downsampled keyframe snapshots across all 4 pillars for historical
trending and analytical replay.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import TelemetryTimeSeriesRecord

logger = logging.getLogger("friday.database.telemetry")

COLLECTION_NAME = "telemetry_time_series"


class TelemetryRepository:
    """Repository managing station time-series telemetry."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def record_snapshot(self, record: TelemetryTimeSeriesRecord) -> str:
        """Store a telemetry keyframe snapshot."""
        doc = record.to_dict()
        return await self.db.insert_record(COLLECTION_NAME, doc)

    async def get_recent_history(
        self, station_id: str = "bharati", limit: int = 60
    ) -> list[dict[str, Any]]:
        """Retrieve recent chronological telemetry snapshots."""
        return await self.db.find_records(
            COLLECTION_NAME,
            filter_dict={"station_id": station_id},
            sort_by="timestamp_utc",
            sort_order=-1,
            limit=limit,
        )
