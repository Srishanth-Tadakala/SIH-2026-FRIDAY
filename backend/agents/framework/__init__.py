"""F.R.I.D.A.Y. Multi-Agent Framework Package.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Exports:
- AgentRole: Cognitive roles for the 9 specialized agents + Friday Orchestrator.
- MessageType: Semantic intent of inter-agent messages.
- SeverityLevel: Operational urgency levels.
- AutonomyTier: Tier 1 (Autonomous), Tier 2 (Supervised), Tier 3 (Commander).
- ProposalStatus: Proposal lifecycle state.
- AgentMessage: Standard envelope for bus communication.
- ActionProposal: Structured operational intervention proposals.
- DeliberationSession: Shared incident blackboard context.
- AgentMessageBus: Pub/sub broker and audit transcript recorder.
- SafetyInterlockManager: Antarctic life-support guardrails & gatekeeping.
- SafetyValidationResult, ExecutionResult: Safety execution contracts.
- BaseSpecializedAgent: Abstract base class for all cognitive agents.
"""

from __future__ import annotations

from .base_agent import BaseSpecializedAgent
from .bus import AgentMessageBus
from .models import (
    ActionProposal,
    AgentMessage,
    AgentRole,
    AutonomyTier,
    DeliberationSession,
    MessageType,
    ProposalStatus,
    SeverityLevel,
)
from .safety_interlock import (
    ExecutionResult,
    SafetyInterlockManager,
    SafetyValidationResult,
)

__all__ = [
    "AgentRole",
    "MessageType",
    "SeverityLevel",
    "AutonomyTier",
    "ProposalStatus",
    "AgentMessage",
    "ActionProposal",
    "DeliberationSession",
    "AgentMessageBus",
    "SafetyInterlockManager",
    "SafetyValidationResult",
    "ExecutionResult",
    "BaseSpecializedAgent",
]
