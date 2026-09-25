import { 
  StationId, 
  StationSnapshot, 
  ActuationRecord, 
  DynamicAgentCall, 
  AgentSocietyStatus 
} from './types';

const API_BASE = '/api';

export async function fetchStationSnapshot(stationId: StationId = 'bharati'): Promise<StationSnapshot> {
  const res = await fetch(`${API_BASE}/stations/${stationId}/snapshot`);
  if (!res.ok) throw new Error(`Snapshot failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAgentSocietyStatus(): Promise<AgentSocietyStatus> {
  const res = await fetch(`${API_BASE}/agents/status`);
  if (!res.ok) throw new Error(`Agent status failed: ${res.statusText}`);
  return res.json();
}

export async function fetchDynamicAgentCalls(limit = 50): Promise<DynamicAgentCall[]> {
  const res = await fetch(`${API_BASE}/agents/dynamic_calls?limit=${limit}`);
  if (!res.ok) throw new Error(`Dynamic calls failed: ${res.statusText}`);
  return res.json();
}

export async function fetchActuationHistory(limit = 50): Promise<ActuationRecord[]> {
  const res = await fetch(`${API_BASE}/actions/history?limit=${limit}`);
  if (!res.ok) throw new Error(`Actuation history failed: ${res.statusText}`);
  return res.json();
}

export async function injectScenario(scenario: string, params: Record<string, any> = {}): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/inject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario, params }),
  });
  if (!res.ok) throw new Error(`Inject scenario failed: ${res.statusText}`);
  return res.json();
}

export async function clearScenario(stationId: StationId = 'bharati'): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/clear?station_id=${stationId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Clear scenario failed: ${res.statusText}`);
  return res.json();
}
