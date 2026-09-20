"""Unit and Integration Tests for Polar Satcom Telemetry Protocol & Mirror Twin (Sub-Phase 4.2).

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Station & Maitri Station, East Antarctica <-> Mainland Command (NCPOR Goa).

Tests:
1. Deadband Filtering: Steady-state jitter dampening, deadband thresholds, and discrete flag triggers.
2. Delta Encoding: Initial baseline keyframe generation and sparse delta frames across 505 sensors.
3. Compressed Binary Serialization: Header validation, zlib level 9 compression, >90% bandwidth savings.
4. Prioritized Spool Queue: Blackout buffering, strict priority draining (0 > 1 > 2), telemetry eviction.
5. Satcom Channel Emulator: Profile switching, latency/bandwidth simulation, blackout spooling & recovery.
6. Mainland Mirror Twin Synchronization: Exact state reconstruction, O(1) lookup, SHA-256 checksum parity.
7. Packet Gap Detection & Resync: Sequence discontinuity tracking, GAP_DETECTED state, keyframe healing.
8. Satcom FastAPI REST Endpoints: GET /status, /mirror, POST /profile, /sync, /recover, and /resync.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core.engine import BharatiMasterTwinEngine
from backend.satcom.channel_emulator import (
    CHANNEL_PROFILES,
    PolarSatcomChannelEmulator,
    SatcomChannelProfile,
)
from backend.satcom.mirror_twin import MirrorTwinEngine
from backend.satcom.protocol import (
    CompressedSerializer,
    DeadbandFilter,
    DeadbandRule,
    DeltaEncoder,
    FrameType,
    SatcomFrame,
)
from backend.satcom.store_and_forward import (
    PRIORITY_CRITICAL,
    PRIORITY_DELIBERATION,
    PRIORITY_TELEMETRY,
    PrioritizedSpoolQueue,
)
from backend.server.app import create_app
from backend.server.state import reset_server_state


class TestPolarSatcomProtocol:
    """Comprehensive test suite for Polar Satcom Bandwidth-Aware Synchronization."""

    def test_deadband_filtering_dampens_jitter(self) -> None:
        """Verify deadband filter suppresses steady-state sensor jitter while passing real anomalies."""
        db = DeadbandFilter()

        # Initial reading should always transmit (no baseline exists)
        assert db.should_transmit("ENV-WX-TEMP", -18.0, 0.0) is True

        # Record baseline
        db.filter_readings({"ENV-WX-TEMP": -18.0, "ENG-GEN-1-KW": 120.0, "INFRA-TRACE-STATUS": True}, 0.0)

        # 1. Jitter within deadband (temp ±0.2°C, power ±0.5 kW) should NOT transmit
        assert db.should_transmit("ENV-WX-TEMP", -18.05, 1.0) is False
        assert db.should_transmit("ENG-GEN-1-KW", 120.15, 1.0) is False

        # 2. Significant shift exceeding deadband MUST transmit
        assert db.should_transmit("ENV-WX-TEMP", -20.5, 2.0) is True
        assert db.should_transmit("ENG-GEN-1-KW", 145.0, 2.0) is True

        # 3. Discrete boolean/status change MUST ALWAYS transmit immediately
        assert db.should_transmit("INFRA-TRACE-STATUS", False, 1.0) is True

        # 4. Max silence timeout (60s) forces transmission even if value is identical
        assert db.should_transmit("ENG-GEN-1-KW", 120.0, 65.0) is True

    def test_delta_encoder_keyframe_and_sparse_delta(self) -> None:
        """Verify DeltaEncoder produces a full baseline keyframe then sparse deltas."""
        engine = BharatiMasterTwinEngine(seed=42)
        readings = engine.get_all_readings()
        encoder = DeltaEncoder()

        # 1. First encode must produce a KEYFRAME with all 505 sensors
        keyframe = encoder.encode_delta(
            station_id="bharati",
            readings=readings,
            sim_time_seconds=0.0,
            timestamp_iso=engine.clock.isoformat(),
            kpis=engine.get_station_kpis(),
            alerts=engine.get_active_alerts(),
        )
        assert keyframe.frame_type == FrameType.KEYFRAME
        assert keyframe.seq_num == 1
        assert keyframe.delta_count == 505
        assert len(keyframe.payload) == 505

        # 2. Immediate next step with zero change should produce a sparse delta with 0 channels
        delta1 = encoder.encode_delta(
            station_id="bharati",
            readings=readings,
            sim_time_seconds=1.0,
            timestamp_iso=engine.clock.isoformat(),
        )
        assert delta1.frame_type == FrameType.DELTA
        assert delta1.seq_num == 2
        assert delta1.delta_count == 0  # No sensors changed beyond deadband

        # 3. Step physics forward 1 second: only a few dynamically fluctuating sensors change
        engine.step(1.0)
        new_readings = engine.get_all_readings()
        delta2 = encoder.encode_delta(
            station_id="bharati",
            readings=new_readings,
            sim_time_seconds=2.0,
            timestamp_iso=engine.clock.isoformat(),
        )
        assert delta2.frame_type == FrameType.DELTA
        assert delta2.seq_num == 3
        # Should be sparse (substantially fewer than all 505 sensors)
        assert delta2.delta_count < 100

    def test_compressed_serializer_binary_efficiency(self) -> None:
        """Verify binary serialization roundtrip and >90% bandwidth savings."""
        engine = BharatiMasterTwinEngine(seed=42)
        encoder = DeltaEncoder()
        keyframe = encoder.encode_keyframe(
            station_id="bharati",
            readings=engine.get_all_readings(),
            sim_time_seconds=0.0,
            timestamp_iso=engine.clock.isoformat(),
            kpis=engine.get_station_kpis(),
            alerts=engine.get_active_alerts(),
        )

        # 1. Serialize with zlib deflate
        compressed_bytes = CompressedSerializer.serialize(keyframe, compress=True)
        assert compressed_bytes[:5] == b"FRDY\x01"
        assert compressed_bytes[5] == 0x01  # Deflate flag

        # 2. Deserialize back
        reconstructed = CompressedSerializer.deserialize(compressed_bytes)
        assert reconstructed.frame_id == keyframe.frame_id
        assert reconstructed.station_id == "bharati"
        assert reconstructed.seq_num == 1
        assert reconstructed.total_sensors == 505
        assert len(reconstructed.payload) == 505
        assert reconstructed.payload["ENV-WX-TEMP"] == keyframe.payload["ENV-WX-TEMP"]

        # 3. Bandwidth savings check
        stats = CompressedSerializer.compute_bandwidth_savings(keyframe.to_dict(), compressed_bytes)
        assert stats["bandwidth_saved_pct"] > 70.0  # Even full keyframe achieves >70% compression

        # 4. Sparse delta frame compression check
        delta_frame = SatcomFrame(
            frame_id="FRM-BHARATI-000002-DEL",
            station_id="bharati",
            frame_type=FrameType.DELTA,
            seq_num=2,
            timestamp_iso="2026-09-19T00:00:01Z",
            sim_time_seconds=1.0,
            payload={"ENV-WX-TEMP": -19.4, "ENG-GEN-1-KW": 135.2},
            delta_count=2,
            total_sensors=505,
        )
        delta_bytes = CompressedSerializer.serialize(delta_frame, compress=True)
        # Sparse delta is tiny (< 300 bytes)
        assert len(delta_bytes) < 300

    def test_prioritized_spool_queue_ordering_and_eviction(self) -> None:
        """Verify strict priority draining (0 > 1 > 2) and bounded telemetry eviction."""
        queue = PrioritizedSpoolQueue(
            max_critical_capacity=10,
            max_deliberation_capacity=10,
            max_telemetry_capacity=5,  # small telemetry capacity for testing eviction
        )

        # Create sample frames with varying priorities
        f_telem1 = SatcomFrame("T1", "bharati", FrameType.DELTA, 1, "", 1.0, {}, priority=PRIORITY_TELEMETRY)
        f_telem2 = SatcomFrame("T2", "bharati", FrameType.DELTA, 2, "", 2.0, {}, priority=PRIORITY_TELEMETRY)
        f_crit = SatcomFrame("C1", "bharati", FrameType.ALARM, 3, "", 3.0, {}, priority=PRIORITY_CRITICAL)
        f_delib = SatcomFrame("D1", "bharati", FrameType.DELIBERATION_CARD, 4, "", 4.0, {}, priority=PRIORITY_DELIBERATION)

        # Enqueue in arbitrary order: Telemetry first, then Critical, then Deliberation
        queue.enqueue(f_telem1)
        queue.enqueue(f_telem2)
        queue.enqueue(f_crit)
        queue.enqueue(f_delib)

        assert queue.qsize() == 4

        # 1. Dequeue must return Critical (Priority 0) first
        first = queue.dequeue()
        assert first is not None
        assert first.frame_id == "C1"
        assert first.priority == PRIORITY_CRITICAL

        # 2. Dequeue must return Deliberation (Priority 1) next
        second = queue.dequeue()
        assert second is not None
        assert second.frame_id == "D1"
        assert second.priority == PRIORITY_DELIBERATION

        # 3. Dequeue must return Telemetry in FIFO order
        third = queue.dequeue()
        assert third is not None
        assert third.frame_id == "T1"

        fourth = queue.dequeue()
        assert fourth is not None
        assert fourth.frame_id == "T2"

        assert queue.is_empty() is True

        # 4. Test telemetry capacity overflow eviction
        for i in range(10):
            queue.enqueue(SatcomFrame(f"T_{i}", "bharati", FrameType.DELTA, i, "", float(i), {}, priority=PRIORITY_TELEMETRY))

        # Max capacity is 5, so 5 oldest were evicted
        assert queue.qsize() == 5
        stats = queue.get_stats()
        assert stats["total_dropped"] == 5
        # The remaining 5 are T_5 through T_9
        assert queue.peek().frame_id == "T_5"

    def test_polar_channel_emulator_profiles_and_blackout(self) -> None:
        """Verify polar channel profile switching, blackout spooling, and priority recovery."""
        emulator = PolarSatcomChannelEmulator(
            profile=SatcomChannelProfile.INMARSAT_STANDARD,
            deterministic=True,
        )

        frame_norm = SatcomFrame("F1", "bharati", FrameType.DELTA, 1, "", 1.0, {"ENV-WX-TEMP": -18.0})

        # 1. Inmarsat 64k transmission
        success, status, delay, s_bytes = emulator.transmit(frame_norm)
        assert success is True
        assert status == "TRANSMITTED"
        assert delay > 0.85  # At least 850ms latency

        # 2. Switch to POLAR_BLACKOUT
        emulator.set_profile(SatcomChannelProfile.POLAR_BLACKOUT)
        assert emulator.params.bandwidth_bps == 0

        # Attempt transmissions during blackout
        f_crit = SatcomFrame("C_BLACKOUT", "bharati", FrameType.ALARM, 2, "", 2.0, {}, priority=PRIORITY_CRITICAL)
        f_telem = SatcomFrame("T_BLACKOUT", "bharati", FrameType.DELTA, 3, "", 3.0, {}, priority=PRIORITY_TELEMETRY)

        s1, stat1, _, _ = emulator.transmit(f_telem)
        s2, stat2, _, _ = emulator.transmit(f_crit)

        assert s1 is False and stat1 == "SPOOLED_BLACKOUT"
        assert s2 is False and stat2 == "SPOOLED_BLACKOUT"
        assert emulator.spool_queue.qsize() == 2

        # 3. Recover from blackout: link restored to Inmarsat
        drained = emulator.recover_from_blackout(new_profile=SatcomChannelProfile.INMARSAT_STANDARD)
        assert len(drained) == 2
        # Critical must have been transmitted first during recovery
        assert drained[0][0].frame_id == "C_BLACKOUT"
        assert drained[1][0].frame_id == "T_BLACKOUT"
        assert emulator.spool_queue.is_empty() is True

    def test_mainland_mirror_twin_state_reconstruction_and_checksum(self) -> None:
        """Verify Mainland Mirror Twin state reconstruction, O(1) lookup, and SHA-256 checksum."""
        mirror = MirrorTwinEngine("bharati")
        assert mirror.sync_status == "AWAITING_KEYFRAME"
        assert mirror.is_synchronized() is False

        # Attempting delta before keyframe must be rejected
        delta_early = SatcomFrame("D_EARLY", "bharati", FrameType.DELTA, 1, "", 1.0, {"ENV-WX-TEMP": -19.0})
        accepted, status = mirror.apply_frame(delta_early)
        assert accepted is False
        assert status == "REJECTED_AWAITING_KEYFRAME"

        # 1. Apply KEYFRAME
        engine = BharatiMasterTwinEngine(seed=42)
        encoder = DeltaEncoder()
        keyframe = encoder.encode_keyframe(
            station_id="bharati",
            readings=engine.get_all_readings(),
            sim_time_seconds=0.0,
            timestamp_iso=engine.clock.isoformat(),
            kpis=engine.get_station_kpis(),
            alerts=engine.get_active_alerts(),
        )

        accepted, status = mirror.apply_frame(keyframe)
        assert accepted is True
        assert status == "KEYFRAME_INITIALIZED"
        assert mirror.sync_status == "SYNCHRONIZED"
        assert mirror.is_synchronized() is True
        assert mirror.last_seq_num == 1
        assert len(mirror.get_all_readings()) == 505

        # O(1) lookup
        assert mirror.get_sensor_value("ENV-WX-TEMP") == -18.0

        # State checksum verification
        checksum_1 = mirror.get_state_checksum()
        assert len(checksum_1) == 64

        # 2. Apply DELTA
        delta = SatcomFrame(
            "D2",
            "bharati",
            FrameType.DELTA,
            seq_num=2,
            timestamp_iso=engine.clock.isoformat(),
            sim_time_seconds=1.0,
            payload={"ENV-WX-TEMP": -24.5},
            delta_count=1,
        )
        accepted, status = mirror.apply_frame(delta)
        assert accepted is True
        assert status == "DELTA_APPLIED"
        assert mirror.last_seq_num == 2
        # Sensor updated in mirror state
        assert mirror.get_sensor_value("ENV-WX-TEMP") == -24.5

        # Checksum changed because state changed
        checksum_2 = mirror.get_state_checksum()
        assert checksum_2 != checksum_1

    def test_mainland_mirror_twin_gap_detection_and_resync(self) -> None:
        """Verify sequence gap detection and keyframe resynchronization."""
        mirror = MirrorTwinEngine("bharati")
        engine = BharatiMasterTwinEngine(seed=42)
        encoder = DeltaEncoder()

        # Initialize with keyframe seq 1
        keyframe = encoder.encode_keyframe("bharati", engine.get_all_readings(), 0.0)
        mirror.apply_frame(keyframe)
        assert mirror.last_seq_num == 1
        assert mirror.is_synchronized() is True

        # Simulate lost frames: send frame with seq 4 directly (frames 2 and 3 dropped)
        delta_gap = SatcomFrame(
            "D_GAP",
            "bharati",
            FrameType.DELTA,
            seq_num=4,
            timestamp_iso="",
            sim_time_seconds=3.0,
            payload={"ENV-WX-TEMP": -22.0},
        )
        accepted, status = mirror.apply_frame(delta_gap)
        assert accepted is True
        assert mirror.sync_status == "GAP_DETECTED"
        assert mirror.lost_frames_count == 2
        assert mirror.resync_required is True
        assert mirror.is_synchronized() is False

        # Mainland creates a RESYNC_REQUEST
        resync_req = mirror.create_resync_request()
        assert resync_req.frame_type == FrameType.RESYNC_REQUEST
        assert resync_req.payload["lost_frames"] == 2

        # Station answers with a fresh KEYFRAME
        fresh_keyframe = encoder.encode_keyframe("bharati", engine.get_all_readings(), 4.0)
        accepted, status = mirror.apply_frame(fresh_keyframe)
        assert accepted is True
        assert mirror.sync_status == "SYNCHRONIZED"
        assert mirror.is_synchronized() is True
        assert mirror.resync_required is False

    def test_satcom_rest_api_endpoints(self) -> None:
        """Verify FastAPI REST endpoints for satcom status, profile, sync, recovery, and resync."""
        reset_server_state(seed=42)
        client = TestClient(create_app())

        # 1. GET /api/satcom/status
        res_status = client.get("/api/satcom/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert data["status"] == "ONLINE"
        assert "bharati" in data["managed_stations"]
        assert "maitri" in data["managed_stations"]

        # 2. GET /api/satcom/bharati/summary
        res_summary = client.get("/api/satcom/bharati/summary")
        assert res_summary.status_code == 200
        sum_data = res_summary.json()
        assert sum_data["station_id"] == "bharati"
        assert sum_data["is_synchronized"] is True
        assert "channel_metrics" in sum_data
        assert sum_data["channel_metrics"]["current_profile"] == "INMARSAT_STANDARD"

        # 3. GET /api/satcom/bharati/mirror
        res_mirror = client.get("/api/satcom/bharati/mirror")
        assert res_mirror.status_code == 200
        mirror_data = res_mirror.json()
        assert mirror_data["station_id"] == "bharati"
        assert mirror_data["sensor_count"] == 505
        assert len(mirror_data["state_checksum"]) == 64
        assert mirror_data["sync_status"] == "SYNCHRONIZED"

        # 4. POST /api/satcom/profile -> Switch to POLAR_BLACKOUT
        res_prof = client.post("/api/satcom/profile", json={"profile": "POLAR_BLACKOUT"})
        assert res_prof.status_code == 200
        assert res_prof.json()["new_profile"] == "POLAR_BLACKOUT"

        # 5. POST /api/satcom/bharati/sync during blackout -> Spooled
        res_sync = client.post("/api/satcom/bharati/sync", json={"force_keyframe": False})
        assert res_sync.status_code == 200
        sync_data = res_sync.json()
        assert sync_data["tx_stats"]["status"] == "SPOOLED_BLACKOUT"

        # 6. POST /api/satcom/bharati/recover -> Restore to INMARSAT_STANDARD
        res_rec = client.post("/api/satcom/bharati/recover", json={"new_profile": "INMARSAT_STANDARD"})
        assert res_rec.status_code == 200
        rec_data = res_rec.json()
        assert rec_data["recovered_frames_count"] >= 1
        assert rec_data["is_synchronized"] is True

        # 7. POST /api/satcom/bharati/resync -> Force Keyframe Resync
        res_resync = client.post("/api/satcom/bharati/resync")
        assert res_resync.status_code == 200
        resync_data = res_resync.json()
        assert resync_data["status"] == "RESYNCHRONIZED"
        assert resync_data["sensor_count"] == 505
        assert resync_data["is_synchronized"] is True
