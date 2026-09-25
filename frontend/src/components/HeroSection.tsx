import React from 'react';
import { ArrowRight, Play, CheckCircle2, Shield, Radio, Award } from 'lucide-react';

interface HeroSectionProps {
  onTriggerDemo: () => void;
  onLaunchCockpit: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onTriggerDemo,
  onLaunchCockpit,
}) => {
  return (
    <section className="relative w-full max-w-[1440px] mx-auto px-6 pt-12 pb-12 lg:pt-16 lg:pb-16 flex flex-col items-center text-center">
      {/* Ambient Auroral Background Glow */}
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[720px] h-[340px] bg-gradient-to-r from-[#e1e0ff] via-[#acedff] to-[#6ffbbe] opacity-50 blur-3xl -z-10 pointer-events-none rounded-full" />

      {/* Pill Badge */}
      <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#eaedff] backdrop-blur-md shadow-sm mb-6 border border-[#c7c4d7]/40">
        <span className="inline-flex h-2 w-2 rounded-full bg-[#006c49] animate-ping" />
        <span className="text-xs uppercase tracking-wider font-semibold text-[#4648d4]">
          ✨ SIH 2026 • PROBLEM SIH26060 — AUTONOMOUS POLAR DIGITAL TWIN
        </span>
      </div>

      {/* Main Display Headline (Plus Jakarta Sans) */}
      <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-[54px] leading-[1.12] text-[#131b2e] tracking-tight max-w-4xl">
        Antarctic station autonomy that feels{' '}
        <span className="text-[#4648d4] underline decoration-[#6cf8bb] decoration-4 underline-offset-4">
          effortless
        </span>
        , resilient, and life-critical.
      </h1>

      {/* Subheadline (Inter) */}
      <p className="font-sans text-base sm:text-lg text-[#464554] max-w-2xl mt-5 leading-relaxed">
        Eliminate remote crisis delays. An autonomous multi-agent digital twin governing 505 physical sensors across Bharati and Maitri stations—stabilizing microgrids, preventing pipe freeze, and actuating mitigations in sub-second timeframes.
      </p>

      {/* Primary Action Buttons Row */}
      <div className="w-full max-w-lg mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={onLaunchCockpit}
          className="w-full sm:w-auto h-12 px-7 rounded-xl bg-[#4648d4] text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-[#4648d4]/25 hover:bg-[#6063ee] transition-all active:scale-[0.98] text-sm"
        >
          <span>Launch Mission Cockpit</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <button
          onClick={onTriggerDemo}
          className="w-full sm:w-auto h-12 px-6 rounded-xl bg-[#eaedff] hover:bg-[#e2e7ff] text-[#131b2e] font-semibold flex items-center justify-center gap-2 transition-colors text-sm border border-[#c7c4d7]/40"
        >
          <Play className="w-4 h-4 text-[#4648d4] fill-[#4648d4]" />
          <span>Interactive Crisis Demo (60s)</span>
        </button>
      </div>

      {/* Micro Trust Indicators Row */}
      <div className="flex flex-wrap items-center justify-center gap-4 text-[#464554] text-xs font-medium mt-6">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-[#006c49]" />
          Client: NCPOR / MoES Govt of India
        </span>
        <span className="text-[#c7c4d7]">•</span>
        <span className="flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-[#4648d4]" />
          3-Tier Defense Safety Interlocks
        </span>
        <span className="text-[#c7c4d7]">•</span>
        <span className="flex items-center gap-1.5">
          <Radio className="w-4 h-4 text-[#006577]" />
          505 Physics Sensor Telemetry
        </span>
      </div>

      {/* Floating Trust Badges */}
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[#eaebf0] shadow-sm text-xs text-[#131b2e]">
          <Award className="w-4 h-4 text-[#f59e0b]" />
          <span><strong>1.2s</strong> Autonomous Resolution vs 45 min remote delay</span>
        </div>

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[#eaebf0] shadow-sm text-xs text-[#131b2e]">
          <span className="w-2 h-2 rounded-full bg-[#10b981]" />
          <span><strong>99.98%</strong> Station Life-Support Envelope Preserved</span>
        </div>
      </div>
    </section>
  );
};
