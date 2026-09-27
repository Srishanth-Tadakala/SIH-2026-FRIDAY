import React from 'react';
import { 
  Zap, 
  Thermometer, 
  Wind, 
  Fuel, 
  Droplet, 
  Radio, 
  ArrowRight,
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
      <div className="flex items-center justify-between gap-2 mb-5">
        <h2 className="font-display font-bold text-2xl text-[#131b2e] tracking-tight">
          Antarctic Research Stations
        </h2>
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
          {/* Card Header */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-2xl bg-[#4648d4]/10 text-[#4648d4] flex items-center justify-center font-bold font-mono text-sm border border-[#4648d4]/20 group-hover:scale-105 transition-transform">
                BH
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight">
                  Bharati Research Station
                </h3>
                <span className="text-xs text-[#73738c] font-mono">
                  Larsemann Hills (69°24'S, 76°11'E)
                </span>
              </div>
            </div>

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold font-mono">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              505 Sensors
            </span>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Zap className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.station_electrical_load_kw != null
                  ? `${bharatiData.kpis.station_electrical_load_kw.toFixed(1)} kW`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.indoor_avg_temp_c != null
                  ? `${bharatiData.kpis.indoor_avg_temp_c > 0 ? '+' : ''}${bharatiData.kpis.indoor_avg_temp_c.toFixed(1)}°C`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.wind_speed_mps != null
                  ? `${bharatiData.kpis.wind_speed_mps.toFixed(1)} m/s`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.fuel_autonomy_days != null
                  ? `${bharatiData.kpis.fuel_autonomy_days.toFixed(0)} Days`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData?.kpis?.potable_tank_level_pct != null
                  ? `${bharatiData.kpis.potable_tank_level_pct.toFixed(0)}% Level`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Radio className="w-3.5 h-3.5 text-[#4648d4]" />
                <span>Twin Telemetry</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {bharatiData ? 'DIGITAL_TWIN' : 'DISCONNECTED'}
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-end">
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
          {/* Card Header */}
          <div className="flex items-center justify-between gap-2 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-10 h-10 rounded-2xl bg-[#006577]/10 text-[#006577] flex items-center justify-center font-bold font-mono text-sm border border-[#006577]/20 group-hover:scale-105 transition-transform">
                MT
              </div>
              <div>
                <h3 className="font-display font-bold text-lg text-[#131b2e] leading-tight">
                  Maitri Research Station
                </h3>
                <span className="text-xs text-[#73738c] font-mono">
                  Schirmacher Oasis (70°45'S, 11°43'E)
                </span>
              </div>
            </div>

            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#ecfdf5] border border-[#a7f3d0] text-[#006c49] text-xs font-semibold font-mono">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-pulse" />
              505 Sensors
            </span>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 my-4">
            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Zap className="w-3.5 h-3.5 text-[#006577]" />
                <span>Microgrid Load</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.station_electrical_load_kw != null
                  ? `${maitriData.kpis.station_electrical_load_kw.toFixed(1)} kW`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Thermometer className="w-3.5 h-3.5 text-[#10b981]" />
                <span>Habitat Temp</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.indoor_avg_temp_c != null
                  ? `${maitriData.kpis.indoor_avg_temp_c > 0 ? '+' : ''}${maitriData.kpis.indoor_avg_temp_c.toFixed(1)}°C`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Wind className="w-3.5 h-3.5 text-[#006577]" />
                <span>Polar Wind</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.wind_speed_mps != null
                  ? `${maitriData.kpis.wind_speed_mps.toFixed(1)} m/s`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Fuel className="w-3.5 h-3.5 text-[#f59e0b]" />
                <span>Fuel Autonomy</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.fuel_autonomy_days != null
                  ? `${maitriData.kpis.fuel_autonomy_days.toFixed(0)} Days`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Droplet className="w-3.5 h-3.5 text-[#06b6d4]" />
                <span>Water Storage</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData?.kpis?.potable_tank_level_pct != null
                  ? `${maitriData.kpis.potable_tank_level_pct.toFixed(0)}% Level`
                  : '—'}
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-[#faf8ff] border border-[#eaedff]">
              <div className="flex items-center gap-1.5 text-xs text-[#73738c] mb-1 font-mono">
                <Radio className="w-3.5 h-3.5 text-[#006577]" />
                <span>Twin Telemetry</span>
              </div>
              <div className="font-mono font-bold text-base text-[#131b2e]">
                {maitriData ? 'DIGITAL_TWIN' : 'DISCONNECTED'}
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="pt-3 border-t border-[#eaebf0] flex items-center justify-end">
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
