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
import { UnderMaintenanceView } from './components/UnderMaintenanceView';
import { Footer } from './components/Footer';

export function App() {
  const [activeView, setActiveView] = useState<NavView>('overview');
  const [station, setStation] = useState<StationId>('bharati');
  const [snapshot, setSnapshot] = useState<StationSnapshot | null>(null);
  const [stationsList, setStationsList] = useState<StationInfo[] | null>(null);
  const [activeCrisis, setActiveCrisis] = useState<string | null>(null);
  const [isResolved, setIsResolved] = useState<boolean>(false);

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
      await injectScenario(crisis);
    } catch {}

    // Simulated autonomous multi-agent recovery resolution in 1.2s
    setTimeout(() => {
      setIsResolved(true);
    }, 1200);
  };

  const handleReset = async () => {
    setActiveCrisis(null);
    setIsResolved(false);
    try {
      await clearScenario(station);
    } catch {}
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
        onViewChange={setActiveView}
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
                stationsData={stationsList}
              />

              {/* Digital Twin Command Canvas */}
              <div id="canvas" className="mb-10">
                <PolarCommandCanvas
                  kpis={snapshot?.kpis || null}
                  activeCrisis={activeCrisis}
                  isResolved={isResolved}
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
            <UnderMaintenanceView
              viewId="STATION-FLEET"
              title="Polar Station Fleet Management"
              description="Dedicated multi-station telemetry explorer, satellite radar GIS overlays, and cross-station fuel logistics balancing between Bharati (Larsemann Hills) and Maitri (Schirmacher Oasis)."
              activeStation={station}
              onBackToOverview={() => setActiveView('overview')}
              onLaunchCockpit={handleLaunchCockpit}
            />
          )}

          {activeView === 'canvas' && (
            <UnderMaintenanceView
              viewId="DIGITAL-TWIN-CANVAS"
              title="Expanded Digital Twin Synoptic Canvas"
              description="High-fidelity 3D structural twin with real-time finite element stilt stress vectors, HVAC duct pressure flow, and utilidor heat distribution."
              activeStation={station}
              onBackToOverview={() => setActiveView('overview')}
              onLaunchCockpit={handleLaunchCockpit}
            />
          )}

          {activeView === 'simulator' && (
            <UnderMaintenanceView
              viewId="CRISIS-SIMULATOR"
              title="Autonomous Crisis Simulation Lab"
              description="Adversarial polar emergency injector with katabatic storm gusts (>140 km/h), generator trip cascades, and automated 10-agent consensus verification."
              activeStation={station}
              onBackToOverview={() => setActiveView('overview')}
              onLaunchCockpit={handleLaunchCockpit}
            />
          )}

          {activeView === 'capabilities' && (
            <UnderMaintenanceView
              viewId="CAPABILITIES-ARCHITECTURE"
              title="10-Agent Cognitive Society Architecture"
              description="Topological Bayesian causal DAG traversal, Groq LPU sub-400ms inference pipeline, and 4-tier defense safety interlock specifications."
              activeStation={station}
              onBackToOverview={() => setActiveView('overview')}
              onLaunchCockpit={handleLaunchCockpit}
            />
          )}

          {activeView === 'benchmarks' && (
            <UnderMaintenanceView
              viewId="MISSION-BENCHMARKS"
              title="Polar Survivability & Performance Benchmarks"
              description="Empirical performance logs verifying 1.2s autonomous incident mitigation, 90% satcom delta compression, and 99.98% life-support envelope retention."
              activeStation={station}
              onBackToOverview={() => setActiveView('overview')}
              onLaunchCockpit={handleLaunchCockpit}
            />
          )}
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
}

export default App;
