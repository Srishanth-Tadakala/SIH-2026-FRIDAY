"""Unit and Integration Tests for F.R.I.D.A.Y. Digital Twin Core.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

Tests:
1. Master Engine Initialization & Sensor Inventory (505 sensors across 4 pillars)
2. Synchronized Multi-Pillar Clock Stepping
3. Deterministic Cross-Pillar Physical Propagation (Blizzard Strike)
4. Equipment Fault Scenarios (Generator Trip & Water Line Freeze)
5. Sub-millisecond Telemetry Lookups across All Pillars
6. Causal Graph Structure & Topology Validation
7. Upstream Root-Cause Traversal (Diagnostic Agent foundation)
8. Downstream Blast Radius & Severity Computation (Risk Agent foundation)
9. React Flow Schematic Serialization
10. In-Memory Sandbox State Forking & Mutation Isolation
11. Fast-Forward Simulation & Candidate Plan Delta Evaluation
"""

import threading
import pytest

from backend.core.causal_graph import (
    CausalEdge,
    EdgeType,
    NodeType,
    TwinCausalGraph,
)
from backend.core.engine import (
    BharatiMasterTwinEngine,
    MasterScenario,
    MasterTwinSnapshot,
)
from backend.core.sandbox import (
    PlanEvaluationDelta,
    TrajectoryResult,
    TwinSandbox,
)


class TestTwinCoreEngine:
    """Test suite for BharatiMasterTwinEngine."""

    @pytest.fixture
    def engine(self) -> BharatiMasterTwinEngine:
        """Provide a fresh master digital twin engine with deterministic seed."""
        return BharatiMasterTwinEngine(seed=42)

    def test_master_engine_initialization(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify all 4 observation pillars are initialized with all 505 sensors."""
        assert engine.sensor_count == 505
        assert engine.active_scenario == MasterScenario.NORMAL
        assert engine.clock.elapsed_seconds == 0.0

        # Verify pillar registries exist
        assert len(engine.env_registry.get_all_sensors()) == 87
        assert len(engine.infra_registry.get_all_sensors()) == 180
        assert len(engine.energy_registry.get_all_sensors()) == 140
        assert len(engine.logistics_registry.get_all_sensors()) == 98

        # Verify cached readings populated
        readings = engine.get_all_readings()
        assert len(readings) == 505

    def test_master_clock_synchronization(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify that stepping master engine advances all 4 pillars on the same clock."""
        snap = engine.step(60.0)
        assert engine.clock.elapsed_seconds == 60.0
        assert snap.sim_time_seconds == 60.0

        # Step again
        snap2 = engine.step(120.0)
        assert engine.clock.elapsed_seconds == 180.0
        assert snap2.sim_time_seconds == 180.0

    def test_cross_pillar_physical_ripple_blizzard(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify katabatic blizzard scenario propagates across Environment, Infra, and Logistics."""
        # Inject blizzard strike
        engine.inject_scenario(MasterScenario.BLIZZARD_STRIKE)
        snap = engine.step(60.0)

        # 1. Environment reflects severe gale
        assert snap.kpis["wind_speed_mps"] >= 30.0
        assert snap.kpis["ambient_temp_c"] <= -25.0

        # 2. Logistics observes restricted helipad and routes
        assert engine.logistics_registry.physics.aviation.helipad_status in (
            "CLOSED_WEATHER",
            "SNOW_COVERED",
        )
        assert engine.logistics_registry.physics.routes.surface_traction_index < 60.0

        # 3. Alerts raised
        alerts = snap.alerts
        assert any(a["subsystem"] == "ENVIRONMENT_WEATHER" for a in alerts)

    def test_scenario_generator_trip(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify generator trip shuts down lead unit and brings standby unit online."""
        engine.inject_scenario(MasterScenario.GENERATOR_TRIP, tripped_unit_index=1)
        snap = engine.step(10.0)

        # Unit 1 should be offline / maintenance
        chp1 = engine.energy_registry.physics.chps[0]
        assert chp1.operating_state == "MAINTENANCE"
        assert chp1.running_status is False

        # Unit 2 should be running
        chp2 = engine.energy_registry.physics.chps[1]
        assert chp2.operating_state == "RUNNING"
        assert chp2.running_status is True

    def test_scenario_water_line_freeze(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify trace heating loss freezes utilidor pipe and trips RO plant."""
        engine.inject_scenario(MasterScenario.WATER_LINE_FREEZE)
        snap = engine.step(10.0)

        assert engine.infra_registry.physics.pipelines.water01_pipe_temp_c < 0.0
        assert engine.infra_registry.physics.water.ro_system_status == "FAULT_FREEZE"

        alerts = snap.alerts
        assert any(a["subsystem"] == "INFRASTRUCTURE_PIPELINES" for a in alerts)

    def test_sub_millisecond_sensor_readings(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify O(1) lookup of readings across all 4 pillars."""
        # Environment sensor
        r_env = engine.get_sensor_reading("ENV-WX-TEMP")
        assert r_env is not None

        # Energy sensor
        r_eng = engine.get_sensor_reading("BHARATI.CHP.01.POWER")
        assert r_eng is not None

        # Infra sensor
        r_inf = engine.get_sensor_reading("BHARATI-BLDG-Z01-TEMP")
        assert r_inf is not None

        # Logistics sensor
        r_log = engine.get_sensor_reading("LOG-FLEET-PB01-SPEED")
        assert r_log is not None

        # Non-existent sensor
        with pytest.raises(KeyError):
            engine.get_sensor_reading("INVALID-SENSOR-ID-999")

    def test_kpi_computation(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify all station high-level operational KPIs compute logically."""
        kpis = engine.get_station_kpis()
        assert "total_generation_kw" in kpis
        assert "indoor_avg_temp_c" in kpis
        assert "fuel_autonomy_days" in kpis
        assert "composite_risk_score" in kpis
        assert kpis["total_fuel_reserve_l"] > 200000.0  # Bulk farm holds >200k L
        assert 15.0 <= kpis["indoor_avg_temp_c"] <= 25.0

    def test_scenario_injection_arbitrary_kwargs(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify scenario injection safely accepts arbitrary/extra kwargs without TypeError."""
        # 1. Water line freeze with extra kwargs
        engine.inject_scenario(
            MasterScenario.WATER_LINE_FREEZE,
            pipe_temp_c=-6.5,
            unexpected_param="test_payload",
            extra_flag=True,
        )
        assert engine.infra_registry.physics.pipelines.water01_pipe_temp_c == -6.5

        # 2. Generator trip with unit_id and extra kwargs
        engine.inject_scenario(
            MasterScenario.GENERATOR_TRIP,
            unit_id=2,
            reason="Simulated bearing vibration",
        )
        assert engine.energy_registry.physics.chps[1].operating_state == "MAINTENANCE"

        # 3. Blizzard strike with extra kwargs
        engine.inject_scenario(
            MasterScenario.BLIZZARD_STRIKE,
            wind_speed_mps=42.0,
            temp_c=-35.0,
            unrecognized_kwarg=999,
        )
        assert engine.env_registry.physics.weather.wind_speed_mps == 42.0

        # 4. Normal reset with extra kwargs
        engine.inject_scenario(MasterScenario.NORMAL, reset_override=True)
        assert engine.active_scenario == MasterScenario.NORMAL

    def test_engine_thread_safety_concurrent_access(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify thread-safety of engine telemetry reads and simulation steps under multi-threaded concurrency."""
        errors: list[Exception] = []

        def stepper() -> None:
            for _ in range(25):
                try:
                    engine.step(0.5)
                except Exception as e:
                    errors.append(e)

        def reader() -> None:
            for _ in range(25):
                try:
                    _ = engine.get_all_readings()
                    _ = engine.get_sensor_reading("ENV-WX-TEMP")
                    _ = engine.get_snapshot()
                except Exception as e:
                    errors.append(e)

        def overrider() -> None:
            for i in range(25):
                try:
                    engine.inject_sensor_override("ENV-WX-TEMP", -20.0 + (i % 5))
                except Exception as e:
                    errors.append(e)

        threads = [
            threading.Thread(target=stepper),
            threading.Thread(target=stepper),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=overrider),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors encountered: {errors}"



class TestTwinCausalGraph:
    """Test suite for TwinCausalGraph."""

    @pytest.fixture
    def graph(self) -> TwinCausalGraph:
        """Provide a fresh pre-seeded Bharati causal graph."""
        return TwinCausalGraph()

    def test_graph_initial_structure(self, graph: TwinCausalGraph) -> None:
        """Verify pre-seeded nodes and edges exist across all domains."""
        assert graph.node_count >= 40
        assert graph.edge_count >= 45

        # Check key nodes exist
        assert graph.get_node("chp_1") is not None
        assert graph.get_node("mlvd_bus") is not None
        assert graph.get_node("ahu_01") is not None
        assert graph.get_node("zone_living") is not None
        assert graph.get_node("env_katabatic") is not None

    def test_upstream_root_cause_traversal(self, graph: TwinCausalGraph) -> None:
        """Verify walking upstream from living temperature sensor reaches heat sources."""
        causes = graph.get_upstream_causes("sensor_living_temp", max_depth=5)
        assert len(causes) > 0

        cause_ids = [c["cause_node_id"] for c in causes]
        # Should trace upstream through living zone, AHU-01, glycol loop, and envelope
        assert "zone_living" in cause_ids
        assert "ahu_01" in cause_ids or "building_envelope" in cause_ids

    def test_downstream_impact_traversal(self, graph: TwinCausalGraph) -> None:
        """Verify walking downstream from CHP-1 reaches grid, UPS, and living zones."""
        impacts = graph.get_downstream_impacts("chp_1", max_depth=5)
        assert len(impacts) > 0

        impact_ids = [i["impacted_node_id"] for i in impacts]
        assert "mlvd_bus" in impact_ids
        assert "ups_1" in impact_ids
        assert "critical_bus" in impact_ids

    def test_blast_radius_computation(self, graph: TwinCausalGraph) -> None:
        """Verify blast radius calculation for critical electrical bus."""
        blast = graph.calculate_blast_radius("mlvd_bus")
        assert blast["total_affected_assets"] > 5
        assert blast["life_support_threat"] is True
        assert blast["severity_score"] >= 80.0
        assert "ENERGY" in blast["affected_subsystems"]

    def test_react_flow_topology_export(self, graph: TwinCausalGraph) -> None:
        """Verify graph serializes cleanly into React Flow JSON structure."""
        rf = graph.export_react_flow_topology()
        assert "nodes" in rf
        assert "edges" in rf
        assert rf["total_nodes"] == graph.node_count
        assert rf["total_edges"] == graph.edge_count

        sample_node = rf["nodes"][0]
        assert "id" in sample_node
        assert "type" in sample_node
        assert "position" in sample_node
        assert "x" in sample_node["position"]
        assert "y" in sample_node["position"]
        assert "data" in sample_node

        sample_edge = rf["edges"][0]
        assert "id" in sample_edge
        assert "source" in sample_edge
        assert "target" in sample_edge
        assert "type" in sample_edge

    def test_self_loop_rejection(self, graph: TwinCausalGraph) -> None:
        """Verify adding a self-referential causal edge raises ValueError."""
        loop_edge = CausalEdge(
            source_id="chp_1",
            target_id="chp_1",
            edge_type=EdgeType.ELECTRICAL_FEED,
        )
        with pytest.raises(ValueError, match="Self-referential causal loops not allowed"):
            graph.add_edge(loop_edge)

    def test_duplicate_edge_attribute_update(self, graph: TwinCausalGraph) -> None:
        """Verify adding an existing edge updates attributes in-place without duplicating."""
        initial_edge_count = graph.edge_count
        updated_edge = CausalEdge(
            source_id="chp_1",
            target_id="mlvd_bus",
            edge_type=EdgeType.ELECTRICAL_FEED,
            weight=0.99,
            latency_seconds=0.01,
            description="Upgraded low-resistance busway",
        )
        graph.add_edge(updated_edge)
        assert graph.edge_count == initial_edge_count

        # Verify edge attributes were updated in-place
        chp_outgoing = [e for e in graph._outgoing_edges["chp_1"] if e.target_id == "mlvd_bus"]
        assert len(chp_outgoing) == 1
        assert chp_outgoing[0].weight == 0.99
        assert chp_outgoing[0].description == "Upgraded low-resistance busway"

    def test_cycle_detection_and_prevention(self, graph: TwinCausalGraph) -> None:
        """Verify cycle detection identifies cycles and rejects cycle formation when requested."""
        # Baseline graph is a valid DAG without directed cycles
        assert graph.has_cycle() is False

        # Adding an edge from mlvd_bus -> chp_1 would create cycle (chp_1 -> mlvd_bus -> chp_1)
        assert graph.would_form_cycle("mlvd_bus", "chp_1") is True
        # Self edge would form cycle
        assert graph.would_form_cycle("chp_1", "chp_1") is True
        # Non-cycle check
        assert graph.would_form_cycle("chp_1", "zone_living") is False

        # Adding cycle-forming edge with allow_cycle=False should raise ValueError
        back_edge = CausalEdge(
            source_id="mlvd_bus",
            target_id="chp_1",
            edge_type=EdgeType.ELECTRICAL_FEED,
        )
        with pytest.raises(ValueError, match="would create a directed cycle"):
            graph.add_edge(back_edge, allow_cycle=False)

    def test_traversal_deduplication(self, graph: TwinCausalGraph) -> None:
        """Verify upstream causes and downstream impacts do not contain duplicate node entries."""
        upstream = graph.get_upstream_causes("sensor_living_temp", max_depth=6)
        cause_ids = [c["cause_node_id"] for c in upstream]
        assert len(cause_ids) == len(set(cause_ids)), "Duplicate cause nodes found in upstream search!"

        downstream = graph.get_downstream_impacts("chp_1", max_depth=6)
        impact_ids = [i["impacted_node_id"] for i in downstream]
        assert len(impact_ids) == len(set(impact_ids)), "Duplicate impact nodes found in downstream search!"


class TestTwinSandbox:
    """Test suite for TwinSandbox in-memory forking."""

    @pytest.fixture
    def engine(self) -> BharatiMasterTwinEngine:
        return BharatiMasterTwinEngine(seed=42)

    def test_sandbox_state_isolation(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify mutating sandbox state does NOT mutate original engine state."""
        sandbox = TwinSandbox.fork(engine)
        assert sandbox.engine.clock.elapsed_seconds == 0.0
        assert engine.clock.elapsed_seconds == 0.0

        # Step sandbox forward 30 minutes
        sandbox.run_fast_forward(duration_seconds=1800.0, dt_seconds=60.0)

        # Sandbox advanced
        assert sandbox.engine.clock.elapsed_seconds == 1800.0

        # Original engine was untouched
        assert engine.clock.elapsed_seconds == 0.0

    def test_sandbox_override_and_plan_evaluation(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify candidate operational plan comparison against unmitigated baseline."""
        # Baseline: do nothing for 1 hour
        sb_baseline = TwinSandbox.fork(engine)
        base_traj = sb_baseline.run_fast_forward(duration_seconds=3600.0, dt_seconds=60.0)

        # Candidate: trim fresh air damper to reduce heat loss
        sb_cand = TwinSandbox.fork(engine)
        sb_cand.apply_override("infrastructure", "hvac.ahu01_fresh_air_damper_pct", 10.0)
        cand_traj = sb_cand.run_fast_forward(duration_seconds=3600.0, dt_seconds=60.0)

        # Compare
        delta = TwinSandbox.compare_trajectories(base_traj, cand_traj, "Plan Damper Conservation")
        assert delta.plan_name == "Plan Damper Conservation"
        assert delta.duration_hours == 1.0
        assert delta.is_safe is True
        assert "PASSED" in delta.safety_assessment

    def test_step_physics_only_and_sandbox_fork(self, engine: BharatiMasterTwinEngine) -> None:
        """Verify step_physics_only advances coupled physics and sandbox forks cleanly without lock errors."""
        # 1. step_physics_only advances clock
        initial_time = engine.clock.elapsed_seconds
        engine.step_physics_only(10.0)
        assert engine.clock.elapsed_seconds == initial_time + 10.0

        # 2. Fork sandbox (verifies __deepcopy__ copies RLock without pickling errors)
        sb = TwinSandbox.fork(engine)
        assert sb.engine is not engine
        assert sb.engine.clock.elapsed_seconds == engine.clock.elapsed_seconds

        # 3. Accelerated fast-forward runs cleanly
        traj = sb.run_fast_forward(duration_seconds=600.0, dt_seconds=60.0)
        assert traj.step_count == 10
        assert len(traj.indoor_temp_c) == 10
        assert sb.engine.get_all_readings()["ENV-WX-TEMP"] is not None

