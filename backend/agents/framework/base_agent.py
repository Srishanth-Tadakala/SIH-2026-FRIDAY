"""Abstract Base Class for F.R.I.D.A.Y. Specialized Cognitive Agents.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Unified Interface: Every specialized agent shares a consistent contract for
   receiving bus messages, reading twin telemetry, and publishing hypotheses.
2. Direct Causal Graph Access: Built-in traversal methods for upstream root-cause
   investigation and downstream risk blast-radius evaluation.
3. Decoupled Sandbox Access: Enables agents to spawn fast What-If sandboxes without
   touching live station telemetry.
4. Fail-Safe Execution: Interlocks all operational proposals through the Safety Manager.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from ...core.causal_graph import TwinCausalGraph
from ...core.engine import BharatiMasterTwinEngine, MasterTwinSnapshot
from ...core.sandbox import TwinSandbox
from .bus import AgentMessageBus
from .models import (
    AgentMessage,
    AgentRole,
    DeliberationSession,
    MessageType,
    SeverityLevel,
)
from .safety_interlock import SafetyInterlockManager


class BaseSpecializedAgent(ABC):
    """Abstract Base Class for all 9 cognitive agents and F.R.I.D.A.Y. Orchestrator."""

    def __init__(
        self,
        role: AgentRole,
        bus: AgentMessageBus,
        engine: BharatiMasterTwinEngine,
        graph: TwinCausalGraph,
        safety_interlock: SafetyInterlockManager | None = None,
    ) -> None:
        self.role = role
        self.bus = bus
        self.engine = engine
        self.graph = graph
        self.safety_interlock = safety_interlock or SafetyInterlockManager()

        # Register self on message bus for messages targeted to this role
        self.bus.subscribe_role(self.role, self.handle_message)

    @abstractmethod
    def handle_message(self, message: AgentMessage) -> None:
        """Handle incoming message routed to this agent from the message bus."""
        pass

    def on_tick(self, snapshot: MasterTwinSnapshot) -> None:
        """Optional hook called on each simulation tick (e.g. for continuous monitoring)."""
        pass

    def publish_message(
        self,
        session_id: str,
        recipient: AgentRole | Literal["BROADCAST"],
        message_type: MessageType,
        severity: SeverityLevel,
        payload: dict[str, Any],
        confidence: float = 1.0,
    ) -> AgentMessage:
        """Helper to create and dispatch a typed message to the bus."""
        # Ensure payload has an expressive human-readable summary for audit trail & UI
        if "summary" not in payload:
            if "title" in payload:
                payload["summary"] = payload["title"]
            elif "explanation" in payload:
                payload["summary"] = payload["explanation"]
            elif "description" in payload:
                payload["summary"] = payload["description"]
            elif "message" in payload:
                payload["summary"] = payload["message"]
            elif "dialogue_text" in payload:
                payload["summary"] = payload["dialogue_text"]

        msg = AgentMessage(
            sender=self.role,
            recipient=recipient,
            message_type=message_type,
            severity=severity,
            payload=payload,
            session_id=session_id,
            confidence=max(0.0, min(1.0, confidence)),
        )
        self.bus.publish(msg)
        return msg

    def query_upstream_causes(self, node_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Traverse causal graph upstream to find root causes."""
        return self.graph.get_upstream_causes(node_id, max_depth=max_depth)

    def query_downstream_impacts(self, node_id: str, max_depth: int = 5) -> list[dict[str, Any]]:
        """Traverse causal graph downstream to evaluate impact blast radius."""
        return self.graph.get_downstream_impacts(node_id, max_depth=max_depth)

    def calculate_blast_radius(self, node_id: str) -> dict[str, Any]:
        """Compute severity score and life-support threat for a node."""
        return self.graph.calculate_blast_radius(node_id)

    def fork_sandbox(self) -> TwinSandbox:
        """Create an isolated in-memory sandbox from the current engine state."""
        return TwinSandbox.fork(self.engine)
