import React from 'react';
import { 
  Construction, 
  ArrowLeft, 
  ArrowUpRight, 
  ShieldCheck, 
  Radio, 
  Cpu, 
  Sparkles,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { StationId } from '../types';

interface UnderMaintenanceViewProps {
  viewId: string;
  title: string;
  description: string;
  activeStation: StationId;
  onBackToOverview: () => void;
  onLaunchCockpit: () => void;
}

export const UnderMaintenanceView: React.FC<UnderMaintenanceViewProps> = ({
  viewId,
  title,
  description,
  activeStation,
  onBackToOverview,
  onLaunchCockpit,
}) => {
  return (
    <div className="w-full max-w-[1100px] mx-auto py-10 flex flex-col items-center text-center">
      {/* Top Breadcrumb & Status Pill */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={onBackToOverview}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white border border-[#eaebf0] text-xs font-medium text-[#464554] hover:text-[#4648d4] hover:border-[#4648d4]/30 shadow-2xs transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Mission Overview</span>
        </button>
        <span className="text-[#c7c4d7]">/</span>
        <span className="text-xs font-mono font-semibold text-[#4648d4] uppercase tracking-wider">
          {viewId}
        </span>
      </div>

      {/* Maintenance Card */}
      <div className="relative w-full rounded-3xl bg-white border border-[#eaedff] shadow-[0_12px_40px_rgba(70,72,212,0.06)] p-8 sm:p-12 overflow-hidden text-left">
        {/* Soft Background Radial Gradient */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-[#f2f3ff] via-[#eaedff]/40 to-transparent rounded-full blur-2xl pointer-events-none -z-0" />

        <div className="relative z-10">
          {/* Top Status Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#fffbeb] border border-[#fef3c7] text-xs font-semibold text-[#b45309]">
              <Construction className="w-4 h-4 text-[#d97706]" />
              <span>MODULE UNDER ACTIVE COMMISSIONING • PHASE II</span>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-[#73738c]">
              <Clock className="w-3.5 h-3.5 text-[#4648d4]" />
              <span>Active Context: </span>
              <span className="font-bold text-[#4648d4] uppercase">
                {activeStation === 'bharati' ? 'Bharati (69°S)' : 'Maitri (70°S)'}
              </span>
            </div>
          </div>

          {/* Module Title */}
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-[#131b2e] tracking-tight leading-tight">
            {title}
          </h1>

          {/* Module Description */}
          <p className="font-sans text-base text-[#464554] mt-3 max-w-2xl leading-relaxed">
            {description}
          </p>

          {/* Integration Status Checklist */}
          <div className="my-8 p-6 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
            <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#4648d4] mb-4 flex items-center gap-2">
              <Cpu className="w-4 h-4" />
              <span>Subsystem Readiness Matrix</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#eaebf0]">
                <CheckCircle2 className="w-4 h-4 text-[#006c49] shrink-0" />
                <div>
                  <div className="font-semibold text-[#131b2e]">FastAPI Backend Telemetry Feed</div>
                  <div className="text-[11px] text-[#73738c]">Live 505 sensors connected (1 Hz)</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#eaebf0]">
                <CheckCircle2 className="w-4 h-4 text-[#006c49] shrink-0" />
                <div>
                  <div className="font-semibold text-[#131b2e]">35-Node Causal Graph RCA</div>
                  <div className="text-[11px] text-[#73738c]">Topological Bayesian routing active</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#eaebf0]">
                <CheckCircle2 className="w-4 h-4 text-[#006c49] shrink-0" />
                <div>
                  <div className="font-semibold text-[#131b2e]">Groq LPU 10-Agent Cognitive Society</div>
                  <div className="text-[11px] text-[#73738c]">Sub-400ms multi-agent bus armed</div>
                </div>
              </div>

              <div className="flex items-center gap-2.5 p-3 rounded-xl bg-white border border-[#eaedff] ring-1 ring-[#4648d4]/20">
                <span className="w-4 h-4 rounded-full border-2 border-[#4648d4] border-t-transparent animate-spin shrink-0" />
                <div>
                  <div className="font-semibold text-[#4648d4]">Dedicated UI Canvas Assembly</div>
                  <div className="text-[11px] text-[#73738c]">Scheduled for modular sprint rollout</div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons Row */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#eaebf0]">
            <div className="flex items-center gap-3">
              <button
                onClick={onBackToOverview}
                className="h-11 px-5 rounded-xl bg-[#f2f3ff] hover:bg-[#eaedff] text-[#4648d4] font-semibold text-xs transition-colors flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Return to Overview</span>
              </button>

              <button
                onClick={onLaunchCockpit}
                className="h-11 px-6 rounded-xl bg-[#4648d4] hover:bg-[#6063ee] text-white font-semibold text-xs shadow-md shadow-[#4648d4]/20 transition-all flex items-center gap-2 active:scale-[0.98]"
              >
                <span>Inspect in Tactical Cockpit</span>
                <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-4 text-xs text-[#73738c]">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-[#006c49]" />
                NCPOR / MoES
              </span>
              <span className="flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-[#006577]" />
                505 Channels
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
