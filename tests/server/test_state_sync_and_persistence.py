"""Unit and Integration Tests for Universal Data Storage and State Synchronization.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Validates that conversation history, active station, active tab, autonomous mode,
and all user/cockpit data are persistently stored to disk, synchronized upon login/refresh,
and survive page reloads.
"""

from __future__ import annotations

import os
import shutil
import time
import pytest
from fastapi.testclient import TestClient

from backend.database.connection import EmbeddedDocumentStore
from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestStateSyncAndPersistence:
    """Test suite covering persistent storage and state synchronization across F.R.I.D.A.Y."""

    @pytest.fixture(autouse=True)
    def setup_client(self, tmp_path) -> TestClient:
        """Provide a clean server state and test client for each test."""
        # Use isolated edge storage directory for test isolation
        test_edge_dir = str(tmp_path / "edge_storage")
        os.environ["FRIDAY_EDGE_STORAGE_DIR"] = test_edge_dir

        reset_server_state(seed=42)
        app = create_app()
        client = TestClient(app)
        yield client

        # Cleanup
        if os.path.exists(test_edge_dir):
            shutil.rmtree(test_edge_dir, ignore_errors=True)
        os.environ.pop("FRIDAY_EDGE_STORAGE_DIR", None)

    @pytest.mark.asyncio
    async def test_embedded_document_store_file_persistence_and_reload(self, tmp_path) -> None:
        """Verify EmbeddedDocumentStore saves to disk JSON and reloads on new instance."""
        storage_dir = str(tmp_path / "store_test")
        store1 = EmbeddedDocumentStore("test_db", storage_dir=storage_dir)

        doc1 = {"id": "DOC-001", "name": "CHP-01 Heat Exchanger", "wear": 0.12}
        doc2 = {"id": "DOC-002", "name": "CHP-02 Turbopump", "wear": 0.45}
        await store1.insert_one("equipment", doc1)
        await store1.insert_one("equipment", doc2)

        count1 = await store1.count_documents("equipment", {})
        assert count1 == 2
        assert os.path.exists(os.path.join(storage_dir, "test_db.json"))

        # Re-initialize store from same directory - simulates server/browser restart
        store2 = EmbeddedDocumentStore("test_db", storage_dir=storage_dir)
        count2 = await store2.count_documents("equipment", {})
        assert count2 == 2
        loaded = await store2.find_one("equipment", {"id": "DOC-001"})
        assert loaded is not None
        assert loaded["name"] == "CHP-01 Heat Exchanger"
        assert loaded["wear"] == 0.12

        # Test update and delete
        await store2.update_one("equipment", {"id": "DOC-001"}, {"wear": 0.18})
        store3 = EmbeddedDocumentStore("test_db", storage_dir=storage_dir)
        doc_updated = await store3.find_one("equipment", {"id": "DOC-001"})
        assert doc_updated["wear"] == 0.18

        deleted_count = await store3.delete_many("equipment", {"id": "DOC-001"})
        assert deleted_count == 1
        count3 = await store3.count_documents("equipment", {})
        assert count3 == 1

    def test_copilot_chat_and_history_persistence(self, setup_client: TestClient) -> None:
        """Verify Copilot messages are saved to database and retrieved in order via /api/copilot/history."""
        client = setup_client

        # Initial history should be empty for a new station session
        res_initial = client.get("/api/copilot/history?station_id=bharati")
        assert res_initial.status_code == 200
        assert res_initial.json()["total"] == 0

        # Ask F.R.I.D.A.Y. Copilot a question
        res_chat = client.post("/api/copilot/chat", json={
            "message": "Assess generator fuel reserve and Madrid protocol compliance.",
            "station_id": "bharati"
        })
        assert res_chat.status_code == 200
        chat_data = res_chat.json()
        assert chat_data["status"] == "SUCCESS"
        assert len(chat_data["reply"]) > 10
        assert "cited_sensors" in chat_data

        # Now retrieve history: should contain 2 records (user query + assistant response)
        res_hist = client.get("/api/copilot/history?station_id=bharati")
        assert res_hist.status_code == 200
        hist_data = res_hist.json()
        assert hist_data["total"] == 2
        messages = hist_data["history"]
        assert len(messages) == 2

        user_msg = messages[0]
        asst_msg = messages[1]

        assert user_msg["role"] == "user"
        assert "Madrid protocol" in user_msg["message"]
        assert user_msg["station_id"] == "bharati"

        assert asst_msg["role"] == "assistant"
        assert asst_msg["station_id"] == "bharati"
        assert asst_msg["model_used"] is not None
        assert asst_msg["latency_ms"] is not None
        assert len(asst_msg["cited_sensors"]) > 0

    def test_copilot_clear_history(self, setup_client: TestClient) -> None:
        """Verify POST /api/copilot/clear removes history from disk storage."""
        client = setup_client

        # Send a message
        client.post("/api/copilot/chat", json={
            "message": "Check utilidor line temperature.",
            "station_id": "bharati"
        })
        hist_before = client.get("/api/copilot/history?station_id=bharati").json()
        assert hist_before["total"] >= 2

        # Clear history
        res_clear = client.post("/api/copilot/clear", json={"station_id": "bharati"})
        assert res_clear.status_code == 200
        assert res_clear.json()["status"] == "SUCCESS"

        # Verify history is now empty
        hist_after = client.get("/api/copilot/history?station_id=bharati").json()
        assert hist_after["total"] == 0

    def test_sync_state_get_and_post(self, setup_client: TestClient) -> None:
        """Verify GET and POST /api/sync/state preserves active tabs, autonomy, and preferences."""
        client = setup_client

        # 1. Default initial state
        res_get = client.get("/api/sync/state?station_id=bharati")
        assert res_get.status_code == 200
        state = res_get.json()
        assert state["station_id"] == "bharati"
        assert state["active_tab"] == "topo"
        assert state["autonomous_mode"] is True

        # 2. Update state to reflect user changing tabs and settings
        res_post = client.post("/api/sync/state", json={
            "station_id": "bharati",
            "operator_id": "CDR-T-SRISHANTH",
            "operator_name": "CDR. T. SRISHANTH",
            "authenticated": True,
            "active_tab": "episodes",
            "autonomous_mode": False,
            "voice_enabled": False,
            "cognitive_category": "DIAGNOSIS",
            "pillar_filter": "ENERGY",
            "active_scenario": "BLIZZARD_STRIKE"
        })
        assert res_post.status_code == 200
        updated = res_post.json()["state"]
        assert updated["active_tab"] == "episodes"
        assert updated["autonomous_mode"] is False
        assert updated["voice_enabled"] is False
        assert updated["cognitive_category"] == "DIAGNOSIS"
        assert updated["pillar_filter"] == "ENERGY"

        # 3. Read back to simulate page refresh
        res_refresh = client.get("/api/sync/state?station_id=bharati")
        assert res_refresh.status_code == 200
        refreshed_state = res_refresh.json()
        assert refreshed_state["active_tab"] == "episodes"
        assert refreshed_state["autonomous_mode"] is False
        assert refreshed_state["cognitive_category"] == "DIAGNOSIS"
        assert refreshed_state["pillar_filter"] == "ENERGY"
        assert refreshed_state["active_scenario"] == "BLIZZARD_STRIKE"

    def test_sync_login_and_logout(self, setup_client: TestClient) -> None:
        """Verify Commander authentication synchronization and session audits."""
        client = setup_client

        # 1. Invalid PIN rejected
        res_bad = client.post("/api/sync/login", json={
            "operator_id": "UNKNOWN",
            "operator_name": "Intruder",
            "pin": "WRONG-PIN-9999",
            "station_id": "bharati"
        })
        assert res_bad.status_code == 401
        assert res_bad.json()["authenticated"] is False

        # 2. Valid Commander PIN accepted
        res_login = client.post("/api/sync/login", json={
            "operator_id": "CDR-T-SRISHANTH",
            "operator_name": "CDR. T. SRISHANTH",
            "pin": "BHARATI-CMD-2026",
            "station_id": "bharati"
        })
        assert res_login.status_code == 200
        login_data = res_login.json()
        assert login_data["authenticated"] is True
        assert login_data["token"].startswith("POLAR-TOKEN-")
        assert login_data["operator_name"] == "CDR. T. SRISHANTH"

        # 3. Verify state reflects authenticated operator
        res_state = client.get("/api/sync/state?station_id=bharati")
        assert res_state.json()["authenticated"] is True
        assert res_state.json()["operator_id"] == "CDR-T-SRISHANTH"

        # 4. Logout resets authentication flag
        res_logout = client.post("/api/sync/logout", json={"station_id": "bharati"})
        assert res_logout.status_code == 200
        assert res_logout.json()["authenticated"] is False

        res_state_after = client.get("/api/sync/state?station_id=bharati")
        assert res_state_after.json()["authenticated"] is False

    def test_sync_full_refresh(self, setup_client: TestClient) -> None:
        """Verify POST /api/sync/full_refresh performs complete disk and twin sync."""
        client = setup_client
        res = client.post("/api/sync/full_refresh", json={"station_id": "bharati"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SYNCHRONIZED"
        assert "twin_status" in data
        assert "database" in data
        assert "synced_state" in data
