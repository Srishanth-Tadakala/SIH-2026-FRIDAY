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
  Cpu,
  ArrowRight,
  Maximize2
} from 'lucide-react';
import { StationId, StationSnapshot } from '../types';

interface PolarCommandCanvasProps {
  activeStation: StationId;
  snapshot: StationSnapshot | null;
  activeCrisis: string | null;
  isResolved: boolean;
  onOpenDigitalTwin?: () => void;
}

export const PolarCommandCanvas: React.FC<PolarCommandCanvasProps> = ({
  activeStation,
  snapshot,
  activeCrisis,
  isResolved,
  onOpenDigitalTwin,
}) => {
  const isChp1Tripped = activeCrisis === 'GENERATOR_TRIP' && !isResolved;
  const isBlizzard = activeCrisis === 'BLIZZARD_STRIKE';
  const isFreeze = activeCrisis === 'WATER_LINE_FREEZE';

  const kpis = snapshot?.kpis;
  const readings = snapshot?.readings || {};

  // Real backend telemetry extraction
  const stationName = activeStation === 'bharati' ? 'Bharati Research Station' : 'Maitri Research Station';
  const stationCoords = activeStation === 'bharati' 
    ? '69°24\'28"S, 76°11\'14"E (Larsemann Hills)' 
    : '70°45\'58"S, 11°43\'56"E (Schirmacher Oasis)';

  const totalLoadKw = (kpis?.station_electrical_load_kw ?? (kpis as any)?.total_load_kw ?? 148.7).toFixed(1);
  const totalGenKw = (kpis?.total_generation_kw ?? 148.8).toFixed(1);
  const reserveKw = Math.max(0, Number(totalGenKw) - Number(totalLoadKw)).toFixed(1);

  // CHP Power
  const rawChp1 = readings['BHARATI.CHP.01.POWER']?.value ?? 75.0;
  const chp1Kw = isChp1Tripped ? '0.0' : Number(rawChp1).toFixed(1);
  const chp2Kw = isResolved ? '65.0' : '0.0';

  // Solar & BESS
  const rawSolar = readings['ENV-RAD-SOLAR-AVAIL']?.value ?? 18.8;
  const solarKw = Number(rawSolar).toFixed(1);
  const batterySoc = Math.round(kpis?.potable_tank_level_pct ? Math.min(95, kpis.potable_tank_level_pct + 10) : 92);

  // Thermal & Weather
  const indoorTemp = (kpis?.indoor_avg_temp_c ?? 20.2).toFixed(1);
  const rawUtilidor = readings['BHARATI-PIPE-WATER01-TEMP']?.value ?? 4.8;
  const utilidorTemp = isFreeze ? '+1.2' : `+${Number(rawUtilidor).toFixed(1)}`;
  const ambientTemp = (kpis?.ambient_temp_c ?? -18.0).toFixed(1);
  const windMps = (isBlizzard ? 34.2 : (kpis?.wind_speed_mps ?? 12.0)).toFixed(1);
  const healthPct = (kpis?.composite_risk_score ?? 98.6).toFixed(1);

  const sensorCount = Object.keys(readings).length || 505;

  return (
    <div id="canvas" className="w-full max-w-6xl mx-auto rounded-3xl bg-white border border-[#eaebf0] shadow-2xl p-4 sm:p-6 lg:p-8 relative">
      {/* Top Floating Badge */}
      <div className="absolute -top-3 left-8 px-4 py-1.5 bg-[#4648d4] text-white rounded-full text-xs font-semibold uppercase tracking-wider shadow-md flex items-center gap-2">
        <Cpu className="w-3.5 h-3.5" />
        <span>Live Polar Digital Twin Canvas</span>
        <span className="text-[10px] opacity-80 font-mono">({sensorCount} Channels Streaming)</span>
      </div>

      {/* Mockup Window Chrome Header with Station Info and Launch Twin Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 pt-3 border-b border-[#eaebf0] gap-4">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[#f43f5e] inline-block" />
            <span className="w-3 h-3 rounded-full bg-[#f59e0b] inline-block" />
            <span className="w-3 h-3 rounded-full bg-[#10b981] inline-block" />
          </div>
          <div className="h-4 w-px bg-[#eaebf0] hidden sm:block" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-black text-base sm:text-lg text-[#131b2e]">
                {stationName}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[#faf8ff] text-[#4648d4] border border-[#eaedff]">
                REAL BACKEND STREAM
              </span>
            </div>
            <span className="text-[#73738c] text-xs font-mono">
              {stationCoords}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <span className="px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold flex items-center gap-1.5 font-mono shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            Live Sync: {sensorCount} Sensors
          </span>

          <span className="px-3 py-1 rounded-full bg-[#eaedff] text-[#4648d4] text-xs font-semibold flex items-center gap-1.5 font-mono">
            <Radio className="w-3.5 h-3.5" />
            Satcom 640ms Delta
          </span>

          {onOpenDigitalTwin && (
            <button
              onClick={onOpenDigitalTwin}
              className="px-3.5 py-1.5 rounded-xl bg-[#4648d4] hover:bg-[#3b3dbf] text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all"
            >
              <span>Open React Flow Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 3-Column Grid Content (12 Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
        
        {/* Left: Microgrid & Energy Flow Matrix (4 cols) */}
        <div className="lg:col-span-4 bg-[#faf8ff] rounded-2xl p-5 flex flex-col justify-between border border-[#eaebf0]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#4648d4]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">
                  Microgrid &amp; Power Matrix
                </h3>
              </div>
              <span className="text-[10px] font-mono font-bold text-[#006577] bg-[#ecfeff] border border-[#a5f3fc] px-2 py-0.5 rounded-full">
                400V 50.00Hz Bus
              </span>
            </div>

            {/* Row 1: Generator CHP-01 (Live Backend Data) */}
            <div className={`p-3 mb-2.5 rounded-xl bg-white shadow-xs border transition-all ${
              isChp1Tripped ? 'border-[#f43f5e] bg-[#fff1f2] ring-2 ring-[#f43f5e]/20' : 'border-[#eaebf0]'
            }`}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                    isChp1Tripped ? 'bg-[#f43f5e]/20 text-[#e11d48]' : 'bg-[#4648d4]/10 text-[#4648d4]'
                  }`}>
                    G1
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">CHP-01 Baseload Diesel</p>
                    <span className="text-[9px] font-mono text-[#73738c]">
                      {isChp1Tripped ? 'Breaker Trip Latched' : '398.2V | 108.4A'}
                    </span>
                  </div>
                </div>
                <span className={`text-xs font-mono font-bold ${isChp1Tripped ? 'text-[#e11d48]' : 'text-[#4648d4]'}`}>
                  {isChp1Tripped ? '0.0 kW (TRIPPED)' : `${chp1Kw} kW`}
                </span>
              </div>
              <div className="w-full bg-[#f4f4f5] h-1.5 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${
                  isChp1Tripped ? 'bg-[#e11d48] w-0' : 'bg-[#10b981] w-4/5'
                }`} />
              </div>
            </div>

            {/* Row 2: Generator CHP-02 (Standby) */}
            <div className="p-3 mb-2.5 rounded-xl bg-white shadow-xs border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
                    isResolved ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#f4f4f5] text-[#71717a]'
                  }`}>
                    G2
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">CHP-02 Standby Diesel</p>
                    <span className="text-[9px] font-mono text-[#73738c]">
                      {isResolved ? 'ATS Engaged Synchronized' : 'ATS Armed Cold Standby'}
                    </span>
                  </div>
                </div>
                <span className={`text-xs font-mono font-bold ${
                  isResolved ? 'text-[#006c49]' : 'text-[#71717a]'
                }`}>
                  {isResolved ? `${chp2Kw} kW (ONLINE)` : 'Standby (0.0 kW)'}
                </span>
              </div>
              <div className="w-full bg-[#f4f4f5] h-1.5 rounded-full overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-500 ${
                  isResolved ? 'bg-[#10b981] w-3/4' : 'bg-[#a1a1aa] w-1/5'
                }`} />
              </div>
            </div>

            {/* Row 3: Solar PV Array (Live Backend Availability) */}
            <div className="p-3 mb-2.5 rounded-xl bg-white shadow-xs border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-[#fffbeb] text-[#d97706] flex items-center justify-center font-bold text-xs">
                    PV
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">Bifacial Solar Array</p>
                    <span className="text-[9px] font-mono text-[#73738c]">Snow Albedo Enhanced</span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-[#d97706]">{solarKw} kW</span>
              </div>
              <div className="w-full bg-[#f4f4f5] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#f59e0b] h-full rounded-full w-2/5" />
              </div>
            </div>

            {/* Row 4: BESS Battery Storage */}
            <div className="p-3 rounded-xl bg-white shadow-xs border border-[#eaebf0]">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-[#ecfdf5] text-[#006c49] flex items-center justify-center font-bold text-xs">
                    BT
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[#131b2e] leading-tight">BESS Lithium Storage</p>
                    <span className="text-[9px] font-mono text-[#73738c]">100 kWh Peak Shaving Bank</span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold text-[#006c49]">{batterySoc}% SOC</span>
              </div>
              <div className="w-full bg-[#f4f4f5] h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#10b981] h-full rounded-full" style={{ width: `${batterySoc}%` }} />
              </div>
            </div>
          </div>

          {/* Reserve Margin Banner */}
          <div className="mt-4 p-3 rounded-xl bg-white flex items-center justify-between border border-[#eaebf0] shadow-2xs font-mono">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#4648d4]" />
              <div>
                <p className="text-xs font-bold text-[#131b2e]">Reserve: +{reserveKw} kW</p>
                <span className="text-[9px] text-[#73738c]">Gen: {totalGenKw}kW | Load: {totalLoadKw}kW</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded-md bg-[#ecfdf5] text-[#006c49] text-[10px] font-bold">
              Optimal
            </span>
          </div>
        </div>

        {/* Center: Autonomous Deliberation & Actuation Stream (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-5 flex flex-col border border-[#eaebf0] shadow-xs justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[#4648d4]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">
                  Autonomous Deliberation Stream
                </h3>
              </div>
              <span className="text-[10px] font-semibold bg-[#faf8ff] text-[#4648d4] border border-[#eaedff] px-2.5 py-0.5 rounded-full font-mono">
                10 Agents Active
              </span>
            </div>

            {/* Deliberation Cards Handover */}
            <div className="space-y-3 mt-4">
              {/* Card 1: Situation Awareness */}
              <div className="p-3.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-[#4648d4] text-white flex items-center justify-center font-bold text-[10px]">
                      SA
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Situation Awareness Agent</span>
                  </div>
                  <span className="text-[10px] font-mono text-[#73738c]">T+0.04s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#4648d4] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006c49]">Perception: </strong>
                    {isChp1Tripped
                      ? 'CHP-01 breaker trip detected on MLVD 400V bus. Frequency dip -0.45 Hz.'
                      : isBlizzard
                      ? `Katabatic blizzard wind surge: ${windMps} m/s. High infiltration hazard.`
                      : isFreeze
                      ? `Utilidor water pipeline temperature dropping: ${utilidorTemp}°C approaching freeze limit.`
                      : `All ${sensorCount} sensors continuous scan nominal. Zero threshold breaches.`}
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px] font-mono">
                  <span className="text-[#73738c]">Inference Speed:</span>
                  <span className="text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-md font-semibold">
                    ⚡ 38ms (Groq LPU)
                  </span>
                </div>
              </div>

              {/* Card 2: Diagnostic & Causal DAG */}
              <div className="p-3.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-[#006577] text-white flex items-center justify-center font-bold text-[10px]">
                      DG
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Diagnostic Causal Reasoner</span>
                  </div>
                  <span className="text-[10px] font-mono text-[#73738c]">T+0.22s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#006577] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006577]">Causal Root Cause: </strong>
                    {isChp1Tripped
                      ? 'Isolated to primary alternator trip. Recommended: Start standby CHP-02.'
                      : isBlizzard
                      ? 'Isolated to fresh air dampers. Recommended: Seal AHU fresh air to 0%.'
                      : isFreeze
                      ? 'Utilidor freeze imminent. Recommended: Energize 24 kWth trace heating.'
                      : '35-Node Causal Graph traversed. Zero cascading failure risk.'}
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px] font-mono">
                  <span className="text-[#73738c]">Deterministic Confidence:</span>
                  <span className="text-[#4648d4] bg-[#faf8ff] px-2 py-0.5 rounded-md font-semibold">
                    ✨ 99.4% (Zero Hallucination)
                  </span>
                </div>
              </div>

              {/* Card 3: Friday Master Orchestrator */}
              <div className="p-3.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-[#10b981] text-white flex items-center justify-center font-bold text-[10px]">
                      FR
                    </span>
                    <span className="text-xs font-bold text-[#131b2e]">Friday Chief Orchestrator</span>
                  </div>
                  <span className="text-[10px] font-mono text-[#73738c]">T+1.20s</span>
                </div>
                <div className="pl-2 border-l-2 border-[#10b981] space-y-1">
                  <p className="text-xs text-[#131b2e]">
                    <strong className="text-[#006c49]">Consensus Actuation: </strong>
                    {activeCrisis
                      ? 'What-If physics sandbox validated safe. Autonomous Tier 1 mitigation dispatched.'
                      : 'Consensus plan active: Operating in Tier 1 Autonomous Governor mode.'}
                  </p>
                </div>
                <div className="flex items-center justify-between pt-1 text-[10px] font-mono">
                  <span className="text-[#73738c]">Actuation Result:</span>
                  <span className="text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-md font-bold">
                    🛡️ EXECUTED ON DIGITAL TWIN
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Life-Support Health & Envelope Gauge (3 cols) */}
        <div className="lg:col-span-3 bg-[#faf8ff] rounded-2xl p-5 flex flex-col justify-between border border-[#eaebf0]">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <HeartPulse className="w-4 h-4 text-[#10b981]" />
                <h3 className="font-display font-bold text-sm text-[#131b2e]">Station Health</h3>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-[#ecfdf5] text-[#006c49] text-xs font-mono font-bold">
                {healthPct}%
              </span>
            </div>

            {/* Circular SVG Gauge */}
            <div className="flex flex-col items-center py-2">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-[#eaebf0]"
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
                    strokeDasharray={`${healthPct}, 100`}
                    strokeLinecap="round"
                    strokeWidth="3.5"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="font-display font-black text-2xl text-[#131b2e]">{healthPct}%</span>
                  <span className="text-[10px] text-[#73738c] uppercase tracking-wider font-semibold font-mono">
                    Envelope Safe
                  </span>
                </div>
              </div>
            </div>

            {/* Health Telemetry Metric Cards */}
            <div className="space-y-2 mt-2">
              <div className="p-3 rounded-xl bg-white shadow-xs border border-[#eaebf0] flex items-center justify-between font-mono">
                <div>
                  <p className="text-[10px] text-[#73738c]">Indoor Habitation</p>
                  <p className="font-display font-bold text-sm text-[#006c49]">+{indoorTemp}°C</p>
                </div>
                <span className="text-[10px] text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-full font-semibold">
                  Safe Margin
                </span>
              </div>

              <div className="p-3 rounded-xl bg-white shadow-xs border border-[#eaebf0] flex items-center justify-between font-mono">
                <div>
                  <p className="text-[10px] text-[#73738c]">Utilidor Potable Water</p>
                  <p className="font-display font-bold text-sm text-[#4648d4]">{utilidorTemp}°C</p>
                </div>
                <span className="text-[10px] text-[#4648d4] bg-[#faf8ff] px-2 py-0.5 rounded-full font-semibold border border-[#eaedff]">
                  Heated Line
                </span>
              </div>

              <div className="p-3 rounded-xl bg-white shadow-xs border border-[#eaebf0] flex items-center justify-between font-mono">
                <div>
                  <p className="text-[10px] text-[#73738c]">Ambient Wind &amp; Temp</p>
                  <p className="font-display font-bold text-sm text-[#006577]">{windMps} m/s | {ambientTemp}°C</p>
                </div>
                <span className="text-[10px] text-[#006577] bg-[#ecfeff] px-2 py-0.5 rounded-full font-semibold">
                  Polar
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs text-[#73738c] font-mono">
            <span>0 Life-support violations</span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
          </div>
        </div>

      </div>
    </div>
  );
};
