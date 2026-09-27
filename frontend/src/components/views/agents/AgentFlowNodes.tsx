import React from 'react';
import { Handle, Position, NodeToolbar } from '@xyflow/react';
import { 
  Brain, 
  Eye, 
  Activity, 
  TrendingUp, 
  ShieldAlert, 
  FileText, 
  Cpu, 
  Flame, 
  Wrench, 
  Sliders, 
  Crown, 
  Zap, 
  Droplet, 
  CloudSnow, 
  CheckCircle2, 
  RotateCcw, 
  Play, 
  Radio, 
  Sparkles,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  ExternalLink
} from 'lucide-react';

const roleIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  SITUATION_AWARENESS: Eye,
  DIAGNOSTIC: Activity,
  PREDICTION: TrendingUp,
  RISK_IMPACT: ShieldAlert,
  PLANNING: FileText,
  WHAT_IF: Cpu,
  RESOURCE_OPTIMIZER: Sliders,
  MAINTENANCE: Wrench,
  MISSION_OPS: ShieldCheck,
  FRIDAY_ORCHESTRATOR: Crown,
};

const roleColors: Record<string, { bg: string; text: string; border: string; glow: string; badge: string }> = {
  SITUATION_AWARENESS: { bg: 'bg-[#4648d4]', text: 'text-[#4648d4]', border: 'border-[#4648d4]', glow: 'shadow-[#4648d4]/15', badge: 'SENSORY' },
  DIAGNOSTIC: { bg: 'bg-[#4648d4]', text: 'text-[#4648d4]', border: 'border-[#4648d4]', glow: 'shadow-[#4648d4]/15', badge: 'CAUSAL' },
  PREDICTION: { bg: 'bg-[#006577]', text: 'text-[#006577]', border: 'border-[#006577]', glow: 'shadow-[#006577]/15', badge: 'FORECAST' },
  RISK_IMPACT: { bg: 'bg-[#f59e0b]', text: 'text-[#d97706]', border: 'border-[#f59e0b]', glow: 'shadow-[#f59e0b]/15', badge: 'SAFETY' },
  PLANNING: { bg: 'bg-[#10b981]', text: 'text-[#006c49]', border: 'border-[#10b981]', glow: 'shadow-[#10b981]/15', badge: 'PLANNER' },
  WHAT_IF: { bg: 'bg-[#006577]', text: 'text-[#006577]', border: 'border-[#006577]', glow: 'shadow-[#006577]/15', badge: 'PHYSICS' },
  RESOURCE_OPTIMIZER: { bg: 'bg-[#4648d4]', text: 'text-[#4648d4]', border: 'border-[#4648d4]', glow: 'shadow-[#4648d4]/15', badge: 'DISPATCH' },
  MAINTENANCE: { bg: 'bg-[#006577]', text: 'text-[#006577]', border: 'border-[#006577]', glow: 'shadow-[#006577]/15', badge: 'ASSET RUL' },
  MISSION_OPS: { bg: 'bg-[#10b981]', text: 'text-[#006c49]', border: 'border-[#10b981]', glow: 'shadow-[#10b981]/15', badge: 'HABITAT' },
  FRIDAY_ORCHESTRATOR: { bg: 'bg-[#4648d4]', text: 'text-[#4648d4]', border: 'border-[#4648d4]', glow: 'shadow-[#4648d4]/25', badge: 'MASTER' },
};

// Mini SVG Sparkline generator for live activity telemetry inside nodes
const renderMiniWaveform = (points: number[], strokeColor: string, height = 20, width = 76) => {
  if (!points || points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  const d = points
    .map((val, idx) => {
      const x = (idx / (points.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');

  return (
    <svg width={width} height={height} className="overflow-visible inline-block opacity-85">
      <path
        d={d}
        fill="none"
        stroke={strokeColor}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.length > 0 && (
        <circle
          cx={width}
          cy={height - ((points[points.length - 1] - min) / range) * (height - 6) - 3}
          r={2.5}
          fill={strokeColor}
          className="animate-ping"
        />
      )}
    </svg>
  );
};

// Radial Confidence Gauge Component (Minimal SVG arc)
const ConfidenceRadialGauge: React.FC<{ pct: number; color: string; size?: number }> = ({ pct, color, size = 38 }) => {
  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#eaebf0"
          strokeWidth={3}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={3}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="none"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute text-[9px] font-mono font-bold text-[#131b2e] tracking-tighter">
        {pct}%
      </div>
    </div>
  );
};

// ========================================================
// 1. CLUSTER ZONE NODE (Clean Architectural Compound Container)
// ========================================================
export const ClusterZoneNode: React.FC<{ data: any }> = ({ data }) => {
  const isAlarm = data.status === 'ALERT' || data.status === 'TRIPPED';
  return (
    <div
      className={`w-full h-full rounded-3xl border-2 transition-all duration-300 p-5 flex flex-col justify-between pointer-events-none select-none ${
        isAlarm
          ? 'bg-[#fff1f2]/20 border-[#f43f5e]/30'
          : 'bg-[#faf8ff]/40 border-[#eaebf0]/80'
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded-md text-[9px] font-mono font-black tracking-wider uppercase bg-[#131b2e] text-white">
            {data.zoneTag || 'ZONE'}
          </span>
          <span className="font-display font-black text-xs text-[#131b2e] tracking-tight uppercase">
            {data.label}
          </span>
        </div>
        {data.kpi && (
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-white/90 border border-[#eaebf0] text-[#4648d4] shadow-2xs">
            {data.kpi}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between text-[9px] font-mono text-[#73738c] pt-2 border-t border-[#eaebf0]/40">
        <span className="font-semibold">{data.description || 'Cognitive Layer'}</span>
        <span className="inline-flex items-center gap-1 font-bold text-[#006c49]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
          ACTIVE
        </span>
      </div>
    </div>
  );
};

// ========================================================
// 2. AGENT PRO NODE (Clean, Minimal-Text, Advanced Cognitive Unit)
// ========================================================
export const AgentProNode: React.FC<{ data: any }> = ({ data }) => {
  const role = data.role || 'SITUATION_AWARENESS';
  const Icon = roleIcons[role] || Brain;
  const theme = roleColors[role] || roleColors['SITUATION_AWARENESS'];
  const isFriday = role === 'FRIDAY_ORCHESTRATOR';
  const isSelected = data.isSelected;
  const confidence = Math.round((data.confidence || 1.0) * 100);
  const state = data.state || 'ACTIVE';

  const isDeliberating = data.isDeliberating || state === 'DELIBERATING' || state === 'ARBITRATING';
  const isAlarm = state === 'ALERT' || state === 'CRITICAL';

  const waveformPoints = data.history || [65, 70, 72, 75, 78, 80, 76, 75];
  const waveformColor = isFriday ? '#4648d4' : isAlarm ? '#e11d48' : theme.bg === 'bg-[#10b981]' ? '#10b981' : '#4648d4';

  // Crisp, glanceable summary insight
  const insightText = data.hypothesis
    ? data.hypothesis.length > 55
      ? data.hypothesis.substring(0, 52) + '...'
      : data.hypothesis
    : 'All monitored telemetry nominal';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`group relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-300 min-w-[260px] max-w-[280px] shadow-xs select-none ${
        isFriday
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md shadow-[#4648d4]/10 bg-gradient-to-br from-white to-[#faf8ff]'
          : isAlarm
          ? 'border-[#f43f5e] ring-3 ring-[#f43f5e]/25 bg-[#fff1f2]/50 shadow-md'
          : isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-md'
      }`}
    >
      {/* Node Action Toolbar */}
      <NodeToolbar
        isVisible={isSelected}
        position={Position.Top}
        offset={10}
        className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30 font-mono text-[10px]"
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('deliberate', data);
          }}
          className="px-2.5 py-1 rounded-lg bg-[#4648d4] text-white hover:bg-[#3b3dbf] font-bold flex items-center gap-1.5 transition-colors shadow-2xs"
        >
          <Play className="w-3 h-3 fill-current" />
          <span>Trigger Reasoning</span>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onSelect?.(data);
          }}
          className="px-2.5 py-1 rounded-lg bg-[#f2f3ff] text-[#4648d4] hover:bg-[#eaedff] font-bold flex items-center gap-1 transition-colors"
        >
          <span>Inspect Memory</span>
          <ChevronRight className="w-3 h-3" />
        </button>
      </NodeToolbar>

      {/* Connection Handles */}
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white shadow-2xs" />
      <Handle type="source" position={Position.Right} className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-2xs" />
      <Handle type="target" position={Position.Top} id="top" className="w-2.5 h-2.5 !bg-[#006577] !border-2 !border-white" />
      <Handle type="source" position={Position.Bottom} id="bottom" className="w-2.5 h-2.5 !bg-[#10b981] !border-2 !border-white" />

      {/* 1. Header: Icon Avatar, Role Name, Cognitive Tier, State Pill */}
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs transition-transform duration-200 group-hover:scale-105 ${
              isFriday
                ? 'bg-[#4648d4] text-white shadow-sm shadow-[#4648d4]/30'
                : isAlarm
                ? 'bg-[#f43f5e]/15 text-[#e11d48]'
                : 'bg-[#f2f3ff] text-[#4648d4]'
            }`}
          >
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
                {data.name || role}
              </span>
            </div>
            <span className="text-[9px] font-mono font-semibold text-[#73738c] tracking-wider uppercase block">
              {theme.badge} • TIER {isFriday ? '0' : '1'}
            </span>
          </div>
        </div>

        {/* State Pill */}
        <span
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold inline-flex items-center gap-1 ${
            isDeliberating
              ? 'bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0] animate-pulse'
              : isAlarm
              ? 'bg-[#fff1f2] text-[#e11d48] border border-[#f43f5e]/30'
              : 'bg-[#faf8ff] border border-[#eaedff] text-[#4648d4]'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isDeliberating ? 'bg-[#10b981] animate-ping' : isAlarm ? 'bg-[#e11d48]' : 'bg-[#4648d4]'
            }`}
          />
          {state}
        </span>
      </div>

      {/* 2. Visual Core: Radial Confidence Gauge & Live Activity Waveform */}
      <div className="flex items-center justify-between p-2 rounded-xl bg-[#faf8ff] border border-[#eaedff]/70 my-2">
        <div className="flex items-center gap-2">
          <ConfidenceRadialGauge pct={confidence} color={isAlarm ? '#f43f5e' : '#10b981'} size={36} />
          <div>
            <span className="text-[8px] font-mono text-[#73738c] uppercase block font-semibold">Certainty</span>
            <span className="text-[11px] font-mono font-bold text-[#131b2e]">
              {confidence >= 95 ? 'High Anchor' : 'Evaluating'}
            </span>
          </div>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[8px] font-mono text-[#73738c] uppercase font-semibold">Pulse Wave</span>
          {renderMiniWaveform(waveformPoints, waveformColor, 18, 68)}
        </div>
      </div>

      {/* 3. Single-Line Glanceable Insight Pill (Minimal Text) */}
      <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-white border border-[#eaebf0] text-[10px] font-mono text-[#464554] truncate">
        {isAlarm ? (
          <ShieldAlert className="w-3 h-3 text-[#e11d48] shrink-0" />
        ) : isDeliberating ? (
          <Sparkles className="w-3 h-3 text-[#d97706] shrink-0 animate-spin" />
        ) : (
          <CheckCircle2 className="w-3 h-3 text-[#10b981] shrink-0" />
        )}
        <span className="truncate">{insightText}</span>
      </div>

      {/* 4. Sleek Interactive Hover Indicator */}
      <div className="mt-2 pt-1.5 border-t border-[#eaebf0]/50 flex items-center justify-between text-[9px] font-mono text-[#73738c]">
        <span className="flex items-center gap-1">
          <Sparkles className="w-2.5 h-2.5 text-[#4648d4]" />
          LPU 280 tok/s
        </span>
        <span className="text-[#4648d4] font-semibold group-hover:underline flex items-center gap-0.5">
          Inspect <ChevronRight className="w-2.5 h-2.5" />
        </span>
      </div>
    </div>
  );
};

// ========================================================
// 3. ACTION FLOW NODE (Live Actuation & Defense Interlock)
// ========================================================
export const ActionFlowNode: React.FC<{ data: any }> = ({ data }) => {
  const isExecuted = data.status === 'EXECUTED';
  const isSupervised = data.tier === 'TIER_2';
  const isCommander = data.tier === 'TIER_3';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[240px] max-w-[260px] shadow-xs select-none ${
        isExecuted
          ? 'border-[#10b981] bg-[#ecfdf5]/40 ring-2 ring-[#10b981]/20'
          : 'border-[#eaebf0] hover:border-[#10b981]/50 hover:shadow-sm'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#10b981] !border-2 !border-white shadow-2xs" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#10b981] !border-2 !border-white shadow-2xs" />

      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase tracking-wider ${
            isCommander
              ? 'bg-[#fff1f2] text-[#e11d48] border border-[#f43f5e]/30'
              : isSupervised
              ? 'bg-[#fffbeb] text-[#d97706] border border-[#f59e0b]/30'
              : 'bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0]'
          }`}
        >
          {data.tierLabel || 'Tier 1 Autonomous'}
        </span>

        <span className="text-[9px] font-mono font-bold text-[#006c49] flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3 text-[#10b981]" />
          {data.status || 'READY'}
        </span>
      </div>

      <div className="font-display font-bold text-xs text-[#131b2e] leading-snug">
        {data.label}
      </div>

      <div className="text-[10px] text-[#73738c] font-mono mt-1">
        Target: <strong className="text-[#131b2e]">{data.targetSystem}</strong>
      </div>

      <div className="mt-2 pt-2 border-t border-[#eaebf0] flex items-center justify-between text-[9px] font-mono">
        <span className="text-[#73738c]">Fast: {data.latency || '<1.2s'}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onExecute?.(data.id);
          }}
          className="px-2.5 py-0.5 rounded-md bg-[#10b981] text-white hover:bg-[#059669] font-bold text-[9px] transition-colors shadow-2xs"
        >
          Execute
        </button>
      </div>
    </div>
  );
};

// ========================================================
// 4. NEURAL BUS HUB NODE (Message Bus Backbone)
// ========================================================
export const NeuralBusNode: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div className="px-5 py-3 rounded-2xl bg-white border border-[#4648d4]/30 shadow-md flex items-center justify-between gap-6 min-w-[300px] select-none">
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />

      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-[#4648d4] text-white flex items-center justify-center font-bold">
          <Radio className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <span className="font-display font-black text-sm text-[#131b2e] block leading-tight">
            Cognitive Neural Bus
          </span>
          <span className="text-[10px] font-mono text-[#4648d4] font-semibold">
            Zero-Copy IPC • Typed
          </span>
        </div>
      </div>

      <div className="text-right font-mono text-xs">
        <div className="font-bold text-[#006c49]">
          {data.totalMessages || 640} Msg
        </div>
        <div className="text-[10px] text-[#73738c]">
          {data.activeSessions || 1} Active Session
        </div>
      </div>
    </div>
  );
};

export const customAgentNodeTypes = {
  clusterZoneNode: ClusterZoneNode,
  agentProNode: AgentProNode,
  actionFlowNode: ActionFlowNode,
  neuralBusNode: NeuralBusNode,
};
