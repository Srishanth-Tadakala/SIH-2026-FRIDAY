import React, { useState } from 'react';
import { 
  Radio, 
  MessageSquare, 
  Sparkles, 
  Cpu, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  CheckCircle2, 
  ShieldCheck, 
  Flame, 
  AlertTriangle,
  ArrowRight,
  Filter
} from 'lucide-react';
import { DynamicAgentCall } from '../../../types';

interface LiveInterAgentCallStreamProps {
  calls: DynamicAgentCall[];
  sessions: any[];
  groqStatus?: any;
  onSelectAgent?: (role: string) => void;
}

export const LiveInterAgentCallStream: React.FC<LiveInterAgentCallStreamProps> = ({
  calls,
  sessions,
  groqStatus,
  onSelectAgent,
}) => {
  const [activeTab, setActiveTab] = useState<'calls' | 'sessions' | 'groq'>('calls');
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [filterRole, setFilterRole] = useState<string>('ALL');

  const filteredCalls = calls.filter((c) => {
    if (filterRole === 'ALL') return true;
    return c.caller === filterRole || c.callee === filterRole;
  });

  return (
    <div className="w-full rounded-3xl bg-white border border-[#eaebf0] shadow-sm overflow-hidden flex flex-col">
      {/* 1. Header Bar with Tabs and Toggle */}
      <div className="px-5 py-3.5 border-b border-[#eaebf0] flex flex-wrap items-center justify-between gap-3 bg-[#faf8ff]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#4648d4] text-white flex items-center justify-center font-bold text-xs shadow-sm">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="font-display font-bold text-sm text-[#131b2e] leading-tight">
              Live Inter-Agent Neural Bus Telemetry
            </h3>
            <span className="text-[10px] font-mono text-[#73738c]">
              Real-Time Dynamic Message Dispatch &amp; Deliberation Logs
            </span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-2">
          <div className="inline-flex p-1 bg-white rounded-xl border border-[#eaebf0] text-xs font-mono font-semibold">
            <button
              onClick={() => setActiveTab('calls')}
              className={`px-3 py-1 rounded-lg transition-all ${
                activeTab === 'calls'
                  ? 'bg-[#4648d4] text-white shadow-2xs font-bold'
                  : 'text-[#464554] hover:text-[#131b2e]'
              }`}
            >
              <span>Dynamic Calls ({calls.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('sessions')}
              className={`px-3 py-1 rounded-lg transition-all ${
                activeTab === 'sessions'
                  ? 'bg-[#4648d4] text-white shadow-2xs font-bold'
                  : 'text-[#464554] hover:text-[#131b2e]'
              }`}
            >
              <span>Sessions ({sessions.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('groq')}
              className={`px-3 py-1 rounded-lg transition-all ${
                activeTab === 'groq'
                  ? 'bg-[#4648d4] text-white shadow-2xs font-bold'
                  : 'text-[#464554] hover:text-[#131b2e]'
              }`}
            >
              <span>Groq LPU Engine</span>
            </button>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg hover:bg-[#eaedff] text-[#73738c] transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 2. Collapsible Content Body */}
      {isExpanded && (
        <div className="p-4">
          {/* TAB 1: DYNAMIC CALLS */}
          {activeTab === 'calls' && (
            <div className="flex flex-col gap-3">
              {/* Optional Filter by Agent */}
              <div className="flex items-center gap-2 text-xs font-mono overflow-x-auto pb-1">
                <span className="text-[#73738c] text-[11px] flex items-center gap-1 font-bold">
                  <Filter className="w-3.5 h-3.5" /> Filter:
                </span>
                {['ALL', 'SITUATION_AWARENESS', 'DIAGNOSTIC', 'PLANNING', 'WHAT_IF', 'FRIDAY_ORCHESTRATOR'].map((r) => (
                  <button
                    key={r}
                    onClick={() => setFilterRole(r)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                      filterRole === r
                        ? 'bg-[#131b2e] text-white'
                        : 'bg-[#faf8ff] text-[#464554] hover:bg-[#eaedff]'
                    }`}
                  >
                    {r.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {filteredCalls.length === 0 ? (
                <div className="py-8 text-center text-xs font-mono text-[#73738c] bg-[#faf8ff] rounded-2xl border border-[#eaedff]">
                  No dynamic inter-agent calls recorded yet. Trigger a deliberation cycle or crisis simulation to watch live messages.
                </div>
              ) : (
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1 font-mono text-xs">
                  {filteredCalls.map((call, idx) => (
                    <div
                      key={call.message_id || idx}
                      className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff] hover:border-[#4648d4]/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-2.5"
                    >
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-[#4648d4] bg-white px-2 py-0.5 rounded-md border border-[#eaedff]">
                          {call.caller}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5 text-[#73738c]" />
                        <span className="font-bold text-[#006577] bg-white px-2 py-0.5 rounded-md border border-[#eaedff]">
                          {call.callee}
                        </span>
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-[#ecfdf5] text-[#006c49]">
                          {call.call_type}
                        </span>
                        <span className="text-[11px] text-[#131b2e] font-sans font-medium line-clamp-1">
                          {call.summary}
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-[10px] text-[#73738c] whitespace-nowrap self-end sm:self-auto">
                        <span className="text-[#006c49] font-bold">{Math.round((call.confidence ?? 1.0) * 100)}% Conf</span>
                        <span>{new Date(call.timestamp * 1000).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: DELIBERATION BLACKBOARD SESSIONS */}
          {activeTab === 'sessions' && (
            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {sessions.length === 0 ? (
                <div className="py-8 text-center text-xs font-mono text-[#73738c] bg-[#faf8ff] rounded-2xl border border-[#eaedff]">
                  No deliberation blackboard sessions recorded yet.
                </div>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.session_id}
                    className="p-3.5 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2 font-mono">
                        <span className="font-bold text-[#4648d4]">{s.session_id}</span>
                        <span className="text-[#73738c]">•</span>
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          s.status === 'RESOLVED' ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fff1f2] text-[#e11d48]'
                        }`}>
                          {s.status}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-[#131b2e] mt-1">
                        {s.trigger_alert?.summary || 'Autonomous System Deliberation'}
                      </div>
                      <div className="text-[11px] text-[#73738c] mt-0.5 font-mono">
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
                ))
              )}
            </div>
          )}

          {/* TAB 3: GROQ LPU SPECS & STATUS */}
          {activeTab === 'groq' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
                <div className="text-[#73738c] text-[10px] uppercase block">Inference Engine</div>
                <div className="font-bold text-base text-[#131b2e] mt-1">
                  {groqStatus?.model_name || 'LLaMA-3.3-70B-Versatile'}
                </div>
                <div className="text-[10px] text-[#006c49] mt-0.5 font-bold">
                  Groq LPU Tensor Acceleration
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
                <div className="text-[#73738c] text-[10px] uppercase block">Inference Latency</div>
                <div className="font-bold text-base text-[#006577] mt-1">
                  &lt;380ms Round-Trip
                </div>
                <div className="text-[10px] text-[#73738c] mt-0.5">
                  Real-time cognitive society bus
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
                <div className="text-[#73738c] text-[10px] uppercase block">Autonomy Level</div>
                <div className="font-bold text-base text-[#4648d4] mt-1">
                  Tier 1 Autonomous Governor
                </div>
                <div className="text-[10px] text-[#10b981] mt-0.5 font-bold">
                  HMAC-SHA256 Token Enforced
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
