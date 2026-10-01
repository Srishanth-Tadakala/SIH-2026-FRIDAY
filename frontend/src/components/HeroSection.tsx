import React, { useState, useEffect } from 'react';
import { 
  Compass, 
  Zap, 
  Thermometer, 
  Droplet, 
  Radio, 
  Shield, 
  Activity, 
  AlertTriangle, 
  RotateCcw, 
  Wind, 
  ChevronRight, 
  Sun, 
  Lock,
  Cpu,
  Layers,
  Sparkles,
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import { StationId, StationSnapshot } from '../types';
import { 
  injectScenario, 
  clearScenario, 
  simulatePolarBlizzard, 
  simulateGeomagneticStorm 
} from '../api';

interface HeroSectionProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  snapshot: StationSnapshot | null;
  activeCrisis: string | null;
  onInjectCrisis: (crisis: string) => void;
  onResetCrisis: () => void;
  onLaunchCockpit: () => void;
  onOpenDigitalTwin: () => void;
  onOpenAgents: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  activeStation,
  onStationChange,
  snapshot,
  activeCrisis,
  onInjectCrisis,
  onResetCrisis,
  onLaunchCockpit,
  onOpenDigitalTwin,
  onOpenAgents,
}) => {
  // Climate Setpoint Micro-interaction
  const [setpoint, setSetpoint] = useState<number>(21.5);
  const [tacticalOverride, setTacticalOverride] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const adjustSetpoint = (delta: number) => {
    const next = Math.round((setpoint + delta) * 10) / 10;
    if (next >= 16.0 && next <= 26.0) {
      setSetpoint(next);
      showToast(`Habitat thermal target adjusted to ${next.toFixed(1)}°C`);
    }
  };

  const stationData = {
    bharati: {
      name: 'BHARATI POLAR STATION',
      coords: '69°24′28″ S, 76°11′14″ E',
      region: 'Larsemann Hills',
      elev: '35.0 m ASL',
      poleDist: '2,290 km',
      defaultPower: '148.4',
      defaultTemp: '+21.4',
      defaultAmb: '-42.8°C',
      defaultWind: 'Wind 28 kt',
      defaultGlycol: '420',
      defaultDays: '284',
      powerBar: 62,
      tempBar: 78,
    },
    maitri: {
      name: 'MAITRI POLAR STATION',
      coords: '70°46′00″ S, 11°44′00″ E',
      region: 'Schirmacher Oasis',
      elev: '117.0 m ASL',
      poleDist: '2,138 km',
      defaultPower: '126.8',
      defaultTemp: '+20.8',
      defaultAmb: '-38.2°C',
      defaultWind: 'Wind 32 kt',
      defaultGlycol: '395',
      defaultDays: '262',
      powerBar: 54,
      tempBar: 74,
    }
  };

  const currentData = stationData[activeStation];

  // Disturbance simulation handlers
  const handleScenario = async (scen: 'NOMINAL' | 'KATABATIC' | 'GEOMAG' | 'TURBINE_SHEAR') => {
    if (scen === 'NOMINAL') {
      onResetCrisis();
      await clearScenario(activeStation).catch(() => {});
      showToast('Baseline restored: All station subsystems in nominal equilibrium.');
    } else if (scen === 'KATABATIC') {
      onInjectCrisis('BLIZZARD_WARNING');
      await simulatePolarBlizzard('CONDITION_1_LOCKOUT').catch(() => {});
      showToast('Katabatic gale injected: Wind velocity spiked to 78 kt (144 km/h).');
    } else if (scen === 'GEOMAG') {
      onInjectCrisis('SOLAR_STORM');
      await simulateGeomagneticStorm('G4').catch(() => {});
      showToast('Kp-8 Geomagnetic storm active: Polar HF radio absorption critical.');
    } else if (scen === 'TURBINE_SHEAR') {
      onInjectCrisis('GENERATOR_TRIP');
      await injectScenario('GENERATOR_TRIP', { station_id: activeStation }).catch(() => {});
      showToast('Wind Turbine #2 shear trip: BESS stepped in to absorb microgrid load.');
    }
  };

  const isKatabatic = activeCrisis === 'BLIZZARD_WARNING' || activeCrisis?.includes('BLIZZARD');
  const isGeomag = activeCrisis === 'SOLAR_STORM' || activeCrisis?.includes('STORM');
  const isShear = activeCrisis === 'GENERATOR_TRIP';

  // Dynamic calculations
  const displayPower = isShear ? '118.2' : (snapshot?.kpis?.total_load_kw?.toFixed(1) ?? currentData.defaultPower);
  const displayTemp = isKatabatic ? '+19.2' : currentData.defaultTemp;
  const displayAmb = isKatabatic ? '-56.4°C' : currentData.defaultAmb;
  const displayWind = isKatabatic ? 'Wind 76 kt' : currentData.defaultWind;
  const displayGlycol = isShear ? '380' : currentData.defaultGlycol;

  const setpointBarWidth = Math.min(100, Math.max(25, (setpoint - 15) * 8 + 30));

  return (
    <div className="w-full space-y-4">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-16 right-6 z-50 bg-[#0d1c2f] text-white px-3.5 py-2 rounded-lg text-xs font-mono shadow-xl border border-white/20 animate-fade-in flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 1. TACTICAL FLIGHT BAR (Minimal Header) */}
      <section className="bg-white border border-[#eaebf0] rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
        {/* Active Station Specific Coordinates & Geographic Depth */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] pulse-emerald" />
            <span className="font-display text-sm font-bold text-[#0d1c2f] tracking-wide">
              {currentData.name}
            </span>
          </div>
          <span className="text-[#c6c5d7]">|</span>
          <div className="flex items-center gap-3 text-[#464554] text-[11px] font-mono">
            <span>COORDS: {currentData.coords}</span>
            <span className="hidden sm:inline">
              REGION: <strong className="text-[#0d1c2f]">{currentData.region}</strong>
            </span>
            <span className="hidden md:inline">
              ELEV: <strong className="text-[#0d1c2f]">{currentData.elev}</strong>
            </span>
            <span className="hidden lg:inline">
              POLE DIST: <strong className="text-[#0d1c2f]">{currentData.poleDist}</strong>
            </span>
          </div>
        </div>

        {/* Autonomous Consensus & Tactical Quick Action */}
        <div className="flex items-center gap-2">
          <div 
            onClick={onOpenAgents}
            className="cursor-pointer flex items-center gap-1.5 bg-[#4648d4]/10 border border-[#4648d4]/20 px-2.5 py-1 rounded text-[#2c2abc] hover:bg-[#4648d4]/15 transition-colors"
            title="Inspect 10-Agent Cognitive Society"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span className="text-[10px] font-mono font-bold tracking-tight">
              AUTO-CONSENSUS [10/10 AGENTS]
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 bg-[#f8f9ff] border border-[#eaebf0] px-2.5 py-1 rounded text-[#0d1c2f]">
            <Radio className="w-3.5 h-3.5 text-[#006577]" />
            <span className="text-[10px] font-mono font-medium">
              STARLINK POLAR 42ms // 99.8% LOCK
            </span>
          </div>

          <button
            onClick={() => {
              const next = !tacticalOverride;
              setTacticalOverride(next);
              showToast(next ? 'TACTICAL OVERRIDE ARMED // Direct telemetry control active' : 'Tactical override disarmed // Returned to AI consensus');
            }}
            className={`px-3 py-1 rounded text-[10px] font-mono font-bold transition-all flex items-center gap-1 shadow-2xs ${
              tacticalOverride 
                ? 'bg-[#ba1a1a] text-white animate-pulse' 
                : 'bg-[#4648d4] text-white hover:bg-[#3537b8]'
            }`}
          >
            <Shield className="w-3 h-3" />
            <span>{tacticalOverride ? 'OVERRIDE ARMED' : 'TACTICAL OVERRIDE'}</span>
          </button>
        </div>
      </section>

      {/* 2. 4-METRIC SLEEK TELEMETRY RAIL */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Card 1: Power & Hybrid Microgrid */}
        <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#4648d4]/60 transition-colors shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono font-semibold text-[#767586] flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
              <span>HYBRID MICROGRID</span>
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold border ${
              isShear 
                ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]' 
                : 'bg-[#6cf8bb]/20 text-[#006c49] border-[#006c49]/30'
            }`}>
              {isShear ? 'BESS COMPENSATING' : 'NOMINAL 50.02 Hz'}
            </span>
          </div>
          <div className="my-1.5">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-mono font-bold text-[#0d1c2f] tabular-nums tracking-tight">
                {displayPower}
              </span>
              <span className="text-xs font-mono text-[#767586] font-medium">kW</span>
            </div>
            <div className="w-full bg-[#f8f9ff] h-1.5 rounded-full overflow-hidden mt-1.5 border border-[#eaebf0]">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${isShear ? 'bg-[#ba1a1a]' : 'bg-[#4648d4]'}`} 
                style={{ width: `${currentData.powerBar}%` }} 
              />
            </div>
          </div>
          <div className="flex justify-between items-center text-[#767586] text-[10px] font-mono pt-1.5 border-t border-[#eaebf0]">
            <span>Diesel: 90kW</span>
            <span>Wind: 58.4kW</span>
            <span className="text-[#4648d4] font-semibold">BESS 240 kWh</span>
          </div>
        </div>

        {/* Card 2: Living Habitat Core Thermal */}
        <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#4648d4]/60 transition-colors shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono font-semibold text-[#767586] flex items-center gap-1.5">
              <Thermometer className="w-3.5 h-3.5 text-[#006c49]" />
              <span>HABITAT THERMAL</span>
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#6cf8bb]/20 text-[#006c49] border border-[#006c49]/30">
              DELTA +64.2°C
            </span>
          </div>
          <div className="my-1.5">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-mono font-bold text-[#0d1c2f] tabular-nums tracking-tight">
                {displayTemp}
              </span>
              <span className="text-xs font-mono text-[#767586] font-medium">°C CORE</span>
            </div>
            <div className="w-full bg-[#f8f9ff] h-1.5 rounded-full overflow-hidden mt-1.5 border border-[#eaebf0]">
              <div 
                className="bg-[#10b981] h-full rounded-full transition-all duration-500" 
                style={{ width: `${currentData.tempBar}%` }} 
              />
            </div>
          </div>
          <div className="flex justify-between items-center text-[#767586] text-[10px] font-mono pt-1.5 border-t border-[#eaebf0]">
            <span>Ambient: <strong className="text-[#0d1c2f]">{displayAmb}</strong></span>
            <span className="text-[#006577] font-semibold">{displayWind}</span>
          </div>
        </div>

        {/* Card 3: Utilidor Glycol Conduit */}
        <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#4648d4]/60 transition-colors shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono font-semibold text-[#767586] flex items-center gap-1.5">
              <Droplet className="w-3.5 h-3.5 text-[#006577]" />
              <span>UTILIDOR CONDUIT</span>
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#6cf8bb]/20 text-[#006c49] border border-[#006c49]/30">
              FREEZE RISK 0.0%
            </span>
          </div>
          <div className="my-1.5">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-mono font-bold text-[#0d1c2f] tabular-nums tracking-tight">
                {displayGlycol}
              </span>
              <span className="text-xs font-mono text-[#767586] font-medium">L/min FLOW</span>
            </div>
            <div className="w-full bg-[#f8f9ff] h-1.5 rounded-full overflow-hidden mt-1.5 border border-[#eaebf0]">
              <div className="bg-[#006577] h-full rounded-full transition-all duration-500" style={{ width: '85%' }} />
            </div>
          </div>
          <div className="flex justify-between items-center text-[#767586] text-[10px] font-mono pt-1.5 border-t border-[#eaebf0]">
            <span>Velocity: 2.4 m/s</span>
            <span>Supply: +62°C</span>
            <span className="text-[#006c49] font-semibold">Loop OK</span>
          </div>
        </div>

        {/* Card 4: Autonomous Polar Reserves */}
        <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 flex flex-col justify-between hover:border-[#4648d4]/60 transition-colors shadow-2xs">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-mono font-semibold text-[#767586] flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-[#4648d4]" />
              <span>AUTONOMOUS BUFFER</span>
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#4648d4]/10 text-[#2c2abc] border border-[#4648d4]/20">
              WINTERING SAFE
            </span>
          </div>
          <div className="my-1.5">
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-mono font-bold text-[#0d1c2f] tabular-nums tracking-tight">
                {currentData.defaultDays}
              </span>
              <span className="text-xs font-mono text-[#767586] font-medium">POLAR DAYS</span>
            </div>
            <div className="w-full bg-[#f8f9ff] h-1.5 rounded-full overflow-hidden mt-1.5 border border-[#eaebf0]">
              <div className="bg-[#10b981] h-full rounded-full" style={{ width: '77%' }} />
            </div>
          </div>
          <div className="flex justify-between items-center text-[#767586] text-[10px] font-mono pt-1.5 border-t border-[#eaebf0]">
            <span>Fuel: 210,000 L</span>
            <span>RO Water: 42k L</span>
            <span className="text-[#0d1c2f] font-semibold">Crew: 24</span>
          </div>
        </div>
      </section>

      {/* 3. CENTRAL VISUALIZER CORE: CIRCULAR RADAR & MULTI-VECTOR COCKPIT */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Polar Radar & Sonar Vector Engine (8 Cols) */}
        <div className="lg:col-span-8 bg-white border border-[#eaebf0] rounded-xl p-4 flex flex-col relative overflow-hidden shadow-2xs">
          {/* Card Header With Vector Diagnostics */}
          <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
            <div className="flex items-center gap-2">
              <Compass className="w-5 h-5 text-[#4648d4]" />
              <span className="font-display text-sm font-bold text-[#0d1c2f] tracking-wide">
                POLAR RANGE VECTOR // LIVE CRYOSPHERIC SWEEP
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-[#767586]">RANGE: 350 KM</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#f8f9ff] text-[#4648d4] border border-[#eaebf0]">
                AZIMUTH 184.2° S
              </span>
            </div>
          </div>

          {/* Radar Core Display Canvas */}
          <div className="relative flex-1 flex items-center justify-center my-4 min-h-[350px]">
            {/* Radar Circular Visualizer with Rings */}
            <div className="relative w-[310px] h-[310px] sm:w-[380px] sm:h-[380px] rounded-full border border-[#eaebf0] flex items-center justify-center bg-[#faf8ff]/80">
              {/* Concentric Range Latitude Rings */}
              <div className="absolute inset-[12%] rounded-full border border-[#eaebf0]" />
              <div className="absolute inset-[28%] rounded-full border border-[#eaebf0]" />
              <div className="absolute inset-[44%] rounded-full border border-[#eaebf0]" />
              <div className="absolute inset-[60%] rounded-full border border-[#4648d4]/20" />

              {/* Cardinal Axes */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-full h-[1px] bg-[#eaebf0]" />
              </div>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="h-full w-[1px] bg-[#eaebf0]" />
              </div>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none rotate-45">
                <div className="w-full h-[1px] bg-[#eaebf0]/50" />
              </div>
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none -rotate-45">
                <div className="w-full h-[1px] bg-[#eaebf0]/50" />
              </div>

              {/* Latitude Markings */}
              <span className="absolute top-2 font-mono text-[9px] text-[#767586]">60°S [POLAR FRONT]</span>
              <span className="absolute top-[14%] font-mono text-[8px] text-[#767586]">70°S [CONTINENTAL MARGIN]</span>
              <span className="absolute top-[30%] font-mono text-[8px] text-[#767586]">80°S [INLAND PLATEAU]</span>
              <span className="absolute bottom-2 font-mono text-[9px] text-[#767586]">SOUTH POLE 90°S</span>

              {/* Sweeping Radar Beam Arm */}
              <div className="absolute inset-0 rounded-full overflow-hidden pointer-events-none">
                <div 
                  className="w-full h-full radar-sweep-arm" 
                  style={{
                    background: 'conic-gradient(from 0deg at 50% 50%, rgba(70, 72, 212, 0.22) 0deg, rgba(70, 72, 212, 0.0) 55deg, transparent 55deg)'
                  }} 
                />
              </div>

              {/* Central South Pole Coordinate Hub */}
              <div className="w-8 h-8 rounded-full bg-white border border-[#4648d4] flex items-center justify-center z-10 shadow-xs">
                <div className="w-2 h-2 rounded-full bg-[#4648d4] status-pulse" />
              </div>

              {/* Interactive Station Plot Points */}
              {/* Bharati Station Node */}
              <div 
                onClick={() => {
                  onStationChange('bharati');
                  showToast('Radar focused on BHARATI BASE (Larsemann Hills)');
                }}
                className={`absolute top-[28%] right-[22%] z-20 flex flex-col items-center cursor-pointer transition-transform hover:scale-110 ${
                  activeStation === 'bharati' ? 'scale-105' : 'opacity-85'
                }`}
                title="Click to focus Bharati Station"
              >
                <div className={`w-4 h-4 rounded-full border-2 border-white shadow-sm flex items-center justify-center ${
                  activeStation === 'bharati' ? 'bg-[#4648d4]' : 'bg-[#767586]'
                }`}>
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                </div>
                <div className={`mt-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold shadow-2xs border ${
                  activeStation === 'bharati'
                    ? 'bg-white border-[#4648d4] text-[#2c2abc]'
                    : 'bg-white border-[#eaebf0] text-[#767586]'
                }`}>
                  BHARATI {activeStation === 'bharati' ? '[ACTIVE]' : ''}
                </div>
              </div>

              {/* Maitri Station Node */}
              <div 
                onClick={() => {
                  onStationChange('maitri');
                  showToast('Radar focused on MAITRI BASE (Schirmacher Oasis)');
                }}
                className={`absolute top-[26%] left-[24%] z-20 flex flex-col items-center cursor-pointer transition-transform hover:scale-110 ${
                  activeStation === 'maitri' ? 'scale-105' : 'opacity-85'
                }`}
                title="Click to focus Maitri Station"
              >
                <div className={`w-4 h-4 rounded-full border-2 border-white shadow-sm flex items-center justify-center ${
                  activeStation === 'maitri' ? 'bg-[#4648d4]' : 'bg-[#767586]'
                }`}>
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                </div>
                <div className={`mt-1 px-1.5 py-0.5 rounded text-[9px] font-mono font-bold shadow-2xs border ${
                  activeStation === 'maitri'
                    ? 'bg-white border-[#4648d4] text-[#2c2abc]'
                    : 'bg-white border-[#eaebf0] text-[#767586]'
                }`}>
                  MAITRI {activeStation === 'maitri' ? '[ACTIVE]' : ''}
                </div>
              </div>

              {/* Floating Dynamic Telemetry Badges */}
              <div className="absolute bottom-[18%] left-[6%] bg-white/95 border border-[#eaebf0] rounded p-1.5 text-left pointer-events-none shadow-2xs">
                <div className="text-[8px] font-mono text-[#767586]">KATABATIC VORTEX</div>
                <div className="text-[11px] font-mono font-bold text-[#006577]">
                  {isKatabatic ? '78 KT // GALE FORCE SE' : '34 KT // NE BEARING'}
                </div>
              </div>
              <div className="absolute bottom-[20%] right-[8%] bg-white/95 border border-[#eaebf0] rounded p-1.5 text-right pointer-events-none shadow-2xs">
                <div className="text-[8px] font-mono text-[#767586]">IONOSPHERIC KP</div>
                <div className={`text-[11px] font-mono font-bold ${isGeomag ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
                  {isGeomag ? 'KP-8.2 SEVERE FLUX' : 'KP-1.8 QUIET'}
                </div>
              </div>
            </div>
          </div>

          {/* Tactile Disturbance & Simulation Triggers directly in Hero */}
          <div className="pt-3 border-t border-[#eaebf0]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-[#767586] font-semibold flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>INJECT REAL-TIME ENVIRONMENTAL DISTURBANCE:</span>
              </span>
              <span className={`text-[10px] font-mono font-bold ${
                activeCrisis ? 'text-[#ba1a1a]' : 'text-[#006c49]'
              }`}>
                ACTIVE: {activeCrisis ? activeCrisis.toUpperCase() : 'NOMINAL OPS'}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                onClick={() => handleScenario('NOMINAL')}
                className={`py-1.5 px-2 rounded text-[10px] font-mono font-bold transition-all flex items-center justify-center gap-1.5 border shadow-2xs ${
                  !activeCrisis
                    ? 'border-[#006c49] bg-[#6cf8bb]/20 text-[#006c49]'
                    : 'border-[#eaebf0] bg-[#f8f9ff] text-[#464554] hover:bg-[#eaedff]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${!activeCrisis ? 'bg-[#10b981]' : 'bg-[#c6c5d7]'}`} />
                <span>NORMAL OPS</span>
              </button>

              <button
                onClick={() => handleScenario('KATABATIC')}
                className={`py-1.5 px-2 rounded text-[10px] font-mono font-bold transition-all flex items-center justify-center gap-1.5 border shadow-2xs ${
                  isKatabatic
                    ? 'border-[#ba1a1a] bg-[#ffdad6] text-[#ba1a1a]'
                    : 'border-[#eaebf0] bg-[#f8f9ff] text-[#464554] hover:bg-[#eaedff]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isKatabatic ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
                <span>KATABATIC GALE</span>
              </button>

              <button
                onClick={() => handleScenario('GEOMAG')}
                className={`py-1.5 px-2 rounded text-[10px] font-mono font-bold transition-all flex items-center justify-center gap-1.5 border shadow-2xs ${
                  isGeomag
                    ? 'border-[#ba1a1a] bg-[#ffdad6] text-[#ba1a1a]'
                    : 'border-[#eaebf0] bg-[#f8f9ff] text-[#464554] hover:bg-[#eaedff]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isGeomag ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
                <span>KP-8 GEOMAG</span>
              </button>

              <button
                onClick={() => handleScenario('TURBINE_SHEAR')}
                className={`py-1.5 px-2 rounded text-[10px] font-mono font-bold transition-all flex items-center justify-center gap-1.5 border shadow-2xs ${
                  isShear
                    ? 'border-[#ba1a1a] bg-[#ffdad6] text-[#ba1a1a]'
                    : 'border-[#eaebf0] bg-[#f8f9ff] text-[#464554] hover:bg-[#eaedff]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${isShear ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
                <span>TURBINE #2 SHEAR</span>
              </button>
            </div>
          </div>
        </div>

        {/* Telemetry Multi-Vector Cockpit & AI Consensus Rail (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col space-y-3">
          {/* Autonomous Multi-Agent Consensus Stream */}
          <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 flex flex-col flex-1 shadow-2xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#eaebf0]">
              <div className="flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-[#4648d4]" />
                <span className="font-display text-xs font-bold text-[#0d1c2f]">AGENT CONSENSUS</span>
              </div>
              <span className="text-[10px] font-mono font-bold text-[#006c49]">10/10 SYNCHRONIZED</span>
            </div>

            {/* Agent Micro-Logs */}
            <div className="space-y-2 overflow-y-auto max-h-[190px] pr-1">
              <div className="p-2 rounded bg-[#f8f9ff] border border-[#eaebf0] flex items-start gap-2">
                <Zap className="w-3.5 h-3.5 text-[#4648d4] shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <strong className="text-[#0d1c2f]">AG-01 // POWER DISPATCH</strong>
                    <span className="text-[#767586]">0.12s ago</span>
                  </div>
                  <p className="text-[11px] font-sans text-[#464554] mt-0.5 leading-snug">
                    Wind turbine surplus +18kW diverted to thermal storage tank #2.
                  </p>
                </div>
              </div>

              <div className="p-2 rounded bg-[#f8f9ff] border border-[#eaebf0] flex items-start gap-2">
                <Thermometer className="w-3.5 h-3.5 text-[#006c49] shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <strong className="text-[#0d1c2f]">AG-04 // HVAC THERMAL</strong>
                    <span className="text-[#767586]">0.45s ago</span>
                  </div>
                  <p className="text-[11px] font-sans text-[#464554] mt-0.5 leading-snug">
                    Living Module A damper positioned at 38% recirculation to optimize delta.
                  </p>
                </div>
              </div>

              <div className="p-2 rounded bg-[#f8f9ff] border border-[#eaebf0] flex items-start gap-2">
                <Radio className="w-3.5 h-3.5 text-[#006577] shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex justify-between items-center text-[10px] font-mono">
                    <strong className="text-[#0d1c2f]">AG-09 // COMMS MESH</strong>
                    <span className="text-[#767586]">1.10s ago</span>
                  </div>
                  <p className="text-[11px] font-sans text-[#464554] mt-0.5 leading-snug">
                    X-Band ground station pointing matrix aligned to Bharati-Maitri link.
                  </p>
                </div>
              </div>
            </div>

            {/* Setpoint Adjuster Bar */}
            <div className="mt-3 pt-2 border-t border-[#eaebf0]">
              <div className="flex items-center justify-between text-[#767586] text-[10px] font-mono mb-1.5">
                <span>HABITAT CLIMATE SETPOINT</span>
                <span className="text-xs font-mono font-bold text-[#4648d4]">{setpoint.toFixed(1)}°C</span>
              </div>
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => adjustSetpoint(-0.5)}
                  className="w-6 h-6 flex items-center justify-center bg-[#f8f9ff] border border-[#eaebf0] rounded text-xs font-mono font-bold hover:bg-[#eaedff] transition-colors"
                >
                  -
                </button>
                <div className="flex-1 bg-[#f8f9ff] h-2 rounded-full overflow-hidden border border-[#eaebf0]">
                  <div 
                    className="bg-[#4648d4] h-full transition-all duration-300" 
                    style={{ width: `${setpointBarWidth}%` }} 
                  />
                </div>
                <button 
                  onClick={() => adjustSetpoint(0.5)}
                  className="w-6 h-6 flex items-center justify-center bg-[#f8f9ff] border border-[#eaebf0] rounded text-xs font-mono font-bold hover:bg-[#eaedff] transition-colors"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Polar Satellite Mesh Matrix Tile */}
          <div className="bg-white border border-[#eaebf0] rounded-xl p-3.5 shadow-2xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#eaebf0]">
              <span className="text-[10px] font-mono text-[#767586] font-semibold">ORBITAL UPLINK CHANNELS</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#6cf8bb]/20 text-[#006c49]">
                POLAR MESH 1.2 GBPS
              </span>
            </div>
            <div className="space-y-1.5 text-[11px] font-mono">
              <div className="flex justify-between items-center">
                <span className="text-[#0d1c2f]">Ka-Band Polar Sat-04</span>
                <span className="text-[#006c49] font-bold">SNR 22.4 dB (LOCKED)</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#0d1c2f]">Maitri Inter-Station Link</span>
                <span className="text-[#006577] font-bold">LOS Microwave 98%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#0d1c2f]">Iridium Extreme Backup</span>
                <span className="text-[#767586]">HOT STANDBY</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. BASE STATUS FOOTER TICKER */}
      <footer className="bg-white border border-[#eaebf0] rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-2 text-[#767586] text-[11px] font-mono shadow-2xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#10b981]" />
            <strong className="text-[#0d1c2f]">LIFE SUPPORT INTEGRITY: 100%</strong>
          </span>
          <span className="text-[#c6c5d7]">|</span>
          <span>DIESEL FUEL DEPOT: 88.4% CAP</span>
          <span className="text-[#c6c5d7] hidden sm:inline">|</span>
          <span className="hidden sm:inline">FRESH WATER ICE-MELT: 420 L/HR</span>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span>SIH 2026 RESEARCH TEAM</span>
          <span className="px-1.5 py-0.5 rounded bg-[#f8f9ff] border border-[#eaebf0] text-[#0d1c2f] font-bold">
            NCAOR / MoES POLAR COMMAND
          </span>
        </div>
      </footer>
    </div>
  );
};
