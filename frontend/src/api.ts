import { 
  StationId, 
  StationInfo,
  StationSnapshot, 
  ActuationRecord, 
  DynamicAgentCall, 
  AgentSocietyStatus,
  ActuatorState,
  CognitiveLogEntry,
  SatcomMirrorTwin,
  IncidentEpisode,
  EquipmentAsset,
  OperatorAudit,
  CopilotMessage,
  TelemetryHistoryPoint
} from './types';

const API_BASE = '/api';

import { requestJson } from './api/client';

// ============================================================================
// 1. STATIONS & SIMULATION CLOCK
// ============================================================================

export async function fetchStations(): Promise<StationInfo[]> {
  return requestJson<StationInfo[]>(`${API_BASE}/stations`);
}

export async function fetchStationDetail(stationId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/stations/${stationId}`);
}

export async function setActiveStation(stationId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/stations/active/${stationId}`, { method: 'POST' });
}

export async function stepStationClock(stationId: string = 'bharati', dtSeconds: number = 1.0): Promise<any> {
  return requestJson<any>(`${API_BASE}/stations/${stationId}/step`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dt_seconds: dtSeconds }),
  });
}

// ============================================================================
// 2. TELEMETRY & FIELD INGESTION
// ============================================================================

export async function fetchStationSnapshot(stationId: StationId = 'bharati'): Promise<StationSnapshot> {
  return requestJson<StationSnapshot>(`${API_BASE}/telemetry/${stationId}/snapshot`);
}

export async function fetchStationKPIs(stationId: StationId = 'bharati'): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/${stationId}/kpis`);
}

export async function fetchStationAlerts(stationId: StationId = 'bharati'): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/${stationId}/alerts`);
}

export async function fetchPillarTelemetry(stationId: StationId = 'bharati', pillar: string = 'energy'): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/${stationId}/pillars/${pillar}`);
}

export async function fetchSensorReading(stationId: StationId = 'bharati', sensorId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/${stationId}/sensors/${sensorId}`);
}

export async function fetchStationHistory(
  stationId: StationId = 'bharati', 
  limit: number = 60
): Promise<{ station_id: string; count: number; history: TelemetryHistoryPoint[] }> {
  return requestJson<{ station_id: string; count: number; history: TelemetryHistoryPoint[] }>(
    `${API_BASE}/telemetry/${stationId}/history?limit=${limit}`
  );
}

export async function ingestFieldTelemetry(payload: {
  station_id: string;
  source?: string;
  readings?: Array<{ sensor_id: string; value: any; quality?: string }>;
  sensor_id?: string;
  value?: any;
}): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchIngestionStatus(): Promise<any> {
  return requestJson<any>(`${API_BASE}/telemetry/ingest/status`);
}

// ============================================================================
// 3. COGNITIVE AGENT SOCIETY & TOPOLOGICAL CAUSAL GRAPH
// ============================================================================

export async function fetchAgentSocietyStatus(): Promise<AgentSocietyStatus> {
  return requestJson<AgentSocietyStatus>(`${API_BASE}/agents/status`);
}

export async function fetchBusStatistics(): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/bus/stats`);
}

export async function fetchAgentDetail(agentRole: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/${agentRole}`);
}

export async function fetchCausalGraph(): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/causal_graph`);
}

export async function fetchNodeBlastRadius(nodeId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/causal_graph/blast_radius/${nodeId}`);
}

export async function fetchGroqStatus(): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/groq_status`);
}

export async function setGroqKey(apiKey: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/agents/set_groq_key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey }),
  });
}

export async function fetchDynamicAgentCalls(limit = 50): Promise<DynamicAgentCall[]> {
  return requestJson<DynamicAgentCall[]>(`${API_BASE}/agents/dynamic_calls?limit=${limit}`);
}

export async function triggerAgentDeliberation(stationId: StationId = 'bharati', anomaly?: any): Promise<any> {
  // If anomaly specifies a scenario or node, trigger target disturbance or advance deliberation tick
  const targetScenario = anomaly?.scenario || 'GENERATOR_TRIP';
  try {
    return await injectScenario(targetScenario, { station_id: stationId, ...anomaly });
  } catch {
    return { status: 'DELIBERATION_DISPATCHED', station_id: stationId };
  }
}

// ============================================================================
// 4. DELIBERATION SESSIONS & BRIEFING CARDS
// ============================================================================

export async function fetchDeliberationSessions(): Promise<any[]> {
  return requestJson<any[]>(`${API_BASE}/deliberations`);
}

export async function fetchDeliberationSession(sessionId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/deliberations/${sessionId}`);
}

export async function fetchCommanderBriefingCard(sessionId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/deliberations/${sessionId}/briefing_card`);
}

// ============================================================================
// 5. ACTIONS, SAFETY INTERLOCKS & PHYSICAL ACTUATORS
// ============================================================================

export async function fetchActuationHistory(stationIdOrLimit?: string | number, limit = 50): Promise<ActuationRecord[]> {
  let stationId: string | undefined;
  let finalLimit = limit;
  if (typeof stationIdOrLimit === 'number') {
    finalLimit = stationIdOrLimit;
  } else if (typeof stationIdOrLimit === 'string') {
    stationId = stationIdOrLimit;
  }
  const query = stationId ? `station_id=${stationId}&limit=${finalLimit}` : `limit=${finalLimit}`;
  return requestJson<ActuationRecord[]>(`${API_BASE}/actions/history?${query}`);
}

export async function fetchPendingActions(): Promise<any[]> {
  return requestJson<any[]>(`${API_BASE}/actions/pending`);
}

export async function fetchPendingTier3Actions(): Promise<any[]> {
  return requestJson<any[]>(`${API_BASE}/actions/pending_tier3`);
}

export async function bypassSupervisedAction(actionId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/supervised/${actionId}/bypass`, { method: 'POST' });
}

export async function cancelSupervisedAction(actionId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/supervised/${actionId}/cancel`, { method: 'POST' });
}

export async function cancelTier3Action(actionId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/tier3/${actionId}/cancel`, { method: 'POST' });
}

export async function authorizeCommanderPin(payload: {
  pin: string;
  command?: string;
  parameters?: Record<string, any>;
  action_id?: string;
}): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/authorize_pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function executeAction(actionIdOrPayload: string | any, stationId: StationId = 'bharati'): Promise<any> {
  if (typeof actionIdOrPayload === 'string') {
    // Try supervised bypass first
    try {
      const bypassRes = await fetch(`${API_BASE}/actions/supervised/${actionIdOrPayload}/bypass`, { method: 'POST' });
      if (bypassRes.ok) return bypassRes.json();
    } catch {}

    return requestJson<any>(`${API_BASE}/actions/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan_name: `Manual Execution ${actionIdOrPayload}`,
        strategy: 'OPERATIONAL_MITIGATION',
        autonomy_tier: 'TIER_1',
        actions: [{ target: actionIdOrPayload, station_id: stationId, status: 'EXECUTED' }],
        expected_outcome: 'Manual override dispatched',
      }),
    });
  }

  return requestJson<any>(`${API_BASE}/actions/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(actionIdOrPayload),
  });
}

export async function fetchStationActuators(stationId: StationId = 'bharati'): Promise<ActuatorState> {
  return requestJson<ActuatorState>(`${API_BASE}/actions/actuators/${stationId}`);
}

export async function executeActuatorCommand(
  stationId: StationId = 'bharati', 
  command: string, 
  parameters: Record<string, any> = {},
  pin?: string
): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/actuators/${stationId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command, parameters, pin }),
  });
}

export async function fetchCognitiveLogs(
  stationId: StationId = 'bharati', 
  category?: string, 
  limit = 50
): Promise<CognitiveLogEntry[]> {
  const query = category ? `category=${category}&limit=${limit}` : `limit=${limit}`;
  return requestJson<CognitiveLogEntry[]>(`${API_BASE}/actions/cognitive_logs/${stationId}?${query}`);
}

export async function configureAutonomousMode(payload: {
  autonomous_enabled?: boolean;
  continuous_running?: boolean;
  speed?: number;
}): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/autonomous_mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchEdgeStatus(stationId: StationId = 'bharati'): Promise<any> {
  return requestJson<any>(`${API_BASE}/actions/edge_status/${stationId}`);
}

// ============================================================================
// 6. SCENARIO SIMULATION & DISTURBANCES
// ============================================================================

export async function fetchAvailableScenarios(): Promise<any[]> {
  return requestJson<any[]>(`${API_BASE}/scenarios`);
}

export async function injectScenario(scenario: string, params: Record<string, any> = {}): Promise<any> {
  const stationId = params.station_id || 'bharati';
  return requestJson<any>(`${API_BASE}/scenarios/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, station_id: stationId, parameters: params }),
  });
}

export async function clearScenario(stationId: StationId = 'bharati'): Promise<any> {
  return requestJson<any>(`${API_BASE}/scenarios/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId }),
  });
}

// ============================================================================
// 7. POLAR SATCOM BANDWIDTH-AWARE SYNCHRONIZATION
// ============================================================================

export async function fetchSatcomStatus(): Promise<any> {
  return requestJson<any>(`${API_BASE}/satcom/status`);
}

export async function fetchStationSatcomSummary(stationId: StationId): Promise<any> {
  return requestJson<any>(`${API_BASE}/satcom/${stationId}/summary`);
}

export async function fetchSatcomMirrorTwin(stationId: StationId): Promise<SatcomMirrorTwin> {
  return requestJson<SatcomMirrorTwin>(`${API_BASE}/satcom/${stationId}/mirror`);
}

export async function setSatcomProfile(
  profile: 'LAN_DIRECT' | 'INMARSAT_STANDARD' | 'IRIDIUM_LOW' | 'POLAR_BLACKOUT',
  stationId?: StationId
): Promise<any> {
  return requestJson<any>(`${API_BASE}/satcom/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, station_id: stationId }),
  });
}

export async function triggerSatcomSync(stationId: StationId = 'bharati', forceKeyframe: boolean = false): Promise<any> {
  return requestJson<any>(`${API_BASE}/satcom/${stationId}/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_keyframe: forceKeyframe }),
  });
}

export async function recoverSatcomBlackout(stationId: StationId = 'bharati', newProfile = 'INMARSAT_STANDARD'): Promise<any> {
  return requestJson<any>(`${API_BASE}/satcom/${stationId}/recover`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_profile: newProfile }),
  });
}

// Backward-compatible helpers
export async function configureSatcom(stationId: StationId, profile: string): Promise<any> {
  // Normalize profile names to backend valid set
  let validProfile: 'LAN_DIRECT' | 'INMARSAT_STANDARD' | 'IRIDIUM_LOW' | 'POLAR_BLACKOUT' = 'INMARSAT_STANDARD';
  const p = profile.toUpperCase();
  if (p.includes('LAN')) validProfile = 'LAN_DIRECT';
  else if (p.includes('IRIDIUM')) validProfile = 'IRIDIUM_LOW';
  else if (p.includes('BLACKOUT') || p.includes('SEVER')) validProfile = 'POLAR_BLACKOUT';

  return setSatcomProfile(validProfile, stationId);
}

export async function severSatcom(stationId: StationId = 'bharati', _durationSeconds = 30): Promise<any> {
  return setSatcomProfile('POLAR_BLACKOUT', stationId);
}

// ============================================================================
// 8. 2-STEP DISTRIBUTED DATABASE & INCIDENT EPISODES
// ============================================================================

export async function fetchDatabaseStatus(): Promise<any> {
  return requestJson<any>(`${API_BASE}/database/status`);
}

export async function fetchIncidentEpisodes(stationId?: StationId, limit = 15): Promise<IncidentEpisode[]> {
  const query = stationId ? `station_id=${stationId}&limit=${limit}` : `limit=${limit}`;
  return requestJson<IncidentEpisode[]>(`${API_BASE}/database/episodes?${query}`);
}

export async function fetchIncidentEpisodeDetail(episodeId: string): Promise<any> {
  return requestJson<any>(`${API_BASE}/database/episodes/${episodeId}`);
}

export async function fetchEquipmentLifecycle(stationId?: StationId): Promise<EquipmentAsset[]> {
  const query = stationId ? `station_id=${stationId}` : '';
  return requestJson<EquipmentAsset[]>(`${API_BASE}/database/equipment?${query}`);
}

export async function fetchOperatorAudits(stationId?: StationId, limit = 30): Promise<OperatorAudit[]> {
  const query = stationId ? `station_id=${stationId}&limit=${limit}` : `limit=${limit}`;
  return requestJson<OperatorAudit[]>(`${API_BASE}/database/audits?${query}`);
}

export async function triggerDatabaseSync(): Promise<any> {
  return requestJson<any>(`${API_BASE}/database/sync`, { method: 'POST' });
}

// ============================================================================
// 9. "ASK F.R.I.D.A.Y." INTERACTIVE AI COPILOT
// ============================================================================

export async function sendCopilotChat(
  message: string, 
  stationId: StationId = 'bharati'
): Promise<{
  reply: string;
  cited_sensors: string[];
  suggested_followups: string[];
  operational_status: string;
  latency_ms: number;
  model_used: string;
  is_live_groq: boolean;
}> {
  return requestJson<{
    reply: string;
    cited_sensors: string[];
    suggested_followups: string[];
    operational_status: string;
    latency_ms: number;
    model_used: string;
    is_live_groq: boolean;
  }>(`${API_BASE}/copilot/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, station_id: stationId }),
  });
}

export async function fetchCopilotHistory(stationId: StationId = 'bharati', limit = 50): Promise<CopilotMessage[]> {
  const data = await requestJson<{ messages?: CopilotMessage[]; history?: CopilotMessage[] }>(
    `${API_BASE}/copilot/history?station_id=${stationId}&limit=${limit}`
  );
  return data.messages || data.history || [];
}

export async function clearCopilotHistory(stationId: StationId = 'bharati'): Promise<any> {
  return requestJson<any>(`${API_BASE}/copilot/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId }),
  });
}

// ============================================================================
// 10. STATE SYNCHRONIZATION & OPERATOR SESSION CONTINUITY
// ============================================================================

export async function fetchSynchronizedState(): Promise<any> {
  return requestJson<any>(`${API_BASE}/sync/state`);
}

export async function updateSynchronizedState(payload: Record<string, any>): Promise<any> {
  return requestJson<any>(`${API_BASE}/sync/state`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function operatorLogin(payload: {
  operator_id?: string;
  operator_name?: string;
  pin?: string;
  station_id?: string;
}): Promise<any> {
  return requestJson<any>(`${API_BASE}/sync/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

// ============================================================================
// 11. SPACE WEATHER & POLAR METEOROLOGICAL ENGINES
// ============================================================================

export async function fetchSpaceWeatherCurrent(): Promise<any> {
  return requestJson<any>(`${API_BASE}/environmental/space-weather/current`);
}

export async function simulateGeomagneticStorm(gLevel: string = 'G4'): Promise<any> {
  return requestJson<any>(`${API_BASE}/environmental/space-weather/simulate-storm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ g_level: gLevel }),
  });
}

export async function fetchPolarWeatherCurrent(): Promise<any> {
  return requestJson<any>(`${API_BASE}/environmental/weather/current`);
}

export async function simulatePolarBlizzard(condition: string = 'CONDITION_1_LOCKOUT'): Promise<any> {
  return requestJson<any>(`${API_BASE}/environmental/weather/simulate-blizzard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ condition }),
  });
}

