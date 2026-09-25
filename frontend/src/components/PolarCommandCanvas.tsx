import React from 'react';
import { 
  Zap, 
  Brain, 
  HeartPulse, 
  Radio, 
  CheckCircle2, 
  ShieldCheck, 
  AlertTriangle,
  TrendingUp,
  Flame,
  Droplet,
  Compass,
  Cpu
} from 'lucide-react';
import { StationKPIs } from '../types';

interface PolarCommandCanvasProps {
  kpis: StationKPIs | null;
  activeCrisis: string | null;
  isResolved: boolean;
}

export const PolarCommandCanvas: React.FC<PolarCommandCanvasProps> = ({
  kpis,
  activeCrisis,
  isResolved,
}) => {
  const isChp1Tripped = activeCrisis === 'GENERATOR_TRIP' && !isResolved;
  const isBlizzard = activeCrisis === 'BLIZZARD_STRIKE';
  const isFreeze = activeCrisis === 'WATER_LINE_FREEZE';

  return (
    <div id="canvas" className="w-full max-w-6xl mx-auto rounded-2xl bg-white border border-[#eaebf0] shadow-2xl p-4 sm:p-6 lg:p-8 relative">
      {/* Top Floating Badge */}
      <div className="absolute -top-3 left-8 px-3.5 py-1 bg-[#4648d4] text-white rounded-full text-xs font-semibold uppercase tracking-wider shadow-md flex items-center gap-1.5">
        <Cpu className="w-3.5 h-3.5" />
        <span>Live Polar Digital Twin Canvas</span>
      </div>

      {/* Mockup Window Chrome Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 pt-2 border-b border-[#eaebf0] gap-4">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#f43f5e] inline-block" />
            <span className="w-3 h-3 rounded-full bg-[#f59e0b] inline-block" />
            <span className="w-3 h-3 rounded-full bg-[#10b981] inline-block" />
          </div>
          <div className="h-4 w-px bg-[#eaebf0] hidden sm:block" />
          <div className="flex items-center gap-2">
            <span className="font-display font-bold text-base text-[#131b2e]">
              Bharati Research Station
            </span>
            <span className="text-[#464554] text-xs font-mono">
              — 69°24'28"S, 76°11'14"E (T+124s)
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-[#10b981]/10 text-[#006c49] text-xs font-semibold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            Live Sync: 505 Sensors
          </span>
          <span className="px-3 py-1 rounded-full bg-[#eaedff] text-[#4648d4] text-xs font-semibold flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5" />
            Satcom 640ms Delta Mode
          </span>
        </div>
      </div>

      {/* 3-Column Grid Content (12 Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
        
        {/* Left: Microgrid & Energy Flow Matrix (4 cols) */}
        <div className="lg:col-span-4 bg-[#f2f3ff] rounded-xl p-5 flex flex-col justify-between border border-[#eaebf0]/60">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#006577]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">
                  Microgrid & Power Matrix
                </h3>
              </div>
              <span className="text-[11px] font-semibold text-[#006577] bg-[#acedff]/60 px-2 py-0.5 rounded-full">
                400V 50Hz Bus
              </span>
            </div>
            <p className="text-xs text-[#464554] mb-4">
              Real-time generation and load balance across energy assets.
            </p>

            {/* Row 1: Generator CHP-01 */}
            <div className={`p-3 mb-2.5 rounded-lg bg-white shadow-sm border transition-all ${
              isChp1Tripped ? 'border-[#f43f5e] bg-[#ffdad6]/20' : 'border-[#eaebf0]'
            }`}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-bold text-xs">
                    G1
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">CHP-01 (Diesel)</p>
                    <p className="text-[10px] text-[#464554]">Baseload Microgrid</p>
                  </div>
                </div>
                <span className={`text-xs font-mono font-bold ${isChp1Tripped ? 'text-[#ba1a1a]' : 'text-[#4648d4]'}`}>
                  {isChp1Tripped ? '0.0 kW (TRIPPED)' : '75.0 kW'}
                </span>
              </div>
              <div className="w-full bg-[#eaedff] h-1.5 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${
                  isChp1Tripped ? 'bg-[#ba1a1a] w-0' : 'bg-[#10b981] w-full'
                }`} />
              </div>
            </div>

            {/* Row 2: Generator CHP-02 (Standby) */}
            <div className="p-3 mb-2.5 rounded-lg bg-white shadow-sm border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold text-xs">
                    G2
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">CHP-02 (Standby)</p>
                    <p className="text-[10px] text-[#464554]">Auto-Transfer Armed</p>
                  </div>
                </div>
                <span className={`text-xs font-mono font-bold ${
                  isResolved || !isChp1Tripped ? 'text-[#006c49]' : 'text-[#464554]'
                }`}>
                  {isResolved ? '65.0 kW (ONLINE)' : 'Standby (0 kW)'}
                </span>
              </div>
              <div className="w-full bg-[#eaedff] h-1.5 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${
                  isResolved ? 'bg-[#10b981] w-4/5' : 'bg-[#767586] w-1/4'
                }`} />
              </div>
            </div>

            {/* Row 3: Solar PV Array */}
            <div className="p-3 mb-2.5 rounded-lg bg-white shadow-sm border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-[#f59e0b]/10 text-[#f59e0b] flex items-center justify-center font-bold text-xs">
                    PV
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">Bifacial Solar Array</p>
                    <p className="text-[10px] text-[#464554]">Polar Latitude 65°</p>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-[#4648d4]">12.4 kW</span>
              </div>
              <div className="w-full bg-[#eaedff] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#4648d4] h-full rounded-full w-2/5" />
              </div>
            </div>

            {/* Row 4: BESS Battery Storage */}
            <div className="p-3 rounded-lg bg-white shadow-sm border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-[#10b981]/10 text-[#006c49] flex items-center justify-center font-bold text-xs">
                    BT
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">BESS Lithium Bank</p>
                    <p className="text-[10px] text-[#464554]">100 kWh Peak Reserve</p>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-[#006c49]">92% SOC</span>
              </div>
              <div className="w-full bg-[#eaedff] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#10b981] h-full rounded-full w-[92%]" />
              </div>
            </div>
          </div>

          {/* Reserve Margin Banner */}
          <div className="mt-4 p-3 rounded-lg bg-[#eaedff] flex items-center justify-between border border-[#c7c4d7]/40">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#006577]" />
              <div>
                <p className="text-xs font-bold text-[#131b2e]">Reserve Margin: +16.6 kW</p>
                <p className="text-[10px] text-[#464554]">50.00 Hz Microgrid Frequency Nominal</p>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#6cf8bb] text-[#002113] text-[10px] font-bold">
              Optimal
            </span>
          </div>
        </div>

        {/* Center: Autonomous Deliberation & Actuation Stream (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl p-5 flex flex-col border border-[#eaebf0] shadow-sm justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[#4648d4]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">
                  Autonomous Deliberation Stream
                </h3>
              </div>
              <span className="text-[10px] font-semibold bg-[#e1e0ff] text-[#07006c] px-2.5 py-0.5 rounded-full">
                10 Agents Active
              </span>
            </div>

            {/* Deliberation Cards Handover */}
            <div className="space-y-3 mt-4">
              {/* Card 1: Situation Awareness */}
              <div className="p-3.5 rounded-lg bg-[#f2f3ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-[#4648d4] text-white flex items-center justify-center font-bold text-[10px]">
                      SA
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Situation Awareness Agent</span>
                  </div>
                  <span className="text-[10px] text-[#464554]">T+0.04s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#4648d4] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006c49]">Perception:</strong> {
                      activeCrisis === 'GENERATOR_TRIP'
                        ? 'CHP-01 breaker trip detected on MLVD 400V bus. Frequency dip -0.45 Hz.'
                        : isBlizzard
                        ? 'Katabatic blizzard wind surge: 34.2 m/s. High infiltration hazard.'
                        : isFreeze
                        ? 'Utilidor water pipeline temperature dropping: +1.2°C approaching freeze.'
                        : 'All 505 sensors continuous scan nominal. Zero threshold breaches.'
                    }
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px]">
                  <span className="text-[#464554]">Inference Speed:</span>
                  <span className="text-[#006c49] bg-[#6cf8bb]/30 px-2 py-0.5 rounded-full font-semibold">
                    ⚡ 38ms (Groq LPU)
                  </span>
                </div>
              </div>

              {/* Card 2: Diagnostic & Causal DAG */}
              <div className="p-3.5 rounded-lg bg-[#f2f3ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-[#006577] text-white flex items-center justify-center font-bold text-[10px]">
                      DG
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Diagnostic Causal Agent</span>
                  </div>
                  <span className="text-[10px] text-[#464554]">T+0.22s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#006577] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006577]">Causal Root Cause:</strong> {
                      activeCrisis === 'GENERATOR_TRIP'
                        ? 'Isolated to primary alternator trip. Recommended: Start standby CHP-02.'
                        : isBlizzard
                        ? 'Isolated to fresh air dampers. Recommended: Seal AHU fresh air to 0%.'
                        : isFreeze
                        ? 'Utilidor freeze imminent in 8.4m. Recommended: Energize trace heating.'
                        : '35-Node Causal Graph traversed. Zero cascading failure risk.'
                    }
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px]">
                  <span className="text-[#464554]">Confidence:</span>
                  <span className="text-[#4648d4] bg-[#e1e0ff] px-2 py-0.5 rounded-full font-semibold">
                    ✨ 99.4% (Zero Hallucination)
                  </span>
                </div>
              </div>

              {/* Card 3: Friday Master Orchestrator */}
              <div className="p-3.5 rounded-lg bg-[#f2f3ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-[#10b981] text-white flex items-center justify-center font-bold text-[10px]">
                      FR
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Friday Chief Orchestrator</span>
                  </div>
                  <span className="text-[10px] text-[#464554]">T+1.20s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#10b981] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006c49]">Consensus Actuation:</strong> {
                      activeCrisis
                        ? 'What-If sandbox validated safe. Physical digital twin overrides applied. Life-support secured.'
                        : 'Consensus plan active: Operating in Tier 1 Autonomous Governor mode.'
                    }
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px]">
                  <span className="text-[#464554]">Actuation Result:</span>
                  <span className="text-[#006c49] bg-[#6cf8bb]/40 px-2 py-0.5 rounded-full font-bold">
                    🛡️ EXECUTED ON DIGITAL TWIN
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Life-Support Health & Envelope Gauge (3 cols) */}
        <div className="lg:col-span-3 bg-[#f2f3ff] rounded-xl p-5 flex flex-col justify-between border border-[#eaebf0]/60">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-[#10b981]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">Station Health</h3>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-[#6cf8bb] text-[#002113] text-xs font-bold">
                98.6%
              </span>
            </div>

            {/* Circular SVG Gauge */}
            <div className="flex flex-col items-center py-3">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-[#eaedff]"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3.5"
                  />
                  <path
                    className="text-[#10b981]"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeDasharray="98.6, 100"
                    strokeLinecap="round"
                    strokeWidth="3.5"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="font-display font-extrabold text-2xl text-[#131b2e]">98.6%</span>
                  <span className="text-[10px] text-[#464554] uppercase tracking-wider font-semibold">
                    Envelope Safe
                  </span>
                </div>
              </div>
            </div>

            {/* Health Telemetry Metric Cards */}
            <div className="space-y-2.5 mt-2">
              <div className="p-3 rounded-lg bg-white shadow-sm border border-[#eaebf0] flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#464554]">Indoor Habitation</p>
                  <p className="font-display font-bold text-sm text-[#006c49]">+21.0°C</p>
                </div>
                <span className="text-[10px] text-[#006c49] bg-[#6cf8bb]/30 px-2 py-0.5 rounded-full font-semibold">
                  Safe Margin
                </span>
              </div>

              <div className="p-3 rounded-lg bg-white shadow-sm border border-[#eaebf0] flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-[#464554]">Utilidor Potable Water</p>
                  <p className="font-display font-bold text-sm text-[#4648d4]">+4.8°C</p>
                </div>
                <span className="text-[10px] text-[#4648d4] bg-[#e1e0ff] px-2 py-0.5 rounded-full font-semibold">
                  Heated
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs text-[#464554]">
            <span>0 Life-support violations</span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
          </div>
        </div>

      </div>
    </div>
  );
};
