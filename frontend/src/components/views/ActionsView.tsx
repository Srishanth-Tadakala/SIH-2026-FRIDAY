import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Play, 
  CheckCircle2, 
  Clock, 
  Lock, 
  RefreshCw, 
  AlertTriangle,
  ArrowRight,
  Cpu
} from 'lucide-react';
import { StationId, ActuationRecord } from '../../types';
import { fetchActuationHistory, fetchPendingActions, executeAction } from '../../api';

interface ActionsViewProps {
  activeStation: StationId;
}

export const ActionsView: React.FC<ActionsViewProps> = ({ activeStation }) => {
  const [history, setHistory] = useState<ActuationRecord[]>([]);
  const [pending, setPending] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadActions = async () => {
    try {
      const [histData, pendData] = await Promise.all([
        fetchActuationHistory(50),
        fetchPendingActions(),
      ]);
      setHistory(histData);
      setPending(pendData);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActions();
    const interval = setInterval(loadActions, 3000);
    return () => clearInterval(interval);
  }, [activeStation]);

  const handleExecutePending = async (actionId: string) => {
    setStatusMessage(`Executing ${actionId}...`);
    try {
      await executeAction(actionId, activeStation);
      setStatusMessage(`Action ${actionId} executed safely on twin!`);
      await loadActions();
    } catch {
      setStatusMessage(`Execution failed.`);
    }
    setTimeout(() => setStatusMessage(null), 3500);
  };

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-bold uppercase tracking-wider text-[#4648d4] mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>ACTION FLIGHT LEDGER &amp; INTERLOCK GATEWAY</span>
          </div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Autonomous Actuation Ledger
          </h1>
          <p className="text-xs sm:text-sm text-[#464554] mt-0.5">
            Immutable record of all physical commands validated by What-If sandbox and executed by F.R.I.D.A.Y.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {statusMessage && (
            <span className="text-xs font-mono text-[#4648d4] bg-[#eaedff] px-3 py-1 rounded-full animate-fade-in">
              {statusMessage}
            </span>
          )}

          <button
            onClick={loadActions}
            className="p-2.5 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Ledger"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 3-Tier Defense Safety Interlocks Card */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-sm">
              Tier 1
            </span>
            <CheckCircle2 className="w-4 h-4 text-[#006c49]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Fully Autonomous</h2>
          <p className="text-xs text-[#73738c] mt-1">
            Safe, reversible micro-adjustments executed in &lt;1.2s without human delay.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#d97706] bg-[#fffbeb] px-2 py-0.5 rounded-sm">
              Tier 2
            </span>
            <Clock className="w-4 h-4 text-[#d97706]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Supervised Autonomy</h2>
          <p className="text-xs text-[#73738c] mt-1">
            Major transitions with 60-second visual &amp; audible supervisor veto window.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#4648d4] bg-[#f2f3ff] px-2 py-0.5 rounded-sm">
              Tier 3
            </span>
            <Lock className="w-4 h-4 text-[#4648d4]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Commander PIN</h2>
          <p className="text-xs text-[#73738c] mt-1">
            Life-critical overrides protected by PBKDF2 (100k rounds) &amp; HMAC token.
          </p>
        </div>
      </div>

      {/* Pending Approval Actions Bar */}
      {pending.length > 0 && (
        <div className="p-5 rounded-2xl bg-[#fffbeb] border border-[#fef3c7]">
          <h3 className="font-display font-bold text-sm text-[#b45309] mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#d97706]" />
            <span>Actions Awaiting Human Confirmation ({pending.length})</span>
          </h3>

          <div className="space-y-2.5">
            {pending.map((p) => (
              <div
                key={p.action_id}
                className="p-3.5 rounded-xl bg-white border border-[#fef3c7] flex items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="font-bold text-[#131b2e]">{p.title}</div>
                  <div className="font-mono text-[11px] text-[#73738c] mt-0.5">
                    ID: {p.action_id} • Tier: {p.autonomy_tier}
                  </div>
                </div>

                <button
                  onClick={() => handleExecutePending(p.action_id)}
                  className="px-4 py-1.5 rounded-lg bg-[#d97706] hover:bg-[#b45309] text-white text-xs font-semibold transition-colors flex items-center gap-1.5"
                >
                  <Play className="w-3 h-3" />
                  <span>Approve &amp; Execute</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution Ledger Table */}
      <div className="rounded-2xl bg-white border border-[#eaebf0] p-6 shadow-xs">
        <h2 className="font-display font-bold text-lg text-[#131b2e] mb-4 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-[#4648d4]" />
          <span>Immutable Actuation Flight Ledger ({history.length} Events)</span>
        </h2>

        {history.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#73738c]">
            No physical actuations recorded yet.
          </div>
        ) : (
          <div className="flex flex-col gap-3.5 max-h-[640px] overflow-y-auto pr-1">
            {history.map((record) => (
              <div
                key={record.action_id}
                className="p-4 rounded-xl bg-[#faf8ff] border border-[#eaedff] hover:border-[#c7c4d7] transition-all text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-[#4648d4]">
                      {record.action_id}
                    </span>
                    <span className="text-[#73738c]">•</span>
                    <span className="font-mono text-[10px] text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-sm font-semibold">
                      {record.autonomy_tier}
                    </span>
                    <span className="text-[#73738c]">•</span>
                    <span className="font-mono text-[10px] text-[#73738c] uppercase">
                      {record.station_id}
                    </span>
                  </div>

                  <span className="font-mono text-[11px] text-[#73738c]">
                    {record.timestamp_iso ? new Date(record.timestamp_iso).toLocaleTimeString() : 'T+103s'}
                  </span>
                </div>

                <div className="font-display font-bold text-sm text-[#131b2e] mb-2">
                  {record.title}
                </div>

                {/* Agent Consensus Chain */}
                {record.dynamic_agent_chain && record.dynamic_agent_chain.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 my-2">
                    <span className="text-[10px] font-mono text-[#73738c]">Chain:</span>
                    {record.dynamic_agent_chain.map((agent, i) => (
                      <span
                        key={agent + i}
                        className="px-2 py-0.5 rounded-md bg-white border border-[#eaedff] text-[10px] font-mono font-semibold text-[#4648d4]"
                      >
                        {agent}
                      </span>
                    ))}
                  </div>
                )}

                {/* Physical Verification */}
                <div className="p-2.5 rounded-lg bg-white border border-[#eaedff] text-[11px] text-[#464554] mt-2">
                  <span className="font-bold text-[#006c49] mr-1.5">✓ Physical Sandbox Verification:</span>
                  <span>{record.physical_verification}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
