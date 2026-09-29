"""Polar Satcom Bandwidth-Aware Synchronization Package.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Provides:
- DeadbandFilter: Sensor jitter dampening and delta thresholding.
- DeltaEncoder: Sparse sequence-tracked differential frame encoding.
- CompressedSerializer: Zlib Level 9 binary serialization (>95% bandwidth savings).
- PrioritizedSpoolQueue: Blackout store-and-forward queue with strict priority eviction.
- PolarSatcomChannelEmulator: Emulates LAN, Inmarsat (64k), Iridium (9.6k), and Blackout (0k).
- MirrorTwinEngine: Mainland digital twin replica maintaining synchronized station state.
"""

from __future__ import annotations

from .channel_emulator import (
    CHANNEL_PROFILES,
    ChannelParameters,
    PolarSatcomChannelEmulator,
    SatcomChannelProfile,
)
from .mirror_twin import MirrorTwinEngine, MirrorTwinMetrics
from .protocol import (
    CompressedSerializer,
    DeadbandFilter,
    DeadbandRule,
    DeltaEncoder,
    FrameType,
    SatcomFrame,
)
from .store_and_forward import (
    PRIORITY_CRITICAL,
    PRIORITY_DELIBERATION,
    PRIORITY_TELEMETRY,
    PrioritizedSpoolQueue,
    QueueMetrics,
)

__all__ = [
    # Protocol
    "FrameType",
    "SatcomFrame",
    "DeadbandRule",
    "DeadbandFilter",
    "DeltaEncoder",
    "CompressedSerializer",
    # Store-and-Forward
    "PRIORITY_CRITICAL",
    "PRIORITY_DELIBERATION",
    "PRIORITY_TELEMETRY",
    "PrioritizedSpoolQueue",
    "QueueMetrics",
    # Channel Emulator
    "SatcomChannelProfile",
    "ChannelParameters",
    "CHANNEL_PROFILES",
    "PolarSatcomChannelEmulator",
    # Mirror Twin
    "MirrorTwinEngine",
    "MirrorTwinMetrics",
    # DTN Bundle Protocol (RFC 9171)
    "BundlePriority",
    "BundleProcessingFlags",
    "CustodyReceipt",
    "DtnBundle",
    "DtnAgentConfig",
    "DtnBundleAgent",
]

from .dtn_bundle import (
    BundlePriority,
    BundleProcessingFlags,
    CustodyReceipt,
    DtnAgentConfig,
    DtnBundle,
    DtnBundleAgent,
)
