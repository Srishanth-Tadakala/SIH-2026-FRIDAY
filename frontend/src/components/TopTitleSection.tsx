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
      setPolarTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="top" className="relative w-full pt-2 pb-6 flex flex-col items-start text-left border-b border-[#eaebf0]/70 mb-7">
      {/* Ambient Auroral Glow */}
      <div className="absolute -top-10 -left-16 w-96 h-48 bg-gradient-to-r from-[#e1e0ff] via-[#acedff] to-[#6ffbbe] opacity-30 blur-3xl -z-10 pointer-events-none rounded-full" />

      {/* Top Meta Bar: SIH Badge + Polar Clock + Satcom Status */}
      <div className="w-full flex flex-wrap items-center justify-between gap-2.5 mb-3.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f2f3ff] border border-[#eaedff] text-[11px] font-semibold text-[#4648d4]">
          <Sparkles className="w-3.5 h-3.5 text-[#4648d4]" />
          <span>SIH 2026 • SIH26060 — NCPOR / MoES GOVT OF INDIA</span>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#464554]">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-[#eaebf0] font-mono text-[11px]">
            <Clock className="w-3.5 h-3.5 text-[#006577]" />
            <span>{polarTime || 'POLAR UTC'}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] font-medium text-[11px]">
            <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
            <span>Satcom Synchronized</span>
          </div>
        </div>
      </div>

      {/* DTIARS Headline with Full Expansion */}
      <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-[44px] leading-[1.12] text-[#131b2e] tracking-tight">
        <span className="text-[#4648d4] font-black mr-3">DTIARS</span>
        Digital Twin for Indian Antarctic Research Stations
        <span className="block text-[#131b2e] text-xl sm:text-2xl font-bold mt-1 text-[#464554]">
          Autonomous Cognitive Operations &amp; Life-Support Governor
        </span>
      </h1>

      {/* Minimal Subhead */}
      <p className="font-sans text-sm sm:text-base text-[#464554] mt-2 max-w-2xl leading-normal">
        Sub-second microgrid stabilization, predictive freeze prevention, and life-critical physics across 505 synchronized sensors for Bharati (69°S) and Maitri (70°S).
      </p>

      {/* Action Buttons & Micro-Trust Badges */}
      <div className="w-full mt-5 flex flex-wrap items-center justify-between gap-3.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={onLaunchCockpit}
            className="h-10 px-5 rounded-xl bg-[#4648d4] text-white text-xs font-semibold flex items-center gap-2 shadow-sm shadow-[#4648d4]/20 hover:bg-[#6063ee] transition-all active:scale-[0.98]"
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

        <div className="flex flex-wrap items-center gap-2 text-xs text-[#73738c] font-medium">
          <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#eaebf0]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#006c49]" />
            NCPOR Goa
          </span>
          <span className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded-lg border border-[#eaebf0]">
            <Shield className="w-3.5 h-3.5 text-[#4648d4]" />
            3-Tier Interlocks
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
