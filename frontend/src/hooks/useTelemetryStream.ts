import { useState, useEffect, useRef, useCallback } from 'react';
import { StationId, StationSnapshot, StationKPIs, AgentSocietyStatus } from '../types';
import { fetchStationSnapshot, fetchAgentSocietyStatus } from '../api';

export type ConnectionMode = 'WEBSOCKET' | 'REST_POLLING' | 'CONNECTING';

export interface UseTelemetryStreamResult {
  snapshot: StationSnapshot | null;
  agentSociety: AgentSocietyStatus | null;
  kpis: StationKPIs | null;
  readings: Record<string, { value: number | string | boolean; unit?: string; status?: string; quality?: string }>;
  alerts: any[];
  satcomData: any | null;
  connectionMode: ConnectionMode;
  lastUpdateTimestamp: number;
  triggerStep: (dtSeconds?: number) => void;
  refresh: () => void;
}

export function useTelemetryStream(stationId: StationId = 'bharati'): UseTelemetryStreamResult {
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null);
  const [agentSociety, setAgentSociety] = useState<AgentSocietyStatus | null>(null);
  const [satcomData, setSatcomData] = useState<any | null>(null);
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>('CONNECTING');
  const [lastUpdateTimestamp, setLastUpdateTimestamp] = useState<number>(Date.now());

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const pingIntervalRef = useRef<any>(null);
  const fallbackIntervalRef = useRef<any>(null);
  const isMountedRef = useRef<boolean>(true);

  // Helper to resolve WebSocket endpoint URL
  const getWsUrl = useCallback((sid: string) => {
    const isHttps = window.location.protocol === 'https:';
    const proto = isHttps ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // If running in Vite dev on 5173, target backend on 8000
    const port = window.location.port === '5173' ? '8000' : window.location.port;
    const hostAndPort = port ? `${host}:${port}` : host;
    return `${proto}//${hostAndPort}/ws/telemetry/${sid}`;
  }, []);

  // REST Polling Fallback (1.5s interval)
  const pollRestFallback = useCallback(async () => {
    try {
      const [snap, soc] = await Promise.all([
        fetchStationSnapshot(stationId),
        fetchAgentSocietyStatus().catch(() => null),
      ]);
      if (!isMountedRef.current) return;
      if (snap) {
        setSnapshot(snap);
      }
      if (soc) {
        setAgentSociety(soc);
      }
      setLastUpdateTimestamp(Date.now());
    } catch {
      // Offline nominal
    }
  }, [stationId]);

  // Connect to Multiplexed WebSocket
  useEffect(() => {
    isMountedRef.current = true;
    let ws: WebSocket | null = null;
    let didConnect = false;

    const connectWebSocket = () => {
      if (!isMountedRef.current) return;

      const wsUrl = getWsUrl(stationId);
      setConnectionMode('CONNECTING');

      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMountedRef.current) return;
          didConnect = true;
          setConnectionMode('WEBSOCKET');

          // Subscribe to all 5 multiplexed channels
          const subscribeMsg = JSON.stringify({
            action: 'subscribe',
            channels: ['kpis', 'sensors', 'alerts', 'deliberations', 'satcom'],
          });
          ws?.send(subscribeMsg);

          // Stop REST polling if active
          if (fallbackIntervalRef.current) {
            clearInterval(fallbackIntervalRef.current);
            fallbackIntervalRef.current = null;
          }

          // Start ping heartbeat (every 10s)
          if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ action: 'ping' }));
            }
          }, 10000);
        };

        ws.onmessage = (event) => {
          if (!isMountedRef.current) return;
          try {
            const data = JSON.parse(event.data);
            const channel = data.channel;

            setLastUpdateTimestamp(Date.now());

            if (channel === 'kpis' && data.kpis) {
              setSnapshot((prev) => {
                if (!prev) {
                  return {
                    station_id: stationId,
                    station_name: stationId === 'bharati' ? 'Bharati Research Station' : 'Maitri Research Station',
                    sim_time_seconds: data.sim_time_seconds || 0,
                    timestamp_iso: new Date().toISOString(),
                    active_scenario: 'NORMAL',
                    kpis: data.kpis,
                    alerts: [],
                    readings: {},
                  };
                }
                return {
                  ...prev,
                  sim_time_seconds: data.sim_time_seconds ?? prev.sim_time_seconds,
                  kpis: { ...prev.kpis, ...data.kpis },
                };
              });
            } else if (channel === 'sensors' && data.readings) {
              setSnapshot((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  readings: { ...prev.readings, ...data.readings },
                };
              });
            } else if (channel === 'alerts' && data.alerts) {
              setSnapshot((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  alerts: data.alerts,
                };
              });
            } else if (channel === 'satcom' && data.satcom) {
              setSatcomData(data.satcom);
            }
          } catch {}
        };

        ws.onerror = () => {
          if (!isMountedRef.current) return;
          // Fall back to REST polling
          if (!didConnect) {
            setConnectionMode('REST_POLLING');
            if (!fallbackIntervalRef.current) {
              pollRestFallback();
              fallbackIntervalRef.current = setInterval(pollRestFallback, 1500);
            }
          }
        };

        ws.onclose = () => {
          if (!isMountedRef.current) return;
          setConnectionMode('REST_POLLING');

          // Engage REST fallback while disconnected
          if (!fallbackIntervalRef.current) {
            pollRestFallback();
            fallbackIntervalRef.current = setInterval(pollRestFallback, 1500);
          }

          // Try reconnecting after 3 seconds
          if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connectWebSocket();
            }
          }, 3000);
        };
      } catch {
        setConnectionMode('REST_POLLING');
        if (!fallbackIntervalRef.current) {
          pollRestFallback();
          fallbackIntervalRef.current = setInterval(pollRestFallback, 1500);
        }
      }
    };

    // Initial snapshot load & WebSocket connection
    pollRestFallback();
    connectWebSocket();

    return () => {
      isMountedRef.current = false;
      if (ws) {
        ws.close();
      }
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (fallbackIntervalRef.current) clearInterval(fallbackIntervalRef.current);
    };
  }, [stationId, getWsUrl, pollRestFallback]);

  // Direct trigger step
  const triggerStep = useCallback((dtSeconds: number = 1.0) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'step', dt_seconds: dtSeconds }));
    } else {
      pollRestFallback();
    }
  }, [pollRestFallback]);

  const kpis = snapshot?.kpis || null;
  const readings = snapshot?.readings || {};
  const alerts = snapshot?.alerts || [];

  return {
    snapshot,
    agentSociety,
    kpis,
    readings,
    alerts,
    satcomData,
    connectionMode,
    lastUpdateTimestamp,
    triggerStep,
    refresh: pollRestFallback,
  };
}
