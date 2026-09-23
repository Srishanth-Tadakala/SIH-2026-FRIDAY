"""Tests for Tier 3 Commander PIN Action Execution and Pending Queue.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.server.app import create_app
from backend.server.state import get_server_state


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_tier3_full_authorization_lifecycle(client: TestClient) -> None:
    """Test full submit -> pending -> authorize PIN -> executed lifecycle."""
    state = get_server_state()
    # Ensure fresh state
    state.safety_interlock._pending_tier3_queue.clear()

    # 1. Submit Tier 3 action without PIN
    payload = {
        "plan_name": "Emergency Standby Diesel Dispatch",
        "strategy": "ENERGY",
        "autonomy_tier": "TIER_3",
        "actions": [
            {"pillar": "energy", "path": "chps[1].operating_state", "value": "RUNNING"},
            {"pillar": "energy", "path": "chps[1].active_power_kw", "value": 75.0},
        ],
        "expected_outcome": "Restore 400V microgrid capacity",
    }
    res_exec = client.post("/api/actions/execute", json=payload)
    assert res_exec.status_code == 200
    data_exec = res_exec.json()
    assert data_exec["status"] == "PENDING_COMMANDER"
    action_id = data_exec["action_id"]
    assert action_id.startswith("ACT-")

    # 2. Verify action appears in pending_tier3 queue
    res_pending = client.get("/api/actions/pending_tier3")
    assert res_pending.status_code == 200
    pending_list = res_pending.json()
    assert any(item["action_id"] == action_id for item in pending_list)

    # 3. Attempt authorization with invalid PIN -> 403 Forbidden
    res_invalid = client.post(
        "/api/actions/authorize_pin",
        json={
            "pin": "WRONG-PIN",
            "action_id": action_id,
        },
    )
    assert res_invalid.status_code == 403

    # 4. Authorize with valid Station Commander PIN -> executed
    res_valid = client.post(
        "/api/actions/authorize_pin",
        json={
            "pin": "BHARATI-CMD-2026",
            "action_id": action_id,
        },
    )
    assert res_valid.status_code == 200
    data_valid = res_valid.json()
    assert data_valid["status"] == "AUTHORIZED"
    assert data_valid["executed_action"] is not None
    assert data_valid["executed_action"]["status"] == "EXECUTED"
    assert data_valid["executed_action"]["success"] is True

    # 5. Verify action is no longer in pending_tier3 queue
    res_pending_after = client.get("/api/actions/pending_tier3")
    assert not any(item["action_id"] == action_id for item in res_pending_after.json())


def test_tier3_direct_pin_execution(client: TestClient) -> None:
    """Test immediate execution when Commander PIN is provided upfront in the execute payload."""
    payload = {
        "plan_name": "Direct Authorized Generator Maintenance Dispatch",
        "strategy": "ENERGY",
        "autonomy_tier": "TIER_3",
        "actions": [
            {"pillar": "energy", "path": "chps[2].operating_state", "value": "STANDBY"},
        ],
        "expected_outcome": "Prepare backup generator for winterover inspection",
        "commander_pin": "BHARATI-CMD-2026",
    }
    res = client.post("/api/actions/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "EXECUTED"
    assert data["success"] is True


def test_tier3_cancel_veto(client: TestClient) -> None:
    """Test cancelling/vetoing an action waiting in the Tier 3 queue."""
    payload = {
        "plan_name": "Erroneous Fuel Depletion Order",
        "strategy": "ENERGY",
        "autonomy_tier": "TIER_3",
        "actions": [
            {"pillar": "energy", "path": "fuel.day_tank_level_l", "value": 100.0},
        ],
        "expected_outcome": "Test veto flow",
    }
    res_exec = client.post("/api/actions/execute", json=payload)
    assert res_exec.status_code == 200
    action_id = res_exec.json()["action_id"]

    # Cancel action
    res_cancel = client.post(f"/api/actions/tier3/{action_id}/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "SUCCESS"

    # Confirm it is gone
    res_pending = client.get("/api/actions/pending_tier3")
    assert not any(item["action_id"] == action_id for item in res_pending.json())
