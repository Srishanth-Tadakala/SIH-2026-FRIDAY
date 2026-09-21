"""Multi-Agent Cognitive Blackboard Dialogue Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Stores the persistent audit trail of inter-agent messages exchanged between
the 10 cognitive agents and F.R.I.D.A.Y. Master Mind.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import DialogueRecord, SyncStatus

logger = logging.getLogger("friday.database.dialogue")

COLLECTION_NAME = "agent_dialogue_log"


class DialogueRepository:
    """Repository managing inter-agent blackboard messages."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def log_message(self, record: DialogueRecord) -> str:
        """Asynchronously log an agent message."""
        doc = record.to_dict()
        return await self.db.insert_record(COLLECTION_NAME, doc)

    async def get_session_dialogue(
        self, session_id: str, limit: int = 50
    ) -> list[DialogueRecord]:
        """Retrieve complete dialogue chain for a specific deliberation session."""
        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict={"session_id": session_id},
            sort_by="timestamp_iso",
            sort_order=1,
            limit=limit,
        )
        results: list[DialogueRecord] = []
        for d in raw_docs:
            try:
                results.append(DialogueRecord(**d))
            except Exception:
                pass
        return results

    async def get_recent_dialogue(
        self, station_id: str | None = None, session_id: str | None = None, limit: int = 50
    ) -> list[DialogueRecord]:
        """Retrieve most recent agent messages across all sessions or for a specific session/station."""
        filter_dict: dict[str, Any] = {}
        if station_id:
            filter_dict["station_id"] = station_id
        if session_id:
            filter_dict["session_id"] = session_id

        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="timestamp_iso",
            sort_order=-1,
            limit=limit,
        )
        results: list[DialogueRecord] = []
        for d in raw_docs:
            try:
                results.append(DialogueRecord(**d))
            except Exception:
                pass
        return results

    async def get_recent_dialogues(
        self, station_id: str | None = None, session_id: str | None = None, limit: int = 50
    ) -> list[DialogueRecord]:
        """Alias for get_recent_dialogue."""
        return await self.get_recent_dialogue(station_id=station_id, session_id=session_id, limit=limit)

    async def count_total_messages(self) -> int:
        """Count total logged agent messages."""
        return await self.db.count_records(COLLECTION_NAME)
