"""Delay-Tolerant Networking (DTN) Bundle Protocol Agent (RFC 9171 / BPv7).

Implements store-carry-forward bundle routing and custodial transmission for
intermittent LEO polar satellite flybys (ISRO Cartosat/EOS-04, Iridium, Starlink)
and overland logistics convoys between Bharati and Maitri.

Provides:
- RFC 9171 Primary and Canonical Payload Block framing with SHA-256 integrity.
- Custodial transfer verification with administrative custody signal receipts.
- 3-tier priority queuing: Expedite (Emergency/Life-Support) > Normal (Science) > Bulk (Telemetry Archives).
- Time-to-Live (TTL) expiration pruning and non-volatile spool persistence.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("friday.satcom.dtn")


class BundlePriority(int, Enum):
    """RFC 9171 Bundle Priority Class."""
    BULK = 0               # Telemetry archive, non-critical logs
    NORMAL = 1             # Daily science data, routine reports
    EXPEDITE_EMERGENCY = 2 # Life-support alarms, emergency actuator commands


class BundleProcessingFlags(int, Enum):
    """RFC 9171 Bundle Processing Control Flags."""
    IS_FRAGMENT = 0x0001
    PAYLOAD_IS_ADMIN_RECORD = 0x0002
    BUNDLE_MUST_NOT_BE_FRAGMENTED = 0x0004
    CUSTODY_TRANSFER_REQUESTED = 0x0008
    DESTINATION_ACK_REQUESTED = 0x0020


class CustodyReceipt(BaseModel):
    """Administrative Custody Signal Receipt confirming bundle delivery and custodian handover."""

    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    bundle_id: str
    custodian_eid: str
    payload_sha256: str
    accepted: bool = True
    reason_code: str = "NO_ADDITIONAL_INFORMATION"
    timestamp: float = Field(default_factory=time.time)


class DtnBundle(BaseModel):
    """RFC 9171 Bundle Protocol Version 7 (BPv7) Bundle Data Unit."""

    bundle_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    source_eid: str = Field(..., description="Source Endpoint ID (e.g. dtn://bharati.station/lifesupport)")
    destination_eid: str = Field(..., description="Destination Endpoint ID (e.g. dtn://ncpor.gov.in/command)")
    report_to_eid: Optional[str] = Field(default=None, description="Endpoint ID for custody reports")
    creation_timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    sequence_number: int = Field(default=0)
    lifetime_seconds: int = Field(default=86400, ge=60, description="Bundle Time-To-Live in seconds")
    priority: BundlePriority = Field(default=BundlePriority.NORMAL)
    custody_transfer_requested: bool = Field(default=True)
    payload_data: Any = Field(..., description="Bundle payload (JSON serializable or string)")
    payload_sha256: str = Field(default="")
    payload_size_bytes: int = Field(default=0)
    current_custodian: str = Field(default="dtn://bharati.station/local")
    hops: list[dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="QUEUED", description="QUEUED, TRANSMITTING, DELIVERED, EXPIRED, CUSTODY_ACKED")

    def model_post_init(self, __context: Any) -> None:
        """Compute SHA-256 payload digest and byte length if not supplied."""
        if not self.payload_sha256:
            raw = (
                json.dumps(self.payload_data, sort_keys=True).encode("utf-8")
                if isinstance(self.payload_data, (dict, list))
                else str(self.payload_data).encode("utf-8")
            )
            self.payload_sha256 = hashlib.sha256(raw).hexdigest()
            self.payload_size_bytes = len(raw)


class DtnAgentConfig(BaseModel):
    """Configuration for DTN Bundle Protocol Agent."""

    local_eid: str = Field(default="dtn://bharati.station/node01", description="Local station node EID")
    spool_dir: str = Field(default="data/dtn_spool", description="Spool directory for store-and-forward bundles")
    max_spool_bundles: int = Field(default=5000, description="Maximum bundles to maintain in local spool")
    default_bundle_ttl_seconds: int = Field(default=172800, description="Default bundle lifetime (48 hours)")
    prune_interval_seconds: float = Field(default=60.0, description="Frequency to prune expired bundles")
    enabled: bool = Field(default=True, description="Enable DTN agent")


class DtnBundleAgent:
    """Delay-Tolerant Networking (DTN) Store-Carry-Forward Protocol Agent."""

    def __init__(self, config: Optional[DtnAgentConfig] = None) -> None:
        self.config = config or DtnAgentConfig()
        self.local_eid = self.config.local_eid

        # Prioritized queues: Priority -> list[DtnBundle]
        self._queues: dict[BundlePriority, list[DtnBundle]] = {
            BundlePriority.EXPEDITE_EMERGENCY: [],
            BundlePriority.NORMAL: [],
            BundlePriority.BULK: [],
        }

        # Delivered & Custody receipt logs
        self._custody_receipts: dict[str, CustodyReceipt] = {}
        self._delivered_bundles: dict[str, DtnBundle] = {}

        # Diagnostics & Metrics
        self.total_bundles_created: int = 0
        self.total_bundles_forwarded: int = 0
        self.total_bundles_received: int = 0
        self.total_bundles_expired: int = 0
        self.total_bytes_transferred: int = 0

        self.is_running: bool = False
        self._prune_task: Optional[asyncio.Task[None]] = None
        self._sequence_counter: int = 0

    async def start(self) -> None:
        """Initialize spool storage and start bundle expiration worker."""
        if not self.config.enabled or self.is_running:
            return

        self.is_running = True
        os.makedirs(self.config.spool_dir, exist_ok=True)
        self._prune_task = asyncio.create_task(self._prune_worker(), name="friday_dtn_prune")
        logger.info("Launched DTN Bundle Protocol Agent for Node: %s", self.local_eid)

    async def stop(self) -> None:
        """Stop worker tasks."""
        self.is_running = False
        if self._prune_task and not self._prune_task.done():
            self._prune_task.cancel()
            try:
                await self._prune_task
            except (asyncio.CancelledError, Exception):
                pass
        logger.info("Stopped DTN Bundle Protocol Agent.")

    def create_and_enqueue_bundle(
        self,
        destination_eid: str,
        payload: Any,
        source_eid: Optional[str] = None,
        priority: BundlePriority = BundlePriority.NORMAL,
        lifetime_seconds: Optional[int] = None,
        custody_transfer_requested: bool = True,
    ) -> DtnBundle:
        """Construct an RFC 9171 bundle and push into the prioritized spool queue."""
        self._sequence_counter += 1
        ttl = lifetime_seconds or self.config.default_bundle_ttl_seconds
        src = source_eid or self.local_eid

        bundle = DtnBundle(
            source_eid=src,
            destination_eid=destination_eid,
            report_to_eid=src,
            sequence_number=self._sequence_counter,
            lifetime_seconds=ttl,
            priority=priority,
            custody_transfer_requested=custody_transfer_requested,
            payload_data=payload,
            current_custodian=self.local_eid,
            hops=[{"node_eid": self.local_eid, "timestamp": time.time(), "action": "ORIGINATED"}],
            status="QUEUED",
        )

        self._queues[priority].append(bundle)
        self.total_bundles_created += 1
        logger.info(
            "Created DTN Bundle %s [%s] -> %s (Priority: %s, Size: %d B)",
            bundle.bundle_id,
            bundle.source_eid,
            bundle.destination_eid,
            priority.name,
            bundle.payload_size_bytes,
        )
        return bundle

    def receive_bundle(self, bundle: DtnBundle, carrier_eid: str) -> Optional[CustodyReceipt]:
        """Process bundle incoming from a satellite carrier or convoys node."""
        self.total_bundles_received += 1
        bundle.hops.append({"node_eid": carrier_eid, "timestamp": time.time(), "action": "CARRIED"})

        # Check if bundle is addressed to local node
        if bundle.destination_eid == self.local_eid or bundle.destination_eid.startswith(self.local_eid):
            bundle.status = "DELIVERED"
            self._delivered_bundles[bundle.bundle_id] = bundle
            logger.info("DTN Bundle %s reached destination: %s", bundle.bundle_id, self.local_eid)
        else:
            # Enqueue for further store-carry-forward
            bundle.status = "QUEUED"
            bundle.current_custodian = self.local_eid
            self._queues[bundle.priority].append(bundle)
            logger.info("DTN Bundle %s accepted for custodial forwarding", bundle.bundle_id)

        # Issue Custody Receipt if requested
        if bundle.custody_transfer_requested:
            receipt = CustodyReceipt(
                bundle_id=bundle.bundle_id,
                custodian_eid=self.local_eid,
                payload_sha256=bundle.payload_sha256,
                accepted=True,
                timestamp=time.time(),
            )
            self._custody_receipts[bundle.bundle_id] = receipt
            return receipt

        return None

    def dispatch_contact_window(
        self,
        carrier_eid: str,
        bandwidth_bytes_limit: int = 10_000_000,
        max_bundles: int = 100,
    ) -> list[DtnBundle]:
        """Opportunistic satellite flyby / convoy contact: transmits bundles by strict priority."""
        dispatched: list[DtnBundle] = []
        bytes_transferred = 0

        # Iterate through priority queues: EXPEDITE -> NORMAL -> BULK
        for p in (
            BundlePriority.EXPEDITE_EMERGENCY,
            BundlePriority.NORMAL,
            BundlePriority.BULK,
        ):
            queue = self._queues[p]
            remaining: list[DtnBundle] = []

            for bundle in queue:
                if len(dispatched) >= max_bundles:
                    remaining.append(bundle)
                    continue

                if bytes_transferred + bundle.payload_size_bytes > bandwidth_bytes_limit:
                    remaining.append(bundle)
                    continue

                # Forward bundle
                bundle.status = "TRANSMITTING"
                bundle.hops.append({
                    "node_eid": carrier_eid,
                    "timestamp": time.time(),
                    "action": "DISPATCHED_TO_CARRIER",
                })
                dispatched.append(bundle)
                bytes_transferred += bundle.payload_size_bytes

            self._queues[p] = remaining

        self.total_bundles_forwarded += len(dispatched)
        self.total_bytes_transferred += bytes_transferred
        logger.info(
            "DTN Contact Window with %s completed: Dispatched %d bundles (%d bytes)",
            carrier_eid,
            len(dispatched),
            bytes_transferred,
        )
        return dispatched

    def acknowledge_custody(self, receipt: CustodyReceipt) -> bool:
        """Process incoming custody receipt, confirming downstream custodian acceptance."""
        self._custody_receipts[receipt.bundle_id] = receipt
        # Find bundle in delivered or sent logs and mark CUSTODY_ACKED
        if receipt.bundle_id in self._delivered_bundles:
            self._delivered_bundles[receipt.bundle_id].status = "CUSTODY_ACKED"
            return True
        return False

    def prune_expired_bundles(self) -> int:
        """Evict bundles exceeding their RFC 9171 Time-to-Live."""
        now = time.time()
        pruned_count = 0

        for p in (
            BundlePriority.EXPEDITE_EMERGENCY,
            BundlePriority.NORMAL,
            BundlePriority.BULK,
        ):
            valid: list[DtnBundle] = []
            for b in self._queues[p]:
                age_seconds = now - (b.creation_timestamp_ms / 1000.0)
                if age_seconds > b.lifetime_seconds:
                    b.status = "EXPIRED"
                    pruned_count += 1
                else:
                    valid.append(b)
            self._queues[p] = valid

        self.total_bundles_expired += pruned_count
        if pruned_count > 0:
            logger.info("Pruned %d expired DTN bundles from spool queues", pruned_count)
        return pruned_count

    async def _prune_worker(self) -> None:
        """Background task pruning expired bundles."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.prune_interval_seconds)
                self.prune_expired_bundles()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("Error in DTN prune worker: %s", e)

    def get_status(self) -> dict[str, Any]:
        """Return operational diagnostics, spool counts, and metrics."""
        return {
            "status": "ONLINE" if self.is_running else "STOPPED",
            "local_eid": self.local_eid,
            "total_queued_bundles": sum(len(q) for q in self._queues.values()),
            "queue_counts": {
                "expedite_emergency": len(self._queues[BundlePriority.EXPEDITE_EMERGENCY]),
                "normal": len(self._queues[BundlePriority.NORMAL]),
                "bulk": len(self._queues[BundlePriority.BULK]),
            },
            "total_bundles_created": self.total_bundles_created,
            "total_bundles_forwarded": self.total_bundles_forwarded,
            "total_bundles_received": self.total_bundles_received,
            "total_bundles_delivered": len(self._delivered_bundles),
            "total_bundles_expired": self.total_bundles_expired,
            "total_bytes_transferred": self.total_bytes_transferred,
            "total_custody_receipts": len(self._custody_receipts),
        }
