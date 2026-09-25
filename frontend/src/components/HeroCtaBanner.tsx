import React from 'react';
import { ArrowRight, BookOpen } from 'lucide-react';

interface HeroCtaBannerProps {
  onLaunchCockpit: () => void;
}

export const HeroCtaBanner: React.FC<HeroCtaBannerProps> = ({ onLaunchCockpit }) => {
  return (
    <section className="w-full max-w-[1440px] mx-auto px-6 py-16">
      <div className="relative rounded-3xl bg-gradient-to-br from-[#4648d4] via-[#5356e8] to-[#006577] text-white p-10 sm:p-16 shadow-2xl overflow-hidden text-center">
        {/* Ambient Decorative Light Orbs */}
        <div className="absolute -top-24 -left-24 w-72 h-72 bg-[#6cf8bb] opacity-25 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-72 h-72 bg-[#acedff] opacity-25 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl mx-auto space-y-6">
          <h2 className="font-display font-extrabold text-3xl sm:text-4xl text-white tracking-tight leading-tight">
            Ready to Launch DTIARS Mission Cockpit?
          </h2>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onLaunchCockpit}
              className="w-full sm:w-auto h-12 px-8 rounded-xl bg-white text-[#4648d4] font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#f2f3ff] transition-all shadow-lg active:scale-[0.98]"
            >
              <span>Launch Mission Cockpit</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <a
              href="https://github.com/Srishanth-Tadakala/SIH-2026-FRIDAY"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto h-12 px-6 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-colors border border-white/20"
            >
              <BookOpen className="w-4 h-4" />
              <span>GitHub Documentation</span>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
