import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Thermometer, 
  Wind, 
  Radio, 
  ShieldCheck, 
  AlertTriangle, 
  Activity, 
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
  CloudSnow, 
  X,
  ExternalLink,
  ChevronRight,
  Flame,
  Radar,
  Sliders,
  Send,
  Lock,
  Compass
} from 'lucide-react';
import { StationId, StationSnapshot, StationInfo, SpaceWeatherMetrics, PolarWeatherObservation } from '../../types';
import { 
  fetchSpaceWeatherCurrent, 
  fetchPolarWeatherCurrent, 
  injectScenario, 
  clearScenario, 
  simulatePolarBlizzard,
  simulateGeomagneticStorm
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

interface ToastNotification {
  id: string;
  title: string;
  desc: string;
  type: 'info' | 'warn' | 'error' | 'success';
}

interface ConsensusLogEntry {
  id: string;
  timestamp: string;
  agent: string;
  directive: string;
  voteRatio: string;
  isAlert?: boolean;
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
  // Environmental telemetry states
  const [spaceWeather, setSpaceWeather] = useState<SpaceWeatherMetrics | null>(null);
  const [polarWeather, setPolarWeather] = useState<PolarWeatherObservation | null>(null);

  // Interactive Subsystem States
  const [o2ValveOpen, setO2ValveOpen] = useState<boolean>(false);
  const [gridLogicAuto, setGridLogicAuto] = useState<boolean>(true);
  const [dewarVenting, setDewarVenting] = useState<boolean>(false);
  const [sounderPulsing, setSounderPulsing] = useState<boolean>(false);

  // Toast System
  const [toasts, setToasts] = useState<ToastNotification[]>([]);

  // Consensus log feed
  const [consensusLogs, setConsensusLogs] = useState<ConsensusLogEntry[]>([
    {
      id: 'log-1',
      timestamp: '14:28:07.8',
      agent: 'THERMAL-GOV',
      directive: 'Rebalancing Hab Core Loop B heat exchange (+0.4°C step for ambient offset)',
      voteRatio: 'CONSENSUS 10/10'
    },
    {
      id: 'log-2',
      timestamp: '14:27:54.2',
      agent: 'GRID-BALANCER',
      directive: 'Diverting 12kW wind peak surplus to Thermal Energy Storage bank #3',
      voteRatio: 'CONSENSUS 10/10'
    },
    {
      id: 'log-3',
      timestamp: '14:27:32.1',
      agent: 'OXYGEN-CYCLE',
      directive: 'CO2 scrub loop cycle synchronized with crew circadian sleep schedule',
      voteRatio: 'CONSENSUS 9/10'
    },
    {
      id: 'log-4',
      timestamp: '14:27:18.9',
      agent: 'WATER-LOOP',
      directive: 'Utilidor Trace Heater #4 impedance nominal; flow 18.2 L/m continuous',
      voteRatio: 'CONSENSUS 10/10'
    },
    {
      id: 'log-5',
      timestamp: '14:27:01.4',
      agent: 'SATELLITE-COMM',
      directive: 'LEO satellite pass azimuth 142° acquired; polar mesh handover latency 38ms',
      voteRatio: 'CONSENSUS 10/10'
    }
  ]);

  const addToast = (title: string, desc: string, type: 'info' | 'warn' | 'error' | 'success' = 'info') => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { id, title, desc, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

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
    const interval = setInterval(loadWeather, 4000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // Handlers for interactive controls
  const handleToggleO2 = () => {
    const next = !o2ValveOpen;
    setO2ValveOpen(next);
    if (next) {
      addToast('OXYGEN INJECTION OPEN', 'Auxiliary O2 enrichment loop active (+1.2 L/min). CO2 scrubbing accelerated.', 'success');
    } else {
      addToast('OXYGEN INJECTION SECURED', 'Auxiliary O2 loop isolated to nominal baseload recirculation.', 'info');
    }
  };

  const handleToggleGridLogic = () => {
    const next = !gridLogicAuto;
    setGridLogicAuto(next);
    if (next) {
      addToast('GRID LOGIC: AUTO', 'Dynamic microgrid peak-shaving & frequency stabilization active.', 'success');
    } else {
      addToast('GRID LOGIC: FIXED', 'Grid dispatch held at static baseload setpoints. Fast peak-shaving disabled.', 'warn');
    }
  };

  const handleVentDewar = () => {
    if (dewarVenting) return;
    setDewarVenting(true);
    addToast('CRYO VENTING INITIATED', 'Mass Spectrometry LN2 Dewar pressure purge active (0.2 bar/s).', 'info');
    setTimeout(() => {
      setDewarVenting(false);
      addToast('CRYO VENT ISOLATED', 'Dewar purge completed. Cryogenic pressure stabilized at 1.4 bar.', 'success');
    }, 4000);
  };

  const handlePingSounder = () => {
    if (sounderPulsing) return;
    setSounderPulsing(true);
    addToast('IONOSPHERIC RADAR PULSE', 'Transmitting 12.4 MHz iono-sounder RF sweep across D/E/F layers.', 'info');
    setTimeout(() => {
      setSounderPulsing(false);
      addToast('IONO-SOUNDER CALIBRATED', 'Reflection vector mapped to Twin-D Atmospheric array with 99.8% SNR.', 'success');
    }, 3000);
  };

  // Scenario Injections
  const handleTriggerScenario = async (type: string) => {
    const now = new Date();
    const timeStr = `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')}`;

    if (type === 'GALE') {
      onInjectCrisis('BLIZZARD_WARNING');
      await simulatePolarBlizzard('CONDITION_1_LOCKOUT').catch(() => {});
      addToast('KATABATIC GALE INJECTED', 'Wind velocity spiked to 41.8 m/s (150 km/h). Structural dampers armed.', 'warn');
      setConsensusLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          timestamp: timeStr,
          agent: 'HAZARD-WATCH',
          directive: 'Locking turbine pitch angles to 45° aerodynamic brake; feathering blades to resist 150 km/h shock',
          voteRatio: 'CONSENSUS 10/10',
          isAlert: true
        },
        ...prev
      ]);
    } else if (type === 'SPACE_STORM') {
      onInjectCrisis('SOLAR_STORM');
      await simulateGeomagneticStorm('G4').catch(() => {});
      addToast('SPACE WEATHER ALERT', 'Kp 8.2 Severe Geomagnetic Storm. Polar HF communications blackout imminent.', 'error');
      setConsensusLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          timestamp: timeStr,
          agent: 'SATELLITE-COMM',
          directive: 'Switching ground-station telemetry uplink to optical sub-ice fiber link due to ionospheric HF absorption',
          voteRatio: 'CONSENSUS 10/10',
          isAlert: true
        },
        ...prev
      ]);
    } else if (type === 'GEN_TRIP') {
      onInjectCrisis('GENERATOR_TRIP');
      await injectScenario('GENERATOR_TRIP', { station_id: activeStation }).catch(() => {});
      addToast('GENERATOR TRIP INJECTED', 'Primary Diesel Gen-Set 1 tripped. BESS battery bank stepped to 98kW load.', 'error');
      setConsensusLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          timestamp: timeStr,
          agent: 'GRID-BALANCER',
          directive: 'Autonomous microgrid failover triggered: BESS stepped to 98kW; dispatching cold-start command to Gen-Set #2',
          voteRatio: 'CONSENSUS 10/10',
          isAlert: true
        },
        ...prev
      ]);
    } else if (type === 'FREEZE') {
      onInjectCrisis('THERMAL_COLLAPSE');
      await injectScenario('THERMAL_COLLAPSE', { station_id: activeStation }).catch(() => {});
      addToast('UTILIDOR FREEZE HAZARD', 'Utilidor conduit 4 showing flow drop. Secondary heat trace firing at 48kW.', 'warn');
      setConsensusLogs((prev) => [
        {
          id: `log-${Date.now()}`,
          timestamp: timeStr,
          agent: 'WATER-LOOP',
          directive: 'Throttling auxiliary booster pump #2 to 100%; pulsing 48kW pulsed heat trace to clear cryo-slush plug',
          voteRatio: 'CONSENSUS 10/10',
          isAlert: true
        },
        ...prev
      ]);
    }
  };

  const handleResetBaseline = async () => {
    onResetCrisis();
    await clearScenario(activeStation).catch(() => {});
    addToast('SIMULATION RESET', 'All physical subsystems and telemetry returned to Antarctic baseline equilibrium.', 'success');
  };

  // Derive dynamic telemetry values based on active scenario or live backend snapshot
  const isGale = activeCrisis === 'BLIZZARD_WARNING' || activeCrisis?.includes('BLIZZARD');
  const isSpaceStorm = activeCrisis === 'SOLAR_STORM' || activeCrisis?.includes('STORM');
  const isGenTrip = activeCrisis === 'GENERATOR_TRIP';
  const isFreeze = activeCrisis === 'THERMAL_COLLAPSE' || activeCrisis?.includes('FREEZE');

  // Pillar 1: Grid Load
  const gridLoadKw = isGenTrip ? 162.0 : (snapshot?.kpis?.total_load_kw ?? snapshot?.kpis?.station_electrical_load_kw ?? 148.4);
  const gridLoadCap = isGenTrip ? 90 : 82;
  const genSet1Kw = isGenTrip ? 0.0 : 82.0;

  // Pillar 2: Living Core Temp
  const livingTempC = isFreeze ? 14.8 : (snapshot?.kpis?.indoor_avg_temp_c ?? snapshot?.kpis?.indoor_temp_living_c ?? 21.4);
  const co2Ppm = o2ValveOpen ? 380 : 410;

  // Pillar 3: Wind Chill & Ambient
  const windChillC = isGale ? -61.4 : -42.8;
  const windGustSpeed = isGale ? 'Katabatic 41.8 m/s (150 km/h)' : 'Gusts 34.2 m/s SE';

  // Pillar 4: Utilidor Flow
  const utilidorFlow = isFreeze ? 0.8 : 2.4;
  const utilidorRisk = isFreeze ? 'Glycol 180 L/m • Freeze Risk 48.2%' : 'Glycol 420 L/m • Freeze 0.0%';

  // Pillar 5: Fuel Days
  const fuelDays = snapshot?.kpis?.fuel_autonomy_days ?? 284;

  // Space Weather
  const kpVal = isSpaceStorm ? 8.2 : (spaceWeather?.kp_index ?? 2.3);
  const solarWindVal = isSpaceStorm ? 742 : (spaceWeather?.solar_wind_speed_kms ?? 382);
  const hfBlackoutVal = isSpaceStorm ? '94.0%' : '< 1.0%';
  const auroraPowerVal = isSpaceStorm ? '148.0 GW Extreme Auroral Influx' : '14.8 GW Integrated Power';

  // 10-Agent Status List
  const agentNodes = [
    { name: 'THERMAL-GOV', vote: 'AGREE', status: isFreeze ? 'CRITICAL ADJUST' : 'NOMINAL' },
    { name: 'GRID-BALANCER', vote: 'AGREE', status: isGenTrip ? 'DISPATCH FAILOVER' : 'NOMINAL' },
    { name: 'OXYGEN-CYCLE', vote: o2ValveOpen ? 'AUX-ACTIVE' : 'AGREE', status: 'NOMINAL' },
    { name: 'WATER-LOOP', vote: 'AGREE', status: isFreeze ? 'TRACE HEAT ENGAGED' : 'NOMINAL' },
    { name: 'SATELLITE-COMM', vote: 'AGREE', status: isSpaceStorm ? 'OPTICAL FALLBACK' : 'NOMINAL' },
    { name: 'DRONE-SURVEY', vote: 'AGREE', status: isGale ? 'GROUNDED LOCK' : 'NOMINAL' },
    { name: 'CRYO-KEEPER', vote: 'AGREE', status: dewarVenting ? 'VENTING REGIME' : 'NOMINAL' },
    { name: 'FUEL-OPTIMIZER', vote: 'AGREE', status: 'NOMINAL' },
    { name: 'PERIMETER-RADAR', vote: 'AGREE', status: sounderPulsing ? 'PULSING SWEEP' : 'NOMINAL' },
    { name: 'HAZARD-WATCH', vote: 'AGREE', status: activeCrisis ? 'TACTICAL ALERT' : 'NOMINAL' },
  ];

  return (
    <div className="space-y-6 pb-28">
      {/* Toast Notification Layer */}
      <div className="fixed top-16 right-6 z-50 pointer-events-none space-y-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto bg-white border ${
              toast.type === 'error' 
                ? 'border-[#ba1a1a] text-[#ba1a1a]' 
                : toast.type === 'warn' 
                ? 'border-[#f59e0b] text-[#b45309]' 
                : toast.type === 'success'
                ? 'border-[#10b981] text-[#006c49]'
                : 'border-[#4648d4] text-[#2c2abc]'
            } p-3 rounded-md shadow-md flex items-start gap-3 transition-all min-w-[300px] max-w-sm`}
          >
            <div className="mt-0.5">
              {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-[#ba1a1a]" />}
              {toast.type === 'warn' && <AlertTriangle className="w-4 h-4 text-[#b45309]" />}
              {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-[#006c49]" />}
              {toast.type === 'info' && <Activity className="w-4 h-4 text-[#4648d4]" />}
            </div>
            <div className="flex-1">
              <div className="text-[10px] font-mono font-bold tracking-wide">{toast.title}</div>
              <div className="text-xs font-sans text-[#0d1c2f] mt-0.5 leading-snug">{toast.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ================= SECTION 1: 6-PILLAR MICRO-TELEMETRY MATRIX ================= */}
      <section className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3" id="overview">
        {/* Pillar 1: GRID LOAD */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">GRID LOAD</span>
            <span className={`w-2 h-2 rounded-full ${isGenTrip ? 'bg-[#ba1a1a] animate-pulse' : 'bg-[#10b981]'}`} />
          </div>
          <div className="my-2">
            <div className="text-xl font-mono font-bold text-[#0d1c2f] tracking-tight tabular-nums">
              {gridLoadKw.toFixed(1)} <span className="text-xs font-normal text-[#767586]">kW</span>
            </div>
            <div className={`text-[11px] font-mono font-medium mt-0.5 ${isGenTrip ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
              {gridLoadCap}% Cap • {isGenTrip ? 'BESS Primary' : '+2.1kW flux'}
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-300 ${isGenTrip ? 'bg-[#ba1a1a]' : 'bg-[#4648d4]'}`} 
                style={{ width: `${gridLoadCap}%` }} 
              />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>HYBRID BESS</span>
              <span>180 kW MAX</span>
            </div>
          </div>
        </div>

        {/* Pillar 2: LIVING CORE TEMP */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">LIVING CORE TEMP</span>
            <span className={`w-2 h-2 rounded-full ${isFreeze ? 'bg-[#ba1a1a] animate-pulse' : 'bg-[#10b981]'}`} />
          </div>
          <div className="my-2">
            <div className="text-xl font-mono font-bold text-[#0d1c2f] tracking-tight tabular-nums">
              +{livingTempC.toFixed(1)} <span className="text-xs font-normal text-[#767586]">°C</span>
            </div>
            <div className="text-[11px] font-mono text-[#767586] mt-0.5">
              Setpoint 22.0°C (Δ {(22.0 - livingTempC).toFixed(1)})
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-300 ${isFreeze ? 'bg-[#ba1a1a]' : 'bg-[#10b981]'}`} 
                style={{ width: `${Math.min(100, Math.max(20, (livingTempC / 25) * 100))}%` }} 
              />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>HAB A/B WING</span>
              <span>THERMAL BAL</span>
            </div>
          </div>
        </div>

        {/* Pillar 3: WIND CHILL / AMBIENT */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">WIND CHILL / AMB</span>
            <span className={`w-2 h-2 rounded-full ${isGale ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#f59e0b] pip-amber-pulse'}`} />
          </div>
          <div className="my-2">
            <div className={`text-xl font-mono font-bold tracking-tight tabular-nums ${isGale ? 'text-[#ba1a1a]' : 'text-[#4648d4]'}`}>
              {windChillC.toFixed(1)} <span className="text-xs font-normal text-[#767586]">°C</span>
            </div>
            <div className={`text-[11px] font-mono font-medium truncate mt-0.5 ${isGale ? 'text-[#ba1a1a]' : 'text-[#b45309]'}`}>
              {windGustSpeed}
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-300 ${isGale ? 'bg-[#ba1a1a]' : 'bg-[#f59e0b]'}`} 
                style={{ width: isGale ? '96%' : '68%' }} 
              />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>AMB -28.2°C</span>
              <span>{isGale ? 'KATABATIC GALE' : 'KATABATIC MOD'}</span>
            </div>
          </div>
        </div>

        {/* Pillar 4: UTILIDOR VELOCITY */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">UTILIDOR VELOCITY</span>
            <span className={`w-2 h-2 rounded-full ${isFreeze ? 'bg-[#ba1a1a] animate-pulse' : 'bg-[#10b981]'}`} />
          </div>
          <div className="my-2">
            <div className={`text-xl font-mono font-bold tracking-tight tabular-nums ${isFreeze ? 'text-[#ba1a1a]' : 'text-[#0d1c2f]'}`}>
              {utilidorFlow.toFixed(1)} <span className="text-xs font-normal text-[#767586]">m/s</span>
            </div>
            <div className={`text-[11px] font-mono font-medium mt-0.5 truncate ${isFreeze ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
              {utilidorRisk}
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-300 ${isFreeze ? 'bg-[#ba1a1a]' : 'bg-[#006577]'}`} 
                style={{ width: isFreeze ? '28%' : '58%' }} 
              />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>TRACE ACTIVE</span>
              <span>{isFreeze ? 'RESTRICTED' : 'NOMINAL LOOP'}</span>
            </div>
          </div>
        </div>

        {/* Pillar 5: AUTONOMOUS FUEL DAYS */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">AUTONOMOUS FUEL</span>
            <span className="w-2 h-2 rounded-full bg-[#10b981]" />
          </div>
          <div className="my-2">
            <div className="text-xl font-mono font-bold text-[#0d1c2f] tracking-tight tabular-nums">
              {fuelDays} <span className="text-xs font-normal text-[#767586]">Days</span>
            </div>
            <div className="text-[11px] font-mono text-[#767586] mt-0.5">
              410,000L Bulk Jet-A1
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div className="bg-[#4648d4] h-full rounded-full" style={{ width: '78%' }} />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>POLAR DIESEL</span>
              <span>WINTER SECURE</span>
            </div>
          </div>
        </div>

        {/* Pillar 6: CONSENSUS INTEGRITY */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-3 flex flex-col justify-between hover:border-[#4648d4] transition-colors shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold text-[#767586]">CONSENSUS INTEGRITY</span>
            <span className="w-2 h-2 rounded-full bg-[#10b981] pulse-emerald" />
          </div>
          <div className="my-2">
            <div className="text-xl font-mono font-bold text-[#006c49] tracking-tight tabular-nums">
              10/10 <span className="text-xs font-normal text-[#767586]">Agents</span>
            </div>
            <div className="text-[11px] font-mono text-[#006c49] font-medium mt-0.5">
              99.94% Synced State
            </div>
          </div>
          <div className="space-y-1">
            <div className="w-full bg-[#e6eeff] h-1.5 rounded-full overflow-hidden">
              <div className="bg-[#10b981] h-full rounded-full" style={{ width: '100%' }} />
            </div>
            <div className="flex justify-between text-[9px] font-mono text-[#767586]">
              <span>ZERO ANOMALY</span>
              <span>QUORUM VALID</span>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 2: INTERACTIVE 4-SUBSYSTEM TWIN MATRIX ================= */}
      <section className="space-y-3" id="twins">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[#4648d4]" />
            <h2 className="font-display text-base font-bold text-[#0d1c2f] tracking-wide">
              DIGITAL TWIN ARCHITECTURE // 4 SUB-MATRICES
            </h2>
          </div>
          <div className="text-[10px] font-mono text-[#767586] hidden sm:block">
            POLLING FREQUENCY: <span className="text-[#4648d4] font-bold">250ms</span> // SYNCHRONIZED TO POLAR UTC
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {/* Twin A: LIFE SUPPORT & HABITATION */}
          <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs hover:border-[#4648d4]/60 transition-all">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
                <div className="flex items-center gap-1.5">
                  <Droplet className="w-4 h-4 text-[#006c49]" />
                  <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">TWIN-A: LIFE SUPPORT</span>
                </div>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#6cf8bb]/20 text-[#006c49] font-bold border border-[#006c49]/20">
                  CREW 24 WINTER
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 my-3">
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">O2 SATURATION</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">20.9%</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Norm 20.8 - 21.2</div>
                </div>
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">CO2 SCRUBBERS</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">{co2Ppm} ppm</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Beds A/B active</div>
                </div>
              </div>

              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Graywater Recycling Loop</span>
                  <span className="font-bold text-[#0d1c2f]">94.2% Eff</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Bulkhead Pressure Seal</span>
                  <span className="font-bold text-[#006c49]">101.32 kPa (Intact)</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[#767586]">Airlock Cycle</span>
                  <span className="text-[#0d1c2f] font-medium">Standby / Locked</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between mt-3">
              <span className="text-[9px] font-mono font-bold text-[#767586]">OXYGEN AUX INJECT</span>
              <button
                onClick={handleToggleO2}
                className={`px-2.5 py-1 text-[10px] font-mono font-bold rounded transition-colors shadow-2xs ${
                  o2ValveOpen
                    ? 'bg-[#006c49] text-white'
                    : 'border border-[#eaebf0] hover:border-[#4648d4] bg-white text-[#0d1c2f]'
                }`}
              >
                {o2ValveOpen ? 'VALVE 100% OPEN' : 'VALVE CLOSED'}
              </button>
            </div>
          </div>

          {/* Twin B: POWER MICROGRID & STORAGE */}
          <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs hover:border-[#4648d4]/60 transition-all">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
                <div className="flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-[#4648d4]" />
                  <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">TWIN-B: MICROGRID BESS</span>
                </div>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#4648d4]/10 text-[#2c2abc] font-bold border border-[#4648d4]/20">
                  FREQ 50.02 Hz
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 my-3">
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">GEN-SET #1</div>
                  <div className={`text-sm font-mono font-bold mt-0.5 ${isGenTrip ? 'text-[#ba1a1a]' : 'text-[#0d1c2f]'}`}>
                    {genSet1Kw.toFixed(1)} kW
                  </div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">
                    {isGenTrip ? 'TRIPPED (OFFLINE)' : 'Diesel Gen Prime'}
                  </div>
                </div>
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">WIND ARRAY 1-3</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">48.2 kW</div>
                  <div className="text-[10px] font-mono text-[#4648d4] font-medium">High Blade Efficiency</div>
                </div>
              </div>

              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">BESS 240 kWh Storage</span>
                  <span className="font-bold text-[#006c49]">{isGenTrip ? '87.2% Fast Disch' : '91.4% SoC'}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">DC Bus Stability</span>
                  <span className="font-bold text-[#0d1c2f]">752 V / ±0.4%</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[#767586]">Thermal Dump Resistor</span>
                  <span className="text-[#0d1c2f] font-medium">18.4 kW Diverted</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between mt-3">
              <span className="text-[9px] font-mono font-bold text-[#767586]">PEAK SHAVING LOGIC</span>
              <button
                onClick={handleToggleGridLogic}
                className={`px-2.5 py-1 text-[10px] font-mono font-bold rounded transition-colors shadow-2xs ${
                  gridLogicAuto
                    ? 'bg-[#4648d4] text-white'
                    : 'border border-[#eaebf0] bg-[#f8f9ff] text-[#0d1c2f]'
                }`}
              >
                {gridLogicAuto ? 'ACTIVE AUTO' : 'FIXED DISPATCH'}
              </button>
            </div>
          </div>

          {/* Twin C: CRYO & CLEANROOM SCI-CORE */}
          <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs hover:border-[#4648d4]/60 transition-all">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
                <div className="flex items-center gap-1.5">
                  <Thermometer className="w-4 h-4 text-[#004b59]" />
                  <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">TWIN-C: CRYO SCI-LABS</span>
                </div>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#006577]/10 text-[#004b59] font-bold border border-[#006577]/20">
                  ISO-4 CLEAN
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 my-3">
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">MASS SPECTROMETRY</div>
                  <div className="text-sm font-mono font-bold text-[#4648d4] mt-0.5">-80.0 °C</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Cryo Dewar Locked</div>
                </div>
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">HE3 COMPRESSOR</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">18.2 bar</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Zero Leakage</div>
                </div>
              </div>

              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Ice Core Drill Station</span>
                  <span className="font-bold text-[#0d1c2f]">Depth 1,248m (Nom)</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Laser Particle Sizer</span>
                  <span className="font-bold text-[#0d1c2f]">0.08 μm background</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[#767586]">LN2 Auto-Transfer Line</span>
                  <span className="text-[#006c49] font-medium">Flow Nominal</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between mt-3">
              <span className="text-[9px] font-mono font-bold text-[#767586]">DEWAR PRESSURE VENT</span>
              <button
                onClick={handleVentDewar}
                className={`px-2.5 py-1 text-[10px] font-mono font-bold rounded transition-colors shadow-2xs ${
                  dewarVenting
                    ? 'bg-[#4648d4] text-white animate-pulse'
                    : 'border border-[#eaebf0] hover:border-[#4648d4] bg-white text-[#0d1c2f]'
                }`}
              >
                {dewarVenting ? 'VENTING (0.2 bar/s)' : 'VENT ISOLATED'}
              </button>
            </div>
          </div>

          {/* Twin D: ATMOSPHERIC & GEO-RADAR */}
          <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs hover:border-[#4648d4]/60 transition-all">
            <div>
              <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
                <div className="flex items-center gap-1.5">
                  <Radar className="w-4 h-4 text-[#4648d4]" />
                  <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">TWIN-D: GEO-ATMOSPHERE</span>
                </div>
                <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#6cf8bb]/20 text-[#006c49] font-bold border border-[#006c49]/20">
                  SWPC LIVE
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 my-3">
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">DOBSON OZONE</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">284 DU</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Stratosphere clear</div>
                </div>
                <div className="bg-[#f8f9ff] p-2 rounded border border-[#eaebf0]">
                  <div className="text-[9px] font-mono text-[#767586]">RIOMETER 30MHz</div>
                  <div className="text-sm font-mono font-bold text-[#0d1c2f] mt-0.5">0.42 dB</div>
                  <div className="text-[10px] font-mono text-[#006c49] font-medium">Cosmic noise nom</div>
                </div>
              </div>

              <div className="space-y-1.5 text-[11px] font-mono">
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Fluxgate Magnetometer</span>
                  <span className="font-bold text-[#0d1c2f]">X: {isSpaceStorm ? '19,890 nT' : '18,420 nT'}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-[#f8f9ff]">
                  <span className="text-[#767586]">Aurora All-Sky Imager</span>
                  <span className="font-bold text-[#006c49]">557.7 nm Line Active</span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-[#767586]">Radar Ground Interf.</span>
                  <span className="text-[#0d1c2f] font-medium">Bedrock 1,840m</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between mt-3">
              <span className="text-[9px] font-mono font-bold text-[#767586]">IONO-SOUNDER PULSE</span>
              <button
                onClick={handlePingSounder}
                className={`px-2.5 py-1 text-[10px] font-mono font-bold rounded transition-colors shadow-2xs ${
                  sounderPulsing
                    ? 'bg-[#4648d4] text-white animate-pulse'
                    : 'border border-[#eaebf0] hover:border-[#4648d4] bg-white text-[#0d1c2f]'
                }`}
              >
                {sounderPulsing ? 'PULSING 12.4 MHz' : 'PULSE READY'}
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 3: POLAR ENVIRONMENTAL INTELLIGENCE DUAL-WIDGET ================= */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4" id="intel">
        {/* Widget 1: NOAA SWPC Space Weather Station */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <Sun className="w-4 h-4 text-[#4648d4]" />
                <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">
                  NOAA SWPC SPACE WEATHER // POLAR MAGNETOSPHERE
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${isSpaceStorm ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#10b981]'}`} />
                <span className={`text-[10px] font-mono font-bold ${isSpaceStorm ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
                  {isSpaceStorm ? 'G4 STORM ACTIVE' : 'QUIET REGIME'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2.5 my-3.5">
              {/* Kp Index */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">GEOMAGNETIC Kp</span>
                <div className={`text-base font-mono font-bold mt-1 ${isSpaceStorm ? 'text-[#ba1a1a]' : 'text-[#0d1c2f]'}`}>
                  Kp {kpVal.toFixed(1)}
                </div>
                <div className={`text-[9px] font-mono font-semibold mt-0.5 truncate ${isSpaceStorm ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
                  {isSpaceStorm ? 'Severe G4 Storm' : 'Sub-Auroral Quiet'}
                </div>
              </div>

              {/* Solar Wind */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">SOLAR WIND SPEED</span>
                <div className="text-base font-mono font-bold text-[#0d1c2f] mt-1 tabular-nums">
                  {solarWindVal} <span className="text-xs font-normal text-[#767586]">km/s</span>
                </div>
                <div className="text-[9px] font-mono text-[#767586] mt-0.5">Density 4.2 p/cm³</div>
              </div>

              {/* Blackout Prob */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">HF RADIO BLACKOUT</span>
                <div className={`text-base font-mono font-bold mt-1 ${isSpaceStorm ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
                  {hfBlackoutVal}
                </div>
                <div className="text-[9px] font-mono text-[#767586] mt-0.5 truncate">D-Region Absorpt</div>
              </div>
            </div>

            {/* Stylized Auroral Oval Intensity Arc Visualizer */}
            <div className="bg-[#f8f9ff] p-3 rounded border border-[#eaebf0] space-y-2">
              <div className="flex justify-between items-center text-[10px] font-mono">
                <span className="text-[#0d1c2f] font-semibold">AURORAL OVAL INTENSITY (60°S - 80°S)</span>
                <span className={`font-bold ${isSpaceStorm ? 'text-[#ba1a1a]' : 'text-[#4648d4]'}`}>
                  {auroraPowerVal}
                </span>
              </div>

              {/* 10-Segmented visual arc meter */}
              <div className="grid grid-cols-10 gap-1 h-2.5">
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((idx) => {
                  let colorClass = 'bg-[#e6eeff]';
                  if (isSpaceStorm) {
                    colorClass = idx < 8 ? 'bg-[#ba1a1a]' : idx < 9 ? 'bg-[#f59e0b]' : 'bg-[#10b981]';
                  } else {
                    colorClass = idx < 3 ? 'bg-[#10b981]' : 'bg-[#e6eeff]';
                  }
                  return <div key={idx} className={`${colorClass} rounded-xs transition-colors duration-300`} />;
                })}
              </div>

              <div className="flex justify-between text-[9px] font-mono text-[#767586]">
                <span>0 GW (STABLE)</span>
                <span>50 GW (MODERATE)</span>
                <span>120+ GW (EXTREME STORM)</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#eaebf0] flex justify-between items-center text-[10px] font-mono text-[#767586] mt-3">
            <span>GOES-18 Polar Heliophysics telemetry stream</span>
            <span className="text-[#006c49] font-medium">Uplink verified</span>
          </div>
        </div>

        {/* Widget 2: AMPS Polar Weather & Katabatic Vector */}
        <div className="bg-white border border-[#eaebf0] rounded-lg p-4 flex flex-col justify-between shadow-2xs">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-[#eaebf0]">
              <div className="flex items-center gap-2">
                <Wind className="w-4 h-4 text-[#4648d4]" />
                <span className="text-[10px] font-mono font-bold text-[#0d1c2f]">
                  AMPS POLAR WEATHER // KATABATIC DYNAMICS
                </span>
              </div>
              <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-[#f8f9ff] text-[#767586] border border-[#eaebf0]">
                BAROMETRIC TENDENCY
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2.5 my-3.5">
              {/* Barometer */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">BAROMETRIC PRESS</span>
                <div className="text-base font-mono font-bold text-[#0d1c2f] mt-1 tabular-nums">
                  982.4 <span className="text-xs font-normal text-[#767586]">hPa</span>
                </div>
                <div className="text-[9px] font-mono text-[#ba1a1a] mt-0.5">Dropping -1.2hPa/3h</div>
              </div>

              {/* Wind Vector */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">KATABATIC VECTOR</span>
                <div className="text-base font-mono font-bold text-[#0d1c2f] mt-1 tabular-nums">
                  114° <span className="text-xs font-normal text-[#767586]">ESE</span>
                </div>
                <div className="text-[9px] font-mono text-[#b45309] mt-0.5 truncate">Down-slope Grav</div>
              </div>

              {/* Whiteout Risk */}
              <div className="bg-[#f8f9ff] p-2.5 rounded border border-[#eaebf0]">
                <span className="text-[9px] font-mono text-[#767586]">12H WHITEOUT RISK</span>
                <div className={`text-base font-mono font-bold mt-1 ${isGale ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`}>
                  {isGale ? 'High (88%)' : 'Low (14%)'}
                </div>
                <div className="text-[9px] font-mono text-[#767586] mt-0.5 truncate">Visual &gt; 8.4 km</div>
              </div>
            </div>

            {/* Shear Threshold Alert Status */}
            <div className="bg-[#f8f9ff] p-3 rounded border border-[#eaebf0] flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="text-[10px] font-mono font-bold text-[#0d1c2f]">SHEAR THRESHOLD ALERT STATUS</div>
                <div className="text-[11px] font-sans text-[#767586]">
                  {isGale 
                    ? 'EXTREME KATABATIC SURGE DETECTED - STRUCTURAL SHIELDING ENGAGED' 
                    : 'Larsemann Hills ridge buffer dissipating katabatic boundary layer'}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Compass className={`w-5 h-5 ${isGale ? 'text-[#ba1a1a]' : 'text-[#006c49]'}`} />
                <div className="text-right font-mono">
                  <div className="text-sm font-bold text-[#0d1c2f]">{isGale ? '92.4 kts' : '66.5 kts'}</div>
                  <div className="text-[9px] text-[#767586]">{isGale ? 'Shear Critical' : 'Gale Margin Safe'}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#eaebf0] flex justify-between items-center text-[10px] font-mono text-[#767586] mt-3">
            <span>Antarctic Mesoscale Prediction System (AMPS WRF 3km)</span>
            <span className="text-[#006c49] font-medium">Valid until +06:00 UTC</span>
          </div>
        </div>
      </section>

      {/* ================= SECTION 4: AUTONOMOUS 10-AGENT CONSENSUS STREAM ================= */}
      <section className="bg-white border border-[#eaebf0] rounded-lg p-4 shadow-2xs" id="consensus">
        <div className="flex items-center justify-between pb-3 border-b border-[#eaebf0]">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-[#4648d4]" />
            <h2 className="font-display text-base font-bold text-[#0d1c2f] tracking-wide">
              AUTONOMOUS 10-AGENT CONSENSUS ENGINE
            </h2>
            <span className="hidden sm:inline text-[9px] font-mono px-2 py-0.5 rounded bg-[#4648d4]/10 text-[#2c2abc] font-bold border border-[#4648d4]/20">
              BYZANTINE FAULT TOLERANCE 3f+1
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-[#767586]">QUORUM STATE:</span>
            <span className="text-[10px] font-mono font-bold text-[#006c49] bg-[#6cf8bb]/20 px-2 py-0.5 rounded border border-[#006c49]/20">
              SYNCHRONIZED (10/10)
            </span>
          </div>
        </div>

        {/* 10 Agent Telemetry Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 my-3">
          {agentNodes.map((ag) => (
            <div key={ag.name} className="bg-[#f8f9ff] border border-[#eaebf0] p-2 rounded flex items-center justify-between">
              <div className="truncate">
                <div className="text-[10px] font-mono font-bold text-[#0d1c2f] truncate">{ag.name}</div>
                <div className="text-[9px] font-mono text-[#006c49] font-medium">{ag.status}</div>
              </div>
              <span className="w-2 h-2 rounded-full bg-[#10b981]" />
            </div>
          ))}
        </div>

        {/* Live Streaming Consensus Log */}
        <div className="bg-[#f8f9ff] rounded border border-[#eaebf0] overflow-hidden">
          <div className="p-2 border-b border-[#eaebf0] bg-[#dde9ff]/40 flex justify-between text-[9px] font-mono text-[#767586] font-semibold">
            <span>TIMESTAMP / AGENT IDENTITY</span>
            <span>AUTONOMOUS DIRECTIVE DISPATCH</span>
            <span>VOTE RATIO</span>
          </div>
          <div className="divide-y divide-[#eaebf0] font-mono text-xs max-h-56 overflow-y-auto">
            {consensusLogs.map((log) => (
              <div
                key={log.id}
                className={`p-2.5 flex items-center justify-between transition-colors ${
                  log.isAlert ? 'bg-[#ffdad6]/30 border-l-2 border-[#ba1a1a]' : 'hover:bg-white'
                }`}
              >
                <div className="flex items-center gap-2 min-w-[170px]">
                  <span className="text-[10px] text-[#767586]">{log.timestamp}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
                    log.isAlert ? 'bg-white text-[#ba1a1a] border-[#ba1a1a]' : 'bg-white text-[#4648d4] border-[#eaebf0]'
                  }`}>
                    {log.agent}
                  </span>
                </div>
                <div className="text-xs font-sans text-[#0d1c2f] truncate px-3 flex-1 font-medium">
                  {log.directive}
                </div>
                <span className="px-2 py-0.5 rounded text-[9px] font-mono font-bold bg-[#6cf8bb]/20 text-[#006c49]">
                  {log.voteRatio}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= SECTION 5: ONE-CLICK TACTILE SCENARIO INJECTION BENCH ================= */}
      <footer className="fixed bottom-0 left-0 md:left-64 lg:left-72 right-0 z-30 bg-white/95 backdrop-blur-md border-t border-[#eaebf0] px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#4648d4]" />
          <span className="text-[10px] font-mono font-bold text-[#0d1c2f] tracking-wider">
            TACTILE SCENARIO BENCH:
          </span>
          <span className="text-[11px] font-sans text-[#767586] hidden xl:inline">
            Inject extreme polar disturbances & observe autonomous agent resilience
          </span>
        </div>

        {/* Tactile Triggers */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => handleTriggerScenario('GALE')}
            className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-semibold border flex items-center gap-1.5 transition-all shadow-2xs ${
              isGale 
                ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]' 
                : 'bg-[#f8f9ff] hover:bg-[#eaedff] text-[#0d1c2f] border-[#eaebf0]'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isGale ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
            <span>KATABATIC GALE (+140 KM/H)</span>
          </button>

          <button
            onClick={() => handleTriggerScenario('SPACE_STORM')}
            className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-semibold border flex items-center gap-1.5 transition-all shadow-2xs ${
              isSpaceStorm 
                ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]' 
                : 'bg-[#f8f9ff] hover:bg-[#eaedff] text-[#0d1c2f] border-[#eaebf0]'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isSpaceStorm ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
            <span>SPACE WEATHER KP-8 STORM</span>
          </button>

          <button
            onClick={() => handleTriggerScenario('GEN_TRIP')}
            className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-semibold border flex items-center gap-1.5 transition-all shadow-2xs ${
              isGenTrip 
                ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]' 
                : 'bg-[#f8f9ff] hover:bg-[#eaedff] text-[#0d1c2f] border-[#eaebf0]'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isGenTrip ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
            <span>GEN-SET 2 EMERGENCY TRIP</span>
          </button>

          <button
            onClick={() => handleTriggerScenario('FREEZE')}
            className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-semibold border flex items-center gap-1.5 transition-all shadow-2xs ${
              isFreeze 
                ? 'bg-[#ffdad6] text-[#ba1a1a] border-[#ba1a1a]' 
                : 'bg-[#f8f9ff] hover:bg-[#eaedff] text-[#0d1c2f] border-[#eaebf0]'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isFreeze ? 'bg-[#ba1a1a] animate-ping' : 'bg-[#c6c5d7]'}`} />
            <span>UTILIDOR FREEZE HAZARD</span>
          </button>

          <button
            onClick={handleResetBaseline}
            className="px-3 py-1.5 rounded text-[10px] font-mono font-bold bg-[#4648d4] text-white hover:bg-[#3537b8] flex items-center gap-1.5 transition-all shadow-xs"
            title="Reset Simulation to Baseline Equilibrium"
          >
            <RotateCcw className="w-3 h-3" />
            <span>RESET BASELINE</span>
          </button>
        </div>
      </footer>
    </div>
  );
};
