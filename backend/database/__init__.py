"""F.R.I.D.A.Y. Database & Distributed Memory Subsystem.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Provides:
- 2-Step Distributed Architecture: Local Station Edge DB + Mainland HQ Cloud DB (MongoDB Atlas).
- Zero-Breakage Dual-Mode Engine: Seamlessly detects MongoDB or falls back to embedded local storage.
- Episodic Case-Based Reasoning Memory for Cognitive Agents.
- Digital Twin Equipment Lifecycle Ledger (running hours & degradation).
- Bandwidth-Aware Store-and-Forward Satcom Sync Worker.
"""

from .connection import DatabaseManager, get_database_manager
from .models import (
    DialogueRecord,
    EpisodeRecord,
    EquipmentLifecycleRecord,
    OperatorAuditRecord,
    SyncPriority,
    SyncStatus,
    TelemetryTimeSeriesRecord,
)

__all__ = [
    "DatabaseManager",
    "get_database_manager",
    "EpisodeRecord",
    "DialogueRecord",
    "EquipmentLifecycleRecord",
    "TelemetryTimeSeriesRecord",
    "OperatorAuditRecord",
    "SyncStatus",
    "SyncPriority",
]
