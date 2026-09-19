"""F.R.I.D.A.Y. Master Orchestration Package.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Exports:
- FridayMasterOrchestrator (Sub-Phase 3.10 Capstone)
- CommanderBriefingCard
"""

from __future__ import annotations

from .friday_core import CommanderBriefingCard, FridayMasterOrchestrator

__all__ = [
    "FridayMasterOrchestrator",
    "CommanderBriefingCard",
]
