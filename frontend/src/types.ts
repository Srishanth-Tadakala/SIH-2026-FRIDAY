// F.R.I.D.A.Y. Polar Digital Twin Telemetry & Cognitive Models

export type StationId = 'bharati' | 'maitri';

export interface StationCoordinates {
  latitude: number;
  longitude: number;
  latitude_dms: string;
  longitude_dms: string;
  elevation_m: number;
}

export interface StationInfo {
  station_id: StationId;
  station_name: string;
  location: string;
  coordinates: StationCoordinates;
  sensor_count: number;
  active_scenario: string;
  sim_time_seconds: number;
  timestamp_iso: string;
  kpis: {
    total_generation_kw: number;
    running_chp_count: number;
    station_electrical_load_kw: number;
    station_heating_demand_kw: number;
    indoor_avg_temp_c: number;
    ambient_temp_c: number;
    wind_speed_mps: number;
    total_fuel_reserve_l: number;
    fuel_autonomy_days: number;
    water_autonomy_days: number;
    potable_tank_level_pct: number;
    fleet_availability_pct: number;
    ground_route_accessibility_pct: number;
    composite_risk_score: number;
  };
  active_alert_count: number;
  is_active_context: boolean;
}

export interface StationKPIs {
  sim_time_seconds?: number;
  total_generation_kw: number;
  total_load_kw?: number;
  station_electrical_load_kw?: number;
  station_heating_demand_kw?: number;
  grid_frequency_hz?: number;
  grid_voltage_v?: number;
  ambient_temp_c?: number;
  wind_speed_mps?: number;
  wind_direction_deg?: number;
  indoor_temp_living_c?: number;
  indoor_temp_labs_c?: number;
  indoor_avg_temp_c?: number;
  utilidor_pipe_temp_c?: number;
  water_storage_liters?: number;
  fuel_storage_liters?: number;
  fuel_burn_rate_lph?: number;
  total_fuel_reserve_l?: number;
  fuel_autonomy_days?: number;
  water_autonomy_days?: number;
  potable_tank_level_pct?: number;
  fleet_availability_pct?: number;
  ground_route_accessibility_pct?: number;
  composite_risk_score?: number;
  running_chp_count?: number;
  science_loads_shed?: boolean;
  active_alert_count?: number;
  satcom_connected?: boolean;
  satcom_latency_ms?: number;
  satcom_bandwidth_kbps?: number;
}

export interface StationSnapshot {
  station_id: StationId;
  station_name: string;
  sim_time_seconds: number;
  timestamp_iso: string;
  active_scenario: string;
  kpis: StationKPIs;
  alerts: Array<{
    alert_id: string;
    subsystem: string;
    severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';
    message: string;
    timestamp: number;
  }>;
  readings: Record<string, { value: number | string | boolean; unit?: string; status?: string; quality?: string }>;
}

export interface ActuationRecord {
  action_id: string;
  session_id: string;
  title: string;
  station_id: string;
  autonomy_tier: string;
  dynamic_agent_chain: string[];
  applied_overrides: Array<{ pillar?: string; path?: string; value?: any }>;
  physical_verification: string;
  status: string;
  timestamp: number;
  timestamp_iso: string;
  sim_time_seconds: number;
}

export interface DynamicAgentCall {
  message_id: string;
  session_id: string;
  caller: string;
  callee: string;
  call_type: string;
  severity: string;
  confidence: number;
  timestamp: number;
  summary: string;
  payload: any;
}

export interface AgentSocietyStatus {
  agents: Record<string, {
    name: string;
    role: string;
    state: string;
    hypothesis?: string;
    last_active_time: number;
    messages_sent: number;
    messages_received: number;
    confidence?: number;
    objective?: string;
    tag?: string;
    icon?: string;
    color?: string;
  }>;
  bus_total_messages: number;
  active_sessions_count: number;
  orchestrator_state?: string;
  total_agents?: number;
}

// -------------------------------------------------------------
// Extended Backend Telemetry & Distributed Governance Models
// -------------------------------------------------------------

export interface ActuatorState {
  station_id: string;
  chps: Array<{
    unit_id: number;
    name: string;
    operating_state: string;
    power_kw: number;
    running: boolean;
    coolant_temp_c: number;
    fuel_flow_lph: number;
    runtime_hours: number;
  }>;
  pipelines: {
    water01_trace_heating_on: boolean;
    water01_pipe_temp_c: number;
    fuel01_trace_heating_on: boolean;
    heat01_trace_heating_on: boolean;
    freeze_hazard: boolean;
  };
  hvac: {
    living_temp_c: number;
    lab_temp_c: number;
    technical_temp_c: number;
    ahu01_fan_running: boolean;
    ahu01_heating_valve_pct: number;
    ahu01_fresh_air_damper_pct: number;
    ahu02_fan_running: boolean;
    ahu02_heating_valve_pct: number;
    ahu02_fresh_air_damper_pct: number;
    blizzard_dampers_sealed: boolean;
  };
  science_loads: {
    science_load_shed: boolean;
    conserved_kw: number;
  };
  water: {
    ro_system_status: string;
    storage_tank_pct: number;
  };
  edge_status: {
    is_polar_blackout: boolean;
    autonomous_governor_active: boolean;
    local_authority_mode: string;
  };
}

export interface CognitiveLogEntry {
  event_id: string;
  timestamp_iso: string;
  timestamp: number;
  station_id: string;
  category: 'PERCEPTION' | 'CAUSAL' | 'PLANNING' | 'PREDICTION' | 'ACTUATION' | 'EDGE_AUTHORITY';
  title: string;
  details: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';
  metadata?: Record<string, any>;
}

export interface SatcomChannelMetrics {
  profile_name: string;
  bandwidth_bps: number;
  latency_ms: number;
  packet_loss_pct: number;
  is_blackout: boolean;
  spooled_frames_count: number;
  total_bytes_sent: number;
  total_bytes_saved: number;
  compression_ratio_pct: number;
}

export interface SatcomMirrorTwin {
  station_id: string;
  sync_status: string;
  is_synchronized: boolean;
  last_seq_num: number;
  last_sim_time_seconds: number;
  sensor_count: number;
  state_checksum: string;
  kpis: Record<string, any>;
  alerts: any[];
  readings: Record<string, any>;
  total_frames_received: number;
  lost_frames_count: number;
}

export interface IncidentEpisode {
  episode_id: string;
  station_id: string;
  scenario: string;
  started_at_sim: number;
  resolved_at_sim?: number;
  duration_seconds?: number;
  trigger_alert?: Record<string, any>;
  root_causes?: any[];
  consensus_plan?: Record<string, any>;
  outcome?: Record<string, any>;
  lessons_learned?: string;
}

export interface EquipmentAsset {
  equipment_id: string;
  station_id: string;
  name: string;
  subsystem: string;
  pillar: string;
  running_hours: number;
  max_rated_hours: number;
  wear_percentage: number;
  maintenance_due: boolean;
  status: string;
}

export interface OperatorAudit {
  audit_id: string;
  timestamp: number;
  station_id: string;
  operator_id: string;
  action_type: string;
  details: string;
  authorized: boolean;
}

export interface CopilotMessage {
  message_id?: string;
  role: 'user' | 'assistant';
  message: string;
  cited_sensors?: string[];
  suggested_followups?: string[];
  operational_status?: string;
  model_used?: string;
  latency_ms?: number;
  timestamp?: number;
}

export interface TelemetryHistoryPoint {
  timestamp: number;
  sim_time_seconds: number;
  kpis: Record<string, number>;
  alert_count: number;
}
