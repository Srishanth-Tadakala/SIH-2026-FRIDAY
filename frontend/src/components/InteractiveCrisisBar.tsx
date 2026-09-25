import React, { useState } from 'react';
import { Flame, CloudSnow, Droplet, RotateCcw, ShieldCheck, Zap } from 'lucide-react';
import confetti from 'canvas-confetti';

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
      // Trigger Scandi celebratory particle burst
      confetti({
        particleCount: 35,
        spread: 50,
        origin: { y: 0.8 },
        colors: ['#4648d4', '#10b981', '#06b6d4'],
      });
    }, 1200);
  };

  return (
    <section id="simulator" className="w-full max-w-6xl mx-auto mt-10 px-4 sm:px-0">
      <div className="p-6 rounded-2xl bg-white border border-[#eaebf0] shadow-sm flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#eaebf0] pb-3">
          <div>
            <h3 className="font-display font-bold text-base text-[#131b2e]">
              Polar Crisis Simulator
            </h3>
          </div>
          <span className="text-xs text-[#464554] font-medium bg-[#f2f3ff] px-3 py-1 rounded-full w-fit">
            3-Tier Safety Interlocks
          </span>
        </div>

        {/* 4 Emergency Trigger Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => handleClick('GENERATOR_TRIP')}
            disabled={!!triggering}
            className={`p-3.5 rounded-xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'GENERATOR_TRIP'
                ? 'border-[#f43f5e] bg-[#ffdad6]/30 shadow-sm'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#4648d4]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#f43f5e]/10 text-[#ba1a1a] flex items-center justify-center">
                <Flame className="w-4 h-4" />
              </div>
              <p className="text-xs font-bold text-[#131b2e]">Generator Trip</p>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#f43f5e]" />
          </button>

          <button
            onClick={() => handleClick('BLIZZARD_STRIKE')}
            disabled={!!triggering}
            className={`p-3.5 rounded-xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'BLIZZARD_STRIKE'
                ? 'border-[#4648d4] bg-[#eaedff] shadow-sm'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#4648d4]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#006577]/10 text-[#006577] flex items-center justify-center">
                <CloudSnow className="w-4 h-4" />
              </div>
              <p className="text-xs font-bold text-[#131b2e]">Katabatic Blizzard</p>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#006577]" />
          </button>

          <button
            onClick={() => handleClick('WATER_LINE_FREEZE')}
            disabled={!!triggering}
            className={`p-3.5 rounded-xl border text-left flex items-center justify-between transition-all ${
              activeCrisis === 'WATER_LINE_FREEZE'
                ? 'border-[#006577] bg-[#acedff]/30 shadow-sm'
                : 'border-[#eaebf0] bg-[#faf8ff] hover:border-[#4648d4]/40 hover:bg-white'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#006577]/10 text-[#006577] flex items-center justify-center">
                <Droplet className="w-4 h-4" />
              </div>
              <p className="text-xs font-bold text-[#131b2e]">Utilidor Freeze</p>
            </div>
            <Zap className="w-3.5 h-3.5 text-[#006577]" />
          </button>

          <button
            onClick={onReset}
            className="p-3.5 rounded-xl border border-[#eaebf0] bg-white hover:bg-[#f2f3ff] text-left flex items-center justify-between transition-all"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[#10b981]/10 text-[#006c49] flex items-center justify-center">
                <RotateCcw className="w-4 h-4" />
              </div>
              <p className="text-xs font-bold text-[#131b2e]">Restore Baseline</p>
            </div>
          </button>
        </div>

        {/* Live Autonomous Resolution Result Banner */}
        {activeCrisis && (
          <div className="p-3.5 rounded-xl bg-[#f2f3ff] border border-[#6cf8bb] flex flex-col sm:flex-row sm:items-center justify-between gap-3 animate-in fade-in duration-300">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-[#10b981] text-white flex items-center justify-center">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <p className="text-xs font-bold text-[#131b2e]">
                  {triggering ? 'AI Deliberation in progress across 10 specialized agents...' : 'Autonomous Mitigation Executed in 1.2s • Tier 1 Autonomy'}
                </p>
                <p className="text-[11px] text-[#464554]">
                  {triggering
                    ? 'Synthesizing Causal DAG root cause and executing What-If physics simulation...'
                    : activeCrisis === 'GENERATOR_TRIP'
                    ? 'Started Standby Generator CHP-02 (+65 kW). Microgrid frequency nominal at 50.00 Hz.'
                    : activeCrisis === 'BLIZZARD_STRIKE'
                    ? 'Sealed AHU fresh air dampers to 0%. Hydronic heating boosted to 85%.'
                    : 'Energized utilidor potable water trace heating. Pipe temperature secured at +4.8°C.'}
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full bg-[#6cf8bb] text-[#002113] text-xs font-bold whitespace-nowrap self-start sm:self-auto">
              {triggering ? 'DELIBERATING...' : '100% RECOVERED'}
            </span>
          </div>
        )}
      </div>
    </section>
  );
};
