"""Test Suite for Delay-Tolerant Networking (DTN) Bundle Protocol Agent (RFC 9171 / BPv7).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Verifies:
1. RFC 9171 Bundle data model and SHA-256 payload digest verification.
2. Store-carry-forward 3-tier priority queuing (Expedite > Normal > Bulk).
3. Opportunistic contact window bundle dispatching and bandwidth budgeting.
4. Custodial transfer handovers and administrative custody signal receipts.
5. Time-To-Live (TTL) expiration pruning.
6. REST API endpoints for DTN bundle management.
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from backend.satcom.dtn_bundle import (
    BundlePriority,
    CustodyReceipt,
    DtnAgentConfig,
    DtnBundle,
    DtnBundleAgent,
)
from backend.server.app import create_app
from backend.server.state import reset_server_state


def test_dtn_bundle_creation_and_integrity() -> None:
    """Verify bundle initialization, automatic SHA-256 calculation, and payload sizing."""
    payload = {"telemetry": "sample_science_reading", "val": 42.5}
    bundle = DtnBundle(
        source_eid="dtn://bharati.station/science",
        destination_eid="dtn://ncpor.gov.in/science",
        payload_data=payload,
        priority=BundlePriority.NORMAL,
    )

    assert bundle.bundle_id is not None
    assert len(bundle.payload_sha256) == 64
    assert bundle.payload_size_bytes > 0
    assert bundle.priority == BundlePriority.NORMAL
    assert bundle.status == "QUEUED"


def test_dtn_agent_priority_queuing_and_dispatch() -> None:
    """Verify strict priority dispatch: Expedite (Emergency) > Normal > Bulk."""
    agent = DtnBundleAgent()

    # 1. Enqueue in mixed order
    b_bulk = agent.create_and_enqueue_bundle(
        destination_eid="dtn://ncpor.gov.in/archive",
        payload={"log": "routine_bulk_log_entry"},
        priority=BundlePriority.BULK,
    )
    b_norm = agent.create_and_enqueue_bundle(
        destination_eid="dtn://ncpor.gov.in/science",
        payload={"experiment": "ozone_lidar_profile"},
        priority=BundlePriority.NORMAL,
    )
    b_emerg = agent.create_and_enqueue_bundle(
        destination_eid="dtn://ncpor.gov.in/command",
        payload={"alert": "LIFE_SUPPORT_HEATER_FAULT"},
        priority=BundlePriority.EXPEDITE_EMERGENCY,
    )

    status = agent.get_status()
    assert status["total_queued_bundles"] == 3
    assert status["queue_counts"]["expedite_emergency"] == 1
    assert status["queue_counts"]["normal"] == 1
    assert status["queue_counts"]["bulk"] == 1

    # 2. Dispatch with contact window (max 2 bundles)
    dispatched = agent.dispatch_contact_window(
        carrier_eid="dtn://sat.cartosat-2f/transponder01",
        max_bundles=2,
    )

    assert len(dispatched) == 2
    # First must be Emergency, second must be Normal
    assert dispatched[0].bundle_id == b_emerg.bundle_id
    assert dispatched[0].priority == BundlePriority.EXPEDITE_EMERGENCY
    assert dispatched[1].bundle_id == b_norm.bundle_id
    assert dispatched[1].priority == BundlePriority.NORMAL

    # Bulk bundle remains in queue
    rem_status = agent.get_status()
    assert rem_status["total_queued_bundles"] == 1
    assert rem_status["queue_counts"]["bulk"] == 1


def test_dtn_custodial_transfer_and_receipts() -> None:
    """Verify custodial handover and custody receipt generation."""
    agent_sender = DtnBundleAgent(config=DtnAgentConfig(local_eid="dtn://bharati.station/node01"))
    agent_receiver = DtnBundleAgent(config=DtnAgentConfig(local_eid="dtn://maitri.station/node02"))

    # Create bundle at sender
    bundle = agent_sender.create_and_enqueue_bundle(
        destination_eid="dtn://maitri.station/node02",
        payload={"transfer_request": "emergency_medical_log"},
        custody_transfer_requested=True,
    )

    # Receiver accepts bundle from overland convoy carrier
    receipt = agent_receiver.receive_bundle(bundle, carrier_eid="dtn://convoy.pistenbully/node09")
    assert receipt is not None
    assert receipt.bundle_id == bundle.bundle_id
    assert receipt.custodian_eid == "dtn://maitri.station/node02"
    assert receipt.payload_sha256 == bundle.payload_sha256
    assert receipt.accepted is True

    # Sender processes receipt
    acked = agent_sender.acknowledge_custody(receipt)
    assert receipt.bundle_id in agent_sender._custody_receipts


def test_dtn_bundle_ttl_expiration_pruning() -> None:
    """Verify expired bundles exceeding TTL are pruned from queue."""
    agent = DtnBundleAgent()

    # Create bundle with 1 second lifetime
    b_short = agent.create_and_enqueue_bundle(
        destination_eid="dtn://ncpor.gov.in/test",
        payload={"ephemeral": "test"},
        lifetime_seconds=60,  # Min lifetime is 60s
    )

    # Manually backdate creation timestamp
    b_short.creation_timestamp_ms = int((time.time() - 120.0) * 1000)

    pruned = agent.prune_expired_bundles()
    assert pruned == 1
    assert b_short.status == "EXPIRED"
    assert agent.get_status()["total_queued_bundles"] == 0


def test_dtn_satcom_rest_api() -> None:
    """Verify /api/satcom/dtn REST endpoints."""
    reset_server_state()
    app = create_app()
    client = TestClient(app)

    # 1. GET Status
    resp_stat = client.get("/api/satcom/dtn/status")
    assert resp_stat.status_code == 200
    stat_data = resp_stat.json()
    assert "total_queued_bundles" in stat_data
    assert "queue_counts" in stat_data

    # 2. POST Send Bundle
    resp_send = client.post(
        "/api/satcom/dtn/send",
        json={
            "destination_eid": "dtn://ncpor.gov.in/telemetry",
            "payload": {"generator_power_kw": 74.8},
            "priority": 2,  # Expedite Emergency
            "lifetime_seconds": 86400,
        },
    )
    assert resp_send.status_code == 200
    send_data = resp_send.json()
    assert send_data["status"] == "QUEUED"
    assert send_data["priority"] == "EXPEDITE_EMERGENCY"
    assert "bundle_id" in send_data

    # 3. GET Bundles List
    resp_list = client.get("/api/satcom/dtn/bundles")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert "EXPEDITE_EMERGENCY" in list_data["queues"]
    assert len(list_data["queues"]["EXPEDITE_EMERGENCY"]) == 1

    # 4. POST Contact Window Simulation
    resp_contact = client.post(
        "/api/satcom/dtn/contact-window",
        json={
            "carrier_eid": "dtn://sat.cartosat-2f/transponder01",
            "bandwidth_bytes_limit": 5000000,
            "max_bundles": 10,
        },
    )
    assert resp_contact.status_code == 200
    contact_data = resp_contact.json()
    assert contact_data["status"] == "CONTACT_WINDOW_COMPLETED"
    assert contact_data["dispatched_count"] == 1
