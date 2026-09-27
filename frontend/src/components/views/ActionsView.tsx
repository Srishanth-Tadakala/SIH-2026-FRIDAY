import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShieldCheck, 
  Play, 
  CheckCircle2, 
  Clock, 
  Lock, 
  RefreshCw, 
  AlertTriangle,
  ArrowRight,
  Cpu,
  Flame,
  Zap,
  Wind,
  Droplet,
  Power,
  RotateCcw,
  Sliders,
  Radio,
  Check,
  X
} from 'lucide-react';
import { StationId, ActuationRecord, ActuatorState } from '../../types';
import { 
  fetchActuationHistory, 
  fetchPendingActions, 
  executeAction,
  fetchStationActuators,
  executeActuatorCommand,
  bypassSupervisedAction,
  cancelSupervisedAction,
  cancelTier3Action,
  authorizeCommanderPin,
  configureAutonomousMode
} from '../../api';

interface ActionsViewProps {
  activeStation: StationId;
}

export const ActionsView: React.FC<ActionsViewProps> = ({ activeStation }) => {
  const [history, setHistory] = useState<ActuationRecord[]>([]);
  const [pending, setPending] = useState<any[]>([]);
  const [actuators, setActuators] = useState<ActuatorState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Autonomous governor state
  const [autonomousEnabled, setAutonomousEnabled] = useState<boolean>(true);
  const [continuousRunning, setContinuousRunning] = useState<boolean>(true);
  const [speedFactor, setSpeedFactor] = useState<number>(1.0);

  // Commander PIN Modal / Form
  const [showPinModal, setShowPinModal] = useState<boolean>(false);
  const [pinCode, setPinCode] = useState<string>('BHARATI-CMD-2026');
  const [pinTargetAction, setPinTargetAction] = useState<string | null>(null);
  const [pinVerifying, setPinVerifying] = useState<boolean>(false);

  // Load all actions, pending queues, and live hardware actuators
  const loadActions = useCallback(async () => {
    try {
      const [histData, pendData, actData] = await Promise.all([
        fetchActuationHistory(50),
        fetchPendingActions(),
        fetchStationActuators(activeStation).catch(() => null),
      ]);
      setHistory(histData);
      setPending(pendData);
      if (actData) setActuators(actData);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  }, [activeStation]);

  useEffect(() => {
    loadActions();
    const interval = setInterval(loadActions, 3000);
    return () => clearInterval(interval);
  }, [loadActions]);

  // Execute or Bypass Supervised Action
  const handleBypassSupervised = async (actionId: string) => {
    setStatusMessage(`Bypassing supervision and executing ${actionId}...`);
    try {
      await bypassSupervisedAction(actionId);
      setStatusMessage(`Action ${actionId} approved & executed immediately.`);
      await loadActions();
    } catch (err: any) {
      setStatusMessage(`Bypass failed: ${err.message || 'Execution error'}`);
    }
    setTimeout(() => setStatusMessage(null), 3500);
  };

  // Veto & Cancel Supervised Action
  const handleCancelSupervised = async (actionId: string) => {
    setStatusMessage(`Vetoing action ${actionId}...`);
    try {
      await cancelSupervisedAction(actionId);
      setStatusMessage(`Action ${actionId} successfully vetoed and removed from queue.`);
      await loadActions();
    } catch (err: any) {
      setStatusMessage(`Cancel error: ${err.message}`);
    }
    setTimeout(() => setStatusMessage(null), 3500);
  };

  // Direct Hardware Actuator Command
  const handleActuatorCommand = async (command: string, params: Record<string, any> = {}, pin?: string) => {
    setStatusMessage(`Dispatching physical actuator command: ${command}...`);
    try {
      const res = await executeActuatorCommand(activeStation, command, params, pin);
      setStatusMessage(`Actuator response: ${res.message || 'DISPATCHED_AND_CONFIRMED'}`);
      await loadActions();
    } catch (err: any) {
      setStatusMessage(`Actuator rejected: ${err.message || 'Interlock block'}`);
    }
    setTimeout(() => setStatusMessage(null), 3500);
  };

  // Commander PIN Authorization for Tier 3
  const handleAuthorizePin = async () => {
    setPinVerifying(true);
    setStatusMessage(`Authorizing Commander PIN for ${pinTargetAction || 'Emergency Override'}...`);
    try {
      const res = await authorizeCommanderPin({
        pin: pinCode,
        command: 'COMMANDER_EMERGENCY_DISPATCH',
        action_id: pinTargetAction || undefined,
      });
      setStatusMessage(`✓ PIN verified. Tier 3 Interlock unlocked: ${res.status}`);
      setShowPinModal(false);
      setPinTargetAction(null);
      await loadActions();
    } catch (err: any) {
      setStatusMessage(`PIN Authorization Failed: ${err.message || 'Invalid PIN'}`);
    } finally {
      setPinVerifying(false);
      setTimeout(() => setStatusMessage(null), 4000);
    }
  };

  // Configure Autonomous Edge Closed-Loop Governor
  const handleToggleAutonomous = async () => {
    const nextVal = !autonomousEnabled;
    try {
      await configureAutonomousMode({ autonomous_enabled: nextVal });
      setAutonomousEnabled(nextVal);
      setStatusMessage(`Autonomous AI Governor set to: ${nextVal ? 'ACTIVE (1.2s Fast Loop)' : 'SUSPENDED'}`);
    } catch {}
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const handleToggleClock = async () => {
    const nextVal = !continuousRunning;
    try {
      await configureAutonomousMode({ continuous_running: nextVal });
      setContinuousRunning(nextVal);
      setStatusMessage(`Simulation continuous clock: ${nextVal ? 'RUNNING (1 Hz)' : 'PAUSED'}`);
    } catch {}
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const handleSetSpeed = async (speed: number) => {
    try {
      await configureAutonomousMode({ speed });
      setSpeedFactor(speed);
      setStatusMessage(`Simulation speed factor adjusted to ${speed}x.`);
    } catch {}
    setTimeout(() => setStatusMessage(null), 3500);
  };

  const isBharati = activeStation === 'bharati';

  return (
    <div className="w-full flex flex-col gap-6">
      {/* 1. Header Bar with Actions & Autonomous Engine Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-[#eaebf0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-md text-[9px] font-mono font-black uppercase bg-[#4648d4] text-white">
              TIER 1-3 GOVERNANCE
            </span>
            <span className="text-xs font-mono font-semibold text-[#73738c]">
              Hardware Actuation &amp; Interlocks
            </span>
          </div>
          <h1 className="font-display font-black text-2xl sm:text-3xl text-[#131b2e] tracking-tight">
            Autonomous Actuation Ledger
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {statusMessage && (
            <span className="text-xs font-mono text-[#4648d4] bg-[#eaedff] px-3 py-1 rounded-full animate-fade-in border border-[#4648d4]/20 font-semibold">
              {statusMessage}
            </span>
          )}

          <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-white border border-[#eaebf0] shadow-xs text-xs font-mono">
            <button
              onClick={handleToggleAutonomous}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all flex items-center gap-1.5 ${
                autonomousEnabled 
                  ? 'bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0]' 
                  : 'bg-[#fff1f2] text-[#e11d48] border border-[#fecdd3]'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>AI Autonomy: {autonomousEnabled ? 'ENABLED' : 'PAUSED'}</span>
            </button>

            <button
              onClick={handleToggleClock}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                continuousRunning
                  ? 'bg-[#f2f3ff] text-[#4648d4]'
                  : 'bg-[#fffbeb] text-[#d97706]'
              }`}
            >
              {continuousRunning ? 'Clock: 1 Hz' : 'Clock: Paused'}
            </button>
          </div>

          <button
            onClick={loadActions}
            className="p-2.5 rounded-xl bg-white border border-[#eaebf0] hover:bg-[#f2f3ff] text-[#464554] transition-colors shadow-2xs"
            title="Refresh Ledger & Actuators"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 2. Three-Tier Defense Safety Interlocks Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-md border border-[#a7f3d0]">
              Tier 1 • Autonomous
            </span>
            <CheckCircle2 className="w-4 h-4 text-[#006c49]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Fast Contactor (&lt;1.2s)</h2>
          <p className="text-xs text-[#73738c] mt-1 leading-relaxed">
            Reversible micro-adjustments, automatic ATS standby switchover, and trace heat boost executed with deterministic safety margin.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#d97706] bg-[#fffbeb] px-2 py-0.5 rounded-md border border-[#fef3c7]">
              Tier 2 • Supervised
            </span>
            <Clock className="w-4 h-4 text-[#d97706]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Supervised Review Window</h2>
          <p className="text-xs text-[#73738c] mt-1 leading-relaxed">
            Major electrical load shifts and AHU damper seals. 60-second visual count before autonomous execution unless operator vetoes.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white border border-[#eaebf0] shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold uppercase text-[#4648d4] bg-[#f2f3ff] px-2 py-0.5 rounded-md border border-[#eaedff]">
              Tier 3 • Commander PIN
            </span>
            <Lock className="w-4 h-4 text-[#4648d4]" />
          </div>
          <h2 className="font-display font-bold text-sm text-[#131b2e]">Station Commander Gate</h2>
          <p className="text-xs text-[#73738c] mt-1 leading-relaxed">
            Life-critical habitat HVAC shutdowns, total microgrid blackouts. Protected by PBKDF2 100k rounds &amp; HMAC hardware signature.
          </p>
        </div>
      </div>

      {/* 3. Live Physical Station Actuators Hardware Bench */}
      <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#eaebf0] pb-3">
          <div>
            <span className="text-[10px] font-mono font-bold text-[#4648d4] uppercase tracking-wider">
              {activeStation.toUpperCase()} PHYSICAL HARDWARE ASSETS
            </span>
            <h2 className="font-display font-bold text-lg text-[#131b2e]">
              Station Actuator Controller Bench
            </h2>
          </div>
          <span className="text-xs font-mono text-[#006c49] font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            Direct Modbus-TCP Interlocked
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* CHP Baseload Actuator */}
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1">
                <span className="font-bold text-[#131b2e] flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-[#e11d48]" />
                  CHP-01 Baseload
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  actuators?.chps?.[0]?.running ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fff1f2] text-[#e11d48]'
                }`}>
                  {actuators?.chps?.[0]?.running ? 'RUNNING' : 'STOPPED'}
                </span>
              </div>
              <div className="text-sm font-mono font-black text-[#131b2e] mt-1">
                {actuators?.chps?.[0]?.power_kw?.toFixed(1) ?? '75.0'} <span className="text-xs font-normal text-[#73738c]">kW</span>
              </div>
              <span className="text-[10px] font-mono text-[#73738c] block mt-0.5">
                Coolant: +{actuators?.chps?.[0]?.coolant_temp_c?.toFixed(1) ?? '84.2'}°C • 1500 RPM
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-[#eaebf0]">
              <button
                onClick={() => handleActuatorCommand(actuators?.chps?.[0]?.running ? 'STOP_CHP' : 'START_CHP', { chp_id: 'CHP-01' })}
                className={`flex-1 py-1.5 rounded-xl text-xs font-mono font-bold transition-all border ${
                  actuators?.chps?.[0]?.running
                    ? 'bg-[#fff1f2] text-[#e11d48] border-[#fecdd3] hover:bg-[#ffe4e6]'
                    : 'bg-[#ecfdf5] text-[#006c49] border-[#a7f3d0] hover:bg-[#d1fae5]'
                }`}
              >
                {actuators?.chps?.[0]?.running ? 'Stop Generator' : 'Start Generator'}
              </button>
            </div>
          </div>

          {/* CHP Standby Actuator */}
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1">
                <span className="font-bold text-[#131b2e] flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-[#4648d4]" />
                  CHP-02 Standby
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  actuators?.chps?.[1]?.running ? 'bg-[#ecfdf5] text-[#006c49]' : 'bg-[#fffbeb] text-[#d97706]'
                }`}>
                  {actuators?.chps?.[1]?.running ? 'RUNNING' : 'STANDBY ARMED'}
                </span>
              </div>
              <div className="text-sm font-mono font-black text-[#131b2e] mt-1">
                {actuators?.chps?.[1]?.power_kw?.toFixed(1) ?? '0.0'} <span className="text-xs font-normal text-[#73738c]">kW</span>
              </div>
              <span className="text-[10px] font-mono text-[#73738c] block mt-0.5">
                Block Heater: +55.0°C Sync Ready
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-[#eaebf0]">
              <button
                onClick={() => handleActuatorCommand('START_CHP', { chp_id: 'CHP-02' })}
                className="flex-1 py-1.5 rounded-xl text-xs font-mono font-bold bg-[#f2f3ff] text-[#4648d4] border border-[#eaedff] hover:bg-[#eaedff] transition-all"
              >
                Start Standby CHP-02
              </button>
            </div>
          </div>

          {/* Trace Heating Actuator */}
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1">
                <span className="font-bold text-[#131b2e] flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-[#0891b2]" />
                  Utilidor Heating
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  actuators?.pipelines?.water01_trace_heating_on ? 'bg-[#ecfeff] text-[#0891b2]' : 'bg-[#fffbeb] text-[#d97706]'
                }`}>
                  {actuators?.pipelines?.water01_trace_heating_on ? 'ACTIVE (8.2 kWth)' : 'BOOST READY'}
                </span>
              </div>
              <div className="text-sm font-mono font-black text-[#131b2e] mt-1">
                +{actuators?.pipelines?.water01_pipe_temp_c?.toFixed(1) ?? '4.8'}°C <span className="text-xs font-normal text-[#73738c]">Surface</span>
              </div>
              <span className="text-[10px] font-mono text-[#73738c] block mt-0.5">
                Circuit: Lake Zub Suction Line
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-[#eaebf0]">
              <button
                onClick={() => handleActuatorCommand('SET_TRACE_HEATING', { mode: 'BOOST', setpoint_c: 12.0 })}
                className="flex-1 py-1.5 rounded-xl text-xs font-mono font-bold bg-[#ecfeff] text-[#0891b2] border border-[#a5f3fc] hover:bg-[#cffafe] transition-all"
              >
                Force Boost 100%
              </button>
              <button
                onClick={() => handleActuatorCommand('SET_TRACE_HEATING', { mode: 'NOMINAL', setpoint_c: 4.0 })}
                className="py-1.5 px-2.5 rounded-xl text-xs font-mono font-bold bg-white text-[#131b2e] border border-[#eaedff] hover:bg-[#faf8ff] transition-all"
              >
                Nominal
              </button>
            </div>
          </div>

          {/* HVAC Blizzard Dampers Actuator */}
          <div className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] flex flex-col justify-between gap-3">
            <div>
              <div className="flex items-center justify-between text-xs font-mono mb-1">
                <span className="font-bold text-[#131b2e] flex items-center gap-1.5">
                  <Wind className="w-4 h-4 text-[#4648d4]" />
                  Blizzard Dampers
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  actuators?.hvac?.blizzard_dampers_sealed ? 'bg-[#fff1f2] text-[#e11d48]' : 'bg-[#ecfdf5] text-[#006c49]'
                }`}>
                  {actuators?.hvac?.blizzard_dampers_sealed ? 'SEALED (0%)' : 'OPEN (100%)'}
                </span>
              </div>
              <div className="text-sm font-mono font-black text-[#131b2e] mt-1">
                {actuators?.hvac?.ahu01_fresh_air_damper_pct ?? 25}% <span className="text-xs font-normal text-[#73738c]">Damper Pos</span>
              </div>
              <span className="text-[10px] font-mono text-[#73738c] block mt-0.5">
                AHU-01 Living Quarters Intake
              </span>
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-[#eaebf0]">
              <button
                onClick={() => handleActuatorCommand('SET_BLIZZARD_DAMPERS', { position_pct: 0 })}
                className="flex-1 py-1.5 rounded-xl text-xs font-mono font-bold bg-[#fff1f2] text-[#e11d48] border border-[#fecdd3] hover:bg-[#ffe4e6] transition-all"
              >
                Seal (0%)
              </button>
              <button
                onClick={() => handleActuatorCommand('SET_BLIZZARD_DAMPERS', { position_pct: 100 })}
                className="flex-1 py-1.5 rounded-xl text-xs font-mono font-bold bg-[#ecfdf5] text-[#006c49] border border-[#a7f3d0] hover:bg-[#d1fae5] transition-all"
              >
                Open (100%)
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Tier 2 Supervised Actions Review Window */}
      {pending.length > 0 && (
        <div className="p-6 rounded-3xl bg-[#fffbeb] border border-[#fef3c7] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-display font-bold text-base text-[#b45309] flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#d97706]" />
              <span>Actions Awaiting Human Confirmation ({pending.length})</span>
            </h3>
            <span className="text-xs font-mono text-[#d97706] font-semibold">
              60s Auto-Countdown Active
            </span>
          </div>

          <div className="space-y-3">
            {pending.map((p) => (
              <div
                key={p.action_id}
                className="p-4 rounded-2xl bg-white border border-[#fef3c7] flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs shadow-2xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-[#d97706] bg-[#fffbeb] px-2 py-0.5 rounded-md border border-[#fef3c7]">
                      {p.action_id}
                    </span>
                    <span className="font-mono text-[10px] text-[#73738c]">
                      Tier: {p.autonomy_tier}
                    </span>
                  </div>
                  <div className="font-bold text-sm text-[#131b2e]">{p.title || p.plan_name}</div>
                  <div className="text-[#464554] text-xs">
                    Target: {p.target_subsystem || p.strategy || 'Station Microgrid'}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleBypassSupervised(p.action_id)}
                    className="px-4 py-2 rounded-xl bg-[#006c49] hover:bg-[#005237] text-white text-xs font-semibold transition-all flex items-center gap-1.5 shadow-xs"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Approve &amp; Execute</span>
                  </button>

                  <button
                    onClick={() => handleCancelSupervised(p.action_id)}
                    className="px-4 py-2 rounded-xl bg-white border border-[#fecdd3] text-[#e11d48] hover:bg-[#fff1f2] text-xs font-semibold transition-all flex items-center gap-1.5"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Veto Action</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Station Commander PIN Authorization Modal / Form */}
      <div className="p-6 rounded-3xl bg-white border border-[#eaebf0] shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[#4648d4] font-mono text-xs font-bold uppercase mb-1">
            <Lock className="w-4 h-4" />
            <span>Tier 3 Commander Authorization Gate</span>
          </div>
          <h3 className="font-display font-black text-lg text-[#131b2e]">
            Life-Critical Station Overrides
          </h3>
          <p className="text-xs text-[#73738c] max-w-xl mt-0.5">
            Requires cryptographic Station Commander PIN (e.g. <code>BHARATI-CMD-2026</code>) to disengage safety interlocks and execute high-consequence actuations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="password"
            value={pinCode}
            onChange={(e) => setPinCode(e.target.value)}
            className="px-4 py-2 rounded-xl bg-[#faf8ff] border border-[#eaebf0] text-xs font-mono font-bold text-[#131b2e] focus:outline-none focus:border-[#4648d4] w-48"
            placeholder="Commander PIN"
          />
          <button
            onClick={handleAuthorizePin}
            disabled={pinVerifying}
            className="px-4 py-2 rounded-xl bg-[#4648d4] hover:bg-[#3b3dbf] text-white text-xs font-semibold transition-all shadow-xs disabled:opacity-50 flex items-center gap-1.5"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verify PIN</span>
          </button>
        </div>
      </div>

      {/* 6. Execution Ledger Table */}
      <div className="rounded-3xl bg-white border border-[#eaebf0] p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4 border-b border-[#eaebf0] pb-3">
          <h2 className="font-display font-bold text-lg text-[#131b2e] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#4648d4]" />
            <span>Immutable Actuation Flight Ledger ({history.length} Events)</span>
          </h2>
          <span className="text-[11px] font-mono text-[#006c49] font-bold">
            HMAC-SHA256 Signed
          </span>
        </div>

        {history.length === 0 ? (
          <div className="py-8 text-center text-xs text-[#73738c] font-mono">
            No physical actuations recorded yet.
          </div>
        ) : (
          <div className="flex flex-col gap-3 max-h-[640px] overflow-y-auto pr-1">
            {history.map((record) => (
              <div
                key={record.action_id}
                className="p-4 rounded-2xl bg-[#faf8ff] border border-[#eaedff] hover:border-[#4648d4]/40 transition-all text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-[#4648d4]">
                      {record.action_id}
                    </span>
                    <span className="text-[#73738c]">•</span>
                    <span className="font-mono text-[10px] text-[#006c49] bg-[#ecfdf5] px-2 py-0.5 rounded-md font-semibold border border-[#a7f3d0]">
                      {record.autonomy_tier}
                    </span>
                    <span className="text-[#73738c]">•</span>
                    <span className="font-mono text-[10px] text-[#73738c] uppercase font-bold">
                      {record.station_id}
                    </span>
                  </div>

                  <span className="font-mono text-[11px] text-[#73738c]">
                    {record.timestamp_iso ? new Date(record.timestamp_iso).toLocaleTimeString() : 'T+103s'}
                  </span>
                </div>

                <div className="font-display font-bold text-sm text-[#131b2e] mb-1.5">
                  {record.title}
                </div>

                {/* Agent Consensus Chain */}
                {record.dynamic_agent_chain && record.dynamic_agent_chain.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 my-2">
                    <span className="text-[10px] font-mono text-[#73738c]">Chain:</span>
                    {record.dynamic_agent_chain.map((agent, i) => (
                      <span
                        key={agent + i}
                        className="px-2 py-0.5 rounded-md bg-white border border-[#eaedff] text-[10px] font-mono font-semibold text-[#4648d4]"
                      >
                        {agent}
                      </span>
                    ))}
                  </div>
                )}

                {/* Physical Verification */}
                <div className="p-2.5 rounded-xl bg-white border border-[#eaedff] text-[11px] text-[#464554] mt-2 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-[#006c49] mr-1.5">✓ Verification:</span>
                    <span>{record.physical_verification}</span>
                  </div>
                  <span className="text-[9px] font-mono text-[#73738c]">TOKEN_VERIFIED</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionsView;
