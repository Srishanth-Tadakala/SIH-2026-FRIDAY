"""Cockpit State Synchronization Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Persists complete operator session state, active station, active tab, autonomous mode,
and UI preferences so the cockpit retains continuity across page refreshes and logins.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import StationStateSyncRecord

logger = logging.getLogger("friday.database.state_sync")

COLLECTION_NAME = "station_state_sync"


class StateSyncRepository:
    """Repository managing persistent cockpit state sync packages."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def save_state(self, record: StationStateSyncRecord) -> bool:
        """Upsert the operational state package for a station."""
        doc = record.to_dict()
        return await self.db.update_record(
            COLLECTION_NAME,
            filter_dict={"sync_id": record.sync_id},
            update_dict={"$set": doc},
            upsert=True,
        )

    async def get_state(self, sync_id: str = "STATE_SYNC_PRIMARY") -> StationStateSyncRecord | None:
        """Retrieve the latest synchronized operational state package."""
        doc = await self.db.find_one_record(COLLECTION_NAME, {"sync_id": sync_id})
        if not doc:
            return None
        try:
            return StationStateSyncRecord(**doc)
        except Exception as e:
            logger.warning("Error deserializing StationStateSyncRecord: %s", e)
            return None
