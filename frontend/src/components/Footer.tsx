import React from 'react';
import { GitBranch } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-white border-t border-[#eaebf0] mt-10 py-10">
      <div className="max-w-[1440px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 pb-8">
          <div className="lg:col-span-2 space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#4648d4] text-white flex items-center justify-center font-bold text-xs">
                DT
              </div>
              <span className="font-display font-black text-lg text-[#131b2e]">
                DTIARS
              </span>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#faf8ff] border border-[#eaedff] text-[#131b2e] text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              <span>505 Telemetry Channels Synchronized</span>
            </div>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              Stations
            </h4>
            <ul className="space-y-2 text-xs text-[#73738c] font-mono">
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Bharati (69°24'S)</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Maitri (70°45'S)</span></li>
            </ul>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              Subsystems
            </h4>
            <ul className="space-y-2 text-xs text-[#73738c] font-mono">
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">400V 50Hz Microgrid</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">HVAC Life Support</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Utilidor Potable Line</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Satcom Delta Sync</span></li>
            </ul>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              Governance
            </h4>
            <ul className="space-y-2 text-xs text-[#73738c] font-mono">
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">10-Agent Society</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Causal DAG Traversal</span></li>
              <li><span className="hover:text-[#4648d4] transition-colors cursor-pointer">Tier 1 Interlocks</span></li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-[#eaebf0] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#73738c] font-mono">
          <p>© 2026 DTIARS • Indian Antarctic Research Stations • NCPOR / MoES Govt of India.</p>
          <a
            href="https://github.com/Srishanth-Tadakala/SIH-2026-FRIDAY"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#4648d4] transition-colors flex items-center gap-1.5 font-semibold text-[#131b2e]"
          >
            <GitBranch className="w-4 h-4 text-[#4648d4]" />
            <span>GitHub Repository</span>
          </a>
        </div>
      </div>
    </footer>
  );
};
