import { 
  StationId, 
  StationInfo,
  StationSnapshot, 
  ActuationRecord, 
  DynamicAgentCall, 
  AgentSocietyStatus 
} from './types';

const API_BASE = '/api';

export async function fetchStations(): Promise<StationInfo[]> {
  const res = await fetch(`${API_BASE}/stations`);
  if (!res.ok) throw new Error(`Stations list failed: ${res.statusText}`);
  return res.json();
}

export async function fetchStationSnapshot(stationId: StationId = 'bharati'): Promise<StationSnapshot> {
  const res = await fetch(`${API_BASE}/telemetry/${stationId}/snapshot`);
  if (!res.ok) throw new Error(`Snapshot failed: ${res.statusText}`);
  return res.json();
}

export async function fetchStationKPIs(stationId: StationId = 'bharati'): Promise<any> {
  const res = await fetch(`${API_BASE}/telemetry/${stationId}/kpis`);
  if (!res.ok) throw new Error(`KPIs failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPillarTelemetry(stationId: StationId = 'bharati', pillar: string = 'energy'): Promise<any> {
  const res = await fetch(`${API_BASE}/telemetry/${stationId}/pillars/${pillar}`);
  if (!res.ok) throw new Error(`Pillar telemetry failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAgentSocietyStatus(): Promise<AgentSocietyStatus> {
  const res = await fetch(`${API_BASE}/agents/status`);
  if (!res.ok) throw new Error(`Agent status failed: ${res.statusText}`);
  return res.json();
}

export async function fetchBusStatistics(): Promise<any> {
  const res = await fetch(`${API_BASE}/agents/bus/stats`);
  if (!res.ok) throw new Error(`Bus stats failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAgentDetail(agentRole: string): Promise<any> {
  const res = await fetch(`${API_BASE}/agents/${agentRole}`);
  if (!res.ok) throw new Error(`Agent detail failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCausalGraph(): Promise<any> {
  const res = await fetch(`${API_BASE}/agents/causal_graph`);
  if (!res.ok) throw new Error(`Causal graph failed: ${res.statusText}`);
  return res.json();
}

export async function fetchGroqStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/agents/groq_status`);
  if (!res.ok) throw new Error(`Groq status failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDynamicAgentCalls(limit = 50): Promise<DynamicAgentCall[]> {
  const res = await fetch(`${API_BASE}/agents/dynamic_calls?limit=${limit}`);
  if (!res.ok) throw new Error(`Dynamic calls failed: ${res.statusText}`);
  return res.json();
}

export async function triggerAgentDeliberation(stationId: StationId = 'bharati', anomaly?: any): Promise<any> {
  const res = await fetch(`${API_BASE}/agents/deliberate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId, anomaly }),
  });
  if (!res.ok) throw new Error(`Deliberation trigger failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDeliberationSessions(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/deliberations`);
  if (!res.ok) throw new Error(`Deliberations list failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDeliberationSession(sessionId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/deliberations/${sessionId}`);
  if (!res.ok) throw new Error(`Session detail failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActuationHistory(limit = 50): Promise<ActuationRecord[]> {
  const res = await fetch(`${API_BASE}/actions/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Actuation history failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPendingActions(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/actions/pending`);
  if (!res.ok) throw new Error(`Pending actions failed: ${res.statusText}`);
  return res.json();
}

export async function executeAction(actionId: string, stationId: StationId = 'bharati'): Promise<any> {
  try {
    const bypassRes = await fetch(`${API_BASE}/actions/supervised/${actionId}/bypass`, { method: 'POST' });
    if (bypassRes.ok) return bypassRes.json();
  } catch {}

  const res = await fetch(`${API_BASE}/actions/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      plan_name: `Manual Execution ${actionId}`,
      strategy: 'OPERATIONAL_MITIGATION',
      autonomy_tier: 'TIER_1',
      actions: [{ target: actionId, station_id: stationId, status: 'EXECUTED' }],
      expected_outcome: 'Manual override dispatched',
    }),
  });
  if (!res.ok) throw new Error(`Action execution failed: ${res.statusText}`);
  return res.json();
}

export async function validateActionInSandbox(action: any): Promise<any> {
  const res = await fetch(`${API_BASE}/actions/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(action),
  });
  if (!res.ok) throw new Error(`Validation failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSatcomStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/satcom/status`);
  if (!res.ok) throw new Error(`Satcom status failed: ${res.statusText}`);
  return res.json();
}

export async function configureSatcom(stationId: StationId, profile: string): Promise<any> {
  const res = await fetch(`${API_BASE}/satcom/configure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId, profile }),
  });
  if (!res.ok) throw new Error(`Satcom configure failed: ${res.statusText}`);
  return res.json();
}

export async function severSatcom(stationId: StationId = 'bharati', durationSeconds = 30): Promise<any> {
  const res = await fetch(`${API_BASE}/satcom/sever`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId, duration_seconds: durationSeconds }),
  });
  if (!res.ok) throw new Error(`Satcom sever failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDatabaseStatus(): Promise<any> {
  const res = await fetch(`${API_BASE}/database/status`);
  if (!res.ok) throw new Error(`Database status failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAvailableScenarios(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/scenarios`);
  if (!res.ok) throw new Error(`Scenarios catalog failed: ${res.statusText}`);
  return res.json();
}

export async function injectScenario(scenario: string, params: Record<string, any> = {}): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, parameters: params }),
  });
  if (!res.ok) throw new Error(`Inject scenario failed: ${res.statusText}`);
  return res.json();
}

export async function clearScenario(stationId: StationId = 'bharati'): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/clear`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId }),
  });
  if (!res.ok) throw new Error(`Clear scenario failed: ${res.statusText}`);
  return res.json();
}
