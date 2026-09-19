"""Specialized Cognitive Agents Package for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Exports:
- SituationAwarenessAgent (Sub-Phase 3.1)
- DiagnosticAgent (Sub-Phase 3.2)
- PredictionAgent (Sub-Phase 3.3)
"""

from __future__ import annotations

from .diagnostic import DiagnosisResult, DiagnosticAgent
from .prediction import PredictionAgent, PredictionProjection
from .situation_awareness import AnomalyRecord, SituationAwarenessAgent

__all__ = [
    "SituationAwarenessAgent",
    "AnomalyRecord",
    "DiagnosticAgent",
    "DiagnosisResult",
    "PredictionAgent",
    "PredictionProjection",
]
