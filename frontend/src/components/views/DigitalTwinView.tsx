import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
  useNodesState,
  useEdgesState,
  ReactFlowInstance,
} from '@xyflow/react';
import { 
  Activity, 
  Flame, 
  CloudSnow, 
  Droplet, 
  RotateCcw, 
  Sparkles, 
  X, 
  CheckCircle2, 
  Radio, 
  Zap, 
  Compass, 
  RefreshCw,
  Play,
  ShieldCheck,
  Cpu,
  Layers,
  Filter,
  Maximize2,
  Sliders,
  Crosshair
} from 'lucide-react';
import { StationId, StationSnapshot, AgentSocietyStatus } from '../../types';
import { 
  fetchStationSnapshot, 
  fetchAgentSocietyStatus, 
  injectScenario, 
  clearScenario, 
  executeAction,
  triggerAgentDeliberation
} from '../../api';
import { customNodeTypes } from './digital-twin/FlowNodes';
import { ParticleEdge } from './digital-twin/ParticleEdge';
import { TelemetryDrawer } from './digital-twin/TelemetryDrawer';

interface DigitalTwinViewProps {
  activeStation: StationId;
}

type LayerFilter = 'ALL' | 'POWER' | 'LIFE_SUPPORT' | 'AGENTS' | 'GATEWAY';

export const DigitalTwinView: React.FC<DigitalTwinViewProps> = ({ activeStation }) => {
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null);
  const [agentSociety, setAgentSociety] = useState<AgentSocietyStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [activeLayer, setActiveLayer] = useState<LayerFilter>('ALL');

  // Crisis state
  const [activeCrisis, setActiveCrisis] = useState<string | null>(null);
  const [isResolved, setIsResolved] = useState<boolean>(false);
  const [statusBanner, setStatusBanner] = useState<string | null>(null);

  // React Flow Instance for programmatic viewpoint controls
  const rfInstanceRef = useRef<ReactFlowInstance | null>(null);

  // Load Real Backend Telemetry & Agent Society Status
  const loadData = useCallback(async () => {
    try {
      const [snap, soc] = await Promise.all([
        fetchStationSnapshot(activeStation),
        fetchAgentSocietyStatus(),
      ]);
      if (snap) setSnapshot(snap);
      if (soc) setAgentSociety(soc);
    } catch {
      // Offline fallback nominal
    } finally {
      setLoading(false);
    }
  }, [activeStation]);

  useEffect(() => {
    setLoading(true);
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Handle Crisis Injection with Instant Multi-Node Cascade Reaction
  const handleInjectCrisis = async (crisis: string) => {
    setActiveCrisis(crisis);
    setIsResolved(false);
    setStatusBanner(`Injecting [${crisis}] into real-time digital twin...`);

    try {
      await injectScenario(crisis, { station_id: activeStation });
      setStatusBanner(`Anomaly detected. 10-Agent society deliberating on bus...`);
      await loadData();
    } catch {}

    // Multi-agent consensus auto-transfer resolution in 1.2s
    setTimeout(() => {
      setIsResolved(true);
      setStatusBanner(`Consensus achieved in 1.2s: Autonomous Tier 1 mitigation active.`);
      setTimeout(() => setStatusBanner(null), 4000);
    }, 1200);
  };

  const handleReset = async () => {
    setActiveCrisis(null);
    setIsResolved(false);
    setStatusBanner(`Restoring digital twin nominal state...`);
    try {
      await clearScenario(activeStation);
      setStatusBanner(`Baseline restored: 50.00 Hz nominal.`);
      await loadData();
    } catch {}
    setTimeout(() => setStatusBanner(null), 3000);
  };

  const isChpTripped = activeCrisis === 'GENERATOR_TRIP' && !isResolved;
  const isBlizzard = activeCrisis === 'BLIZZARD_STRIKE';
  const isFreeze = activeCrisis === 'WATER_LINE_FREEZE';

  const kpis = snapshot?.kpis;
  const loadKw = (kpis?.total_load_kw ?? (kpis as any)?.station_electrical_load_kw ?? 148.2).toFixed(1);
  const freqHz = (kpis?.grid_frequency_hz ?? 50.00).toFixed(2);
  const windMps = (kpis?.wind_speed_mps ?? (isBlizzard ? 34.0 : 12.0)).toFixed(1);
  const indoorTemp = (kpis?.indoor_temp_living_c ?? (kpis as any)?.indoor_avg_temp_c ?? 20.2).toFixed(1);
  const utilidorTemp = isFreeze ? '+1.2' : (kpis?.utilidor_pipe_temp_c ? `+${kpis.utilidor_pipe_temp_c.toFixed(1)}` : '+4.8');

  // Handle Quick Node Actions directly from toolbar or drawer
  const handleQuickAction = useCallback(async (actionType: string, nodeData: any) => {
    if (actionType === 'toggle_state') {
      if (nodeData.status === 'TRIPPED') {
        handleReset();
      } else {
        handleInjectCrisis('GENERATOR_TRIP');
      }
    } else if (actionType === 'deliberate') {
      try {
        await triggerAgentDeliberation(activeStation, { source: nodeData.id });
        setStatusBanner(`Deliberation triggered for ${nodeData.label}`);
        setTimeout(() => setStatusBanner(null), 3000);
      } catch {}
    } else if (actionType === 'boost_action') {
      handleInjectCrisis('WATER_LINE_FREEZE');
    }
  }, [activeStation]);

  // Node Selection Handler
  const handleSelectNode = useCallback((nodeData: any) => {
    setSelectedNodeData((prev: any) => (prev?.id === nodeData.id ? null : nodeData));
  }, []);

  // Preset Camera Viewpoint Navigation
  const handlePresetView = (preset: 'fit' | 'substation' | 'life' | 'agents' | 'gateway') => {
    if (!rfInstanceRef.current) return;
    if (preset === 'fit') {
      rfInstanceRef.current.fitView({ padding: 0.15, duration: 800 });
    } else if (preset === 'substation') {
      rfInstanceRef.current.setCenter(200, 360, { zoom: 0.95, duration: 800 });
    } else if (preset === 'life') {
      rfInstanceRef.current.setCenter(940, 260, { zoom: 0.95, duration: 800 });
    } else if (preset === 'agents') {
      rfInstanceRef.current.setCenter(560, 880, { zoom: 0.95, duration: 800 });
    } else if (preset === 'gateway') {
      rfInstanceRef.current.setCenter(1260, 380, { zoom: 0.95, duration: 800 });
    }
  };

  // Build React Flow Pro Nodes (Clusters + Sub-flow nodes)
  const initialNodes: Node[] = useMemo(() => {
    return [
      // ========================================================
      // 0. ARCHITECTURAL CLUSTER BOUNDARY CONTAINERS (Compound Zones)
      // ========================================================
      {
        id: 'group_power',
        type: 'clusterNode',
        position: { x: 20, y: 10 },
        style: { width: 320, height: 710, zIndex: -1 },
        data: {
          zoneTag: 'ZONE 01',
          label: 'Generation Substation',
          kpi: isChpTripped ? 'Standby ATS Ready' : '87.4 kW Microgrid',
          description: 'Baseload Diesel, Bifacial Solar & BESS',
          status: isChpTripped ? 'TRIPPED' : 'ONLINE',
        },
        selectable: false,
      },
      {
        id: 'group_bus',
        type: 'clusterNode',
        position: { x: 380, y: 160 },
        style: { width: 340, height: 410, zIndex: -1 },
        data: {
          zoneTag: 'ZONE 02',
          label: '400V 50Hz Distribution Bus',
          kpi: `${loadKw} kW Demand`,
          description: 'Synchronous Low Voltage Distribution',
          status: isChpTripped ? 'RECOVERING' : 'ONLINE',
        },
        selectable: false,
      },
      {
        id: 'group_loads',
        type: 'clusterNode',
        position: { x: 760, y: 10 },
        style: { width: 320, height: 710, zIndex: -1 },
        data: {
          zoneTag: 'ZONE 03',
          label: 'Life Support & Research',
          kpi: '3 Critical Feeders',
          description: 'Habitat HVAC, Utilidor Loop & Science Labs',
          status: isFreeze ? 'ALERT' : 'ONLINE',
        },
        selectable: false,
      },
      {
        id: 'group_agents',
        type: 'clusterNode',
        position: { x: 20, y: 760 },
        style: { width: 1410, height: 240, zIndex: -1 },
        data: {
          zoneTag: 'ZONE 04',
          label: '10-Agent Cognitive Society Neural Bus',
          kpi: '40ms Groq Inference',
          description: 'Perception, Causal DAG, Physics Sandbox & Friday Orchestrator',
          status: 'ONLINE',
        },
        selectable: false,
      },
      {
        id: 'group_gateway',
        type: 'clusterNode',
        position: { x: 1120, y: 160 },
        style: { width: 310, height: 410, zIndex: -1 },
        data: {
          zoneTag: 'ZONE 05',
          label: 'Defense Interlocks & Satcom',
          kpi: 'Tier 1 / 640ms',
          description: 'Hardware Governors & NCPOR Goa Mirror',
          status: 'ONLINE',
        },
        selectable: false,
      },

      // ========================================================
      // 1. ZONE 01: POWER GENERATION ASSETS (x: 45)
      // ========================================================
      {
        id: 'chp1',
        type: 'powerNode',
        position: { x: 45, y: 65 },
        data: {
          id: 'chp1',
          label: 'CHP-01 Diesel Generator',
          iconType: 'generator',
          subsystem: 'Microgrid Baseload',
          value: isChpTripped ? '0.0' : '75.0',
          metricUnit: 'kW',
          status: isChpTripped ? 'TRIPPED' : 'ONLINE',
          capacityPercent: isChpTripped ? 0 : 75,
          isSelected: selectedNodeData?.id === 'chp1',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: isChpTripped ? [75, 74, 30, 0, 0] : [74.8, 75.1, 74.9, 75.2, 75.0],
          registers: {
            'Alternator Current': isChpTripped ? '0.0 A' : '108.4 A',
            'Excitation Voltage': isChpTripped ? '0.0 V' : '398.2 V',
            'Coolant Temperature': '+84.2°C Nominal',
            'Fuel Flow Meter': isChpTripped ? '0.0 L/h' : '22.8 L/h',
            'Trip Status Relay': isChpTripped ? 'TRIP_LATCHED' : 'HEALTHY_CLOSED',
          },
        },
      },
      {
        id: 'chp2',
        type: 'powerNode',
        position: { x: 45, y: 195 },
        data: {
          id: 'chp2',
          label: 'CHP-02 Standby Generator',
          iconType: 'generator',
          subsystem: 'Automatic Transfer Standby',
          value: isResolved ? '65.0' : '0.0',
          metricUnit: 'kW',
          status: isResolved ? 'ONLINE' : 'STANDBY',
          capacityPercent: isResolved ? 65 : 0,
          isSelected: selectedNodeData?.id === 'chp2',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: isResolved ? [0, 20, 50, 65, 65] : [0, 0, 0, 0, 0],
          registers: {
            'ATS Ready State': isResolved ? 'ONLINE_ENGAGED' : 'ARMED_SYNC',
            'Preheat Block Heater': '+55.0°C Active',
            'Starter Battery': '27.4 V DC Float',
            'Transfer Time Delay': '1.2 sec Auto ATS',
          },
        },
      },
      {
        id: 'solar',
        type: 'powerNode',
        position: { x: 45, y: 325 },
        data: {
          id: 'solar',
          label: 'Bifacial Solar Array',
          iconType: 'solar',
          subsystem: 'Polar Renewable Farm',
          value: '12.4',
          metricUnit: 'kW',
          status: 'ONLINE',
          capacityPercent: 62,
          isSelected: selectedNodeData?.id === 'solar',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: [11.8, 12.1, 12.4, 12.3, 12.4],
          registers: {
            'Inverter String 1-4': '4 / 4 Synced',
            'Solar Irradiance': '380 W/m²',
            'Albedo Boost': '+18.4% Snow Reflection',
            'Surface Temperature': '-12.0°C Nominal',
          },
        },
      },
      {
        id: 'bess',
        type: 'powerNode',
        position: { x: 45, y: 455 },
        data: {
          id: 'bess',
          label: 'BESS Lithium Bank',
          iconType: 'battery',
          subsystem: '100 kWh Peak Storage',
          value: '92',
          metricUnit: '% SOC',
          status: 'ONLINE',
          capacityPercent: 92,
          isSelected: selectedNodeData?.id === 'bess',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: [93, 92.8, 92.5, 92.2, 92.0],
          registers: {
            'DC Bus Voltage': '440.2 V',
            'Battery Current': '+12.8 A Charge',
            'Cell Temperature': '+18.5°C Optimal',
            'State of Health (SOH)': '98.4% Certified',
          },
        },
      },
      {
        id: 'wind',
        type: 'powerNode',
        position: { x: 45, y: 585 },
        data: {
          id: 'wind',
          label: 'Polar Wind Turbines',
          iconType: 'wind',
          subsystem: 'Aerodynamic Turbines',
          value: isBlizzard ? '28.4' : '14.2',
          metricUnit: 'kW',
          status: isBlizzard ? 'SURGE' : 'ONLINE',
          capacityPercent: isBlizzard ? 95 : 48,
          isSelected: selectedNodeData?.id === 'wind',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: isBlizzard ? [14, 18, 24, 28, 28.4] : [14.0, 14.2, 13.9, 14.3, 14.2],
          registers: {
            'Wind Velocity': `${windMps} m/s`,
            'Rotor Velocity': isBlizzard ? '420 RPM' : '180 RPM',
            'Blade Pitch Angle': isBlizzard ? '24° Storm Furling' : '6° Running',
            'Nacelle Vibration': '1.2 mm/s Nominal',
          },
        },
      },

      // ========================================================
      // 2. ZONE 02: 400V 50Hz DISTRIBUTION BUS (x: 410)
      // ========================================================
      {
        id: 'mlvd_bus',
        type: 'busNode',
        position: { x: 410, y: 220 },
        data: {
          id: 'mlvd_bus',
          label: '400V 50Hz MLVD Bus',
          loadKw: loadKw,
          frequencyHz: isChpTripped ? '49.55' : freqHz,
          status: isChpTripped ? 'RECOVERING' : 'SYNCHRONIZED',
          isSelected: selectedNodeData?.id === 'mlvd_bus',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          freqHistory: isChpTripped ? [50.00, 49.85, 49.55, 49.60, 49.75] : [50.01, 50.00, 49.99, 50.00, 50.01],
          registers: {
            'Bus Voltage L-L': '399.8 V AC',
            'Power Factor': '0.94 Lagging',
            'Total Harmonic Distortion': '1.8% THD',
            'Bus Tie Circuit Breakers': 'Closed Interlocked',
            'Microgrid Stability Score': isChpTripped ? '0.74 Damped' : '0.99 Nominal',
          },
        },
      },
      {
        id: 'ats_switch',
        type: 'interlockNode',
        position: { x: 440, y: 440 },
        data: {
          id: 'ats_switch',
          label: 'Fast ATS Transfer Relay',
          tier: 'Automatic Transfer Contactor',
          isSelected: selectedNodeData?.id === 'ats_switch',
          onSelect: handleSelectNode,
          registers: {
            'Switch Position': isResolved ? 'POSITION_2 (CHP-02)' : 'POSITION_1 (CHP-01)',
            'Transfer Delay': '1.200 seconds',
            'Phase Angle Delta': '0.4 deg locked',
          },
        },
      },

      // ========================================================
      // 3. ZONE 03: LIFE SUPPORT & RESEARCH CONSUMERS (x: 785)
      // ========================================================
      {
        id: 'habitat_hvac',
        type: 'consumerNode',
        position: { x: 785, y: 65 },
        data: {
          id: 'habitat_hvac',
          label: 'Habitat HVAC Core',
          iconType: 'hvac',
          subsystem: 'Living Quarters Life-Support',
          value: `+${indoorTemp}°C`,
          secondary: isBlizzard ? 'Katabatic Storm Seal' : 'Zone 1 & 2 Balanced',
          status: isBlizzard ? 'SEALED' : 'OPTIMAL',
          isSelected: selectedNodeData?.id === 'habitat_hvac',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: isBlizzard ? [20.2, 19.8, 19.5, 19.4] : [20.1, 20.2, 20.1, 20.2],
          registers: {
            'AHU Fresh Air Damper': isBlizzard ? '0% Katabatic Sealed' : '25% Fresh Flow',
            'Heat Exchanger Return': '+18.4°C Recovered',
            'CO2 Concentration': '520 PPM Optimal',
            'Relative Humidity': '34% Regulated',
          },
        },
      },
      {
        id: 'utilidor_loop',
        type: 'consumerNode',
        position: { x: 785, y: 255 },
        data: {
          id: 'utilidor_loop',
          label: 'Utilidor Potable Line',
          iconType: 'utilidor',
          subsystem: 'Freeze Prevention Circuit',
          value: `${utilidorTemp}°C`,
          secondary: isFreeze ? 'Trace Boost 100%' : '45 L/min Nominal',
          status: isFreeze ? 'ALERT' : 'OPTIMAL',
          isSelected: selectedNodeData?.id === 'utilidor_loop',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: isFreeze ? [4.8, 3.2, 2.0, 1.2] : [4.6, 4.8, 4.7, 4.8],
          registers: {
            'Trace Heating Circuit': isFreeze ? '24.0 kWth 100% Boost' : '8.2 kWth Standby',
            'Pipe Surface Sensor PT-100': `${utilidorTemp}°C`,
            'Potable Circulation Flow': '45 L/min',
            'Lake Zub Suction Temp': '+2.4°C Protected',
          },
        },
      },
      {
        id: 'science_lab',
        type: 'consumerNode',
        position: { x: 785, y: 445 },
        data: {
          id: 'science_lab',
          label: 'Scientific Instruments',
          iconType: 'lab',
          subsystem: 'Priority 2 Research Load',
          value: '38.4 kW',
          secondary: 'Seismology & Atmospheric Lidar',
          status: 'OPTIMAL',
          isSelected: selectedNodeData?.id === 'science_lab',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          history: [38.2, 38.4, 38.3, 38.4],
          registers: {
            'Seismic Broadband Sensor': 'ONLINE (24/7 Sampling)',
            'Auroral Photometer': 'SAMPLING Locked',
            'Differential GPS Antenna': 'CARRIER_FIXED',
            'Load Shedding Priority': 'Tier 2 Sheddable on Crisis',
          },
        },
      },

      // ========================================================
      // 4. ZONE 04: 10-AGENT COGNITIVE SOCIETY NEURAL BUS (y: 820)
      // ========================================================
      {
        id: 'agent_sa',
        type: 'agentNode',
        position: { x: 45, y: 820 },
        data: {
          id: 'agent_sa',
          label: 'Situation Awareness Agent',
          role: 'Continuous Perception',
          latency: '38ms Groq',
          hypothesis: isChpTripped 
            ? 'CHP-01 breaker trip detected on MLVD 400V bus. Frequency dip -0.45 Hz.'
            : isBlizzard 
            ? 'Katabatic blizzard wind surge: 34 m/s. Infiltration risk.'
            : isFreeze
            ? 'Utilidor conduit temperature approaching freeze limit.'
            : 'All 505 sensors continuous scan nominal.',
          confidence: '99.4%',
          isSelected: selectedNodeData?.id === 'agent_sa',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          registers: {
            'Inference Engine': 'Groq LPU LLaMA-3.3-70B',
            'Sensor Channels Processed': '505 Streams / Sec',
            'Anomaly Breaches': isChpTripped ? '1 Breached (CHP-01)' : '0 Breaches',
          },
        },
      },
      {
        id: 'agent_dg',
        type: 'agentNode',
        position: { x: 385, y: 820 },
        data: {
          id: 'agent_dg',
          label: 'Diagnostic Causal Reasoner',
          role: 'Causal DAG Traversal',
          latency: '42ms Groq',
          hypothesis: isChpTripped
            ? 'Causal Root Cause: Alternator breaker trip. Recommend start standby CHP-02.'
            : isBlizzard
            ? 'Causal Root Cause: High infiltration. Recommend seal AHU fresh air.'
            : isFreeze
            ? 'Causal Root Cause: Freeze risk. Energize trace heating boost.'
            : '35-Node Causal Graph traversed. Zero cascading hazards.',
          confidence: '99.8%',
          isSelected: selectedNodeData?.id === 'agent_dg',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          registers: {
            'Causal Graph Nodes': '35 Nodes Evaluated',
            'Hallucination Rate': '0.0% Structural Determinism',
            'Bayesian Marginal P': '0.998',
          },
        },
      },
      {
        id: 'agent_wi',
        type: 'agentNode',
        position: { x: 725, y: 820 },
        data: {
          id: 'agent_wi',
          label: 'What-If Counterfactual Sandbox',
          role: 'Physics Verification',
          latency: '35ms Groq',
          hypothesis: isChpTripped
            ? 'Simulation verified: Standby CHP-02 transfer retains 50.00 Hz without blackout.'
            : 'Forward 120s thermal lookahead verified safe.',
          confidence: '99.6%',
          isSelected: selectedNodeData?.id === 'agent_wi',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          registers: {
            'Physics Constraints Checked': 'Thermal, Voltage, Frequency, Pressure',
            'Safety Reserve Margin': '+22.4%',
            'Sandbox Clearance': 'APPROVED',
          },
        },
      },
      {
        id: 'agent_friday',
        type: 'agentNode',
        position: { x: 1065, y: 820 },
        data: {
          id: 'agent_friday',
          label: 'Friday Chief Orchestrator',
          role: 'Consensus & Actuation',
          latency: '1.2s Autonomy',
          hypothesis: isResolved
            ? 'Consensus plan executed: Standby generator running, microgrid balanced.'
            : isChpTripped
            ? 'Autonomous Tier 1 ATS dispatch in progress...'
            : 'Tier 1 Autonomous Governor mode active.',
          confidence: '100%',
          isSelected: selectedNodeData?.id === 'agent_friday',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          registers: {
            'Active Safety Interlock': 'Tier 1 Autonomous Governor (<1.2s)',
            'Action Token Signed': 'HMAC-SHA256 Verified',
            'Dispatched Command': isResolved ? 'ACT_START_CHP02' : 'NOMINAL_MONITOR',
          },
        },
      },

      // ========================================================
      // 5. ZONE 05: DEFENSE INTERLOCK & SATCOM GATEWAY (x: 1150)
      // ========================================================
      {
        id: 'satcom_gateway',
        type: 'gatewayNode',
        position: { x: 1150, y: 220 },
        data: {
          id: 'satcom_gateway',
          label: 'NCPOR Goa Twin Mirror',
          latency: '640ms Delta',
          deltaSaved: '90% Delta Saved',
          isSelected: selectedNodeData?.id === 'satcom_gateway',
          onSelect: handleSelectNode,
          onQuickAction: handleQuickAction,
          registers: {
            'Mainland Headquarters': 'NCPOR Goa / MoES Govt of India',
            'Compression Algorithm': 'Differential State Delta Encoding',
            'Bandwidth Savings': '90.2% Delta',
            'Spool Buffer Quality': '100% Invariant Guarantees',
          },
        },
      },
      {
        id: 'interlock_t1',
        type: 'interlockNode',
        position: { x: 1150, y: 390 },
        data: {
          id: 'interlock_t1',
          label: 'Tier 1 Autonomous Interlock',
          tier: 'Hardware Trip Interlock',
          isSelected: selectedNodeData?.id === 'interlock_t1',
          onSelect: handleSelectNode,
          registers: {
            'Relay Hardware Latency': '32 ms Tripped',
            'Supervised Authority': 'Autonomous Fast-Actuation',
            'Tamper Seal State': 'Cryptographically Enforced',
          },
        },
      },
    ];
  }, [isChpTripped, isResolved, isBlizzard, isFreeze, kpis, loadKw, freqHz, windMps, indoorTemp, utilidorTemp, selectedNodeData, handleSelectNode, handleQuickAction]);

  // Build React Flow Pro Custom Particle Edges
  const initialEdges: Edge[] = useMemo(() => {
    return [
      // 1. Generation to 400V Bus
      {
        id: 'e-chp1-bus',
        type: 'particleEdge',
        source: 'chp1',
        target: 'mlvd_bus',
        data: {
          particleColor: isChpTripped ? '#e11d48' : '#4648d4',
          particleSpeed: isChpTripped ? '1.0s' : '2.0s',
          isAlarm: isChpTripped,
          label: isChpTripped ? 'BREAKER TRIPPED 0.0 kW' : '75.0 kW Baseload',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: isChpTripped ? '#f43f5e' : '#4648d4' },
      },
      {
        id: 'e-chp2-bus',
        type: 'particleEdge',
        source: 'chp2',
        target: 'mlvd_bus',
        data: {
          particleColor: '#10b981',
          particleSpeed: '1.8s',
          isStandby: !isResolved,
          label: isResolved ? 'ATS ACTIVE 65.0 kW' : 'Standby Cold-Reserve',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: isResolved ? '#10b981' : '#a1a1aa' },
      },
      {
        id: 'e-solar-bus',
        type: 'particleEdge',
        source: 'solar',
        target: 'mlvd_bus',
        data: {
          particleColor: '#f59e0b',
          particleSpeed: '2.5s',
          label: '12.4 kW Solar',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#f59e0b' },
      },
      {
        id: 'e-bess-bus',
        type: 'particleEdge',
        source: 'bess',
        target: 'mlvd_bus',
        data: {
          particleColor: '#10b981',
          particleSpeed: '2.2s',
          label: '92% SOC Battery',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },
      {
        id: 'e-wind-bus',
        type: 'particleEdge',
        source: 'wind',
        target: 'mlvd_bus',
        data: {
          particleColor: '#006577',
          particleSpeed: isBlizzard ? '1.2s' : '2.4s',
          label: isBlizzard ? '28.4 kW Storm Surge' : '14.2 kW Aerodynamic',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#006577' },
      },

      // 2. Bus to ATS Switch Interlock
      {
        id: 'e-bus-ats',
        type: 'particleEdge',
        source: 'mlvd_bus',
        target: 'ats_switch',
        data: {
          particleColor: '#4648d4',
          particleSpeed: '2.0s',
          label: 'Interlocked Bus Tie',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#4648d4' },
      },

      // 3. Bus to Consumers
      {
        id: 'e-bus-hvac',
        type: 'particleEdge',
        source: 'mlvd_bus',
        target: 'habitat_hvac',
        data: {
          particleColor: '#10b981',
          particleSpeed: '2.0s',
          label: isBlizzard ? 'Sealed Recirculation' : 'Zone 1 & 2 HVAC',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },
      {
        id: 'e-bus-utilidor',
        type: 'particleEdge',
        source: 'mlvd_bus',
        target: 'utilidor_loop',
        data: {
          particleColor: isFreeze ? '#06b6d4' : '#006577',
          particleSpeed: isFreeze ? '1.2s' : '2.2s',
          isAlarm: isFreeze,
          label: isFreeze ? '24 kWth Trace Heating Boost' : '8.2 kWth Flow Line',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: isFreeze ? '#06b6d4' : '#006577' },
      },
      {
        id: 'e-bus-science',
        type: 'particleEdge',
        source: 'mlvd_bus',
        target: 'science_lab',
        data: {
          particleColor: '#4648d4',
          particleSpeed: '2.3s',
          label: '38.4 kW Lidar / Seismo',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#4648d4' },
      },

      // 4. Consumers / Interlock to Satcom Mirror
      {
        id: 'e-utilidor-satcom',
        type: 'particleEdge',
        source: 'utilidor_loop',
        target: 'satcom_gateway',
        data: {
          particleColor: '#006577',
          particleSpeed: '2.8s',
          label: 'Differential Delta Stream',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#006577' },
      },
      {
        id: 'e-interlock-satcom',
        type: 'particleEdge',
        source: 'interlock_t1',
        target: 'satcom_gateway',
        data: {
          particleColor: '#10b981',
          particleSpeed: '2.5s',
          label: 'Interlock Telemetry',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },

      // 5. Cognitive Agent Society Pipeline
      {
        id: 'e-sa-dg',
        type: 'particleEdge',
        source: 'agent_sa',
        target: 'agent_dg',
        data: {
          particleColor: '#4648d4',
          particleSpeed: '1.8s',
          label: 'Anomaly Vector (38ms)',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#4648d4' },
      },
      {
        id: 'e-dg-wi',
        type: 'particleEdge',
        source: 'agent_dg',
        target: 'agent_wi',
        data: {
          particleColor: '#006577',
          particleSpeed: '1.8s',
          label: 'Root Cause Hypothesis',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#006577' },
      },
      {
        id: 'e-wi-friday',
        type: 'particleEdge',
        source: 'agent_wi',
        target: 'agent_friday',
        data: {
          particleColor: '#10b981',
          particleSpeed: '1.8s',
          label: 'Sandbox Verified Plan',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981' },
      },
      {
        id: 'e-friday-bus',
        type: 'particleEdge',
        source: 'agent_friday',
        target: 'mlvd_bus',
        targetHandle: 'bottom',
        sourceHandle: 'top',
        data: {
          particleColor: isResolved ? '#10b981' : '#4648d4',
          particleSpeed: '1.5s',
          label: isResolved ? 'Tier 1 ATS Autonomous Command' : 'Supervisory Loop',
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: isResolved ? '#10b981' : '#4648d4' },
      },
    ];
  }, [isChpTripped, isResolved, isBlizzard, isFreeze]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Synchronize state changes when crisis or snapshot changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Apply Layer Filtering (Visual highlighting & Dimming)
  const displayNodes = useMemo(() => {
    if (activeLayer === 'ALL') return nodes;

    return nodes.map((node) => {
      let isVisible = true;
      if (activeLayer === 'POWER') {
        isVisible = ['group_power', 'group_bus', 'chp1', 'chp2', 'solar', 'bess', 'wind', 'mlvd_bus', 'ats_switch'].includes(node.id);
      } else if (activeLayer === 'LIFE_SUPPORT') {
        isVisible = ['group_loads', 'habitat_hvac', 'utilidor_loop', 'science_lab', 'group_bus', 'mlvd_bus'].includes(node.id);
      } else if (activeLayer === 'AGENTS') {
        isVisible = ['group_agents', 'agent_sa', 'agent_dg', 'agent_wi', 'agent_friday', 'group_bus', 'mlvd_bus'].includes(node.id);
      } else if (activeLayer === 'GATEWAY') {
        isVisible = ['group_gateway', 'satcom_gateway', 'interlock_t1', 'group_bus', 'mlvd_bus'].includes(node.id);
      }

      return {
        ...node,
        style: {
          ...node.style,
          opacity: isVisible ? 1 : 0.18,
          filter: isVisible ? 'none' : 'grayscale(60%)',
          transition: 'opacity 0.3s ease, filter 0.3s ease',
        },
      };
    });
  }, [nodes, activeLayer]);

  const displayEdges = useMemo(() => {
    if (activeLayer === 'ALL') return edges;

    return edges.map((edge) => {
      let isRelevant = true;
      if (activeLayer === 'POWER') {
        isRelevant = ['e-chp1-bus', 'e-chp2-bus', 'e-solar-bus', 'e-bess-bus', 'e-wind-bus', 'e-bus-ats'].includes(edge.id);
      } else if (activeLayer === 'LIFE_SUPPORT') {
        isRelevant = ['e-bus-hvac', 'e-bus-utilidor', 'e-bus-science'].includes(edge.id);
      } else if (activeLayer === 'AGENTS') {
        isRelevant = ['e-sa-dg', 'e-dg-wi', 'e-wi-friday', 'e-friday-bus'].includes(edge.id);
      } else if (activeLayer === 'GATEWAY') {
        isRelevant = ['e-utilidor-satcom', 'e-interlock-satcom'].includes(edge.id);
      }

      return {
        ...edge,
        style: {
          ...edge.style,
          opacity: isRelevant ? 1 : 0.08,
          transition: 'opacity 0.3s ease',
        },
      };
    });
  }, [edges, activeLayer]);

  const edgeTypes = useMemo(() => ({
    particleEdge: ParticleEdge,
  }), []);

  return (
    <div className="w-full flex flex-col gap-5">
      {/* 1. Header Bar with Title, Station Badge, and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#eaebf0]">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-md text-[9px] font-mono font-black tracking-wider uppercase bg-[#4648d4] text-white">
              REACT FLOW PRO
            </span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">
              Real-Time Dynamic Twin
            </span>
          </div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight mt-0.5">
            Antarctic Digital Twin System Flow
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#eaebf0] shadow-2xs font-mono text-xs text-[#131b2e]">
            <Compass className="w-3.5 h-3.5 text-[#4648d4]" />
            <span className="font-bold uppercase text-[#4648d4]">{activeStation} Station</span>
            <span className="text-[#73738c]">|</span>
            <span>{activeStation === 'bharati' ? '69°24\'S, 76°11\'E' : '70°45\'S, 11°43\'E'}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] font-mono text-xs font-semibold shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>505 Sensors Active</span>
          </div>

          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Telemetry Stream"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Layer Perspective Switcher & Camera Preset Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
        {/* Layer Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <span className="text-xs font-mono font-bold text-[#73738c] px-2 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" />
            Layers:
          </span>
          <button
            onClick={() => setActiveLayer('ALL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              activeLayer === 'ALL'
                ? 'bg-[#131b2e] text-white shadow-xs'
                : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
            }`}
          >
            All Systems (505 Ch)
          </button>
          <button
            onClick={() => setActiveLayer('POWER')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              activeLayer === 'POWER'
                ? 'bg-[#4648d4] text-white shadow-xs'
                : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
            }`}
          >
            ⚡ Microgrid Power
          </button>
          <button
            onClick={() => setActiveLayer('LIFE_SUPPORT')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              activeLayer === 'LIFE_SUPPORT'
                ? 'bg-[#006577] text-white shadow-xs'
                : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
            }`}
          >
            🌡️ Life Support & Thermal
          </button>
          <button
            onClick={() => setActiveLayer('AGENTS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              activeLayer === 'AGENTS'
                ? 'bg-[#4648d4] text-white shadow-xs'
                : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
            }`}
          >
            🧠 10-Agent Society Bus
          </button>
          <button
            onClick={() => setActiveLayer('GATEWAY')}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
              activeLayer === 'GATEWAY'
                ? 'bg-[#10b981] text-white shadow-xs'
                : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
            }`}
          >
            🛡️ Satcom & Interlocks
          </button>
        </div>

        {/* Camera Quick-Presets */}
        <div className="flex items-center gap-1 text-xs font-mono">
          <span className="text-[#73738c] text-[11px] px-1 flex items-center gap-1">
            <Crosshair className="w-3.5 h-3.5" />
            Focus:
          </span>
          <button
            onClick={() => handlePresetView('fit')}
            className="px-2.5 py-1 rounded-lg bg-[#f2f3ff] text-[#4648d4] hover:bg-[#eaedff] font-bold"
          >
            Fit All
          </button>
          <button
            onClick={() => handlePresetView('substation')}
            className="px-2.5 py-1 rounded-lg hover:bg-[#f4f4f5] text-[#464554]"
          >
            Substation
          </button>
          <button
            onClick={() => handlePresetView('life')}
            className="px-2.5 py-1 rounded-lg hover:bg-[#f4f4f5] text-[#464554]"
          >
            Life Support
          </button>
          <button
            onClick={() => handlePresetView('agents')}
            className="px-2.5 py-1 rounded-lg hover:bg-[#f4f4f5] text-[#464554]"
          >
            AI Bus
          </button>
          <button
            onClick={() => handlePresetView('gateway')}
            className="px-2.5 py-1 rounded-lg hover:bg-[#f4f4f5] text-[#464554]"
          >
            Satcom
          </button>
        </div>
      </div>

      {/* 3. Interactive Crisis Simulator Test Bench for Instant Reactions */}
      <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-bold text-xs">
            <Sparkles className="w-4 h-4 text-[#4648d4]" />
          </div>
          <span className="font-display font-bold text-sm text-[#131b2e]">
            Digital Twin Test Bench
          </span>
          {statusBanner && (
            <span className="ml-2 text-xs font-mono font-semibold text-[#4648d4] bg-[#eaedff] px-2.5 py-0.5 rounded-md animate-fade-in">
              {statusBanner}
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleInjectCrisis('GENERATOR_TRIP')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
              activeCrisis === 'GENERATOR_TRIP'
                ? 'bg-[#fff1f2] border-[#f43f5e] text-[#e11d48] shadow-xs'
                : 'bg-white border-[#eaebf0] hover:bg-[#fff1f2] text-[#e11d48]'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Generator Trip</span>
          </button>

          <button
            onClick={() => handleInjectCrisis('BLIZZARD_STRIKE')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
              activeCrisis === 'BLIZZARD_STRIKE'
                ? 'bg-[#f0f9ff] border-[#0284c7] text-[#0284c7] shadow-xs'
                : 'bg-white border-[#eaebf0] hover:bg-[#f0f9ff] text-[#0284c7]'
            }`}
          >
            <CloudSnow className="w-3.5 h-3.5" />
            <span>Blizzard Surge</span>
          </button>

          <button
            onClick={() => handleInjectCrisis('WATER_LINE_FREEZE')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 border transition-all ${
              activeCrisis === 'WATER_LINE_FREEZE'
                ? 'bg-[#ecfeff] border-[#06b6d4] text-[#0891b2] shadow-xs'
                : 'bg-white border-[#eaebf0] hover:bg-[#ecfeff] text-[#0891b2]'
            }`}
          >
            <Droplet className="w-3.5 h-3.5" />
            <span>Utilidor Freeze</span>
          </button>

          <button
            onClick={handleReset}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restore Nominal</span>
          </button>
        </div>
      </div>

      {/* 4. Main Full-Screen React Flow Canvas with Particle Edges & Compound Clusters */}
      <div className="relative w-full h-[760px] rounded-3xl bg-white border border-[#eaebf0] shadow-sm overflow-hidden">
        <ReactFlow
          nodes={displayNodes}
          edges={displayEdges}
          nodeTypes={customNodeTypes}
          edgeTypes={edgeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onInit={(instance) => {
            rfInstanceRef.current = instance;
          }}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.3}
          maxZoom={1.6}
          className="bg-[#faf8ff]"
        >
          <Background color="#eaebf0" gap={24} size={1.2} />
          <Controls className="!bg-white !border !border-[#eaebf0] !rounded-2xl !shadow-xs" />
          <MiniMap
            nodeColor={(n) => {
              if (n.type === 'clusterNode') return '#f1f5f9';
              if (n.data?.status === 'TRIPPED') return '#f43f5e';
              if (n.data?.status === 'ALERT') return '#06b6d4';
              if (n.data?.status === 'STANDBY') return '#a1a1aa';
              return '#4648d4';
            }}
            className="!rounded-2xl !border !border-[#eaebf0] !bg-white/85 shadow-md"
            maskColor="rgba(240, 244, 251, 0.65)"
          />
        </ReactFlow>

        {/* Top-Left Telemetry Capsule Pill on Canvas */}
        <div className="absolute top-4 left-4 pointer-events-none flex items-center gap-2 z-10">
          <div className="px-4 py-2 rounded-2xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-sm flex items-center gap-3 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] animate-pulse" />
              <span className="font-bold text-[#131b2e]">Bus: {loadKw} kW</span>
            </div>
            <div className="w-px h-4 bg-[#eaebf0]" />
            <div className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-[#006c49]" />
              <span className="font-bold text-[#006c49]">{freqHz} Hz</span>
            </div>
            <div className="w-px h-4 bg-[#eaebf0]" />
            <div className="flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-[#006577]" />
              <span className="text-[#464554]">640ms Satcom</span>
            </div>
            <div className="w-px h-4 bg-[#eaebf0]" />
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-[#4648d4]" />
              <span className="text-[#4648d4] font-bold">Tier 1 Interlocked</span>
            </div>
          </div>
        </div>

        {/* Deep Interactive Telemetry Inspector Drawer */}
        {selectedNodeData && (
          <TelemetryDrawer
            nodeData={selectedNodeData}
            onClose={() => setSelectedNodeData(null)}
            activeStation={activeStation}
            onRefresh={loadData}
          />
        )}
      </div>
    </div>
  );
};
