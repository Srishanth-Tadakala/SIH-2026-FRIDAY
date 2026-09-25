import React from 'react';
import { Cpu, GitBranch, ExternalLink } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-white border-t border-[#eaebf0] mt-12 py-12">
      <div className="max-w-[1440px] mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 pb-10">
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-[#4648d4] text-white flex items-center justify-center font-bold text-xs">
                DT
              </div>
              <span className="font-display font-black text-lg text-[#131b2e]">
                DTIARS
              </span>
            </div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#f2f3ff] text-[#131b2e] text-xs font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10b981] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10b981]" />
              </span>
              <span>All 505 Telemetry Channels Synchronized • 99.98%</span>
            </div>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              Station Twins
            </h4>
            <ul className="space-y-2 text-xs text-[#464554]">
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Bharati Station (69°S)</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Maitri Station (70°S)</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Larsemann Hills Topology</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Schirmacher Oasis Hydrology</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              Core Subsystems
            </h4>
            <ul className="space-y-2 text-xs text-[#464554]">
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">400V 50Hz Microgrid</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Thermal HVAC & AHU Dampers</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Potable Water Utilidor</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Polar Satcom Delta Channel</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-display font-bold text-xs text-[#131b2e] uppercase tracking-wider mb-3">
              AI Governance
            </h4>
            <ul className="space-y-2 text-xs text-[#464554]">
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">Groq LPU LLaMA-3.3-70B</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">35-Node Causal DAG</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">What-If Counterfactual Sandbox</a></li>
              <li><a href="#" className="hover:text-[#4648d4] transition-colors">3-Tier Safety Interlocks</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-[#eaebf0] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#464554]">
          <p>© 2026 DTIARS • Digital Twin for Indian Antarctic Research Stations • Problem SIH26060 • Client: NCPOR / MoES Govt of India.</p>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/Srishanth-Tadakala/SIH-2026-FRIDAY"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-[#4648d4] transition-colors flex items-center gap-1 font-medium"
            >
              <GitBranch className="w-4 h-4" />
              <span>GitHub Repository</span>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
