"""Data models and enums for F.R.I.D.A.Y. multi-agent communication and deliberation.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Strongly Typed Inter-Agent Protocol: All communication across the 9 agents and
   F.R.I.D.A.Y. Core uses strictly typed contracts.
2. Tiered Autonomy Classification: Distinguishes between safe reversible micro-actions (Tier 1),
   supervised actions with 60s timeout (Tier 2), and life-critical operations requiring
   human Commander PIN confirmation (Tier 3).
3. Deliberation Session Blackboard: A shared context object that aggregates alerts,
   root-cause diagnoses, forward projections, risk scores, candidate action proposals,
   and dialogue transcripts during an operational incident.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Literal
import uuid


class AgentRole(str, Enum):
    """The 9 specialized cognitive roles plus F.R.I.D.A.Y. Master Orchestrator."""
    SITUATION_AWARENESS = "SITUATION_AWARENESS"
    DIAGNOSTIC = "DIAGNOSTIC"
    PREDICTION = "PREDICTION"
    RISK_IMPACT = "RISK_IMPACT"
    PLANNING = "PLANNING"
    WHAT_IF = "WHAT_IF"
    MISSION_OPS = "MISSION_OPS"
    MAINTENANCE = "MAINTENANCE"
    RESOURCE_OPTIMIZER = "RESOURCE_OPTIMIZER"
    FRIDAY_ORCHESTRATOR = "FRIDAY_ORCHESTRATOR"


class MessageType(str, Enum):
    """Semantic intent of an inter-agent message."""
    ALERT = "ALERT"
    QUERY = "QUERY"
    DIAGNOSIS = "DIAGNOSIS"
    PREDICTION_PROJECTION = "PREDICTION_PROJECTION"
    IMPACT_ASSESSMENT = "IMPACT_ASSESSMENT"
    PROPOSAL = "PROPOSAL"
    CRITIQUE = "CRITIQUE"
    SIM_REQUEST = "SIM_REQUEST"
    SIM_RESULT = "SIM_RESULT"
    CONSENSUS_PLAN = "CONSENSUS_PLAN"
    OPERATOR_COMMAND = "OPERATOR_COMMAND"


class SeverityLevel(str, Enum):
    """Operational urgency level of an event or message."""
    INFO = "INFO"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class AutonomyTier(str, Enum):
    """Safety-critical autonomy classification for station actions."""
    TIER_1_AUTONOMOUS = "TIER_1_AUTONOMOUS"  # Micro-adjustments, self-contained, reversible
    TIER_2_SUPERVISED = "TIER_2_SUPERVISED"  # 60-second engineer veto countdown
    TIER_3_COMMANDER_CONFIRMATION = "TIER_3_COMMANDER_CONFIRMATION"  # Explicit human sign-off required


class ProposalStatus(str, Enum):
    """Lifecycle status of a candidate operational action proposal."""
    DRAFT = "DRAFT"
    SIMULATING = "SIMULATING"
    SIMULATED = "SIMULATED"
    PENDING_SUPERVISION = "PENDING_SUPERVISION"
    PENDING_COMMANDER = "PENDING_COMMANDER"
    EXECUTED = "EXECUTED"
    VETOED = "VETOED"
    REJECTED = "REJECTED"


@dataclass
class AgentMessage:
    """Standard message envelope exchanged on the Agent Message Bus."""
    sender: AgentRole
    recipient: AgentRole | Literal["BROADCAST"]
    message_type: MessageType
    severity: SeverityLevel
    payload: dict[str, Any]
    session_id: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    confidence: float = 1.0  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Serialize message to dictionary for JSON streaming to frontend."""
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "sender": self.sender.value,
            "recipient": self.recipient.value if isinstance(self.recipient, AgentRole) else self.recipient,
            "message_type": self.message_type.value,
            "severity": self.severity.value,
            "payload": self.payload,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


@dataclass
class ActionProposal:
    """Action proposal formulated by Planning Agent and verified by What-If and Safety."""
    title: str
    target_subsystem: str
    parameter_overrides: list[dict[str, Any]]
    tier: AutonomyTier
    rationale: str
    proposal_id: str = field(default_factory=lambda: f"ACT-{str(uuid.uuid4())[:6].upper()}")
    projected_impact: dict[str, Any] = field(default_factory=dict)
    simulation_delta: dict[str, Any] | None = None
    status: ProposalStatus = ProposalStatus.DRAFT
    created_at: float = field(default_factory=time.time)


@dataclass
class DeliberationSession:
    """Shared blackboard session context during a station incident or operator task."""
    session_id: str = field(default_factory=lambda: f"SES-{str(uuid.uuid4())[:8].upper()}")
    created_at: float = field(default_factory=time.time)
    trigger_alert: dict[str, Any] = field(default_factory=dict)
    root_causes: list[dict[str, Any]] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)
    risk_assessment: dict[str, Any] = field(default_factory=dict)
    candidate_proposals: list[ActionProposal] = field(default_factory=list)
    critiques: list[dict[str, Any]] = field(default_factory=list)
    transcript: list[AgentMessage] = field(default_factory=list)
    final_plan: ActionProposal | None = None
    resolved: bool = False
