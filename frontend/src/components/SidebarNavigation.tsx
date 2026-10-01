import React from 'react';
import { 
  LayoutDashboard, 
  Compass, 
  Activity, 
  Users, 
  BarChart3, 
  ShieldCheck, 
  ArrowUpRight, 
  Database,
  Radio,
  Lock,
  X
} from 'lucide-react';
import { StationId } from '../types';

export type NavView = 'overview' | 'stations' | 'digital_twin' | 'agents' | 'memory' | 'analytics' | 'actions';

interface SidebarNavigationProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  onLaunchCockpit: () => void;
  activeView: NavView;
  onViewChange: (view: NavView) => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  onLockdown?: () => void;
}

export const SidebarNavigation: React.FC<SidebarNavigationProps> = ({
  activeStation,
  onStationChange,
  onLaunchCockpit,
  activeView,
  onViewChange,
  mobileOpen = false,
  onMobileClose = () => {},
  onLockdown = () => {},
}) => {
  const navItems: Array<{ id: NavView; label: string; icon: React.ComponentType<{ className?: string }> }> = [
    { id: 'overview', label: 'Overview Telemetry', icon: LayoutDashboard },
    { id: 'digital_twin', label: 'Subsystem Twins', icon: Activity },
    { id: 'stations', label: 'Station Fleet', icon: Compass },
    { id: 'agents', label: 'Agent Consensus', icon: Users },
    { id: 'memory', label: 'Sovereign Memory', icon: Database },
    { id: 'analytics', label: 'Polar Intelligence', icon: BarChart3 },
    { id: 'actions', label: 'Command Actions', icon: ShieldCheck },
  ];

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div 
          onClick={onMobileClose} 
          className="md:hidden fixed inset-0 bg-black/40 backdrop-blur-xs z-40 transition-opacity"
        />
      )}

      {/* Main Sidebar Navigation */}
      <aside 
        className={`fixed top-14 bottom-0 left-0 w-64 lg:w-72 bg-white/95 backdrop-blur-xl border-r border-[#eaebf0] z-40 flex flex-col justify-between p-4 transition-transform duration-300 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="flex flex-col gap-4">
          {/* Station Ops Header & Subsystem Uplink */}
          <div className="flex items-center justify-between px-2 py-2 border-b border-[#eaebf0]">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded bg-[#4648d4] text-white flex items-center justify-center font-bold text-xs">
                ICE
              </div>
              <div>
                <div className="text-xs font-mono font-bold text-[#0d1c2f] tracking-wide leading-none">
                  STATION OPS
                </div>
                <div className="text-[10px] font-mono text-[#006c49] font-medium mt-0.5">
                  UPLINK NOMINAL 99.8%
                </div>
              </div>
            </div>

            {/* Mobile close button inside drawer */}
            <button
              onClick={onMobileClose}
              className="md:hidden p-1 rounded text-[#767586] hover:text-[#0d1c2f]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Station Switcher Context (Available in Drawer for mobile/tablet) */}
          <div className="flex flex-col gap-1.5 px-1">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#767586]">
              Target Station
            </span>
            <div className="grid grid-cols-2 p-1 bg-[#f8f9ff] rounded-lg border border-[#eaebf0] text-xs font-mono font-semibold">
              <button
                onClick={() => {
                  onStationChange('bharati');
                  onMobileClose();
                }}
                className={`py-1 px-2 rounded flex items-center justify-center gap-1.5 transition-all ${
                  activeStation === 'bharati'
                    ? 'bg-white text-[#2c2abc] shadow-xs font-bold border border-[#4648d4]/30'
                    : 'text-[#464554] hover:text-[#0d1c2f]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${activeStation === 'bharati' ? 'bg-[#10b981]' : 'bg-[#767586]'}`} />
                Bharati
              </button>
              <button
                onClick={() => {
                  onStationChange('maitri');
                  onMobileClose();
                }}
                className={`py-1 px-2 rounded flex items-center justify-center gap-1.5 transition-all ${
                  activeStation === 'maitri'
                    ? 'bg-white text-[#2c2abc] shadow-xs font-bold border border-[#4648d4]/30'
                    : 'text-[#464554] hover:text-[#0d1c2f]'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${activeStation === 'maitri' ? 'bg-[#10b981]' : 'bg-[#767586]'}`} />
                Maitri
              </button>
            </div>
          </div>

          {/* Navigation Items (Minimal Technical UI) */}
          <nav className="flex flex-col gap-1">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#767586] px-1 mb-1">
              Command Modules
            </span>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onViewChange(item.id);
                    onMobileClose();
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded text-left transition-all text-xs font-mono ${
                    isActive
                      ? 'border-l-2 border-[#4648d4] bg-[#f8f9ff] text-[#2c2abc] font-bold shadow-2xs'
                      : 'text-[#464554] hover:text-[#0d1c2f] hover:bg-[#f8f9ff]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#4648d4]' : 'text-[#767586]'}`} />
                  <span className="tracking-wide">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Telemetry Quick Status Strip */}
          <div className="p-2.5 rounded bg-[#f8f9ff] border border-[#eaebf0] flex flex-col gap-1.5 text-[11px] font-mono">
            <div className="flex items-center justify-between text-[#464554]">
              <span className="flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#006577]" />
                Satcom Link
              </span>
              <span className="text-[#006c49] font-bold">94.2% Synced</span>
            </div>
            <div className="flex items-center justify-between text-[#464554]">
              <span>Society Quorum</span>
              <span className="font-bold text-[#4648d4]">10/10 Online</span>
            </div>
            <div className="flex items-center justify-between text-[#464554]">
              <span>Microgrid Freq</span>
              <span className="font-bold text-[#10b981]">50.02 Hz</span>
            </div>
          </div>
        </div>

        {/* Bottom Actions: Lockdown, Cockpit & Institutional Attribution */}
        <div className="flex flex-col gap-2.5 pt-3 border-t border-[#eaebf0]">
          {/* System Lockdown Action */}
          <button
            onClick={onLockdown}
            className="w-full py-2 px-3 rounded bg-white border border-[#ba1a1a] text-[#ba1a1a] hover:bg-[#ba1a1a] hover:text-white transition-colors text-[10px] font-mono font-bold tracking-wider flex items-center justify-center gap-2 shadow-2xs"
            title="Arm Station Lockdown Protocol"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>SYSTEM LOCKDOWN</span>
          </button>

          {/* Launch Mission Cockpit Button */}
          <button
            onClick={onLaunchCockpit}
            className="w-full h-10 px-3 rounded bg-[#4648d4] text-white text-xs font-mono font-semibold hover:bg-[#3537b8] transition-all flex items-center justify-between shadow-xs active:scale-[0.98]"
            title="Open Fullscreen Legacy Mission Cockpit"
          >
            <span>Mission Cockpit</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>

          {/* Sovereign Attribution */}
          <div className="flex items-center justify-between px-1 text-[10px] font-mono text-[#767586]">
            <span className="flex items-center gap-1 text-[#006c49] font-semibold">
              <ShieldCheck className="w-3 h-3 text-[#006c49]" />
              NCPOR / MoES
            </span>
            <span>SIH-2026</span>
          </div>
        </div>
      </aside>
    </>
  );
};
