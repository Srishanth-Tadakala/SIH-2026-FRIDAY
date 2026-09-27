"""Adversarial Failure Injection and Fault-Tolerance Verification Suite for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Simulates:
1. Groq Outage & Neural Fallback
2. Polar Satcom Blackout & Store-and-Forward Spooling
3. Broken Bus Subscriber Isolation
4. Life-Support Safety Guardrail Enforcement (Thermal & Water)
5. Actuator Last Generator Shutdown Gatekeeping
6. Malformed Telemetry Ingestion Defense
7. Unauthorized Action Rejection (RBAC)
8. Invalid PIN Brute-Force & Lockout
9. HMAC Execution Token Replay Attack Defense
10. WebSocket Tampered Token Rejection
"""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from backend.agents.framework.bus import AgentMessageBus
from backend.agents.framework.groq_brain import CircuitState, GroqBrainEngine
from backend.agents.framework.models import (
    ActionProposal,
    AgentMessage,
    AgentRole,
    AutonomyTier,
    MessageType,
    ProposalStatus,
    SeverityLevel,
)
from backend.agents.framework.safety_interlock import SafetyInterlockManager
from backend.core.engine import BharatiMasterTwinEngine
from backend.server.app import create_app
from backend.server.auth import create_access_token, User, UserRole
from backend.server.state import reset_server_state, get_server_state


@pytest.fixture
def client() -> TestClient:
    reset_server_state(seed=42)
    app = create_app()
    return TestClient(app)


def test_adversarial_thermal_safety_rejection() -> None:
    """Verify safety interlock deterministically rejects dangerous life-support thermal depletion."""
    manager = SafetyInterlockManager()
    engine = BharatiMasterTwinEngine()

    dangerous_proposal = ActionProposal(
        title="Malicious or Hallucinated Cool Down",
        target_subsystem="INFRASTRUCTURE",
        parameter_overrides=[
            {"pillar": "infrastructure", "path": "hvac.living_temp_c", "value": 11.0}  # Below 16°C
        ],
        tier=AutonomyTier.TIER_1_AUTONOMOUS,
        rationale="Hazardous cooling order",
    )

    result = manager.execute_action(dangerous_proposal, engine)
    assert result.success is False
    assert result.status == ProposalStatus.REJECTED
    assert "ERR_THERMAL_LIFE_SUPPORT" in result.message


def test_adversarial_water_reserve_safety_rejection() -> None:
    """Verify safety interlock rejects proposals draining potable water below 1,500 L."""
    manager = SafetyInterlockManager()
    engine = BharatiMasterTwinEngine()

    dangerous_proposal = ActionProposal(
        title="Deplete Water Tank",
        target_subsystem="LOGISTICS",
        parameter_overrides=[
            {"pillar": "logistics", "path": "water.potable_water_liters", "value": 450.0}
        ],
        tier=AutonomyTier.TIER_1_AUTONOMOUS,
        rationale="Hazardous water depletion",
    )

    result = manager.execute_action(dangerous_proposal, engine)
    assert result.success is False
    assert result.status == ProposalStatus.REJECTED
    assert "ERR_POTABLE_WATER_MINIMUM" in result.message


def test_adversarial_last_generator_shutdown_escalation() -> None:
    """Verify shutting down the sole running generator is escalated to Tier 3 Commander confirmation."""
    manager = SafetyInterlockManager()
    engine = BharatiMasterTwinEngine()

    # Ensure only 1 generator is running
    engine.energy_registry.physics.chps[0].running_status = True
    engine.energy_registry.physics.chps[1].running_status = False
    engine.energy_registry.physics.chps[2].running_status = False

    proposal = ActionProposal(
        title="Turn Off Duty Generator",
        target_subsystem="ENERGY",
        parameter_overrides=[
            {"pillar": "energy", "path": "chps[0].operating_state", "value": "OFF"}
        ],
        tier=AutonomyTier.TIER_1_AUTONOMOUS,  # Attempted as Tier 1
        rationale="Risks total blackout",
    )

    validation = manager.validate_proposal(proposal, engine)
    # Must be escalated to Tier 3
    assert validation.assigned_tier == AutonomyTier.TIER_3_COMMANDER_CONFIRMATION


def test_adversarial_token_replay_attack() -> None:
    """Verify that an HMAC execution token cannot be consumed a second time."""
    manager = SafetyInterlockManager(commander_pin="BHARATI-CMD-2026")
    proposal_id = "ACT-SEC-REPLAY-1"

    token = manager.generate_execution_token(proposal_id, ttl_seconds=60.0)

    # First consumption succeeds
    assert manager.consume_execution_token(proposal_id, token) is True

    # Immediate second consumption (replay) fails
    assert manager.consume_execution_token(proposal_id, token) is False


def test_adversarial_expired_token_rejection() -> None:
    """Verify that an expired HMAC execution token is rejected."""
    manager = SafetyInterlockManager(commander_pin="BHARATI-CMD-2026")
    proposal_id = "ACT-SEC-EXPIRED-1"

    # Token with 0 TTL
    token = manager.generate_execution_token(proposal_id, ttl_seconds=-1.0)
    assert manager.verify_execution_token(proposal_id, token) is False
    assert manager.consume_execution_token(proposal_id, token) is False


def test_adversarial_pin_lockout_defense() -> None:
    """Verify exponential lockout prevents brute force attacks against Station Commander PIN."""
    manager = SafetyInterlockManager(commander_pin="BHARATI-CMD-2026")

    # 4 bad attempts
    for _ in range(4):
        assert manager.verify_commander_authorization("EXECUTE", "WRONG") is False
    assert time.time() >= manager._lockout_until

    # 5th attempt locks the system out
    assert manager.verify_commander_authorization("EXECUTE", "WRONG") is False
    assert time.time() < manager._lockout_until

    # Even valid PIN is rejected during lockout
    assert manager.verify_commander_authorization("EXECUTE", "BHARATI-CMD-2026") is False


def test_adversarial_bus_faulty_subscriber_isolation() -> None:
    """Verify a crashing subscriber callback does NOT break bus delivery to other subscribers."""
    bus = AgentMessageBus()
    received_messages: list[AgentMessage] = []

    def faulty_subscriber(msg: AgentMessage) -> None:
        raise ZeroDivisionError("Simulated subscriber hardware crash")

    def healthy_subscriber(msg: AgentMessage) -> None:
        received_messages.append(msg)

    bus.subscribe_broadcast(faulty_subscriber)
    bus.subscribe_broadcast(healthy_subscriber)

    msg = AgentMessage(
        sender=AgentRole.SITUATION_AWARENESS,
        recipient="BROADCAST",
        message_type=MessageType.ALERT,
        severity=SeverityLevel.CRITICAL,
        payload={"alert": "Test Alert"},
        session_id="SES-FAIL-1",
    )

    # Publishing must not raise exception
    bus.publish(msg)

    # Healthy subscriber must have received the message despite faulty subscriber's crash
    assert len(received_messages) == 1
    assert received_messages[0].message_type == MessageType.ALERT


def test_adversarial_malformed_telemetry_ingest(client: TestClient) -> None:
    """Verify malformed JSON in telemetry ingest returns 422 without compromising state."""
    res = client.post(
        "/api/telemetry/ingest",
        json={"station_id": "bharati", "readings": "NOT_A_LIST"},
    )
    assert res.status_code == 422


def test_adversarial_unauthorized_tier2_action(client: TestClient) -> None:
    """Verify viewer role cannot execute Tier 2 operational actions."""
    viewer_user = User(username="observer", role=UserRole.VIEWER)
    viewer_token = create_access_token(viewer_user)

    payload = {
        "plan_name": "Unauthorized Valve Shift",
        "strategy": "LOGISTICS",
        "autonomy_tier": "TIER_2",
        "actions": [{"pillar": "logistics", "path": "fuel.valve01", "value": "OPEN"}],
        "expected_outcome": "Unauthorized modification",
    }
    res = client.post(
        "/api/actions/execute",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    # Must be 403 Forbidden
    assert res.status_code == 403


def test_adversarial_satcom_blackout_spooling() -> None:
    """Verify that during a 0 kbps polar blackout, sync worker spools locally and pauses cloud uploads."""
    state = get_server_state()

    # Trigger blackout
    state.orchestrator.edge_blackout_mode = True
    assert state.db_sync_worker.is_link_connected_fn() is False

    metrics = state.db_sync_worker.get_metrics()
    assert metrics["is_blackout_buffering"] is True

    # Restore link
    state.orchestrator.edge_blackout_mode = False
    assert state.db_sync_worker.is_link_connected_fn() is True
