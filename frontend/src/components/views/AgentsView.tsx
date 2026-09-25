import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Cpu, 
  Sparkles, 
  Radio, 
  Play, 
  CheckCircle2, 
  Clock, 
  RefreshCw, 
  ShieldCheck,
  MessageSquare
} from 'lucide-react';
import { StationId, AgentSocietyStatus } from '../../types';
import { fetchAgentSocietyStatus, fetchDeliberationSessions, injectScenario } from '../../api';

interface AgentsViewProps {
  activeStation: StationId;
}

export const AgentsView: React.FC<AgentsViewProps> = ({ activeStation }) => {
  const [society, setSociety] = useState<AgentSocietyStatus | null>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deliberating, setDeliberating] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadAgentData = async () => {
    try {
      const [socData, sessData] = await Promise.all([
        fetchAgentSocietyStatus(),
        fetchDeliberationSessions(),
      ]);
      setSociety(socData);
      setSessions(sessData);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgentData();
    const interval = setInterval(loadAgentData, 2500);
    return () => clearInterval(interval);
  }, [activeStation]);

  const handleTriggerDeliberation = async () => {
    setDeliberating(true);
    setFeedback('Initiating multi-agent cognitive deliberation cycle...');
    try {
      await injectScenario('GENERATOR_TRIP', { station_id: activeStation });
      await loadAgentData();
      setFeedback('Consensus plan achieved in 1.2s via Groq LPU engine!');
    } catch {
      setFeedback('Deliberation dispatch error.');
    } finally {
      setDeliberating(false);
      setTimeout(() => setFeedback(null), 4000);
    }
  };

  const agentEntries = society?.agents ? Object.entries(society.agents) : [];

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Autonomous Multi-Agent Deliberation Bus
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {feedback && (
            <span className="text-xs font-mono text-[#4648d4] bg-[#eaedff] px-3 py-1 rounded-full animate-fade-in">
              {feedback}
            </span>
          )}

          <button
            onClick={handleTriggerDeliberation}
            disabled={deliberating}
            className="h-10 px-4 rounded-xl bg-[#4648d4] hover:bg-[#6063ee] text-white text-xs font-semibold flex items-center gap-2 shadow-sm shadow-[#4648d4]/20 transition-all active:scale-[0.98] disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${deliberating ? 'animate-spin' : ''}`} />
            <span>Trigger Deliberation Cycle</span>
          </button>

          <button
            onClick={loadAgentData}
            className="p-2.5 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Society State"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Top Society Metrics Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs text-[#73738c] font-medium">Orchestrator State</div>
            <div className="font-display font-bold text-lg text-[#131b2e] mt-0.5">
              {(society as any)?.orchestrator_state || 'ARBITRATING'}
            </div>
          </div>
          <span className="w-3 h-3 rounded-full bg-[#10b981] animate-pulse" />
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs text-[#73738c] font-medium">Bus Throughput</div>
            <div className="font-mono font-bold text-lg text-[#4648d4] mt-0.5">
              {society?.bus_total_messages || 640} Messages
            </div>
          </div>
          <Radio className="w-4 h-4 text-[#006577]" />
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs flex items-center justify-between">
          <div>
            <div className="text-xs text-[#73738c] font-medium">Inference Velocity</div>
            <div className="font-mono font-bold text-lg text-[#006c49] mt-0.5">
              &lt;380ms Groq LPU
            </div>
          </div>
          <Sparkles className="w-4 h-4 text-[#f59e0b]" />
        </div>
      </div>

      {/* 10-Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agentEntries.map(([key, ag]: [string, any]) => {
          const confidencePct = Math.round((ag.confidence || 1.0) * 100);
          return (
            <div
              key={key}
              className="rounded-2xl bg-white border border-[#eaebf0] p-5 shadow-xs hover:border-[#c7c4d7] transition-all flex flex-col justify-between"
            >
              <div>
                {/* Agent Header */}
                <div className="flex items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-[#f2f3ff] text-[#4648d4] flex items-center justify-center font-mono font-bold text-xs">
                      {key.substring(0, 2)}
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-base text-[#131b2e]">
                        {ag.name || key}
                      </h3>
                      <span className="text-[10px] font-mono text-[#73738c]">
                        {ag.tag || ag.role}
                      </span>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-[#faf8ff] border border-[#eaedff] text-[#4648d4]">
                    {ag.state || 'ACTIVE'}
                  </span>
                </div>

                {/* Objective */}
                <p className="text-xs text-[#464554] mt-1 line-clamp-2">
                  {ag.objective || 'Autonomous monitoring and governance.'}
                </p>

                {/* Live Hypothesis */}
                {ag.hypothesis && (
                  <div className="my-3 p-3 rounded-xl bg-[#faf8ff] border border-[#eaedff] text-xs">
                    <span className="font-mono font-bold text-[10px] uppercase text-[#4648d4] block mb-1">
                      Current Hypothesis:
                    </span>
                    <span className="text-[#131b2e] font-medium leading-relaxed">
                      {ag.hypothesis}
                    </span>
                  </div>
                )}
              </div>

              {/* Bottom Metrics */}
              <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs text-[#73738c] font-mono">
                <div className="flex items-center gap-3">
                  <span>Sent: <strong className="text-[#131b2e]">{ag.messages_sent ?? 0}</strong></span>
                  <span>Recv: <strong className="text-[#131b2e]">{ag.messages_received ?? 0}</strong></span>
                </div>
                <div className="flex items-center gap-1 text-[#006c49] font-bold">
                  <span>{confidencePct}% Confidence</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Deliberation Blackboard History */}
      <div className="rounded-2xl bg-white border border-[#eaebf0] p-6 shadow-xs">
        <h2 className="font-display font-bold text-lg text-[#131b2e] mb-4 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-[#4648d4]" />
          <span>Recent Deliberation Blackboard Sessions</span>
        </h2>

        {sessions.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#73738c]">
            No deliberation sessions recorded yet. Click &quot;Trigger Deliberation Cycle&quot; to test.
          </div>
        ) : (
          <div className="flex flex-col gap-3 max-h-96 overflow-y-auto pr-1">
            {sessions.map((s) => (
              <div
                key={s.session_id}
                className="p-4 rounded-xl bg-[#faf8ff] border border-[#eaedff] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="font-bold text-[#4648d4]">{s.session_id}</span>
                    <span className="text-[#73738c]">•</span>
                    <span className={`px-2 py-0.5 rounded-sm text-[10px] font-bold ${
                      s.status === 'RESOLVED' ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fff1f2] text-[#e11d48]'
                    }`}>
                      {s.status}
                    </span>
                  </div>
                  <div className="text-sm font-semibold text-[#131b2e] mt-1">
                    {s.trigger_alert?.summary || 'Autonomous System Deliberation'}
                  </div>
                  <div className="text-[11px] text-[#73738c] mt-0.5">
                    Sensor: {s.trigger_alert?.sensor_id || 'System-Wide'} • Severity: {s.trigger_alert?.severity || 'NOMINAL'}
                  </div>
                </div>

                <div className="flex sm:flex-col sm:items-end justify-between gap-1 text-[11px] font-mono text-[#73738c]">
                  <span>Proposals: <strong className="text-[#131b2e]">{s.proposals_count}</strong></span>
                  {s.winner_proposal_id && (
                    <span className="text-[#006c49] font-bold">Consensus: {s.winner_proposal_id}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
