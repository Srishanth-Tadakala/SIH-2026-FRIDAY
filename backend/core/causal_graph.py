"""Topological Causal Dependency Graph for Bharati Station Digital Twin.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
Target: Bharati Research Station, Larsemann Hills, East Antarctica.

ARCHITECTURAL PRINCIPLES:
1. Explicit Causal Modeling: Encodes physical, electrical, thermal, hydraulic, and
   environmental dependencies as a directed acyclic / cyclic graph.
2. Root-Cause Traversal: Enables Diagnostic Agents to trace anomalies upstream to
   the originating physical failure in O(V + E) time.
3. Blast Radius Computation: Enables Risk & Impact Agents to compute cascading
   failure severity across life-support and mission assets.
4. React Flow Compatibility: Directly exports nodes, positions, and styling tokens
   for the frontend tactical topological schematic.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class NodeType(str, Enum):
    """Categorization of topological nodes in the station digital twin."""
    ENVIRONMENT_SOURCE = "ENVIRONMENT_SOURCE"
    EQUIPMENT_ASSET = "EQUIPMENT_ASSET"
    DISTRIBUTION_BUS = "DISTRIBUTION_BUS"
    ZONE_ENCLOSURE = "ZONE_ENCLOSURE"
    STORAGE_RESERVOIR = "STORAGE_RESERVOIR"
    PHYSICAL_SENSOR = "PHYSICAL_SENSOR"
    MISSION_ENTITY = "MISSION_ENTITY"


class EdgeType(str, Enum):
    """Physical and operational relationship types linking station nodes."""
    THERMAL_TRANSFER = "THERMAL_TRANSFER"
    ELECTRICAL_FEED = "ELECTRICAL_FEED"
    HYDRAULIC_FLOW = "HYDRAULIC_FLOW"
    FUEL_SUPPLY = "FUEL_SUPPLY"
    ATMOSPHERIC_EXPOSURE = "ATMOSPHERIC_EXPOSURE"
    SENSOR_OBSERVATION = "SENSOR_OBSERVATION"
    LOGICAL_INTERLOCK = "LOGICAL_INTERLOCK"


@dataclass
class CausalNode:
    """Individual node within the station causal dependency topology."""
    node_id: str
    name: str
    node_type: NodeType
    subsystem: str
    criticality: int = 3  # 1 (low) to 5 (life-support / mission fatal)
    x: float = 0.0  # 2D schematic coordinate for React Flow
    y: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalEdge:
    """Directed causal dependency between two station nodes."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0  # Strength of causal propagation (0.1 to 1.0)
    latency_seconds: float = 0.0  # Physical time delay for ripple
    description: str = ""


class TwinCausalGraph:
    """High-performance in-memory directed causal graph for Bharati Station."""

    def __init__(self) -> None:
        self._nodes: dict[str, CausalNode] = {}
        self._outgoing_edges: dict[str, list[CausalEdge]] = {}
        self._incoming_edges: dict[str, list[CausalEdge]] = {}

        # Pre-seed graph with complete Bharati Station topology
        self._initialize_bharati_topology()

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._outgoing_edges.values())

    def add_node(self, node: CausalNode) -> None:
        """Register a node in the causal graph."""
        self._nodes[node.node_id] = node
        if node.node_id not in self._outgoing_edges:
            self._outgoing_edges[node.node_id] = []
        if node.node_id not in self._incoming_edges:
            self._incoming_edges[node.node_id] = []

    def add_edge(self, edge: CausalEdge, allow_cycle: bool = True) -> None:
        """Add a directed causal edge between two registered nodes with cycle and duplicate guards."""
        if edge.source_id not in self._nodes:
            raise KeyError(f"Source node '{edge.source_id}' does not exist in causal graph.")
        if edge.target_id not in self._nodes:
            raise KeyError(f"Target node '{edge.target_id}' does not exist in causal graph.")

        if edge.source_id == edge.target_id:
            raise ValueError(f"Self-referential causal loops not allowed on node '{edge.source_id}'.")

        # Duplicate edge guard: update existing edge attributes in-place if duplicate is added
        for existing in self._outgoing_edges[edge.source_id]:
            if existing.target_id == edge.target_id and existing.edge_type == edge.edge_type:
                existing.weight = edge.weight
                existing.latency_seconds = edge.latency_seconds
                existing.description = edge.description
                return

        if not allow_cycle and self.would_form_cycle(edge.source_id, edge.target_id):
            raise ValueError(
                f"Adding causal edge '{edge.source_id}' -> '{edge.target_id}' would create a directed cycle."
            )

        self._outgoing_edges[edge.source_id].append(edge)
        self._incoming_edges[edge.target_id].append(edge)

    def would_form_cycle(self, source_id: str, target_id: str) -> bool:
        """Check if adding an edge source_id -> target_id would form a directed cycle.
        
        Returns True if target_id can already reach source_id via existing outgoing edges.
        """
        if source_id == target_id:
            return True
        visited: set[str] = {target_id}
        queue: deque[str] = deque([target_id])
        while queue:
            curr = queue.popleft()
            if curr == source_id:
                return True
            for edge in self._outgoing_edges.get(curr, []):
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append(edge.target_id)
        return False

    def has_cycle(self) -> bool:
        """Detect whether the causal graph contains any directed cycle (using DFS 3-color traversal)."""
        # 0 = WHITE (unvisited), 1 = GRAY (visiting in current path), 2 = BLACK (visited & resolved)
        color: dict[str, int] = {node_id: 0 for node_id in self._nodes}

        def dfs(u: str) -> bool:
            color[u] = 1
            for edge in self._outgoing_edges.get(u, []):
                v = edge.target_id
                if color.get(v, 0) == 1:
                    return True
                if color.get(v, 0) == 0:
                    if dfs(v):
                        return True
            color[u] = 2
            return False

        for node_id in self._nodes:
            if color[node_id] == 0:
                if dfs(node_id):
                    return True
        return False

    def get_node(self, node_id: str) -> CausalNode | None:
        """Lookup node by identifier."""
        return self._nodes.get(node_id)

    def get_upstream_causes(
        self,
        node_id: str,
        max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Traverse incoming edges to isolate potential upstream root causes.
        
        Used by the Diagnostic / Root-Cause Agent.
        """
        if node_id not in self._nodes:
            return []

        results: list[dict[str, Any]] = []
        recorded_causes: set[str] = set()
        visited: set[str] = {node_id}
        queue: deque[tuple[str, list[str], list[str], float, int]] = deque([
            (node_id, [node_id], [], 0.0, 0)
        ])

        while queue:
            curr_id, path, edge_types, cum_latency, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in self._incoming_edges.get(curr_id, []):
                parent_id = edge.source_id
                parent_node = self._nodes[parent_id]
                new_path = [parent_id] + path
                new_edge_types = [edge.edge_type.value] + edge_types
                new_latency = cum_latency + edge.latency_seconds

                if parent_id not in recorded_causes:
                    recorded_causes.add(parent_id)
                    results.append({
                        "cause_node_id": parent_id,
                        "cause_name": parent_node.name,
                        "cause_type": parent_node.node_type.value,
                        "subsystem": parent_node.subsystem,
                        "criticality": parent_node.criticality,
                        "depth": depth + 1,
                        "cumulative_latency_seconds": round(new_latency, 2),
                        "path": new_path,
                        "edge_types": new_edge_types,
                        "causal_weight": edge.weight,
                    })

                if parent_id not in visited:
                    visited.add(parent_id)
                    queue.append((parent_id, new_path, new_edge_types, new_latency, depth + 1))

        # Sort by proximity (depth) and weight
        results.sort(key=lambda r: (r["depth"], -r["causal_weight"]))
        return results

    def get_downstream_impacts(
        self,
        node_id: str,
        max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Traverse outgoing edges to compute downstream consequences.
        
        Used by the Risk & Impact Agent.
        """
        if node_id not in self._nodes:
            return []

        results: list[dict[str, Any]] = []
        recorded_impacts: set[str] = set()
        visited: set[str] = {node_id}
        queue: deque[tuple[str, list[str], list[str], float, int]] = deque([
            (node_id, [node_id], [], 0.0, 0)
        ])

        while queue:
            curr_id, path, edge_types, cum_latency, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in self._outgoing_edges.get(curr_id, []):
                child_id = edge.target_id
                child_node = self._nodes[child_id]
                new_path = path + [child_id]
                new_edge_types = edge_types + [edge.edge_type.value]
                new_latency = cum_latency + edge.latency_seconds

                if child_id not in recorded_impacts:
                    recorded_impacts.add(child_id)
                    results.append({
                        "impacted_node_id": child_id,
                        "impacted_name": child_node.name,
                        "impacted_type": child_node.node_type.value,
                        "subsystem": child_node.subsystem,
                        "criticality": child_node.criticality,
                        "depth": depth + 1,
                        "cumulative_latency_seconds": round(new_latency, 2),
                        "path": new_path,
                        "edge_types": new_edge_types,
                        "causal_weight": edge.weight,
                    })

                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, new_path, new_edge_types, new_latency, depth + 1))

        # Sort by criticality descending, then proximity
        results.sort(key=lambda r: (-r["criticality"], r["depth"]))
        return results

    def calculate_blast_radius(self, node_id: str) -> dict[str, Any]:
        """Compute aggregated blast radius metrics for a potential or actual fault."""
        impacts = self.get_downstream_impacts(node_id, max_depth=6)
        if not impacts and node_id not in self._nodes:
            return {
                "root_node_id": node_id,
                "total_affected_assets": 0,
                "max_criticality": 0,
                "life_support_threat": False,
                "affected_subsystems": [],
                "affected_sensors": [],
                "severity_score": 0.0,
            }

        root_node = self._nodes.get(node_id)
        affected_nodes = {imp["impacted_node_id"]: imp for imp in impacts}
        if root_node:
            affected_nodes[node_id] = {
                "criticality": root_node.criticality,
                "subsystem": root_node.subsystem,
                "impacted_type": root_node.node_type.value,
            }

        crit_dist: dict[int, int] = {i: 0 for i in range(1, 6)}
        subsystems: set[str] = set()
        sensors: list[str] = []
        life_support_threat = False

        for n_id, data in affected_nodes.items():
            c = data["criticality"]
            crit_dist[c] = crit_dist.get(c, 0) + 1
            subsystems.add(data["subsystem"])
            if c >= 5:
                life_support_threat = True
            if data["impacted_type"] == NodeType.PHYSICAL_SENSOR.value:
                sensors.append(n_id)

        # Calculate severity score (0 to 100)
        weighted_crit = (
            crit_dist[5] * 35.0
            + crit_dist[4] * 20.0
            + crit_dist[3] * 10.0
            + crit_dist[2] * 5.0
            + crit_dist[1] * 2.0
        )
        severity_score = min(100.0, round(weighted_crit, 1))

        return {
            "root_node_id": node_id,
            "root_name": root_node.name if root_node else node_id,
            "total_affected_assets": len(affected_nodes),
            "max_criticality": max((d["criticality"] for d in affected_nodes.values()), default=1),
            "life_support_threat": life_support_threat,
            "criticality_distribution": crit_dist,
            "affected_subsystems": sorted(list(subsystems)),
            "affected_sensors": sorted(sensors),
            "severity_score": severity_score,
        }

    def export_react_flow_topology(self) -> dict[str, Any]:
        """Serialize graph to React Flow compatible nodes and animated edges format."""
        rf_nodes: list[dict[str, Any]] = []
        rf_edges: list[dict[str, Any]] = []

        # Map nodes
        for node in self._nodes.values():
            rf_nodes.append({
                "id": node.node_id,
                "type": self._map_react_flow_node_type(node.node_type),
                "position": {"x": node.x, "y": node.y},
                "data": {
                    "label": node.name,
                    "nodeType": node.node_type.value,
                    "subsystem": node.subsystem,
                    "criticality": node.criticality,
                    **node.metadata,
                },
            })

        # Map edges
        edge_idx = 1
        for src_id, edges in self._outgoing_edges.items():
            for edge in edges:
                rf_edges.append({
                    "id": f"edge_{src_id}_{edge.target_id}_{edge_idx}",
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "type": "smoothstep",
                    "animated": edge.edge_type in (
                        EdgeType.ELECTRICAL_FEED,
                        EdgeType.HYDRAULIC_FLOW,
                        EdgeType.THERMAL_TRANSFER,
                    ),
                    "label": edge.edge_type.value,
                    "data": {
                        "edgeType": edge.edge_type.value,
                        "weight": edge.weight,
                        "latency": edge.latency_seconds,
                        "description": edge.description,
                    },
                })
                edge_idx += 1

        return {
            "nodes": rf_nodes,
            "edges": rf_edges,
            "total_nodes": len(rf_nodes),
            "total_edges": len(rf_edges),
        }

    @staticmethod
    def _map_react_flow_node_type(node_type: NodeType) -> str:
        """Map internal node type to React Flow custom component type."""
        mapping = {
            NodeType.ENVIRONMENT_SOURCE: "environmentSourceNode",
            NodeType.EQUIPMENT_ASSET: "equipmentAssetNode",
            NodeType.DISTRIBUTION_BUS: "distributionBusNode",
            NodeType.ZONE_ENCLOSURE: "zoneEnclosureNode",
            NodeType.STORAGE_RESERVOIR: "storageReservoirNode",
            NodeType.PHYSICAL_SENSOR: "sensorTelemetryNode",
            NodeType.MISSION_ENTITY: "missionEntityNode",
        }
        return mapping.get(node_type, "default")

    def _initialize_bharati_topology(self) -> None:
        """Construct the comprehensive topological causal model of Bharati Station."""
        # ---------------------------------------------------------------------
        # 1. Environment Sources
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("env_ambient", "Antarctic Coastal Atmosphere", NodeType.ENVIRONMENT_SOURCE, "ENVIRONMENT", 4, x=100, y=50))
        self.add_node(CausalNode("env_katabatic", "Katabatic Wind Vector", NodeType.ENVIRONMENT_SOURCE, "ENVIRONMENT", 4, x=300, y=50))
        self.add_node(CausalNode("env_solar", "Solar Irradiance (GHI)", NodeType.ENVIRONMENT_SOURCE, "ENVIRONMENT", 2, x=500, y=50))
        self.add_node(CausalNode("env_sea_ice", "Prydz Bay Sea Ice Sheet", NodeType.ENVIRONMENT_SOURCE, "ENVIRONMENT", 3, x=700, y=50))
        self.add_node(CausalNode("env_ocean", "Quilty Bay Seawater", NodeType.ENVIRONMENT_SOURCE, "ENVIRONMENT", 3, x=900, y=50))

        # ---------------------------------------------------------------------
        # 2. Fuel & Energy Generation Module
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("bulk_fuel_farm", "Bulk Fuel Farm (13x 24kL Tanks)", NodeType.STORAGE_RESERVOIR, "ENERGY", 5, x=100, y=250))
        self.add_node(CausalNode("fuel_transfer_pump", "Fuel Transfer Pump Skid", NodeType.EQUIPMENT_ASSET, "ENERGY", 4, x=250, y=250))
        self.add_node(CausalNode("day_tank", "CHP Day Tank (1,500 L)", NodeType.STORAGE_RESERVOIR, "ENERGY", 5, x=400, y=250))

        self.add_node(CausalNode("chp_1", "CHP Unit 1 (100 kVA Scania)", NodeType.EQUIPMENT_ASSET, "ENERGY", 5, x=550, y=200))
        self.add_node(CausalNode("chp_2", "CHP Unit 2 (100 kVA Scania)", NodeType.EQUIPMENT_ASSET, "ENERGY", 5, x=550, y=270))
        self.add_node(CausalNode("chp_3", "CHP Unit 3 (100 kVA Reserve)", NodeType.EQUIPMENT_ASSET, "ENERGY", 4, x=550, y=340))

        self.add_node(CausalNode("mlvd_bus", "Main Low Voltage Distribution (400V)", NodeType.DISTRIBUTION_BUS, "ENERGY", 5, x=750, y=270))
        self.add_node(CausalNode("ups_1", "UPS Plant 1 (60 kVA)", NodeType.EQUIPMENT_ASSET, "ENERGY", 5, x=900, y=220))
        self.add_node(CausalNode("ups_2", "UPS Plant 2 (60 kVA)", NodeType.EQUIPMENT_ASSET, "ENERGY", 5, x=900, y=320))
        self.add_node(CausalNode("critical_bus", "Critical Life-Support Bus (230V)", NodeType.DISTRIBUTION_BUS, "ENERGY", 5, x=1050, y=270))

        # ---------------------------------------------------------------------
        # 3. Thermal Recovery & Hydronic Heating
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("chp_exhaust_hex", "Exhaust Waste Heat Exchangers", NodeType.EQUIPMENT_ASSET, "ENERGY", 4, x=550, y=450))
        self.add_node(CausalNode("glycol_loop", "Primary Hydronic Glycol Loop", NodeType.DISTRIBUTION_BUS, "INFRASTRUCTURE", 5, x=750, y=450))
        self.add_node(CausalNode("heating_buffer_tank", "Thermal Buffer Storage Tank", NodeType.STORAGE_RESERVOIR, "INFRASTRUCTURE", 4, x=900, y=450))

        # ---------------------------------------------------------------------
        # 4. Infrastructure HVAC & Enclosures
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("building_envelope", "Bharati Aerodynamic Envelope", NodeType.ZONE_ENCLOSURE, "INFRASTRUCTURE", 5, x=300, y=600))
        self.add_node(CausalNode("ahu_01", "AHU-01 (Residential & Dining)", NodeType.EQUIPMENT_ASSET, "INFRASTRUCTURE", 5, x=550, y=570))
        self.add_node(CausalNode("ahu_02", "AHU-02 (Labs & Technical)", NodeType.EQUIPMENT_ASSET, "INFRASTRUCTURE", 4, x=550, y=640))
        self.add_node(CausalNode("zone_living", "Living & Accommodation Block", NodeType.ZONE_ENCLOSURE, "INFRASTRUCTURE", 5, x=750, y=570))
        self.add_node(CausalNode("zone_labs", "Scientific Research Labs", NodeType.ZONE_ENCLOSURE, "INFRASTRUCTURE", 4, x=750, y=640))
        self.add_node(CausalNode("zone_medical", "Medical & Surgical Facility", NodeType.ZONE_ENCLOSURE, "INFRASTRUCTURE", 5, x=900, y=570))
        self.add_node(CausalNode("emergency_shelter", "Emergency Refuge Shelter", NodeType.ZONE_ENCLOSURE, "INFRASTRUCTURE", 5, x=900, y=640))

        # ---------------------------------------------------------------------
        # 5. Water & Wastewater Cycle
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("seawater_intake", "Quilty Bay Seawater Intake", NodeType.EQUIPMENT_ASSET, "INFRASTRUCTURE", 4, x=100, y=750))
        self.add_node(CausalNode("utilidor_water_line", "Utilidor Intake Line", NodeType.DISTRIBUTION_BUS, "INFRASTRUCTURE", 4, x=250, y=750))
        self.add_node(CausalNode("ro_plant", "Reverse Osmosis Desalination Plant", NodeType.EQUIPMENT_ASSET, "INFRASTRUCTURE", 5, x=450, y=750))
        self.add_node(CausalNode("potable_reservoir", "Potable Water Reservoir (25,000 L)", NodeType.STORAGE_RESERVOIR, "INFRASTRUCTURE", 5, x=650, y=750))
        self.add_node(CausalNode("mbr_wastewater", "MBR Wastewater Treatment Plant", NodeType.EQUIPMENT_ASSET, "INFRASTRUCTURE", 4, x=850, y=750))

        # ---------------------------------------------------------------------
        # 6. Logistics & Cold Chain
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("reefer_01", "Cold Provisions Reefer-01", NodeType.EQUIPMENT_ASSET, "LOGISTICS", 4, x=1050, y=400))
        self.add_node(CausalNode("pb_01", "PistenBully PB-01 (Lead Hauler)", NodeType.EQUIPMENT_ASSET, "LOGISTICS", 4, x=100, y=900))
        self.add_node(CausalNode("station_ring_route", "Station Perimeter Ground Route", NodeType.MISSION_ENTITY, "LOGISTICS", 3, x=300, y=900))
        self.add_node(CausalNode("helipad", "Bharati Helipad Deck", NodeType.MISSION_ENTITY, "LOGISTICS", 4, x=500, y=900))
        self.add_node(CausalNode("sea_berth", "Quilty Bay Ship Offload Berth", NodeType.MISSION_ENTITY, "LOGISTICS", 3, x=700, y=900))
        self.add_node(CausalNode("fast_ice_route", "Prydz Bay Fast Ice Traverse", NodeType.MISSION_ENTITY, "LOGISTICS", 4, x=900, y=900))

        # ---------------------------------------------------------------------
        # 7. Instrumentation / Representative Sensors
        # ---------------------------------------------------------------------
        self.add_node(CausalNode("sensor_chp1_kw", "BH-ENG-CHP1-001 (Active Power kW)", NodeType.PHYSICAL_SENSOR, "ENERGY", 4, x=650, y=170))
        self.add_node(CausalNode("sensor_fuel_day_lvl", "BH-ENG-FUEL-001 (Day Tank Level)", NodeType.PHYSICAL_SENSOR, "ENERGY", 5, x=400, y=170))
        self.add_node(CausalNode("sensor_living_temp", "BH-INF-BLD-001 (Living Temp °C)", NodeType.PHYSICAL_SENSOR, "INFRASTRUCTURE", 5, x=850, y=530))
        self.add_node(CausalNode("sensor_wind_speed", "BH-ENV-WTH-001 (AWS Wind m/s)", NodeType.PHYSICAL_SENSOR, "ENVIRONMENT", 4, x=300, y=120))
        self.add_node(CausalNode("sensor_reefer_temp", "BH-LOG-COLD-001 (Reefer Core Temp)", NodeType.PHYSICAL_SENSOR, "LOGISTICS", 4, x=1150, y=400))

        # ---------------------------------------------------------------------
        # EDGES: Establish Multi-Pillar Physical Dependencies
        # ---------------------------------------------------------------------
        # Fuel delivery chain
        self.add_edge(CausalEdge("bulk_fuel_farm", "fuel_transfer_pump", EdgeType.FUEL_SUPPLY, weight=1.0, latency_seconds=5.0))
        self.add_edge(CausalEdge("fuel_transfer_pump", "day_tank", EdgeType.FUEL_SUPPLY, weight=1.0, latency_seconds=10.0))
        self.add_edge(CausalEdge("day_tank", "chp_1", EdgeType.FUEL_SUPPLY, weight=1.0, latency_seconds=2.0))
        self.add_edge(CausalEdge("day_tank", "chp_2", EdgeType.FUEL_SUPPLY, weight=1.0, latency_seconds=2.0))
        self.add_edge(CausalEdge("day_tank", "chp_3", EdgeType.FUEL_SUPPLY, weight=1.0, latency_seconds=2.0))
        self.add_edge(CausalEdge("day_tank", "sensor_fuel_day_lvl", EdgeType.SENSOR_OBSERVATION, weight=1.0))

        # Electrical power flow
        self.add_edge(CausalEdge("chp_1", "mlvd_bus", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.1))
        self.add_edge(CausalEdge("chp_2", "mlvd_bus", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.1))
        self.add_edge(CausalEdge("chp_3", "mlvd_bus", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.1))
        self.add_edge(CausalEdge("chp_1", "sensor_chp1_kw", EdgeType.SENSOR_OBSERVATION, weight=1.0))

        self.add_edge(CausalEdge("mlvd_bus", "ups_1", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.05))
        self.add_edge(CausalEdge("mlvd_bus", "ups_2", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.05))
        self.add_edge(CausalEdge("ups_1", "critical_bus", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.01))
        self.add_edge(CausalEdge("ups_2", "critical_bus", EdgeType.ELECTRICAL_FEED, weight=1.0, latency_seconds=0.01))

        # Thermal energy recovery & distribution
        self.add_edge(CausalEdge("chp_1", "chp_exhaust_hex", EdgeType.THERMAL_TRANSFER, weight=0.85, latency_seconds=15.0))
        self.add_edge(CausalEdge("chp_2", "chp_exhaust_hex", EdgeType.THERMAL_TRANSFER, weight=0.85, latency_seconds=15.0))
        self.add_edge(CausalEdge("chp_exhaust_hex", "glycol_loop", EdgeType.THERMAL_TRANSFER, weight=0.90, latency_seconds=30.0))
        self.add_edge(CausalEdge("glycol_loop", "heating_buffer_tank", EdgeType.HYDRAULIC_FLOW, weight=1.0, latency_seconds=20.0))
        self.add_edge(CausalEdge("glycol_loop", "ahu_01", EdgeType.THERMAL_TRANSFER, weight=0.90, latency_seconds=25.0))
        self.add_edge(CausalEdge("glycol_loop", "ahu_02", EdgeType.THERMAL_TRANSFER, weight=0.90, latency_seconds=25.0))

        # Infrastructure loads on power grid
        self.add_edge(CausalEdge("mlvd_bus", "ahu_01", EdgeType.ELECTRICAL_FEED, weight=0.5))
        self.add_edge(CausalEdge("mlvd_bus", "ahu_02", EdgeType.ELECTRICAL_FEED, weight=0.5))
        self.add_edge(CausalEdge("mlvd_bus", "ro_plant", EdgeType.ELECTRICAL_FEED, weight=0.6))
        self.add_edge(CausalEdge("mlvd_bus", "mbr_wastewater", EdgeType.ELECTRICAL_FEED, weight=0.4))
        self.add_edge(CausalEdge("mlvd_bus", "reefer_01", EdgeType.ELECTRICAL_FEED, weight=0.7))
        self.add_edge(CausalEdge("reefer_01", "sensor_reefer_temp", EdgeType.SENSOR_OBSERVATION, weight=1.0))

        # Environmental atmospheric coupling
        self.add_edge(CausalEdge("env_katabatic", "building_envelope", EdgeType.ATMOSPHERIC_EXPOSURE, weight=0.95, latency_seconds=60.0))
        self.add_edge(CausalEdge("env_ambient", "building_envelope", EdgeType.ATMOSPHERIC_EXPOSURE, weight=0.90, latency_seconds=120.0))
        self.add_edge(CausalEdge("env_katabatic", "sensor_wind_speed", EdgeType.SENSOR_OBSERVATION, weight=1.0))
        self.add_edge(CausalEdge("env_katabatic", "helipad", EdgeType.ATMOSPHERIC_EXPOSURE, weight=1.0, latency_seconds=5.0))
        self.add_edge(CausalEdge("env_katabatic", "station_ring_route", EdgeType.ATMOSPHERIC_EXPOSURE, weight=0.8, latency_seconds=30.0))
        self.add_edge(CausalEdge("env_sea_ice", "fast_ice_route", EdgeType.ATMOSPHERIC_EXPOSURE, weight=1.0))
        self.add_edge(CausalEdge("env_ocean", "sea_berth", EdgeType.ATMOSPHERIC_EXPOSURE, weight=0.9))

        # Thermal envelope into indoor zones
        self.add_edge(CausalEdge("building_envelope", "zone_living", EdgeType.THERMAL_TRANSFER, weight=0.85, latency_seconds=180.0))
        self.add_edge(CausalEdge("building_envelope", "zone_labs", EdgeType.THERMAL_TRANSFER, weight=0.85, latency_seconds=180.0))
        self.add_edge(CausalEdge("ahu_01", "zone_living", EdgeType.THERMAL_TRANSFER, weight=0.95, latency_seconds=60.0))
        self.add_edge(CausalEdge("ahu_02", "zone_labs", EdgeType.THERMAL_TRANSFER, weight=0.95, latency_seconds=60.0))
        self.add_edge(CausalEdge("zone_living", "sensor_living_temp", EdgeType.SENSOR_OBSERVATION, weight=1.0))

        # Water cycle
        self.add_edge(CausalEdge("env_ocean", "seawater_intake", EdgeType.HYDRAULIC_FLOW, weight=1.0))
        self.add_edge(CausalEdge("seawater_intake", "utilidor_water_line", EdgeType.HYDRAULIC_FLOW, weight=1.0, latency_seconds=10.0))
        self.add_edge(CausalEdge("utilidor_water_line", "ro_plant", EdgeType.HYDRAULIC_FLOW, weight=1.0, latency_seconds=10.0))
        self.add_edge(CausalEdge("ro_plant", "potable_reservoir", EdgeType.HYDRAULIC_FLOW, weight=1.0, latency_seconds=30.0))
        self.add_edge(CausalEdge("potable_reservoir", "zone_living", EdgeType.HYDRAULIC_FLOW, weight=1.0))
        self.add_edge(CausalEdge("zone_living", "mbr_wastewater", EdgeType.HYDRAULIC_FLOW, weight=0.9, latency_seconds=60.0))

        # Emergency & Medical power dependencies
        self.add_edge(CausalEdge("critical_bus", "zone_medical", EdgeType.ELECTRICAL_FEED, weight=1.0))
        self.add_edge(CausalEdge("critical_bus", "emergency_shelter", EdgeType.ELECTRICAL_FEED, weight=1.0))
        self.add_edge(CausalEdge("bulk_fuel_farm", "pb_01", EdgeType.FUEL_SUPPLY, weight=0.8))
        self.add_edge(CausalEdge("pb_01", "station_ring_route", EdgeType.LOGICAL_INTERLOCK, weight=0.7))
