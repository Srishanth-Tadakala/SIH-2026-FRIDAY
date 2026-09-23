"""High-Performance In-Memory Agent Message Bus.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Event-Driven Publish/Subscribe: Allows agents to communicate, debate, critique,
   and coordinate asynchronously or synchronously.
2. Priority Routing: Emergency and Critical alerts jump ahead to ensure immediate
   life-support and mission protection.
3. Dialogue Audit Trail: Every inter-agent message is stored with session context
   for transparent replay and real-time streaming to the React Flow frontend.
4. Deliberation Session Tracking: Central blackboard registry maintaining active
   incident sessions and shared hypothesis contexts.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable

from .models import (
    AgentMessage,
    AgentRole,
    DeliberationSession,
    MessageType,
    SeverityLevel,
)


class AgentMessageBus:
    """Central event broker and dialogue recording bus for F.R.I.D.A.Y. agents."""

    def __init__(self, max_history: int = 2000, max_sessions: int = 200) -> None:
        # Role-based subscribers: role -> list of callbacks
        self._role_subscribers: dict[AgentRole, list[Callable[[AgentMessage], None]]] = defaultdict(list)
        # Type-based subscribers: message_type -> list of callbacks
        self._type_subscribers: dict[MessageType, list[Callable[[AgentMessage], None]]] = defaultdict(list)
        # Global broadcast subscribers: list of callbacks
        self._broadcast_subscribers: list[Callable[[AgentMessage], None]] = []

        # Audit history & active sessions (bounded to prevent memory leaks in continuous 24/7 ops)
        self._max_history: int = max_history
        self._max_sessions: int = max_sessions
        self._message_history: deque[AgentMessage] = deque(maxlen=self._max_history)
        self._total_messages_processed: int = 0
        self._sessions: dict[str, DeliberationSession] = {}

    @property
    def total_messages_processed(self) -> int:
        """Total messages routed through the bus."""
        return self._total_messages_processed

    def subscribe_role(
        self,
        role: AgentRole,
        callback: Callable[[AgentMessage], None],
    ) -> None:
        """Register a callback for messages addressed specifically to an agent role or BROADCAST."""
        self._role_subscribers[role].append(callback)

    def subscribe_type(
        self,
        msg_type: MessageType,
        callback: Callable[[AgentMessage], None],
    ) -> None:
        """Register a callback for messages of a specific semantic type (e.g. ALERT, PROPOSAL)."""
        self._type_subscribers[msg_type].append(callback)

    def subscribe_broadcast(
        self,
        callback: Callable[[AgentMessage], None],
    ) -> None:
        """Register a global callback receiving all messages published on the bus."""
        self._broadcast_subscribers.append(callback)

    def create_session(
        self,
        trigger_alert: dict[str, Any] | None = None,
    ) -> DeliberationSession:
        """Create and register a new DeliberationSession blackboard."""
        # Prune oldest resolved sessions if capacity exceeded
        if len(self._sessions) >= self._max_sessions:
            resolved_keys = [k for k, s in self._sessions.items() if s.resolved]
            if resolved_keys:
                for k in resolved_keys[: max(1, len(resolved_keys) // 2)]:
                    self._sessions.pop(k, None)
            elif len(self._sessions) > self._max_sessions * 2:
                oldest_key = next(iter(self._sessions))
                self._sessions.pop(oldest_key, None)

        session = DeliberationSession(
            trigger_alert=trigger_alert or {},
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> DeliberationSession | None:
        """Retrieve a deliberation session by its unique ID."""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> list[DeliberationSession]:
        """Return all active or past deliberation sessions."""
        return list(self._sessions.values())

    def get_active_sessions(self) -> list[DeliberationSession]:
        """Return all currently active deliberation sessions."""
        return [s for s in self._sessions.values() if not s.resolved]

    def get_history(self) -> list[AgentMessage]:
        """Return all recorded messages in the bus audit history."""
        return list(self._message_history)

    def publish(self, message: AgentMessage) -> None:
        """Publish a message onto the bus and dispatch it to relevant subscribers."""
        # 1. Record in global audit history and increment total lifetime counter
        self._total_messages_processed += 1
        self._message_history.append(message)

        # 2. Append to deliberation session transcript if registered
        session = self._sessions.get(message.session_id)
        if session is not None:
            session.transcript.append(message)

        # 3. Dispatch to Global broadcast subscribers
        for cb in self._broadcast_subscribers:
            cb(message)

        # 4. Dispatch to Type-based subscribers
        for cb in self._type_subscribers.get(message.message_type, []):
            cb(message)

        # 5. Dispatch to Role-based recipient
        if message.recipient == "BROADCAST":
            for role_subscribers in self._role_subscribers.values():
                for cb in role_subscribers:
                    cb(message)
        elif isinstance(message.recipient, AgentRole):
            for cb in self._role_subscribers.get(message.recipient, []):
                cb(message)

    def get_session_transcript(self, session_id: str) -> list[AgentMessage]:
        """Return the chronological dialogue transcript for a deliberation session."""
        session = self._sessions.get(session_id)
        if session:
            return list(session.transcript)
        return [m for m in self._message_history if m.session_id == session_id]

    def get_recent_messages(self, limit: int = 50) -> list[AgentMessage]:
        """Return the N most recent messages dispatched across the platform."""
        hist = list(self._message_history)
        return hist[-limit:]

    def clear(self) -> None:
        """Clear all subscribers, sessions, and message history (primarily for unit testing)."""
        self._role_subscribers.clear()
        self._type_subscribers.clear()
        self._broadcast_subscribers.clear()
        self._message_history.clear()
        self._total_messages_processed = 0
        self._sessions.clear()
