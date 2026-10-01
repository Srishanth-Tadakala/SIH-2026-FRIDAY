import React, { useState, useEffect } from 'react';
import { 
  Compass, 
  Menu, 
  X, 
  AlertTriangle, 
  Radio, 
  ShieldCheck, 
  Satellite, 
  SlidersHorizontal,
  Activity,
  Lock,
  ChevronDown
} from 'lucide-react';
import { StationId } from '../types';

interface TopMissionHeaderProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  activeCrisis: string | null;
  opMode: 'AUTO' | 'MANUAL';
  onOpModeChange: (mode: 'AUTO' | 'MANUAL') => void;
  onEmergencyOverride: () => void;
  onMobileMenuToggle: () => void;
  mobileMenuOpen: boolean;
}

export const TopMissionHeader: React.FC<TopMissionHeaderProps> = ({
  activeStation,
  onStationChange,
  activeCrisis,
  opMode,
  onOpModeChange,
  onEmergencyOverride,
  onMobileMenuToggle,
  mobileMenuOpen,
}) => {
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hrs = String(now.getUTCHours()).padStart(2, '0');
      const mins = String(now.getUTCMinutes()).padStart(2, '0');
      const secs = String(now.getUTCSeconds()).padStart(2, '0');
      const ms = Math.floor(now.getUTCMilliseconds() / 100);
      setUtcTime(`UTC ${hrs}:${mins}:${secs}.${ms}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex justify-between items-center w-full px-4 sm:px-6 h-14 bg-white/95 backdrop-blur-md border-b border-[#eaebf0] selection:bg-[#4648d4] selection:text-white">
      {/* Brand & Station Switcher */}
      <div className="flex items-center gap-4 sm:gap-6">
        {/* Mobile Menu Trigger */}
        <button
          onClick={onMobileMenuToggle}
          className="md:hidden p-1.5 rounded-lg text-[#464554] hover:bg-[#eaedff] transition-colors"
          aria-label="Toggle Navigation Drawer"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Brand Identity */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-[#4648d4] text-white flex items-center justify-center font-bold text-xs shadow-xs">
            ❄
          </div>
          <div className="flex flex-col">
            <span className="font-display text-sm font-bold tracking-wider text-[#0d1c2f] leading-none">
              POLARIS // ANTARCTIC CMD
            </span>
            <span className="text-[9px] font-mono font-medium text-[#767586] tracking-tight hidden sm:inline">
              NCPOR • MoES SOVEREIGN DIGITAL TWIN
            </span>
          </div>
        </div>

        {/* Station Toggles (Bharati / Maitri) */}
        <div className="hidden lg:flex items-center gap-1.5 p-0.5 bg-[#f8f9ff] border border-[#eaebf0] rounded-md">
          <button
            id="btn-bharati"
            onClick={() => onStationChange('bharati')}
            className={`px-3 py-1 rounded text-[10px] font-mono font-semibold flex items-center gap-2 transition-all ${
              activeStation === 'bharati'
                ? 'bg-white text-[#2c2abc] border border-[#4648d4]/40 shadow-xs'
                : 'text-[#464554] hover:text-[#0d1c2f]'
            }`}
            title="Switch to Bharati Station (Larsemann Hills)"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${activeStation === 'bharati' ? 'bg-[#10b981] pulse-emerald' : 'bg-[#767586]'}`} />
            <span>BHARATI [69°24'S]</span>
          </button>
          <button
            id="btn-maitri"
            onClick={() => onStationChange('maitri')}
            className={`px-3 py-1 rounded text-[10px] font-mono font-semibold flex items-center gap-2 transition-all ${
              activeStation === 'maitri'
                ? 'bg-white text-[#2c2abc] border border-[#4648d4]/40 shadow-xs'
                : 'text-[#464554] hover:text-[#0d1c2f]'
            }`}
            title="Switch to Maitri Station (Schirmacher Oasis)"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${activeStation === 'maitri' ? 'bg-[#10b981] pulse-emerald' : 'bg-[#767586]'}`} />
            <span>MAITRI [70°46'S]</span>
          </button>
        </div>
      </div>

      {/* Center Station Health Badge */}
      <div className="hidden md:flex items-center gap-3 px-3 py-1 bg-[#f8f9ff] border border-[#eaebf0] rounded text-[11px] font-mono">
        <span className={`w-2 h-2 rounded-full ${activeCrisis ? 'bg-[#f59e0b] pip-amber-pulse' : 'bg-[#10b981] pulse-emerald'}`} />
        <span className={`font-semibold tracking-wide ${activeCrisis ? 'text-[#b45309]' : 'text-[#006c49]'}`}>
          {activeCrisis ? `ADVISORY: ${activeCrisis.toUpperCase()}` : 'STATION TELEMETRY NOMINAL 99.8%'}
        </span>
        <span className="text-[#c6c5d7]">|</span>
        <span className="text-[#464554] flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 text-[#006577]" />
          <span>STARLINK POLAR 42ms</span>
        </span>
      </div>

      {/* Trailing Controls & Mission Actions */}
      <div className="flex items-center gap-3">
        {/* Polar UTC Mesh Clock */}
        <div className="hidden sm:flex flex-col items-end">
          <span className="text-[9px] font-mono text-[#767586] leading-none">POLAR UTC MESH</span>
          <span className="text-xs font-mono font-bold text-[#0d1c2f] tabular-nums mt-0.5">
            {utcTime || 'UTC --:--:--.-'}
          </span>
        </div>

        {/* Operation Mode Selector */}
        <div className="hidden xl:flex items-center bg-[#f8f9ff] border border-[#eaebf0] rounded p-0.5 text-[10px] font-mono">
          <button
            onClick={() => onOpModeChange('AUTO')}
            className={`px-2 py-0.5 rounded font-semibold transition-all ${
              opMode === 'AUTO'
                ? 'bg-[#4648d4] text-white shadow-xs'
                : 'text-[#464554] hover:text-[#0d1c2f]'
            }`}
          >
            AUTO-CONSENSUS
          </button>
          <button
            onClick={() => onOpModeChange('MANUAL')}
            className={`px-2 py-0.5 rounded font-semibold transition-all ${
              opMode === 'MANUAL'
                ? 'bg-[#f59e0b] text-white shadow-xs'
                : 'text-[#464554] hover:text-[#0d1c2f]'
            }`}
          >
            CREW OVERRIDE
          </button>
        </div>

        {/* Emergency Override Button */}
        <button
          onClick={onEmergencyOverride}
          className="bg-white text-[#ba1a1a] border border-[#ba1a1a] hover:bg-[#ba1a1a] hover:text-white px-2.5 sm:px-3 py-1 rounded text-[10px] font-mono font-bold tracking-wider transition-colors flex items-center gap-1.5 shadow-2xs"
          title="Trigger Emergency Station Override"
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">EMERGENCY OVERRIDE</span>
          <span className="sm:hidden">OVERRIDE</span>
        </button>
      </div>
    </header>
  );
};
