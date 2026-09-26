import React from 'react';
import { Handle, Position, NodeToolbar } from '@xyflow/react';
import { 
  Zap, 
  Flame, 
  Sun, 
  BatteryCharging, 
  Wind, 
  Thermometer, 
  Droplet, 
  Microscope, 
  Brain, 
  ShieldCheck, 
  Radio, 
  AlertTriangle,
  CheckCircle2,
  Lock,
  Cpu,
  Activity,
  Sliders,
  Play,
  RotateCcw,
  Sparkles,
  Info
} from 'lucide-react';

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  generator: Flame,
  solar: Sun,
  battery: BatteryCharging,
  wind: Wind,
  bus: Zap,
  hvac: Thermometer,
  utilidor: Droplet,
  lab: Microscope,
  agent: Brain,
  interlock: ShieldCheck,
  satcom: Radio,
};

// Mini SVG Sparkline generator for live telemetry waveforms inside nodes
const renderMiniSparkline = (points: number[], strokeColor: string, height = 22, width = 90) => {
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
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Active pulse endpoint */}
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

// 0. ARCHITECTURAL CLUSTER GROUP NODE (Compound Area Container)
export const ClusterGroupNode: React.FC<{ data: any }> = ({ data }) => {
  const isAlarm = data.status === 'ALARM' || data.status === 'TRIPPED';
  return (
    <div
      className={`w-full h-full rounded-3xl border-2 transition-all duration-300 p-5 flex flex-col justify-between pointer-events-none select-none ${
        isAlarm
          ? 'bg-[#fff1f2]/30 border-[#f43f5e]/30'
          : 'bg-[#f8fafc]/40 border-[#eaebf0]/80'
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
        <span>{data.description || 'System Sub-array'}</span>
        <span className="inline-flex items-center gap-1 font-bold text-[#006c49]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
          ACTIVE
        </span>
      </div>
    </div>
  );
};

// 1. POWER SOURCE NODE (Generators, Solar, BESS, Wind Turbines)
export const PowerSourceNode: React.FC<{ data: any }> = ({ data }) => {
  const Icon = iconMap[data.iconType] || Zap;
  const isTripped = data.status === 'TRIPPED';
  const isStandby = data.status === 'STANDBY';
  const isSurge = data.status === 'SURGE';
  const isSelected = data.isSelected;

  const sparklineData = data.history || (isTripped ? [75, 74, 50, 20, 0, 0] : isStandby ? [0, 0, 0, 0] : [72, 75, 74, 76, 75, 75.4]);
  const sparklineColor = isTripped ? '#e11d48' : isSurge ? '#006577' : '#4648d4';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[240px] shadow-xs select-none ${
        isTripped
          ? 'border-[#f43f5e] ring-4 ring-[#f43f5e]/20 bg-[#fff1f2] shadow-lg shadow-[#f43f5e]/10'
          : isStandby
          ? 'border-[#eaebf0] hover:border-[#c7c4d7] bg-white/95'
          : isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-sm'
      }`}
    >
      {/* Floating Action Toolbar on Selected Node */}
      <NodeToolbar isVisible={isSelected} position={Position.Top} offset={10} className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('toggle_state', data);
          }}
          className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold flex items-center gap-1 transition-colors ${
            isTripped ? 'bg-[#ecfdf5] text-[#006c49] hover:bg-[#d1fae5]' : 'bg-[#fff1f2] text-[#e11d48] hover:bg-[#ffe4e6]'
          }`}
        >
          {isTripped ? <RotateCcw className="w-3 h-3" /> : <Flame className="w-3 h-3" />}
          <span>{isTripped ? 'Reset Breaker' : 'Trip Breaker'}</span>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onSelect?.(data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#f2f3ff] text-[#4648d4] hover:bg-[#eaedff] flex items-center gap-1"
        >
          <Sliders className="w-3 h-3" />
          <span>Inspect Registers</span>
        </button>
      </NodeToolbar>

      <Handle type="source" position={Position.Right} className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-xs" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#73738c] !border-2 !border-white" />

      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs transition-colors ${
              isTripped
                ? 'bg-[#f43f5e]/15 text-[#e11d48]'
                : isStandby
                ? 'bg-[#f4f4f5] text-[#71717a]'
                : isSurge
                ? 'bg-[#006577]/15 text-[#006577]'
                : 'bg-[#f2f3ff] text-[#4648d4]'
            }`}
          >
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
              {data.label}
            </span>
            <span className="text-[10px] font-mono text-[#73738c]">
              {data.subsystem || 'Asset Point'}
            </span>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold inline-flex items-center gap-1 ${
            isTripped
              ? 'bg-[#fff1f2] text-[#e11d48] border border-[#f43f5e]/30 animate-pulse'
              : isStandby
              ? 'bg-[#f4f4f5] text-[#71717a]'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isTripped ? 'bg-[#e11d48]' : isStandby ? 'bg-[#a1a1aa]' : 'bg-[#10b981] animate-pulse'
            }`}
          />
          {data.status || 'ONLINE'}
        </span>
      </div>

      {/* Sparkline & Real-time Value */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#eaebf0]/70">
        <div>
          <span className="text-[9px] font-mono text-[#73738c] uppercase block">Output Power</span>
          <div className="flex items-baseline gap-1">
            <span className={`font-mono font-black text-lg ${isTripped ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
              {data.value}
            </span>
            <span className="text-xs font-mono font-semibold text-[#4648d4]">
              {data.metricUnit || 'kW'}
            </span>
          </div>
        </div>

        {/* Real-time Inline Waveform */}
        <div className="flex flex-col items-end">
          <span className="text-[8px] font-mono text-[#73738c] uppercase">Telemetry Wave</span>
          {renderMiniSparkline(sparklineData, sparklineColor, 20, 75)}
        </div>
      </div>

      {/* Load percentage progress bar */}
      {data.capacityPercent !== undefined && (
        <div className="mt-2 w-full bg-[#f4f4f5] rounded-full h-1.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              isTripped ? 'bg-[#e11d48]' : 'bg-[#4648d4]'
            }`}
            style={{ width: `${Math.min(Math.max(data.capacityPercent, 0), 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};

// 2. MAIN SWITCHBOARD BUS NODE (400V 50Hz MLVD Bus)
export const BusNode: React.FC<{ data: any }> = ({ data }) => {
  const isRecovering = data.status === 'RECOVERING';
  const isSelected = data.isSelected;
  const freqPoints = data.freqHistory || (isRecovering ? [50.00, 49.98, 49.70, 49.55, 49.80] : [50.01, 50.00, 49.99, 50.01, 50.00]);

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-5 py-4 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[280px] shadow-sm select-none ${
        isRecovering
          ? 'border-[#f59e0b] ring-4 ring-[#f59e0b]/25 bg-[#fffbeb] shadow-lg'
          : isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#4648d4] hover:shadow-md'
      }`}
    >
      <NodeToolbar isVisible={isSelected} position={Position.Top} offset={10} className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('harmonic_scan', data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#f2f3ff] text-[#4648d4] hover:bg-[#eaedff] flex items-center gap-1"
        >
          <Activity className="w-3 h-3" />
          <span>Harmonic Scan</span>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onSelect?.(data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-white text-[#131b2e] border border-[#eaebf0] hover:bg-[#faf8ff] flex items-center gap-1"
        >
          <Sliders className="w-3 h-3" />
          <span>Bus Health</span>
        </button>
      </NodeToolbar>

      <Handle type="target" position={Position.Left} className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-xs" />
      <Handle type="source" position={Position.Right} className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-xs" />
      <Handle type="target" position={Position.Bottom} id="bottom" className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-xs" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shadow-xs font-bold text-xs">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-display font-bold text-sm text-[#131b2e] block leading-tight">
              {data.label}
            </span>
            <span className="text-[10px] font-mono text-[#4648d4] font-semibold">
              3-Phase 400V AC Bus
            </span>
          </div>
        </div>

        <span
          className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold inline-flex items-center gap-1.5 ${
            isRecovering
              ? 'bg-[#fffbeb] text-[#d97706] border border-[#f59e0b]/30 animate-pulse'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${isRecovering ? 'bg-[#d97706]' : 'bg-[#10b981]'}`} />
          {data.status || 'SYNCHRONIZED'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3 pt-2.5 border-t border-[#eaebf0]">
        <div>
          <span className="text-[10px] text-[#73738c] font-medium block">Total Demand</span>
          <span className="font-mono font-extrabold text-base text-[#131b2e]">
            {data.loadKw} kW
          </span>
        </div>
        <div>
          <span className="text-[10px] text-[#73738c] font-medium block">Grid Frequency</span>
          <span className={`font-mono font-extrabold text-base ${isRecovering ? 'text-[#d97706]' : 'text-[#006c49]'}`}>
            {data.frequencyHz || '50.00'} Hz
          </span>
        </div>
      </div>

      {/* Frequency Oscilloscope Wave */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#eaebf0]/60">
        <span className="text-[9px] font-mono text-[#73738c]">50Hz PLL Lock</span>
        {renderMiniSparkline(freqPoints, isRecovering ? '#d97706' : '#10b981', 18, 90)}
      </div>
    </div>
  );
};

// 3. CONSUMER LOAD NODE (HVAC, Utilidor, Science)
export const ConsumerNode: React.FC<{ data: any }> = ({ data }) => {
  const Icon = iconMap[data.iconType] || Droplet;
  const isAlert = data.status === 'ALERT';
  const isSealed = data.status === 'SEALED';
  const isSelected = data.isSelected;

  const points = data.history || (isAlert ? [4.8, 3.2, 2.0, 1.2] : [20.0, 20.2, 20.1, 20.2]);
  const sparkColor = isAlert ? '#0891b2' : '#006577';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[240px] shadow-xs select-none ${
        isAlert
          ? 'border-[#06b6d4] ring-4 ring-[#06b6d4]/25 bg-[#ecfeff] shadow-md'
          : isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-sm'
      }`}
    >
      <NodeToolbar isVisible={isSelected} position={Position.Top} offset={10} className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('boost_action', data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#ecfeff] text-[#0891b2] hover:bg-[#cffafe] flex items-center gap-1"
        >
          <Sparkles className="w-3 h-3" />
          <span>Trace Heat Boost</span>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onSelect?.(data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#f2f3ff] text-[#4648d4] hover:bg-[#eaedff]"
        >
          Inspect
        </button>
      </NodeToolbar>

      <Handle type="target" position={Position.Left} className="w-3.5 h-3.5 !bg-[#4648d4] !border-2 !border-white shadow-xs" />
      <Handle type="source" position={Position.Right} className="w-3.5 h-3.5 !bg-[#006577] !border-2 !border-white shadow-xs" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold text-xs">
            <Icon className="w-4 h-4" />
          </div>
          <div>
            <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
              {data.label}
            </span>
            <span className="text-[10px] font-mono text-[#73738c]">
              {data.subsystem || 'Life Support'}
            </span>
          </div>
        </div>

        <span
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold inline-flex items-center gap-1 ${
            isAlert
              ? 'bg-[#ecfeff] text-[#0891b2] border border-[#06b6d4]/30 animate-pulse'
              : isSealed
              ? 'bg-[#f0f9ff] text-[#0284c7]'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              isAlert ? 'bg-[#06b6d4] animate-ping' : isSealed ? 'bg-[#0284c7]' : 'bg-[#10b981]'
            }`}
          />
          {data.status || 'OPTIMAL'}
        </span>
      </div>

      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#eaebf0]/70">
        <div>
          <span className="font-mono font-black text-lg text-[#131b2e]">
            {data.value}
          </span>
          <span className="text-[10px] font-mono font-semibold text-[#006577] block">
            {data.secondary}
          </span>
        </div>

        <div className="flex flex-col items-end">
          <span className="text-[8px] font-mono text-[#73738c] uppercase">Loop Trend</span>
          {renderMiniSparkline(points, sparkColor, 18, 75)}
        </div>
      </div>
    </div>
  );
};

// 4. COGNITIVE AGENT NODE (Situation Awareness, Causal Diagnostic, Sandbox, Friday)
export const AgentNode: React.FC<{ data: any }> = ({ data }) => {
  const isFriday = data.id === 'agent_friday';
  const isSelected = data.isSelected;

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[240px] shadow-xs select-none ${
        isFriday
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/25 shadow-md bg-gradient-to-br from-white to-[#f2f3ff]'
          : isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/40 hover:shadow-sm'
      }`}
    >
      <NodeToolbar isVisible={isSelected} position={Position.Top} offset={10} className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('deliberate', data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#faf8ff] text-[#4648d4] border border-[#eaedff] hover:bg-[#f2f3ff] flex items-center gap-1"
        >
          <Brain className="w-3 h-3 text-[#4648d4]" />
          <span>Deliberate</span>
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onSelect?.(data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-white text-[#131b2e] border border-[#eaebf0] hover:bg-[#faf8ff]"
        >
          Inspect
        </button>
      </NodeToolbar>

      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Top} id="top" className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
              isFriday ? 'bg-[#4648d4] text-white shadow-xs' : 'bg-[#e1e0ff] text-[#07006c]'
            }`}
          >
            {isFriday ? <ShieldCheck className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
          </div>
          <div>
            <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
              {data.label}
            </span>
            <span className="text-[10px] font-mono text-[#4648d4] font-semibold">
              {data.role || 'Autonomous Cognitive'}
            </span>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#faf8ff] text-[#4648d4] border border-[#eaedff]">
          {data.latency || '<40ms'}
        </span>
      </div>

      <div className="text-[11px] text-[#464554] font-mono line-clamp-2 mt-2 pt-2 border-t border-[#eaebf0]/70">
        <strong className="text-[#006c49]">Hypothesis: </strong>
        {data.hypothesis || 'All sensor streams nominal.'}
      </div>

      <div className="flex items-center justify-between mt-2 pt-1.5 text-[10px] font-mono text-[#73738c]">
        <span>Consensus Confidence</span>
        <span className="font-bold text-[#006c49]">{data.confidence || '99.4%'}</span>
      </div>
    </div>
  );
};

// 5. GATEWAY & SATCOM NODE (NCPOR Goa, Interlocks)
export const GatewayNode: React.FC<{ data: any }> = ({ data }) => {
  const isSelected = data.isSelected;

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[220px] shadow-xs select-none ${
        isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50'
      }`}
    >
      <NodeToolbar isVisible={isSelected} position={Position.Top} className="flex items-center gap-1 p-1 rounded-xl bg-white/95 backdrop-blur-md border border-[#eaebf0] shadow-md z-30">
        <button
          onClick={(e) => {
            e.stopPropagation();
            data.onQuickAction?.('ping_satcom', data);
          }}
          className="px-2 py-1 rounded-lg text-[10px] font-mono font-bold bg-[#ecfeff] text-[#006577] hover:bg-[#cffafe] flex items-center gap-1"
        >
          <Radio className="w-3 h-3" />
          <span>Ping Satcom</span>
        </button>
      </NodeToolbar>

      <Handle type="target" position={Position.Left} className="w-3.5 h-3.5 !bg-[#006577] !border-2 !border-white shadow-xs" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold text-xs">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
              {data.label}
            </span>
            <span className="text-[10px] font-mono text-[#006577] font-semibold">
              Polar Satcom Link
            </span>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#ecfdf5] text-[#006c49]">
          SYNC
        </span>
      </div>

      <div className="flex items-baseline justify-between mt-2 pt-2 border-t border-[#eaebf0]/70">
        <span className="font-mono font-bold text-sm text-[#131b2e]">
          {data.latency || '640ms'}
        </span>
        <span className="text-[10px] font-mono text-[#006c49] font-bold">
          {data.deltaSaved || '90% Delta Saved'}
        </span>
      </div>
    </div>
  );
};

// 6. SAFETY INTERLOCK GOVERNOR NODE (Tier 1/2/3 Hardware Protections)
export const InterlockNode: React.FC<{ data: any }> = ({ data }) => {
  const isSelected = data.isSelected;

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[210px] shadow-xs select-none ${
        isSelected
          ? 'border-[#4648d4] ring-3 ring-[#4648d4]/25 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/40'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#10b981] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#10b981] !border-2 !border-white" />

      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#ecfdf5] text-[#006c49] flex items-center justify-center font-bold text-xs">
            <Lock className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-display font-bold text-xs text-[#131b2e] leading-tight block">
              {data.label}
            </span>
            <span className="text-[9px] font-mono text-[#006c49] font-semibold">
              {data.tier || 'Tier 1 Autonomous'}
            </span>
          </div>
        </div>

        <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-[#ecfdf5] text-[#006c49]">
          ARMED
        </span>
      </div>

      <div className="text-[10px] font-mono text-[#464554] mt-1.5 pt-1.5 border-t border-[#eaebf0]/70 flex items-center justify-between">
        <span>Hardware Limit</span>
        <span className="font-bold text-[#131b2e]">&lt; 1.20s Relay</span>
      </div>
    </div>
  );
};

export const customNodeTypes = {
  clusterNode: ClusterGroupNode,
  powerNode: PowerSourceNode,
  busNode: BusNode,
  consumerNode: ConsumerNode,
  agentNode: AgentNode,
  gatewayNode: GatewayNode,
  interlockNode: InterlockNode,
};
