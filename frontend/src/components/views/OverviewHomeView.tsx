import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Thermometer, 
  Wind, 
  Radio, 
  ShieldCheck, 
  AlertTriangle, 
  Compass, 
  Activity, 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  Layers, 
  Sun, 
  Droplet, 
  Sparkles, 
  ArrowRight, 
  Clock, 
  Fuel, 
  Cpu, 
  Users, 
  Check, 
  Flame, 
  CloudSnow, 
  X,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { StationId, StationSnapshot, StationInfo, SpaceWeatherMetrics, PolarWeatherObservation } from '../../types';
import { 
  fetchSpaceWeatherCurrent, 
  fetchPolarWeatherCurrent, 
  injectScenario, 
  clearScenario, 
  simulatePolarBlizzard 
} from '../../api';

interface OverviewHomeViewProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  snapshot: StationSnapshot | null;
  stationsList: StationInfo[] | null;
  activeCrisis: string | null;
  isResolved: boolean;
  onOpenDigitalTwin: () => void;
  onOpenAgents: () => void;
  onOpenActions: () => void;
  onLaunchCockpit: () => void;
  onInjectCrisis: (crisis: string) => void;
  onResetCrisis: () => void;
}

export const OverviewHomeView: React.FC<OverviewHomeViewProps> = ({
  activeStation,
  onStationChange,
  snapshot,
  stationsList,
  activeCrisis,
  isResolved,
  onOpenDigitalTwin,
  onOpenAgents,
  onOpenActions,
  onLaunchCockpit,
  onInjectCrisis,
  onResetCrisis,
}) => {
  const [utcTime, setUtcTime] = useState<string>('');
  const [selectedSubsystem, setSelectedSubsystem] = useState<string | null>(null);
  const [spaceWeather, setSpaceWeather] = useState<SpaceWeatherMetrics | null>(null);
  const [polarWeather, setPolarWeather] = useState<PolarWeatherObservation | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Polar UTC Clock Tick
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll Space Weather & Polar AMPS Weather
  useEffect(() => {
    let isMounted = true;
    const loadWeather = async () => {
      try {
        const [sw, pw] = await Promise.all([
          fetchSpaceWeatherCurrent().catch(() => null),
          fetchPolarWeatherCurrent().catch(() => null),
        ]);
        if (isMounted) {
          if (sw) setSpaceWeather(sw);
          if (pw) setPolarWeather(pw);
        }
      } catch {}
    };
    loadWeather();
    const interval = setInterval(loadWeather, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const isBharati = activeStation === 'bharati';
  const kpis = snapshot?.kpis;
  const readings = snapshot?.readings || {};

  // Resolved live telemetry readings
  const totalLoadKw = kpis?.station_electrical_load_kw != null 
    ? kpis.station_electrical_load_kw.toFixed(1) 
    : (kpis as any)?.total_load_kw != null ? (kpis as any).total_load_kw.toFixed(1) : '142.5';
    
  const totalGenKw = kpis?.total_generation_kw != null 
    ? kpis.total_generation_kw.toFixed(1) 
    : '185.0';

  const gridFreqHz = kpis?.grid_frequency_hz != null ? kpis.grid_frequency_hz.toFixed(2) : '50.02';
  const indoorTemp = kpis?.indoor_avg_temp_c != null ? kpis.indoor_avg_temp_c.toFixed(1) : '+20.5';
  const ambientTemp = kpis?.ambient_temp_c != null ? kpis.ambient_temp_c.toFixed(1) : '-28.4';
  const windMps = kpis?.wind_speed_mps != null ? kpis.wind_speed_mps.toFixed(1) : '14.2';
  const fuelDays = kpis?.fuel_autonomy_days != null ? Math.round(kpis.fuel_autonomy_days) : 182;
  const waterDays = kpis?.water_autonomy_days != null ? Math.round(kpis.water_autonomy_days) : 45;
  const healthPct = kpis?.composite_risk_score != null 
    ? Math.max(0, Math.min(100, Math.round((1.0 - (kpis.composite_risk_score / 100.0)) * 100))) 
    : 98.4;

  const isChpTripped = activeCrisis === 'GENERATOR_TRIP' && !isResolved;
  const isBlizzard = activeCrisis === 'BLIZZARD_STRIKE';
  const isFreeze = activeCrisis === 'WATER_LINE_FREEZE';

  const handleDrill = async (drillName: string) => {
    setActionFeedback(`Injecting physical disturbance: ${drillName}...`);
    try {
      if (drillName === 'GENERATOR_TRIP') {
        await onInjectCrisis('GENERATOR_TRIP');
        setActionFeedback('Genset 01 tripped. 10-Agent society deliberating ATS transfer.');
      } else if (drillName === 'BLIZZARD_STRIKE') {
        await simulatePolarBlizzard('CONDITION_1_LOCKOUT');
        await onInjectCrisis('BLIZZARD_STRIKE');
        setActionFeedback('AMPS Katabatic Blizzard: 42 m/s winds, Condition 1 Lockout active.');
      } else if (drillName === 'WATER_LINE_FREEZE') {
        await onInjectCrisis('WATER_LINE_FREEZE');
        setActionFeedback('Lake Priyadarshini water line freeze hazard: emergency trace heat on.');
      } else if (drillName === 'RESET') {
        await onResetCrisis();
        setActionFeedback('Nominal baseline restored across both stations.');
      }
    } catch {
      setActionFeedback('Failed to execute scenario.');
    }
    setTimeout(() => setActionFeedback(null), 3500);
  };

  return (
    <div className="w-full flex flex-col gap-8 text-left animate-in fade-in duration-300">
      {/* ========================================================================= */}
      {/* 1. TOP HEADER & SOVEREIGN STATUS RIBBON                                  */}
      {/* ========================================================================= */}
      <div className="w-full pb-6 border-b border-[#eaebf0] flex flex-col gap-4">
        {/* Top Metadata Badges */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f2f3ff] border border-[#eaedff] text-[11px] font-semibold text-[#4648d4] font-mono shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              <span>NCPOR • MoES Govt of India</span>
            </span>

            <span className="px-2.5 py-1 rounded-full bg-white border border-[#eaebf0] text-[11px] font-mono text-[#73738c] shadow-2xs">
              SIH 2026 PS26060
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
            {/* Live Clock */}
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#eaebf0] text-[#131b2e] shadow-2xs">
              <Clock className="w-3.5 h-3.5 text-[#006577]" />
              <span>{utcTime || 'POLAR UTC'}</span>
            </div>

            {/* 1Hz Telemetry Sync Badge */}
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] font-medium shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              <span>1 Hz Multiplexed Stream</span>
            </div>
          </div>
        </div>

        {/* Hero Title & Context Switcher */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pt-2">
          <div>
            <h1 className="font-display font-black text-3xl sm:text-4xl lg:text-[42px] leading-[1.12] text-[#131b2e] tracking-tight">
              <span className="text-[#4648d4] font-black mr-3">DTIARS</span>
              Digital Twin for Indian Antarctic Research Stations
            </h1>
            <p className="text-sm text-[#464554] mt-2 max-w-3xl leading-relaxed">
              Real-time remote monitoring, microgrid physics simulation, autonomous multi-agent governance, and life-support cryospheric protection for Bharati and Maitri stations.
            </p>
          </div>

          {/* Station Switcher Dual Pill */}
          <div className="p-1 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex items-center gap-1 self-start lg:self-auto shrink-0 font-mono text-xs">
            <button
              onClick={() => onStationChange('bharati')}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
                isBharati
                  ? 'bg-[#4648d4] text-white font-bold shadow-md'
                  : 'text-[#464554] hover:text-[#131b2e] hover:bg-[#faf8ff]'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-[#10b981]" />
              <span>Bharati Station</span>
              <span className="text-[10px] opacity-80">(69°S)</span>
            </button>

            <button
              onClick={() => onStationChange('maitri')}
              className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all cursor-pointer ${
                !isBharati
                  ? 'bg-[#4648d4] text-white font-bold shadow-md'
                  : 'text-[#464554] hover:text-[#131b2e] hover:bg-[#faf8ff]'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
              <span>Maitri Station</span>
              <span className="text-[10px] opacity-80">(70°S)</span>
            </button>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. GLANCEABLE SIX-PILLAR OPERATIONAL METRICS RIBBON                        */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {/* Microgrid Load */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Microgrid Load
            </span>
            <Zap className="w-4 h-4 text-[#4648d4]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-2xl font-black font-mono text-[#131b2e]">{totalLoadKw}</span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">kW</span>
          </div>
          <span className="text-[11px] font-mono text-[#006c49] mt-1">
            {totalGenKw} kW Gen ({gridFreqHz} Hz)
          </span>
        </div>

        {/* Habitat Thermal */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Living Thermal
            </span>
            <Thermometer className="w-4 h-4 text-[#006577]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-2xl font-black font-mono text-[#131b2e]">{indoorTemp}</span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">°C</span>
          </div>
          <span className="text-[11px] font-mono text-[#73738c] mt-1">
            Ambient: {ambientTemp}°C
          </span>
        </div>

        {/* Katabatic Winds */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Katabatic Wind
            </span>
            <Wind className="w-4 h-4 text-[#006577]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className={`text-2xl font-black font-mono ${isBlizzard ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
              {windMps}
            </span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">m/s</span>
          </div>
          <span className="text-[11px] font-mono text-[#73738c] mt-1">
            {Number(windMps) > 25 ? 'Blizzard Surge' : 'Polar Drift Nominal'}
          </span>
        </div>

        {/* Potable Utilidor */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Utilidor Flow
            </span>
            <Droplet className="w-4 h-4 text-[#4648d4]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className={`text-2xl font-black font-mono ${isFreeze ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
              {isFreeze ? '-1.8' : '+4.2'}
            </span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">°C</span>
          </div>
          <span className={`text-[11px] font-mono mt-1 ${isFreeze ? 'text-[#e11d48] font-bold' : 'text-[#006c49]'}`}>
            {isFreeze ? 'Freeze Alert (12m)' : 'Trace Heat Safe'}
          </span>
        </div>

        {/* Fuel Autonomy */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Fuel Autonomy
            </span>
            <Fuel className="w-4 h-4 text-[#f59e0b]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-2xl font-black font-mono text-[#131b2e]">{fuelDays}</span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">Days</span>
          </div>
          <span className="text-[11px] font-mono text-[#006c49] mt-1">
            124,500 L ATF Jet A-1
          </span>
        </div>

        {/* Station Integrity Score */}
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-[#73738c] uppercase tracking-wider">
              Health Index
            </span>
            <ShieldCheck className="w-4 h-4 text-[#10b981]" />
          </div>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-2xl font-black font-mono text-[#131b2e]">{healthPct}%</span>
            <span className="text-xs font-mono font-semibold text-[#006c49]">Nominal</span>
          </div>
          <span className="text-[11px] font-mono text-[#73738c] mt-1">
            0 Critical Lockouts
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. HERO INTERACTIVE STATION DIGITAL TWIN CANVAS                           */}
      {/* ========================================================================= */}
      <div className="rounded-3xl bg-white border border-[#eaebf0] shadow-xl p-6 sm:p-7 relative flex flex-col gap-6">
        {/* Top Card Bar */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-5 border-b border-[#eaebf0]">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full bg-[#f2f3ff] text-[#4648d4] text-[10px] font-mono font-bold uppercase tracking-wider">
                PHYSICS-INFORMED DIGITAL TWIN
              </span>
              <span className="text-xs font-mono text-[#73738c]">
                {isBharati ? "Larsemann Hills (69°24'S, 76°11'E)" : "Schirmacher Oasis (70°45'S, 11°43'E)"}
              </span>
            </div>
            <h2 className="font-display font-black text-xl text-[#131b2e] mt-1">
              {isBharati ? 'Bharati Research Station Subsystem Architecture' : 'Maitri Research Station Container Infrastructure'}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onOpenDigitalTwin}
              className="px-4 py-2 rounded-xl bg-[#4648d4] hover:bg-[#3b3dbf] text-white text-xs font-mono font-bold flex items-center gap-2 shadow-sm transition-all"
            >
              <span>Open React Flow Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 4 Interactive Subsystem Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Subsystem 1: Power & Microgrid */}
          <div 
            onClick={() => setSelectedSubsystem(selectedSubsystem === 'POWER' ? null : 'POWER')}
            className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
              selectedSubsystem === 'POWER'
                ? 'bg-[#f2f3ff] border-[#4648d4] shadow-md ring-2 ring-[#4648d4]/20'
                : isChpTripped
                ? 'bg-[#fff1f2] border-[#f43f5e]'
                : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#c7c4d7]'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isChpTripped ? 'bg-[#f43f5e] text-white' : 'bg-[#4648d4] text-white'}`}>
                    <Zap className="w-4 h-4" />
                  </div>
                  <span className="font-display font-bold text-sm text-[#131b2e]">Power Substation</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-[#eaebf0] text-[#464554]">
                  400V 50Hz
                </span>
              </div>
              <p className="text-xs text-[#464554] font-mono leading-relaxed mb-3">
                3x Volvo Penta CHP generators with automatic bus transfer (ATS) &amp; BESS battery bank.
              </p>
            </div>
            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono">
              <span className="text-[#73738c]">Genset 01:</span>
              <span className={`font-bold ${isChpTripped ? 'text-[#e11d48]' : 'text-[#006c49]'}`}>
                {isChpTripped ? 'TRIPPED (0.0 kW)' : '72.4 kW'}
              </span>
            </div>
          </div>

          {/* Subsystem 2: Potable Utilidor */}
          <div 
            onClick={() => setSelectedSubsystem(selectedSubsystem === 'UTILIDOR' ? null : 'UTILIDOR')}
            className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
              selectedSubsystem === 'UTILIDOR'
                ? 'bg-[#f2f3ff] border-[#4648d4] shadow-md ring-2 ring-[#4648d4]/20'
                : isFreeze
                ? 'bg-[#ecfeff] border-[#06b6d4]'
                : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#c7c4d7]'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isFreeze ? 'bg-[#06b6d4] text-white' : 'bg-[#006577] text-white'}`}>
                    <Droplet className="w-4 h-4" />
                  </div>
                  <span className="font-display font-bold text-sm text-[#131b2e]">Potable Utilidor</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-[#eaebf0] text-[#464554]">
                  Trace Heat
                </span>
              </div>
              <p className="text-xs text-[#464554] font-mono leading-relaxed mb-3">
                3.5 km delivery line from Lake Priyadarshini with automated anchor-ice burst prevention.
              </p>
            </div>
            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono">
              <span className="text-[#73738c]">Line Temp:</span>
              <span className={`font-bold ${isFreeze ? 'text-[#0891b2]' : 'text-[#006c49]'}`}>
                {isFreeze ? '-1.8°C (FREEZE)' : '+4.2°C Heated'}
              </span>
            </div>
          </div>

          {/* Subsystem 3: HVAC Life Support */}
          <div 
            onClick={() => setSelectedSubsystem(selectedSubsystem === 'HVAC' ? null : 'HVAC')}
            className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
              selectedSubsystem === 'HVAC'
                ? 'bg-[#f2f3ff] border-[#4648d4] shadow-md ring-2 ring-[#4648d4]/20'
                : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#c7c4d7]'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-[#10b981] text-white flex items-center justify-center">
                    <Thermometer className="w-4 h-4" />
                  </div>
                  <span className="font-display font-bold text-sm text-[#131b2e]">HVAC Life Support</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-[#eaebf0] text-[#464554]">
                  Hab Core
                </span>
              </div>
              <p className="text-xs text-[#464554] font-mono leading-relaxed mb-3">
                Dual AHU fresh air recirculation with katabatic blizzard storm damper containment seals.
              </p>
            </div>
            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono">
              <span className="text-[#73738c]">Dampers:</span>
              <span className={`font-bold ${isBlizzard ? 'text-[#0284c7]' : 'text-[#006c49]'}`}>
                {isBlizzard ? 'SEALED (100%)' : 'OPEN (45%)'}
              </span>
            </div>
          </div>

          {/* Subsystem 4: Satcom Gateway */}
          <div 
            onClick={() => setSelectedSubsystem(selectedSubsystem === 'SATCOM' ? null : 'SATCOM')}
            className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
              selectedSubsystem === 'SATCOM'
                ? 'bg-[#f2f3ff] border-[#4648d4] shadow-md ring-2 ring-[#4648d4]/20'
                : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#c7c4d7]'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-[#4648d4] text-white flex items-center justify-center">
                    <Radio className="w-4 h-4" />
                  </div>
                  <span className="font-display font-bold text-sm text-[#131b2e]">Satcom Gateway</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white border border-[#eaebf0] text-[#464554]">
                  DTN RFC 9171
                </span>
              </div>
              <p className="text-xs text-[#464554] font-mono leading-relaxed mb-3">
                Bandwidth-aware telemetry sync with NCPOR Goa Atlas using differential keyframe compression.
              </p>
            </div>
            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono">
              <span className="text-[#73738c]">Mainland Link:</span>
              <span className="font-bold text-[#006c49]">640ms Synchronized</span>
            </div>
          </div>
        </div>

        {/* Selected Subsystem Detail Flyout */}
        {selectedSubsystem && (
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex items-start justify-between gap-4 animate-in fade-in duration-200">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[#4648d4] animate-pulse" />
                <span className="font-mono text-xs font-bold text-[#4648d4] uppercase">
                  Active Subsystem Telemetry Diagnostics: {selectedSubsystem}
                </span>
              </div>
              <p className="text-xs text-[#464554] font-mono leading-relaxed">
                {selectedSubsystem === 'POWER' && 'Genset 01 (Volvo Penta D16): 72.4 kW • Genset 02: Standby 0.0 kW • Coolant: 84.5°C • Fuel flow: 34.2 L/h • Bus Voltage: 401.2 V'}
                {selectedSubsystem === 'UTILIDOR' && 'Water Delivery Line: +4.2°C • Trace Heater Loop: Auto (3.2 kW) • Flow: 48.5 LPM • Strainer Depth: 6.2m below Priyadarshini ice sheet'}
                {selectedSubsystem === 'HVAC' && 'Living Quarters: +20.5°C • Lab Complex: +18.2°C • CO2: 520 ppm • Recirculation: 85% • Blizzard Storm Damper: Ready'}
                {selectedSubsystem === 'SATCOM' && 'Inmarsat BGAN: 640ms latency • Bandwidth: 256 kbps • Differential Delta: 90.2% bandwidth saved • DTN Spool Buffer: 0 pending'}
              </p>
            </div>
            <button
              onClick={() => setSelectedSubsystem(null)}
              className="text-[#73738c] hover:text-[#131b2e] p-1.5 rounded-lg hover:bg-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 4. DUAL RADARS: SPACE WEATHER × AMPS POLAR NUMERICAL METEOROLOGY          */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: NOAA SWPC Space Weather Radar */}
        <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#fef3c7] text-[#d97706] flex items-center justify-center font-bold text-xs">
                  <Sun className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-[#131b2e]">
                    NOAA Space Weather Observation
                  </h3>
                  <span className="text-[10px] font-mono text-[#73738c]">
                    Live SWPC Feed • Polar Cap Absorption &amp; Satcom Attenuation
                  </span>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-[10px] font-mono font-bold">
                Online
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs mb-4">
              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Kp Index</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {spaceWeather?.kp_index != null ? spaceWeather.kp_index.toFixed(2) : '2.33'}
                </span>
                <span className="text-[10px] text-[#006c49]">Quiet (G0)</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Solar Wind</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {spaceWeather?.solar_wind_speed_kms != null ? spaceWeather.solar_wind_speed_kms.toFixed(0) : '420'}
                </span>
                <span className="text-[10px] text-[#73738c]">km/s</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">IMF (Bz)</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {spaceWeather?.imf_bz_nt != null ? `${spaceWeather.imf_bz_nt > 0 ? '+' : ''}${spaceWeather.imf_bz_nt.toFixed(1)}` : '+1.4'}
                </span>
                <span className="text-[10px] text-[#73738c]">nT</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Absorption</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {spaceWeather?.auroral_absorption_db != null ? `${spaceWeather.auroral_absorption_db.toFixed(2)}` : '0.12'}
                </span>
                <span className="text-[10px] text-[#006c49]">dB Safe</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono text-[#73738c]">
            <span>Satcom BGAN Margin: <strong className="text-[#131b2e]">14.8 dB</strong></span>
            <span className="text-[#006c49] font-medium">HF Radio: Normal</span>
          </div>
        </div>

        {/* Right: AMPS Polar Numerical Weather Radar */}
        <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#ecfeff] text-[#0891b2] flex items-center justify-center font-bold text-xs">
                  <Wind className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-[#131b2e]">
                    AMPS Polar Numerical Weather
                  </h3>
                  <span className="text-[10px] font-mono text-[#73738c]">
                    Antarctic Mesoscale Prediction System (WRF Model)
                  </span>
                </div>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold border ${
                isBlizzard
                  ? 'bg-[#fff1f2] border-[#f43f5e] text-[#e11d48] animate-pulse'
                  : 'bg-[#ecfdf5] border-[#a7f3d0] text-[#006c49]'
              }`}>
                {isBlizzard ? 'CONDITION 1 LOCKOUT' : 'CONDITION 3 NOMINAL'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs mb-4">
              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Surface Temp</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {ambientTemp}°C
                </span>
                <span className="text-[10px] text-[#73738c]">Ground Sensor</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Wind Chill</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  {polarWeather?.wind_chill_c != null ? polarWeather.wind_chill_c.toFixed(1) : '-36.2'}°C
                </span>
                <span className="text-[10px] text-[#d97706]">Exposure 15m</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Wind Velocity</span>
                <span className={`text-base font-black mt-0.5 block ${isBlizzard ? 'text-[#e11d48]' : 'text-[#131b2e]'}`}>
                  {windMps} m/s
                </span>
                <span className="text-[10px] text-[#73738c]">10m Mast</span>
              </div>

              <div className="p-3 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
                <span className="text-[10px] text-[#73738c] block uppercase">Barometer</span>
                <span className="text-base font-black text-[#131b2e] mt-0.5 block">
                  985 hPa
                </span>
                <span className="text-[10px] text-[#006c49]">Steady (-0.8)</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono text-[#73738c]">
            <span>Expedition Safety Directive: <strong className="text-[#131b2e]">{isBlizzard ? 'Mandatory Lockdown' : 'Outdoor Travel Allowed'}</strong></span>
            <span className="text-[#4648d4] font-medium">WRF Polar 48h Verified</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 5. TACTILE CRISIS DRILL BENCH & 10-AGENT DELIBERATION STREAM               */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Crisis Drill Testing Bench (7 cols) */}
        <div className="lg:col-span-7 p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#f2f3ff] text-[#4648d4] flex items-center justify-center font-bold text-xs">
                  <Play className="w-4 h-4 fill-current" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-[#131b2e]">
                    Emergency Crisis &amp; Autonomy Drill Bench
                  </h3>
                  <span className="text-[10px] font-mono text-[#73738c]">
                    Trigger physical disturbances to validate autonomous multi-agent response
                  </span>
                </div>
              </div>
              <span className="text-xs font-mono text-[#4648d4] font-bold">
                &lt;1.2s Autonomy
              </span>
            </div>

            <p className="text-xs text-[#464554] font-mono leading-relaxed mb-4">
              Inject real physical disturbances into the station governor. Notice how the 10 cognitive agents immediately deliberate on the message bus and execute Tier 1 safety interlocks without human intervention.
            </p>

            {/* Drill Buttons Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                onClick={() => handleDrill('GENERATOR_TRIP')}
                className={`p-3.5 rounded-2xl border text-left font-mono transition-all cursor-pointer flex flex-col justify-between gap-1.5 ${
                  isChpTripped
                    ? 'bg-[#fff1f2] border-[#f43f5e] shadow-sm'
                    : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#f43f5e]/40'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-[#e11d48]">
                  <span>Genset 01 Trip</span>
                  <Flame className="w-4 h-4" />
                </div>
                <span className="text-[11px] text-[#73738c]">
                  ATS Transfer to Genset 02 in &lt;1.2s
                </span>
              </button>

              <button
                onClick={() => handleDrill('BLIZZARD_STRIKE')}
                className={`p-3.5 rounded-2xl border text-left font-mono transition-all cursor-pointer flex flex-col justify-between gap-1.5 ${
                  isBlizzard
                    ? 'bg-[#f0f9ff] border-[#0284c7] shadow-sm'
                    : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#0284c7]/40'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-[#0284c7]">
                  <span>Katabatic Blizzard</span>
                  <CloudSnow className="w-4 h-4" />
                </div>
                <span className="text-[11px] text-[#73738c]">
                  42 m/s winds, Cond 1 Damper Seal
                </span>
              </button>

              <button
                onClick={() => handleDrill('WATER_LINE_FREEZE')}
                className={`p-3.5 rounded-2xl border text-left font-mono transition-all cursor-pointer flex flex-col justify-between gap-1.5 ${
                  isFreeze
                    ? 'bg-[#ecfeff] border-[#06b6d4] shadow-sm'
                    : 'bg-[#faf8ff] border-[#eaebf0] hover:border-[#06b6d4]/40'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-[#0891b2]">
                  <span>Utilidor Freeze</span>
                  <Droplet className="w-4 h-4" />
                </div>
                <span className="text-[11px] text-[#73738c]">
                  Emergency trace heat boost (24 kW)
                </span>
              </button>
            </div>
          </div>

          {/* Drill Action Feedback & Reset */}
          <div className="mt-4 pt-3 border-t border-[#eaebf0] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
            <span className="text-[#4648d4] font-medium">
              {actionFeedback || 'Drill system ready. Click any scenario button to trigger.'}
            </span>

            <button
              onClick={() => handleDrill('RESET')}
              className="px-3.5 py-1.5 rounded-xl bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] font-bold flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restore Nominal</span>
            </button>
          </div>
        </div>

        {/* Right: 10-Agent Cognitive Society Stream (5 cols) */}
        <div className="lg:col-span-5 p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#f2f3ff] text-[#4648d4] flex items-center justify-center font-bold text-xs">
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-display font-bold text-base text-[#131b2e]">
                    10-Agent Cognitive Society
                  </h3>
                  <span className="text-[10px] font-mono text-[#73738c]">
                    Sovereign Inter-Agent Bus Activity
                  </span>
                </div>
              </div>
              <button
                onClick={onOpenAgents}
                className="text-xs font-mono text-[#4648d4] font-bold flex items-center gap-1 hover:underline"
              >
                <span>Inspect Graph</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Agent Live Status Badges */}
            <div className="space-y-2 font-mono text-xs mb-3">
              <div className="p-2.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex items-center justify-between">
                <span className="text-[#131b2e] font-semibold">PerceptionAgent</span>
                <span className="text-[#006c49] font-bold text-[11px] flex items-center gap-1">
                  <Check className="w-3 h-3" /> 1 Hz Sensor Scan
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex items-center justify-between">
                <span className="text-[#131b2e] font-semibold">CausalEngineAgent</span>
                <span className="text-[#4648d4] font-bold text-[11px]">
                  Blast Radius Clean
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex items-center justify-between">
                <span className="text-[#131b2e] font-semibold">ResourceOptimizer</span>
                <span className="text-[#006c49] font-bold text-[11px]">
                  45 kW Reserve Valid
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0] flex items-center justify-between">
                <span className="text-[#131b2e] font-semibold">FridayChiefOrchestrator</span>
                <span className="text-[#4648d4] font-bold text-[11px]">
                  Tier 1 Interlocks Active
                </span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between text-xs font-mono text-[#73738c]">
            <span>Consensus Latency: <strong className="text-[#131b2e]">1.18s</strong></span>
            <span className="text-[#006c49]">100% Deterministic</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 6. INSTITUTIONAL ACCREDITATION & STRATEGIC PARTNERS                        */}
      {/* ========================================================================= */}
      <div className="w-full p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#10b981]" />
            <h4 className="font-display font-bold text-sm text-[#131b2e]">
              National Polar &amp; Space Infrastructure Integration
            </h4>
          </div>
          <p className="text-xs text-[#73738c] font-mono">
            Cryptographically authenticated CAP v1.2 webhook links and differential telemetry replication.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs font-mono font-bold text-[#4648d4]">
          <span className="px-3 py-1.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
            NCPOR Goa (HQ)
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
            MoES Govt of India
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
            ISRO ISTRAC
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
            IMD Polar Met
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-[#faf8ff] border border-[#eaebf0]">
            INCOIS Sea Ice
          </span>
        </div>
      </div>
    </div>
  );
};
