"""Bandwidth-Aware Satcom Store-and-Forward Database Sync Worker.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

POLAR BLACKOUT RESILIENT REPLICATION:
- Step 1: Local Station Edge records transactions locally with sync_status = "PENDING_HQ_SYNC".
- Step 2: When polar satcom link is healthy (Inmarsat BGAN 64-256 kbps), this worker
  batches and compresses pending records, uploading them to Mainland HQ Cloud MongoDB Atlas.
- When Satcom is severed (0 kbps Polar Blackout):
  Worker immediately halts cloud calls, allowing the local station to operate without packet drops.
- Upon reconnection:
  Drains the prioritized queue (Priority 0 Emergency Audits ➔ Priority 1 Episodes ➔ Priority 2 Telemetry).
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable

from .connection import DatabaseManager
from .models import SyncPriority, SyncStatus, generate_utc_now

logger = logging.getLogger("friday.database.sync_worker")


class SatcomDatabaseSyncWorker:
    """Asynchronous background worker synchronizing Local Station DB to Mainland Cloud Atlas."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        is_link_connected_fn: Callable[[], bool] | None = None,
        sync_interval_seconds: float = 2.0,
    ) -> None:
        self.db = db_manager
        self.is_link_connected_fn = is_link_connected_fn or (lambda: True)
        self.sync_interval = sync_interval_seconds
        
        self.is_running: bool = False
        self._task: asyncio.Task | None = None
        
        # Live metrics
        self.total_synced_records: int = 0
        self.total_spooled_records: int = 0
        self.last_sync_utc: str | None = None
        self.last_sync_status: str = "INITIALIZED"

    def start(self) -> None:
        """Launch synchronization loop background task."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._sync_loop(), name="friday_satcom_db_sync")
        logger.info("Started Satcom Database Sync Worker (Interval: %ss)", self.sync_interval)

    def stop(self) -> None:
        """Cancel synchronization worker."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Stopped Satcom Database Sync Worker.")

    async def _sync_loop(self) -> None:
        """Continuous polling and batch synchronization loop."""
        while self.is_running:
            try:
                await self.sync_pending_batches()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in database sync worker loop: %s", e)
                self.last_sync_status = f"ERROR ({str(e)[:40]})"

            await asyncio.sleep(self.sync_interval)

    async def sync_pending_batches(self) -> int:
        """Execute a single store-and-forward batch synchronization pass."""
        is_online = self.is_link_connected_fn()

        # 1. Count pending local records
        collections_to_sync = [
            ("operator_audit_trail", SyncPriority.CRITICAL_0),
            ("station_episodes", SyncPriority.HIGH_1),
            ("equipment_lifecycle", SyncPriority.HIGH_1),
            ("agent_dialogue_log", SyncPriority.HIGH_1),
            ("telemetry_time_series", SyncPriority.NORMAL_2),
        ]

        total_pending = 0
        for col_name, _ in collections_to_sync:
            count = await self.db.count_records(
                col_name, {"sync_status": SyncStatus.PENDING_HQ_SYNC.value}
            )
            total_pending += count

        self.total_spooled_records = total_pending

        if not is_online:
            self.last_sync_status = f"POLAR_BLACKOUT (0 kbps - {total_pending} Records Spooled Locally)"
            return 0

        if total_pending == 0:
            self.last_sync_status = "IDLE_SYNCHRONIZED (All Local Records Mirrored to HQ)"
            return 0

        dest_label = "NCPOR Goa Atlas" if self.db.is_cloud_mongo_connected else "Mainland Cloud Mirror"
        self.last_sync_status = f"SYNCING_TO_HQ ({total_pending} Records In-Transit to {dest_label})"
        synced_this_pass = 0

        # 2. Sync collections in priority order
        for col_name, priority in collections_to_sync:
            batch = await self.db.find_records(
                col_name,
                filter_dict={"sync_status": SyncStatus.PENDING_HQ_SYNC.value},
                limit=20,
            )

            for doc in batch:
                doc_id = doc.get("_id")
                success = await self.db.replicate_to_cloud(col_name, doc)
                if success:
                    # Update local sync state
                    await self.db.update_record(
                        col_name,
                        {"_id": doc_id},
                        {
                            "$set": {
                                "sync_status": SyncStatus.SYNCED_TO_HQ.value,
                                "synced_at_utc": generate_utc_now(),
                            }
                        },
                    )
                    self.total_synced_records += 1
                    synced_this_pass += 1

        if synced_this_pass > 0:
            self.last_sync_utc = generate_utc_now()
            self.last_sync_status = f"SYNCHRONIZED (+{synced_this_pass} Batched to {dest_label})"
            logger.info("Synced %d records to %s.", synced_this_pass, dest_label)

        return synced_this_pass

    async def sync_pending_records_now(self) -> dict[str, Any]:
        """Manually trigger an immediate batch sync pass and return execution stats."""
        is_online = self.is_link_connected_fn()
        synced = await self.sync_pending_batches()
        return {
            "synced_count": synced,
            "pending_count": self.total_spooled_records,
            "link_connected": is_online,
            "status": self.last_sync_status,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Return synchronization telemetry for Cockpit UI."""
        return {
            "sync_worker_active": self.is_running,
            "spooled_records_count": self.total_spooled_records,
            "total_synced_to_hq": self.total_synced_records,
            "last_sync_status": self.last_sync_status,
            "last_sync_timestamp": self.last_sync_utc,
            "is_blackout_buffering": not self.is_link_connected_fn(),
        }
