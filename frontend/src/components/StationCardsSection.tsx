import React from 'react';
import { 
  Compass, 
  Zap, 
  Thermometer, 
  Wind, 
  Fuel, 
  Droplet, 
  CheckCircle2, 
  Radio, 
  ArrowRight,
  ShieldAlert,
  Cpu
} from 'lucide-react';
import { StationId, StationInfo } from '../types';

interface StationCardsSectionProps {
  activeStation: StationId;
  onStationChange: (station: StationId) => void;
  onSelectStationTwin: (station: StationId) => void;
  stationsData?: StationInfo[] | null;
}

export const StationCardsSection: React.FC<StationCardsSectionProps> = ({
  activeStation,
  onStationChange,
  onSelectStationTwin,
  stationsData,
}) => {
  const bharatiData = stationsData?.find((s) => s.station_id === 'bharati');
  const maitriData = stationsData?.find((s) => s.station_id === 'maitri');

  return (
    <section id="stations" className="w-full mb-10">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 mb-5">
        <div>
          <h2 className="font-display font-bold text-2xl text-[#131b2e] tracking-tight">
            Indian Antarctic Research Stations
          </h2>
          <p className="text-xs text-[#73738c] mt-1 font-mono">
            Select a station card to open its real-time React Flow digital twin
          </p>
        </div>

        <div className="text-xs text-[#73738c] font-mono">
          <span>Active Context: </span>
          <span className="font-bold text-[#4648d4] uppercase">
            {activeStation === 'bharati' ? 'Bharati (69°S)' : 'Maitri (70°S)'}
          </span>
        </div>
      </div>

      {/* 2 Interactive Station Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* ================= CARD 1: BHARATI ================= */}
        <div
          onClick={() => onSelectStationTwin('bharati')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onSelectStationTwin('bharati');
          }}
          className={`relative rounded-3xl p-6 transition-all duration-200 cursor-pointer text-left border group ${
            activeStation === 'bharati'
              ? 'bg-white border-[#4648d4] ring-2 ring-[#4648d4]/20 shadow-xl shadow-[#4648d4]/10'
              : 'bg-white/85 hover:bg-white border-[#eaebf0] hover:border-[#4648d4]/40 shadow-sm hover:shadow-md'
          }`}
        >
          {/* Active Context Glow Pill */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-2xl bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-bold font-mono text-sm border border-[#4648d4]/20 group-hover:scale-105 transition-transform">
                BH
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight flex items-center gap-2">
                  <span>Bharati Research Station</span>
                </h3>
                <span className="text-xs text-[#73738c] font-medium">
                  Larsemann Hills, East Antarctica (69° 24&apos; S, 76° 11&apos; E)
                </span>
              </div>
            </div>

            {/* Active Status Badge */}
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold font-mono">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              505 Sensors Active
            </span>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            {/* Microgrid Load */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.station_electrical_load_kw?.toFixed(1) || '148.7'} kW
              </div>
            </div>

            {/* Indoor Temperature */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                +{bharatiData?.kpis?.indoor_avg_temp_c?.toFixed(1) || '20.2'}°C
              </div>
            </div>

            {/* Ambient Climate */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.wind_speed_mps?.toFixed(1) || '12.0'} m/s
              </div>
            </div>

            {/* Bulk Fuel Autonomy */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.fuel_autonomy_days?.toFixed(0) || '282'} Days
              </div>
            </div>

            {/* Potable Water Tank */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.potable_tank_level_pct?.toFixed(0) || '82'}% Level
              </div>
            </div>

            {/* Sensor Channels */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Radio className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Satcom Uplink</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                640ms Delta
              </div>
            </div>
          </div>

          {/* Action Button: Opens Bharati Digital Twin */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between">
            <span className="text-xs font-mono text-[#73738c]">
              Click card to open Bharati Digital Twin
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelectStationTwin('bharati');
              }}
              className="px-4 py-2 rounded-xl bg-[#4648d4] text-white hover:bg-[#3b3dbf] font-mono text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Open Bharati Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* ================= CARD 2: MAITRI ================= */}
        <div
          onClick={() => onSelectStationTwin('maitri')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') onSelectStationTwin('maitri');
          }}
          className={`relative rounded-3xl p-6 transition-all duration-200 cursor-pointer text-left border group ${
            activeStation === 'maitri'
              ? 'bg-white border-[#006577] ring-2 ring-[#006577]/20 shadow-xl shadow-[#006577]/10'
              : 'bg-white/85 hover:bg-white border-[#eaebf0] hover:border-[#006577]/40 shadow-sm hover:shadow-md'
          }`}
        >
          {/* Active Context Glow Pill */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-2xl bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold font-mono text-sm border border-[#006577]/20 group-hover:scale-105 transition-transform">
                MT
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight flex items-center gap-2">
                  <span>Maitri Research Station</span>
                </h3>
                <span className="text-xs text-[#73738c] font-medium">
                  Schirmacher Oasis, Queen Maud Land (70° 45&apos; S, 11° 43&apos; E)
                </span>
              </div>
            </div>

            {/* Active Status Badge */}
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold font-mono">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              505 Sensors Active
            </span>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            {/* Microgrid Load */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Zap className="w-3.5 h-3.5 text-[#006577]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.station_electrical_load_kw?.toFixed(1) || '148.0'} kW
              </div>
            </div>

            {/* Indoor Temperature */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                +{maitriData?.kpis?.indoor_avg_temp_c?.toFixed(1) || '20.2'}°C
              </div>
            </div>

            {/* Ambient Climate */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.wind_speed_mps?.toFixed(1) || '12.0'} m/s
              </div>
            </div>

            {/* Bulk Fuel Autonomy */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.fuel_autonomy_days?.toFixed(0) || '262'} Days
              </div>
            </div>

            {/* Potable Water Tank */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.potable_tank_level_pct?.toFixed(0) || '82'}% Level
              </div>
            </div>

            {/* Sensor Channels */}
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1">
                <Radio className="w-3.5 h-3.5 text-[#006577]" />
                <span>Satcom Uplink</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                640ms Delta
              </div>
            </div>
          </div>

          {/* Action Button: Opens Maitri Digital Twin */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-between">
            <span className="text-xs font-mono text-[#73738c]">
              Click card to open Maitri Digital Twin
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelectStationTwin('maitri');
              }}
              className="px-4 py-2 rounded-xl bg-[#006577] text-white hover:bg-[#005160] font-mono text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Open Maitri Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
