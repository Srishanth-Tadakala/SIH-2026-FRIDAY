import React, { useState } from 'react';
import { Flame, CloudSnow, Droplet, RotateCcw, ShieldCheck, Zap } from 'lucide-react';

interface InteractiveCrisisBarProps {
  onInject: (crisis: string) => void;
  onReset: () => void;
  activeCrisis: string | null;
  isResolved: boolean;
}

export const InteractiveCrisisBar: React.FC<InteractiveCrisisBarProps> = ({
  onInject,
  onReset,
  activeCrisis,
  isResolved,
}) => {
  const [triggering, setTriggering] = useState<string | null>(null);

  const handleClick = (crisis: string) => {
    setTriggering(crisis);
    onInject(crisis);

    setTimeout(() => {
      setTriggering(null);
    }, 1200);
  };

  return (
    <section id="simulator" className="w-full max-w-6xl mx-auto mt-8 px-4 sm:px-0">
      <div className="p-5 rounded-3xl bg-white border border-[#eaebf0] shadow-xs flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-[#eaebf0] pb-3">
          <h3 className="font-display font-bold text-sm text-[#131b2e]">
            Simulation Test Bench
          </h3>
          <span className="text-[11px] font-mono text-[#4648d4] font-semibold bg-[#faf8ff] px-2.5 py-0.5 rounded-full border border-[#eaedff]">
            Hardware Interlocked
          </span>
        </div>

        {/* 4 Emergency Trigger Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => handleClick('GENERATOR_TRIP')}
            disabled={!!triggering}
            className={`p-3 rounded-2xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'GENERATOR_TRIP'
                ? 'border-[#f43f5e] bg-[#fff1f2] shadow-xs'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#f43f5e]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#f43f5e]/10 text-[#e11d48] flex items-center justify-center">
                <Flame className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-[#131b2e]">Generator Trip</span>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#f43f5e]" />
          </button>

          <button
            onClick={() => handleClick('BLIZZARD_STRIKE')}
            disabled={!!triggering}
            className={`p-3 rounded-2xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'BLIZZARD_STRIKE'
                ? 'border-[#0284c7] bg-[#f0f9ff] shadow-xs'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#0284c7]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#006577]/10 text-[#006577] flex items-center justify-center">
                <CloudSnow className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-[#131b2e]">Katabatic Blizzard</span>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#006577]" />
          </button>

          <button
            onClick={() => handleClick('WATER_LINE_FREEZE')}
            disabled={!!triggering}
            className={`p-3 rounded-2xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'WATER_LINE_FREEZE'
                ? 'border-[#06b6d4] bg-[#ecfeff] shadow-xs'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#06b6d4]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#006577]/10 text-[#006577] flex items-center justify-center">
                <Droplet className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-[#131b2e]">Utilidor Freeze</span>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#006577]" />
          </button>

          <button
            onClick={onReset}
            className="p-3 rounded-2xl border border-[#eaebf0] bg-white hover:bg-[#f2f3ff] text-left flex items-center justify-between transition-all shadow-2xs"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#10b981]/10 text-[#006c49] flex items-center justify-center">
                <RotateCcw className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-[#131b2e]">Restore Baseline</span>
            </div>
          </button>
        </div>

        {/* Live Autonomous Resolution Result Banner */}
        {activeCrisis && (
          <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#a7f3d0] flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in duration-200">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 text-[#006c49]" />
              <p className="text-xs font-mono font-semibold text-[#131b2e]">
                {triggering
                  ? 'Deliberating across 10 cognitive agents...'
                  : activeCrisis === 'GENERATOR_TRIP'
                  ? 'Autonomous Tier 1 ATS: Started CHP-02 (+65 kW). 50.00 Hz nominal.'
                  : activeCrisis === 'BLIZZARD_STRIKE'
                  ? 'Autonomous Mitigation: Sealed fresh air dampers. Heating at 85%.'
                  : 'Autonomous Trace Boost: 24 kWth engaged. Pipe temperature secured.'}
              </p>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-[#ecfdf5] text-[#006c49] text-[11px] font-mono font-bold whitespace-nowrap self-start sm:self-auto">
              {triggering ? 'DELIBERATING' : 'RECOVERED IN 1.2s'}
            </span>
          </div>
        )}
      </div>
    </section>
  );
};
