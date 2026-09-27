/**
 * Persistent Cognitive Memory API Client.
 * 
 * Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
 */

import { requestJson } from './client';

export type MemoryType = 'GLOBAL' | 'STATION' | 'AGENT' | 'INCIDENT' | 'EVENT' | 'OPERATOR' | 'SOP';

export interface MemoryRecord {
  memory_id: string;
  memory_type: MemoryType;
  agent_role: string;
  station_id: string;
  title: string;
  summary: string;
  content: string;
  importance: number;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  source: string;
  tags: string[];
  related_incident_id?: string | null;
  related_event_id?: string | null;
  metadata?: Record<string, any>;
  created_at_utc: string;
  updated_at_utc: string;
}

export interface MemoryRetrievalEvent {
  event_id: string;
  agent_role: string;
  station_id: string;
  query: string;
  memories_found: number;
  memory_ids: string[];
  retrieval_latency_ms: number;
  context_size_bytes: number;
  memory_injection_success: boolean;
  timestamp_utc: string;
}

export interface MemoryStatsSummary {
  total_memories: number;
  counts_by_agent: Record<string, number>;
  counts_by_type: Record<string, number>;
  counts_by_station: Record<string, number>;
  total_retrieval_events: number;
  average_retrieval_latency_ms: number;
  recent_retrieval_events: MemoryRetrievalEvent[];
}

export interface MemoryFilterParams {
  agent_role?: string;
  station_id?: string;
  memory_type?: string;
  severity?: string;
  query?: string;
  limit?: number;
  offset?: number;
}

export async function fetchMemories(params: MemoryFilterParams = {}): Promise<MemoryRecord[]> {
  const queryParts: string[] = [];
  if (params.agent_role && params.agent_role !== 'ALL') queryParts.push(`agent_role=${encodeURIComponent(params.agent_role)}`);
  if (params.station_id && params.station_id !== 'all') queryParts.push(`station_id=${encodeURIComponent(params.station_id)}`);
  if (params.memory_type && params.memory_type !== 'ALL') queryParts.push(`memory_type=${encodeURIComponent(params.memory_type)}`);
  if (params.severity && params.severity !== 'ALL') queryParts.push(`severity=${encodeURIComponent(params.severity)}`);
  if (params.query) queryParts.push(`query=${encodeURIComponent(params.query)}`);
  if (params.limit) queryParts.push(`limit=${params.limit}`);
  if (params.offset) queryParts.push(`offset=${params.offset}`);

  const qs = queryParts.length > 0 ? `?${queryParts.join('&')}` : '';
  return requestJson<MemoryRecord[]>(`/api/memory${qs}`);
}

export async function fetchMemoryDetail(memoryId: string): Promise<MemoryRecord> {
  return requestJson<MemoryRecord>(`/api/memory/${encodeURIComponent(memoryId)}`);
}

export async function searchMemories(payload: {
  query: string;
  agent_role?: string;
  station_id?: string;
  tags?: string[];
  limit?: number;
}): Promise<{
  query: string;
  memories_found: number;
  retrieval_event: MemoryRetrievalEvent;
  memories: MemoryRecord[];
}> {
  return requestJson(`/api/memory/search`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createMemory(payload: {
  title: string;
  summary?: string;
  content: string;
  memory_type?: MemoryType;
  agent_role?: string;
  station_id?: string;
  importance?: number;
  severity?: 'INFO' | 'WARNING' | 'CRITICAL';
  source?: string;
  tags?: string[];
  related_incident_id?: string;
}): Promise<{
  status: string;
  memory_id: string;
  database_id: string;
  record: MemoryRecord;
}> {
  return requestJson(`/api/memory`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchMemoryStats(): Promise<MemoryStatsSummary> {
  return requestJson<MemoryStatsSummary>(`/api/memory/stats/summary`);
}

export async function fetchMemoryRetrievalEvents(limit: number = 20): Promise<MemoryRetrievalEvent[]> {
  return requestJson<MemoryRetrievalEvent[]>(`/api/memory/retrievals?limit=${limit}`);
}

export async function fetchAgentMemories(agentRole: string, stationId?: string, limit: number = 30): Promise<MemoryRecord[]> {
  const qs = stationId ? `?station_id=${encodeURIComponent(stationId)}&limit=${limit}` : `?limit=${limit}`;
  return requestJson<MemoryRecord[]>(`/api/memory/agent/${encodeURIComponent(agentRole)}${qs}`);
}

export async function fetchStationMemories(stationId: string, agentRole?: string, limit: number = 30): Promise<MemoryRecord[]> {
  const qs = agentRole ? `?agent_role=${encodeURIComponent(agentRole)}&limit=${limit}` : `?limit=${limit}`;
  return requestJson<MemoryRecord[]>(`/api/memory/station/${encodeURIComponent(stationId)}${qs}`);
}
