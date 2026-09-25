import React, { useState, useEffect } from 'react';
import { StationId, StationSnapshot } from './types';
import { fetchStationSnapshot, injectScenario, clearScenario } from './api';
import { NavigationHeader } from './components/NavigationHeader';
import { HeroSection } from './components/HeroSection';
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
  const [activeCrisis, setActiveCrisis] = useState<string | null>(null);
  const [isResolved, setIsResolved] = useState<boolean>(false);

  // Poll Backend Snapshot
  useEffect(() => {
    let isMounted = true;
    const loadSnapshot = async () => {
      try {
        const snap = await fetchStationSnapshot(station);
        if (isMounted && snap) {
          setSnapshot(snap);
        }
      } catch {
        // Fallback default snapshot if offline
      }
    };

    loadSnapshot();
    const interval = setInterval(loadSnapshot, 2500);
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
    <div className="flex flex-col min-h-screen bg-[#faf8ff] text-[#131b2e] antialiased selection:bg-[#4648d4]/15 selection:text-[#4648d4]">
      {/* Navigation Header */}
      <NavigationHeader
        activeStation={station}
        onStationChange={setStation}
        onLaunchCockpit={handleLaunchCockpit}
      />

      {/* Main Homepage Flow */}
      <main className="w-full pt-16 scandi-aura">
        {/* 1. Hero Section */}
        <HeroSection
          onTriggerDemo={() => {
            const el = document.getElementById('simulator');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
          }}
          onLaunchCockpit={handleLaunchCockpit}
        />

        {/* 2. Central Product Showcase Canvas */}
        <div className="px-4 sm:px-6">
          <PolarCommandCanvas
            kpis={snapshot?.kpis || null}
            activeCrisis={activeCrisis}
            isResolved={isResolved}
          />
        </div>

        {/* 3. Interactive Tactile Crisis Bar */}
        <InteractiveCrisisBar
          onInject={handleInjectCrisis}
          onReset={handleReset}
          activeCrisis={activeCrisis}
          isResolved={isResolved}
        />

        {/* 4. Scientific Partner & Institution Cloud */}
        <PartnerCloud />

        {/* 5. 4 Core Capabilities Bento Grid */}
        <BentoCapabilities />

        {/* 6. Live Metric ROI Cards */}
        <MetricRoiCards />

        {/* 7. Bottom Radiant CTA Banner */}
        <HeroCtaBanner onLaunchCockpit={handleLaunchCockpit} />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
