import React from 'react';
import { ArrowRight, BookOpen } from 'lucide-react';

interface HeroCtaBannerProps {
  onLaunchCockpit: () => void;
}

export const HeroCtaBanner: React.FC<HeroCtaBannerProps> = ({ onLaunchCockpit }) => {
  return (
    <section className="w-full max-w-[1440px] mx-auto px-6 py-12">
      <div className="relative rounded-3xl bg-gradient-to-r from-[#4648d4] to-[#006577] text-white p-8 sm:p-12 shadow-xl overflow-hidden flex flex-col sm:flex-row items-center justify-between gap-6">
        <div>
          <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-white tracking-tight leading-tight">
            DTIARS Mission Cockpit
          </h2>
          <span className="text-xs font-mono opacity-80 mt-1 block">
            Integrated Polar Command Interface • NCPOR / MoES
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onLaunchCockpit}
            className="h-11 px-6 rounded-xl bg-white text-[#4648d4] font-bold text-xs flex items-center gap-2 hover:bg-[#f2f3ff] transition-all shadow-md active:scale-[0.98]"
          >
            <span>Launch Cockpit</span>
            <ArrowRight className="w-4 h-4" />
          </button>

          <a
            href="https://github.com/Srishanth-Tadakala/SIH-2026-FRIDAY"
            target="_blank"
            rel="noopener noreferrer"
            className="h-11 px-5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-xs flex items-center gap-2 transition-colors border border-white/20"
          >
            <BookOpen className="w-4 h-4" />
            <span>GitHub</span>
          </a>
        </div>
      </div>
    </section>
  );
};
