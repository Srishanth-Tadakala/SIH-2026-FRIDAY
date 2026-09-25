// F.R.I.D.A.Y. Polar Digital Twin Telemetry & Cognitive Models

export type StationId = 'bharati' | 'maitri';

export interface StationKPIs {
  sim_time_seconds: number;
  total_generation_kw: number;
  total_load_kw: number;
  grid_frequency_hz: number;
  grid_voltage_v: number;
  ambient_temp_c: number;
  wind_speed_mps: number;
  wind_direction_deg: number;
  indoor_temp_living_c: number;
  indoor_temp_labs_c: number;
  utilidor_pipe_temp_c: number;
  water_storage_liters: number;
  fuel_storage_liters: number;
  fuel_burn_rate_lph: number;
  running_chp_count: number;
  science_loads_shed: boolean;
  active_alert_count: number;
  satcom_connected: boolean;
  satcom_latency_ms: number;
  satcom_bandwidth_kbps: number;
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
  readings: Record<string, { value: number | string | boolean; unit?: string; status?: string }>;
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
  }>;
  bus_total_messages: number;
  active_sessions_count: number;
}
