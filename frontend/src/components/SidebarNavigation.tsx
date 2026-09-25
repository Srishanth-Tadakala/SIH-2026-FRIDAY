import React, { useState } from 'react';
import { 
  Cpu, 
  LayoutDashboard, 
  Compass, 
  Activity, 
  Users, 
  BarChart3, 
  ShieldCheck, 
  ArrowUpRight, 
  Menu, 
  X,
  Radio
} from 'lucide-react';
import { StationId } from '../types';

export type NavView = 'overview' | 'stations' | 'digital_twin' | 'agents' | 'analytics' | 'actions';

interface SidebarNavigationProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  onLaunchCockpit: () => void;
  activeView: NavView;
  onViewChange: (view: NavView) => void;
}

export const SidebarNavigation: React.FC<SidebarNavigationProps> = ({
  activeStation,
  onStationChange,
  onLaunchCockpit,
  activeView,
  onViewChange,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems: Array<{ id: NavView; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'stations', label: 'Station Fleet', icon: Compass },
    { id: 'digital_twin', label: 'Digital Twin', icon: Activity },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'actions', label: 'Actions', icon: ShieldCheck },
  ];

  return (
    <>
      {/* Mobile Top Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 bg-white/95 backdrop-blur-md border-b border-[#eaebf0] z-50 px-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#4648d4] text-white flex items-center justify-center shadow-md shadow-[#4648d4]/20 font-bold text-xs">
            DT
          </div>
          <div>
            <span className="font-display font-bold text-base text-[#131b2e] leading-none">DTIARS</span>
            <span className="block text-[9px] font-mono text-[#464554]">POLAR DIGITAL TWIN</span>
          </div>
        </div>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-2 rounded-lg text-[#464554] hover:bg-[#eaedff] transition-colors"
          aria-label="Toggle navigation menu"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div 
          onClick={() => setMobileOpen(false)} 
          className="md:hidden fixed inset-0 bg-black/30 backdrop-blur-xs z-40"
        />
      )}

      {/* Main Sidebar Navigation */}
      <aside 
        className={`fixed top-0 bottom-0 left-0 w-64 lg:w-72 bg-white/95 backdrop-blur-xl border-r border-[#eaebf0] z-50 flex flex-col justify-between p-5 transition-transform duration-300 md:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="flex flex-col gap-5">
          {/* Brand Logo & System Status */}
          <div className="pt-1">
            <button 
              onClick={() => {
                onViewChange('overview');
                setMobileOpen(false);
              }}
              className="w-full flex items-center gap-3 group text-left"
            >
              <div className="w-10 h-10 rounded-xl bg-[#4648d4] text-white flex items-center justify-center shadow-md shadow-[#4648d4]/25 group-hover:scale-105 transition-transform font-bold text-sm">
                DT
              </div>
              <div className="flex flex-col">
                <span className="font-display font-black text-2xl text-[#131b2e] tracking-tight leading-none">
                  DTIARS
                </span>
                <span className="text-[9px] font-mono font-bold text-[#4648d4] tracking-wide mt-1 uppercase leading-tight line-clamp-1">
                  INDIAN ANTARCTIC DIGITAL TWIN
                </span>
              </div>
            </button>

            {/* Defense Status Pill */}
            <div className="mt-4 px-3 py-1.5 rounded-lg bg-[#f2f3ff] border border-[#eaedff] flex items-center justify-between text-[11px] font-semibold text-[#4648d4]">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
                DEFENSE OPERATIONAL
              </span>
              <span className="font-mono text-[10px] text-[#464554]">505 CH</span>
            </div>
          </div>

          {/* Station Context Switcher (Quick Toggle) */}
          <div className="flex flex-col gap-1.5">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#73738c]">
              Target Station Context
            </span>
            <div className="grid grid-cols-2 p-1 bg-[#f2f3ff] rounded-xl border border-[#eaedff] text-xs font-semibold">
              <button
                onClick={() => {
                  onStationChange('bharati');
                  setMobileOpen(false);
                }}
                className={`py-1.5 px-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeStation === 'bharati'
                    ? 'bg-white text-[#4648d4] shadow-sm font-bold'
                    : 'text-[#464554] hover:text-[#131b2e]'
                }`}
              >
                <Compass className="w-3.5 h-3.5 text-[#4648d4]" />
                Bharati
              </button>
              <button
                onClick={() => {
                  onStationChange('maitri');
                  setMobileOpen(false);
                }}
                className={`py-1.5 px-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeStation === 'maitri'
                    ? 'bg-white text-[#4648d4] shadow-sm font-bold'
                    : 'text-[#464554] hover:text-[#131b2e]'
                }`}
              >
                <Compass className="w-3.5 h-3.5 text-[#4648d4]" />
                Maitri
              </button>
            </div>
          </div>

          {/* Navigation Links (Module Tabs) */}
          <nav className="flex flex-col gap-1 text-sm font-medium">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#73738c] mb-1">
              Navigation Console
            </span>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onViewChange(item.id);
                    setMobileOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left text-sm font-medium ${
                    isActive
                      ? 'bg-[#4648d4] text-white font-semibold shadow-xs'
                      : 'text-[#464554] hover:text-[#4648d4] hover:bg-[#f2f3ff]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#73738c]'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Live Telemetry Health Mini Capsule */}
          <div className="p-3 rounded-xl bg-gradient-to-br from-[#faf8ff] to-[#f2f3ff] border border-[#eaedff] flex flex-col gap-2">
            <div className="flex items-center justify-between text-[11px] text-[#464554] font-medium">
              <span className="flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#006577]" />
                Satcom Link
              </span>
              <span className="text-[#006c49] font-semibold">94.2% Delta</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-[#464554] font-medium">
              <span>Cognitive Society</span>
              <span className="font-semibold text-[#4648d4]">10 Agents Active</span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-[#464554] font-medium">
              <span>Grid Frequency</span>
              <span className="font-mono font-semibold text-[#10b981]">50.00 Hz</span>
            </div>
          </div>
        </div>

        {/* Bottom Actions & Institutional Attribution */}
        <div className="flex flex-col gap-3 pt-4 border-t border-[#eaebf0]">
          {/* Launch Mission Cockpit Button */}
          <button
            onClick={onLaunchCockpit}
            className="w-full h-11 px-4 rounded-xl bg-[#4648d4] text-white text-xs font-semibold hover:bg-[#6063ee] shadow-[0_4px_14px_rgba(70,72,212,0.22)] transition-all flex items-center justify-between active:scale-[0.98]"
          >
            <span>Launch Mission Cockpit</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>

          {/* Institutional Badge */}
          <div className="flex items-center justify-between px-2 text-[11px] text-[#73738c]">
            <span className="flex items-center gap-1 font-medium text-[#006c49]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#006c49]" />
              NCPOR / MoES
            </span>
            <span className="font-mono text-[10px]">DTIARS</span>
          </div>
        </div>
      </aside>
    </>
  );
};
