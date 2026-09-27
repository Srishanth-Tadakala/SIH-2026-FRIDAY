/**
 * Real Operational Alerts API Client.
 * 
 * Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
 */

import { requestJson } from './client';

export interface AlertRecord {
  id: string;
  station_id: string;
  station_name: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'EMERGENCY' | 'INFO';
  source: string;
  message: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED';
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  related_agent?: string;
  related_telemetry?: {
    sim_time_seconds?: number;
    indoor_temp_c?: number;
    ambient_temp_c?: number;
    wind_speed_mps?: number;
    composite_risk_score?: number;
  };
}

export interface AlertsSummary {
  total_active_alerts: number;
  critical_count: number;
  warning_count: number;
  unacknowledged_count: number;
  alerts: AlertRecord[];
}

export async function fetchAlerts(stationId?: string, severity?: string): Promise<AlertRecord[]> {
  const parts: string[] = [];
  if (stationId && stationId !== 'all') parts.push(`station_id=${encodeURIComponent(stationId)}`);
  if (severity && severity !== 'ALL') parts.push(`severity=${encodeURIComponent(severity)}`);
  const qs = parts.length > 0 ? `?${parts.join('&')}` : '';
  return requestJson<AlertRecord[]>(`/api/alerts${qs}`);
}

export async function acknowledgeAlert(alertId: string, note: string = ''): Promise<{
  status: string;
  alert_id: string;
  acknowledged: boolean;
  operator: string;
  timestamp: string;
}> {
  return requestJson(`/api/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export async function fetchAlertsSummary(stationId?: string): Promise<AlertsSummary> {
  const qs = stationId && stationId !== 'all' ? `?station_id=${encodeURIComponent(stationId)}` : '';
  return requestJson<AlertsSummary>(`/api/alerts/summary${qs}`);
}
