import React from 'react';
import { Handle, Position } from '@xyflow/react';
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
  Cpu
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

// 1. POWER SOURCE NODE (Generators, Solar, BESS, Wind)
export const PowerSourceNode: React.FC<{ data: any }> = ({ data }) => {
  const Icon = iconMap[data.iconType] || Zap;
  const isTripped = data.status === 'TRIPPED';
  const isStandby = data.status === 'STANDBY';
  const isSurge = data.status === 'SURGE';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[220px] shadow-xs select-none ${
        isTripped
          ? 'border-[#f43f5e] ring-3 ring-[#f43f5e]/25 bg-[#fff1f2] shadow-md shadow-[#f43f5e]/10'
          : isStandby
          ? 'border-[#eaebf0] hover:border-[#c7c4d7] bg-white/90'
          : data.isSelected
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-sm'
      }`}
    >
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#73738c] !border-2 !border-white" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
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
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold ${
            isTripped
              ? 'bg-[#fff1f2] text-[#e11d48] border border-[#f43f5e]/30'
              : isStandby
              ? 'bg-[#f4f4f5] text-[#71717a]'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          {data.status || 'ONLINE'}
        </span>
      </div>

      <div className="flex items-baseline justify-between mt-2 pt-2 border-t border-[#eaebf0]/70">
        <span className={`font-mono font-black text-lg ${isTripped ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
          {data.value}
        </span>
        <span className="text-xs font-mono font-semibold text-[#4648d4]">
          {data.metricUnit || 'kW'}
        </span>
      </div>
    </div>
  );
};

// 2. MAIN SWITCHBOARD BUS NODE (400V 50Hz MLVD Bus)
export const BusNode: React.FC<{ data: any }> = ({ data }) => {
  const isRecovering = data.status === 'RECOVERING';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-5 py-4 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[260px] shadow-sm select-none ${
        isRecovering
          ? 'border-[#f59e0b] ring-3 ring-[#f59e0b]/25 bg-[#fffbeb]'
          : data.isSelected
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md'
          : 'border-[#4648d4] hover:shadow-md'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="target" position={Position.Bottom} id="bottom" className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />

      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shadow-xs font-bold text-xs">
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
          className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
            isRecovering
              ? 'bg-[#fffbeb] text-[#d97706] border border-[#f59e0b]/30'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          {data.status || 'SYNCHRONIZED'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-3 pt-2 border-t border-[#eaebf0]">
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
    </div>
  );
};

// 3. CONSUMER LOAD NODE (HVAC, Utilidor, Science)
export const ConsumerNode: React.FC<{ data: any }> = ({ data }) => {
  const Icon = iconMap[data.iconType] || Droplet;
  const isAlert = data.status === 'ALERT';
  const isSealed = data.status === 'SEALED';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[220px] shadow-xs select-none ${
        isAlert
          ? 'border-[#06b6d4] ring-3 ring-[#06b6d4]/25 bg-[#ecfeff]'
          : data.isSelected
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-sm'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-[#006577] !border-2 !border-white" />

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
          className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold ${
            isAlert
              ? 'bg-[#ecfeff] text-[#0891b2] border border-[#06b6d4]/30'
              : isSealed
              ? 'bg-[#f0f9ff] text-[#0284c7]'
              : 'bg-[#ecfdf5] text-[#006c49]'
          }`}
        >
          {data.status || 'OPTIMAL'}
        </span>
      </div>

      <div className="flex items-baseline justify-between mt-2 pt-2 border-t border-[#eaebf0]/70">
        <span className="font-mono font-black text-lg text-[#131b2e]">
          {data.value}
        </span>
        <span className="text-xs font-mono font-semibold text-[#006577]">
          {data.secondary}
        </span>
      </div>
    </div>
  );
};

// 4. COGNITIVE AGENT NODE (Situation Awareness, Causal Diagnostic, Sandbox, Friday)
export const AgentNode: React.FC<{ data: any }> = ({ data }) => {
  const isFriday = data.id === 'agent_friday';

  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className={`relative px-4 py-3.5 rounded-2xl bg-white border text-left cursor-pointer transition-all duration-200 min-w-[230px] shadow-xs select-none ${
        isFriday
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md bg-gradient-to-br from-white to-[#f2f3ff]'
          : data.isSelected
          ? 'border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-md'
          : 'border-[#eaebf0] hover:border-[#4648d4]/40 hover:shadow-sm'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-2.5 h-2.5 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 !bg-[#4648d4] !border-2 !border-white" />
      <Handle type="source" position={Position.Top} id="top" className="w-2.5 h-2.5 !bg-[#4648d4] !border-2 !border-white" />

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

      <div className="flex items-center justify-between mt-2 pt-1 text-[10px] font-mono text-[#73738c]">
        <span>Confidence</span>
        <span className="font-bold text-[#006c49]">{data.confidence || '99.4%'}</span>
      </div>
    </div>
  );
};

// 5. GATEWAY & SATCOM NODE (NCPOR Goa, Interlocks)
export const GatewayNode: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div
      onClick={() => data.onSelect?.(data)}
      className="relative px-4 py-3.5 rounded-2xl bg-white border border-[#eaebf0] hover:border-[#4648d4]/50 text-left cursor-pointer transition-all duration-200 min-w-[210px] shadow-xs select-none"
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-[#006577] !border-2 !border-white" />

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
          90% Delta Saved
        </span>
      </div>
    </div>
  );
};

export const customNodeTypes = {
  powerNode: PowerSourceNode,
  busNode: BusNode,
  consumerNode: ConsumerNode,
  agentNode: AgentNode,
  gatewayNode: GatewayNode,
};
