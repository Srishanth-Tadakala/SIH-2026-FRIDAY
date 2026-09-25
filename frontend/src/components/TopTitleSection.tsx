import React, { useState, useEffect } from 'react';
import { ArrowRight, Play, CheckCircle2, Shield, Radio, Clock, Sparkles } from 'lucide-react';

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
      setPolarTime(
        now.toUTCString().replace('GMT', 'UTC')
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="top" className="relative w-full pt-4 pb-8 flex flex-col items-start text-left border-b border-[#eaebf0]/60 mb-8">
      {/* Ambient Auroral Background Soft Glow */}
      <div className="absolute -top-12 -left-20 w-[500px] h-[250px] bg-gradient-to-r from-[#e1e0ff] via-[#acedff] to-[#6ffbbe] opacity-35 blur-3xl -z-10 pointer-events-none rounded-full" />

      {/* Top Meta Bar: SIH Badge + Polar Clock + Satcom Status */}
      <div className="w-full flex flex-wrap items-center justify-between gap-3 mb-4">
        {/* SIH Pill Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#f2f3ff] border border-[#eaedff] text-xs font-semibold text-[#4648d4] shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-[#4648d4]" />
          <span>SIH 2026 • PROBLEM SIH26060 — NCPOR / MoES GOVT OF INDIA</span>
        </div>

        {/* Live Polar Clock & Satcom Pill */}
        <div className="flex items-center gap-2 text-xs text-[#464554]">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#eaebf0] font-mono text-[11px] shadow-xs">
            <Clock className="w-3.5 h-3.5 text-[#006577]" />
            <span>{polarTime || 'POLAR UTC CLOCK'}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] font-medium text-[11px]">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>Satcom Synchronized</span>
          </div>
        </div>
      </div>

      {/* Clean Display Headline (Plus Jakarta Sans) */}
      <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-[46px] leading-[1.14] text-[#131b2e] tracking-tight max-w-4xl">
        Autonomous Polar Digital Twin &amp;{' '}
        <span className="text-[#4648d4] underline decoration-[#6cf8bb] decoration-4 underline-offset-4">
          Multi-Agent
        </span>{' '}
        Cognitive Governor
      </h1>

      {/* Clean Subheadline (Inter) */}
      <p className="font-sans text-base sm:text-lg text-[#464554] max-w-3xl mt-3.5 leading-relaxed">
        Eliminate remote crisis latency. An autonomous multi-agent society governing 505 physics sensors across Bharati and Maitri stations—stabilizing microgrids, preventing utilidor freeze, and actuating mitigations in sub-second timeframes.
      </p>

      {/* Quick CTAs and Micro-Trust Badges Row */}
      <div className="w-full mt-6 flex flex-wrap items-center justify-between gap-4">
        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onLaunchCockpit}
            className="h-11 px-6 rounded-xl bg-[#4648d4] text-white text-xs font-semibold flex items-center gap-2 shadow-md shadow-[#4648d4]/20 hover:bg-[#6063ee] transition-all active:scale-[0.98]"
          >
            <span>Launch Mission Cockpit</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <button
            onClick={onTriggerDemo}
            className="h-11 px-5 rounded-xl bg-white hover:bg-[#f2f3ff] text-[#131b2e] text-xs font-semibold flex items-center gap-2 border border-[#eaebf0] shadow-xs transition-colors"
          >
            <Play className="w-3.5 h-3.5 text-[#4648d4] fill-[#4648d4]" />
            <span>Interactive Crisis Demo (60s)</span>
          </button>
        </div>

        {/* Micro-Trust Pills */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-[#73738c] font-medium">
          <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#eaebf0]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#006c49]" />
            NCPOR Goa
          </span>
          <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#eaebf0]">
            <Shield className="w-3.5 h-3.5 text-[#4648d4]" />
            3-Tier Safety Interlocks
          </span>
          <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#eaebf0]">
            <Radio className="w-3.5 h-3.5 text-[#006577]" />
            505 Sensors
          </span>
        </div>
      </div>
    </section>
  );
};
