import React, { useState, useEffect } from 'react';
import { StationId, StationInfo, StationSnapshot } from './types';
import { fetchStationSnapshot, fetchStations, injectScenario, clearScenario } from './api';
import { SidebarNavigation } from './components/SidebarNavigation';
import { TopTitleSection } from './components/TopTitleSection';
import { StationCardsSection } from './components/StationCardsSection';
import { PolarCommandCanvas } from './components/PolarCommandCanvas';
import { InteractiveCrisisBar } from './components/InteractiveCrisisBar';
import { PartnerCloud } from './components/PartnerCloud';
import { BentoCapabilities } from './components/BentoCapabilities';
import { MetricRoiCards } from './components/MetricRoiCards';
import { HeroCtaBanner } from './components/HeroCtaBanner';
import { Footer } from './components/Footer';

export function App() {
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
          fetchStations()
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
      />

      {/* 2. Main Clean Content Area */}
      <div className="flex-1 md:ml-64 lg:ml-72 min-h-screen flex flex-col justify-between overflow-x-hidden pt-16 md:pt-0">
        <main className="w-full max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-10 py-6 lg:py-8 scandi-aura">
          {/* A. Clean Top Title Section */}
          <TopTitleSection
            onTriggerDemo={() => {
              const el = document.getElementById('simulator');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
            onLaunchCockpit={handleLaunchCockpit}
          />

          {/* B. 2 Interactive Station Cards (Bharati & Maitri) */}
          <StationCardsSection
            activeStation={station}
            onStationChange={setStation}
            stationsData={stationsList}
          />

          {/* C. Central Product Showcase Canvas */}
          <div id="canvas" className="mb-10">
            <PolarCommandCanvas
              kpis={snapshot?.kpis || null}
              activeCrisis={activeCrisis}
              isResolved={isResolved}
            />
          </div>

          {/* D. Interactive Tactile Crisis Bar */}
          <InteractiveCrisisBar
            onInject={handleInjectCrisis}
            onReset={handleReset}
            activeCrisis={activeCrisis}
            isResolved={isResolved}
          />

          {/* E. Scientific Partner Cloud */}
          <PartnerCloud />

          {/* F. 4 Core Capabilities Bento Grid */}
          <BentoCapabilities />

          {/* G. Live Metric ROI Cards */}
          <MetricRoiCards />

          {/* H. Bottom Radiant CTA Banner */}
          <HeroCtaBanner onLaunchCockpit={handleLaunchCockpit} />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
}

export default App;
