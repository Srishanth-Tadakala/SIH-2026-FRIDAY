import React from 'react';
import { Compass, ShieldCheck, Cpu, ArrowUpRight } from 'lucide-react';
import { StationId } from '../types';

interface NavigationHeaderProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  onLaunchCockpit: () => void;
}

export const NavigationHeader: React.FC<NavigationHeaderProps> = ({
  activeStation,
  onStationChange,
  onLaunchCockpit,
}) => {
  return (
    <header className="fixed top-0 w-full z-50 bg-[#faf8ff]/85 backdrop-blur-xl border-b border-[#eaebf0] shadow-[0_1px_8px_rgba(15,23,42,0.04)]">
      <div className="h-16 w-full max-w-[1440px] mx-auto px-6 flex items-center justify-between">
        {/* Brand & System Status Pill */}
        <div className="flex items-center gap-4">
          <a href="#" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shadow-md shadow-[#4648d4]/20 group-hover:scale-105 transition-transform">
              <Cpu className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-display font-bold text-lg text-[#131b2e] tracking-tight leading-none">
                F.R.I.D.A.Y.
              </span>
              <span className="text-[10px] font-mono text-[#464554] tracking-tight mt-0.5">
                ANTARCTIC DIGITAL TWIN
              </span>
            </div>
          </a>

          {/* Operational Status Pill */}
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#eaedff] text-[#4648d4] text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse"></span>
            DEFENSE OPERATIONAL: 505 CHANNELS
          </span>
        </div>

        {/* Center Station Switcher & Nav Links */}
        <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-[#464554]">
          <div className="flex items-center bg-[#eaedff] p-1 rounded-full text-xs font-medium">
            <button
              onClick={() => onStationChange('bharati')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full transition-all duration-200 ${
                activeStation === 'bharati'
                  ? 'bg-white text-[#4648d4] font-semibold shadow-sm'
                  : 'text-[#464554] hover:text-[#131b2e]'
              }`}
            >
              <Compass className="w-3.5 h-3.5 text-[#4648d4]" />
              Bharati (69°S)
            </button>
            <button
              onClick={() => onStationChange('maitri')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full transition-all duration-200 ${
                activeStation === 'maitri'
                  ? 'bg-white text-[#4648d4] font-semibold shadow-sm'
                  : 'text-[#464554] hover:text-[#131b2e]'
              }`}
            >
              <Compass className="w-3.5 h-3.5 text-[#4648d4]" />
              Maitri (70°S)
            </button>
          </div>

          <a href="#canvas" className="hover:text-[#4648d4] transition-colors">Digital Twin Canvas</a>
          <a href="#simulator" className="hover:text-[#4648d4] transition-colors">Crisis Simulation</a>
          <a href="#capabilities" className="hover:text-[#4648d4] transition-colors">Capabilities</a>
          <a href="#metrics" className="hover:text-[#4648d4] transition-colors">Benchmarks</a>
        </nav>

        {/* Right Action CTA */}
        <div className="flex items-center gap-3">
          <span className="hidden xl:flex items-center gap-1 text-xs text-[#006c49] bg-[#6cf8bb]/20 px-2.5 py-1 rounded-full font-medium">
            <ShieldCheck className="w-3.5 h-3.5 text-[#006c49]" />
            NCPOR / MoES
          </span>

          <button
            onClick={onLaunchCockpit}
            className="inline-flex items-center justify-center gap-1.5 px-4 h-10 rounded-lg bg-[#4648d4] text-white text-xs font-semibold hover:bg-[#6063ee] shadow-[0_4px_14px_rgba(70,72,212,0.25)] transition-all active:scale-[0.98]"
          >
            <span>Launch Mission Cockpit</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
