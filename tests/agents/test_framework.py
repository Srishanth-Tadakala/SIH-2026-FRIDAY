"""Unit and Integration Tests for F.R.I.D.A.Y. Multi-Agent Framework.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Agent Message Bus Role-Based Pub/Sub Delivery
2. Agent Message Bus Semantic Type Filtering
3. Broadcast Dispatch across All Agents
4. Deliberation Session Blackboard & Dialogue Transcript Recording
5. Safety Interlock Tier 1 Autonomous Execution
6. Safety Interlock Thermal Life-Support Guardrail Rejection (<16°C)
7. Safety Interlock Potable Water Minimum Reserve Rejection (<1500L)
8. Safety Interlock Fire Damper Smoke Lockout
9. Safety Interlock Tier 3 Commander PIN Confirmation
10. Safety Interlock Tier 2 Supervised Veto Window
11. BaseSpecializedAgent Subclass Lifecycle & Causal Integration
"""

import pytest

from backend.agents.framework.base_agent import BaseSpecializedAgent
from backend.agents.framework.bus import AgentMessageBus
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
from backend.core.causal_graph import TwinCausalGraph
from backend.core.engine import BharatiMasterTwinEngine


class DummySpecializedAgent(BaseSpecializedAgent):
    """Test concrete implementation of BaseSpecializedAgent."""

    def __init__(
        self,
        role: AgentRole,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
    ) -> None:
        super().__init__(role, bus, engine, graph)
        self.received_messages: list[AgentMessage] = []

    def handle_message(self, message: AgentMessage) -> None:
        self.received_messages.append(message)


class TestAgentMessageBus:
    """Test suite for AgentMessageBus event broker."""

    @pytest.fixture
    def bus(self) -> AgentMessageBus:
        return AgentMessageBus()

    def test_role_subscription_and_delivery(self, bus: AgentMessageBus) -> None:
        """Verify message targeted to a specific agent role is delivered correctly."""
        received: list[AgentMessage] = []
        bus.subscribe_role(AgentRole.DIAGNOSTIC, lambda msg: received.append(msg))

        msg = AgentMessage(
            sender=AgentRole.SITUATION_AWARENESS,
            recipient=AgentRole.DIAGNOSTIC,
            message_type=MessageType.ALERT,
            severity=SeverityLevel.WARNING,
            payload={"anomaly": "Generator overheat"},
            session_id="SES-001",
        )
        bus.publish(msg)

        assert len(received) == 1
        assert received[0].message_id == msg.message_id
        assert received[0].payload["anomaly"] == "Generator overheat"

    def test_broadcast_delivery(self, bus: AgentMessageBus) -> None:
        """Verify broadcast messages are received by all registered role subscribers."""
        r_diag: list[AgentMessage] = []
        r_plan: list[AgentMessage] = []

        bus.subscribe_role(AgentRole.DIAGNOSTIC, lambda m: r_diag.append(m))
        bus.subscribe_role(AgentRole.PLANNING, lambda m: r_plan.append(m))

        broadcast_msg = AgentMessage(
            sender=AgentRole.FRIDAY_ORCHESTRATOR,
            recipient="BROADCAST",
            message_type=MessageType.OPERATOR_COMMAND,
            severity=SeverityLevel.INFO,
            payload={"cmd": "Station Health Check"},
            session_id="SES-002",
        )
        bus.publish(broadcast_msg)

        assert len(r_diag) == 1
        assert len(r_plan) == 1

    def test_type_subscription(self, bus: AgentMessageBus) -> None:
        """Verify subscribers listening to specific message types receive only those types."""
        alert_msgs: list[AgentMessage] = []
        bus.subscribe_type(MessageType.ALERT, lambda m: alert_msgs.append(m))

        m_alert = AgentMessage(
            sender=AgentRole.SITUATION_AWARENESS,
            recipient=AgentRole.DIAGNOSTIC,
            message_type=MessageType.ALERT,
            severity=SeverityLevel.CRITICAL,
            payload={"alert": "Freeze detected"},
            session_id="SES-003",
        )
        m_query = AgentMessage(
            sender=AgentRole.PLANNING,
            recipient=AgentRole.WHAT_IF,
            message_type=MessageType.SIM_REQUEST,
            severity=SeverityLevel.INFO,
            payload={"test": "4hr run"},
            session_id="SES-003",
        )

        bus.publish(m_alert)
        bus.publish(m_query)

        assert len(alert_msgs) == 1
        assert alert_msgs[0].message_type == MessageType.ALERT

    def test_deliberation_session_transcript(self, bus: AgentMessageBus) -> None:
        """Verify messages are aggregated into a shared deliberation session transcript."""
        session = bus.create_session(trigger_alert={"code": "GEN_TRIP"})
        assert session.session_id.startswith("SES-")

        msg1 = AgentMessage(
            sender=AgentRole.SITUATION_AWARENESS,
            recipient=AgentRole.DIAGNOSTIC,
            message_type=MessageType.ALERT,
            severity=SeverityLevel.CRITICAL,
            payload={"alert": "CHP-1 offline"},
            session_id=session.session_id,
        )
        msg2 = AgentMessage(
            sender=AgentRole.DIAGNOSTIC,
            recipient=AgentRole.PLANNING,
            message_type=MessageType.DIAGNOSIS,
            severity=SeverityLevel.WARNING,
            payload={"root_cause": "Exciter diode failure"},
            session_id=session.session_id,
        )

        bus.publish(msg1)
        bus.publish(msg2)

        transcript = bus.get_session_transcript(session.session_id)
        assert len(transcript) == 2
        assert transcript[0].message_type == MessageType.ALERT
        assert transcript[1].message_type == MessageType.DIAGNOSIS

    def test_bounded_history_and_lifetime_counter(self) -> None:
        """Verify message bus bounds in-memory history while retaining lifetime counter."""
        bus = AgentMessageBus(max_history=5)
        for i in range(12):
            msg = AgentMessage(
                sender=AgentRole.SITUATION_AWARENESS,
                recipient=AgentRole.DIAGNOSTIC,
                message_type=MessageType.ALERT,
                severity=SeverityLevel.INFO,
                payload={"tick": i},
                session_id=f"SES-{i}",
            )
            bus.publish(msg)

        # Monotonic counter tracks all processed messages
        assert bus.total_messages_processed == 12
        # History queue bounded to max_history
        assert len(bus._message_history) == 5
        assert len(bus.get_recent_messages(50)) == 5
        # Oldest stored message is tick 7
        assert bus.get_recent_messages(1)[0].payload["tick"] == 11

        bus.clear()
        assert bus.total_messages_processed == 0
        assert len(bus.get_recent_messages(10)) == 0

    def test_session_pruning_on_capacity(self) -> None:
        """Verify oldest resolved sessions are pruned when session limit is reached."""
        bus = AgentMessageBus(max_sessions=4)
        sessions = [bus.create_session() for _ in range(4)]
        assert len(bus._sessions) == 4

        # Mark first two sessions as resolved
        sessions[0].resolved = True
        sessions[1].resolved = True

        # Creating a 5th session should trigger pruning of resolved sessions
        s5 = bus.create_session()
        assert s5.session_id in bus._sessions
        assert len(bus._sessions) <= 4
        # Resolved session 0 should have been pruned
        assert sessions[0].session_id not in bus._sessions


class TestSafetyInterlockManager:
    """Test suite for SafetyInterlockManager guardrails."""

    @pytest.fixture
    def engine(self) -> BharatiMasterTwinEngine:
        return BharatiMasterTwinEngine(seed=42)

    @pytest.fixture
    def interlock(self) -> SafetyInterlockManager:
        return SafetyInterlockManager()

    def test_tier_1_autonomous_execution(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify safe reversible micro-action executes autonomously."""
        proposal = ActionProposal(
            title="Trim Fresh Air Damper",
            target_subsystem="HVAC",
            parameter_overrides=[
                {"pillar": "infrastructure", "path": "hvac.ahu01_fresh_air_damper_pct", "value": 15.0}
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Conserve heating during mild weather",
        )

        result = interlock.execute_action(proposal, engine)
        assert result.success is True
        assert result.status == ProposalStatus.EXECUTED
        assert engine.infra_registry.physics.hvac.ahu01_fresh_air_damper_pct == 15.0

    def test_thermal_life_support_guardrail_rejection(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify attempt to set indoor temperature below 16°C is rejected."""
        proposal = ActionProposal(
            title="Aggressive Heating Cutback",
            target_subsystem="BUILDING",
            parameter_overrides=[
                {"pillar": "infrastructure", "path": "building.temp_living_c", "value": 12.0}
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Conserve fuel aggressively",
        )

        result = interlock.execute_action(proposal, engine)
        assert result.success is False
        assert result.status == ProposalStatus.REJECTED
        assert "ERR_THERMAL_LIFE_SUPPORT" in result.message

    def test_potable_water_guardrail_rejection(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify attempt to deplete potable water below 1,500 L is rejected."""
        proposal = ActionProposal(
            title="Drain Water Tank",
            target_subsystem="WATER",
            parameter_overrides=[
                {"pillar": "infrastructure", "path": "water.potable_tank_volume_l", "value": 800.0}
            ],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Test drainage",
        )

        result = interlock.execute_action(proposal, engine)
        assert result.success is False
        assert result.status == ProposalStatus.REJECTED
        assert "ERR_POTABLE_WATER_MINIMUM" in result.message

    def test_fire_damper_smoke_lockout(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify fire dampers cannot be opened during active smoke detection."""
        # Inject smoke in zone 1
        engine.infra_registry.physics.fire.z01_smoke_obs_pct = 4.5

        proposal = ActionProposal(
            title="Open Zone 1 Damper",
            target_subsystem="FIRE",
            parameter_overrides=[
                {"pillar": "infrastructure", "path": "fire.z01_damper_open", "value": True}
            ],
            tier=AutonomyTier.TIER_1_AUTONOMOUS,
            rationale="Clear air",
        )

        result = interlock.execute_action(proposal, engine)
        assert result.success is False
        assert "ERR_FIRE_DAMPER_SMOKE_LOCKOUT" in result.message

    def test_tier_3_commander_pin_authorization(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify Tier 3 action requires valid Commander PIN."""
        proposal = ActionProposal(
            title="Emergency Load Shedding Living Block",
            target_subsystem="ENERGY",
            parameter_overrides=[
                {"pillar": "energy", "path": "chps[0].operating_state", "value": "STANDBY"}
            ],
            tier=AutonomyTier.TIER_3_COMMANDER_CONFIRMATION,
            rationale="Grid overload protection",
        )

        # 1. Attempt execution without PIN -> fails
        res_no_pin = interlock.execute_action(proposal, engine, commander_pin=None)
        assert res_no_pin.success is False
        assert res_no_pin.status == ProposalStatus.PENDING_COMMANDER

        # 2. Attempt with invalid PIN -> fails
        res_bad_pin = interlock.execute_action(proposal, engine, commander_pin="WRONG_PIN")
        assert res_bad_pin.success is False

        # 3. Attempt with correct Commander PIN -> succeeds
        res_ok = interlock.execute_action(
            proposal, engine, commander_pin=SafetyInterlockManager.COMMANDER_DEFAULT_PIN
        )
        assert res_ok.success is True
        assert res_ok.status == ProposalStatus.EXECUTED

    def test_tier_2_supervised_veto(
        self, interlock: SafetyInterlockManager, engine: BharatiMasterTwinEngine
    ) -> None:
        """Verify Tier 2 supervised actions enter veto queue and can be cancelled."""
        proposal = ActionProposal(
            title="Adjust Heating Pump Flow",
            target_subsystem="HEATING",
            parameter_overrides=[
                {"pillar": "energy", "path": "heating.heating_pump_flow", "value": 10.0}
            ],
            tier=AutonomyTier.TIER_2_SUPERVISED,
            rationale="Hydronic flow trim",
        )

        # First execution initiates supervision window
        res_q = interlock.execute_action(proposal, engine)
        assert res_q.success is False
        assert res_q.status == ProposalStatus.PENDING_SUPERVISION

        # Veto action
        veto_ok = interlock.veto_action(proposal.proposal_id, "Engineer Manual Veto")
        assert veto_ok is True


class TestBaseSpecializedAgent:
    """Test suite for BaseSpecializedAgent abstract base class."""

    def test_agent_lifecycle_and_helpers(self) -> None:
        """Verify specialized agent subscribes to bus and accesses twin tools."""
        bus = AgentMessageBus()
        engine = BharatiMasterTwinEngine(seed=42)
        graph = TwinCausalGraph()

        agent = DummySpecializedAgent(AgentRole.DIAGNOSTIC, bus, engine, graph)

        # Test message dispatch to agent
        msg = AgentMessage(
            sender=AgentRole.SITUATION_AWARENESS,
            recipient=AgentRole.DIAGNOSTIC,
            message_type=MessageType.ALERT,
            severity=SeverityLevel.WARNING,
            payload={"event": "Wind surge"},
            session_id="SES-LIFE-001",
        )
        bus.publish(msg)

        assert len(agent.received_messages) == 1
        assert agent.received_messages[0].payload["event"] == "Wind surge"

        # Test helper methods
        causes = agent.query_upstream_causes("sensor_living_temp", max_depth=3)
        assert len(causes) > 0

        blast = agent.calculate_blast_radius("chp_1")
        assert blast["total_affected_assets"] > 0

        sandbox = agent.fork_sandbox()
        assert sandbox.engine.clock.elapsed_seconds == 0.0
