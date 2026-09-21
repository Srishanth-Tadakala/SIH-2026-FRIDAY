"""Operator Action & Tier 3 PIN Audit Ledger Repository.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides a permanent, tamper-evident audit ledger of all human commander actions,
manual actuator overrides, and Tier 3 safety PIN verifications.
"""

from __future__ import annotations

import logging
from typing import Any

from ..connection import DatabaseManager
from ..models import OperatorAuditRecord

logger = logging.getLogger("friday.database.audit")

COLLECTION_NAME = "operator_audit_trail"


class AuditRepository:
    """Repository managing operator audits and safety interlock authorizations."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager

    async def log_action(self, record: OperatorAuditRecord) -> str:
        """Log an operator action or PIN override."""
        doc = record.to_dict()
        doc_id = await self.db.insert_record(COLLECTION_NAME, doc)
        logger.info("Audit logged: %s by %s (Auth: %s)", record.action_type, record.operator_id, record.authorized)
        return doc_id

    async def log_audit(self, record: OperatorAuditRecord) -> str:
        """Alias for log_action."""
        return await self.log_action(record)

    async def get_recent_audits(
        self, station_id: str | None = None, limit: int = 30
    ) -> list[OperatorAuditRecord]:
        """Retrieve recent commander actions."""
        filter_dict = {"station_id": station_id} if station_id else {}
        raw_docs = await self.db.find_records(
            COLLECTION_NAME,
            filter_dict=filter_dict,
            sort_by="timestamp_utc",
            sort_order=-1,
            limit=limit,
        )
        results: list[OperatorAuditRecord] = []
        for d in raw_docs:
            try:
                results.append(OperatorAuditRecord(**d))
            except Exception:
                pass
        return results
