"""Data Models and Document Schemas for F.R.I.D.A.Y. Memory & Database Subsystem.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Defines Pydantic v2 schemas for the 6 core database collections:
1. station_episodes (Episodic Memory / Case-Based Reasoning)
2. agent_dialogue_log (Multi-Agent Blackboard Memory)
3. equipment_lifecycle (Digital Twin Asset Health & Degradation)
4. telemetry_time_series (Time-Series Downsampled Store)
5. operator_audit_trail (Commander Actions & Tier 3 PIN Ledger)
6. cloud_fleet_intelligence (Mainland HQ Multi-Station Knowledge)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import time
from typing import Any
import uuid

from pydantic import BaseModel, Field


class SyncStatus(str, Enum):
    """Store-and-forward satellite replication synchronization states."""
    PENDING_HQ_SYNC = "PENDING_HQ_SYNC"
    SYNCED_TO_HQ = "SYNCED_TO_HQ"
    FAILED_RETRY = "FAILED_RETRY"


class SyncPriority(int, Enum):
    """Replication priority classes matching polar satcom spooling queues."""
    CRITICAL_0 = 0      # Emergency life-safety alarms, generator trips, PIN audits
    HIGH_1 = 1          # Multi-agent deliberation cards, incident episodes
    NORMAL_2 = 2        # Routine sensor delta frames, periodic snapshots


def generate_utc_now() -> str:
    """Generate ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class EpisodeRecord(BaseModel):
    """Incident episode record for cognitive episodic memory and case-based reasoning."""
    episode_id: str = Field(default_factory=lambda: f"EP-{uuid.uuid4().hex[:8].upper()}")
    session_id: str = Field(..., description="Message bus deliberation session ID")
    station_id: str = Field(..., description="Target station ('bharati' or 'maitri')")
    incident_type: str = Field(..., description="Crisis identifier (e.g. GENERATOR_TRIP, WATER_LINE_FREEZE)")
    severity: str = Field(default="CRITICAL", description="Severity classification")
    start_sim_time: float = Field(..., description="Simulation clock time at crisis onset")
    end_sim_time: float | None = Field(default=None, description="Simulation clock time when resolved")
    
    # Environmental Context at onset
    environmental_context: dict[str, Any] = Field(default_factory=dict)
    
    # Initial Station KPIs
    initial_kpis: dict[str, Any] = Field(default_factory=dict)
    
    # Isolated Root Cause & Causal Path
    root_cause_diagnosis: dict[str, Any] = Field(default_factory=dict)
    
    # Multi-Agent Deliberated Plan
    deliberated_plan: dict[str, Any] = Field(default_factory=dict)
    
    # Resolution Outcome & Performance Metrics
    outcome: dict[str, Any] = Field(default_factory=dict)
    
    # Natural Language Lessons Learned (Passed into Groq LPU prompt for grounding)
    lessons_learned: str = Field(default="", description="Key takeaways and operational advice")
    
    # Store-and-Forward Satcom Replication Metadata
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING_HQ_SYNC)
    sync_priority: int = Field(default=SyncPriority.HIGH_1.value)
    created_at_utc: str = Field(default_factory=generate_utc_now)
    synced_at_utc: str | None = Field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """Serialize model to clean dictionary."""
        return self.model_dump()


class DialogueRecord(BaseModel):
    """Individual cognitive message logged from the multi-agent bus."""
    message_id: str = Field(default_factory=lambda: f"MSG-{uuid.uuid4().hex[:8].upper()}")
    session_id: str = Field(..., description="Associated deliberation session ID")
    station_id: str = Field(default="bharati", description="Station ID")
    timestamp_iso: str = Field(default_factory=generate_utc_now)
    sim_time_seconds: float = Field(default=0.0)
    sender: str = Field(..., description="AgentRole of sender")
    recipient: str = Field(..., description="AgentRole of recipient or BROADCAST")
    message_type: str = Field(..., description="MessageType string")
    severity: str = Field(default="INFO")
    confidence: float = Field(default=1.0)
    payload: dict[str, Any] = Field(default_factory=dict)
    
    # Replication Metadata
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING_HQ_SYNC)
    sync_priority: int = Field(default=SyncPriority.HIGH_1.value)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class EquipmentLifecycleRecord(BaseModel):
    """Digital twin asset health, cumulative wear, and degradation record."""
    equipment_id: str = Field(..., description="Unique equipment component ID (e.g. chp_1, ahu_01)")
    name: str = Field(..., description="Human-readable equipment name")
    station_id: str = Field(default="bharati")
    subsystem: str = Field(..., description="Subsystem domain (ENERGY, INFRASTRUCTURE, etc.)")
    total_running_hours: float = Field(default=0.0)
    total_crank_cycles: int = Field(default=0)
    thermal_stress_index: float = Field(default=0.0)
    efficiency_health_pct: float = Field(default=100.0)
    vibration_rms_mms: float = Field(default=1.5)
    last_service_sim_time: float = Field(default=0.0)
    next_service_due_hours: float = Field(default=5000.0)
    health_status: str = Field(default="OPTIMAL", description="OPTIMAL, ADVISORY, MAINTENANCE_DUE, CRITICAL_WEAR")
    maintenance_notes: str = Field(default="")
    last_updated_utc: str = Field(default_factory=generate_utc_now)
    
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING_HQ_SYNC)
    sync_priority: int = Field(default=SyncPriority.HIGH_1.value)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class TelemetryTimeSeriesRecord(BaseModel):
    """High-density downsampled sensor telemetry keyframe."""
    record_id: str = Field(default_factory=lambda: f"TS-{uuid.uuid4().hex[:10].upper()}")
    timestamp_utc: str = Field(default_factory=generate_utc_now)
    station_id: str = Field(default="bharati")
    sim_time_seconds: float = Field(default=0.0)
    kpis: dict[str, Any] = Field(default_factory=dict)
    critical_sensors: dict[str, Any] = Field(default_factory=dict)
    alert_count: int = Field(default=0)
    active_scenario: str = Field(default="NORMAL")
    
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING_HQ_SYNC)
    sync_priority: int = Field(default=SyncPriority.NORMAL_2.value)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class OperatorAuditRecord(BaseModel):
    """Tamper-evident audit ledger for human commander actions and Tier 3 PIN overrides."""
    audit_id: str = Field(default_factory=lambda: f"AUDIT-{uuid.uuid4().hex[:8].upper()}")
    station_id: str = Field(default="bharati")
    timestamp_utc: str = Field(default_factory=generate_utc_now)
    sim_time_seconds: float = Field(default=0.0)
    operator_id: str = Field(default="STATION_COMMANDER")
    action_type: str = Field(..., description="MANUAL_OVERRIDE, TIER_3_PIN_VERIFIED, BLACKOUT_SEVER, etc.")
    details: str = Field(default="")
    target_component: str | None = Field(default=None)
    authorized: bool = Field(default=True)
    
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING_HQ_SYNC)
    sync_priority: int = Field(default=SyncPriority.CRITICAL_0.value)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class CloudFleetIntelligenceRecord(BaseModel):
    """Mainland HQ fleet registry and cross-station SOP intelligence."""
    station_id: str
    station_name: str
    coordinates: str
    last_contact_utc: str = Field(default_factory=generate_utc_now)
    link_state: str = Field(default="NOMINAL")
    active_expedition: str = Field(default="44th Indian Antarctic Expedition")
    total_episodes_recorded: int = Field(default=0)
    fleet_sops: list[dict[str, Any]] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class CopilotChatRecord(BaseModel):
    """Persistent chat message exchange between Commander/Judge and F.R.I.D.A.Y."""
    chat_id: str = Field(default_factory=lambda: f"CHAT-{uuid.uuid4().hex[:8].upper()}")
    station_id: str = Field(default="bharati")
    session_id: str | None = Field(default=None)
    role: str = Field(..., description="'user' or 'assistant'")
    message: str = Field(...)
    cited_sensors: list[str] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)
    operational_status: str = Field(default="NOMINAL")
    model_used: str = Field(default="llama-3.3-70b-versatile")
    latency_ms: float = Field(default=0.0)
    timestamp_iso: str = Field(default_factory=generate_utc_now)
    timestamp_unix: float = Field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class StationStateSyncRecord(BaseModel):
    """Persistent state sync package representing the complete operational cockpit state."""
    sync_id: str = Field(default="STATE_SYNC_PRIMARY")
    station_id: str = Field(default="bharati")
    operator_id: str = Field(default="STATION_COMMANDER")
    operator_name: str = Field(default="Cmdr. T. Srishanth")
    authenticated: bool = Field(default=True)
    active_tab: str = Field(default="topo")
    autonomous_mode: bool = Field(default=True)
    voice_enabled: bool = Field(default=True)
    cognitive_category: str = Field(default="ALL")
    pillar_filter: str = Field(default="ALL")
    active_scenario: str = Field(default="NORMAL")
    preferences: dict[str, Any] = Field(default_factory=dict)
    last_synced_utc: str = Field(default_factory=generate_utc_now)
    last_synced_unix: float = Field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
