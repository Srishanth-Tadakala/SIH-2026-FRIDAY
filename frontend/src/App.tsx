import React, { useState, useEffect } from 'react';
import { StationId, StationInfo, StationSnapshot } from './types';
import { fetchStationSnapshot, fetchStations, injectScenario, clearScenario } from './api';
import { SidebarNavigation, NavView } from './components/SidebarNavigation';
import { TopMissionHeader } from './components/TopMissionHeader';
import { OverviewHomeView } from './components/views/OverviewHomeView';
import { StationFleetView } from './components/views/StationFleetView';
import { DigitalTwinView } from './components/views/DigitalTwinView';
import { AgentsView } from './components/views/AgentsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { ActionsView } from './components/views/ActionsView';
import { MemoryView } from './components/views/MemoryView';
import { Footer } from './components/Footer';
import { CopilotDrawer } from './components/CopilotDrawer';
import { Sparkles } from 'lucide-react';

const getInitialView = (): NavView => {
  try {
    const params = new URLSearchParams(window.location.search);
    const viewParam = params.get('view')?.toLowerCase();
    const hash = window.location.hash.replace('#', '').toLowerCase();
    const path = window.location.pathname.replace(/^\//, '').toLowerCase();

    const candidate = viewParam || hash || path;
    const validViews: NavView[] = ['overview', 'stations', 'digital_twin', 'agents', 'memory', 'analytics', 'actions'];
    if (validViews.includes(candidate as NavView)) {
      return candidate as NavView;
    }
  } catch {}
  return 'overview';
};

export function App() {
  const [activeView, setActiveView] = useState<NavView>(getInitialView);
  const [station, setStation] = useState<StationId>('bharati');
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null);
  const [stationsList, setStationsList] = useState<StationInfo[] | null>(null);
  const [activeCrisis, setActiveCrisis] = useState<string | null>(null);
  const [isResolved, setIsResolved] = useState<boolean>(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(false);
  const [opMode, setOpMode] = useState<'AUTO' | 'MANUAL'>('AUTO');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const handleViewChange = (newView: NavView) => {
    setActiveView(newView);
    try {
      const url = new URL(window.location.href);
      if (newView === 'overview') {
        url.searchParams.delete('view');
      } else {
        url.searchParams.set('view', newView);
      }
      window.history.pushState({}, '', url.toString());
    } catch {}
  };

  useEffect(() => {
    const onPopState = () => {
      setActiveView(getInitialView());
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  // Poll Backend Snapshot & Station List
  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const [snap, stations] = await Promise.all([
          fetchStationSnapshot(station),
          fetchStations(),
        ]);
        if (isMounted) {
          if (snap) setSnapshot(snap);
          if (stations) setStationsList(stations);
        }
      } catch {
        // Fallback default snapshot if offline
      }
    };

    loadData();
    const interval = setInterval(loadData, 2500);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [station]);

  // Handle Crisis Injection
  const handleInjectCrisis = async (crisis: string) => {
    setActiveCrisis(crisis);
    setIsResolved(false);

    try {
      const res = await injectScenario(crisis, { station_id: station });
      if (res?.active_scenario) {
        setActiveCrisis(res.active_scenario);
      }
    } catch {}
  };

  const handleReset = async () => {
    try {
      await clearScenario(station);
    } catch {}
    setActiveCrisis(null);
    setIsResolved(false);
  };

  const handleLaunchCockpit = () => {
    window.location.href = '/legacy-ui';
  };

  const handleEmergencyOverride = () => {
    const confirmed = window.confirm(
      'ATTENTION: Trigger EMERGENCY OVERRIDE on Antarctic station life support loops?\n\nThis will force all secondary generators into parallel dispatch and hold utilidor valves open.'
    );
    if (confirmed) {
      handleInjectCrisis('EMERGENCY_OVERRIDE');
    }
  };

  const handleLockdown = () => {
    const confirmed = window.confirm(
      'INITIATE STATION LOCKDOWN?\n\nExternal utilidor blast seals will close and autonomous containment will arm.'
    );
    if (confirmed) {
      handleInjectCrisis('STATION_LOCKDOWN');
    }
  };

  return (
    <div className="flex min-h-screen bg-[#faf8ff] text-[#0d1c2f] antialiased selection:bg-[#4648d4] selection:text-white">
      {/* 1. Fixed Top Mission Header (Polaris Antarctic Command) */}
      <TopMissionHeader
        activeStation={station}
        onStationChange={setStation}
        activeCrisis={activeCrisis}
        opMode={opMode}
        onOpModeChange={setOpMode}
        onEmergencyOverride={handleEmergencyOverride}
        onMobileMenuToggle={() => setMobileMenuOpen((prev) => !prev)}
        mobileMenuOpen={mobileMenuOpen}
      />

      {/* 2. Fixed Left Sidebar Navigation */}
      <SidebarNavigation
        activeStation={station}
        onStationChange={setStation}
        onLaunchCockpit={handleLaunchCockpit}
        activeView={activeView}
        onViewChange={handleViewChange}
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
        onLockdown={handleLockdown}
      />

      {/* 3. Main Command Content Area */}
      <div className="flex-1 md:ml-64 lg:ml-72 min-h-screen flex flex-col justify-between overflow-x-hidden pt-14">
        <main className="w-full max-w-[1500px] mx-auto px-4 sm:px-6 lg:px-8 py-5 scandi-aura">
          {/* ================= VIEW ROUTING ================= */}
          {activeView === 'overview' && (
            <OverviewHomeView
              activeStation={station}
              onStationChange={setStation}
              snapshot={snapshot}
              stationsList={stationsList}
              activeCrisis={activeCrisis}
              isResolved={isResolved}
              onOpenDigitalTwin={() => handleViewChange('digital_twin')}
              onOpenAgents={() => handleViewChange('agents')}
              onOpenActions={() => handleViewChange('actions')}
              onLaunchCockpit={handleLaunchCockpit}
              onInjectCrisis={handleInjectCrisis}
              onResetCrisis={handleReset}
            />
          )}

          {activeView === 'stations' && (
            <StationFleetView
              activeStation={station}
              onStationChange={setStation}
            />
          )}

          {activeView === 'digital_twin' && (
            <DigitalTwinView activeStation={station} />
          )}

          {activeView === 'agents' && (
            <AgentsView activeStation={station} />
          )}

          {activeView === 'memory' && (
            <MemoryView activeStation={station} />
          )}

          {activeView === 'analytics' && (
            <AnalyticsView activeStation={station} />
          )}

          {activeView === 'actions' && (
            <ActionsView activeStation={station} />
          )}
        </main>

        {/* Footer */}
        <Footer />
      </div>

      {/* Floating Ask F.R.I.D.A.Y. AI Copilot Button */}
      <button
        onClick={() => setIsCopilotOpen((prev) => !prev)}
        className="fixed bottom-14 right-6 z-40 px-4 py-2.5 rounded-xl bg-gradient-to-tr from-[#4648d4] to-[#006577] text-white font-mono text-xs font-bold shadow-lg shadow-[#4648d4]/25 hover:shadow-xl hover:shadow-[#4648d4]/40 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center gap-2 border border-white/20 cursor-pointer"
        title="Open Interactive F.R.I.D.A.Y. AI Copilot"
      >
        <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
        <Sparkles className="w-3.5 h-3.5 text-white" />
        <span>Ask F.R.I.D.A.Y.</span>
      </button>

      {/* Interactive Copilot Drawer */}
      <CopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        activeStation={station}
      />
    </div>
  );
}

export default App;
