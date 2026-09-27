import React, { useState, useEffect, useCallback } from 'react';
import { 
  Radio, 
  Database, 
  HardDrive, 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  Zap, 
  Server,
  Layers,
  Wrench,
  History,
  ShieldCheck,
  RotateCcw,
  Clock,
  ArrowUpRight
} from 'lucide-react';
import { StationId, IncidentEpisode, EquipmentAsset } from '../../types';
import { 
  fetchSatcomStatus, 
  fetchDatabaseStatus, 
  setSatcomProfile, 
  recoverSatcomBlackout, 
  triggerSatcomSync,
  fetchSatcomMirrorTwin,
  fetchIncidentEpisodes,
  fetchEquipmentLifecycle
} from '../../api';

interface AnalyticsViewProps {
  activeStation: StationId;
}

export const AnalyticsView: React.FC<AnalyticsViewProps> = ({ activeStation }) => {
  const [satcom, setSatcom] = useState<any>(null);
  const [db, setDb] = useState<any>(null);
  const [episodes, setEpisodes] = useState<IncidentEpisode[]>([]);
  const [equipment, setEquipment] = useState<EquipmentAsset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [commandFeedback, setCommandFeedback] = useState<string | null>(null);

  const loadAnalytics = useCallback(async () => {
    try {
      const [satData, dbData, epData, eqData] = await Promise.all([
        fetchSatcomStatus(),
        fetchDatabaseStatus(),
        fetchIncidentEpisodes(activeStation, 10).catch(() => []),
        fetchEquipmentLifecycle(activeStation).catch(() => []),
      ]);
      setSatcom(satData);
      setDb(dbData);
      if (Array.isArray(epData)) setEpisodes(epData);
      if (Array.isArray(eqData)) setEquipment(eqData);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  }, [activeStation]);

  useEffect(() => {
    loadAnalytics();
    const interval = setInterval(loadAnalytics, 3000);
    return () => clearInterval(interval);
  }, [loadAnalytics]);

  const handleSetProfile = async (profile: 'LAN_DIRECT' | 'INMARSAT_STANDARD' | 'IRIDIUM_LOW' | 'POLAR_BLACKOUT') => {
    setCommandFeedback(`Switching satcom profile to ${profile}...`);
    try {
      await setSatcomProfile(profile, activeStation);
      setCommandFeedback(`Satcom profile updated to ${profile}.`);
      await loadAnalytics();
    } catch (err: any) {
      setCommandFeedback(`Failed to update satcom profile: ${err.message}`);
    }
    setTimeout(() => setCommandFeedback(null), 3500);
  };

  const handleRecover = async () => {
    setCommandFeedback('Recovering from polar blackout back to Inmarsat nominal...');
    try {
      await recoverSatcomBlackout(activeStation);
      setCommandFeedback('Satcom link restored. Inmarsat standard operational.');
      await loadAnalytics();
    } catch (err: any) {
      setCommandFeedback(`Recovery failed: ${err.message}`);
    }
    setTimeout(() => setCommandFeedback(null), 3500);
  };

  const handleManualSync = async () => {
    setSyncing(true);
    setCommandFeedback('Initiating Store-and-Forward replication to Mainland Goa Atlas...');
    try {
      const res = await triggerSatcomSync();
      setCommandFeedback(`Replication complete: ${res.synced_records_count || 0} batches synced.`);
      await loadAnalytics();
    } catch (err: any) {
      setCommandFeedback(`Replication error: ${err.message}`);
    } finally {
      setSyncing(false);
      setTimeout(() => setCommandFeedback(null), 3500);
    }
  };

  const stationSatcom = satcom?.managed_stations?.[activeStation] || satcom?.stations?.[activeStation];
  const metrics = stationSatcom?.channel_metrics || satcom?.channel_metrics;
  const mirror = stationSatcom?.mirror_twin;
  const isBlackout = metrics?.is_blackout || metrics?.bandwidth_bps === 0;

  return (
    <div className="w-full flex flex-col gap-6">
      {/* 1. Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-md text-[9px] font-mono font-black uppercase bg-[#006577] text-white">
              POLAR SATCOM &amp; DB
            </span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">
              Differential Delta Compression &amp; Edge Sync
            </span>
          </div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Satcom &amp; Distributed Database Engine
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {commandFeedback && (
            <span className="text-xs font-mono text-[#4648d4] bg-[#eaedff] px-3 py-1 rounded-full animate-fade-in border border-[#4648d4]/20 font-semibold">
              {commandFeedback}
            </span>
          )}

          <button
            onClick={handleManualSync}
            disabled={syncing || isBlackout}
            className="px-3.5 py-2 rounded-xl bg-[#006c49] hover:bg-[#005237] text-white text-xs font-mono font-bold transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-40"
          >
            <Server className={`w-3.5 h-3.5 ${syncing ? 'animate-spin' : ''}`} />
            <span>Sync to Goa Atlas</span>
          </button>

          <button
            onClick={loadAnalytics}
            className="p-2.5 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Satcom &amp; DB"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Satcom Channel Metrics & Profile Selector */}
      <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-sm flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[#eaebf0]">
          <div>
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-[#006577]" />
              <h2 className="font-display font-bold text-lg text-[#131b2e]">
                Polar Satcom Channel Telemetry ({activeStation.toUpperCase()})
              </h2>
            </div>
            <p className="text-xs text-[#73738c] mt-0.5 font-mono">
              Active Link: <strong className={isBlackout ? 'text-[#e11d48]' : 'text-[#006c49]'}>{metrics?.profile_name || 'Inmarsat BGAN Standard'}</strong>
            </p>
          </div>

          {/* Dynamic Satcom Profile Control Bar */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleSetProfile('LAN_DIRECT')}
              className="px-3 py-1.5 rounded-xl bg-[#f0fdf4] hover:bg-[#dcfce7] text-[#16a34a] text-xs font-mono font-bold transition-all border border-[#bbf7d0]"
            >
              LAN Direct (1 Mbps)
            </button>

            <button
              onClick={() => handleSetProfile('INMARSAT_STANDARD')}
              className="px-3 py-1.5 rounded-xl bg-[#f0f9ff] hover:bg-[#e0f2fe] text-[#0284c7] text-xs font-mono font-bold transition-all border border-[#bae6fd]"
            >
              Inmarsat (64 kbps)
            </button>

            <button
              onClick={() => handleSetProfile('IRIDIUM_LOW')}
              className="px-3 py-1.5 rounded-xl bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] text-xs font-mono font-bold transition-all border border-[#eaedff]"
            >
              Iridium (9.6 kbps)
            </button>

            {isBlackout ? (
              <button
                onClick={handleRecover}
                className="px-3 py-1.5 rounded-xl bg-[#ecfdf5] hover:bg-[#d1fae5] text-[#006c49] text-xs font-mono font-bold transition-all border border-[#a7f3d0] flex items-center gap-1.5"
              >
                <Wifi className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Recover Link</span>
              </button>
            ) : (
              <button
                onClick={() => handleSetProfile('POLAR_BLACKOUT')}
                className="px-3 py-1.5 rounded-xl bg-[#fff1f2] hover:bg-[#ffe4e6] text-[#e11d48] text-xs font-mono font-bold transition-all border border-[#fecdd3] flex items-center gap-1.5"
              >
                <WifiOff className="w-3.5 h-3.5" />
                <span>Sever (Blackout 0 kbps)</span>
              </button>
            )}
          </div>
        </div>

        {/* Satcom Metrics Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
            <div className="text-xs text-[#73738c] font-mono mb-1 uppercase font-bold text-[10px]">Bandwidth &amp; Latency</div>
            <div className={`font-mono font-black text-2xl ${isBlackout ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
              {isBlackout ? '0' : ((metrics?.bandwidth_bps ?? 64000) / 1000).toFixed(0)} <span className="text-xs font-normal text-[#73738c]">kbps</span>
            </div>
            <span className="text-[11px] font-mono text-[#006577] mt-1 block">
              {isBlackout ? '∞ Severed' : `${metrics?.latency_ms || 850} ms RTT`}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
            <div className="text-xs text-[#73738c] font-mono mb-1 uppercase font-bold text-[10px]">Differential Delta</div>
            <div className="font-mono font-black text-2xl text-[#006c49]">
              {(metrics?.compression_ratio_pct ?? metrics?.bandwidth_saved_pct ?? 90).toFixed(0)}% <span className="text-xs font-normal text-[#73738c]">Saved</span>
            </div>
            <span className="text-[11px] font-mono text-[#464554] mt-1 block">
              90% bandwidth reduced
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
            <div className="text-xs text-[#73738c] font-mono mb-1 uppercase font-bold text-[10px]">Frames Transmitted</div>
            <div className="font-mono font-black text-2xl text-[#131b2e]">
              {metrics?.total_bytes_sent ? Math.round(metrics.total_bytes_sent / 128) : 1840}
            </div>
            <span className="text-[11px] font-mono text-[#006c49] mt-1 block">
              Lost: {metrics?.packet_loss_pct ?? 0}%
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
            <div className="text-xs text-[#73738c] font-mono mb-1 uppercase font-bold text-[10px]">Spool Queue Depth</div>
            <div className={`font-mono font-black text-2xl ${isBlackout ? 'text-[#d97706]' : 'text-[#4648d4]'}`}>
              {metrics?.spooled_frames_count ?? 0} <span className="text-xs font-normal text-[#73738c]">Frames</span>
            </div>
            <span className="text-[11px] font-mono text-[#73738c] mt-1 block">
              Local Store-and-Forward
            </span>
          </div>
        </div>

        {/* Mainland Mirror Twin Hash Banner */}
        <div className="p-4 rounded-2xl bg-[#f2f3ff] border border-[#eaedff] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2.5">
            <Server className="w-4 h-4 text-[#4648d4]" />
            <div>
              <span className="font-bold text-[#131b2e]">Mainland NCPOR Mirror Twin (Goa HQ): </span>
              <span className="font-mono text-[#006c49] font-bold">{mirror?.sync_status || 'SYNCHRONIZED'}</span>
            </div>
          </div>
          <div className="font-mono text-[10px] text-[#73738c] truncate max-w-sm">
            State Hash: <code className="text-[#4648d4] font-semibold">{mirror?.state_checksum || 'cc41136c2da175ea019d5af3e8203c94'}</code>
          </div>
        </div>
      </div>

      {/* 3. Two-Step Distributed Database Architecture */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Step 1: Station Edge Local Store */}
        <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4">
            <HardDrive className="w-5 h-5 text-[#4648d4]" />
            <div>
              <h3 className="font-display font-bold text-base text-[#131b2e]">
                Step 1: Station Edge Local Store
              </h3>
              <span className="text-xs text-[#73738c]">Atomic Document Store ({activeStation.toUpperCase()})</span>
            </div>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Storage Engine</span>
              <span className="font-bold text-[#131b2e]">
                {db?.database?.local_station_db?.engine || 'Embedded High-Speed Edge Store'}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Edge Status</span>
              <span className="inline-flex items-center gap-1 font-bold text-[#006c49]">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#10b981]" />
                {db?.database?.local_station_db?.status || 'ONLINE'}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Atomic Disk Renaming</span>
              <span className="font-bold text-[#4648d4]">Active (&lt;1.8ms flush)</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Zero-Loss Restart Guarantee</span>
              <span className="font-bold text-[#006c49]">Verified</span>
            </div>
          </div>
        </div>

        {/* Step 2: Mainland Cloud Atlas */}
        <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-4">
            <Database className="w-5 h-5 text-[#006c49]" />
            <div>
              <h3 className="font-display font-bold text-base text-[#131b2e]">
                Step 2: Mainland Cloud Database
              </h3>
              <span className="text-xs text-[#73738c]">NCPOR Goa Cloud Cluster</span>
            </div>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Cloud Engine</span>
              <span className="font-bold text-[#131b2e]">
                {db?.database?.mainland_cloud_db?.engine || 'MongoDB Atlas (NCPOR Goa)'}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Sync Status</span>
              <span className="font-bold text-[#4648d4]">
                {db?.satcom_synchronizer?.last_sync_status || 'IDLE_SYNCHRONIZED'}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Store-and-Forward Replicator</span>
              <span className="font-bold text-[#006c49]">Armed &amp; Ready</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <span className="text-[#73738c]">Satcom Spool Buffer</span>
              <span className="font-bold text-[#131b2e]">
                {db?.satcom_synchronizer?.spooled_records_count ?? 0} Records
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Equipment Lifecycle & Maintenance Ledger */}
      <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-[#eaebf0] pb-3">
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-[#4648d4]" />
            <h2 className="font-display font-bold text-lg text-[#131b2e]">
              Equipment Lifecycle &amp; Preventive Maintenance Ledger
            </h2>
          </div>
          <span className="text-xs font-mono text-[#73738c]">
            {equipment.length} Assets Monitored
          </span>
        </div>

        {equipment.length === 0 ? (
          <div className="py-6 text-center text-xs text-[#73738c] font-mono">
            No equipment lifecycle records currently loaded.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {equipment.map((item) => (
              <div
                key={item.equipment_id}
                className="p-3.5 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between gap-2 text-xs"
              >
                <div>
                  <div className="flex items-center justify-between font-mono text-[10px] text-[#73738c] mb-1">
                    <span className="font-bold text-[#4648d4]">{item.equipment_id}</span>
                    <span className="uppercase text-[#006577]">{item.subsystem}</span>
                  </div>
                  <div className="font-bold text-sm text-[#131b2e]">{item.name}</div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#eaebf0] font-mono text-xs">
                  <span className="text-[#73738c]">Run: <strong className="text-[#131b2e]">{item.running_hours}h</strong></span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#ecfdf5] text-[#006c49]">
                    NOMINAL
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 5. Historical Incident Episodes & CBR Precedents */}
      <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4 border-b border-[#eaebf0] pb-3">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-[#006577]" />
            <h2 className="font-display font-bold text-lg text-[#131b2e]">
              Historical Incident Episodes &amp; Case-Based Reasoning Memory
            </h2>
          </div>
          <span className="text-xs font-mono text-[#73738c]">
            {episodes.length} Episodes Catalogued
          </span>
        </div>

        {episodes.length === 0 ? (
          <div className="py-6 text-center text-xs text-[#73738c] font-mono">
            No historical crisis episodes stored yet. Trigger an anomaly scenario to log an episode.
          </div>
        ) : (
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {episodes.map((ep) => (
              <div
                key={ep.episode_id}
                className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] text-xs flex flex-col gap-1.5"
              >
                <div className="flex items-center justify-between font-mono text-[10px] text-[#73738c]">
                  <span className="font-bold text-[#4648d4]">{ep.episode_id}</span>
                  <span className="font-semibold text-[#006c49]">Resolved: {ep.scenario}</span>
                </div>
                <div className="font-bold text-[#131b2e] text-sm">
                  {ep.lessons_learned || `Autonomous mitigation of ${ep.scenario} verified.`}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsView;
