import React, { useState, useEffect } from 'react';
import { StationId, StationInfo, StationSnapshot } from './types';
import { fetchStationSnapshot, fetchStations, injectScenario, clearScenario } from './api';
import { SidebarNavigation, NavView } from './components/SidebarNavigation';
import { TopTitleSection } from './components/TopTitleSection';
import { StationCardsSection } from './components/StationCardsSection';
import { PolarCommandCanvas } from './components/PolarCommandCanvas';
import { InteractiveCrisisBar } from './components/InteractiveCrisisBar';
import { PartnerCloud } from './components/PartnerCloud';
import { BentoCapabilities } from './components/BentoCapabilities';
import { MetricRoiCards } from './components/MetricRoiCards';
import { HeroCtaBanner } from './components/HeroCtaBanner';
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

  return (
    <div className="flex min-h-screen bg-[#faf8ff] text-[#131b2e] antialiased selection:bg-[#4648d4]/15 selection:text-[#4648d4]">
      {/* 1. Left Sidebar Navigation */}
      <SidebarNavigation
        activeStation={station}
        onStationChange={setStation}
        onLaunchCockpit={handleLaunchCockpit}
        activeView={activeView}
        onViewChange={handleViewChange}
      />

      {/* 2. Main Content Area */}
      <div className="flex-1 md:ml-64 lg:ml-72 min-h-screen flex flex-col justify-between overflow-x-hidden pt-16 md:pt-0">
        <main className="w-full max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-10 py-6 lg:py-8 scandi-aura">
          {/* ================= VIEW ROUTING ================= */}
          {activeView === 'overview' && (
            <>
              {/* Clean Minimalist Top Title Section */}
              <TopTitleSection
                onTriggerDemo={() => {
                  const el = document.getElementById('simulator');
                  if (el) el.scrollIntoView({ behavior: 'smooth' });
                }}
                onLaunchCockpit={handleLaunchCockpit}
              />

              {/* 2 Interactive Station Cards (Bharati & Maitri) */}
              <StationCardsSection
                activeStation={station}
                onStationChange={setStation}
                onSelectStationTwin={(st) => {
                  setStation(st);
                  handleViewChange('digital_twin');
                }}
                stationsData={stationsList}
              />

              {/* Digital Twin Command Canvas */}
              <div id="canvas" className="mb-10">
                <PolarCommandCanvas
                  activeStation={station}
                  snapshot={snapshot}
                  activeCrisis={activeCrisis}
                  isResolved={isResolved}
                  onOpenDigitalTwin={() => handleViewChange('digital_twin')}
                />
              </div>

              {/* Interactive Tactile Crisis Bar */}
              <div id="simulator">
                <InteractiveCrisisBar
                  onInject={handleInjectCrisis}
                  onReset={handleReset}
                  activeCrisis={activeCrisis}
                  isResolved={isResolved}
                />
              </div>

              {/* Scientific Partner Cloud */}
              <PartnerCloud />

              {/* 4 Core Capabilities Bento Grid */}
              <div id="capabilities">
                <BentoCapabilities />
              </div>

              {/* Live Metric ROI Cards */}
              <div id="metrics">
                <MetricRoiCards />
              </div>

              {/* Bottom Radiant Launch Banner */}
              <HeroCtaBanner onLaunchCockpit={handleLaunchCockpit} />
            </>
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
        className="fixed bottom-6 right-6 z-40 px-4 py-3 rounded-2xl bg-linear-to-tr from-[#4648d4] to-[#006577] text-white font-mono text-xs font-bold shadow-xl shadow-[#4648d4]/25 hover:shadow-2xl hover:shadow-[#4648d4]/40 hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center gap-2.5 border border-white/20 cursor-pointer"
        title="Open Interactive F.R.I.D.A.Y. AI Copilot"
      >
        <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
        <Sparkles className="w-4 h-4 text-white" />
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
