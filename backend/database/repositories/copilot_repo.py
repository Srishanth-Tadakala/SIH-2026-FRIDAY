"""Persistent Copilot Conversation History Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Manages persistent audit trails and conversational exchanges between human commanders,
hackathon judges, and F.R.I.D.A.Y. Chief AI Orchestrator across stations and page refreshes.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import CopilotChatRecord

logger = logging.getLogger("friday.database.copilot")

COLLECTION_NAME = "copilot_chat_history"


class CopilotRepository:
    """Repository managing persistent Copilot chats."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def save_message(self, record: CopilotChatRecord) -> str:
        """Asynchronously save a user or assistant chat message."""
        doc = record.to_dict()
        return await self.db.insert_record(COLLECTION_NAME, doc)

    async def get_history(
        self, station_id: str | None = None, limit: int = 50
    ) -> list[CopilotChatRecord]:
        """Retrieve conversation history in chronological order."""
        filter_dict: dict[str, Any] = {}
        if station_id:
            filter_dict["station_id"] = station_id

        # Fetch latest 'limit' messages, sorted by timestamp ascending for display
        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="timestamp_unix",
            sort_order=1,
            limit=limit,
        )

        results: list[CopilotChatRecord] = []
        for d in raw_docs:
            try:
                results.append(CopilotChatRecord(**d))
            except Exception as e:
                logger.debug("Failed deserializing CopilotChatRecord: %s", e)
        return results

    async def clear_history(self, station_id: str | None = None) -> int:
        """Clear conversation history for a station or all stations."""
        filter_dict: dict[str, Any] = {}
        if station_id:
            filter_dict["station_id"] = station_id

        return await self.db.delete_records(COLLECTION_NAME, filter_dict)

    async def count_messages(self, station_id: str | None = None) -> int:
        """Count total stored copilot chat messages."""
        filter_dict: dict[str, Any] = {}
        if station_id:
            filter_dict["station_id"] = station_id
        return await self.db.count_records(COLLECTION_NAME, filter_dict)
