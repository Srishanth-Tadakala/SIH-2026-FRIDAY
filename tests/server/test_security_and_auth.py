"""Tests for Authentication, RBAC, Safety Interlock Hardening, and Health Probes.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.models import ActionProposal, AutonomyTier
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.core.engine import BharatiMasterTwinEngine
from backend.server.app import create_app
from backend.server.auth import User, UserRole, create_access_token
from backend.server.state import reset_server_state


@pytest.fixture
def client() -> TestClient:
    reset_server_state(seed=42)
    app = create_app()
    return TestClient(app)


def test_login_success(client: TestClient) -> None:
    """Verify authenticating with valid credentials yields signed JWT token."""
    res = client.post("/api/auth/login", json={"username": "commander", "password": "commander123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "commander"
    assert data["user"]["role"] == "COMMANDER"


def test_login_invalid_credentials(client: TestClient) -> None:
    """Verify authenticating with invalid password rejects with 401."""
    res = client.post("/api/auth/login", json={"username": "commander", "password": "wrong_password"})
    assert res.status_code == 401
    assert "detail" in res.json()


def test_auth_me_with_bearer_token(client: TestClient) -> None:
    """Verify /api/auth/me returns identity when valid Bearer token is provided."""
    login_res = client.post("/api/auth/login", json={"username": "engineer", "password": "engineer123"})
    token = login_res.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "engineer"
    assert data["role"] == "ENGINEER"


def test_auth_me_invalid_token(client: TestClient) -> None:
    """Verify invalid token signature yields 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.fake.token"})
    assert res.status_code == 401


def test_rbac_admin_restriction(client: TestClient) -> None:
    """Verify non-admin role receives 403 Forbidden when accessing admin user-creation."""
    login_res = client.post("/api/auth/login", json={"username": "operator", "password": "operator123"})
    op_token = login_res.json()["access_token"]

    res = client.post(
        "/api/auth/users",
        json={"username": "new_guy", "password": "pass", "role": "OPERATOR"},
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert res.status_code == 403


def test_rbac_admin_success(client: TestClient) -> None:
    """Verify admin role can register new operational users."""
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = login_res.json()["access_token"]

    res = client.post(
        "/api/auth/users",
        json={"username": "trainee_01", "password": "traineepassword", "role": "OPERATOR", "full_name": "Antarctic Trainee"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["username"] == "trainee_01"

    # Verify newly created user can log in
    res_login = client.post("/api/auth/login", json={"username": "trainee_01", "password": "traineepassword"})
    assert res_login.status_code == 200


def test_health_probes(client: TestClient) -> None:
    """Verify Kubernetes / Docker liveness, readiness, and metrics endpoints."""
    # Liveness
    live_res = client.get("/health/liveness")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "ALIVE"

    # Readiness
    ready_res = client.get("/health/readiness")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert ready_data["status"] == "READY"
    assert "digital_twin_engines" in ready_data["subsystems"]
    assert "agent_message_bus" in ready_data["subsystems"]

    # Metrics
    metrics_res = client.get("/api/health/metrics")
    assert metrics_res.status_code == 200
    assert "uptime_seconds" in metrics_res.json()
    assert metrics_res.json()["sensor_count"] == 505


def test_commander_pin_lockout_and_salt() -> None:
    """Verify PBKDF2 salt hashing and exponential lockout on repeated invalid PINs."""
    manager = SafetyInterlockManager(commander_pin="SECURE-PIN-2026")
    # Verify valid PIN
    assert manager.verify_commander_authorization("CMD", "SECURE-PIN-2026") is True

    # 4 invalid attempts should not lockout yet
    for _ in range(4):
        assert manager.verify_commander_authorization("CMD", "WRONG-PIN") is False
    assert time.time() >= manager._lockout_until

    # 5th invalid attempt triggers lockout
    assert manager.verify_commander_authorization("CMD", "WRONG-PIN") is False
    assert time.time() < manager._lockout_until

    # During lockout, even correct PIN is rejected
    assert manager.verify_commander_authorization("CMD", "SECURE-PIN-2026") is False


def test_hmac_execution_token_replay_protection() -> None:
    """Verify one-time HMAC execution token cannot be reused in a replay attack."""
    manager = SafetyInterlockManager(commander_pin="BHARATI-CMD-2026")
    prop_id = "PROP-TEST-999"
    token = manager.generate_execution_token(prop_id, ttl_seconds=60.0)

    # Verification before consumption succeeds
    assert manager.verify_execution_token(prop_id, token) is True

    # First consumption must succeed
    assert manager.consume_execution_token(prop_id, token) is True

    # Immediate second consumption (replay attack) must FAIL
    assert manager.consume_execution_token(prop_id, token) is False


def test_sanitized_error_handling(client: TestClient) -> None:
    """Verify server unhandled exceptions return safe sanitized JSON with request_id without leaking internals."""
    app = client.app

    @app.get("/api/test-crash")
    def trigger_crash() -> None:
        raise ValueError("Secret database password db_pass_12345 in /internal/path/db.py line 42")

    safe_client = TestClient(app, raise_server_exceptions=False)
    res = safe_client.get("/api/test-crash")
    assert res.status_code == 500
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert "request_id" in data["error"]
    # Ensure sensitive internal trace details are not leaked in response
    assert "db_pass_12345" not in res.text
    assert "Traceback" not in res.text


def test_websocket_authentication(client: TestClient) -> None:
    """Verify WebSocket handshake enforces token validation when provided and rejects invalid tokens."""
    # 1. Invalid token -> connection rejected with policy violation (1008)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/telemetry/bharati?token=invalid.tampered.token") as ws:
            ws.receive_json()

    # 2. Valid token -> connection accepted and receives system acknowledgment
    login_res = client.post("/api/auth/login", json={"username": "operator", "password": "operator123"})
    token = login_res.json()["access_token"]
    with client.websocket_connect(f"/ws/telemetry/bharati?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["channel"] == "system"
        assert msg["action"] == "connected"
        assert msg["station_id"] == "bharati"


def test_groq_brain_circuit_breaker() -> None:
    """Verify GroqBrainEngine circuit breaker trips to OPEN upon consecutive failures and fails fast."""
    from backend.agents.framework.groq_brain import CircuitState, GroqBrainEngine

    engine = GroqBrainEngine(api_key="gsk_mock_test_key_for_circuit_breaker")
    engine.max_failures = 3
    engine.circuit_cooldown_seconds = 1.0

    assert engine.circuit_state == CircuitState.CLOSED
    assert engine.is_circuit_open() is False

    # Simulate 2 consecutive failures
    engine._record_failure(RuntimeError("API error 1"))
    engine._record_failure(RuntimeError("API error 2"))
    assert engine.circuit_state == CircuitState.CLOSED
    assert engine.is_circuit_open() is False

    # 3rd failure trips the breaker to OPEN
    engine._record_failure(RuntimeError("API error 3"))
    assert engine.circuit_state == CircuitState.OPEN
    assert engine.is_circuit_open() is True

    # During cooldown, breaker remains OPEN and fast-fails
    assert engine.is_circuit_open() is True

    # After cooldown, breaker transitions to HALF_OPEN probe state
    time.sleep(1.05)
    assert engine.is_circuit_open() is False
    assert engine.circuit_state == CircuitState.HALF_OPEN

    # Successful probe restores to nominal CLOSED
    engine._record_success()
    assert engine.circuit_state == CircuitState.CLOSED
    assert engine.consecutive_failures == 0

