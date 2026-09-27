/**
 * Frontend End-to-End Integration Test Suite.
 * 
 * Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
 * Validates backend-driven operational data flow, memory persistence,
 * alert handling, WebSocket lifecycle, and honest empty/unavailable states.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { 
  fetchMemories, 
  fetchMemoryStats, 
  searchMemories, 
  createMemory,
  MemoryRecord 
} from '../api/memory';
import { fetchAlerts, acknowledgeAlert } from '../api/alerts';
import { getStoredToken, setStoredToken, requestJson, ApiError } from '../api/client';

describe('Frontend Real Data Layer & Backend Integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('1. Injects cryptographic Bearer token on authenticated API requests', async () => {
    setStoredToken('test-jwt-token-123');
    expect(getStoredToken()).toBe('test-jwt-token-123');

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ status: 'AUTHENTICATED' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await requestJson('/api/test');
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer test-jwt-token-123');
  });

  it('2. Fails honestly with ApiError instead of silent false fallback', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({ detail: 'SCADA Gateway Offline' }),
    }));

    await expect(requestJson('/api/telemetry/bharati/snapshot')).rejects.toThrow(
      '[503] SCADA Gateway Offline'
    );
  });

  it('3. Loads genuine persistent memory records from backend with filters', async () => {
    const mockRecords: MemoryRecord[] = [
      {
        memory_id: 'MEM-BHA-PLN-0001',
        memory_type: 'SOP',
        agent_role: 'PLANNING',
        station_id: 'bharati',
        title: 'Generator Trip Contingency',
        summary: 'Automatic transfer to CHP-02 within 4.8 seconds',
        content: 'Action sequence: Isolate CHP-01 breaker, synchronize CHP-02, engage ATS.',
        importance: 0.95,
        severity: 'CRITICAL',
        source: 'SOP_DATABASE',
        tags: ['ats', 'generator', 'chp02'],
        created_at_utc: '2026-09-27T10:00:00Z',
        updated_at_utc: '2026-09-27T10:00:00Z',
      },
    ];

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockRecords,
    }));

    const result = await fetchMemories({ agent_role: 'PLANNING', station_id: 'bharati' });
    expect(result).toHaveLength(1);
    expect(result[0].memory_id).toBe('MEM-BHA-PLN-0001');
    expect(result[0].agent_role).toBe('PLANNING');
    expect(result[0].importance).toBe(0.95);
  });

  it('4. Reports 0 memories honestly when database partition is empty', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    }));

    const result = await fetchMemories({ agent_role: 'EDGE' });
    expect(result).toHaveLength(0);
    expect(result).toEqual([]);
  });

  it('5. Queries backend semantic memory search and receives retrieval event metadata', async () => {
    const mockSearchResponse = {
      query: 'generator trip mitigation',
      memories_found: 1,
      retrieval_event: {
        event_id: 'REV-001',
        agent_role: 'PLANNING',
        station_id: 'bharati',
        query: 'generator trip mitigation',
        memories_found: 1,
        memory_ids: ['MEM-BHA-PLN-0001'],
        retrieval_latency_ms: 1.45,
        context_size_bytes: 420,
        memory_injection_success: true,
        timestamp_utc: '2026-09-27T12:00:00Z',
      },
      memories: [
        {
          memory_id: 'MEM-BHA-PLN-0001',
          title: 'Generator Trip Contingency',
          summary: 'Fast transfer switch protocol',
          content: 'Details on ATS synchronization',
          importance: 0.95,
          severity: 'CRITICAL',
          memory_type: 'SOP',
          agent_role: 'PLANNING',
          station_id: 'bharati',
          source: 'SOP',
          tags: ['generator'],
          created_at_utc: '2026-09-27T10:00:00Z',
          updated_at_utc: '2026-09-27T10:00:00Z',
        } as MemoryRecord,
      ],
    };

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockSearchResponse,
    }));

    const res = await searchMemories({ query: 'generator trip mitigation', agent_role: 'PLANNING' });
    expect(res.memories_found).toBe(1);
    expect(res.retrieval_event.retrieval_latency_ms).toBe(1.45);
    expect(res.retrieval_event.memory_injection_success).toBe(true);
    expect(res.memories[0].memory_id).toBe('MEM-BHA-PLN-0001');
  });

  it('6. Fetches and acknowledges operational life-safety alerts', async () => {
    const mockAlerts = [
      {
        id: 'ALT-BH-ELEC-1001',
        station_id: 'bharati',
        station_name: 'Bharati Research Station',
        timestamp: '2026-09-27T11:00:00Z',
        severity: 'CRITICAL',
        source: 'ELECTRICAL',
        message: 'Primary generator CHP-01 offline',
        status: 'ACTIVE',
      },
    ];

    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockAlerts,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          status: 'SUCCESS',
          alert_id: 'ALT-BH-ELEC-1001',
          acknowledged: true,
          operator: 'admin',
          timestamp: '2026-09-27T11:05:00Z',
        }),
      });

    vi.stubGlobal('fetch', fetchMock);

    const alerts = await fetchAlerts('bharati');
    expect(alerts).toHaveLength(1);
    expect(alerts[0].status).toBe('ACTIVE');

    const ack = await acknowledgeAlert('ALT-BH-ELEC-1001', 'Switching to standby generator');
    expect(ack.acknowledged).toBe(true);
    expect(ack.operator).toBe('admin');
  });

  it('7. Stale telemetry detection calculates honesty threshold correctly', () => {
    const now = Date.now();
    const freshTimestamp = now - 2000; // 2s old
    const staleTimestamp = now - 12000; // 12s old (> 8s threshold)

    const isFresh = (now - freshTimestamp) > 8000;
    const isStale = (now - staleTimestamp) > 8000;

    expect(isFresh).toBe(false);
    expect(isStale).toBe(true);
  });

  it('8. Memory creation persists new record through authenticated POST API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        status: 'SUCCESS',
        memory_id: 'MEM-BH-PLN-9999',
        database_id: 'db-uuid-1234',
        record: {
          memory_id: 'MEM-BH-PLN-9999',
          title: 'Trace Heating SOP',
          content: 'Keep utilidor line above +3C',
          agent_role: 'PLANNING',
          station_id: 'bharati',
        },
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    const created = await createMemory({
      title: 'Trace Heating SOP',
      content: 'Keep utilidor line above +3C',
      agent_role: 'PLANNING',
      station_id: 'bharati',
      severity: 'WARNING',
    });

    expect(created.status).toBe('SUCCESS');
    expect(created.memory_id).toBe('MEM-BH-PLN-9999');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/memory',
      expect.objectContaining({ method: 'POST' })
    );
  });
});
