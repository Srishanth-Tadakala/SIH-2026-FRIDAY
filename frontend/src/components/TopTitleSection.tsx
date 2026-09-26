import React, { useState, useEffect } from 'react';
import { ArrowRight, Play, Clock, Sparkles } from 'lucide-react';

interface TopTitleSectionProps {
  onTriggerDemo: () => void;
  onLaunchCockpit: () => void;
}

export const TopTitleSection: React.FC<TopTitleSectionProps> = ({
  onTriggerDemo,
  onLaunchCockpit,
}) => {
  const [polarTime, setPolarTime] = useState<string>('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setPolarTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="top" className="relative w-full pt-2 pb-6 flex flex-col items-start text-left border-b border-[#eaebf0]/70 mb-7">
      {/* Top Meta Bar: Project Badge + Polar Clock + Satcom Status */}
      <div className="w-full flex flex-wrap items-center justify-between gap-2.5 mb-3.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f2f3ff] border border-[#eaedff] text-[11px] font-semibold text-[#4648d4] font-mono">
          <Sparkles className="w-3.5 h-3.5 text-[#4648d4]" />
          <span>DTIARS • NCPOR / MoES</span>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#464554]">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#eaebf0] font-mono text-[11px] shadow-2xs">
            <Clock className="w-3.5 h-3.5 text-[#006577]" />
            <span>{polarTime || 'POLAR UTC'}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] font-medium text-[11px] font-mono shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>Satcom Synchronized</span>
          </div>
        </div>
      </div>

      {/* DTIARS Headline */}
      <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-[44px] leading-[1.12] text-[#131b2e] tracking-tight">
        <span className="text-[#4648d4] font-black mr-3">DTIARS</span>
        Digital Twin for Indian Antarctic Research Stations
      </h1>

      {/* Action Buttons */}
      <div className="w-full mt-5 flex flex-wrap items-center gap-3">
        <button
          onClick={onLaunchCockpit}
          className="h-10 px-5 rounded-xl bg-[#4648d4] text-white text-xs font-semibold flex items-center gap-2 shadow-sm shadow-[#4648d4]/20 hover:bg-[#3b3dbf] transition-all active:scale-[0.98]"
        >
          <span>Launch Mission Cockpit</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onTriggerDemo}
          className="h-10 px-4 rounded-xl bg-white hover:bg-[#f2f3ff] text-[#131b2e] text-xs font-semibold flex items-center gap-2 border border-[#eaebf0] shadow-2xs transition-colors"
        >
          <Play className="w-3 h-3 text-[#4648d4] fill-[#4648d4]" />
          <span>Crisis Simulator</span>
        </button>
      </div>
    </section>
  );
};
